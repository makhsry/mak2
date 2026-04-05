# Import required libraries with auto-installation
import subprocess
import sys
import os
import math
import shutil
from pathlib import Path

def install_package(package):
    """Silently install a package if not already installed"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")
        sys.exit(1)

def install_ffmpeg():
    """Check if ffmpeg is installed, provide instructions if not"""
    try:
        subprocess.check_call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ffmpeg is not installed.")
        print("Please install ffmpeg:")
        print("  - Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  - macOS: brew install ffmpeg")
        print("  - Windows: Download from https://ffmpeg.org/download.html")
        sys.exit(1)

def check_gpu():
    """Check if GPU (CUDA) is available"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"GPU detected: {gpu_name}")
            return True
        else:
            print("No GPU detected, using CPU (will be slower)")
            return False
    except ImportError:
        print("PyTorch not found, using CPU")
        return False

# Check and install required packages
print("Checking dependencies...")
required_packages = {
    'torch': 'torch',
    'demucs': 'demucs',
    'soundfile': 'soundfile',
    'librosa': 'librosa',
    'numpy': 'numpy',
    'scipy': 'scipy',
    'matplotlib': 'matplotlib'
}

for import_name, package_name in required_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing {package_name}...")
        install_package(package_name)

# Check ffmpeg
install_ffmpeg()

# Now import the libraries
import torch
from demucs import pretrained
from demucs.apply import apply_model
import soundfile as sf
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import librosa
import librosa.display

def to_wav_preserve(input_path, out_wav=None):
    """Convert input audio to 32-bit float WAV preserving sample rate"""
    if out_wav is None:
        stem = Path(input_path).stem
        out_wav = f"{stem}_converted.wav"
    
    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn", "-map", "0:a:0", 
           "-c:a", "pcm_f32le", str(out_wav)]
    
    print("Converting to WAV (32-bit float)...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error converting file: {e}")
        sys.exit(1)
    
    return out_wav

def split_into_chunks(signal, sr, chunk_sec=6, overlap_sec=1.0):
    """Split signal into overlapping chunks"""
    step = int((chunk_sec - overlap_sec) * sr)
    win = int(chunk_sec * sr)
    
    if step <= 0:
        raise ValueError("chunk_sec must be > overlap_sec.")
    
    chunks = []
    idx = 0
    while idx < len(signal):
        chunk = signal[idx: idx + win]
        chunks.append((idx, chunk))
        idx += step
    
    return chunks, win, step

def overlap_add_segments(segments, length, step):
    """Reconstruct full audio from overlapping segments"""
    n_chunks = len(segments)
    n_sources = segments[0].shape[0]
    
    out = [np.zeros(length, dtype=np.float32) for _ in range(n_sources)]
    counts = np.zeros(length, dtype=np.float32)
    
    pos = 0
    for seg in segments:
        seg_len = seg.shape[1]
        for s in range(n_sources):
            end = pos + seg_len
            out[s][pos:end] += seg[s]
        counts[pos:pos+seg_len] += 1.0
        pos += step
    
    # Avoid division by zero
    counts[counts == 0] = 1.0
    for s in range(n_sources):
        out[s] /= counts
    
    return out

def separate_with_demucs(wav_path, output_dir, model_name="htdemucs", 
                         chunk_seconds=6, chunk_overlap=1.0):
    """Separate audio using Demucs model"""
    print(f"Loading Demucs model: {model_name}...")
    
    try:
        model = pretrained.get_model(model_name)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)
        model.eval()
        print(f"Model loaded on {device}")
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)
    
    # Load audio
    print("Loading audio...")
    full_audio, full_sr = sf.read(wav_path, dtype='float32')
    
    if full_audio.ndim == 1:
        full_audio = full_audio[np.newaxis, :]
    else:
        full_audio = full_audio.T
    
    print(f"Audio shape (channels, samples): {full_audio.shape}")
    
    # Split into chunks
    chunks, win, step = split_into_chunks(full_audio[0], full_sr, 
                                         chunk_seconds, chunk_overlap)
    print(f"Processing {len(chunks)} chunks (window={win} samples, step={step} samples)")
    
    # Process each chunk
    separated_chunks = []
    for i, (start, chunk0) in enumerate(chunks):
        chunk_slice = full_audio[:, start:start+win]
        
        # Pad if needed
        if chunk_slice.shape[1] < win:
            pad_width = win - chunk_slice.shape[1]
            chunk_slice = np.pad(chunk_slice, ((0,0),(0,pad_width)), mode='constant')
        
        with torch.no_grad():
            wav_tensor = torch.from_numpy(chunk_slice).unsqueeze(0)
            wav_tensor = wav_tensor.to(device)
            
            est = apply_model(model, wav_tensor, device=device, split=False, overlap=0)
            est_np = est.cpu().numpy()[0]
            
            # Average channels to mono
            est_mono = est_np.mean(axis=1)
            separated_chunks.append(est_mono.astype(np.float32))
        
        print(f"  Processed chunk {i+1}/{len(chunks)}")
    
    # Overlap-add reconstruction
    print("Reconstructing full audio from chunks...")
    full_length = full_audio.shape[1]
    reconstructed_sources = overlap_add_segments(separated_chunks, full_length, step)
    
    # Save separated sources
    out_paths = []
    os.makedirs(output_dir, exist_ok=True)
    
    for idx, src in enumerate(reconstructed_sources, start=1):
        outp = os.path.join(output_dir, f"component_{idx}.wav")
        sf.write(outp, src, full_sr, subtype='FLOAT')
        out_paths.append(outp)
        print(f"  Saved: {outp}")
    
    return out_paths, full_sr, full_audio

def plot_waveforms(mixture_path, out_files, output_dir):
    """Plot overlayed waveforms"""
    print("Generating waveform plot...")
    
    mixture, sr = sf.read(mixture_path, dtype='float32')
    if mixture.ndim > 1:
        mixture_mono = mixture.mean(axis=1)
    else:
        mixture_mono = mixture
    
    plt.figure(figsize=(14, 5))
    t = np.arange(len(mixture_mono)) / sr
    plt.plot(t, mixture_mono / (np.max(np.abs(mixture_mono)) + 1e-9), 
            alpha=0.25, linewidth=0.7, label="mixture (normalized)")
    
    for i, fpath in enumerate(out_files):
        sig, _ = sf.read(fpath, dtype='float32')
        if sig.ndim > 1:
            sig = sig.mean(axis=1)
        sig = sig[:len(mixture_mono)]
        sign = sig / (np.max(np.abs(sig)) + 1e-9)
        plt.plot(t, sign, linewidth=0.9, label=f"component {i+1}")
    
    plt.xlim(0, len(mixture_mono)/sr)
    plt.xlabel("Time (s)")
    plt.ylabel("Normalized amplitude")
    plt.legend(loc='upper right')
    plt.title("Overlayed waveforms - mixture + separated components")
    
    plot_path = os.path.join(output_dir, "waveforms.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    print(f"  Waveform plot saved: {plot_path}")
    return plot_path

def plot_spectrograms(mixture_path, out_files, output_dir):
    """Plot spectrograms for mixture and separated components"""
    print("Generating spectrograms...")
    
    mixture, sr = sf.read(mixture_path, dtype='float32')
    if mixture.ndim > 1:
        mixture_mono = mixture.mean(axis=1)
    else:
        mixture_mono = mixture
    
    n = len(out_files)
    cols = 2
    rows = math.ceil((n+1)/cols)
    
    plt.figure(figsize=(14, 3*rows))
    
    # Mixture spectrogram
    plt.subplot(rows, cols, 1)
    D = np.abs(librosa.stft(mixture_mono, n_fft=2048, hop_length=512))
    librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max), 
                            sr=sr, x_axis='time', y_axis='log')
    plt.title("Mixture spectrogram")
    plt.colorbar(format="%+2.0f dB")
    
    # Component spectrograms
    for i, fpath in enumerate(out_files, start=1):
        plt.subplot(rows, cols, i+1)
        sig, _ = sf.read(fpath, dtype='float32')
        if sig.ndim > 1:
            sig = sig.mean(axis=1)
        D = np.abs(librosa.stft(sig, n_fft=2048, hop_length=512))
        librosa.display.specshow(librosa.amplitude_to_db(D, ref=np.max), 
                                sr=sr, x_axis='time', y_axis='log')
        plt.title(f"Component {i} spectrogram")
        plt.colorbar(format="%+2.0f dB")
    
    plt.tight_layout()
    
    plot_path = os.path.join(output_dir, "spectrograms.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    
    print(f"  Spectrogram plot saved: {plot_path}")
    return plot_path

def guess_label(signal, sr):
    """Guess component label using simple heuristics"""
    if signal.ndim > 1:
        signal = signal.mean(axis=1)
    
    centroid = librosa.feature.spectral_centroid(y=signal, sr=sr).mean()
    rms = librosa.feature.rms(y=signal).mean()
    
    if centroid < 200 and rms > 1e-5:
        return "low-hum/low-frequency noise"
    if 200 < centroid < 3000 and rms < 0.02:
        return "possible speech/voice"
    if centroid >= 3000:
        return "music/bright content"
    
    return "unknown"

# Main execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_separation_demucs.py <input_audio_file> [model] [chunk_seconds] [overlap]")
        print("\nModels: htdemucs (default, best quality), demucs")
        print("Chunk seconds: 6 (default, lower for less GPU memory)")
        print("Overlap: 1.0 (default, seconds of overlap between chunks)")
        print("\nExamples:")
        print("  python audio_separation_demucs.py audio.m4a")
        print("  python audio_separation_demucs.py audio.mp3 htdemucs 10 1.5")
        print("\nNote: Requires GPU for best performance. First run downloads model (~300MB).")
        sys.exit(1)
    
    # Get arguments
    input_file = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "htdemucs"
    chunk_seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 6
    chunk_overlap = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    # Check GPU
    check_gpu()
    
    try:
        # Setup output directory
        base_name = Path(input_file).stem
        output_dir = f"{base_name}_separated"
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert to WAV
        if not input_file.lower().endswith('.wav'):
            wav_file = to_wav_preserve(input_file)
        else:
            wav_file = input_file
        
        # Load and display info
        data, sr = sf.read(wav_file, dtype='float32')
        duration = len(data) / sr
        print(f"Audio loaded: duration={duration:.2f}s, sr={sr}Hz")
        
        # Separate with Demucs
        print("\n" + "="*50)
        print("Starting Demucs separation...")
        print("="*50)
        out_files, sr, full_audio = separate_with_demucs(
            wav_file, output_dir, model_name, chunk_seconds, chunk_overlap
        )
        
        # Generate visualizations
        print("\n" + "="*50)
        print("Generating visualizations...")
        print("="*50)
        waveform_plot = plot_waveforms(wav_file, out_files, output_dir)
        spectrogram_plot = plot_spectrograms(wav_file, out_files, output_dir)
        
        # Auto-label components
        print("\n" + "="*50)
        print("Auto-labeling components...")
        print("="*50)
        for f in out_files:
            s, _ = sf.read(f, dtype='float32')
            if s.ndim > 1:
                s_m = s.mean(axis=1)
            else:
                s_m = s
            label = guess_label(s_m, sr)
            print(f"  {Path(f).name} -> {label}")
        
        # Create archive
        print("\n" + "="*50)
        print("Creating archive...")
        print("="*50)
        archive_name = shutil.make_archive(output_dir, 'zip', output_dir)
        print(f"  ✓ Archive created: {archive_name}")
        
        # Summary
        print("\n" + "="*50)
        print("✓ Audio separation complete!")
        print("="*50)
        print(f"Separated components: {len(out_files)}")
        print(f"Output directory: {output_dir}/")
        print(f"Archive: {archive_name}")
        print(f"\nFiles created:")
        for f in out_files:
            print(f"  - {f}")
        print(f"  - {waveform_plot}")
        print(f"  - {spectrogram_plot}")
        
    except Exception as e:
        print(f"\nError during separation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
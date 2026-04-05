# Import required libraries with auto-installation
import subprocess
import sys
import os

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

# The NMF algorithm itself (from scikit-learn) doesn't have GPU support, 
# but CuPy can accelerate some NumPy operations. 
def check_gpu():
    """Check if GPU (CUDA) is available"""
    try:
        import cupy as cp
        print(f"GPU detected: CUDA available")
        return True
    except ImportError:
        print("No GPU/CuPy detected, using CPU (NumPy)")
        return False

# Check and install required packages
required_packages = {
    'numpy': 'numpy',
    'scipy': 'scipy',
    'matplotlib': 'matplotlib',
    'soundfile': 'soundfile',
    'sklearn': 'scikit-learn'
}

for import_name, package_name in required_packages.items():
    try:
        __import__(import_name)
    except ImportError:
        print(f"Installing {package_name}...")
        install_package(package_name)

# Try to install CuPy for GPU acceleration (optional)
try:
    import cupy as cp
    xp = cp
    gpu_available = True
except ImportError:
    import numpy as np
    xp = np
    gpu_available = False

# Check ffmpeg
install_ffmpeg()

# Now import the libraries
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy import signal
import soundfile as sf
from sklearn.decomposition import NMF

def convert_to_wav(input_file, output_file):
    """Convert audio file to WAV using ffmpeg"""
    print(f"Converting '{input_file}' to WAV format...")
    res = subprocess.run(['ffmpeg', '-y', '-i', input_file, output_file], 
                        capture_output=True, text=True)
    
    if res.returncode != 0:
        print(f"ffmpeg error: {res.stderr[:1000]}")
        raise RuntimeError("ffmpeg failed to convert the file")
    
    print(f"Converted to '{output_file}'")
    return output_file

def load_audio(wav_file):
    """Load audio file and convert to mono if needed"""
    print(f"Loading audio file...")
    y, sr = sf.read(wav_file)
    
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    
    y = y.astype(np.float32)
    duration = len(y) / sr
    print(f"Loaded: duration={duration:.2f}s, sample_rate={sr}Hz, samples={len(y)}")
    
    return y, sr, duration

def perform_stft(y, sr, n_fft=2048, hop_length=512):
    """Compute Short-Time Fourier Transform"""
    print("Computing STFT...")
    f, t, Zxx = signal.stft(y, fs=sr, nperseg=n_fft, 
                            noverlap=n_fft-hop_length, boundary=None)
    S = np.abs(Zxx)
    print(f"STFT shape: {S.shape}")
    
    return f, t, Zxx, S

def find_optimal_components(S, min_components=2, max_components=7):
    """Find optimal number of NMF components"""
    print(f"Finding optimal number of components ({min_components}-{max_components})...")
    
    S_max = S.max() if S.max() > 0 else 1.0
    S_norm = S / S_max + 1e-10
    
    recons_scores = {}
    for n_comp in range(min_components, max_components):
        model = NMF(n_components=n_comp, init='nndsvda', solver='mu', 
                   beta_loss='kullback-leibler', max_iter=500, random_state=0)
        W = model.fit_transform(S_norm)
        H = model.components_
        S_approx = np.dot(W, H)
        err = np.linalg.norm(S_norm - S_approx, ord='fro')
        fit = 1 - (err / np.linalg.norm(S_norm, ord='fro'))
        recons_scores[n_comp] = fit
        print(f"  n={n_comp} fit={fit:.4f}")
    
    # Choose best n with diminishing returns
    prev = None
    best_n = max_components - 1
    for n, fit in sorted(recons_scores.items()):
        if prev is not None:
            if fit - prev < 0.02:
                best_n = n
                break
        prev = fit
    
    print(f"Chosen components: {best_n}")
    return best_n, S_norm, S_max

def separate_sources(S, S_norm, S_max, n_components, Zxx, sr, n_fft=2048, hop_length=512):
    """Perform NMF-based source separation"""
    print(f"Separating sources with {n_components} components...")
    
    # Run NMF
    model = NMF(n_components=n_components, init='nndsvda', solver='mu',
               beta_loss='kullback-leibler', max_iter=500, random_state=0)
    W = model.fit_transform(S_norm)
    H = model.components_
    
    # Compute component spectrograms
    components_S = []
    for k in range(n_components):
        comp = np.outer(W[:, k], H[k, :]) * S_max
        components_S.append(comp)
    components_S = np.array(components_S)
    
    # Create masks and reconstruct
    eps = 1e-10
    sum_S = np.sum(components_S, axis=0) + eps
    masks = components_S / sum_S
    
    reconstructed = []
    for k in range(n_components):
        masked = masks[k] * Zxx
        _, y_comp = signal.istft(masked, fs=sr, nperseg=n_fft, 
                                noverlap=n_fft-hop_length, input_onesided=True)
        reconstructed.append(y_comp)
    
    print(f"Separated into {n_components} components")
    return reconstructed

def save_components(reconstructed, sr, output_prefix):
    """Save separated components to WAV files"""
    print("Saving separated components...")
    out_files = []
    
    for k, y_comp in enumerate(reconstructed):
        output_file = f"{output_prefix}_component_{k+1}.wav"
        sf.write(output_file, y_comp, sr)
        out_files.append(output_file)
        print(f"  ✓ Saved: {output_file}")
    
    return out_files

def plot_waveforms(y, reconstructed, sr, duration, output_file):
    """Plot overlayed waveforms"""
    print("Generating waveform plot...")
    
    plt.figure(figsize=(12, 6))
    t_axis = np.arange(len(y)) / sr
    plt.plot(t_axis, y / (np.max(np.abs(y)) + 1e-9), alpha=0.25, 
            linewidth=0.8, label='mixture (normalized)')
    
    for k, sig in enumerate(reconstructed):
        if np.max(np.abs(sig)) > 0:
            sign = sig / np.max(np.abs(sig))
        else:
            sign = sig
        t_axis_comp = np.arange(len(sign)) / sr
        plt.plot(t_axis_comp, sign, linewidth=1, label=f'component {k+1}')
    
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (normalized)')
    plt.title('Overlayed waveforms: separated components (normalized)')
    plt.legend(loc='upper right', fontsize='small')
    plt.xlim(0, duration)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()
    
    print(f"Plot saved: {output_file}")

# Main execution
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_separation.py <input_audio_file> [n_components]")
        print("\nOptional:")
        print("  n_components: Number of sources to separate (default: auto-detect)")
        print("\nExamples:")
        print("  python audio_separation.py audio.m4a")
        print("  python audio_separation.py audio.mp3 4")
        print("\nSupported formats: mp3, m4a, wav, flac, ogg, etc.")
        sys.exit(1)
    
    # Get input file
    input_file = sys.argv[1]
    
    # Get optional number of components
    n_components = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    
    # Check GPU
    gpu_available = check_gpu()
    
    try:
        # Convert to WAV if needed
        if not input_file.lower().endswith('.wav'):
            base_name = os.path.splitext(input_file)[0]
            wav_file = f"{base_name}_converted.wav"
            convert_to_wav(input_file, wav_file)
        else:
            wav_file = input_file
            base_name = os.path.splitext(input_file)[0]
        
        # Load audio
        y, sr, duration = load_audio(wav_file)
        
        # Perform STFT
        f, t, Zxx, S = perform_stft(y, sr)
        
        # Find optimal components or use specified
        if n_components is None:
            n_components, S_norm, S_max = find_optimal_components(S)
        else:
            S_max = S.max() if S.max() > 0 else 1.0
            S_norm = S / S_max + 1e-10
            print(f"Using specified number of components: {n_components}")
        
        # Separate sources
        reconstructed = separate_sources(S, S_norm, S_max, n_components, Zxx, sr)
        
        # Trim reconstructed signals to match original length
        reconstructed = [y_comp[:len(y)] for y_comp in reconstructed]
        
        # Save components
        output_prefix = base_name
        out_files = save_components(reconstructed, sr, output_prefix)
        
        # Plot waveforms
        plot_file = f"{base_name}_waveforms.png"
        plot_waveforms(y, reconstructed, sr, duration, plot_file)
        
        print("\n" + "="*50)
        print("Audio separation complete!")
        print("="*50)
        print(f"Separated components: {len(out_files)}")
        print(f"Output files: {', '.join(out_files)}")
        print(f"Waveform plot: {plot_file}")
        
    except Exception as e:
        print(f"Error during separation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
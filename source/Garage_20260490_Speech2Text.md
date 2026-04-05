# Speech-to-Text via OpenAI Whisper

Two Python scripts ([CPU version](#cpu-script) and [GPU version](#gpu-script)) that perform automatic speech recognition (ASR) on audio files using OpenAI's Whisper model. One targets CPU-only environments; the other adds GPU (CUDA) acceleration via PyTorch.

Whisper is a sequence-to-sequence Transformer trained on 680,000 hours of labelled speech. The `model_size` argument selects one of five pre-trained checkpoints. `whisper.load_model(model_size)` downloads (on first run) and caches the corresponding checkpoint and returns a `Whisper` object whose `transcribe` method drives the full inference pipeline.

| `model_size` | Parameters | Encoder layers | Decoder layers | d_model | Heads |  Download size |
|---|---|---|---|---|---|---|
| `tiny`   |  39 M |  4 |  4 |  384 |  6 | ~75 MB
| `base`   |  74 M |  6 |  6 |  512 |  8 | ~145 MB
| `small`  | 244 M | 12 | 12 |  768 | 12 | ~465 MB
| `medium` | 769 M | 24 | 24 | 1024 | 16 | ~1.5 GB
| `large`  | 1550 M | 32 | 32 | 1280 | 20 | ~2.9 GB

## Usage Instructions
### Prerequisites
1. **Python 3.8+** — required by `openai-whisper`.
2. **ffmpeg** — must be on `PATH`. The scripts will exit with an error and installation hints if it is not found.
3. **pip** — standard Python package installer (required for the auto-install logic).
4. **(GPU script only) CUDA-capable NVIDIA GPU** with a compatible CUDA driver — optional; the script falls back to CPU automatically.

For CPU script:
```bash
python speech2text_via_OpenAI_Whisper.py <audio_file> [model_size] [language]
```

**Positional argument (required):**

| Position | Name | Description |
|---|---|---|
| 1 | `audio_file` | Path to the input audio file (any format supported by ffmpeg: `.mp3`, `.mp4`, `.wav`, `.flac`, `.ogg`, `.m4a`, etc.) |

**Positional arguments (optional, must appear in order):**

| Position | Name | Default | Description |
|---|---|---|---|
| 2 | `model_size` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| 3 | `language` | *(auto-detect)* | ISO 639-1 language code, e.g., `en`, `es`, `fr`, `de`, `zh`, `ar` |

For GPU script:
```bash
python speech2text_via_OpenAI_Whisper_GPU.py <audio_file> [model_size] [language] [device]
```

All arguments from the CPU script apply. One additional optional argument is added:

| Position | Name | Default | Description |
|---|---|---|---|
| 4 | `device` | *(auto-detect)* | `cuda` to force GPU, `cpu` to force CPU |

> **Note:** When `device` is required but `language` should remain auto-detected, there is no way to skip `language` positionally. You must either pass `None` as the literal string for `language` (the script will pass it as the string `"None"` to Whisper, which may not behave as expected), or edit the script to use `argparse`. If you want GPU with auto-detected language, omit both arguments and let the auto-detection handle both:
> ```bash
> python speech2text_via_OpenAI_Whisper_GPU.py audio.mp3 base
> ```
> This will auto-detect language and select CUDA automatically.

## CPU Script

```python
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
# Check and install required packages
required_packages = {
    'whisper': 'openai-whisper'
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
import whisper
def transcribe_audio(audio_file, model_size="base", language=None):
    """
    Transcribe audio file using Whisper
    Parameters:
    - audio_file: path to audio file
    - model_size: 'tiny', 'base', 'small', 'medium', 'large'
    - language: e.g., 'en', 'es', 'fr' (None for auto-detect)
    """
    print(f"Loading {model_size} model...")
    model = whisper.load_model(model_size)
    print("Transcribing audio...")
    if language:
        result = model.transcribe(audio_file, language=language)
    else:
        result = model.transcribe(audio_file)
    return result
def save_transcription(result, output_file="transcription.txt"):
    """Save transcription to file"""
    # Full text
    full_text = result["text"]
    # Create detailed output
    output = "=" * 50 + "\n"
    output += "FULL TRANSCRIPTION\n"
    output += "=" * 50 + "\n\n"
    output += full_text + "\n\n"
    output += "=" * 50 + "\n"
    output += "TIMESTAMPED SEGMENTS\n"
    output += "=" * 50 + "\n\n"
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        output += f"[{start:.2f}s - {end:.2f}s] {text}\n"
    # Detected language
    if "language" in result:
        output += f"\n\nDetected Language: {result['language']}\n"
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Transcription saved to {output_file}")
    return full_text
# Main execution
if __name__ == "__main__":
    # Check if file path is provided as command-line argument
    if len(sys.argv) < 2:
        print("Usage: python speech2text.py <path_to_audio_file> [model_size] [language]")
        print("\nModel sizes: tiny, base (default), small, medium, large")
        print("Language: en, es, fr, etc. (optional, auto-detect by default)")
        print("\nExample: python speech2text.py audio.mp3 base en")
        sys.exit(1)
    # Get file path from command-line argument
    audio_file = sys.argv[1]
    # Get optional model size (default: base)
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    # Get optional language (default: None for auto-detect)
    language = sys.argv[3] if len(sys.argv) > 3 else None
    # Check if file exists
    if not os.path.exists(audio_file):
        print(f"Error: File '{audio_file}' not found.")
        sys.exit(1)
    # Transcribe
    try:
        result = transcribe_audio(audio_file, model_size=model_size, language=language)
        # Display results
        print("\n" + "=" * 50)
        print("TRANSCRIPTION:")
        print("=" * 50)
        print(result["text"])
        # Save transcription
        output_filename = os.path.splitext(os.path.basename(audio_file))[0] + "_transcription.txt"
        save_transcription(result, output_filename)
    except Exception as e:
        print(f"Error during transcription: {e}")
        sys.exit(1)
```

## GPU Script

```python
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
def check_gpu():
    """Check if GPU (CUDA) is available"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"GPU detected: {gpu_name}")
            return True
        else:
            print("No GPU detected, using CPU")
            return False
    except ImportError:
        print("PyTorch not found, using CPU")
        return False
# Check and install required packages
required_packages = {
    'whisper': 'openai-whisper',
    'torch': 'torch'
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
import whisper
import torch
#
def transcribe_audio(audio_file, model_size="base", language=None, device=None):
    """
    Transcribe audio file using Whisper
    Parameters:
    - audio_file: path to audio file
    - model_size: 'tiny', 'base', 'small', 'medium', 'large'
    - language: e.g., 'en', 'es', 'fr' (None for auto-detect)
    - device: 'cuda' for GPU, 'cpu' for CPU (None for auto-detect)
    """
    # Auto-detect device if not specified
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {model_size} model on {device.upper()}...")
    model = whisper.load_model(model_size, device=device)
    print("Transcribing audio...")
    if language:
        result = model.transcribe(audio_file, language=language)
    else:
        result = model.transcribe(audio_file)
    return result
#
def save_transcription(result, output_file="transcription.txt"):
    """Save transcription to file"""
    # Full text
    full_text = result["text"]
    # Create detailed output
    output = "=" * 50 + "\n"
    output += "FULL TRANSCRIPTION\n"
    output += "=" * 50 + "\n\n"
    output += full_text + "\n\n"
    output += "=" * 50 + "\n"
    output += "TIMESTAMPED SEGMENTS\n"
    output += "=" * 50 + "\n\n"
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        output += f"[{start:.2f}s - {end:.2f}s] {text}\n"
    # Detected language
    if "language" in result:
        output += f"\n\nDetected Language: {result['language']}\n"
    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Transcription saved to {output_file}")
    return full_text
# Main execution
if __name__ == "__main__":
    # Check if file path is provided as command-line argument
    if len(sys.argv) < 2:
        print("Usage: python speech2text.py <path_to_audio_file> [model_size] [language] [device]")
        print("\nModel sizes: tiny, base (default), small, medium, large")
        print("Language: en, es, fr, etc. (optional, auto-detect by default)")
        print("Device: cuda, cpu (optional, auto-detect by default)")
        print("\nExamples:")
        print("  python speech2text.py audio.mp3")
        print("  python speech2text.py audio.mp3 base en")
        print("  python speech2text.py audio.mp3 large en cuda")
        sys.exit(1)
    # Get file path from command-line argument
    audio_file = sys.argv[1]
    # Get optional model size (default: base)
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    # Get optional language (default: None for auto-detect)
    language = sys.argv[3] if len(sys.argv) > 3 else None
    # Get optional device (default: None for auto-detect)
    device = sys.argv[4] if len(sys.argv) > 4 else None
    # Check if file exists
    if not os.path.exists(audio_file):
        print(f"Error: File '{audio_file}' not found.")
        sys.exit(1)
    # Check GPU availability
    check_gpu()
    # Transcribe
    try:
        result = transcribe_audio(audio_file, model_size=model_size, language=language, device=device)
        # Display results
        print("\n" + "=" * 50)
        print("TRANSCRIPTION:")
        print("=" * 50)
        print(result["text"])
        # Save transcription
        output_filename = os.path.splitext(os.path.basename(audio_file))[0] + "_transcription.txt"
        save_transcription(result, output_filename)
    except Exception as e:
        print(f"Error during transcription: {e}")
        sys.exit(1)
```
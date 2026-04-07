# Import required libraries with auto-installation
import subprocess
import sys
import os

HELP_TEXT = """
USAGE:
  python Garage_20260490_Speech2Text.py <audio_file> [OPTIONS]

POSITIONAL ARGUMENT:
  audio_file          Path to the audio file to transcribe.
                      Supported formats: mp3, wav, m4a, ogg, flac, mp4, etc.

OPTIONS:
  --model   SIZE      Whisper model size (default: base)
                        tiny   – fastest, least accurate  (~39 M params)
                        base   – good balance             (~74 M params)
                        small  – better accuracy          (~244 M params)
                        medium – high accuracy            (~769 M params)
                        large  – best accuracy, slowest   (~1550 M params)

  --lang    CODE      ISO language code, e.g. en, es, fr, de, zh
                      Omit to let Whisper auto-detect the language.

  --device  DEVICE    Processing device:
                        cpu    – force CPU inference
                        cuda   – force GPU (CUDA) inference
                      Omit to auto-detect (uses GPU if available).

  --output  FILE      Path for the output transcription file.
                      Default: <audio_file_name>_transcription.txt

  --help, -h          Show this help message and exit.

EXAMPLES:
  # Basic usage – auto-detect device, base model
  python Garage_20260490_Speech2Text.py interview.mp3

  # Use large model with English, force GPU
  python Garage_20260490_Speech2Text.py lecture.wav --model large --lang en --device cuda

  # Force CPU, Spanish, save to custom file
  python Garage_20260490_Speech2Text.py podcast.mp3 --model small --lang es --device cpu --output result.txt

DEPENDENCIES (auto-installed if missing):
  openai-whisper, torch

  ffmpeg must be installed separately:
    Ubuntu/Debian : sudo apt-get install ffmpeg
    macOS         : brew install ffmpeg
    Windows       : https://ffmpeg.org/download.html
"""

def install_package(package):
    """Silently install a package if not already installed."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")
        sys.exit(1)


def install_ffmpeg():
    """Check if ffmpeg is installed; print instructions and exit if not."""
    try:
        subprocess.check_call(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ERROR: ffmpeg is not installed.")
        print("Please install ffmpeg:")
        print("  Ubuntu/Debian : sudo apt-get install ffmpeg")
        print("  macOS         : brew install ffmpeg")
        print("  Windows       : https://ffmpeg.org/download.html")
        sys.exit(1)


def ensure_dependencies():
    """Auto-install Python dependencies if missing."""
    required = {"whisper": "openai-whisper", "torch": "torch"}
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"Installing {package_name}…")
            install_package(package_name)


def resolve_device(requested_device):
    """
    Determine the actual device to use.
    - 'cpu'  → always CPU
    - 'cuda' → GPU (exits with error if CUDA unavailable)
    - None   → auto-detect
    """
    import torch

    if requested_device == "cpu":
        print("Device: CPU (forced)")
        return "cpu"

    if requested_device == "cuda":
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"Device: GPU – {gpu_name} (forced)")
            return "cuda"
        else:
            print("ERROR: --device cuda was requested but no CUDA GPU is available.")
            sys.exit(1)

    # Auto-detect
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        print(f"Device: GPU – {gpu_name} (auto-detected)")
        return "cuda"
    else:
        print("Device: CPU (no GPU detected)")
        return "cpu"


def transcribe_audio(audio_file, model_size="base", language=None, device="cpu"):
    """
    Transcribe an audio file using Whisper.

    Parameters
    ----------
    audio_file  : path to the audio file
    model_size  : 'tiny' | 'base' | 'small' | 'medium' | 'large'
    language    : ISO code, e.g. 'en' (None = auto-detect)
    device      : 'cpu' | 'cuda'
    """
    import whisper

    print(f"Loading '{model_size}' model on {device.upper()}…")
    model = whisper.load_model(model_size, device=device)

    print("Transcribing audio…")
    transcribe_kwargs = {}
    if language:
        transcribe_kwargs["language"] = language

    result = model.transcribe(audio_file, **transcribe_kwargs)
    return result


def save_transcription(result, output_file):
    """Write the transcription (full text + timestamped segments) to a file."""
    full_text = result["text"]

    lines = []
    lines.append("=" * 50)
    lines.append("FULL TRANSCRIPTION")
    lines.append("=" * 50)
    lines.append("")
    lines.append(full_text)
    lines.append("")
    lines.append("=" * 50)
    lines.append("TIMESTAMPED SEGMENTS")
    lines.append("=" * 50)
    lines.append("")

    for seg in result["segments"]:
        lines.append(f"[{seg['start']:.2f}s – {seg['end']:.2f}s] {seg['text'].strip()}")

    if "language" in result:
        lines.append("")
        lines.append(f"Detected Language: {result['language']}")

    content = "\n".join(lines) + "\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Transcription saved → {output_file}")
    return full_text


def parse_args(argv):
    """Lightweight argument parser (avoids argparse dependency issues)."""
    args = {
        "audio_file": None,
        "model": "base",
        "lang": None,
        "device": None,
        "output": None,
    }

    i = 0
    positional_done = False

    while i < len(argv):
        token = argv[i]

        if token in ("--help", "-h"):
            print(HELP_TEXT)
            sys.exit(0)
        elif token == "--model":
            i += 1
            args["model"] = argv[i]
        elif token == "--lang":
            i += 1
            args["lang"] = argv[i]
        elif token == "--device":
            i += 1
            args["device"] = argv[i].lower()
            if args["device"] not in ("cpu", "cuda"):
                print(f"ERROR: Unknown device '{args['device']}'. Choose 'cpu' or 'cuda'.")
                sys.exit(1)
        elif token == "--output":
            i += 1
            args["output"] = argv[i]
        elif not token.startswith("--") and not positional_done:
            args["audio_file"] = token
            positional_done = True
        else:
            print(f"ERROR: Unknown argument '{token}'. Run with --help for usage.")
            sys.exit(1)

        i += 1

    return args


if __name__ == "__main__":
    cli_args = parse_args(sys.argv[1:])

    if cli_args["audio_file"] is None:
        print("ERROR: No audio file specified.\n")
        print(HELP_TEXT)
        sys.exit(1)

    audio_file = cli_args["audio_file"]

    if not os.path.exists(audio_file):
        print(f"ERROR: File '{audio_file}' not found.")
        sys.exit(1)

    # Install dependencies before importing them
    ensure_dependencies()
    install_ffmpeg()

    # Resolve device after torch is guaranteed to be installed
    device = resolve_device(cli_args["device"])

    # Default output filename
    output_file = cli_args["output"] or (
        os.path.splitext(os.path.basename(audio_file))[0] + "_transcription.txt"
    )

    try:
        result = transcribe_audio(
            audio_file,
            model_size=cli_args["model"],
            language=cli_args["lang"],
            device=device,
        )

        print("\n" + "=" * 50)
        print("TRANSCRIPTION:")
        print("=" * 50)
        print(result["text"])

        save_transcription(result, output_file)

    except Exception as e:
        print(f"ERROR during transcription: {e}")
        sys.exit(1)

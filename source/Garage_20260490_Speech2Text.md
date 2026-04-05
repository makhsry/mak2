## Speech-to-Text via OpenAI Whisper

Two Python scripts ([CPU version](Garage_20260490_Speech2Text_cpu.py) and [GPU version](Garage_20260490_Speech2Text_gpu.py)) that perform automatic speech recognition (ASR) on audio files using OpenAI's Whisper model. One targets CPU-only environments; the other adds GPU (CUDA) acceleration via PyTorch.

Whisper is a sequence-to-sequence Transformer trained on 680,000 hours of labelled speech. The `model_size` argument selects one of five pre-trained checkpoints. `whisper.load_model(model_size)` downloads (on first run) and caches the corresponding checkpoint and returns a `Whisper` object whose `transcribe` method drives the full inference pipeline.

| `model_size` | Parameters | Encoder layers | Decoder layers | d_model | Heads |  Download size |
|:---|:---|:---|:---|:---|:---|:---|
| `tiny`   |  39 M |  4 |  4 |  384 |  6 | ~75 MB
| `base`   |  74 M |  6 |  6 |  512 |  8 | ~145 MB
| `small`  | 244 M | 12 | 12 |  768 | 12 | ~465 MB
| `medium` | 769 M | 24 | 24 | 1024 | 16 | ~1.5 GB
| `large`  | 1550 M | 32 | 32 | 1280 | 20 | ~2.9 GB

**Usage Instructions**      
**Prerequisites**      
1. **Python 3.8+** — required by `openai-whisper`.
2. **ffmpeg** — must be on `PATH`. The scripts will exit with an error and installation hints if it is not found.
3. **pip** — standard Python package installer (required for the auto-install logic).
4. **(GPU script only) CUDA-capable NVIDIA GPU** with a compatible CUDA driver — optional; the script falls back to CPU automatically.

**For CPU script:**
```bash
python speech2text_via_OpenAI_Whisper.py <audio_file> [model_size] [language]
```

**- Positional argument (required):**

| Position | Name | Description |
|:---|:---|:---|
| 1 | `audio_file` | Path to the input audio file (any format supported by ffmpeg: `.mp3`, `.mp4`, `.wav`, `.flac`, `.ogg`, `.m4a`, etc.) |

**- Positional arguments (optional, must appear in order):**

| Position | Name | Default | Description |
|:---|:---|:---|:---|
| 2 | `model_size` | `base` | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
| 3 | `language` | *(auto-detect)* | ISO 639-1 language code, e.g., `en`, `es`, `fr`, `de`, `zh`, `ar` |

**For GPU script:**
```bash
python speech2text_via_OpenAI_Whisper_GPU.py <audio_file> [model_size] [language] [device]
```

**- All arguments from the CPU script apply. One additional optional argument is added:**

| Position | Name | Default | Description |
|:---|:---|:---|:---|
| 4 | `device` | *(auto-detect)* | `cuda` to force GPU, `cpu` to force CPU |

**Note:** When `device` is required but `language` should remain auto-detected, there is no way to skip `language` positionally. You must either pass `None` as the literal string for `language` (the script will pass it as the string `"None"` to Whisper, which may not behave as expected), or edit the script to use `argparse`. If you want GPU with auto-detected language, omit both arguments and let the auto-detection handle both:

```bash
python speech2text_via_OpenAI_Whisper_GPU.py audio.mp3 base
```

This will auto-detect language and select CUDA automatically.
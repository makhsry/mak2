## Speech-to-Text via OpenAI Whisper

The Python scripts performs **automatic speech recognition (ASR) on audio files using OpenAI's Whisper model**. 

**Download** the script from [**here**](Garage_20260490_Speech2Text.py).

**How to Use**
- to show help: **`python script_name.py --help`**
- to auto-detect device (uses GPU if available): **`python script_name.py audio.mp3`**
- to force GPU, large model, English: **`python script_name.py audio.mp3 --model large --lang en --device cuda`**
- to force CPU, save to custom file: **`python script_name.py audio.mp3 --device cpu --output result.txt`**

The **`model_size`** argument selects one of five pre-trained checkpoints. **`whisper.load_model(model_size)`** downloads (on first run) and caches the corresponding checkpoint and returns a **`Whisper`** object whose **`transcribe`** method drives the full inference pipeline.

| `model_size` | Parameters | Encoder layers | Decoder layers | d_model | Heads |  Download size |
|:---|:---|:---|:---|:---|:---|:---|
| `tiny`   |  39 M |  4 |  4 |  384 |  6 | ~75 MB
| `base`   |  74 M |  6 |  6 |  512 |  8 | ~145 MB
| `small`  | 244 M | 12 | 12 |  768 | 12 | ~465 MB
| `medium` | 769 M | 24 | 24 | 1024 | 16 | ~1.5 GB
| `large`  | 1550 M | 32 | 32 | 1280 | 20 | ~2.9 GB 
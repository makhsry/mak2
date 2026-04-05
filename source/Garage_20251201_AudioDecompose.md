## Blind Audio Source Separation 

Two scripts are available for decomposing a single mixed audio recording into its constituent spectral or acoustic components. They differ fundamentally in their underlying algorithm, computational backend, and the number of separated streams they produce. Both scripts contain a runtime dependency check at module level.  

You can also test the script using [**our standalone Python Notebook (HTML)**](Garage_20260405_ipynb.html). 

| Criterion | [**NMF version**](Garage_20251201_NMF.py) | [**Demucs version**](Garage_20251201_Demucs.py) |
|:---|:---|:---|
| **Algorithm** | Classical non-negative matrix factorization on the STFT magnitude spectrogram | End-to-end deep neural network trained on music/speech datasets |
| **Number of outputs** | Flexible: 2–6 (auto) or user-specified | Fixed by model architecture (4 stems for `htdemucs`) |
| **No GPU required** | Fully functional on CPU; CuPy optional | GPU strongly recommended; runs on CPU but is very slow |
| **First-run download** | None | ~300 MB Demucs model weights |
| **Best suited for** | Arbitrary noise decomposition, stationary spectra, machine hum, tonal interference | Music stem separation (drums/bass/other/vocals) or speech separation |
| **Phase coherence** | Yes — uses masked complex STFT (phase preserved from input) | Yes — waveform-domain model, no explicit phase manipulation |
| **Memory scaling** | Linear in spectrogram size; feasible for long files | Chunked to bound GPU memory; chunk size is user-tunable |
| **Labelling** | None | Heuristic (spectral centroid + RMS thresholds) |
| **Usage** | `python NMF.py <input_audio_file> [n_components (optional range 2–6)]` | `python Demucs.py <input_audio_file> [model] [chunk_seconds] [overlap (must be < chunk_seconds)]` |

**Note**: The NMF is run with `init='nndsvda`, `solver='mu` (multiplicative updates), `beta_loss='kullback-leibler`, `max_iter=500`, `random_state=0`. These settings are identical for both the component-selection loop and the final separation run.

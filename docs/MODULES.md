# Modules: downloads, installation and activation

This is the complete supported catalog for VoxLoom 0.4.0 on Windows, macOS and
Ubuntu. Open **Models** in the app for the same instructions, clickable links and
installation status in English or Russian. Five components are included; five
optional packs cover all supported Whisper models, DeepFilterNet3 and FlexSED/CLAP.

## Install any optional pack

1. Click its **Download ZIP** link below or in **Models**. Your browser saves the file.
2. Keep the ZIP intact. In VoxLoom choose **Models → Install pack…**, select one to
   five ZIP files and wait for verification and installation to finish.
3. Reopen **Models** and check **installed**. Select that component in its tool tab
   using the activation instructions below. Installing Base does not select it in
   place of Small; choose `base` explicitly.
4. Open audio and select the desired passage, or leave no selection to process the
   full track where supported. Transcription always requires a selection.

The links pin published **v1 packs from release 0.3.0**, which also match 0.4.0's
unchanged trusted catalog. These are application-ready packs; upstream repositories
are linked separately for provenance and development. Once installed, all inference
is offline. You do not need Python, CUDA, an API account or separate CLAP downloads.

## Complete catalog

| Component | Installation | Activation and use |
| --- | --- | --- |
| [Spectral Gate](https://github.com/timsainb/noisereduce) | Included — nothing to download | Cleanup → Spectral Gate → Clean. Optionally select at least 0.1 s of noise, capture the profile, then select the speech to process. Enable Use noise profile. |
| [RNNoise](https://github.com/xiph/rnnoise) | Included — nothing to download | Cleanup → RNNoise → Clean. Included native library and weights; no separate download. |
| [Silero VAD](https://github.com/snakers4/silero-vad) | Included — nothing to download | Speech → Find speech on track. Click a colored region to listen or transcribe. VAD detects intervals; it does not clean audio. |
| DSP | Included — nothing to download | Cleanup → DSP → Clean. Reduces 50 Hz hum and low frequencies. No neural model is required. |
| [LUFS / Peak](https://github.com/csteinmetz1/pyloudnorm) | Included — nothing to download | Level → choose LUFS or Peak → set a target → Normalize. LUFS requires at least 0.4 s and supports up to 5 channels; Peak supports all 8. |
| [Whisper Base](https://huggingface.co/Systran/faster-whisper-base) | [Download ZIP](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-whisper-base-v1.zip) · 134 / 148 MB download / installed | Speech → base → choose the spoken language → select audio → Transcribe selection. A lighter model for quick drafts. |
| [Whisper Small](https://huggingface.co/Systran/faster-whisper-small) | [Download ZIP](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-whisper-small-v1.zip) · 448 / 486 MB download / installed | Speech → small → choose the spoken language → select audio → Transcribe selection. The default transcription choice; its pack must be installed. |
| [Whisper Large v3 Turbo](https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo) | [Download ZIP](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-whisper-large-v3-turbo-v1.zip) · 1.50 / 1.62 GB download / installed | Speech → large-v3-turbo → choose the spoken language → select audio → Transcribe selection. Requires more memory than Base or Small. |
| [DeepFilterNet3](https://github.com/Rikorose/DeepFilterNet) | [Download ZIP](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-DeepFilterNet3-v1.zip) · 8 / 9 MB download / installed | Cleanup → DeepFilterNet3 → Clean. Compare original A and processed B by listening. Uses 48 kHz internally; input sample rate and channel layout are preserved. |
| [FlexSED + CLAP](https://huggingface.co/Higobeatz/FlexSED/tree/main/ckpts) | [Download ZIP](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-flexsed-v1.zip) · 862 / 937 MB download / installed | Events → enter English descriptions such as Speech; Conversation; Whispering → choose channels and threshold → Find events. The pack includes the CLAP text encoder. Results are event markers, not cleaned audio or transcripts. |

## Listen, compare and export

Cleanup and normalization use the active **A/B** track and the selected passage
(or the whole track when nothing is selected). **A** always preserves the original;
**B** contains the processed copy. Silero searches the full active track; FlexSED
searches the selection or the full active track. Set the spoken language in
**Speech** independently of the interface language. Use **Listen** or Space to
audition the selection, **TXT** to save edited text, **SRT** for the model's original
timed segments, and **Export audio** for WAV/FLAC/OGG.

Spectral Gate is the `noisereduce` spectral gating implementation. Stationary mode
uses the captured noise profile; adaptive mode works without one. Avoid capturing
quiet speech as noise. After capturing a pause, select the speech you actually want
to process. Strong denoising can remove quiet words; compare A and B by listening.

FlexSED's CLAP component is a text encoder used for event descriptions. Its labels
are not a transcript, and neither component separates a target speaker. Keep event
descriptions in English even when using the Russian interface or Russian audio.
Changing the threshold changes which event markers are shown; scores are not
calibrated guarantees. UMX SE, ConvTasNet and PANNs are **not integrated**.

## Integrity, space and troubleshooting

The installer checks every model file against `assets/model-catalog.json` (path,
size, SHA-256), stages the result, then activates the completed revision. Cancelled
or failed installation leaves the previous revision active. Allow disk space for
both the ZIP and the extracted model; replacing a model also retains older files.
Use the release's `SHA256SUMS.txt` to verify downloaded ZIPs externally.

Arbitrary `.pth`, `.pt`, `.onnx`, Hugging Face snapshots, source ZIPs and VST plugins
cannot be imported as model packs. If a ZIP is rejected, download the exact linked
VoxLoom pack again. Do not rename a weight file to ZIP or edit the trusted catalog
to bypass verification. See [storage paths and troubleshooting](DOWNLOADS.md).

## Building or preparing weights from source

Follow [the platform build guide](BUILDING.md) first. From the repository root,
using its prepared Python environment:

```bash
# All three Whisper models and DeepFilterNet3
python tools/prepare_models.py
# Or just one Whisper model plus DeepFilterNet3
python tools/prepare_models.py --whisper base
python tools/prepare_models.py --whisper small
python tools/prepare_models.py --whisper large-v3-turbo
# FlexSED checkpoint plus the required CLAP text encoder and tokenizer
python tools/prepare_flexsed.py
# Validate all prepared models; build the five application-ready packs
python tools/doctor.py --models
python tools/build_model_packs.py
```

The three `--whisper` commands are alternatives, not mandatory extra steps after
the all-model command. `doctor --models` and pack creation require all five packs'
source models. Scripts pin revisions and verify weights; `prepare_flexsed.py`
converts the CLAP text encoder to the layout expected by the adapter. Source runs
read the `models` folder; compact installed applications use per-user storage.
Model provenance is recorded in [model-sources.json](../model-sources.json),
[prepare_flexsed.py](../tools/prepare_flexsed.py) and [license notices](LICENSES.md).
The CLAP upstream model is [laion/clap-htsat-unfused](https://huggingface.co/laion/clap-htsat-unfused).

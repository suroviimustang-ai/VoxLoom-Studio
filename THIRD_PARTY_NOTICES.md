# VoxLoom Studio components

**English** | [Русский](THIRD_PARTY_NOTICES.ru.md)

VoxLoom is a separate MatSoftAI project. Its interface was developed independently
using Keyboard_Lab's workflow principles: transport controls, a timeline,
selections and an event table. There are no direct runtime dependencies on
Keyboard_Lab or SpeechCleaner. The look-ahead limiter concept was adapted from
`SpeechCleaner-Avalonia/app/dsp/limiter.py`, adding linked gain control across
channels. The neural backend resampling approach also draws on SpeechCleaner.

Third-party libraries and weights retain their respective licenses. Available
license texts are collected from installed distributions into `licenses/`;
versions are recorded in `licenses/dependencies.json` and `requirements-lock.txt`.

- PyQt6: GPLv3 / Riverbank commercial license. This build uses the public GPL version.
- Qt: licenses of the relevant modules in the PyQt6-Qt6 distribution.
- noisereduce: MIT, https://github.com/timsainb/noisereduce
- DeepFilterNet: MIT / Apache-2.0, https://github.com/Rikorose/DeepFilterNet
- RNNoise: BSD-3-Clause, https://github.com/xiph/rnnoise
- pyrnnoise: https://github.com/pengzhendong/pyrnnoise
- Silero VAD: MIT, https://github.com/snakers4/silero-vad
- faster-whisper: MIT, https://github.com/SYSTRAN/faster-whisper
- Whisper: MIT, https://github.com/openai/whisper
- CTranslate2: MIT, https://github.com/OpenNMT/CTranslate2
- ONNX Runtime: MIT, https://github.com/microsoft/onnxruntime
- PyAV and bundled FFmpeg libraries: licenses of the specific binary distribution.
- NumPy, SciPy, soundfile, sounddevice, pyloudnorm and PyTorch: license texts in `licenses/`.

Redistribution requires the applicable corresponding source and notices for
copyleft components, including PyQt. This file does not relicense dependencies.

## FlexSED

FlexSED inference sources: JHU-LCAP/FlexSED, copyright (c) 2025 Jiarui Hai,
MIT; license retained in licenses/FlexSED/LICENSE. Checkpoint Higobeatz/FlexSED
is tagged MIT by its publisher. Pinned versions and SHA-256 are recorded in
licenses/FlexSED/provenance.json and models/flexsed/manifest.json.
The CLAP text encoder is derived from laion/clap-htsat-unfused; its model card
is retained in licenses/CLAP/README.md. Transformers is Apache-2.0 and einops MIT;
installed distribution notices are collected by tools/collect_licenses.py.


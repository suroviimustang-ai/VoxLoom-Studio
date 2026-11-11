# Licensing and source distribution

VoxLoom application code and original icons: **GPL-3.0-only**, copyright 2026
MatSoftAI and VoxLoom contributors. The complete license is at the repository
root. Commercial use is allowed subject to the license. There is no warranty.

The public repository contains source code and build instructions, not executable
releases, private audio or model weights. Preparation scripts download weights
from their publishers at build time. Those assets retain their own licenses.

| Component | License / origin |
| --- | --- |
| PyQt6 | GPLv3; [Riverbank terms](https://www.riverbankcomputing.com/software/pyqt/intro) |
| Qt | Component-specific Qt licenses; LGPL distribution supplied by PyQt wheels |
| FlexSED inference and published checkpoint | MIT; pinned JHU-LCAP/Higobeatz revisions |
| CLAP published model | Apache-2.0 according to the retained model card; upstream LAION code has its own CC0 license |
| Whisper / faster-whisper | MIT |
| Silero VAD | MIT |
| DeepFilterNet / DeepFilterLib | MIT / Apache-2.0; retain upstream notices |
| RNNoise | BSD-3-Clause; pyrnnoise packaging is Apache-2.0 |
| noisereduce | MIT |
| PyAV | BSD-3-Clause; bundled FFmpeg and codecs have separate licenses |
| PyTorch, NumPy, SciPy, audio libraries | Their upstream licenses, copied by the build tool |

`licenses/` contains collected notices. `licenses/dependencies.json` describes
the local build environment, including development dependencies; it is not a
claim that every installed package ships in the executable. The Windows lock
records the tested environment. Other operating systems resolve their own native
wheels using the documented requirements and installer script.

The vendored FlexSED source is unmodified and keeps its original MIT notice.
VoxLoom adapters are separate GPLv3 code. The application license does not replace
licenses of models or dependencies. Installing a model does not imply any rights
to redistribute its training data.

If you independently distribute a compiled application, include the licenses and
corresponding source required for that exact build, including copyleft libraries;
keep build recipes and exact versions accessible alongside the binary. A source
repository alone does not waive obligations for separately redistributed binaries.
See [GPLv3 section 6](https://www.gnu.org/licenses/gpl-3.0.html#section6).

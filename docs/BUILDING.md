# Build from source: Windows, macOS and Ubuntu

**English** | [Русский](BUILDING.ru.md)

The Git source tree contains code and documentation. Ready-made apps and optional
model packs are published separately in [GitHub Releases](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases).
Build natively on each target OS: PyInstaller is not a cross-compiler.
The full source-build commands below prepare all models; compact builds can skip
both model-preparation scripts and use the section below.

| Platform | Profile | Status |
| --- | --- | --- |
| Windows 10/11 x64 | Python 3.11 x64, CPU | Local full-EXE checks and native CI passed |
| macOS 15+ Apple Silicon | Python 3.11 ARM64, CPU | Native imports, tests and interface checks passed in CI |
| Ubuntu 24.04 x64 | Python 3.11, CPU | Native imports, tests and interface checks passed in CI |

The [GitHub Actions run on November 11, 2026](https://github.com/suroviimustang-ai/VoxLoom-Studio/actions/runs/42965738853)
passed 47 tests and six display configurations on each OS. CI uses Windows Server
2022, macOS 15 ARM64 and Ubuntu 24.04 x64. Full packaging and all-model checks were
completed locally on Windows. macOS/Linux bundles still require separate validation
after building them.

Intel Macs are outside this profile: PyTorch stopped providing macOS x86_64 wheels
after the 2.2 series, while this dependency set uses 2.8. Do not run ARM64 Python
through Rosetta or substitute an arbitrary older PyTorch version; that requires
separate validation of the whole pipeline. On Apple Silicon,
`python -c "import platform; print(platform.machine())"` must print `arm64`.
Windows/Linux ARM also requires separate validation.

We recommend 16 GB of RAM and 20–30 GB of free space for dependencies, models and
build outputs. An 8 GB system can run the app, but use short selections for demanding
operations. Run all commands from the root of the downloaded or cloned project.

## Windows

Install Python 3.11 x64 from python.org and Git. In PowerShell:

```powershell
py -3.11 -m venv .venv311
.venv311/Scripts/python tools/install_dependencies.py
.venv311/Scripts/python tools/doctor.py
.venv311/Scripts/python tools/prepare_models.py
.venv311/Scripts/python tools/prepare_flexsed.py
.venv311/Scripts/python tools/doctor.py --models
.venv311/Scripts/python main.py
```

Build a portable directory without Inno Setup:

```powershell
.venv311/Scripts/python tools/build_portable.py
```

Output: `dist-native/VoxLoom/VoxLoom.exe`; keep the **entire directory**.
To build your own installer, install Inno Setup 6 and an English Windows SAPI voice
for the speech fixture, then run `./build.ps1`. Do not commit the installer or weights.

## macOS 15+ (Apple Silicon)

This profile requires macOS 15 or later: the RNNoise 0.4.3 wheel for Mac targets
macOS 15 as its minimum version. Supporting older systems requires a separate build
and validation of that dependency.

Install Python 3.11 ARM64/universal2 from python.org or through uv. If needed,
install developer tools with `xcode-select --install`.

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
python tools/install_dependencies.py
python tools/doctor.py
python tools/prepare_models.py
python tools/prepare_flexsed.py
python tools/doctor.py --models
python main.py
python tools/build_portable.py
```

Output: `dist-native/VoxLoom.app`. CUDA is not used; Whisper selects a supported CPU
compute type. Apple Developer ID signing and notarization are not part of this local
build procedure. The resulting app is not guaranteed to run on macOS versions older
than those supported by the Python, Qt and wheels used to build it.

## Ubuntu 24.04 (x64)

Install the system libraries and pipx:

```bash
sudo apt update
sudo apt install -y git pipx build-essential pkg-config libportaudio2 libsndfile1 libegl1 libgl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0 libxcb-render-util0 libxcb-xinerama0 libxcb-randr0 libxcb-shape0 fonts-dejavu-core
pipx install uv
pipx ensurepath
```

Open a new terminal, then run:

```bash
uv python install 3.11
uv venv --python 3.11 --seed .venv311
source .venv311/bin/activate
python tools/install_dependencies.py
python tools/doctor.py
python tools/prepare_models.py
python tools/prepare_flexsed.py
python tools/doctor.py --models
python main.py
python tools/build_portable.py
```

Output: `dist-native/VoxLoom/VoxLoom` and its adjacent libraries. Launch it with
`./dist-native/VoxLoom/VoxLoom`. The build uses the host OS's glibc; supporting an
older Ubuntu release requires building and testing on that release.

## Checks and troubleshooting

```text
python -m pytest -q
python tools/check_startup.py
python tools/doctor.py --models
```

`doctor` checks imports for Qt, codecs, RNNoise, Torch/DeepFilterNet and CLAP in
separate processes, then checks model completeness. It does not evaluate model
quality. `check_startup` checks window bounds on simulated displays. The environment
variables `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` are suitable for checks
after model preparation; unset them before the initial downloads.

- **Windows QtWidgets/DLL errors:** use a clean environment with a consistent
  architecture. Do not copy arbitrary Qt/ICU DLLs into the application directory.
  The packaging pipeline includes native import validation.
- **Ubuntu xcb errors:** install the libraries listed above. For an XWayland session,
  try `QT_QPA_PLATFORM=xcb python main.py`. `offscreen` is intended for tests.
- **No output device:** check the default audio device and audio availability in
  your OS. Do not launch the Linux GUI with `sudo`.
- **No DeepFilterLib/RNNoise wheel:** check Python 3.11 and your architecture first.
  Manually compiling Rust/C dependencies is a separate procedure; do not mix
  unrelated DLLs or dylibs.
- **Out of memory:** choose Whisper base/small and a shorter selection.
- **Missing weights:** rerun both preparation scripts. `model-sources.json` pins
  Whisper revisions and checksums. Do not download arbitrary `.pth` files.

The Windows `requirements-lock.txt` is not a universal lock for macOS/Linux:
it contains Windows packages and CPU-wheel suffixes. Use `install_dependencies.py`
on other platforms and save your own `pip freeze` after successful validation.

GitHub Actions includes Windows, macOS ARM64 and Ubuntu jobs. Check the repository's
Actions page for current results; the first successful native run is linked above.
The `Native platform checks` workflow does not download large weights. The separate
release workflow installs all model packs and tests frozen inference with synthetic
speech; it does not evaluate transcription accuracy on real recordings.

Sources: [PyInstaller native builds](https://pyinstaller.org/en/stable/operating-mode.html),
[Python management with uv](https://docs.astral.sh/uv/guides/install-python/),
[Qt Linux dependencies](https://doc.qt.io/qt-6/linux-requirements.html),
[PyTorch Intel Mac wheel deprecation](https://dev-discuss.pytorch.org/t/pytorch-macos-x86-builds-deprecation-starting-january-2024/1690).

## Compact release packages

After installing dependencies in the native Python 3.11 environment:

```text
python tools/build_portable.py --compact
python tools/package_release.py
```

No model download is needed for a compact app build. The reviewed catalog in
`assets/model-catalog.json` is bundled with the app to verify optional ZIP packs.
Windows packaging requires Inno Setup 6 or later. Linux packaging downloads
appimagetool and its runtime from pinned releases and verifies their SHA-256 hashes
in `packaging/tool-sources.json`. macOS packaging uses the system `hdiutil`.

Outputs under `release-native/` are the Windows x64 `.exe`, Linux x86_64 `.AppImage`
or macOS ARM64 `.dmg`. Windows is unsigned; macOS is not Developer ID signed or
notarized. Packaging does not bypass OS security protections.

To create optional model packs, prepare the pinned models first, then run:

```text
python tools/build_model_packs.py
```

This checks every file against the committed catalog before writing the five ZIPs.
`--write-catalog` is a maintainer operation for reviewed upstream model updates,
not a workaround for a checksum mismatch. Users import packs using the
[download guide](DOWNLOADS.md). Installed model revisions remain available if a
replacement fails; previous revisions are retained on disk.

The `Native release packages` workflow builds on all three operating systems,
tests the frozen app and each installed/mounted distribution, and publishes the
draft release only when every platform passes and uploaded hashes match.

# Download and install

**English** | [Русский](DOWNLOADS.ru.md)

Open [GitHub Releases](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases)
and expand the release's **Assets** list. The desktop interface is currently Russian;
the language links in this repository switch the documentation.

| System | Download | Install or launch |
| --- | --- | --- |
| Windows 10/11 x64 | `VoxLoom-Studio-0.3.0-windows-x64.exe` | Run the installer; it installs for the current user |
| Ubuntu 24.04 x64 | `VoxLoom-Studio-0.3.0-linux-x86_64.AppImage` | Make it executable, then launch it |
| macOS 15+ Apple Silicon | `VoxLoom-Studio-0.3.0-macos-arm64.dmg` | Open the disk image and drag VoxLoom into Applications |

The first binary release is a preview. Windows binaries are unsigned and the macOS
app is not Developer ID signed or notarized. Consult the release reports for the
tested operating systems and exact source commit. Intel Macs are not supported by
this dependency profile.

On Linux:

```bash
chmod +x VoxLoom-Studio-0.3.0-linux-x86_64.AppImage
./VoxLoom-Studio-0.3.0-linux-x86_64.AppImage
```

If the system has no FUSE support, the runtime also supports:

```bash
APPIMAGE_EXTRACT_AND_RUN=1 ./VoxLoom-Studio-0.3.0-linux-x86_64.AppImage
```

## Optional model packs

The compact app includes Spectral Gate, DSP, RNNoise and Silero VAD. Download only
the additional ZIP packs you need from the **same release**:

| Pack | Purpose | Unpacked model size, approximately |
| --- | --- | --- |
| `VoxLoom-Models-whisper-base-v1.zip` | Fast transcription drafts | 148 MB |
| `VoxLoom-Models-whisper-small-v1.zip` | Balanced transcription; default model | 486 MB |
| `VoxLoom-Models-whisper-large-v3-turbo-v1.zip` | Larger transcription model | 1.62 GB |
| `VoxLoom-Models-DeepFilterNet3-v1.zip` | Neural speech enhancement | 9 MB |
| `VoxLoom-Models-flexsed-v1.zip` | FlexSED + CLAP sound-event detection | 937 MB |

1. Keep each ZIP intact; do not unpack it manually.
2. Open **Модели → Установить пакет…** (Models → Install pack) in VoxLoom.
3. Select one or more packs. The app checks file names, sizes and SHA-256 hashes
   against its built-in catalog before activating a model.
4. Wait for the installation status. For transcription, choose a model you installed
   in the **Речь** (Speech) tab. No restart or internet connection is required.

A failed or cancelled installation does not activate an incomplete revision.
When replacing a model, the previous revision remains on disk. Allow room for
the downloaded ZIP, the new extracted model and any older revisions.

Installed models are stored outside the application bundle:

- Windows: `%LOCALAPPDATA%/VoxLoom/models`.
- macOS: `~/Library/Application Support/VoxLoom/models`.
- Linux: `${XDG_DATA_HOME:-~/.local/share}/voxloom/models`.

For a custom location, set `VOXLOOM_MODEL_HOME` to an absolute path before launch.
Do not edit the `current.json` revision pointers manually. Older model packs may
be rejected if a future app version changes its trusted catalog; use matching packs.

## Verify downloads

Each release includes `SHA256SUMS.txt` and build reports. For example, on Windows:

```powershell
Get-FileHash -Algorithm SHA256 .\VoxLoom-Studio-0.3.0-windows-x64.exe
```

Compare the result with the matching filename in `SHA256SUMS.txt`. On Linux use
`sha256sum`, or `shasum -a 256` on macOS. The app also verifies model contents during
installation. Model outputs still require listening checks; integrity checks do
not establish transcription accuracy.

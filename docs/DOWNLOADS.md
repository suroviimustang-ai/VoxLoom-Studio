# Download and install

**English** | [Русский](DOWNLOADS.ru.md)

This guide covers **VoxLoom 0.3.0**. A normal installation needs no separate Python,
Git, Windows terminal, API keys or dedicated graphics card. The desktop interface
is currently Russian; the language links switch the documentation.

## 1. Download the app for your system

Use a direct link below. The same files are in **Assets** on the
[0.3.0 release page](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/tag/v0.3.0).
The **Source code** archives and `.json` build reports are not needed for installation.

| System | Download | Install or launch |
| --- | --- | --- |
| Windows 10/11 x64 | [Download EXE · 300 MB](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Studio-0.3.0-windows-x64.exe) | Open the EXE, finish the installer, then launch VoxLoom from Start |
| Ubuntu 24.04 x64 | [Download AppImage · 442 MB](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Studio-0.3.0-linux-x86_64.AppImage) | Make the file executable, then launch it |
| macOS 15+ Apple Silicon | [Download DMG · 289 MB](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Studio-0.3.0-macos-arm64.dmg) | Open the image, drag VoxLoom into Applications, then launch it from Applications |

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

## 2. Choose your models

**Whisper Small is enough for your first transcript.** It converts speech, including
Russian, into text and is already selected by default in the app. Optionally add
DeepFilterNet3 for neural speech cleanup. Other packs can be installed later.

Version 0.3.0 has no built-in model downloader: open a link below in your browser,
save the ZIP, then import it into the app. The same model packs work on Windows,
macOS and Linux.

The compact app includes Spectral Gate, DSP, RNNoise and Silero VAD. Download only
the additional ZIP packs you need from the **same release**:

| Download pack | Purpose | Download / installed size, approximately |
| --- | --- | --- |
| [Whisper Small](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-whisper-small-v1.zip) | Start here: speech to text | 448 / 486 MB |
| [DeepFilterNet3](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-DeepFilterNet3-v1.zip) | Optional neural speech cleanup | 8 / 9 MB |
| [Whisper Base](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-whisper-base-v1.zip) | A lighter transcription option | 134 / 148 MB |
| [Whisper Large v3 Turbo](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-whisper-large-v3-turbo-v1.zip) | A larger transcription model | 1.50 / 1.62 GB |
| [FlexSED + CLAP](https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/VoxLoom-Models-flexsed-v1.zip) | Find sounds by description; optional for ordinary speech detection and transcription | 862 / 937 MB |

## 3. Install the downloaded packs

1. Keep each ZIP intact; do not unpack it manually.
2. Open **Модели → Установить пакет…** (Models → Install pack) in VoxLoom.
3. Select one or more packs. The app checks file names, sizes and SHA-256 hashes
   against its built-in catalog before activating a model.
4. Wait for the installation status. For transcription, choose a model you installed
   in the **Речь** (Speech) tab. No restart or internet connection is required.
5. Reopen **Модели**. The starter pack should show **Whisper small: готова** (ready),
   and the cleanup pack **DeepFilterNet3: установлена** (installed), if selected.
   Other models can remain uninstalled.

## 4. Get your first transcript

1. Open a short recording with clear speech using **Ctrl+O**, or drag it into the window.
2. Keep the original track **A** active. Open **Речь** (Speech), then click
   **Найти речь на дорожке** (Find speech on track). Colored intervals should appear.
3. Click an interval or select a short passage with the mouse. Choose **small** and
   **Русский** for Russian or **English** for English, then **Распознать выделение**
   (Transcribe selection).
4. Wait for the text, check it by listening, and save it with **TXT**.

Cleanup before transcription is optional. To compare results, open **Очистка**
(Cleanup), choose RNNoise or your installed DeepFilterNet3, then process the audio.
The original stays on **A**, the result is on **B**. Listen to both; choose **B**
to transcribe the processed audio.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| Model not installed | Import its ZIP using Models. In the Speech tab, select that installed model: installing Base does not automatically replace Small |
| Transcription button disabled | Open audio, then select a speech interval or passage; wait for other processing to finish |
| ZIP rejected or checksum mismatch | Download the pack again from release 0.3.0. Keep the original ZIP intact; an app source archive is not a model pack |
| Not enough disk space | Allow space for the app, the downloaded ZIP and the extracted model; model sizes are listed above |
| Processing is slow or memory runs out | Start with a short selection; install Base and select `base` instead of a larger model |
| Operating system blocks launch | This preview has no Windows signature or Apple notarization. See [Microsoft's guidance](https://support.microsoft.com/en-gb/windows/security/windows-security/app-browser-control-in-the-windows-security-app) or [Apple's guidance](https://support.apple.com/en-us/102445). This guide does not require disabling system protections |

If you still need help, [open an issue](https://github.com/suroviimustang-ai/VoxLoom-Studio/issues)
with your OS and app versions, the selected model and the exact error message.
A description is usually enough; do not attach private recordings or transcripts.

## Model storage and updates

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

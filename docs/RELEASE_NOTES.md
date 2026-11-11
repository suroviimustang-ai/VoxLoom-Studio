# VoxLoom Studio 0.3.0 — compact native packages

Preview release for Windows x64, Ubuntu 24.04 x86_64 and macOS 15+ Apple Silicon.

- Install the Windows **EXE**, run the Linux **AppImage**, or open the macOS **DMG**.
- Spectral Gate, DSP, RNNoise and Silero VAD are included in the compact app.
- Download optional **model ZIPs** and import them through **Модели → Установить пакет…**.
  Whisper base/small/turbo, DeepFilterNet3 and FlexSED + CLAP are available separately.
- After model installation, audio processing is local and works offline.
- English documentation is the default; **English | Русский** links switch the docs.
  The desktop interface remains Russian.

[English installation guide](https://github.com/suroviimustang-ai/VoxLoom-Studio/blob/v0.3.0/docs/DOWNLOADS.md) ·
[Инструкция на русском](https://github.com/suroviimustang-ai/VoxLoom-Studio/blob/v0.3.0/docs/DOWNLOADS.ru.md)

Every published platform package must pass native bundle checks, installation of
all five model packs, frozen GUI/codec/model checks and an installed or mounted
distribution check. Build reports identify the exact source commit and checks.
`SHA256SUMS.txt` covers the applications, model packs and source archive.

Windows binaries are unsigned. The macOS app is not Developer ID signed or
notarized; Intel Mac builds are not included. Recognition results are model
predictions and must be checked by listening.

GPL-3.0-only application sources and build recipes are included in the source
archive and repository tag. Dependencies and model weights retain their original
licenses; notices are included in the app and model packs.

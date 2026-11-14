# VoxLoom Studio 0.4.1 — Classic desktop menus

Preview for Windows x64, Ubuntu 24.04 x86_64 and macOS 15+ Apple Silicon.

- Classic File, Edit, View, Process and About menus with live EN/RU switching.
- Menu commands follow audio, selection and busy states.
- Ctrl+Alt+Z undoes audio processing; Ctrl+Z keeps its native text-editor behavior.
- English on first launch on every platform; switch to Russian in the top bar.
  The choice persists. Switching preserves audio, selections and transcript edits.
- Transcription language is a separate setting in the Speech tab.
- Models now lists every built-in component and all five optional packs, with
  download links, installation status and activation instructions in both languages.
- Documentation is maintained in English; separate `*.ru.md` files are removed.
- The v1 model packs from 0.3.0 remain compatible. Existing installations keep
  their model storage; no new weights are needed for the language update.

[Installation](https://github.com/suroviimustang-ai/VoxLoom-Studio/blob/v0.4.1/docs/DOWNLOADS.md) ·
[All modules](https://github.com/suroviimustang-ai/VoxLoom-Studio/blob/v0.4.1/docs/MODULES.md)

Every platform package must pass native tests, both-language layout checks,
installation of all five packs, frozen GUI/model checks and an installed or mounted
distribution check. Build reports identify the source commit and completed checks.
`SHA256SUMS.txt` covers applications, model packs and sources. The speech fixture
is synthetic test audio and contains no user recordings.

Windows binaries are unsigned. The macOS app is not Developer ID signed or
notarized. Intel Mac builds are not included. Verify model outputs by listening.

Application sources are GPL-3.0-only. Dependencies and weights retain their original
licenses, included in the app and model packs.

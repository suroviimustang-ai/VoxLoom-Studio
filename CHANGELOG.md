# Changelog

## 0.4.1

- Add classic File, Edit, View, Process and About menus in English and Russian.
- Share menu commands and enabled states with the workspace controls.
- Preserve native text-editor undo; use Ctrl+Alt+Z to undo audio processing.
- Keep English CLAP queries and event names unchanged when switching languages.

## 0.4.0

- English-first UI with persistent live Russian switching on all platforms.
- Localized splash, controls, tooltips, errors and worker responses.
- Complete module catalog with verified download links and activation instructions.
- English-only Markdown documentation; removed separate Russian files.
- Added catalog/translation coverage, worker-language and session-preservation checks.
- Select a complete current x64 Visual C++ runtime for all Windows DLL copies,
  preventing Qt's older runtime from shadowing ONNX dependencies.


## 0.3.0

- Add compact Windows EXE, Linux AppImage and Apple Silicon macOS DMG builders.
- Distribute five optional model packs with a trusted file-hash catalog.
- Install packs through the Models dialog with atomic activation and rollback on failure.
- Validate native bundles, model installation and installed or mounted distributions
  before publishing release assets with SHA-256 checksums.
- Make English the default documentation language and retain Russian translations.

## 0.2.2

- Standardize owned Python and PowerShell sources, pin formatter/analyzer versions,
  and add EditorConfig, Git line-ending rules, coding standards and quality CI.

- Remove whole-window scrolling and adapt spacing to the available logical size.
- Move normalization into its own tool tab; retain readable control text.
- Switch results between side-by-side panels and tabs on narrow windows.
- Keep filenames and long progress messages within their row, with full tooltips.
- Check all tool pages, busy controls and panel state across six display profiles.

## 0.2.1

- Bundle Whisper base, small and large-v3-turbo; remove runtime downloads.
- Add startup branding and maximize to the current screen work area.
- Keep the window within small/high-DPI displays with scrollable content.
- Recover from malformed worker output and locked temporary files.
- Preserve existing TXT/SRT/JSON exports when replacement fails.
- Close disconnected audio devices and add bounded local diagnostics.
- Prepare GPLv3 public sources, CI and pinned model manifests.
- Add native RNNoise library selection and source-build profiles for Windows,
  Apple Silicon macOS and Ubuntu; non-Windows execution still needs native validation.

## 0.2.0

- Add offline FlexSED + CLAP event detection, colored events, per-channel
  analysis and selection-to-Whisper workflow.

## 0.1.0

- Add A/B restoration, Spectral Gate, RNNoise, DeepFilterNet3, Silero VAD,
  Whisper, normalization and audio/text export.

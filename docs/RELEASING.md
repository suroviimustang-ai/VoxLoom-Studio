# Public source release procedure

The GitHub project distributes source code and build instructions. Do not attach
EXE files, compiled bundles or neural weights to the public repository/release.

1. Check the native dependency profile and instructions in BUILDING.md.
2. Run `tools/prepare_models.py` and `tools/prepare_flexsed.py` during preparation.
3. Run `build.ps1`: unit tests, license collection, PyInstaller, DLL import
   validation, packaged GUI/model checks, packaged codec/ASR checks, Inno Setup.
4. Run `tools/finalize_flexsed_release.py` to hash the installer and bundled weights.
5. Generate the allowlisted public source export and review its manifest.
6. Publish the reviewed source tree, notices and build instructions, and tag the
   version. The source archive and SOURCE_MANIFEST.json can be attached to a release.
7. Keep generated models, binaries, private material and local verification logs
   out of Git. Individual users build for their own OS using BUILDING.md.

The GitHub CI configuration runs synthetic unit/recovery/display tests, without private recordings
or large neural weights. Full offline-model and frozen-EXE checks run locally
before release. CI success and a clean-machine installer test are different checks.
Do not label a platform as tested until its native CI run actually succeeds.

Enable private vulnerability reporting in GitHub settings. Do not commit audio,
transcripts, model weights, local logs, virtual environments or build directories.
Publishing is a separate action from generating the local release files.

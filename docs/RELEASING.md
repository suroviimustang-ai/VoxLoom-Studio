# Release procedure

Source history contains code, build recipes, documentation and a trusted model
catalog. Publish compiled applications and model ZIPs as GitHub Release assets,
never as Git blobs. Do not publish private recordings, transcripts or local logs.

## Native preview releases

1. Update the version in `pyproject.toml`, `voxloom/__init__.py` and the installer
   recipes. Update `CHANGELOG.md`, `docs/RELEASE_NOTES.md` and download filenames.
2. Review model revisions and checksums. For a deliberate model update, prepare
   pinned weights, review every changed hash, then regenerate the catalog with
   `python tools/build_model_packs.py --write-catalog`.
3. Run code-quality checks, tests, startup display checks and the allowlisted
   source exporter. Update `SOURCE_MANIFEST.json` from the new export.
4. Run the **Native release packages** workflow on the intended commit. A push
   changing the release workflow or application version on `main` also starts it.
5. The model job creates a **draft** release and uploads verified packs and the
   source archive. The native matrix builds compact Windows EXE, Linux AppImage
   and macOS ARM64 DMG packages on their respective operating systems.
6. A Windows job generates a synthetic SAPI speech fixture and uploads it to the
   same draft. Each platform verifies its checksum, installs the model ZIPs through the frozen worker, runs the GUI
   and offline codec/model checks, then verifies the final installed/mounted package.
7. Only after all platform jobs succeed does the publisher compare uploaded hashes
   against reports from the same commit and publish the preview release.

The workflow uses the repository-scoped `GITHUB_TOKEN`; it needs no personal token
or signing secrets. Its build jobs need release write permission to access the draft.
Already published versions are not overwritten. Bump the version for a new release;
rerunning an unpublished draft is supported.

## Local builders

See [BUILDING.md](BUILDING.md#compact-release-packages). The core commands are:

```text
python tools/build_portable.py --compact
python tools/package_release.py
python tools/build_model_packs.py
```

The last command requires prepared weights matching the committed catalog.
The application remains offline: importing a downloaded model pack does not
contact a server. Source tests do not replace frozen-app or installer checks.

The full model-bundled Windows pipeline remains available through `build.ps1`
and `tools/finalize_flexsed_release.py` for local builds. Its large installer may
exceed GitHub's per-file size limit; public releases use compact apps and separate
packs instead.

Keep original third-party notices and corresponding-source directions with exact
dependency versions. Do not label signed/notarized or untested platforms as validated.

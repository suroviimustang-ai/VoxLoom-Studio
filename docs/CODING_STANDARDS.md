# VoxLoom coding standards


These rules apply to application-owned code, tests, analysis scripts and build tools.
Generated results, builds, environments and weights are excluded.
`voxloom/_vendor` remains a pinned copy of third-party code: update it separately,
reviewing provenance and licenses, rather than applying bulk formatting.

## Python 3.11

- Use PEP 8 and Ruff formatting: four spaces, double quotes, LF and an 88-character
  target line length, following the project's Black-compatible convention.
  Do not manually split user-facing strings or URLs solely to meet that target.
- Use one statement per line. Group imports into the standard library, third-party
  packages and project modules. Remove unused imports.
- Ruff checks E4/E7/E9, Pyflakes (`F`), import order (`I`) and target-version
  syntax (`UP`). Do not apply unsafe automatic fixes.
- Use `snake_case` for functions and variables, `PascalCase` for classes, and
  `UPPER_SNAKE_CASE` for constants. Qt overrides such as `paintEvent`,
  `resizeEvent` and `setText` retain their API names. New public interfaces
  should have clear type annotations and purpose descriptions.
- Configure the environment before importing native libraries. Deferred ASR
  imports after expensive DSP operations in two local utilities have targeted
  `noqa: E402` comments explaining why. PyInstaller-provided globals are allowed
  in `VoxLoom.spec`.
- Keep network requests and heavy processing out of the GUI thread. Preserve
  cancellation and the immutable original track.

In the active project environment:

```text
python -m pip install -r requirements-dev.txt
python tools/check_style.py
python tools/check_style.py --fix
```

The Ruff version is pinned separately from application dependencies. Always review
automatic changes and run the relevant tests.

## PowerShell

Use PSScriptAnalyzer 1.24.0 and `PSScriptAnalyzerSettings.psd1`: four spaces,
consistent braces, spacing and command casing, and the standard error checks.
Use CRLF and UTF-8 BOM for `.ps1`/`.psd1` files to support Windows PowerShell 5.1.
Prefix task-specific variables with `task`, pass paths through `-LiteralPath`,
and explicitly check external program exit codes.

```powershell
Save-Module -Name PSScriptAnalyzer -RequiredVersion 1.24.0 -Path .tooling -Repository PSGallery -Force
./tools/check_powershell.ps1
./tools/check_powershell.ps1 -Fix
```

The check does not download the module automatically. It uses the local copy in
`.tooling` or an installed version 1.24.0.

## Configuration and change validation

`.editorconfig` defines encoding, indentation and line endings: two spaces for
YAML/JSON and four for Python/PowerShell/TOML. `.gitattributes` fixes Git line
endings. Inno Setup `.iss` files retain their directive names and section order;
the installer compiler validates their syntax. Do not reformat license texts or
third-party resources.

```text
python -m pytest -q
python tools/check_startup.py
```

GitHub Actions checks Python and PowerShell in the separate `code-quality` job.
Packaging changes require packaged-application validation through `build.ps1`.

References: [Ruff](https://docs.astral.sh/ruff/configuration/),
[PSScriptAnalyzer](https://learn.microsoft.com/en-us/powershell/utility-modules/psscriptanalyzer/using-scriptanalyzer).

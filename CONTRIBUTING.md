# Contributing

Use Python 3.11 and the native platform instructions in docs/BUILDING.md. Development is
under GPL-3.0-only; contributions must be compatible with that license.

1. Reproduce issues with synthetic audio or audio you are allowed to share.
2. Keep the original track immutable and heavy computation in cancellable workers.
3. Add regression tests for behavior changes and recovered failures.
4. Follow [coding standards](docs/CODING_STANDARDS.md): install `requirements-dev.txt`,
   run `python tools/check_style.py` and `./tools/check_powershell.ps1`.
5. Run `python -m pytest -q` and `python tools/check_startup.py`.
6. For packaged changes run `build.ps1`; source tests do not validate native DLLs.

Describe the problem, resulting behavior and validation. Never submit private
recordings, transcripts, tokens, weights, environments or unreviewed logs.
Preserve the pinned model revisions and checksums. Do not execute untrusted
model pickles. Accuracy claims require a reproducible evaluation and reference text.

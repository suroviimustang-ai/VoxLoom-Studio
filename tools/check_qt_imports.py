"""Locate missing PE imports against the actual packaged DLL search paths."""

import argparse
import json
from pathlib import Path

import pefile

parser = argparse.ArgumentParser()
parser.add_argument("target", nargs="?", default="PyQt6/QtWidgets.pyd")
parser.add_argument("--root", default="dist/VoxLoom/_internal")
args = parser.parse_args()
root = Path(args.root).resolve()
locations = [root, root / "PyQt6/Qt6/bin", root / "PyQt6", Path("C:/Windows/System32")]
checked = set()
errors = []


def inspect(path):
    if path in checked or "Windows" in path.parts:
        return
    checked.add(path)
    pe = pefile.PE(str(path), fast_load=True, max_symbol_exports=65536)
    pe.parse_data_directories(
        directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]]
    )
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
        name = entry.dll.decode()
        if name.lower().startswith(("api-ms-", "ext-ms-")):
            continue
        target = next(
            (folder / name for folder in locations if (folder / name).exists()), None
        )
        if target is None:
            errors.append(dict(binary=str(path), dependency=name, missing_dll=True))
            continue
        library = pefile.PE(str(target), fast_load=True, max_symbol_exports=65536)
        library.parse_data_directories(
            directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_EXPORT"]]
        )
        symbols = getattr(library, "DIRECTORY_ENTRY_EXPORT", None)
        exports = (
            {item for s in symbols.symbols for item in [s.name, s.ordinal]}
            if symbols
            else set()
        )
        missing = [
            s.name.decode() if s.name else s.ordinal
            for s in entry.imports
            if (s.name if s.name else s.ordinal) not in exports
        ]
        if missing:
            errors.append(
                dict(
                    binary=str(path),
                    dependency=str(target),
                    missing_symbols=missing[:20],
                )
            )
        library.close()
        inspect(target)
    pe.close()


target = root / args.target
locations.insert(1, target.parent)
inspect(target)
Path("artifacts/qt-import-check.json").write_text(
    json.dumps(errors, indent=2), encoding="utf-8"
)
print(json.dumps(errors, indent=2))
raise SystemExit(1 if errors else 0)

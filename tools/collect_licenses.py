import json
import shutil
from importlib.metadata import distributions
from pathlib import Path

root = Path(__file__).resolve().parents[1]
destination = root / "licenses"
destination.mkdir(exist_ok=True)
manifest = []
for package in distributions():
    name = package.metadata["Name"]
    manifest.append(
        {
            "name": name,
            "version": package.version,
            "license": package.metadata.get("License-Expression")
            or package.metadata.get("License", ""),
            "home": package.metadata.get("Home-page", ""),
        }
    )
    for file in package.files or []:
        if any(
            token in file.name.lower() for token in ["license", "copying", "notice"]
        ):
            source = Path(package.locate_file(file))
            if source.is_file() and source.suffix not in [
                ".py",
                ".pyc",
                ".dll",
                ".pyd",
            ]:
                target = destination / name / str(file).replace("..", "_")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
(destination / "dependencies.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
)
print(f"Collected notices for {len(manifest)} installed distributions")

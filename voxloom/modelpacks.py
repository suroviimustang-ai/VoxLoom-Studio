"""Install verified model archives without exposing incomplete model directories."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from .files import write_text_atomic
from .i18n import tr


def load_catalog() -> dict:
    from .processing import resource_root

    path = resource_root() / "assets/model-catalog.json"
    return json.loads(path.read_text(encoding="utf-8"))["models"]


def installed_directory(root: Path, name: str) -> Path | None:
    """Resolve only app-owned revision names, never arbitrary paths from JSON."""
    try:
        revision = json.loads((root / name / "current.json").read_text("utf-8"))[
            "revision"
        ]
        if not isinstance(revision, str) or not re.fullmatch(
            r"revision-[0-9a-f]{32}", revision
        ):
            return None
        target = root / name / revision
        if target.is_dir() and not target.is_symlink():
            return target
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def install_pack(
    archive: Path,
    *,
    catalog: dict | None = None,
    models_root: Path | None = None,
    staging_root: Path | None = None,
) -> str:
    """Trust the app's catalog, not hashes supplied by an imported ZIP archive."""
    from .processing import writable_models

    catalog = load_catalog() if catalog is None else catalog
    models_root = writable_models() if models_root is None else models_root
    with zipfile.ZipFile(archive) as zf:
        members = zf.infolist()
        names = [member.filename for member in members]
        if len(set(names)) != len(names) or "pack.json" not in names:
            raise ValueError(
                tr("Invalid model pack: duplicate files or missing manifest.")
            )
        header = zf.getinfo("pack.json")
        if header.file_size > 65536:
            raise ValueError(tr("The model pack manifest is too large."))
        metadata = json.loads(zf.read(header))
        if not isinstance(metadata, dict):
            raise ValueError(tr("Invalid model pack manifest."))
        name = metadata.get("model")
        if (
            metadata.get("schema") != 1
            or not isinstance(name, str)
            or name not in catalog
        ):
            raise ValueError(
                tr("This model pack is not supported by this version of VoxLoom.")
            )
        expected = catalog[name]["files"]
        if set(names) != {"pack.json", *expected}:
            raise ValueError(
                tr("The pack contents do not match the trusted model catalog.")
            )
        for member in members:
            path = PurePosixPath(member.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in member.filename
                or ":" in member.filename
                or member.is_dir()
                or stat.S_ISLNK(member.external_attr >> 16)
                or member.flag_bits & 1
            ):
                raise ValueError(tr("Invalid path or file type in the model pack."))
            if (
                member.filename != "pack.json"
                and member.file_size != expected[member.filename]["bytes"]
            ):
                raise ValueError(tr("The model file size does not match the catalog."))
        parent = models_root / name
        parent.mkdir(parents=True, exist_ok=True)
        required = sum(item["bytes"] for item in expected.values())
        if shutil.disk_usage(parent).free < required + 64 * 1024**2:
            raise OSError(
                tr("There is not enough free space to install the model pack.")
            )
        revision = "revision-" + uuid.uuid4().hex
        destination = parent / revision
        with tempfile.TemporaryDirectory(
            prefix=".install-", dir=staging_root or parent
        ) as temporary:
            stage = Path(temporary)
            for filename, spec in expected.items():
                target = stage / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                checksum = hashlib.sha256()
                length = 0
                with zf.open(filename) as source, target.open("xb") as output:
                    while chunk := source.read(1024**2):
                        length += len(chunk)
                        if length > spec["bytes"]:
                            raise ValueError(
                                tr("The model file exceeds the allowed size.")
                            )
                        checksum.update(chunk)
                        output.write(chunk)
                if length != spec["bytes"] or checksum.hexdigest() != spec["sha256"]:
                    raise ValueError(tr("Model checksum mismatch: {v0}", v0=filename))
            os.replace(stage, destination)
            try:
                write_text_atomic(
                    parent / "current.json", json.dumps({"revision": revision})
                )
            except BaseException:
                # This directory was created by this invocation; the old pointer is intact.
                shutil.rmtree(destination)
                raise
    return name

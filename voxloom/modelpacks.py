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
                "Некорректный пакет моделей: повторяющиеся файлы или нет описания."
            )
        header = zf.getinfo("pack.json")
        if header.file_size > 65536:
            raise ValueError("Описание пакета моделей слишком велико.")
        metadata = json.loads(zf.read(header))
        if not isinstance(metadata, dict):
            raise ValueError("Некорректное описание пакета моделей.")
        name = metadata.get("model")
        if (
            metadata.get("schema") != 1
            or not isinstance(name, str)
            or name not in catalog
        ):
            raise ValueError(
                "Этот пакет моделей не поддерживается данной версией VoxLoom."
            )
        expected = catalog[name]["files"]
        if set(names) != {"pack.json", *expected}:
            raise ValueError(
                "Состав пакета не совпадает с проверенным каталогом моделей."
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
                raise ValueError("Недопустимый путь или тип файла в пакете моделей.")
            if (
                member.filename != "pack.json"
                and member.file_size != expected[member.filename]["bytes"]
            ):
                raise ValueError("Размер файла модели не совпадает с каталогом.")
        parent = models_root / name
        parent.mkdir(parents=True, exist_ok=True)
        required = sum(item["bytes"] for item in expected.values())
        if shutil.disk_usage(parent).free < required + 64 * 1024**2:
            raise OSError("Недостаточно места для установки пакета моделей.")
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
                            raise ValueError("Превышен допустимый размер файла модели.")
                        checksum.update(chunk)
                        output.write(chunk)
                if length != spec["bytes"] or checksum.hexdigest() != spec["sha256"]:
                    raise ValueError(f"Контрольная сумма модели не совпала: {filename}")
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

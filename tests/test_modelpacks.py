import hashlib
import json
import stat
import zipfile

import pytest

from voxloom import modelpacks, processing


def test_pack_text_is_identical_on_windows_and_unix(tmp_path):
    from tools.build_model_packs import text_bytes

    path = tmp_path / "config.json"
    path.write_bytes(b'{\r\n  "size": 1\r\n}\r\n')
    windows = text_bytes(path)
    path.write_bytes(b'{\n  "size": 1\n}\n')
    assert text_bytes(path) == windows
    binary = tmp_path / "model.bin"
    binary.write_bytes(b"\r\n")
    assert text_bytes(binary) is None


def make_pack(tmp_path, data=b"verified model", extra=None, header=None):
    archive = tmp_path / "pack.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(
            "pack.json",
            json.dumps(
                header if header is not None else {"schema": 1, "model": "whisper-base"}
            ),
        )
        zf.writestr("model.bin", data)
        if extra:
            zf.writestr(*extra)
    catalog = {
        "whisper-base": {
            "files": {
                "model.bin": {
                    "bytes": len(b"verified model"),
                    "sha256": hashlib.sha256(b"verified model").hexdigest(),
                }
            }
        }
    }
    return archive, catalog


def test_verified_install_and_replacement_keep_previous_revision(tmp_path):
    archive, catalog = make_pack(tmp_path)
    root = tmp_path / "models"
    modelpacks.install_pack(archive, catalog=catalog, models_root=root)
    original = modelpacks.installed_directory(root, "whisper-base")
    assert (original / "model.bin").read_bytes() == b"verified model"
    modelpacks.install_pack(archive, catalog=catalog, models_root=root)
    assert modelpacks.installed_directory(root, "whisper-base") != original
    assert original.is_dir()


def test_corrupt_pack_does_not_replace_existing_model(tmp_path):
    archive, catalog = make_pack(tmp_path)
    root = tmp_path / "models"
    modelpacks.install_pack(archive, catalog=catalog, models_root=root)
    original = modelpacks.installed_directory(root, "whisper-base")
    archive, _ = make_pack(tmp_path, data=b"tampered model")
    with pytest.raises(ValueError):
        modelpacks.install_pack(archive, catalog=catalog, models_root=root)
    assert modelpacks.installed_directory(root, "whisper-base") == original
    assert not list((root / "whisper-base").glob(".install-*"))


@pytest.mark.parametrize(
    "extra", [("../escape", b"bad"), ("model.bin", b"bad"), ("unknown", b"bad")]
)
def test_unexpected_and_duplicate_members_rejected(tmp_path, extra):
    archive, catalog = make_pack(tmp_path, extra=extra)
    with pytest.raises(ValueError):
        modelpacks.install_pack(
            archive, catalog=catalog, models_root=tmp_path / "models"
        )
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize(
    "header",
    [[], {"schema": 2, "model": "whisper-base"}, {"schema": 1, "model": "../outside"}],
)
def test_invalid_metadata_rejected(tmp_path, header):
    archive, catalog = make_pack(tmp_path, header=header)
    with pytest.raises(ValueError):
        modelpacks.install_pack(
            archive, catalog=catalog, models_root=tmp_path / "models"
        )


def test_symlink_model_rejected(tmp_path):
    archive, catalog = make_pack(tmp_path)
    info = zipfile.ZipInfo("model.bin")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("pack.json", json.dumps({"schema": 1, "model": "whisper-base"}))
        zf.writestr(info, b"verified model")
    with pytest.raises(ValueError, match="file type"):
        modelpacks.install_pack(
            archive, catalog=catalog, models_root=tmp_path / "models"
        )


def test_pointer_failure_preserves_previous_model(tmp_path, monkeypatch):
    archive, catalog = make_pack(tmp_path)
    root = tmp_path / "models"
    modelpacks.install_pack(archive, catalog=catalog, models_root=root)
    original = modelpacks.installed_directory(root, "whisper-base")

    def fail(*_):
        raise PermissionError("locked pointer")

    monkeypatch.setattr(modelpacks, "write_text_atomic", fail)
    with pytest.raises(PermissionError):
        modelpacks.install_pack(archive, catalog=catalog, models_root=root)
    assert modelpacks.installed_directory(root, "whisper-base") == original
    assert list((root / "whisper-base").glob("revision-*")) == [original]


def test_path_override_and_pointer_do_not_escape(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXLOOM_MODEL_HOME", str(tmp_path))
    assert processing.writable_models() == tmp_path
    path = tmp_path / "whisper-base"
    path.mkdir()
    (path / "current.json").write_text('{"revision":"../../outside"}')
    assert modelpacks.installed_directory(tmp_path, "whisper-base") is None
    monkeypatch.setenv("VOXLOOM_MODEL_HOME", "relative")
    with pytest.raises(ValueError, match="absolute"):
        processing.writable_models()

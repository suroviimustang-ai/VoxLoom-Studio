import pytest

from tools.windows_runtime import RUNTIME_NAMES, select_runtime


def runtime(directory, versions, machine=0x8664):
    directory.mkdir()
    info = {}
    for name, version in zip(RUNTIME_NAMES, versions):
        path = directory / name
        path.write_bytes(b"fixture")
        info[path] = (machine, (14, version, 0, 0))
    return info


def test_newer_complete_runtime_wins_independent_of_collection_order(tmp_path):
    old, current, incomplete = [tmp_path / name for name in ("qt", "system", "partial")]
    info = runtime(old, [26, 26, 26])
    info.update(runtime(current, [44, 44, 44]))
    info.update(runtime(incomplete, [99]))
    for paths in ([old, current, incomplete], [incomplete, current, old]):
        selected = select_runtime(paths, inspect=lambda path: info[path])
        assert {path.parent for path in selected.values()} == {current}


def test_runtime_does_not_mix_directories_or_accept_wrong_architecture(tmp_path):
    mixed, coherent, x86 = [tmp_path / name for name in ("mixed", "coherent", "x86")]
    info = runtime(mixed, [50, 20, 20])
    info.update(runtime(coherent, [44, 44, 44]))
    info.update(runtime(x86, [99, 99, 99], machine=0x14C))
    selected = select_runtime([mixed, coherent, x86], inspect=lambda path: info[path])
    assert {path.parent for path in selected.values()} == {coherent}


def test_incomplete_runtime_fails_before_packaging(tmp_path):
    runtime(tmp_path / "partial", [44, 44])
    with pytest.raises(RuntimeError, match="complete x64"):
        select_runtime(
            [tmp_path / "partial"], inspect=lambda _: (0x8664, (14, 44, 0, 0))
        )

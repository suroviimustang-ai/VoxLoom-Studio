import pytest

from tools.install_dependencies import commands
from voxloom.rnnoise_native import library_name


def test_windows_and_linux_cpu_index_not_used_on_macos():
    for system in ("Windows", "Linux"):
        assert "https://download.pytorch.org/whl/cpu" in commands(system, "x86_64")[1]
    assert "--index-url" not in commands("Darwin", "arm64")[1]
    with pytest.raises(RuntimeError, match="Intel"):
        commands("Darwin", "x86_64")


def test_native_rnnoise_names_and_unsupported_platform():
    assert library_name("win32") == "rnnoise.dll"
    assert library_name("darwin") == "librnnoise.dylib"
    assert library_name("linux") == "librnnoise.so"
    with pytest.raises(RuntimeError):
        library_name("unsupported")

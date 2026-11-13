"""Select one complete x64 Visual C++ runtime for every copy in a bundle."""

from pathlib import Path, PureWindowsPath

RUNTIME_NAMES = ("msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll")


def inspect_dll(path):
    import pefile

    with pefile.PE(str(path), fast_load=False) as binary:
        info = binary.VS_FIXEDFILEINFO[0]
        version = (
            info.FileVersionMS >> 16,
            info.FileVersionMS & 65535,
            info.FileVersionLS >> 16,
            info.FileVersionLS & 65535,
        )
        return binary.FILE_HEADER.Machine, version


def select_runtime(directories, inspect=inspect_dll):
    candidates = []
    for directory in sorted({Path(p).resolve() for p in directories}):
        paths = {name: directory / name for name in RUNTIME_NAMES}
        if not all(path.is_file() for path in paths.values()):
            continue
        try:
            info = {name: inspect(path) for name, path in paths.items()}
        except (OSError, ValueError, AttributeError, IndexError):
            continue
        if any(
            machine != 0x8664 or version[0] != 14 for machine, version in info.values()
        ):
            continue
        versions = tuple(info[name][1] for name in RUNTIME_NAMES)
        # Choose a complete set; do not mix runtimes from unrelated directories.
        candidates.append((min(versions), versions, str(directory), paths))
    if not candidates:
        raise RuntimeError(
            "No complete x64 Visual C++ runtime found. Install the current Microsoft x64 redistributable before building."
        )
    return max(candidates, key=lambda candidate: candidate[:3])[3]


def harmonize(binaries, extra_directories=()):
    directories = [
        Path(source).parent
        for destination, source, _ in binaries
        if PureWindowsPath(destination).name.lower() in RUNTIME_NAMES
    ]
    selected = select_runtime([*directories, *extra_directories])
    result = []
    for destination, source, kind in binaries:
        name = PureWindowsPath(destination).name.lower()
        result.append((destination, str(selected.get(name, source)), kind))
    present = {destination.lower() for destination, _, _ in result}
    for name, source in selected.items():
        if name not in present:
            result.append((name, str(source), "BINARY"))
        print(
            f"Visual C++ runtime: {name} {inspect_dll(source)[1]} from {source}",
            flush=True,
        )
    return result

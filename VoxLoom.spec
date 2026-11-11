import os
import sys
import tomllib
from importlib.metadata import distribution
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

root = Path(SPECPATH).resolve()
app_version = tomllib.loads((root / "pyproject.toml").read_text("utf-8"))["project"][
    "version"
]
bundle_models = os.environ.get("VOXLOOM_BUNDLE_MODELS", "1") != "0"
required_assets = [root / "assets/voxloom.ico", root / "assets/model-catalog.json"]
if bundle_models:
    required_assets += [
        root / "models/DeepFilterNet3/config.ini",
        root / "assets/voxloom.ico",
        root / "models/flexsed/manifest.json",
        root / "models/flexsed/flexsed_as.pt",
        root / "models/flexsed/clap-text/model.safetensors",
    ]
for model in ("base", "small", "large-v3-turbo") if bundle_models else ():
    vocabulary = "vocabulary.json" if model == "large-v3-turbo" else "vocabulary.txt"
    required_assets.extend(
        root / "models" / f"whisper-{model}" / filename
        for filename in ("model.bin", "config.json", "tokenizer.json", vocabulary)
    )
for required in required_assets:
    if not required.is_file():
        raise RuntimeError(f"Offline release asset missing: {required}")
datas = [
    (str(root / "assets"), "assets"),
    (str(root / "README.md"), "."),
    (str(root / "README.ru.md"), "."),
    (str(root / "THIRD_PARTY_NOTICES.md"), "."),
    (str(root / "LICENSE"), "."),
    (str(root / "docs/ARCHITECTURE.md"), "docs"),
    (str(root / "docs/RELEASING.md"), "docs"),
    (str(root / "docs/BUILDING.md"), "docs"),
    (str(root / "docs/LICENSES.md"), "docs"),
]
rnnoise_name = {
    "win32": "rnnoise.dll",
    "darwin": "librnnoise.dylib",
    "linux": "librnnoise.so",
}[sys.platform]
binaries = [
    (str(distribution("pyrnnoise").locate_file("pyrnnoise/" + rnnoise_name)), "native")
]
if sys.platform == "linux":
    portaudio = Path("/usr/lib/x86_64-linux-gnu/libportaudio.so.2")
    if not portaudio.is_file():
        raise RuntimeError(
            "Install libportaudio2 before building the Linux application"
        )
    binaries.append((str(portaudio.resolve()), "."))
hiddenimports = [
    "df.deepfilternet3",
    "transformers.models.clap.modeling_clap",
    "transformers.models.clap.configuration_clap",
    "transformers.models.roberta.tokenization_roberta_fast",
]
# Import only the inference graph from df, not training/evaluation entry points.
datas += collect_data_files("df")
for package in ("faster_whisper", "ctranslate2", "noisereduce"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
for name in (
    "deepfilternet",
    "faster-whisper",
    "noisereduce",
    "pyrnnoise",
    "transformers",
    "einops",
):
    datas += copy_metadata(name)
for path in (root / "models").rglob("*") if bundle_models else ():
    if path.is_file() and ".cache" not in path.parts and path.suffix != ".log":
        datas.append(
            (str(path), str(Path("models") / path.parent.relative_to(root / "models")))
        )
if (root / "licenses").exists():
    datas.append((str(root / "licenses"), "licenses"))
a = Analysis(
    [str(root / "main.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports
    + ["soundfile", "sounddevice", "av", "onnxruntime", "torch", "torchaudio", "libdf"],
    excludes=[
        "PySide6",
        "PyQt5",
        "tkinter",
        "tensorflow",
        "tensorboard",
        "torch.utils.tensorboard",
        "pytest",
        "IPython",
        "audiolab",
        "pyrnnoise",
    ],
    noarchive=False,
)
# Qt 6.10 uses the ICU API supplied by Windows. PATH may contain Poppler's
# incompatible, version-suffixed ICU DLL with the same filename. Never shadow
# the operating-system ICU provider with that unrelated binary.
if sys.platform == "win32":
    a.binaries = [
        entry
        for entry in a.binaries
        if Path(entry[0]).name.lower() not in {"icuuc.dll", "icudt78.dll"}
    ]
# PyQt's wheel includes an older C++ runtime. The Qt runtime hook loads it
# before ONNX in frozen workers unless every copy uses the same newer runtime.
if sys.platform == "win32":
    runtime_names = {"msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"}
    runtime_sources = {
        dest.lower(): source
        for dest, source, kind in a.binaries
        if dest.lower() in runtime_names
    }
    if runtime_sources.keys() != runtime_names:
        raise RuntimeError("Missing canonical Visual C++ runtime in binary collection")
    a.binaries = [
        (dest, runtime_sources.get(Path(dest).name.lower(), source), kind)
        for dest, source, kind in a.binaries
    ]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VoxLoom",
    console=False,
    debug=False,
    strip=False,
    upx=False,
    icon=str(root / "assets/voxloom.ico") if sys.platform == "win32" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="VoxLoom", strip=False, upx=False)
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="VoxLoom.app",
        bundle_identifier="org.matsoftai.voxloom",
        version=app_version,
        icon=str(root / "assets/voxloom.icns"),
        info_plist={"NSHighResolutionCapable": True},
    )

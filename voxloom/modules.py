"""Supported modules, verified pack URLs and activation instructions.

Pack links pin an already published release. Its v1 packs also match the 0.4
trusted catalog; changing an application version must not break download links.
"""

from html import escape

from .i18n import tr

PACK_RELEASE = (
    "https://github.com/suroviimustang-ai/VoxLoom-Studio/releases/download/v0.3.0/"
)


def catalog():
    return [
        dict(
            id="spectral",
            name="Spectral Gate",
            upstream="https://github.com/timsainb/noisereduce",
            instructions=tr(
                "Cleanup → Spectral Gate → Clean. Optionally select at least 0.1 s of noise, capture the profile, then select the speech to process. Enable Use noise profile."
            ),
        ),
        dict(
            id="rnnoise",
            name="RNNoise",
            upstream="https://github.com/xiph/rnnoise",
            instructions=tr(
                "Cleanup → RNNoise → Clean. Included native library and weights; no separate download."
            ),
        ),
        dict(
            id="silero",
            name="Silero VAD",
            upstream="https://github.com/snakers4/silero-vad",
            instructions=tr(
                "Speech → Find speech on track. Click a colored region to listen or transcribe. VAD detects intervals; it does not clean audio."
            ),
        ),
        dict(
            id="dsp",
            name="DSP",
            upstream=None,
            instructions=tr(
                "Cleanup → DSP → Clean. Reduces 50 Hz hum and low frequencies. No neural model is required."
            ),
        ),
        dict(
            id="normalization",
            name="LUFS / Peak",
            upstream="https://github.com/csteinmetz1/pyloudnorm",
            instructions=tr(
                "Level → choose LUFS or Peak → set a target → Normalize. LUFS requires at least 0.4 s and supports up to 5 channels; Peak supports all 8."
            ),
        ),
        dict(
            id="whisper-base",
            name="Whisper Base",
            size="134 / 148 MB",
            pack="VoxLoom-Models-whisper-base-v1.zip",
            upstream="https://huggingface.co/Systran/faster-whisper-base",
            instructions=tr(
                "Speech → base → choose the spoken language → select audio → Transcribe selection. A lighter model for quick drafts."
            ),
        ),
        dict(
            id="whisper-small",
            name="Whisper Small",
            size="448 / 486 MB",
            pack="VoxLoom-Models-whisper-small-v1.zip",
            upstream="https://huggingface.co/Systran/faster-whisper-small",
            instructions=tr(
                "Speech → small → choose the spoken language → select audio → Transcribe selection. The default transcription choice; its pack must be installed."
            ),
        ),
        dict(
            id="whisper-large-v3-turbo",
            name="Whisper Large v3 Turbo",
            size="1.50 / 1.62 GB",
            pack="VoxLoom-Models-whisper-large-v3-turbo-v1.zip",
            upstream="https://huggingface.co/mobiuslabsgmbh/faster-whisper-large-v3-turbo",
            instructions=tr(
                "Speech → large-v3-turbo → choose the spoken language → select audio → Transcribe selection. Requires more memory than Base or Small."
            ),
        ),
        dict(
            id="DeepFilterNet3",
            name="DeepFilterNet3",
            size="8 / 9 MB",
            pack="VoxLoom-Models-DeepFilterNet3-v1.zip",
            upstream="https://github.com/Rikorose/DeepFilterNet",
            instructions=tr(
                "Cleanup → DeepFilterNet3 → Clean. Compare original A and processed B by listening. Uses 48 kHz internally; input sample rate and channel layout are preserved."
            ),
        ),
        dict(
            id="flexsed",
            name="FlexSED + CLAP",
            size="862 / 937 MB",
            pack="VoxLoom-Models-flexsed-v1.zip",
            upstream="https://huggingface.co/Higobeatz/FlexSED/tree/main/ckpts",
            instructions=tr(
                "Events → enter English descriptions such as Speech; Conversation; Whispering → choose channels and threshold → Find events. The pack includes the CLAP text encoder. Results are event markers, not cleaned audio or transcripts."
            ),
        ),
    ]


def installed(module):
    from .processing import model_directory, whisper_ready

    if "pack" not in module:
        return True
    key = module["id"]
    if key.startswith("whisper-"):
        return whisper_ready(key.removeprefix("whisper-"))
    if key == "DeepFilterNet3":
        return (model_directory(key) / "config.ini").is_file()
    from .events import available

    return available()


def catalog_html():
    parts = ["<h2>" + escape(tr("Modules and model packs")) + "</h2>"]
    parts.append(
        "<p>"
        + escape(
            tr(
                "Open Download ZIP in your browser, keep the ZIP intact, then choose Install pack below. Installation verifies every file. Once installed, models work offline on Windows, macOS and Linux."
            )
        )
        + "</p>"
    )
    for module in sorted(catalog(), key=lambda item: "pack" not in item):
        status = (
            tr("Built in")
            if "pack" not in module
            else tr("installed")
            if installed(module)
            else tr("not installed")
        )
        parts.append(f"<h3>{escape(module['name'])} — {escape(status)}</h3>")
        parts.append("<p>" + escape(module["instructions"]) + "</p>")
        links = []
        if "pack" in module:
            url = PACK_RELEASE + module["pack"]
            links.append(
                f'<a href="{url}">{escape(tr("Download ZIP"))}</a> · {escape(module["size"])} ({escape(tr("download / installed"))})'
            )
        if module["upstream"]:
            links.append(
                f'<a href="{module["upstream"]}">{escape(tr("Upstream project"))}</a>'
            )
        parts.append("<p>" + " · ".join(links) + "</p>")
    parts.append(
        "<p>"
        + escape(
            tr(
                "Use the VoxLoom ZIP links above for installation. Upstream weights, arbitrary .pth/.onnx files and VST plugins cannot be imported directly. UMX SE, ConvTasNet and PANNs are not integrated."
            )
        )
        + "</p>"
    )
    return "".join(parts)

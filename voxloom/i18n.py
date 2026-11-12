"""English source messages with a Russian catalog, also usable in workers.

Messages retain their template and arguments so widgets can change language
without rebuilding the workspace or touching user transcripts.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

LANGUAGES = ("en", "ru")
_language = "en"


@lru_cache(maxsize=1)
def russian_catalog():
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return json.loads(
        (root / "assets/translations/ru.json").read_text(encoding="utf-8")
    )


def language():
    return _language


def set_language(code):
    global _language
    _language = code if code in LANGUAGES else "en"


class Message(str):
    """A rendered string that keeps the source needed for live translation."""

    def __new__(cls, source, values):
        template = (
            russian_catalog().get(source, source) if language() == "ru" else source
        )
        result = super().__new__(cls, template.format(**render(values)))
        result.source, result.values = source, values
        return result


def tr(source, **values):
    return Message(source, values)


def render(value):
    if isinstance(value, Message):
        return str(tr(value.source, **value.values))
    if isinstance(value, dict):
        return {key: render(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [render(item) for item in value]
    return value

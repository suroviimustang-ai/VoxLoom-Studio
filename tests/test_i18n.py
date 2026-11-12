import ast
import json
from pathlib import Path
from string import Formatter

import pytest

from voxloom.i18n import language, render, russian_catalog, set_language, tr
from voxloom.modules import catalog, catalog_html

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def restore_language():
    previous = language()
    set_language("en")
    yield
    set_language(previous)


def test_default_and_unknown_language_fall_back_to_english():
    set_language("unsupported")
    assert language() == "en"
    assert tr("Open audio") == "Open audio"


def test_formatted_message_can_be_rendered_again_without_changing_values():
    message = tr("Channel {v0}", v0=3)
    assert message == "Channel 3"
    set_language("ru")
    assert render(message) == "Канал 3"
    assert message.values == {"v0": 3}
    set_language("en")
    assert render(message) == "Channel 3"


def test_every_source_message_has_a_translation_with_identical_placeholders():
    translations = russian_catalog()
    formatter = Formatter()

    def fields(text):
        return sorted(
            (name, spec, conversion)
            for _, name, spec, conversion in formatter.parse(text)
            if name is not None
        )

    sources = [ROOT / "main.py", *(ROOT / "voxloom").glob("*.py")]
    for path in sources:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "tr"
            ):
                if not isinstance(node.args[0], ast.Constant):
                    assert path.name == "i18n.py", (
                        "Application messages need literal source templates"
                    )
                    continue
                source = node.args[0].value
                assert source in translations, (path.name, source)
                assert fields(source) == fields(translations[source]), source


def test_all_trusted_packs_have_download_and_activation_instructions():
    trusted = json.loads(
        (ROOT / "assets/model-catalog.json").read_text(encoding="utf-8")
    )
    modules = catalog()
    packs = [module for module in modules if "pack" in module]
    assert len(modules) == 10 and len(packs) == 5
    assert {module["id"] for module in packs} == set(trusted["models"])
    for module in modules:
        assert "→" in module["instructions"]
    english = catalog_html()
    set_language("ru")
    russian = catalog_html()
    assert "Download ZIP" in english and "Скачать ZIP" in russian
    assert (
        english.count("releases/download/") == russian.count("releases/download/") == 5
    )

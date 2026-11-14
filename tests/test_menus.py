from unittest.mock import Mock

import pytest
from PyQt6 import QtCore as C
from PyQt6 import QtWidgets as W

from voxloom.ui_language import initialize
from voxloom.window import MainWindow


@pytest.fixture
def window(tmp_path):
    app = W.QApplication.instance() or W.QApplication([])
    settings = C.QSettings(str(tmp_path / "settings.ini"), C.QSettings.Format.IniFormat)
    initialize(app, settings)
    widget = MainWindow(settings)
    widget.show()
    app.processEvents()
    yield widget
    widget.job = None
    widget.close()
    widget.deleteLater()
    settings.setValue("ui_language", "en")
    initialize(app, settings)
    app.processEvents()


def test_menu_translation_preserves_clap_queries_and_labels(window):
    expected = ["&File", "&Edit", "&View", "&Process", "&About"]
    assert [a.text() for a in window.menuBar().actions()] == expected
    for code in ("ru", "en"):
        window.ui_language.setCurrentIndex(window.ui_language.findData(code))
        assert window.event_queries.text() == "Speech; Conversation; Whispering"
        assert window.menus.actions[code].isChecked()
    assert [a.text() for a in window.menuBar().actions()] == expected


def test_menu_commands_follow_busy_and_selection_states(window, monkeypatch):
    actions = window.menus.actions
    assert actions["open"].isEnabled()
    assert not actions["export"].isEnabled()
    assert not actions["transcribe"].isEnabled()
    dialog = Mock(return_value=("", ""))
    monkeypatch.setattr(W.QFileDialog, "getOpenFileName", dialog)
    actions["open"].trigger()
    dialog.assert_called_once()
    window.job = object()
    window.refresh()
    assert not actions["open"].isEnabled()
    assert not actions["models"].isEnabled()
    assert not actions["en"].isEnabled()
    assert actions["cancel"].isEnabled()
    actions["open"].trigger()
    dialog.assert_called_once()


def test_text_undo_is_separate_from_processing_and_about_shows_version(
    window, monkeypatch
):
    from voxloom import __version__

    window.transcript.setFocus()
    W.QApplication.processEvents()
    window.update_transport_shortcuts()
    assert not any(shortcut.isEnabled() for shortcut in window.transport_shortcuts)
    window.transcript.insertPlainText("Sample transcript")
    window.menus.refresh()
    assert window.menus.actions["undo"].isEnabled()
    window.menus.actions["undo"].trigger()
    assert not window.transcript.toPlainText()
    window.menus.refresh()
    window.menus.actions["redo"].trigger()
    assert window.transcript.toPlainText() == "Sample transcript"
    assert window.menus.actions["undo_processing"].shortcut().toString() == "Ctrl+Alt+Z"
    about = Mock()
    monkeypatch.setattr(W.QMessageBox, "about", about)
    window.menus.actions["about"].trigger()
    assert __version__ in about.call_args.args[2]

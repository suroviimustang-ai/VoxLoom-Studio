from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
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


@pytest.mark.parametrize("outcome", ["success", "error", "cancel", "start_error"])
def test_whisper_keeps_playback_and_transport_available(window, monkeypatch, outcome):
    from voxloom.jobs import Job

    window.source = np.zeros((48000 * 3, 1), np.float32)
    window.selection = (0.5, 2.0)
    player = SimpleNamespace(playing=True, stream=None, position=24000)
    player.pause = Mock(side_effect=lambda: setattr(player, "playing", False))
    player.play = Mock(side_effect=lambda *args: setattr(player, "playing", True))
    window.player = player
    window.error = Mock()
    start = Mock(
        side_effect=OSError("worker could not start")
        if outcome == "start_error"
        else None
    )
    monkeypatch.setattr(Job, "start", start)
    window.transcribe()
    player.pause.assert_not_called()
    assert player.playing
    assert window.play_button.isEnabled() and window.stop_button.isEnabled()
    if outcome == "start_error":
        assert window.job is None
        window.error.assert_called_once()
        return
    assert not window.a_b.isEnabled() and not window.open_button.isEnabled()
    assert start.call_args.args[0]["action"] == "transcribe"
    window.toggle_play()
    assert not player.playing
    window.toggle_play()
    assert player.playing
    window.stop()
    assert not player.playing
    window.toggle_play()
    player.pause.reset_mock()
    job = window.job
    job.cancelled = outcome == "cancel"
    response = dict(
        ok=outcome == "success",
        text="Test",
        segments=[],
        language="en",
        error="Test error",
    )
    job.finished.emit(response, None)
    player.pause.assert_not_called()
    assert player.playing and window.job is None
    assert window.selection == (0.5, 2.0)


@pytest.mark.parametrize("action", ["load", "denoise", "normalize"])
def test_audio_replacement_jobs_still_pause_playback(window, monkeypatch, action):
    from voxloom.jobs import Job

    window.source = np.zeros((48000, 1), np.float32)
    player = SimpleNamespace(playing=True, stream=None)
    player.pause = Mock(side_effect=lambda: setattr(player, "playing", False))
    window.player = player
    monkeypatch.setattr(Job, "start", Mock())
    window.run_job({"action": action}, "Test", lambda *_: None)
    player.pause.assert_called_once()
    assert not window.play_button.isEnabled()
    window.toggle_play()
    assert not player.playing

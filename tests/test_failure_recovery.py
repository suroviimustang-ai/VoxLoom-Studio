import json
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PyQt6.QtCore import QCoreApplication

from voxloom.files import write_text_atomic
from voxloom.jobs import Job
from voxloom.playback import Playback
from voxloom.worker import execute


@pytest.fixture(scope="module")
def app():
    return QCoreApplication.instance() or QCoreApplication([])


@pytest.mark.parametrize("response", ["{", "[]", '{"ok": "yes"}', '{"ok": true}'])
def test_broken_worker_reply_settles_once(app, tmp_path, response):
    (tmp_path / "result.json").write_text(response, encoding="utf-8")
    job = Job()
    job.action = "load"
    job.temp = SimpleNamespace(name=str(tmp_path), cleanup=lambda: None)
    replies = []
    job.finished.connect(lambda result, output: replies.append((result, output)))
    job._finished(0)
    job._finished(0)
    assert len(replies) == 1 and not replies[0][0]["ok"]


def test_cleanup_failure_does_not_swallow_completion(app):
    def fail():
        raise PermissionError("file locked")

    job = Job()
    job.temp = SimpleNamespace(cleanup=fail)
    replies = []
    job.finished.connect(lambda result, output: replies.append(result))
    job._settle({"ok": True}, None)
    assert replies == [{"ok": True}]


def test_worker_bad_request_is_structured(tmp_path):
    request = tmp_path / "request.json"
    request.write_text("{", encoding="utf-8")
    assert execute(str(request)) == 1
    result = json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))
    assert result["ok"] is False and result["error"]


def test_text_export_failure_preserves_existing_file(tmp_path, monkeypatch):
    target = tmp_path / "текст.txt"
    target.write_text("Старый текст", encoding="utf-8")

    def full_disk(*args):
        raise OSError("Disk full")

    monkeypatch.setattr("voxloom.files.os.replace", full_disk)
    with pytest.raises(OSError):
        write_text_atomic(target, "Новый текст")
    assert target.read_text(encoding="utf-8") == "Старый текст"
    assert list(tmp_path.iterdir()) == [target]


def test_lost_audio_device_always_closes():
    closed = []

    def fail():
        raise RuntimeError("device disconnected")

    player = Playback()
    player.stream = SimpleNamespace(stop=fail, close=lambda: closed.append(True))
    player.pause()
    player.pause()
    assert player.stream is None and closed == [True]

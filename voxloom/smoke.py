"""Release validation using the same UI and subprocess entry point as users."""

import json
import logging
import time
from pathlib import Path

import numpy as np
from PyQt6 import QtWidgets as W


def run(app, window, fixture, destination):
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=True)
    from .diagnostics import LOG

    diagnostic_log = logging.FileHandler(root / "runtime.log", encoding="utf-8")
    LOG.addHandler(diagnostic_log)
    errors, checks = [], []
    W.QMessageBox.warning = lambda parent, title, text: errors.append(text)

    def wait(timeout=240):
        end = time.monotonic() + timeout
        while window.job and time.monotonic() < end:
            app.processEvents()
            time.sleep(0.015)
        assert not window.job, "Worker timeout"
        assert not errors, errors
        app.processEvents()

    try:
        app.processEvents()
        assert window.isMaximized(), "Workspace did not start maximized"
        available = window.screen().availableGeometry()
        assert (
            window.width() <= available.width()
            and window.height() <= available.height()
        )
        window.grab().save(str(root / "startup-workspace.png"))
        checks.append("screen-sized-startup")
        from .i18n import language
        from .modules import catalog_html

        assert language() == "en" and window.open_button.text() == "Open audio"
        checks.append("english-first-launch")
        assert catalog_html().count("releases/download/") == 5
        checks.append("complete-model-download-catalog")
        from .processing import WHISPER_MODELS, whisper_ready

        assert all(whisper_ready(name) for name in WHISPER_MODELS), (
            "Incomplete offline ASR bundle"
        )
        checks.append("all-whisper-models-bundled")
        window.load_path(fixture)
        wait()
        original = window.source.copy()
        checks.append("decode")
        for method in ["spectral", "rnnoise", "deepfilter"]:
            window.a_b.setCurrentIndex(0)
            window.method.setCurrentIndex(window.method.findData(method))
            window.clean()
            wait()
            assert (
                window.result.shape == original.shape
                and np.isfinite(window.result).all()
            )
            np.testing.assert_array_equal(window.source, original)
            checks.append(method)
        window.a_b.setCurrentIndex(0)
        window.detect()
        wait()
        assert window.regions, "No speech detected in spoken fixture"
        checks.append("silero")
        from .events import available

        if available():
            window.event_queries.setText("Conversation")
            window.select_range(0, 0)
            window.detect_events()
            wait()
            assert window.events, "No FlexSED Conversation events in spoken fixture"
            np.testing.assert_array_equal(window.source, original)
            window.select_event(0)
            assert window.selection and window.region_index == -1
            checks.append("flexsed-offline-events")
            window.language.setCurrentIndex(window.language.findData("en"))
            window.transcribe()
            wait()
            assert window.transcript.toPlainText().strip(), (
                "Empty ASR for FlexSED selection"
            )
            checks.append("flexsed-selection-to-asr")
            window.grab().save(str(root / "release-events.png"))
        window.select_range(window.regions[0].start, window.regions[-1].end)
        window.language.setCurrentIndex(window.language.findData("en"))
        window.transcribe()
        wait()
        transcript = window.transcript.toPlainText()
        assert "speech" in transcript.lower(), transcript
        checks.append("whisper-small")
        selection = window.selection
        for code, expected in (("ru", "Открыть аудио"), ("en", "Open audio")):
            window.ui_language.setCurrentIndex(window.ui_language.findData(code))
            app.processEvents()
            assert window.open_button.text() == expected
            assert window.selection == selection
            assert window.transcript.toPlainText() == transcript
            assert window.language.currentData() == "en"
            np.testing.assert_array_equal(window.source, original)
        checks.append("live-language-switch-preserves-session")
        app.processEvents()
        window.grab().save(str(root / "release-ui.png"))
        window.select_range(0, 0)
        window.apply_normalize()
        wait()
        checks.append("lufs")
        window.run_job(
            {
                "action": "export",
                "path": str(root / "release-export.flac"),
                "rate": window.rate,
            },
            "Test export",
            lambda *_: None,
            window.result,
        )
        wait()
        checks.append("export")
        previous = window.result.copy()
        window.clean()
        window.cancel_job()
        wait()
        np.testing.assert_array_equal(window.result, previous)
        checks.append("cancel-preserves-result")
        (root / "release-smoke.json").write_text(
            json.dumps(
                {
                    "ok": True,
                    "checks": checks,
                    "transcript": transcript,
                    "regions": [r.as_dict() for r in window.regions],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        window.close()
        return 0
    except Exception as exc:
        (root / "release-smoke.json").write_text(
            json.dumps(
                {"ok": False, "checks": checks, "error": str(exc), "errors": errors},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        window.close()
        return 1
    finally:
        LOG.removeHandler(diagnostic_log)
        diagnostic_log.close()

"""Exercise window bounds and splash centering on simulated Qt displays."""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/startup-check"
sys.path.insert(0, str(ROOT))


def check(name):
    import numpy as np
    from PyQt6 import QtCore as C
    from PyQt6 import QtWidgets as W

    from voxloom.speech import Region
    from voxloom.startup import StartupSplash, show_workspace
    from voxloom.ui_language import initialize
    from voxloom.window import MainWindow

    app = W.QApplication([])
    app.setStyle("Fusion")
    settings = C.QSettings(
        str(OUT / f"{name}-settings.ini"), C.QSettings.Format.IniFormat
    )
    settings.clear()
    initialize(app, settings)
    screen = app.screens()[-1]
    available = screen.availableGeometry()
    splash = StartupSplash(screen)
    splash.show()
    app.processEvents()
    assert available.contains(splash.geometry())
    assert (splash.geometry().center() - available.center()).manhattanLength() <= 2
    splash.grab().save(str(OUT / f"{name}-splash.png"))
    window = MainWindow(settings)
    assert window.open_button.text() == "Open audio"
    assert window.ui_language.currentData() == "en"
    show_workspace(window, screen)
    for _ in range(5):
        app.processEvents()
    splash.finish(window)
    assert window.isMaximized()
    assert window.screen() == screen
    assert window.frameGeometry() == available, (window.frameGeometry(), available)
    assert window.geometry().width() <= available.width()
    assert window.geometry().height() <= available.height()
    assert not isinstance(window.centralWidget(), W.QScrollArea)

    def check_controls():
        # Inspect actual clipping, not just the outer window. Text/table contents
        # may scroll, but toolbar buttons and every tool page must remain visible.
        essential = [
            window.open_button,
            window.models_button,
            window.ui_language,
            window.export_button,
            window.play_button,
            window.stop_button,
            window.a_b,
            window.zoom_in,
            window.zoom_out,
            window.fit_button,
            window.clean_button,
            window.method,
            window.noise_button,
            window.norm_mode,
            window.target,
            window.normalize_button,
            window.threshold,
            window.silence,
            window.detect_button,
            window.asr_model,
            window.language,
            window.transcribe_button,
            window.event_queries,
            window.event_threshold,
            window.event_channel,
            window.events_button,
            window.undo_button,
            window.add_region_button,
            window.delete_region_button,
            window.listen_button,
            window.labels_button,
            window.save_text_button,
            window.save_srt_button,
            window.table,
            window.event_table,
            window.transcript,
            window.cancel_button,
            window.progress,
        ]
        for page in range(window.tool_tabs.count()):
            window.tool_tabs.setCurrentIndex(page)
            app.processEvents()
            for widget in essential:
                if widget.isVisibleTo(window):
                    visible = widget.visibleRegion().boundingRect()
                    assert visible == widget.rect(), (
                        name,
                        page,
                        type(widget).__name__,
                        widget.objectName(),
                        visible,
                        widget.rect(),
                    )
                    assert widget.width() > 0 and widget.height() > 0
        window.tool_tabs.setCurrentIndex(0)
        app.processEvents()

    # Populate the UI with synthetic data and long metadata without loading models.
    time = np.arange(48000 * 8) / 48000
    amplitude = 0.3 * np.maximum(0, np.sin(time * 2.2))
    signal = (amplitude * np.sin(time * 2 * np.pi * 190)).astype(np.float32)[:, None]
    window.source = signal
    window.result = signal * 0.8
    window.rate = 48000
    window.timeline.set_audio(window.source, window.result, window.rate)
    window.timeline.fit()
    window.regions = [Region(0.35, 1.4), Region(3, 4.1), Region(5.9, 7.1)]
    window.update_regions()
    window.select_range(0.35, 1.4)
    text = (
        "Пример текста выделенного фрагмента. Можно прослушать запись и уточнить слова."
    )
    window.transcript.setPlainText(text)
    window.file_label.setText(
        "Очень длинное имя аудиозаписи " * 12 + ".wav • 48 000 Hz • 2 ch"
    )
    window.refresh()
    app.processEvents()
    check_controls()
    # Changing UI language must not reset audio, selection, edits or ASR settings.
    before = (
        window.selection,
        window.language.currentData(),
        window.asr_model.currentText(),
    )
    for code, caption in (("ru", "Открыть аудио"), ("en", "Open audio")):
        window.ui_language.setCurrentIndex(window.ui_language.findData(code))
        app.processEvents()
        assert window.open_button.text() == caption
        assert window.transcript.toPlainText() == text
        assert window.source is signal
        assert before == (
            window.selection,
            window.language.currentData(),
            window.asr_model.currentText(),
        )
        restored = C.QSettings(settings.fileName(), C.QSettings.Format.IniFormat)
        assert restored.value("ui_language") == code
        initialize(app, restored)
        if code == "ru":
            assert not app._qt_language.isEmpty(), "Qt Russian dialogs are missing"
        window.player.stream = SimpleNamespace(active=True)
        window.tick()
        assert window.play_button.text() == ("Pause" if code == "en" else "Пауза")
        window.player.stream = None
        window.tick()
        check_controls()
        window.grab().save(str(OUT / f"{name}-{code}-workspace.png"))
        if name == "laptop":

            def check_models():
                dialog = app.activeModalWidget()
                assert available.contains(dialog.frameGeometry())
                browser = dialog.findChild(W.QTextBrowser)
                assert browser.toHtml().count("releases/download/") == 5
                dialog.grab().save(str(OUT / f"{name}-{code}-models.png"))
                dialog.accept()

            C.QTimer.singleShot(100, check_models)
            window.models()
    if window._narrow_results:
        window.results_tabs.setCurrentWidget(window.transcript_box)
        app.processEvents()
        assert window.transcript.isVisibleTo(window)
        check_controls()
        window.results_tabs.setCurrentWidget(window.regions_box)
    else:
        assert window.table.isVisibleTo(window) and window.transcript.isVisibleTo(
            window
        )
    # Processing controls and long status must not push the workspace off-screen.
    window.job = object()
    window.message.setText("Обработка выделенного фрагмента… " * 12)
    window.refresh()
    app.processEvents()
    check_controls()
    window.job = None
    window.refresh()
    window.message.setText("Готово. Демонстрационная дорожка.")
    window.file_label.setText(
        "Демонстрационная дорожка.wav   •   48 000 Hz   •   1 ch   •   8.00 s"
    )
    app.processEvents()
    window.grab().save(str(OUT / f"{name}-workspace.png"))
    window.tool_tabs.setCurrentIndex(2)
    if window._narrow_results:
        window.results_tabs.setCurrentWidget(window.transcript_box)
    app.processEvents()
    window.grab().save(str(OUT / f"{name}-speech.png"))
    window.tool_tabs.setCurrentIndex(0)
    result = dict(
        name=name,
        available=available.getRect(),
        frame=window.frameGeometry().getRect(),
        device_pixel_ratio=screen.devicePixelRatio(),
        maximized=window.isMaximized(),
        all_tool_pages_unclipped=True,
        ui_languages=["en", "ru"],
        language_switch_preserves_session=True,
        compact=window._density_mode,
        tabbed_results=window._narrow_results,
    )
    # Moving between wide and narrow screens must preserve and show both panels.
    window.showNormal()
    for width, height in [(800, 600), (1366, 768), (1024, 600), (1920, 1080)]:
        window.resize(width, height)
        for _ in range(4):
            app.processEvents()
        assert window.transcript.toPlainText() == text
        assert window.table.rowCount() == 3
        if window._narrow_results:
            window.results_tabs.setCurrentWidget(window.transcript_box)
            app.processEvents()
            assert window.transcript.isVisibleTo(window)
        else:
            assert window.transcript.isVisibleTo(window) and window.table.isVisibleTo(
                window
            )
        check_controls()
    (OUT / f"{name}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    window.close()


def run_matrix():
    OUT.mkdir(parents=True, exist_ok=True)
    cases = {
        "fullhd": [dict(name="main", width=1920, height=1080)],
        "laptop": [dict(name="main", width=1366, height=768)],
        "small-workarea": [dict(name="main", width=1280, height=680)],
        "small-laptop": [dict(name="main", width=1024, height=600)],
        "hidpi-small": [dict(name="main", width=800, height=600, dpr=2)],
        "secondary-left": [
            dict(name="main", width=1920, height=1080),
            dict(name="secondary", x=-1280, width=1280, height=720),
        ],
    }
    reports = []
    for name, screens in cases.items():
        config = OUT / f"{name}-screens.json"
        # Qt's offscreen plugin translates every negative-x window by its fake
        # 2-pixel frame margin (qoffscreenwindow.cpp::setGeometryImpl). Disable
        # only that simulated frame for the left-hand monitor case.
        config.write_text(
            json.dumps(
                dict(screens=screens, windowFrameMargins=name != "secondary-left")
            ),
            encoding="utf-8",
        )
        environment = dict(
            os.environ,
            QT_QPA_PLATFORM="offscreen:configfile="
            + config.relative_to(ROOT).as_posix(),
        )
        subprocess.run(
            [sys.executable, __file__, name],
            cwd=ROOT,
            env=environment,
            check=True,
            timeout=60,
        )
        reports.append(json.loads((OUT / f"{name}.json").read_text(encoding="utf-8")))
    (OUT / "report.json").write_text(
        json.dumps(dict(ok=True, simulated_screens=reports), indent=2), encoding="utf-8"
    )
    print(
        f"Startup, unclipped controls and responsive panels: {len(cases)} simulated displays passed."
    )


if __name__ == "__main__":
    check(sys.argv[1]) if len(sys.argv) > 1 else run_matrix()

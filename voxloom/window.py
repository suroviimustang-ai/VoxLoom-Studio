from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from PyQt6 import QtCore as C
from PyQt6 import QtGui as G
from PyQt6 import QtWidgets as W

from . import __version__
from .audio import bounds
from .diagnostics import LOG
from .files import write_text_atomic
from .i18n import language, tr
from .jobs import Job
from .playback import Playback
from .processing import WHISPER_MODELS, resource_root, writable_models
from .speech import Region
from .timeline import Timeline
from .ui_language import add_item, add_tab, apply_language, bind, retranslate

STYLE = """
QWidget { background: #161c25; color: #dbe5f3; font-family: 'Segoe UI'; font-size: 10pt; }
QMainWindow { background: #10151d; }
QLabel#brand { font-size: 22pt; font-weight: 700; color: #f1f6ff; }
QLabel#muted { color: #91a1b9; }
QLabel#section { color: #5bdac6; font-size: 10pt; font-weight: 600; padding: 8px 0; }
QLabel#clock { font-family: Consolas; font-size: 21pt; color: #f4c163; padding: 6px 16px; background: #10151d; border-radius: 5px; }
QPushButton { background: #253143; border: 1px solid #37475f; border-radius: 5px; padding: 8px 12px; }
QPushButton:hover { background: #31425a; border-color: #758aa6; }
QPushButton:pressed { background: #405471; }
QPushButton:disabled { color: #637087; background: #1b2330; border-color: #283346; }
QPushButton#primary { background: #267e73; border-color: #42baa7; color: #f3fffc; font-weight: 600; }
QPushButton#primary:hover { background: #2f998c; }
QPushButton#primary:disabled { background: #233c3c; color: #658580; border-color: #36524f; }
QPushButton#danger { color: #ff9eaa; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background: #101722; border: 1px solid #354358; border-radius: 4px; padding: 6px; min-height: 20px; }
QComboBox QAbstractItemView { background: #202c3d; selection-background-color: #317e75; }
QTextEdit, QTableWidget { background: #101720; border: 1px solid #2c394b; selection-background-color: #335a60; }
QHeaderView::section { background: #202b3b; border: none; padding: 8px; color: #9fb1ca; }
QTableWidget::item { padding: 4px; }
QTabWidget::pane { border: none; }
QTabBar::tab { background: #1a2432; color: #95a6bf; padding: 9px 12px; border-bottom: 2px solid #243043; }
QTabBar::tab:selected { color: #7ae1cd; border-bottom: 2px solid #5bdac6; }
QGroupBox { border: 1px solid #2c394b; border-radius: 6px; margin-top: 12px; padding: 12px; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; color: #a8bbd5; }
QSplitter::handle { background: #293447; width: 3px; height: 3px; }
QProgressBar { background: #101722; border: none; border-radius: 3px; height: 5px; }
QProgressBar::chunk { background: #5bdac6; }
QScrollBar:vertical { background: #101722; width: 10px; }
QScrollBar::handle:vertical { background: #41536c; min-height: 30px; border-radius: 4px; }
QScrollBar:horizontal { background: #101722; height: 10px; }
QScrollBar::handle:horizontal { background: #41536c; min-width: 30px; border-radius: 4px; }
QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: #101722; }
QStatusBar { color: #92a5be; background: #10151d; }
QToolTip { background: #26364b; color: #e2edff; border: 1px solid #526a87; }
"""

COMPACT_STYLE = """
QLabel#brand { font-size: 17pt; }
QLabel#section { padding: 3px 0; }
QLabel#clock { font-size: 16pt; padding: 3px 8px; }
QPushButton { padding: 4px 8px; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { padding: 3px; min-height: 18px; }
QTabBar::tab { padding: 5px 4px; }
QHeaderView::section { padding: 4px; }
QTableWidget::item { padding: 2px; }
"""


class ElidedLabel(W.QLabel):
    """Keep long filenames, selections and status messages inside their row."""

    def __init__(self, text, name="muted"):
        super().__init__()
        self.setObjectName(name)
        self.setMinimumWidth(0)
        self.setSizePolicy(W.QSizePolicy.Policy.Ignored, W.QSizePolicy.Policy.Preferred)
        bind(self, "setText", text)

    def setText(self, text):
        super().setText(text)
        self.setToolTip(text)

    def paintEvent(self, event):
        painter = G.QPainter(self)
        painter.setPen(self.palette().color(G.QPalette.ColorRole.WindowText))
        text = self.fontMetrics().elidedText(
            self.text(), C.Qt.TextElideMode.ElideRight, self.contentsRect().width()
        )
        painter.drawText(self.contentsRect(), self.alignment(), text)


def label(text, name=None):
    widget = W.QLabel()
    bind(widget, "setText", text)
    if name:
        widget.setObjectName(name)
    return widget


class MainWindow(W.QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for filename in ["segoeui.ttf", "seguisb.ttf", "consola.ttf", "seguisym.ttf"]:
            if (fonts / filename).is_file():
                G.QFontDatabase.addApplicationFont(str(fonts / filename))
        bind(self, "setWindowTitle", "VoxLoom Studio · MatSoftAI")
        # Density and panel arrangement follow logical pixels, including high DPI.
        self.setMinimumSize(320, 240)
        self.setStyleSheet(STYLE)
        self.setAcceptDrops(True)
        self.source = self.result = self.previous = self.noise = None
        self.rate, self.path = 48000, None
        self.regions = []
        self.events = []
        self.event_analysis = {}
        self.selection = None
        self.job = None
        self.region_index = -1
        self.transcript_segments = []
        self.player = Playback()
        self.settings = settings if settings is not None else C.QSettings()
        self._density_mode = None
        self._narrow_results = None
        self._build()
        self.timer = C.QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(40)
        for sequence, action in [
            ("Space", self.toggle_play),
            ("Escape", self.stop),
            ("Ctrl+O", self.open_file),
            ("Ctrl+Z", self.undo),
            ("Ctrl+S", self.export_audio),
        ]:
            shortcut = G.QShortcut(G.QKeySequence(sequence), self)
            shortcut.activated.connect(action)
        self.refresh()

    def button(self, text, callback, primary=False):
        button = W.QPushButton()
        bind(button, "setText", text)
        button.clicked.connect(callback)
        if primary:
            button.setObjectName("primary")
        return button

    def _build(self):
        root = W.QWidget()
        self.setCentralWidget(root)
        layout = self.root_layout = W.QVBoxLayout(root)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(12)
        header = self.header_layout = W.QHBoxLayout()
        mark = W.QLabel()
        mark.setPixmap(
            G.QPixmap(str(resource_root() / "assets/voxloom.png")).scaled(
                38,
                38,
                C.Qt.AspectRatioMode.KeepAspectRatio,
                C.Qt.TransformationMode.SmoothTransformation,
            )
        )
        header.addWidget(mark)
        header.addWidget(label("VoxLoom", "brand"))
        self.tagline = label("STUDIO  /  SPEECH RESTORATION", "muted")
        header.addWidget(self.tagline)
        header.addStretch()
        self.ui_language = W.QComboBox()
        self.ui_language.addItem("English", "en")
        self.ui_language.addItem("Русский", "ru")
        self.ui_language.setCurrentIndex(self.ui_language.findData(language()))
        bind(
            self.ui_language,
            "setToolTip",
            tr("Interface language (separate from transcription language)"),
        )
        self.ui_language.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.ui_language)
        self.open_button = self.button(tr("Open audio"), self.open_file)
        self.models_button = self.button(tr("Models"), self.models)
        self.export_button = self.button(tr("Export audio"), self.export_audio, True)
        for widget in [self.open_button, self.models_button, self.export_button]:
            header.addWidget(widget)
        layout.addLayout(header)
        transport = self.transport_layout = W.QHBoxLayout()
        self.play_button = self.button(tr("Play"), self.toggle_play)
        self.stop_button = self.button(tr("Stop"), self.stop)
        self.stop_button.setIcon(
            self.style().standardIcon(W.QStyle.StandardPixmap.SP_MediaStop)
        )
        bind(self.play_button, "setToolTip", tr("Play / pause — Space"))
        bind(self.stop_button, "setToolTip", tr("Stop — Esc"))
        self.clock = label("00:00.000", "clock")
        self.a_b = W.QComboBox()
        add_item(self.a_b, tr("A  ·  Original"), "original")
        add_item(self.a_b, tr("B  ·  Result"), "result")
        bind(
            self.a_b,
            "setToolTip",
            tr("Track used for playback, speech detection and subsequent processing"),
        )
        self.a_b.currentIndexChanged.connect(self.switch_track)
        self.selection_label = ElidedLabel(tr("Whole file"))
        for widget in [
            self.play_button,
            self.stop_button,
            self.clock,
            self.a_b,
            self.selection_label,
        ]:
            transport.addWidget(widget, 1 if widget is self.selection_label else 0)
        self.zoom_out = self.button("−", lambda: self.timeline.zoom(1.5))
        self.zoom_in = self.button("+", lambda: self.timeline.zoom(1 / 1.5))
        self.fit_button = self.button(tr("Whole file"), lambda: self.timeline.fit())
        bind(self.zoom_out, "setToolTip", tr("Zoom out"))
        bind(self.zoom_in, "setToolTip", tr("Zoom in"))
        bind(self.fit_button, "setToolTip", tr("Fit the entire recording"))
        for button in (self.zoom_out, self.zoom_in, self.fit_button):
            transport.addWidget(button)
        layout.addLayout(transport)
        self.file_label = ElidedLabel(
            tr("Local processing • recordings are not sent to the cloud")
        )
        layout.addWidget(self.file_label)
        body = self.body = W.QSplitter(C.Qt.Orientation.Horizontal)
        body.setChildrenCollapsible(False)
        layout.addWidget(body, 1)
        self.controls = W.QWidget()
        self.controls.setMinimumWidth(246)
        self.controls.setMaximumWidth(350)
        left = self.controls_layout = W.QVBoxLayout(self.controls)
        left.setContentsMargins(0, 0, 12, 0)
        tabs = self.tool_tabs = W.QTabWidget()
        tabs.setUsesScrollButtons(False)
        left.addWidget(tabs)
        clean = W.QWidget()
        clean_layout = W.QVBoxLayout(clean)
        add_tab(tabs, clean, tr("Cleanup"))
        clean_layout.addWidget(label(tr("01  NOISE REDUCTION"), "section"))
        self.method = W.QComboBox()
        for name, key in [
            (tr("Spectral Gate · adaptive"), "spectral"),
            (tr("RNNoise · neural"), "rnnoise"),
            (tr("DeepFilterNet3 · neural"), "deepfilter"),
            (tr("DSP · 50 Hz hum / low frequencies"), "dsp"),
        ]:
            add_item(self.method, name, key)
        clean_layout.addWidget(self.method)
        self.strength = W.QSlider(C.Qt.Orientation.Horizontal)
        self.strength.setRange(0, 100)
        self.strength.setValue(80)
        self.strength_label = label(tr("Cleanup strength · 80%"), "muted")
        self.strength.valueChanged.connect(
            lambda v: bind(
                self.strength_label, "setText", tr("Cleanup strength · {v0}%", v0=v)
            )
        )
        clean_layout.addWidget(self.strength_label)
        clean_layout.addWidget(self.strength)
        self.use_noise = W.QCheckBox()
        bind(self.use_noise, "setText", tr("Use noise profile"))
        clean_layout.addWidget(self.use_noise)
        self.noise_button = self.button(
            tr("Capture noise from selection"), self.capture_noise
        )
        clean_layout.addWidget(self.noise_button)
        self.noise_label = label(tr("Select at least 0.1 s without speech."), "muted")
        self.noise_label.setWordWrap(True)
        clean_layout.addWidget(self.noise_label)
        self.clean_button = self.button(tr("Clean"), self.clean, True)
        clean_layout.addWidget(self.clean_button)
        clean_layout.addStretch()
        level = W.QWidget()
        level_layout = W.QVBoxLayout(level)
        add_tab(tabs, level, tr("Level"))
        level_layout.addWidget(label(tr("LOUDNESS NORMALIZATION"), "section"))
        self.norm_mode = W.QComboBox()
        add_item(self.norm_mode, tr("Integrated loudness · LUFS"), "lufs")
        add_item(self.norm_mode, tr("Peak · dBFS"), "peak")
        level_layout.addWidget(self.norm_mode)
        self.target = W.QDoubleSpinBox()
        self.target.setRange(-36, -1)
        self.target.setValue(-16)
        bind(self.target, "setSuffix", " LUFS")
        self.norm_mode.currentIndexChanged.connect(self.normalization_mode)
        level_layout.addWidget(self.target)
        self.normalize_button = self.button(tr("Normalize"), self.apply_normalize)
        level_layout.addWidget(self.normalize_button)
        note = label(
            tr(
                "Processes the active A/B track, or just the selection if present. The original remains available."
            ),
            "muted",
        )
        note.setWordWrap(True)
        level_layout.addWidget(note)
        level_layout.addStretch()
        self.undo_button = self.button(tr("Undo processing"), self.undo)
        self.undo_button.setIcon(
            self.style().standardIcon(W.QStyle.StandardPixmap.SP_ArrowBack)
        )
        left.addWidget(self.undo_button)
        speech = W.QWidget()
        speech_layout = W.QVBoxLayout(speech)
        add_tab(tabs, speech, tr("Speech"))
        speech_layout.addWidget(label(tr("01  SPEECH DETECTION · SILERO"), "section"))
        self.threshold = W.QDoubleSpinBox()
        self.threshold.setRange(0.1, 0.95)
        self.threshold.setSingleStep(0.05)
        self.threshold.setValue(0.5)
        self.silence = W.QSpinBox()
        self.silence.setRange(100, 3000)
        self.silence.setValue(350)
        bind(self.silence, "setSuffix", tr(" ms"))
        vad_fields = W.QFormLayout()
        vad_fields.addRow(label(tr("Speech threshold")), self.threshold)
        vad_fields.addRow(label(tr("Silence")), self.silence)
        bind(self.silence, "setToolTip", tr("Silence between speech fragments"))
        speech_layout.addLayout(vad_fields)
        self.detect_button = self.button(tr("Find speech on track"), self.detect, True)
        speech_layout.addWidget(self.detect_button)
        speech_layout.addWidget(label(tr("02  SPEECH TO TEXT · WHISPER"), "section"))
        self.asr_model = W.QComboBox()
        for name in WHISPER_MODELS:
            add_item(self.asr_model, name)
        self.asr_model.setCurrentText("small")
        speech_layout.addWidget(self.asr_model)
        self.language = W.QComboBox()
        for text, key in [
            (tr("Russian"), "ru"),
            (tr("Auto-detect"), "auto"),
            (tr("English"), "en"),
        ]:
            add_item(self.language, text, key)
        speech_layout.addWidget(self.language)
        self.transcribe_button = self.button(
            tr("Transcribe selection"), self.transcribe, True
        )
        speech_layout.addWidget(self.transcribe_button)
        hint = label(
            tr(
                "Click a speech region or drag to select audio. Only the selection on the active track is transcribed."
            ),
            "muted",
        )
        hint.setWordWrap(True)
        speech_layout.addWidget(hint)
        self.speech_hint = hint
        bind(
            self.transcribe_button,
            "setToolTip",
            hint._language_bindings[("setText", None)][0],
        )
        speech_layout.addStretch()
        events = W.QWidget()
        event_layout = W.QVBoxLayout(events)
        add_tab(tabs, events, tr("Events"))
        event_layout.addWidget(label(tr("FLEXSED · SEARCH BY DESCRIPTION"), "section"))
        event_hint = label(
            tr(
                "Enter events in English separated by semicolons. The model also works with Russian recordings. Results are markers for listening."
            ),
            "muted",
        )
        event_hint.setWordWrap(True)
        event_layout.addWidget(event_hint)
        self.event_queries = W.QLineEdit("Speech; Conversation; Whispering")
        bind(self.event_queries, "setPlaceholderText", "Speech; Dog; Door")
        event_layout.addWidget(self.event_queries)
        event_layout.addWidget(label(tr("Model score threshold"), "muted"))
        self.event_threshold = W.QDoubleSpinBox()
        self.event_threshold.setRange(0.05, 0.95)
        self.event_threshold.setSingleStep(0.05)
        self.event_threshold.setValue(0.5)
        event_layout.addWidget(self.event_threshold)
        self.event_channel = W.QComboBox()
        add_item(self.event_channel, tr("Each channel separately"), 0)
        event_layout.addWidget(self.event_channel)
        self.events_button = self.button(tr("Find events"), self.detect_events, True)
        event_layout.addWidget(self.events_button)
        note = label(
            tr(
                "Analyzes the selection or the entire active A/B track. Colored bars below the waveform mark events. Audio is unchanged. Review quiet speech by listening."
            ),
            "muted",
        )
        note.setWordWrap(True)
        event_layout.addWidget(note)
        self.event_note = note
        bind(
            self.events_button,
            "setToolTip",
            note._language_bindings[("setText", None)][0],
        )
        event_layout.addStretch()
        body.addWidget(self.controls)
        workspace = self.workspace = W.QSplitter(C.Qt.Orientation.Vertical)
        workspace.setChildrenCollapsible(False)
        body.addWidget(workspace)
        self.timeline = Timeline()
        workspace.addWidget(self.timeline)
        self.timeline.selectionChanged.connect(self.select_range)
        self.timeline.seekRequested.connect(self.seek)
        self.timeline.regionClicked.connect(self.select_region)
        self.timeline.eventClicked.connect(self.select_event)
        self.results_host = W.QStackedWidget()
        workspace.addWidget(self.results_host)
        bottom = self.results_splitter = W.QSplitter(C.Qt.Orientation.Horizontal)
        bottom.setChildrenCollapsible(False)
        self.results_tabs = W.QTabWidget()
        self.results_host.addWidget(bottom)
        self.results_host.addWidget(self.results_tabs)
        regions_box = self.regions_box = W.QWidget()
        regions_layout = W.QVBoxLayout(regions_box)
        regions_layout.setContentsMargins(0, 0, 6, 0)
        regions_header = W.QHBoxLayout()
        self.regions_label = label(tr("MARKERS"), "section")
        regions_header.addWidget(self.regions_label)
        regions_header.addStretch()
        self.add_region_button = self.button("+", self.add_region)
        self.delete_region_button = self.button("−", self.delete_region)
        bind(
            self.add_region_button, "setToolTip", tr("Add selection as a speech region")
        )
        bind(
            self.delete_region_button,
            "setToolTip",
            tr("Delete the selected speech region"),
        )
        regions_header.addWidget(self.add_region_button)
        regions_header.addWidget(self.delete_region_button)
        regions_layout.addLayout(regions_header)
        self.table = W.QTableWidget(0, 3)
        bind(self.table, "setHorizontalHeaderLabels", ["№", tr("Start"), tr("Length")])
        self.table.horizontalHeader().setSectionResizeMode(
            W.QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(
            W.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(W.QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.table_selected)
        self.table.cellDoubleClicked.connect(lambda *_: self.play_selection())
        self.region_tabs = W.QTabWidget()
        add_tab(self.region_tabs, self.table, tr("Speech"))
        self.event_table = W.QTableWidget(0, 4)
        bind(
            self.event_table,
            "setHorizontalHeaderLabels",
            [tr("Event"), tr("Start"), tr("Channel"), tr("Score")],
        )
        self.event_table.horizontalHeader().setSectionResizeMode(
            W.QHeaderView.ResizeMode.Stretch
        )
        self.event_table.verticalHeader().hide()
        self.event_table.setSelectionBehavior(
            W.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.event_table.setSelectionMode(
            W.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.event_table.setEditTriggers(W.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.event_table.itemSelectionChanged.connect(self.event_selected)
        self.event_table.cellDoubleClicked.connect(lambda *_: self.play_selection())
        add_tab(self.region_tabs, self.event_table, tr("Events"))
        self.region_tabs.currentChanged.connect(lambda _: self.refresh())
        regions_layout.addWidget(self.region_tabs)
        region_actions = W.QHBoxLayout()
        self.listen_button = self.button(tr("Listen"), self.play_selection)
        self.listen_button.setIcon(
            self.style().standardIcon(W.QStyle.StandardPixmap.SP_MediaPlay)
        )
        self.labels_button = self.button(tr("Markers JSON"), self.export_regions)
        region_actions.addWidget(self.listen_button)
        region_actions.addWidget(self.labels_button)
        regions_layout.addLayout(region_actions)
        bottom.addWidget(regions_box)
        transcript_box = self.transcript_box = W.QWidget()
        text_layout = W.QVBoxLayout(transcript_box)
        text_layout.setContentsMargins(6, 0, 0, 0)
        transcript_title = self.transcript_title = label(
            tr("SELECTION TRANSCRIPT"), "section"
        )
        transcript_title.setWordWrap(True)
        text_layout.addWidget(transcript_title)
        self.transcript = W.QTextEdit()
        bind(
            self.transcript,
            "setPlaceholderText",
            tr(
                "Recognized text will appear here.\n\nSpeech tab → Transcribe selection.\nYou can edit the text before exporting TXT."
            ),
        )
        text_layout.addWidget(self.transcript)
        text_actions = W.QHBoxLayout()
        self.save_text_button = self.button("TXT", self.export_text)
        bind(self.save_text_button, "setToolTip", tr("Save edited text"))
        self.save_srt_button = self.button("SRT", self.export_srt)
        bind(
            self.save_srt_button,
            "setToolTip",
            tr(
                "Original model transcript with recording timestamps; editor changes are saved in TXT"
            ),
        )
        text_actions.addWidget(self.save_text_button)
        text_actions.addWidget(self.save_srt_button)
        text_layout.addLayout(text_actions)
        bottom.addWidget(transcript_box)
        body.setSizes([300, 1100])
        workspace.setSizes([450, 260])
        bottom.setSizes([420, 640])
        footer = self.footer_layout = W.QHBoxLayout()
        self.message = ElidedLabel(
            tr("Ready. Open a recording, then choose cleanup or speech detection.")
        )
        footer.addWidget(self.message, 1)
        self.progress = W.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedWidth(130)
        self.progress.setTextVisible(False)
        self.progress.hide()
        footer.addWidget(self.progress)
        self.cancel_button = self.button(tr("Cancel task"), self.cancel_job)
        self.cancel_button.setObjectName("danger")
        self.cancel_button.hide()
        footer.addWidget(self.cancel_button)
        layout.addLayout(footer)
        bind(
            self.statusBar(),
            "showMessage",
            tr(
                "VoxLoom Studio {v0} · Offline  •  MatSoftAI  |  Ctrl+wheel: zoom  •  Space: play/pause",
                v0=__version__,
            ),
        )
        self.page_layouts = (clean_layout, level_layout, speech_layout, event_layout)
        for combo in self.controls.findChildren(W.QComboBox):
            combo.setSizeAdjustPolicy(
                W.QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            combo.setMinimumContentsLength(10)
            combo.setSizePolicy(
                W.QSizePolicy.Policy.Expanding, W.QSizePolicy.Policy.Fixed
            )
        self._apply_density()

    def change_language(self):
        code = self.ui_language.currentData()
        apply_language(W.QApplication.instance(), code)
        self.settings.setValue("ui_language", code)
        self.settings.sync()
        retranslate(self)
        self.timeline.update()
        bind(self.message, "setText", tr("Interface language saved."))

    def _apply_density(self):
        if not hasattr(self, "page_layouts"):
            return
        compact = self.height() < 850 or self.width() < 1180
        narrow = self.width() < 1100
        if compact != self._density_mode:
            self._density_mode = compact
            self.setStyleSheet(STYLE + (COMPACT_STYLE if compact else ""))
            self.root_layout.setContentsMargins(
                *((10, 6, 10, 6) if compact else (18, 12, 18, 12))
            )
            self.root_layout.setSpacing(6 if compact else 10)
            for row in (self.header_layout, self.transport_layout, self.footer_layout):
                row.setSpacing(6 if compact else 8)
            self.controls_layout.setContentsMargins(0, 0, 6 if compact else 12, 0)
            self.controls_layout.setSpacing(4 if compact else 8)
            for page in self.page_layouts:
                page.setContentsMargins(6, 6, 6, 6)
                page.setSpacing(5 if compact else 8)
            self.controls.setMaximumWidth(270 if compact else 320)
            self.timeline.setMinimumHeight(180 if compact else 250)
            self.speech_hint.setVisible(not compact)
            self.event_note.setVisible(not compact)
            self.statusBar().setVisible(not compact)
            self.body.setSizes([256 if compact else 300, max(1, self.width() - 300)])
            self.workspace.setSizes(
                [max(180, self.height() * 3 // 5), max(180, self.height() * 2 // 5)]
            )
        if narrow != self._narrow_results:
            self._narrow_results = narrow
            if narrow:
                add_tab(self.results_tabs, self.regions_box, tr("Markers"))
                add_tab(self.results_tabs, self.transcript_box, tr("Text"))
                self.results_host.setCurrentWidget(self.results_tabs)
            else:
                while self.results_tabs.count():
                    self.results_tabs.removeTab(0)
                self.results_splitter.addWidget(self.regions_box)
                self.results_splitter.addWidget(self.transcript_box)
                self.regions_box.show()
                self.transcript_box.show()
                self.results_splitter.setSizes([420, 640])
                self.results_host.setCurrentWidget(self.results_splitter)
        self.tagline.setVisible(self.width() >= 1250 and not compact)

    def active(self):
        return (
            self.result
            if self.a_b.currentData() == "result" and self.result is not None
            else self.source
        )

    def refresh(self):
        loaded, busy = self.source is not None, self.job is not None
        for widget in [
            self.controls,
            self.timeline,
            self.table,
            self.event_table,
            self.a_b,
            self.open_button,
            self.models_button,
            self.ui_language,
        ]:
            widget.setEnabled(not busy)
        for widget in [
            self.play_button,
            self.stop_button,
            self.export_button,
            self.clean_button,
            self.normalize_button,
            self.detect_button,
            self.add_region_button,
            self.delete_region_button,
            self.labels_button,
            self.events_button,
        ]:
            widget.setEnabled(loaded and not busy)
        self.a_b.model().item(1).setEnabled(self.result is not None)
        self.noise_button.setEnabled(loaded and self.selection is not None and not busy)
        self.transcribe_button.setEnabled(
            loaded and self.selection is not None and not busy
        )
        self.listen_button.setEnabled(
            loaded and self.selection is not None and not busy
        )
        self.add_region_button.setEnabled(
            loaded
            and self.selection is not None
            and not busy
            and self.region_tabs.currentIndex() == 0
        )
        self.delete_region_button.setEnabled(
            not busy and self.region_index >= 0 and self.region_tabs.currentIndex() == 0
        )
        self.undo_button.setEnabled(self.result is not None and not busy)
        self.cancel_button.setVisible(busy)
        self.progress.setVisible(busy)
        self.save_srt_button.setEnabled(bool(self.transcript_segments) and not busy)

    def error(self, text):
        bind(self.message, "setText", str(text).splitlines()[0][:180])
        W.QMessageBox.warning(self, "VoxLoom Studio", text)

    def open_file(self):
        if self.job:
            return
        path, _ = W.QFileDialog.getOpenFileName(
            self,
            tr("Open audio recording"),
            self.settings.value("folder", ""),
            tr(
                "Audio (*.wav *.flac *.mp3 *.ogg *.oga *.opus *.aac *.acc *.m4a *.aif *.aiff *.wma *.mp4 *.webm);;All files (*)"
            ),
        )
        if path:
            self.load_path(path)

    def load_path(self, path):
        if self.job:
            return

        def loaded(response, output):
            from .audio import validate

            output = validate(output, response["rate"])
            self.source, self.rate, self.path = (
                output,
                response["rate"],
                str(Path(path).resolve()),
            )
            self.source.setflags(write=False)
            self.result = self.previous = self.noise = None
            self.regions, self.selection, self.region_index = [], None, -1
            self.timeline.selection = None
            self.timeline.cursor = 0.0
            self.events = []
            self.event_analysis = {}
            self.update_events()
            self.event_channel.clear()
            add_item(self.event_channel, tr("Each channel separately"), 0)
            for channel in range(output.shape[1]):
                add_item(
                    self.event_channel, tr("Channel {v0}", v0=channel + 1), channel + 1
                )
            self.transcript.clear()
            self.transcript_segments = []
            self.use_noise.setChecked(False)
            bind(
                self.noise_label, "setText", tr("Select at least 0.1 s without speech.")
            )
            self.a_b.setCurrentIndex(0)
            self.timeline.set_audio(self.source, None, self.rate)
            self.timeline.fit()
            self.update_regions()
            self.select_range(0, 0)
            bind(
                self.file_label,
                "setText",
                f"{Path(path).name}   •   {self.rate:,} Hz   •   {output.shape[1]} ch   •   {len(output) / self.rate:.2f} s",
            )
            self.settings.setValue("folder", str(Path(path).parent))

        self.run_job(
            {"action": "load", "path": str(path)},
            tr("Opening and decoding the recording…"),
            loaded,
        )

    def run_job(self, request, title, callback, data=None, noise=None):
        if self.job:
            return
        self.player.pause()
        job = Job(self)
        self.job = job
        bind(self.message, "setText", title)
        self.refresh()

        def finished(response, output):
            self.job = None
            try:
                if response.get("ok"):
                    callback(response, output)
                    bind(self.message, "setText", response.get("message", tr("Done.")))
                elif job.cancelled:
                    bind(self.message, "setText", response["error"])
                else:
                    LOG.error(
                        "Worker failed: %s",
                        response.get("traceback", response.get("error")),
                    )
                    self.error(response.get("error", tr("Processing error.")))
            except Exception as exc:
                LOG.exception("Applying worker result failed")
                self.error(str(exc))
            finally:
                job.deleteLater()
                self.refresh()

        job.finished.connect(finished)
        try:
            job.start(request, data, noise)
        except Exception as exc:
            job.cleanup()
            LOG.exception("Starting worker failed")
            self.job = None
            job.deleteLater()
            self.refresh()
            self.error(str(exc))

    def cancel_job(self):
        if self.job:
            self.job.cancel()

    def processing_range(self):
        if self.selection:
            return bounds(*self.selection, self.rate, len(self.source))
        return 0, len(self.source)

    def process_audio(self, request, title, noise=None):
        if self.source is None or self.job:
            return
        current = self.active()
        a, b = self.processing_range()

        def completed(response, output):
            if output.shape != current[a:b].shape or not np.isfinite(output).all():
                raise ValueError(tr("Invalid processing result."))
            self.previous = self.result
            updated = current.copy()
            # Short edge fades avoid clicks on partial edits; the file edges are untouched.
            fade = min(round(self.rate * 0.005), (b - a) // 2)
            if a > 0 and fade:
                weights = np.linspace(0, 1, fade)[:, None]
                output[:fade] = (
                    current[a : a + fade] * (1 - weights) + output[:fade] * weights
                )
            if b < len(current) and fade:
                weights = np.linspace(1, 0, fade)[:, None]
                output[-fade:] = (
                    current[b - fade : b] * (1 - weights) + output[-fade:] * weights
                )
            updated[a:b] = output
            self.result = updated
            self.invalidate_result_events()
            self.a_b.setCurrentIndex(1)
            self.timeline.set_audio(self.source, self.result, self.rate)

        self.run_job(
            dict(request, rate=self.rate), title, completed, current[a:b], noise
        )

    def clean(self):
        if self.use_noise.isChecked() and self.noise is None:
            return self.error(
                tr(
                    "Select a fragment without speech, then click Capture noise from selection."
                )
            )
        self.process_audio(
            {
                "action": "denoise",
                "method": self.method.currentData(),
                "strength": self.strength.value() / 100,
            },
            tr("Reducing noise…"),
            self.noise
            if self.use_noise.isChecked() and self.method.currentData() == "spectral"
            else None,
        )

    def capture_noise(self):
        if not self.selection or self.source is None:
            return
        a, b = self.processing_range()
        if b - a < self.rate * 0.1:
            return self.error(
                tr("Select at least 0.1 seconds without speech for the noise profile.")
            )
        self.noise = self.active()[a:b].copy()
        self.use_noise.setChecked(True)
        bind(
            self.noise_label,
            "setText",
            tr(
                "Profile: {v0:.2f}–{v1:.2f} s. Used by Spectral Gate only.",
                v0=a / self.rate,
                v1=b / self.rate,
            ),
        )

    def normalization_mode(self):
        peak = self.norm_mode.currentData() == "peak"
        self.target.setRange(-36, -1)
        self.target.setValue(-1 if peak else -16)
        bind(self.target, "setSuffix", " dBFS" if peak else " LUFS")

    def apply_normalize(self):
        self.process_audio(
            {
                "action": "normalize",
                "mode": self.norm_mode.currentData(),
                "target": self.target.value(),
            },
            tr("Normalizing loudness…"),
        )

    def undo(self):
        if self.job or self.result is None:
            return
        self.player.pause()
        self.result, self.previous = self.previous, None
        self.invalidate_result_events()
        if self.result is None:
            self.a_b.setCurrentIndex(0)
        self.timeline.set_audio(self.source, self.result, self.rate)
        bind(self.message, "setText", tr("Last processing step undone."))
        self.refresh()

    def detect(self):
        if self.source is None:
            return

        def completed(response, output):
            self.regions = [Region(**r) for r in response["regions"]]
            self.update_regions()
            self.select_range(0, 0)
            self.region_tabs.setCurrentIndex(0)
            if self._narrow_results:
                self.results_tabs.setCurrentWidget(self.regions_box)
            response["message"] = tr(
                "Speech regions found: {v0}.", v0=len(self.regions)
            )

        self.run_job(
            {
                "action": "detect",
                "rate": self.rate,
                "threshold": self.threshold.value(),
                "silence_ms": self.silence.value(),
            },
            tr("Silero VAD: finding speech…"),
            completed,
            self.active(),
        )

    def update_regions(self):
        self.timeline.regions = self.regions
        self.timeline.update()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.regions))
        for row, region in enumerate(self.regions):
            for col, value in enumerate(
                [
                    f"{row + 1:02}",
                    tr("{v0:.3f} s", v0=region.start),
                    tr("{v0:.3f} s", v0=region.end - region.start),
                ]
            ):
                item = W.QTableWidgetItem()
                bind(item, "setText", value)
                self.table.setItem(row, col, item)
        self.table.clearSelection()
        self.table.blockSignals(False)
        bind(
            self.region_tabs, "setTabText", 0, tr("Speech · {v0}", v0=len(self.regions))
        )
        self.region_index = -1

    def detect_events(self):
        if self.source is None or self.job:
            return
        from .events import available, parse_queries

        try:
            queries = parse_queries(self.event_queries.text())
            if not available():
                raise ValueError(
                    tr(
                        "FlexSED is missing. Install the FlexSED pack via Models → Install pack."
                    )
                )
        except ValueError as exc:
            return self.error(str(exc))
        a, b = self.processing_range()
        track = self.a_b.currentData()

        def completed(response, output):
            offset = a / self.rate
            self.events = [
                dict(e, start=e["start"] + offset, end=e["end"] + offset, track=track)
                for e in response["events"]
            ]
            self.event_analysis = {
                k: response[k]
                for k in ("model", "queries", "threshold", "frame_rate", "score_kind")
            }
            self.event_analysis.update(track=track, start=offset, end=b / self.rate)
            self.update_events()
            self.select_range(0, 0)
            self.region_tabs.setCurrentIndex(1)
            if self._narrow_results:
                self.results_tabs.setCurrentWidget(self.regions_box)
            response["message"] = tr(
                "FlexSED: {v0} events. Listen to review the model predictions.",
                v0=len(self.events),
            )

        self.run_job(
            dict(
                action="events",
                rate=self.rate,
                queries=queries,
                threshold=self.event_threshold.value(),
                channel=self.event_channel.currentData(),
            ),
            tr("FlexSED: analyzing sound events…"),
            completed,
            self.active()[a:b],
        )

    def invalidate_result_events(self):
        if self.event_analysis.get("track") == "result":
            self.events = []
            self.event_analysis = {}
            self.update_events()

    def update_events(self):
        self.timeline.events = self.events
        self.timeline.update()
        bind(
            self.region_tabs, "setTabText", 1, tr("Events · {v0}", v0=len(self.events))
        )
        self.event_table.blockSignals(True)
        self.event_table.setRowCount(len(self.events))
        for row, event in enumerate(self.events):
            values = [
                event["label"],
                tr("{v0:.2f} s", v0=event["start"]),
                str(event["channel"]),
                f"{event['score']:.2f}",
            ]
            for col, value in enumerate(values):
                item = W.QTableWidgetItem()
                bind(item, "setText", value)
                bind(
                    item,
                    "setToolTip",
                    tr(
                        "{v0:.3f}–{v1:.3f} s · {v2} · model score, not a guarantee of an event",
                        v0=event["start"],
                        v1=event["end"],
                        v2=event["track"],
                    ),
                )
                if col == 0:
                    item.setForeground(G.QColor(event["color"]))
                self.event_table.setItem(row, col, item)
        self.event_table.clearSelection()
        self.event_table.blockSignals(False)

    def event_selected(self):
        rows = self.event_table.selectionModel().selectedRows()
        if rows:
            self.select_event(rows[0].row())

    def select_event(self, index):
        if self.job or not 0 <= index < len(self.events):
            return
        event = self.events[index]
        self.player.pause()
        self.a_b.setCurrentIndex(
            1 if event["track"] == "result" and self.result is not None else 0
        )
        self.select_range(event["start"], event["end"])
        self.region_tabs.setCurrentIndex(1)
        self.event_table.blockSignals(True)
        self.event_table.selectRow(index)
        self.event_table.blockSignals(False)
        self.timeline.cursor = event["start"]
        if (
            not self.timeline.left
            <= event["start"]
            < self.timeline.left + self.timeline.span
        ):
            self.timeline.left = max(
                0, min(event["start"], self.timeline.duration - self.timeline.span)
            )
        self.timeline.update()

    def table_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            self.select_region(rows[0].row())

    def select_region(self, index):
        if self.job or not 0 <= index < len(self.regions):
            return
        self.player.pause()
        region = self.regions[index]
        self.select_range(region.start, region.end)
        self.region_index = index
        self.table.blockSignals(True)
        self.table.selectRow(index)
        self.table.blockSignals(False)
        self.timeline.cursor = region.start
        self.transcript.setPlainText(region.text)
        self.transcript_segments = []
        if (
            not self.timeline.left
            <= region.start
            < self.timeline.left + self.timeline.span
        ):
            self.timeline.left = max(
                0, min(region.start, self.timeline.duration - self.timeline.span)
            )
        self.timeline.update()
        self.refresh()

    def select_range(self, start, end):
        self.transcript.clear()
        self.transcript_segments = []
        self.selection = (start, end) if end > start else None
        self.timeline.selection = self.selection
        self.region_index = -1
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.blockSignals(False)
        self.event_table.blockSignals(True)
        self.event_table.clearSelection()
        self.event_table.blockSignals(False)
        bind(
            self.selection_label,
            "setText",
            tr("{v0:.3f} → {v1:.3f} s  /  {v2:.3f} s", v0=start, v1=end, v2=end - start)
            if self.selection
            else tr("Whole file"),
        )
        self.timeline.update()
        self.refresh()

    def add_region(self):
        if not self.selection or self.job:
            return
        start, end = self.selection
        if any(start < r.end and end > r.start for r in self.regions):
            return self.error(tr("The selection overlaps an existing region."))
        self.regions.append(Region(start, end))
        self.regions.sort(key=lambda r: r.start)
        self.update_regions()

    def delete_region(self):
        if self.job or not 0 <= self.region_index < len(self.regions):
            return
        del self.regions[self.region_index]
        self.update_regions()
        self.select_range(0, 0)

    def transcribe(self):
        if not self.selection or self.source is None:
            return
        a, b = self.processing_range()
        region_index = self.region_index

        def completed(response, output):
            self.transcript.setPlainText(response["text"])
            if self._narrow_results:
                self.results_tabs.setCurrentWidget(self.transcript_box)
            self.transcript_segments = [
                dict(s, start=s["start"] + a / self.rate, end=s["end"] + a / self.rate)
                for s in response["segments"]
            ]
            if 0 <= region_index < len(self.regions):
                self.regions[region_index].text = response["text"]
            response["message"] = tr(
                "Transcription complete. Language: {v0}.", v0=response["language"]
            )
            if response.get("review_count"):
                response["message"] += tr(
                    " Listen to review: {v0}.", v0=response["review_count"]
                )

        self.run_job(
            {
                "action": "transcribe",
                "rate": self.rate,
                "model": self.asr_model.currentText(),
                "language": self.language.currentData(),
            },
            tr("Whisper: transcribing the selected fragment…"),
            completed,
            self.active()[a:b],
        )

    def seek(self, seconds):
        self.player.pause()
        self.timeline.cursor = seconds

    def switch_track(self):
        playing = self.player.playing
        self.player.pause()
        if playing:
            self.toggle_play()

    def toggle_play(self):
        if self.source is None or self.job:
            return
        if self.player.playing:
            self.player.pause()
            return
        a, b = self.processing_range()
        start = round(self.timeline.cursor * self.rate)
        if not a <= start < b:
            start = a
        try:
            self.player.play(self.active(), self.rate, start, b)
        except Exception as exc:
            self.error(tr("Could not open the playback device: {v0}", v0=exc))

    def play_selection(self):
        if self.selection:
            self.player.pause()
            self.timeline.cursor = self.selection[0]
            self.toggle_play()

    def stop(self):
        self.player.pause()
        self.timeline.cursor = self.selection[0] if self.selection else 0.0
        self.timeline.update()

    def tick(self):
        if self.player.stream is not None:
            self.timeline.cursor = self.player.position / self.rate
            self.timeline.update()
        bind(
            self.play_button,
            "setText",
            tr("Pause") if self.player.playing else tr("Play"),
        )
        self.play_button.setIcon(
            self.style().standardIcon(
                W.QStyle.StandardPixmap.SP_MediaPause
                if self.player.playing
                else W.QStyle.StandardPixmap.SP_MediaPlay
            )
        )
        t = self.timeline.cursor
        bind(self.clock, "setText", f"{int(t // 60):02}:{t % 60:06.3f}")

    def export_audio(self):
        if self.source is None or self.job:
            return
        a, b = self.processing_range()
        name = (
            Path(self.path).stem
            + ("_fragment" if self.selection else "_restored")
            + ".wav"
        )
        path, _ = W.QFileDialog.getSaveFileName(
            self,
            tr("Save active track / selection"),
            str(Path(self.path).with_name(name)),
            "WAV (*.wav);;FLAC (*.flac);;OGG (*.ogg)",
        )
        if not path:
            return
        if Path(path).resolve() == Path(self.path).resolve():
            return self.error(
                tr("The original file is protected. Choose another name.")
            )
        self.run_job(
            {"action": "export", "path": path, "rate": self.rate},
            tr("Exporting audio…"),
            lambda *_: None,
            self.active()[a:b],
        )

    def write_text(self, title, extension, content):
        path, _ = W.QFileDialog.getSaveFileName(
            self,
            title,
            "transcript." + extension,
            f"{extension.upper()} (*.{extension})",
        )
        if path:
            try:
                if self.path and Path(path).resolve() == Path(self.path).resolve():
                    raise ValueError(
                        tr("The original file is protected. Choose another name.")
                    )
                write_text_atomic(path, content)
                bind(self.message, "setText", tr("Saved: {v0}", v0=path))
            except (OSError, ValueError) as exc:
                self.error(str(exc))

    def export_text(self):
        self.write_text(tr("Save text"), "txt", self.transcript.toPlainText())

    def export_srt(self):
        def stamp(seconds):
            ms = round(seconds * 1000)
            return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"

        body = "\n\n".join(
            f"{i + 1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}"
            for i, s in enumerate(self.transcript_segments)
        )
        self.write_text(
            tr("Save subtitles with original recording timestamps"), "srt", body + "\n"
        )

    def export_regions(self):
        data = {
            "schema": "voxloom.regions.v1",
            "source": self.path,
            "rate": self.rate,
            "frames": len(self.source),
            "regions": [r.as_dict() for r in self.regions],
            "events": self.events,
            "event_analysis": self.event_analysis,
        }
        self.write_text(
            tr("Save speech regions and events"),
            "json",
            json.dumps(data, ensure_ascii=False, indent=2),
        )

    def models(self):
        from .modules import catalog_html

        dialog = W.QDialog(self)
        dialog.setWindowTitle(tr("VoxLoom models"))
        layout = W.QVBoxLayout(dialog)
        browser = W.QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.document().setDefaultStyleSheet("a { color: #75dfca; }")
        browser.setHtml(catalog_html())
        layout.addWidget(browser, 1)
        folder = label(
            tr("Models folder: {path}", path=str(writable_models())), "muted"
        )
        folder.setWordWrap(True)
        folder.setTextInteractionFlags(C.Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(folder)
        actions = W.QHBoxLayout()
        install = self.button(tr("Install pack…"), lambda: self.install_models(dialog))
        install.setEnabled(self.job is None)
        actions.addWidget(install)
        actions.addWidget(self.button(tr("Close"), dialog.accept))
        layout.addLayout(actions)
        available = self.screen().availableGeometry().size() - C.QSize(32, 48)
        dialog.resize(C.QSize(760, 600).boundedTo(available))
        dialog.exec()

    def install_models(self, dialog=None):
        if self.job:
            return
        paths, _ = W.QFileDialog.getOpenFileNames(
            self,
            tr("Select VoxLoom model packs from GitHub Releases"),
            "",
            "VoxLoom model packs (*.zip)",
        )
        if not paths:
            return
        if dialog is not None:
            dialog.accept()
        self.run_job(
            {"action": "install_models", "paths": paths},
            tr("Checking and installing models…"),
            lambda *_: None,
        )

    def dragEnterEvent(self, event):
        if (
            not self.job
            and event.mimeData().hasUrls()
            and event.mimeData().urls()[0].isLocalFile()
        ):
            event.acceptProposedAction()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_density()

    def dropEvent(self, event):
        if not self.job:
            self.load_path(event.mimeData().urls()[0].toLocalFile())

    def closeEvent(self, event):
        self.player.pause()
        if self.job:
            self.job.cancel()
            self.job.process.waitForFinished(3000)
        event.accept()

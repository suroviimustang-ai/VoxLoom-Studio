"""Classic menus sharing the workspace's commands and availability rules."""

from PyQt6 import QtCore as C
from PyQt6 import QtGui as G
from PyQt6 import QtWidgets as W

from . import __version__
from .i18n import tr
from .ui_language import bind


class WorkspaceMenus:
    def __init__(self, window):
        self.window = window
        self.actions = {}
        self.linked = []
        self.idle = []
        self.loaded = []
        bar = window.menuBar()
        # Keep the same visible top menu on all three desktop platforms.
        bar.setNativeMenuBar(False)
        self.file = self.menu(bar, tr("&File"))
        self.link(self.file, "open", tr("&Open audio…"), window.open_button, "Ctrl+O")
        self.link(
            self.file, "export", tr("&Export audio…"), window.export_button, "Ctrl+S"
        )
        self.link(
            self.file, "text", tr("Save transcript as &TXT…"), window.save_text_button
        )
        self.link(
            self.file, "srt", tr("Save subtitles as &SRT…"), window.save_srt_button
        )
        self.link(self.file, "markers", tr("Export &markers…"), window.labels_button)
        self.file.addSeparator()
        self.action(self.file, "exit", tr("E&xit"), window.close, "Ctrl+Q")

        self.edit = self.menu(bar, tr("&Edit"))
        self.link(
            self.edit,
            "undo_processing",
            tr("Undo &processing"),
            window.undo_button,
            "Ctrl+Alt+Z",
        )
        self.edit.addSeparator()
        # Native editor shortcuts remain owned by the focused text widget.
        for key, title in (
            ("undo", tr("&Undo text edit")),
            ("redo", tr("&Redo text edit")),
            ("cut", tr("Cu&t")),
            ("copy", tr("&Copy")),
            ("paste", tr("&Paste")),
            ("selectAll", tr("Select &all text")),
        ):
            self.action(
                self.edit, key, title, lambda method=key: self.edit_text(method)
            )

        self.view = self.menu(bar, tr("&View"))
        self.loaded.append(
            self.action(
                self.view, "zoom_in", tr("Zoom &in"), lambda: window.timeline.zoom(0.7)
            )
        )
        self.loaded.append(
            self.action(
                self.view,
                "zoom_out",
                tr("Zoom &out"),
                lambda: window.timeline.zoom(1.4),
            )
        )
        self.loaded.append(
            self.action(
                self.view, "fit", tr("Fit &whole recording"), window.timeline.fit
            )
        )
        self.view.addSeparator()
        for index, title in enumerate(
            (tr("&Cleanup"), tr("&Level"), tr("&Speech"), tr("&Events"))
        ):
            self.idle.append(
                self.action(
                    self.view,
                    f"page_{index}",
                    title,
                    lambda i=index: window.tool_tabs.setCurrentIndex(i),
                )
            )
        self.view.addSeparator()
        self.languages = self.menu(self.view, tr("Interface &language"))
        group = G.QActionGroup(window)
        group.setExclusive(True)
        for code, title in (("en", "English"), ("ru", "Русский")):
            action = self.action(
                self.languages,
                code,
                title,
                lambda c=code: window.ui_language.setCurrentIndex(
                    window.ui_language.findData(c)
                ),
            )
            action.setCheckable(True)
            group.addAction(action)
            self.idle.append(action)

        self.process = self.menu(bar, tr("&Process"))
        for key, title, button in (
            ("clean", tr("&Clean audio"), window.clean_button),
            ("normalize", tr("&Normalize audio"), window.normalize_button),
            ("speech", tr("Find &speech"), window.detect_button),
            ("events", tr("Find &events"), window.events_button),
            ("transcribe", tr("&Transcribe selection"), window.transcribe_button),
        ):
            self.link(self.process, key, title, button)
        self.process.addSeparator()
        self.link(self.process, "models", tr("&Models…"), window.models_button)
        self.action(self.process, "cancel", tr("Cancel &task"), window.cancel_job)

        self.about = self.menu(bar, tr("&About"))
        self.action(self.about, "about", tr("&About VoxLoom…"), self.show_about)
        self.action(self.about, "website", tr("Project on &GitHub"), self.open_website)
        for menu in (self.file, self.edit, self.view, self.process, self.about):
            menu.aboutToShow.connect(self.refresh)

    def menu(self, parent, title):
        menu = W.QMenu(self.window)
        bind(menu, "setTitle", title)
        parent.addMenu(menu)
        return menu

    def action(self, menu, key, title, callback, shortcut=None):
        action = G.QAction(self.window)
        action.setMenuRole(G.QAction.MenuRole.NoRole)
        bind(action, "setText", title)
        if shortcut:
            action.setShortcut(G.QKeySequence(shortcut))
        action.triggered.connect(lambda checked=False: callback())
        menu.addAction(action)
        self.actions[key] = action
        return action

    def link(self, menu, key, title, button, shortcut=None):
        action = self.action(menu, key, title, button.click, shortcut)
        self.linked.append((action, button))

    def editor(self):
        widget = self.window.focusWidget()
        if isinstance(widget, (W.QLineEdit, W.QTextEdit, W.QPlainTextEdit)):
            return widget
        return self.window.transcript

    def edit_text(self, method):
        editor = self.editor()
        if editor.isEnabled() and (
            method in ("copy", "selectAll") or not editor.isReadOnly()
        ):
            getattr(editor, method)()

    def refresh(self):
        window = self.window
        idle = window.job is None
        for action, button in self.linked:
            action.setEnabled(button.isEnabled())
        self.actions["text"].setEnabled(idle and bool(window.transcript.toPlainText()))
        self.actions["cancel"].setEnabled(not idle)
        for action in self.idle:
            action.setEnabled(idle)
        for action in self.loaded:
            action.setEnabled(idle and window.source is not None)
        for code in ("en", "ru"):
            self.actions[code].setChecked(window.ui_language.currentData() == code)
        editor = self.editor()
        line = isinstance(editor, W.QLineEdit)
        selection = (
            editor.hasSelectedText() if line else editor.textCursor().hasSelection()
        )
        editable = idle and editor.isEnabled() and not editor.isReadOnly()
        self.actions["undo"].setEnabled(
            editable
            and (
                editor.isUndoAvailable()
                if line
                else editor.document().isUndoAvailable()
            )
        )
        self.actions["redo"].setEnabled(
            editable
            and (
                editor.isRedoAvailable()
                if line
                else editor.document().isRedoAvailable()
            )
        )
        self.actions["cut"].setEnabled(editable and selection)
        self.actions["copy"].setEnabled(editor.isEnabled() and selection)
        mime = W.QApplication.clipboard().mimeData()
        self.actions["paste"].setEnabled(
            editable and mime is not None and mime.hasText()
        )
        self.actions["selectAll"].setEnabled(editor.isEnabled())

    def show_about(self):
        W.QMessageBox.about(
            self.window,
            tr("About VoxLoom"),
            tr(
                "VoxLoom Studio {version}\n\nLocal audio cleanup, speech detection and transcription.\nProcessing runs on your computer. Model outputs should be checked by listening.\n\nMatSoftAI · GPL-3.0-only\nDependencies and models retain their own licenses, included in the application.",
                version=__version__,
            ),
        )

    def open_website(self):
        if not G.QDesktopServices.openUrl(
            C.QUrl("https://github.com/suroviimustang-ai/VoxLoom-Studio")
        ):
            self.window.error(
                tr(
                    "Could not open the browser. Visit github.com/suroviimustang-ai/VoxLoom-Studio."
                )
            )

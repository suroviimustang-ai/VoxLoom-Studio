"""Qt language settings and explicit bindings for application-owned UI text."""

from PyQt6 import QtCore as C
from PyQt6 import QtWidgets as W

from .i18n import Message, language, render, set_language


def _translated(value):
    if isinstance(value, Message):
        return True
    return isinstance(value, (tuple, list)) and any(_translated(v) for v in value)


def bind(widget, method, *arguments):
    """Set a property and retain only localized arguments for future changes."""
    indexed = method in ("setItemText", "setTabText")
    key = (method, arguments[0] if indexed else None)
    bindings = getattr(widget, "_language_bindings", {})
    if _translated(arguments):
        bindings[key] = arguments
    else:
        bindings.pop(key, None)
    widget._language_bindings = bindings
    return getattr(widget, method)(*render(arguments))


def add_item(combo, text, *data):
    combo.addItem(str(text), *data)
    bind(combo, "setItemText", combo.count() - 1, text)


def add_tab(tabs, widget, text):
    index = tabs.addTab(widget, str(text))
    bind(tabs, "setTabText", index, text)
    return index


def retranslate(root):
    """Update labels only; selection, audio, input fields and jobs stay intact."""
    for widget in [root, *root.findChildren(C.QObject)]:
        for (method, index), args in list(
            getattr(widget, "_language_bindings", {}).items()
        ):
            if index is not None and index >= widget.count():
                continue
            blocker = C.QSignalBlocker(widget)
            getattr(widget, method)(*render(args))
            del blocker
        if isinstance(widget, W.QTableWidget):
            for row in range(widget.rowCount()):
                for column in range(widget.columnCount()):
                    item = widget.item(row, column)
                    if item:
                        for (method, _), args in getattr(
                            item, "_language_bindings", {}
                        ).items():
                            getattr(item, method)(*render(args))
    root.update()


def apply_language(app, code):
    set_language(code)
    previous = getattr(app, "_qt_language", None)
    if previous:
        app.removeTranslator(previous)
    translator = C.QTranslator(app)
    if language() == "ru":
        translator.load(
            "qtbase_ru",
            C.QLibraryInfo.path(C.QLibraryInfo.LibraryPath.TranslationsPath),
        )
        app.installTranslator(translator)
    app._qt_language = translator
    if previous:
        previous.deleteLater()
    C.QLocale.setDefault(C.QLocale("ru_RU" if language() == "ru" else "en_US"))


def initialize(app, settings=None):
    settings = settings if settings is not None else C.QSettings()
    apply_language(app, settings.value("ui_language", "en"))

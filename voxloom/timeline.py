from __future__ import annotations

import math

import numpy as np
from PyQt6 import QtCore as C
from PyQt6 import QtGui as G
from PyQt6 import QtWidgets as W

from .i18n import tr
from .ui_language import bind


class Timeline(W.QWidget):
    selectionChanged = C.pyqtSignal(float, float)
    seekRequested = C.pyqtSignal(float)
    regionClicked = C.pyqtSignal(int)
    eventClicked = C.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(290)
        self.setMouseTracking(True)
        self.setFocusPolicy(C.Qt.FocusPolicy.StrongFocus)
        self.data = [None, None]
        self.envelopes = [None, None]
        self.rate = 48000
        self.duration = 0.0
        self.left, self.span = 0.0, 10.0
        self.regions = []
        self.events = []
        self.event_hits = []
        self.selection = None
        self.cursor = 0.0
        self.anchor = None
        self.pan_anchor = None
        self.amplitude = 1.0
        bind(
            self,
            "setToolTip",
            tr(
                "Drag to select • Ctrl + wheel to zoom • wheel to scroll • double-click to fit"
            ),
        )

    def set_audio(self, original, processed, rate):
        self.rate = rate
        self.duration = len(original) / rate if original is not None else 0.0
        for i, data in enumerate([original, processed]):
            if data is not self.data[i]:
                self.data[i] = data
                if data is None:
                    self.envelopes[i] = None
                else:
                    # Block envelope preserves transients of every channel, not a decimated line.
                    low, high = data.min(axis=1), data.max(axis=1)
                    block = 256
                    count = (len(data) + block - 1) // block
                    low = (
                        np.pad(low, (0, count * block - len(low)), mode="edge")
                        .reshape(count, block)
                        .min(axis=1)
                    )
                    high = (
                        np.pad(high, (0, count * block - len(high)), mode="edge")
                        .reshape(count, block)
                        .max(axis=1)
                    )
                    self.envelopes[i] = (low, high)
        self.update()

    def fit(self):
        self.left, self.span = 0.0, max(0.02, self.duration)
        self.update()

    def zoom(self, factor, center=None):
        center = self.left + self.span / 2 if center is None else center
        ratio = (center - self.left) / self.span
        span = min(max(0.02, self.span * factor), max(0.02, self.duration))
        self.left = max(0.0, min(center - ratio * span, max(0.0, self.duration - span)))
        self.span = span
        self.update()

    def x_at(self, seconds):
        return 130 + (seconds - self.left) / self.span * max(1, self.width() - 144)

    def time_at(self, x):
        return float(
            np.clip(
                self.left + (x - 130) / max(1, self.width() - 144) * self.span,
                0,
                self.duration,
            )
        )

    def paintEvent(self, event):
        p = G.QPainter(self)
        p.fillRect(self.rect(), G.QColor("#10151d"))
        width, height = self.width(), self.height()
        self.event_hits = []
        if not self.duration:
            p.setPen(G.QColor("#8390a5"))
            p.setFont(G.QFont("Segoe UI", 15))
            p.drawText(
                self.rect(),
                C.Qt.AlignmentFlag.AlignCenter,
                tr(
                    "Open an audio recording\n\nWAV · FLAC · MP3 · OGG · AAC · M4A\n\nor drop a file into this window"
                ),
            )
            return
        track_height = (height - 38) / 2
        p.setFont(G.QFont("Segoe UI", 9))
        # Time grid uses a human-readable spacing at every zoom level.
        desired = self.span / max(2, (width - 144) / 100)
        power = 10 ** math.floor(math.log10(max(desired, 0.001)))
        step = next(v * power for v in [1, 2, 5, 10] if v * power >= desired)
        tick = math.ceil(self.left / step) * step
        while tick <= self.left + self.span:
            x = round(self.x_at(tick))
            p.setPen(G.QColor("#27303d"))
            p.drawLine(x, 30, x, height)
            p.setPen(G.QColor("#8d9aaf"))
            p.drawText(x + 5, 21, f"{tick:.2f}s")
            tick += step
        for i, (title, subtitle, color) in enumerate(
            [
                ("01  ORIGINAL", tr("Original recording"), "#758aa6"),
                ("02  RESTORED", tr("Result"), "#5bdac6"),
            ]
        ):
            top = 36 + i * track_height
            mid = top + track_height / 2
            p.fillRect(C.QRectF(0, top, 125, track_height - 3), G.QColor("#1a222d"))
            p.setPen(G.QColor(color))
            p.drawText(12, round(top + 25), title)
            p.setPen(G.QColor("#8d9aaf"))
            p.drawText(12, round(top + 47), subtitle)
            p.drawText(
                12,
                round(top + 66),
                f"{self.data[i].shape[1]} ch"
                if self.data[i] is not None
                else tr("Waiting for processing"),
            )
            p.setPen(G.QColor("#344050"))
            p.drawLine(130, round(mid), width - 14, round(mid))
            p.save()
            p.setClipRect(C.QRectF(130, top, width - 144, track_height - 3))
            for index, region in enumerate(self.regions):
                a, b = self.x_at(region.start), self.x_at(region.end)
                if b < 130 or a > width:
                    continue
                p.fillRect(
                    C.QRectF(a, top, max(1, b - a), track_height - 3),
                    G.QColor(54, 200, 154, 40),
                )
                caption = tr("Speech {v0:02}", v0=index + 1)
                label_left = max(a, 130) + 5
                # Short neighbouring regions must not paint over each other's labels.
                if (
                    min(b, width - 14) - label_left
                    >= p.fontMetrics().horizontalAdvance(caption) + 3
                ):
                    p.setPen(G.QColor("#5bdac6"))
                    p.drawText(round(label_left), round(top + 17), caption)
            data = self.data[i]
            if data is not None:
                path = G.QPainterPath()
                n = len(data)
                for px in range(130, max(131, width - 14)):
                    a = max(0, min(n - 1, int(self.time_at(px) * self.rate)))
                    b = max(a + 1, min(n, int(self.time_at(px + 1) * self.rate)))
                    if b - a > 512:
                        lo, hi = self.envelopes[i]
                        start, end = a // 256, max(a // 256 + 1, (b + 255) // 256)
                        minimum, maximum = lo[start:end].min(), hi[start:end].max()
                    else:
                        minimum, maximum = data[a:b].min(), data[a:b].max()
                    scale = track_height * 0.39 * self.amplitude
                    path.moveTo(px, mid - float(minimum) * scale)
                    path.lineTo(px, mid - float(maximum) * scale)
                p.setPen(G.QPen(G.QColor(color), 1))
                p.drawPath(path)
            # Separate lanes for event categories; analysis is tied to its A/B source.
            event_labels = list(dict.fromkeys(e["label"] for e in self.events))
            for index, item in enumerate(self.events):
                if item["track"] != ("original" if i == 0 else "result"):
                    continue
                a, b = self.x_at(item["start"]), self.x_at(item["end"])
                if b < 130 or a > width - 14:
                    continue
                lane = event_labels.index(item["label"])
                y = top + track_height - 18 * (lane + 1) - 4
                rect = C.QRectF(
                    max(130, a), y, max(1, min(width - 14, b) - max(130, a)), 16
                )
                color = G.QColor(item["color"])
                color.setAlpha(155)
                p.fillRect(rect, color)
                p.setPen(G.QColor("#10151d"))
                caption = f"{item['label']} · {item['channel']}"
                if rect.width() > p.fontMetrics().horizontalAdvance(caption) + 6:
                    p.drawText(round(rect.left() + 3), round(y + 12), caption)
                self.event_hits.append((rect, index))
            if self.selection:
                a, b = map(self.x_at, self.selection)
                p.fillRect(
                    C.QRectF(a, top, b - a, track_height - 3),
                    G.QColor(244, 193, 99, 42),
                )
                p.setPen(G.QPen(G.QColor("#f4c163"), 1))
                p.drawRect(C.QRectF(a, top, b - a, track_height - 3))
            p.restore()
        if self.left <= self.cursor <= self.left + self.span:
            x = round(self.x_at(self.cursor))
            p.setPen(G.QPen(G.QColor("#f4c163"), 2))
            p.drawLine(x, 30, x, height)

    def mousePressEvent(self, event):
        if not self.duration or event.position().x() < 130:
            return
        t = self.time_at(event.position().x())
        if event.button() == C.Qt.MouseButton.MiddleButton:
            self.pan_anchor = (event.position().x(), self.left)
        elif event.button() == C.Qt.MouseButton.LeftButton:
            self.anchor = t
            self.selection = None
            self.cursor = t
            self.seekRequested.emit(t)
        self.update()

    def mouseMoveEvent(self, event):
        if self.pan_anchor:
            x, left = self.pan_anchor
            self.left = float(
                np.clip(
                    left
                    - (event.position().x() - x)
                    * self.span
                    / max(1, self.width() - 144),
                    0,
                    max(0, self.duration - self.span),
                )
            )
        elif self.anchor is not None:
            t = self.time_at(event.position().x())
            self.selection = tuple(sorted([self.anchor, t]))
        self.update()

    def mouseReleaseEvent(self, event):
        self.pan_anchor = None
        if self.anchor is None:
            return
        t = self.time_at(event.position().x())
        if abs(t - self.anchor) < self.span * 3 / max(1, self.width() - 144):
            self.selection = None
            for rect, index in reversed(self.event_hits):
                if rect.contains(event.position()):
                    self.eventClicked.emit(index)
                    self.anchor = None
                    self.update()
                    return
            for i, region in enumerate(self.regions):
                if region.start <= t <= region.end:
                    self.regionClicked.emit(i)
                    break
            else:
                self.selectionChanged.emit(0, 0)
        else:
            self.selection = tuple(sorted([self.anchor, t]))
            self.selectionChanged.emit(*self.selection)
        self.anchor = None
        self.update()

    def mouseDoubleClickEvent(self, event):
        self.anchor = None
        self.fit()

    def wheelEvent(self, event):
        amount = event.angleDelta().y() / 120
        if event.modifiers() & C.Qt.KeyboardModifier.ControlModifier:
            self.zoom(0.8**amount, self.time_at(event.position().x()))
        elif event.modifiers() & C.Qt.KeyboardModifier.ShiftModifier:
            self.amplitude = float(np.clip(self.amplitude * 1.2**amount, 0.25, 16))
            self.update()
        else:
            self.left = float(
                np.clip(
                    self.left - amount * self.span * 0.1,
                    0,
                    max(0, self.duration - self.span),
                )
            )
            self.update()
        event.accept()

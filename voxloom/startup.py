"""Lightweight branding before the audio/scientific modules are imported."""

import math
import os
import sys
from pathlib import Path

from PyQt6 import QtCore as C
from PyQt6 import QtGui as G
from PyQt6 import QtWidgets as W

from . import __version__
from .i18n import tr


def assets_root():
    return (
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "assets"
    )


def launch_screen(app):
    return app.screenAt(G.QCursor.pos()) or app.primaryScreen()


class StartupSplash(W.QSplashScreen):
    def __init__(self, screen):
        fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
        for name in ("segoeui.ttf", "seguisb.ttf"):
            if (fonts / name).is_file():
                G.QFontDatabase.addApplicationFont(str(fonts / name))
        width = min(620, screen.availableGeometry().width() - 32)
        height = min(360, screen.availableGeometry().height() - 32)
        ratio = screen.devicePixelRatio()
        canvas = G.QPixmap(round(width * ratio), round(height * ratio))
        canvas.setDevicePixelRatio(ratio)
        canvas.fill(C.Qt.GlobalColor.transparent)
        painter = G.QPainter(canvas)
        painter.setRenderHint(G.QPainter.RenderHint.Antialiasing)
        painter.scale(width / 620, height / 360)
        area = C.QRectF(1, 1, 618, 358)
        background = G.QLinearGradient(0, 0, 620, 360)
        background.setColorAt(0, G.QColor("#243a4e"))
        background.setColorAt(0.55, G.QColor("#101b29"))
        background.setColorAt(1, G.QColor("#0c121d"))
        painter.setBrush(background)
        painter.setPen(G.QPen(G.QColor("#425b71"), 1))
        painter.drawRoundedRect(area, 18, 18)
        # Quiet waveform detail, painted at display DPI rather than a bitmap banner.
        painter.setPen(G.QPen(G.QColor(91, 218, 198, 30), 2))
        for x in range(30, 601, 7):
            amplitude = 5 + 32 * abs(math.sin(x * 0.073)) * math.exp(
                -(((x - 480) / 130) ** 2)
            )
            painter.drawLine(
                C.QPointF(x, 246 - amplitude), C.QPointF(x, 246 + amplitude)
            )
        logo = G.QPixmap(str(assets_root() / "voxloom.png"))
        painter.drawPixmap(C.QRectF(40, 52, 96, 96), logo, C.QRectF(logo.rect()))
        painter.setPen(G.QColor("#eff7ff"))
        font = G.QFont("Segoe UI")
        font.setPixelSize(49)
        font.setWeight(G.QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(C.QRectF(156, 45, 420, 72), "VoxLoom")
        font.setPixelSize(14)
        font.setWeight(G.QFont.Weight.Normal)
        font.setLetterSpacing(G.QFont.SpacingType.AbsoluteSpacing, 5)
        painter.setFont(font)
        painter.setPen(G.QColor("#75dfca"))
        painter.drawText(C.QRectF(160, 115, 400, 30), "S T U D I O")
        font.setLetterSpacing(G.QFont.SpacingType.AbsoluteSpacing, 0)
        font.setPixelSize(18)
        painter.setFont(font)
        painter.setPen(G.QColor("#bfccdf"))
        painter.drawText(
            C.QRectF(44, 177, 540, 35), tr("Clean audio. Find speech. Get text.")
        )
        painter.setPen(G.QPen(G.QColor("#2d4055"), 1))
        painter.drawLine(44, 280, 576, 280)
        painter.setPen(G.QPen(G.QColor("#75dfca"), 2))
        painter.drawLine(44, 280, 174, 280)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(G.QColor("#8b9eb7"))
        painter.drawText(
            C.QRectF(44, 325, 400, 20), f"MatSoftAI  /  {__version__}  /  OFFLINE"
        )
        painter.end()
        super().__init__(screen, canvas)
        self.setAttribute(C.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.move(screen.availableGeometry().center() - self.rect().center())
        self.set_status(tr("Preparing the studio…"))

    def set_status(self, message):
        self.showMessage(
            message,
            C.Qt.AlignmentFlag.AlignHCenter | C.Qt.AlignmentFlag.AlignBottom,
            G.QColor("#dbe5f3"),
        )

    def drawContents(self, painter):
        painter.save()
        painter.scale(self.width() / 620, self.height() / 360)
        font = G.QFont("Segoe UI")
        font.setPixelSize(13)
        painter.setFont(font)
        painter.setPen(G.QColor("#dbe5f3"))
        painter.drawText(C.QRectF(44, 293, 532, 24), self.message())
        painter.restore()


def show_workspace(window, screen):
    # Qt coordinates are logical pixels; Windows maximization handles decorations,
    # taskbars, mixed-DPI monitors and subsequent monitor/work-area changes.
    window.setScreen(screen)
    window.setGeometry(screen.availableGeometry())
    window.showMaximized()

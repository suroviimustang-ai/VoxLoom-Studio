import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

root = Path(__file__).resolve().parents[1]
app = QApplication([])
renderer = QSvgRenderer(str(root / "assets" / "voxloom.svg"))
canvas = QImage(512, 512, QImage.Format.Format_ARGB32)
canvas.fill(Qt.GlobalColor.transparent)
painter = QPainter(canvas)
renderer.render(painter)
painter.end()
canvas.save(str(root / "assets" / "voxloom.png"))
Image.open(root / "assets" / "voxloom.png").save(
    root / "assets" / "voxloom.ico",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
Image.open(root / "assets" / "voxloom.png").save(root / "assets" / "voxloom.icns")
print("Created VoxLoom icon")

"""
DevClean özel Windows 7 çok çözünürlüklü .ico üreticisi (PyQt6 tabanlı).
İsteğe bağlı olarak assets/devclean.ico dosyasını yeniden üretmek için çalıştırılabilir.
"""

from __future__ import annotations

import os
import struct
import sys

from PyQt6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)


def render_master_image(size: int = 256) -> QImage:
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.scale(size / 256.0, size / 256.0)

    # 1. Alt gölge
    shadow = QPolygonF([QPointF(16, 198), QPointF(176, 224), QPointF(242, 152), QPointF(82, 130)])
    p.setBrush(QColor(10, 22, 38, 62))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(shadow)

    # 2. Sabit disk üst kapak
    top = QPolygonF([QPointF(72, 74), QPointF(228, 92), QPointF(174, 168), QPointF(18, 146)])
    gt = QLinearGradient(30, 74, 210, 168)
    gt.setColorAt(0.0, QColor("#FAFCFF"))
    gt.setColorAt(0.45, QColor("#DCE5F0"))
    gt.setColorAt(1.0, QColor("#9EACBE"))
    p.setBrush(gt)
    p.setPen(QPen(QColor("#606E80"), 3.5))
    p.drawPolygon(top)

    # Sağ yan yüzey
    side = QPolygonF([QPointF(174, 168), QPointF(228, 92), QPointF(228, 134), QPointF(174, 212)])
    gs = QLinearGradient(174, 92, 228, 212)
    gs.setColorAt(0.0, QColor("#B8C4D4"))
    gs.setColorAt(1.0, QColor("#687586"))
    p.setBrush(gs)
    p.setPen(QPen(QColor("#4E5A6A"), 3.5))
    p.drawPolygon(side)

    # Ön panel
    front = QPolygonF([QPointF(18, 146), QPointF(174, 168), QPointF(174, 212), QPointF(18, 188)])
    gf = QLinearGradient(18, 146, 18, 212)
    gf.setColorAt(0.0, QColor("#606D7D"))
    gf.setColorAt(0.5, QColor("#303844"))
    gf.setColorAt(1.0, QColor("#1A1F27"))
    p.setBrush(gf)
    p.setPen(QPen(QColor("#222932"), 3.5))
    p.drawPolygon(front)

    # Yeşil LED
    led = QLinearGradient(140, 177, 156, 193)
    led.setColorAt(0.0, QColor("#CDFFAA"))
    led.setColorAt(1.0, QColor("#109620"))
    p.setBrush(led)
    p.setPen(QPen(QColor("#0A5812"), 2.0))
    p.drawEllipse(QRectF(140, 178, 16, 13))

    # 3. Aero mavi </> rozeti
    badge_rect = QRectF(20, 26, 96, 90)
    bg = QLinearGradient(20, 26, 20, 116)
    bg.setColorAt(0.0, QColor("#60C0FC"))
    bg.setColorAt(0.5, QColor("#2076C6"))
    bg.setColorAt(1.0, QColor("#0F488A"))
    p.setBrush(bg)
    p.setPen(QPen(QColor("#0B3569"), 3.8))
    p.drawRoundedRect(badge_rect, 20, 20)

    gloss = QLinearGradient(25, 30, 25, 68)
    gloss.setColorAt(0.0, QColor(255, 255, 255, 155))
    gloss.setColorAt(1.0, QColor(255, 255, 255, 15))
    p.setBrush(gloss)
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(25, 30, 86, 38), 15, 15)

    code_pen = QPen(QColor("#FFFFFF"), 7.5)
    code_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    code_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(code_pen)
    left_c = QPainterPath(QPointF(52, 55))
    left_c.lineTo(36, 71)
    left_c.lineTo(52, 87)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(left_c)

    right_c = QPainterPath(QPointF(84, 55))
    right_c.lineTo(100, 71)
    right_c.lineTo(84, 87)
    p.drawPath(right_c)

    slash_pen = QPen(QColor("#D2F2FF"), 6.5)
    slash_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(slash_pen)
    p.drawLine(QPointF(74, 50), QPointF(62, 92))

    # 4. Windows 7 temizleme fırçası
    bristles = QPolygonF([QPointF(122, 96), QPointF(186, 138), QPointF(154, 178), QPointF(88, 134)])
    gb = QLinearGradient(88, 96, 186, 178)
    gb.setColorAt(0.0, QColor("#FFF1A2"))
    gb.setColorAt(0.5, QColor("#F4C038"))
    gb.setColorAt(1.0, QColor("#CA8410"))
    p.setBrush(gb)
    p.setPen(QPen(QColor("#8E5608"), 3.4))
    p.drawPolygon(bristles)

    band = QPolygonF([QPointF(136, 76), QPointF(199, 117), QPointF(186, 138), QPointF(122, 96)])
    gband = QLinearGradient(122, 76, 199, 138)
    gband.setColorAt(0.0, QColor("#F5F9FD"))
    gband.setColorAt(1.0, QColor("#8E9CAE"))
    p.setBrush(gband)
    p.setPen(QPen(QColor("#566272"), 3.2))
    p.drawPolygon(band)

    handle = QPolygonF([QPointF(196, 18), QPointF(232, 42), QPointF(186, 108), QPointF(151, 86)])
    gh = QLinearGradient(151, 18, 232, 108)
    gh.setColorAt(0.0, QColor("#E07E2E"))
    gh.setColorAt(1.0, QColor("#7E340A"))
    p.setBrush(gh)
    p.setPen(QPen(QColor("#5C2406"), 3.4))
    p.drawPolygon(handle)

    p.end()
    return img


def qimage_to_png_bytes(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def build_ico(output_path: str) -> None:
    master = render_master_image(256)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames: list[bytes] = []

    for sz in sizes:
        scaled = master.scaled(
            sz,
            sz,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        frames.append(qimage_to_png_bytes(scaled))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(struct.pack("<HHH", 0, 1, len(sizes)))
        offset = 6 + 16 * len(sizes)
        for sz, payload in zip(sizes, frames):
            dim = 0 if sz >= 256 else sz
            f.write(struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(payload), offset))
            offset += len(payload)
        for payload in frames:
            f.write(payload)


if __name__ == "__main__":
    _app = QGuiApplication(sys.argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target = os.path.join(root, "assets", "devclean.ico")
    build_ico(target)
    print(f"Simge olusturuldu: {target}")

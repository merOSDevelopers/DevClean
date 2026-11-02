"""
Geleneksel Windows 7 (Aero / Denetim Masası / Gezgin) tarzı çok çözünürlüklü
skeuomorfik simge üreticisi. Windows 10/11 üzerinde dahi düz simgeler yerine
klasik Windows 7 parlak ve üç boyutlu simge görünümünü korur.
"""

from __future__ import annotations

import os
from typing import Callable

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
)

from core.utils import resource_path


_cache: dict[str, QIcon] = {}


def _build_multi_icon(key: str, draw_fn: Callable[[QPainter], None]) -> QIcon:
    """16, 24, 32 ve 48 piksel boyutlarında yüksek kaliteli QIcon oluşturur."""
    if key in _cache:
        return _cache[key]

    icon = QIcon()
    for sz in (16, 24, 32, 48):
        pix = QPixmap(sz, sz)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.scale(sz / 64.0, sz / 64.0)
        draw_fn(painter)
        painter.end()
        icon.addPixmap(pix)

    _cache[key] = icon
    return icon


def _draw_hard_drive_base(p: QPainter, y_offset: float = 0.0) -> None:
    """Geleneksel Windows 7 Bilgisayarım (imageres.dll) izometrik sabit sürücü gövdesi."""
    p.save()
    p.translate(0.0, y_offset)

    # Alt gölge
    shadow = QPainterPath()
    shadow.moveTo(6, 46)
    shadow.lineTo(44, 52)
    shadow.lineTo(60, 34)
    shadow.lineTo(22, 29)
    shadow.closeSubpath()
    p.fillPath(shadow, QColor(0, 0, 0, 45))

    # Üst metal kapak
    top = QPolygonF([QPointF(18, 16), QPointF(56, 20), QPointF(44, 39), QPointF(5, 34)])
    grad_top = QLinearGradient(12, 16, 48, 39)
    grad_top.setColorAt(0.0, QColor("#F5F8FC"))
    grad_top.setColorAt(0.45, QColor("#D5DEE8"))
    grad_top.setColorAt(1.0, QColor("#AEB9C7"))
    p.setBrush(grad_top)
    p.setPen(QPen(QColor("#6E7B8B"), 1.6))
    p.drawPolygon(top)

    # Sağ yan metal yüzey
    side = QPolygonF([QPointF(44, 39), QPointF(56, 20), QPointF(56, 30), QPointF(44, 49)])
    grad_side = QLinearGradient(44, 20, 56, 49)
    grad_side.setColorAt(0.0, QColor("#B4C0CE"))
    grad_side.setColorAt(1.0, QColor("#7B8898"))
    p.setBrush(grad_side)
    p.setPen(QPen(QColor("#5C6775"), 1.5))
    p.drawPolygon(side)

    # Ön koyu panel (Windows 7 sürücü ön yüzü)
    front = QPolygonF([QPointF(5, 34), QPointF(44, 39), QPointF(44, 49), QPointF(5, 44)])
    grad_front = QLinearGradient(5, 34, 5, 49)
    grad_front.setColorAt(0.0, QColor("#596370"))
    grad_front.setColorAt(0.5, QColor("#363E47"))
    grad_front.setColorAt(1.0, QColor("#222830"))
    p.setBrush(grad_front)
    p.setPen(QPen(QColor("#2B323B"), 1.5))
    p.drawPolygon(front)

    # Parlak yeşil durum LED'i
    led_grad = QRadialGradient(QPointF(37.5, 43.5), 4.0)
    led_grad.setColorAt(0.0, QColor("#C6FF9E"))
    led_grad.setColorAt(0.5, QColor("#3CE33C"))
    led_grad.setColorAt(1.0, QColor("#0F8A1C"))
    p.setBrush(led_grad)
    p.setPen(QPen(QColor("#0B5412"), 1.0))
    p.drawEllipse(QPointF(37.5, 43.5), 3.0, 2.3)

    p.restore()


def _draw_optical_disc(p: QPainter, cx: float, cy: float, r: float) -> None:
    """Windows 7 appwiz.cpl tarzı parlak CD/DVD optik diski."""
    disc_grad = QLinearGradient(cx - r, cy - r, cx + r, cy + r)
    disc_grad.setColorAt(0.0, QColor("#F2FAFF"))
    disc_grad.setColorAt(0.28, QColor("#9EE2FF"))
    disc_grad.setColorAt(0.5, QColor("#FFFFFF"))
    disc_grad.setColorAt(0.75, QColor("#8BC7F7"))
    disc_grad.setColorAt(1.0, QColor("#D8F0FF"))

    p.setBrush(disc_grad)
    p.setPen(QPen(QColor("#5C87AD"), 1.5))
    p.drawEllipse(QPointF(cx, cy), r, r)

    # İç halka
    p.setBrush(QColor(230, 240, 250, 190))
    p.setPen(QPen(QColor("#8AA9C4"), 1.0))
    p.drawEllipse(QPointF(cx, cy), r * 0.34, r * 0.34)

    # Merkez delik
    p.setBrush(QColor("#FFFFFF"))
    p.setPen(QPen(QColor("#6E8DA8"), 1.0))
    p.drawEllipse(QPointF(cx, cy), r * 0.14, r * 0.14)


def _draw_win7_folder_base(p: QPainter) -> None:
    """Geleneksel Windows 7 dikey altın sarısı klasör simgesi."""
    # Arka kapak
    back = QPainterPath()
    back.moveTo(10, 12)
    back.lineTo(25, 12)
    back.lineTo(29, 16)
    back.lineTo(48, 16)
    back.lineTo(48, 54)
    back.lineTo(10, 54)
    back.closeSubpath()

    grad_back = QLinearGradient(10, 12, 48, 54)
    grad_back.setColorAt(0.0, QColor("#FFE38A"))
    grad_back.setColorAt(1.0, QColor("#D4921C"))
    p.setBrush(grad_back)
    p.setPen(QPen(QColor("#9E680C"), 1.6))
    p.drawPath(back)

    # İçerideki beyaz belge sayfası (Windows 7 dikey klasör detayı)
    doc_rect = QRectF(15, 18, 29, 31)
    grad_doc = QLinearGradient(15, 18, 44, 49)
    grad_doc.setColorAt(0.0, QColor("#FFFFFF"))
    grad_doc.setColorAt(1.0, QColor("#DCE6F2"))
    p.setBrush(grad_doc)
    p.setPen(QPen(QColor("#A3B5C9"), 1.2))
    p.drawRect(doc_rect)

    # Ön parlak eğimli kapak
    front = QPolygonF([QPointF(10, 24), QPointF(53, 21), QPointF(50, 54), QPointF(10, 54)])
    grad_front = QLinearGradient(10, 21, 50, 54)
    grad_front.setColorAt(0.0, QColor("#FFF2B2"))
    grad_front.setColorAt(0.35, QColor("#FAD15A"))
    grad_front.setColorAt(1.0, QColor("#DF9B1E"))
    p.setBrush(grad_front)
    p.setPen(QPen(QColor("#A66E0E"), 1.6))
    p.drawPolygon(front)

    # Üst parlama çizgisi
    p.setPen(QPen(QColor(255, 255, 255, 170), 1.4))
    p.drawLine(QPointF(12, 25.5), QPointF(51, 22.7))


class Win7Icons:
    """DevClean genelinde kullanılan klasik Windows 7 simgeleri."""

    @staticmethod
    def app_icon() -> QIcon:
        """
        DevClean özel çok çözünürlüklü Windows 7 simgesini (assets/devclean.ico) yükler.
        PyInstaller --onedir derlemesinde ve kaynak kodda aynı simgeyi döndürür.
        """
        if "app_icon" in _cache:
            return _cache["app_icon"]

        ico_file = resource_path(os.path.join("assets", "devclean.ico"))
        if os.path.isfile(ico_file):
            loaded = QIcon(ico_file)
            if not loaded.isNull():
                _cache["app_icon"] = loaded
                return loaded

        def _draw(p: QPainter) -> None:
            _draw_hard_drive_base(p, y_offset=5.0)
            # Aero geliştirici </> rozeti
            badge_rect = QRectF(5, 6, 25, 23)
            bg = QLinearGradient(5, 6, 5, 29)
            bg.setColorAt(0.0, QColor("#60C0FC"))
            bg.setColorAt(1.0, QColor("#0F488A"))
            p.setBrush(bg)
            p.setPen(QPen(QColor("#0B3569"), 1.6))
            p.drawRoundedRect(badge_rect, 5, 5)

            code_pen = QPen(QColor("#FFFFFF"), 2.1)
            code_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(code_pen)
            p.drawLine(QPointF(13, 14), QPointF(9, 17.5))
            p.drawLine(QPointF(9, 17.5), QPointF(13, 21))
            p.drawLine(QPointF(22, 14), QPointF(26, 17.5))
            p.drawLine(QPointF(26, 17.5), QPointF(22, 21))
            p.drawLine(QPointF(19, 13), QPointF(16, 22))

            # Klasik temizleme fırçası
            bristles = QPolygonF([QPointF(30, 25), QPointF(46, 35), QPointF(39, 45), QPointF(22, 34)])
            b_grad = QLinearGradient(22, 25, 46, 45)
            b_grad.setColorAt(0.0, QColor("#FFE885"))
            b_grad.setColorAt(1.0, QColor("#D4951A"))
            p.setBrush(b_grad)
            p.setPen(QPen(QColor("#8F5E09"), 1.5))
            p.drawPolygon(bristles)

            band = QPolygonF([QPointF(34, 20), QPointF(49, 30), QPointF(46, 35), QPointF(30, 25)])
            p.setBrush(QColor("#D0D8E2"))
            p.setPen(QPen(QColor("#626D7A"), 1.3))
            p.drawPolygon(band)

            handle = QPolygonF([QPointF(45, 7), QPointF(54, 13), QPointF(45, 27), QPointF(37, 22)])
            h_grad = QLinearGradient(37, 7, 54, 27)
            h_grad.setColorAt(0.0, QColor("#D67A2E"))
            h_grad.setColorAt(1.0, QColor("#8F430E"))
            p.setBrush(h_grad)
            p.setPen(QPen(QColor("#5E2905"), 1.5))
            p.drawPolygon(handle)

        return _build_multi_icon("app_icon", _draw)

    @staticmethod
    def drive_fixed() -> QIcon:
        """Windows 7 sabit disk sürücüsü simgesi."""
        return _build_multi_icon("drive_fixed", lambda p: _draw_hard_drive_base(p, 2.0))

    @staticmethod
    def programs_features() -> QIcon:
        """Windows 7 'Programlar ve Özellikler' (appwiz.cpl) yazılım kutusu + optik disk simgesi."""
        def _draw(p: QPainter) -> None:
            # 3B Yazılım Kutusu
            # Ön kapak
            box_front = QPolygonF([QPointF(8, 13), QPointF(35, 9), QPointF(35, 51), QPointF(8, 46)])
            gf = QLinearGradient(8, 9, 35, 51)
            gf.setColorAt(0.0, QColor("#4EB2F2"))
            gf.setColorAt(0.45, QColor("#1D76BD"))
            gf.setColorAt(1.0, QColor("#104B82"))
            p.setBrush(gf)
            p.setPen(QPen(QColor("#0B3761"), 1.6))
            p.drawPolygon(box_front)

            # Yan sırt
            box_side = QPolygonF([QPointF(35, 9), QPointF(44, 13), QPointF(44, 48), QPointF(35, 51)])
            gs = QLinearGradient(35, 9, 44, 51)
            gs.setColorAt(0.0, QColor("#2B87CC"))
            gs.setColorAt(1.0, QColor("#0C3A66"))
            p.setBrush(gs)
            p.drawPolygon(box_side)

            # Kutu üzerindeki beyaz şerit detayı
            stripe = QPolygonF([QPointF(11, 20), QPointF(32, 17), QPointF(32, 23), QPointF(11, 26)])
            p.setBrush(QColor(255, 255, 255, 195))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(stripe)

            # Sağ alt ön planda parlak CD/DVD
            _draw_optical_disc(p, 43.0, 41.0, 15.5)

        return _build_multi_icon("programs_features", _draw)

    @staticmethod
    def folder_win7() -> QIcon:
        """Geleneksel Windows 7 sarı klasör simgesi."""
        return _build_multi_icon("folder_win7", _draw_win7_folder_base)

    @staticmethod
    def folder_cache() -> QIcon:
        """Geçici geliştirici dosyaları için Windows 7 klasörü + önbellek dişlisi simgesi."""
        def _draw(p: QPainter) -> None:
            _draw_win7_folder_base(p)
            # Sağ alt köşeye parlak mavi-gümüş önbellek rozeti
            cx, cy, r = 46.0, 46.0, 12.5
            g = QRadialGradient(QPointF(cx - 3, cy - 4), r * 1.3)
            g.setColorAt(0.0, QColor("#B5E6FF"))
            g.setColorAt(0.55, QColor("#298CE0"))
            g.setColorAt(1.0, QColor("#12518F"))
            p.setBrush(g)
            p.setPen(QPen(QColor("#0C3863"), 1.6))
            p.drawEllipse(QPointF(cx, cy), r, r)

            # İçeride beyaz dairesel önbellek oku
            pen = QPen(QColor("#FFFFFF"), 2.4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(cx - 6.5, cy - 6.5, 13.0, 13.0), 35 * 16, 260 * 16)

        return _build_multi_icon("folder_cache", _draw)

    @staticmethod
    def dev_tools() -> QIcon:
        """Geliştirme araçları ve SDK yönetimi simgesi (Windows 7 bileşen kutusu ve anahtar)."""
        def _draw(p: QPainter) -> None:
            # İzometrik SDK paketi
            top = QPolygonF([QPointF(30, 8), QPointF(54, 17), QPointF(30, 27), QPointF(6, 17)])
            gt = QLinearGradient(6, 8, 54, 27)
            gt.setColorAt(0.0, QColor("#F5E2B8"))
            gt.setColorAt(1.0, QColor("#D4A553"))
            p.setBrush(gt)
            p.setPen(QPen(QColor("#8C621C"), 1.5))
            p.drawPolygon(top)

            left = QPolygonF([QPointF(6, 17), QPointF(30, 27), QPointF(30, 52), QPointF(6, 41)])
            gl = QLinearGradient(6, 17, 30, 52)
            gl.setColorAt(0.0, QColor("#DDA94B"))
            gl.setColorAt(1.0, QColor("#B07A22"))
            p.setBrush(gl)
            p.drawPolygon(left)

            right = QPolygonF([QPointF(30, 27), QPointF(54, 17), QPointF(54, 41), QPointF(30, 52)])
            gr = QLinearGradient(30, 17, 54, 52)
            gr.setColorAt(0.0, QColor("#C48E33"))
            gr.setColorAt(1.0, QColor("#8F6014"))
            p.setBrush(gr)
            p.drawPolygon(right)

            # Sağ altta metalik İngiliz anahtarı / ayar rozeti
            badge = QRadialGradient(QPointF(44, 42), 16)
            badge.setColorAt(0.0, QColor("#F5F9FC"))
            badge.setColorAt(0.6, QColor("#BAC7D6"))
            badge.setColorAt(1.0, QColor("#738294"))
            p.setBrush(badge)
            p.setPen(QPen(QColor("#434F5E"), 1.6))
            p.drawEllipse(QPointF(46, 45), 13, 13)

            p.setBrush(QColor("#236BB2"))
            p.setPen(QPen(QColor("#134273"), 1.2))
            p.drawEllipse(QPointF(46, 45), 6.2, 6.2)
            p.setBrush(QColor("#F0F5FA"))
            p.drawEllipse(QPointF(46, 45), 2.8, 2.8)

        return _build_multi_icon("dev_tools", _draw)

    @staticmethod
    def recycle_bin() -> QIcon:
        """Geleneksel Windows 7 yarı saydam Aero Geri Dönüşüm Kutusu simgesi."""
        def _draw(p: QPainter) -> None:
            # Arka ağız elipsi
            p.setBrush(QColor("#B9D5EC"))
            p.setPen(QPen(QColor("#5C82A3"), 1.5))
            p.drawEllipse(QRectF(14, 9, 36, 10))

            # Cam gövde (yamuk)
            body = QPolygonF([QPointF(14, 14), QPointF(50, 14), QPointF(45, 55), QPointF(19, 55)])
            gb = QLinearGradient(14, 14, 50, 55)
            gb.setColorAt(0.0, QColor(225, 243, 255, 235))
            gb.setColorAt(0.45, QColor(175, 212, 240, 235))
            gb.setColorAt(1.0, QColor(126, 169, 204, 240))
            p.setBrush(gb)
            p.setPen(QPen(QColor("#567A99"), 1.6))
            p.drawPolygon(body)

            # Ön üst çember
            p.setBrush(QColor(235, 247, 255, 210))
            p.setPen(QPen(QColor("#567A99"), 1.5))
            p.drawEllipse(QRectF(14, 9, 36, 9))

            # Yeşil geri dönüşüm amblemi
            pen = QPen(QColor("#239C38"), 2.6)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(24, 28, 16, 16), 20 * 16, 285 * 16)

        return _build_multi_icon("recycle_bin", _draw)

    @staticmethod
    def delete_permanent() -> QIcon:
        """Windows 7 imageres.dll parlak kırmızı Sil (X) simgesi."""
        def _draw(p: QPainter) -> None:
            g = QRadialGradient(QPointF(26, 22), 26)
            g.setColorAt(0.0, QColor("#FF8A80"))
            g.setColorAt(0.45, QColor("#E02F24"))
            g.setColorAt(1.0, QColor("#96130B"))
            p.setBrush(g)
            p.setPen(QPen(QColor("#6E0B05"), 1.8))
            p.drawEllipse(QPointF(32, 32), 24, 24)

            # Üst cam yansıması
            gloss = QLinearGradient(16, 10, 16, 30)
            gloss.setColorAt(0.0, QColor(255, 255, 255, 165))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 10))
            p.setBrush(gloss)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(16, 10, 32, 18))

            # Beyaz X
            pen = QPen(QColor("#FFFFFF"), 5.5)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(22, 22), QPointF(42, 42))
            p.drawLine(QPointF(42, 22), QPointF(22, 42))

        return _build_multi_icon("delete_permanent", _draw)

    @staticmethod
    def refresh() -> QIcon:
        """Windows 7 Gezgin parlak yeşil Yenile küresi simgesi."""
        def _draw(p: QPainter) -> None:
            g = QRadialGradient(QPointF(25, 20), 28)
            g.setColorAt(0.0, QColor("#B9F7A6"))
            g.setColorAt(0.5, QColor("#36B839"))
            g.setColorAt(1.0, QColor("#18781C"))
            p.setBrush(g)
            p.setPen(QPen(QColor("#115915"), 1.8))
            p.drawEllipse(QPointF(32, 32), 24, 24)

            # Cam yansıması
            gloss = QLinearGradient(16, 10, 16, 30)
            gloss.setColorAt(0.0, QColor(255, 255, 255, 155))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
            p.setBrush(gloss)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(16, 10, 32, 17))

            # İki kavisli yenileme oku
            pen = QPen(QColor("#FFFFFF"), 4.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawArc(QRectF(19, 19, 26, 26), 30 * 16, 130 * 16)
            p.drawArc(QRectF(19, 19, 26, 26), 210 * 16, 130 * 16)

            p.setBrush(QColor("#FFFFFF"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(QPolygonF([QPointF(44, 18), QPointF(49, 27), QPointF(39, 26)]))
            p.drawPolygon(QPolygonF([QPointF(20, 46), QPointF(15, 37), QPointF(25, 38)]))

        return _build_multi_icon("refresh", _draw)

    @staticmethod
    def search_scan() -> QIcon:
        """Windows 7 Aero büyüteç (Tara / Ara) simgesi."""
        def _draw(p: QPainter) -> None:
            # Sap
            pen_h = QPen(QColor("#3E4B59"), 7.0)
            pen_h.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen_h)
            p.drawLine(QPointF(39, 39), QPointF(55, 55))

            pen_hi = QPen(QColor("#7B8FA3"), 2.5)
            pen_hi.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen_hi)
            p.drawLine(QPointF(39, 38), QPointF(54, 53))

            # Mercek çerçevesi ve camı
            lens = QRadialGradient(QPointF(22, 20), 20)
            lens.setColorAt(0.0, QColor("#EBF8FF"))
            lens.setColorAt(0.6, QColor("#99D9FF"))
            lens.setColorAt(1.0, QColor("#4BA3E3"))
            p.setBrush(lens)
            p.setPen(QPen(QColor("#3A6891"), 3.2))
            p.drawEllipse(QPointF(26, 26), 17, 17)

            # Parlama
            p.setBrush(QColor(255, 255, 255, 165))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QRectF(16, 13, 14, 8))

        return _build_multi_icon("search_scan", _draw)

    @staticmethod
    def uninstall() -> QIcon:
        """Windows 7 Kaldır simgesi (yazılım paketi + kırmızı eksi rozeti)."""
        def _draw(p: QPainter) -> None:
            # Kutu
            rect = QRectF(8, 10, 36, 42)
            g = QLinearGradient(8, 10, 44, 52)
            g.setColorAt(0.0, QColor("#67BDF7"))
            g.setColorAt(1.0, QColor("#185C9E"))
            p.setBrush(g)
            p.setPen(QPen(QColor("#0D3B69"), 1.8))
            p.drawRoundedRect(rect, 4, 4)

            p.setBrush(QColor(255, 255, 255, 190))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRect(QRectF(12, 18, 28, 6))

            # Sağ altta parlak kırmızı eksi rozeti
            rg = QRadialGradient(QPointF(42, 40), 16)
            rg.setColorAt(0.0, QColor("#FF887D"))
            rg.setColorAt(0.55, QColor("#DC2A1F"))
            rg.setColorAt(1.0, QColor("#8F1008"))
            p.setBrush(rg)
            p.setPen(QPen(QColor("#610702"), 1.6))
            p.drawEllipse(QPointF(45, 45), 13.5, 13.5)

            pen = QPen(QColor("#FFFFFF"), 4.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(39, 45), QPointF(51, 45))

        return _build_multi_icon("uninstall", _draw)

    @staticmethod
    def uac_shield() -> QIcon:
        """Geleneksel 4 bölmeli Windows 7 UAC (Kullanıcı Hesabı Denetimi) kalkanı simgesi."""
        def _draw(p: QPainter) -> None:
            shield = QPainterPath()
            shield.moveTo(32, 6)
            shield.cubicTo(42, 10, 52, 11, 54, 12)
            shield.cubicTo(54, 34, 46, 48, 32, 58)
            shield.cubicTo(18, 48, 10, 34, 10, 12)
            shield.cubicTo(12, 11, 22, 10, 32, 6)
            shield.closeSubpath()

            p.save()
            p.setClipPath(shield)
            # Sol üst mavi, sağ üst sarı, sol alt sarı, sağ alt mavi (Windows 7 UAC kalkanı)
            p.fillRect(QRectF(8, 4, 24, 27), QColor("#2582D4"))
            p.fillRect(QRectF(32, 4, 24, 27), QColor("#F5B922"))
            p.fillRect(QRectF(8, 31, 24, 29), QColor("#EAA315"))
            p.fillRect(QRectF(32, 31, 24, 29), QColor("#1864B0"))

            # Cam parlaklık katmanı
            gloss = QLinearGradient(10, 6, 48, 45)
            gloss.setColorAt(0.0, QColor(255, 255, 255, 120))
            gloss.setColorAt(0.5, QColor(255, 255, 255, 20))
            gloss.setColorAt(1.0, QColor(0, 0, 0, 25))
            p.fillRect(QRectF(8, 4, 48, 56), gloss)
            p.restore()

            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor("#465466"), 2.4))
            p.drawPath(shield)

        return _build_multi_icon("uac_shield", _draw)

    @staticmethod
    def info_orb() -> QIcon:
        """Windows 7 parlak mavi Bilgi (i) simgesi."""
        def _draw(p: QPainter) -> None:
            g = QRadialGradient(QPointF(25, 20), 28)
            g.setColorAt(0.0, QColor("#9EE0FF"))
            g.setColorAt(0.5, QColor("#2181D4"))
            g.setColorAt(1.0, QColor("#0E4782"))
            p.setBrush(g)
            p.setPen(QPen(QColor("#09325E"), 1.8))
            p.drawEllipse(QPointF(32, 32), 24, 24)

            p.setBrush(QColor("#FFFFFF"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(32, 19), 3.4, 3.4)
            p.drawRoundedRect(QRectF(28.8, 26, 6.4, 21), 2.5, 2.5)

        return _build_multi_icon("info_orb", _draw)

    @staticmethod
    def badge_icon(bg_top: str, bg_bottom: str, border: str, text: str) -> QIcon:
        """Dil ve IDE kategorileri için geleneksel parlak Windows 7 rozet simgesi."""
        key = f"badge_{text}_{bg_top}"

        def _draw(p: QPainter) -> None:
            rect = QRectF(7, 7, 50, 50)
            g = QLinearGradient(7, 7, 7, 57)
            g.setColorAt(0.0, QColor(bg_top))
            g.setColorAt(1.0, QColor(bg_bottom))
            p.setBrush(g)
            p.setPen(QPen(QColor(border), 2.0))
            p.drawRoundedRect(rect, 9, 9)

            # Üst Aero parlama
            gloss = QLinearGradient(9, 9, 9, 31)
            gloss.setColorAt(0.0, QColor(255, 255, 255, 130))
            gloss.setColorAt(1.0, QColor(255, 255, 255, 10))
            p.setBrush(gloss)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(9, 9, 46, 21), 7, 7)

            font = QFont("Segoe UI", 16 if len(text) <= 2 else 13, QFont.Weight.Bold)
            p.setFont(font)
            p.setPen(QColor("#FFFFFF"))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

        return _build_multi_icon(key, _draw)

    @staticmethod
    def category_vs() -> QIcon:
        return Win7Icons.badge_icon("#8E5CE6", "#53259E", "#37156E", "VS")

    @staticmethod
    def category_sdk() -> QIcon:
        return Win7Icons.badge_icon("#3C99DC", "#195B96", "#0E3B66", "SDK")

    @staticmethod
    def category_python() -> QIcon:
        return Win7Icons.badge_icon("#3B82C4", "#1F5487", "#13385C", "Py")

    @staticmethod
    def category_pycharm() -> QIcon:
        return Win7Icons.badge_icon("#33B864", "#187D3E", "#0E5227", "PC")

    @staticmethod
    def category_android() -> QIcon:
        return Win7Icons.badge_icon("#52C45A", "#278730", "#17591D", "AS")

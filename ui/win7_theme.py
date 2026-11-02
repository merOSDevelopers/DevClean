"""
Geleneksel Windows 7 Denetim Masası (Programlar ve Özellikler / Disk Temizleme)
görsel teması ve ortak arayüz bileşenleri.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.i18n import tr
from core.utils import format_bytes
from ui.win7_icons import Win7Icons


SORT_ROLE = Qt.ItemDataRole.UserRole + 10


def ask_yes_no(parent: Optional[QWidget], title: str, text: str) -> bool:
    """Etkin arayüz dilinde (Evet/Hayır veya Yes/No) onay iletişim kutusu gösterir."""
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setIcon(QMessageBox.Icon.Question)
    box.setText(text)
    btn_yes = box.addButton(tr("yes"), QMessageBox.ButtonRole.YesRole)
    btn_no = box.addButton(tr("no"), QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(btn_no)
    box.exec()
    return box.clickedButton() == btn_yes


class SortableTreeItem(QTreeWidgetItem):
    """Sayısal boyut ve tarih sütunlarının doğru sıralanmasını sağlayan ağaç öğesi."""

    def __lt__(self, other: QTreeWidgetItem) -> bool:
        tree = self.treeWidget()
        col = tree.sortColumn() if tree is not None else 0
        v1 = self.data(col, SORT_ROLE)
        v2 = other.data(col, SORT_ROLE)
        if v1 is not None and v2 is not None:
            try:
                return v1 < v2
            except TypeError:
                pass
        return self.text(col).lower() < other.text(col).lower()


class Win7HeaderBanner(QFrame):
    """Windows 7 Denetim Masası üst başlık şeridi (#003399 ana yönerge rengi ile)."""

    def __init__(self, icon: QIcon, title: str, subtitle: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Win7HeaderBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(34, 34)
        self.icon_label.setPixmap(icon.pixmap(QSize(32, 32)))
        layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("Win7MainInstruction")
        text_box.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("Win7SubInstruction")
        self.subtitle_label.setWordWrap(True)
        text_box.addWidget(self.subtitle_label)

        layout.addLayout(text_box, 1)

    def set_texts(self, title: str, subtitle: str) -> None:
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)


class Win7DriveWidget(QFrame):
    """Windows 7 Bilgisayarım tarzı sürücü doluluk göstergesi."""

    def __init__(
        self,
        drive_letter: str,
        total_bytes: int,
        used_bytes: int,
        free_bytes: int,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("Win7DriveCard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        ico_lbl = QLabel()
        ico_lbl.setFixedSize(26, 26)
        ico_lbl.setPixmap(Win7Icons.drive_fixed().pixmap(QSize(24, 24)))
        layout.addWidget(ico_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(3)

        clean_drive = drive_letter.rstrip("\\/")
        title_lbl = QLabel(tr("drive_title", drive=clean_drive))
        title_lbl.setObjectName("Win7DriveTitle")
        info_layout.addWidget(title_lbl)

        bar = QProgressBar()
        bar.setRange(0, 100)
        pct = int(round((used_bytes / total_bytes) * 100)) if total_bytes > 0 else 0
        pct = max(0, min(100, pct))
        bar.setValue(pct)
        bar.setTextVisible(False)
        bar.setFixedHeight(13)
        bar.setObjectName("Win7DriveBarCritical" if pct >= 90 else "Win7DriveBarNormal")
        info_layout.addWidget(bar)

        cap_lbl = QLabel(
            tr("drive_sub", free=format_bytes(free_bytes), total=format_bytes(total_bytes))
        )
        cap_lbl.setObjectName("Win7DriveSub")
        info_layout.addWidget(cap_lbl)

        layout.addLayout(info_layout, 1)


class Win7DetailsPane(QFrame):
    """Windows 7 Gezgin / Programlar ve Özellikler alt ayrıntı paneli."""

    def __init__(self, default_icon: QIcon, default_title: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Win7DetailsPane")
        self._default_icon = default_icon
        self._default_title = default_title

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(14)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(36, 36)
        layout.addWidget(self.icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(3)

        self.title_lbl = QLabel()
        self.title_lbl.setObjectName("Win7DetailsTitle")
        right.addWidget(self.title_lbl)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(22)
        self.grid.setVerticalSpacing(2)

        self._field_labels: list[QLabel] = []
        for idx in range(4):
            lbl = QLabel("")
            lbl.setObjectName("Win7DetailsField")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            self._field_labels.append(lbl)
            self.grid.addWidget(lbl, idx // 2, idx % 2)

        right.addLayout(self.grid)
        layout.addLayout(right, 1)

        self.reset()

    def set_default_title(self, title: str) -> None:
        self._default_title = title

    def reset(self, summary_fields: Optional[list[str]] = None) -> None:
        self.icon_lbl.setPixmap(self._default_icon.pixmap(QSize(32, 32)))
        self.title_lbl.setText(self._default_title)
        fields = summary_fields or []
        for idx, lbl in enumerate(self._field_labels):
            lbl.setText(fields[idx] if idx < len(fields) else "")

    def set_details(self, icon: QIcon, title: str, fields: list[str]) -> None:
        pix: QPixmap = icon.pixmap(QSize(32, 32))
        if pix.isNull():
            pix = self._default_icon.pixmap(QSize(32, 32))
        self.icon_lbl.setPixmap(pix)
        self.title_lbl.setText(title)
        for idx, lbl in enumerate(self._field_labels):
            lbl.setText(fields[idx] if idx < len(fields) else "")


WIN7_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #FFFFFF;
    color: #1B2028;
    font-family: "Segoe UI", Tahoma, sans-serif;
    font-size: 9pt;
}

QWidget {
    font-family: "Segoe UI", Tahoma, sans-serif;
    font-size: 9pt;
    color: #1B2028;
}

/* Sol Denetim Masası Gezinti Bölmesi */
QFrame#Win7Sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F3F7FC, stop:0.6 #EBF2FA, stop:1 #E3ECF7);
    border-right: 1px solid #C9D6E6;
}

QLabel#SidebarSectionTitle {
    color: #1E395B;
    font-weight: 600;
    font-size: 9pt;
    padding: 4px 6px 2px 6px;
}

QPushButton[navButton="true"] {
    text-align: left;
    padding: 7px 10px;
    border: 1px solid transparent;
    border-radius: 3px;
    background: transparent;
    color: #153359;
    font-size: 9pt;
}

QPushButton[navButton="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F5FAFF, stop:1 #E1EEFC);
    border: 1px solid #B8D6F5;
}

QPushButton[navButton="true"]:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #EBF4FE, stop:1 #CFE4FC);
    border: 1px solid #84ACDD;
    color: #002B66;
    font-weight: 600;
}

/* Windows 7 Üst Başlık Şeridi */
QFrame#Win7HeaderBanner {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E9F2;
}

QLabel#Win7MainInstruction {
    color: #003399;
    font-size: 12pt;
    font-weight: normal;
}

QLabel#Win7SubInstruction {
    color: #3E4A59;
    font-size: 9pt;
}

/* Windows 7 Gezgin Komut Çubuğu (Command Bar) */
QFrame#Win7CommandBar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FDFEFF, stop:0.48 #ECF3FB, stop:0.52 #E2EDF9, stop:1 #D8E6F5);
    border-bottom: 1px solid #B6CAE2;
}

QFrame#Win7CommandBar QPushButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 4px 10px;
    color: #1E395B;
    min-height: 22px;
}

QFrame#Win7CommandBar QPushButton:hover:!disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F6FBFF, stop:0.5 #E5F2FE, stop:1 #CFE6FC);
    border: 1px solid #86B2E0;
}

QFrame#Win7CommandBar QPushButton:pressed:!disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #C7E1FB, stop:1 #DCECFB);
    border: 1px solid #6396CC;
}

QFrame#Win7CommandBar QPushButton:disabled {
    color: #8D99A8;
}

/* Standart Windows 7 Düğmeleri */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F4F5F7, stop:0.48 #EAECEF, stop:0.52 #DCDFE4, stop:1 #D2D6DC);
    border: 1px solid #8E97A4;
    border-radius: 3px;
    padding: 4px 12px;
    color: #1A1F26;
    min-height: 21px;
}

QPushButton:hover:!disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #EAF6FD, stop:0.48 #D9F0FC, stop:0.52 #BEE6FD, stop:1 #A7D9F5);
    border: 1px solid #3C7FB1;
}

QPushButton:pressed:!disabled {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #C4E5F6, stop:1 #98D1EF);
    border: 1px solid #2C628B;
}

QPushButton:disabled {
    background: #EFEFEF;
    border: 1px solid #C6CBD1;
    color: #939AA3;
}

/* Arama ve Metin Kutuları */
QLineEdit, QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #ABADB3;
    border-top-color: #8E949E;
    border-radius: 2px;
    padding: 3px 6px;
    min-height: 20px;
    selection-background-color: #3399FF;
    selection-color: #FFFFFF;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3D7BAD;
}

/* Windows 7 Gezgin Ağaç ve Liste Görünümü */
QTreeWidget {
    background-color: #FFFFFF;
    alternate-background-color: #FAFBFD;
    border: none;
    outline: 0;
}

QTreeWidget::item {
    padding: 4px 4px;
    border: 1px solid transparent;
    color: #1B2028;
}

QTreeWidget::item:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F6FAFF, stop:1 #E8F3FE);
    border: 1px solid #C2DDF8;
    border-radius: 2px;
}

QTreeWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #EBF4FE, stop:1 #CEE5FC);
    border: 1px solid #7DA2CE;
    border-radius: 2px;
    color: #0D1826;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FFFFFF, stop:0.6 #F4F6F9, stop:1 #E9EDF2);
    color: #384659;
    border: none;
    border-right: 1px solid #D5DCE6;
    border-bottom: 1px solid #C8D1DE;
    padding: 4px 8px;
    font-weight: normal;
}

QHeaderView::section:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F3F9FF, stop:1 #DCECFD);
    color: #13396B;
}

/* Windows 7 Alt Ayrıntılar Paneli */
QFrame#Win7DetailsPane {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #F2F7FD, stop:1 #E0EBF7);
    border-top: 1px solid #C3D3E6;
}

QLabel#Win7DetailsTitle {
    color: #0E2A4D;
    font-size: 10pt;
    font-weight: 600;
}

QLabel#Win7DetailsField {
    color: #3A495C;
    font-size: 8.5pt;
}

/* Sürücü Doluluk Kartı */
QFrame#Win7DriveCard {
    background-color: rgba(255, 255, 255, 165);
    border: 1px solid #CBD8E8;
    border-radius: 3px;
}

QLabel#Win7DriveTitle {
    color: #162F4F;
    font-weight: 600;
    font-size: 8.5pt;
}

QLabel#Win7DriveSub {
    color: #4A5A6E;
    font-size: 8pt;
}

QProgressBar#Win7DriveBarNormal {
    background-color: #E6E8EB;
    border: 1px solid #B2BBC4;
    border-radius: 2px;
}

QProgressBar#Win7DriveBarNormal::chunk {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #79E2FF, stop:0.45 #2CB5E8, stop:0.55 #1B9AD1, stop:1 #24AEE3);
}

QProgressBar#Win7DriveBarCritical {
    background-color: #E6E8EB;
    border: 1px solid #B2BBC4;
    border-radius: 2px;
}

QProgressBar#Win7DriveBarCritical::chunk {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #FF8F85, stop:0.5 #DF2E21, stop:1 #B51B10);
}

/* Windows 7 Yeşil İlerleme Çubuğu */
QProgressBar#Win7GreenProgress {
    background-color: #E6E6E6;
    border: 1px solid #ACACAC;
    border-radius: 2px;
    text-align: center;
    height: 15px;
}

QProgressBar#Win7GreenProgress::chunk {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #ADF2AF, stop:0.48 #42C847, stop:0.52 #22AD28, stop:1 #36C23B);
}

/* Durum Çubuğu */
QStatusBar {
    background: #F1F4F8;
    border-top: 1px solid #CFD8E3;
    color: #324052;
    font-size: 8.5pt;
}
"""

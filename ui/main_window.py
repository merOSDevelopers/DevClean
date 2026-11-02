"""DevClean ana uygulama penceresi (Windows 7 Denetim Masası düzeni, Türkçe ve İngilizce dil destekli)."""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.i18n import i18n, tr
from core.utils import get_fixed_drives
from ui.apps_tab import InstalledAppsTab
from ui.caches_tab import DeveloperCachesTab
from ui.devtools_tab import DevToolsManagerTab
from ui.win7_icons import Win7Icons
from ui.win7_theme import WIN7_STYLESHEET, Win7DriveWidget


class DevCleanMainWindow(QMainWindow):
    """DevClean ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DevClean")
        self.setWindowIcon(Win7Icons.app_icon())
        self.resize(1160, 720)
        self.setMinimumSize(940, 580)
        self.setStyleSheet(WIN7_STYLESHEET)

        self._scanned_tabs: set[int] = set()
        self._build_menu_bar()
        self._build_central_ui()
        self._build_status_bar()

        self.retranslate_ui()
        i18n.language_changed.connect(self._on_language_changed)

        QTimer.singleShot(120, lambda: self._switch_page(0))

    def _build_menu_bar(self) -> None:
        menubar: QMenuBar = self.menuBar()

        self.file_menu = menubar.addMenu("")
        self.act_refresh_view = QAction(Win7Icons.refresh(), "", self)
        self.act_refresh_view.setShortcut("F5")
        self.act_refresh_view.triggered.connect(self._refresh_current_tab)
        self.file_menu.addAction(self.act_refresh_view)

        self.file_menu.addSeparator()
        self.act_exit = QAction("", self)
        self.act_exit.setShortcut("Alt+F4")
        self.act_exit.triggered.connect(self.close)
        self.file_menu.addAction(self.act_exit)

        self.view_menu = menubar.addMenu("")
        self.act_v0 = QAction(Win7Icons.programs_features(), "", self)
        self.act_v0.triggered.connect(lambda: self._switch_page(0))
        self.view_menu.addAction(self.act_v0)

        self.act_v1 = QAction(Win7Icons.folder_cache(), "", self)
        self.act_v1.triggered.connect(lambda: self._switch_page(1))
        self.view_menu.addAction(self.act_v1)

        self.act_v2 = QAction(Win7Icons.dev_tools(), "", self)
        self.act_v2.triggered.connect(lambda: self._switch_page(2))
        self.view_menu.addAction(self.act_v2)

        self.view_menu.addSeparator()
        self.act_drives = QAction(Win7Icons.drive_fixed(), "", self)
        self.act_drives.triggered.connect(self.refresh_drives)
        self.view_menu.addAction(self.act_drives)

        # Dil / Language Menüsü
        self.lang_menu = menubar.addMenu("")
        self.lang_action_group = QActionGroup(self)
        self.lang_action_group.setExclusive(True)

        self.act_lang_tr = QAction("Türkçe", self)
        self.act_lang_tr.setCheckable(True)
        self.act_lang_tr.triggered.connect(lambda: i18n.set_language("tr"))
        self.lang_action_group.addAction(self.act_lang_tr)
        self.lang_menu.addAction(self.act_lang_tr)

        self.act_lang_en = QAction("English", self)
        self.act_lang_en.setCheckable(True)
        self.act_lang_en.triggered.connect(lambda: i18n.set_language("en"))
        self.lang_action_group.addAction(self.act_lang_en)
        self.lang_menu.addAction(self.act_lang_en)

        self.help_menu = menubar.addMenu("")
        self.act_about = QAction(Win7Icons.info_orb(), "", self)
        self.act_about.triggered.connect(self._show_about_dialog)
        self.help_menu.addAction(self.act_about)

    def _build_central_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Win7Sidebar")
        sidebar.setFixedWidth(250)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(10, 12, 10, 12)
        sb_layout.setSpacing(6)

        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(4, 0, 4, 8)
        brand_row.setSpacing(10)

        app_ico_lbl = QLabel()
        app_ico_lbl.setFixedSize(36, 36)
        app_ico_lbl.setPixmap(Win7Icons.app_icon().pixmap(QSize(32, 32)))
        brand_row.addWidget(app_ico_lbl)

        brand_text = QVBoxLayout()
        brand_text.setContentsMargins(0, 0, 0, 0)
        brand_text.setSpacing(1)
        lbl_name = QLabel("DevClean")
        lbl_name.setStyleSheet("color: #003399; font-size: 12pt; font-weight: 600;")
        brand_text.addWidget(lbl_name)
        self.lbl_app_sub = QLabel()
        self.lbl_app_sub.setStyleSheet("color: #4A5B70; font-size: 8pt;")
        self.lbl_app_sub.setWordWrap(True)
        brand_text.addWidget(self.lbl_app_sub)
        brand_row.addLayout(brand_text, 1)
        sb_layout.addLayout(brand_row)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet("color: #CFDCEB;")
        sb_layout.addWidget(sep1)

        self.lbl_nav_section = QLabel()
        self.lbl_nav_section.setObjectName("SidebarSectionTitle")
        sb_layout.addWidget(self.lbl_nav_section)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        self._nav_specs = [
            (0, Win7Icons.programs_features(), "nav_apps"),
            (1, Win7Icons.folder_cache(), "nav_caches"),
            (2, Win7Icons.dev_tools(), "nav_devtools"),
        ]
        self._nav_buttons: list[QPushButton] = []

        for idx, icon, _key in self._nav_specs:
            btn = QPushButton()
            btn.setProperty("navButton", True)
            btn.setCheckable(True)
            btn.setIcon(icon)
            btn.setIconSize(QSize(22, 22))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked, page_idx=idx: self._switch_page(page_idx))
            self._nav_group.addButton(btn, idx)
            self._nav_buttons.append(btn)
            sb_layout.addWidget(btn)

        sb_layout.addStretch(1)

        # Sol Yan Panel Dil Seçici
        sep_lang = QFrame()
        sep_lang.setFrameShape(QFrame.Shape.HLine)
        sep_lang.setStyleSheet("color: #CFDCEB;")
        sb_layout.addWidget(sep_lang)

        self.lbl_lang_section = QLabel()
        self.lbl_lang_section.setObjectName("SidebarSectionTitle")
        sb_layout.addWidget(self.lbl_lang_section)

        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem("Türkçe", "tr")
        self.cmb_lang.addItem("English", "en")
        self.cmb_lang.currentIndexChanged.connect(self._on_lang_combo_changed)
        sb_layout.addWidget(self.cmb_lang)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color: #CFDCEB;")
        sb_layout.addWidget(sep2)

        self.lbl_drives_section = QLabel()
        self.lbl_drives_section.setObjectName("SidebarSectionTitle")
        sb_layout.addWidget(self.lbl_drives_section)

        self._drives_container = QVBoxLayout()
        self._drives_container.setContentsMargins(0, 0, 0, 0)
        self._drives_container.setSpacing(6)
        sb_layout.addLayout(self._drives_container)

        main_layout.addWidget(sidebar)

        self.stack = QStackedWidget()

        self.tab_apps = InstalledAppsTab(self)
        self.tab_apps.status_message.connect(self._set_status)
        self.tab_apps.disk_refresh_requested.connect(self.refresh_drives)
        self.stack.addWidget(self.tab_apps)

        self.tab_caches = DeveloperCachesTab(self)
        self.tab_caches.status_message.connect(self._set_status)
        self.tab_caches.disk_refresh_requested.connect(self.refresh_drives)
        self.stack.addWidget(self.tab_caches)

        self.tab_devtools = DevToolsManagerTab(self)
        self.tab_devtools.status_message.connect(self._set_status)
        self.tab_devtools.disk_refresh_requested.connect(self.refresh_drives)
        self.stack.addWidget(self.tab_devtools)

        main_layout.addWidget(self.stack, 1)

    def _build_status_bar(self) -> None:
        status = QStatusBar(self)
        self.setStatusBar(status)

    def _on_lang_combo_changed(self, idx: int) -> None:
        code = self.cmb_lang.itemData(idx)
        if code:
            i18n.set_language(str(code))

    def _on_language_changed(self, _lang: str) -> None:
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        lang = i18n.language

        # Menü çubuğu
        self.file_menu.setTitle(tr("menu_file"))
        self.act_refresh_view.setText(tr("menu_refresh_view"))
        self.act_exit.setText(tr("menu_exit"))

        self.view_menu.setTitle(tr("menu_view"))
        self.act_v0.setText(tr("nav_apps"))
        self.act_v1.setText(tr("nav_caches"))
        self.act_v2.setText(tr("nav_devtools"))
        self.act_drives.setText(tr("menu_refresh_drives"))

        self.lang_menu.setTitle(tr("menu_language"))
        self.act_lang_tr.setChecked(lang == "tr")
        self.act_lang_en.setChecked(lang == "en")

        self.help_menu.setTitle(tr("menu_help"))
        self.act_about.setText(tr("menu_about"))

        # Yan panel
        self.lbl_app_sub.setText(tr("app_subtitle"))
        self.lbl_nav_section.setText(tr("sidebar_sections"))
        for idx, (_page_idx, _ico, key) in enumerate(self._nav_specs):
            if idx < len(self._nav_buttons):
                self._nav_buttons[idx].setText(tr(key))

        self.lbl_lang_section.setText(tr("sidebar_language"))
        self.cmb_lang.blockSignals(True)
        self.cmb_lang.setCurrentIndex(0 if lang == "tr" else 1)
        self.cmb_lang.blockSignals(False)

        self.lbl_drives_section.setText(tr("sidebar_drives"))
        self.refresh_drives()
        self._set_status(tr("ready"))

    def _set_status(self, message: str) -> None:
        sb = self.statusBar()
        if sb is not None:
            sb.showMessage(message)

    def _switch_page(self, index: int) -> None:
        if index < 0 or index >= self.stack.count():
            return
        self.stack.setCurrentIndex(index)
        if index < len(self._nav_buttons):
            self._nav_buttons[index].setChecked(True)

        if index not in self._scanned_tabs:
            self._scanned_tabs.add(index)
            self._refresh_current_tab()

    def _refresh_current_tab(self) -> None:
        idx = self.stack.currentIndex()
        self.refresh_drives()
        if idx == 0:
            self.tab_apps.start_scan()
        elif idx == 1:
            self.tab_caches.start_scan()
        elif idx == 2:
            self.tab_devtools.start_scan()

    def refresh_drives(self) -> None:
        while self._drives_container.count():
            item = self._drives_container.takeAt(0)
            w = item.widget() if item else None
            if w is not None:
                w.deleteLater()

        for letter, total, used, free in get_fixed_drives()[:3]:
            card = Win7DriveWidget(letter, total, used, free, self)
            self._drives_container.addWidget(card)

    def _show_about_dialog(self) -> None:
        QMessageBox.about(self, tr("about_title"), tr("about_html"))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.tab_apps.stop_workers()
        self.tab_caches.stop_workers()
        self.tab_devtools.stop_workers()
        super().closeEvent(event)

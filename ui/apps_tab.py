"""Modül 1: Çok yer kaplayan yüklü uygulamaları listeleme, filtreleme ve kaldırma görünümü."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.app_scanner import AppScanWorker, InstalledApp
from core.i18n import i18n, tr
from core.utils import (
    format_bytes,
    format_install_date,
    launch_uninstaller,
    open_in_explorer,
)
from core.win32_icons import parse_display_icon, resolve_app_icon
from ui.win7_icons import Win7Icons
from ui.win7_theme import (
    SORT_ROLE,
    SortableTreeItem,
    Win7DetailsPane,
    Win7HeaderBanner,
    ask_yes_no,
)


APP_DATA_ROLE = Qt.ItemDataRole.UserRole + 1


class InstalledAppsTab(QWidget):
    """Windows 7 'Programlar ve Özellikler' düzeninde yüklü uygulamalar yöneticisi."""

    status_message = pyqtSignal(str)
    disk_refresh_requested = pyqtSignal()

    SIZE_FILTER_KEYS = [
        ("apps_filter_all", 0),
        ("apps_filter_100mb", 100 * 1024 * 1024),
        ("apps_filter_500mb", 500 * 1024 * 1024),
        ("apps_filter_1gb", 1024 * 1024 * 1024),
        ("apps_filter_5gb", 5 * 1024 * 1024 * 1024),
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._apps: list[InstalledApp] = []
        self._worker: Optional[AppScanWorker] = None
        self._fallback_icon = Win7Icons.programs_features()
        self._build_ui()
        self.retranslate_ui()
        i18n.language_changed.connect(lambda _lang: self.retranslate_ui())

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.banner = Win7HeaderBanner(Win7Icons.programs_features(), "", "")
        root.addWidget(self.banner)

        cmd_bar = QFrame()
        cmd_bar.setObjectName("Win7CommandBar")
        cmd_layout = QHBoxLayout(cmd_bar)
        cmd_layout.setContentsMargins(10, 4, 10, 4)
        cmd_layout.setSpacing(6)

        self.btn_uninstall = QPushButton()
        self.btn_uninstall.setIcon(Win7Icons.uac_shield())
        self.btn_uninstall.setIconSize(QSize(16, 16))
        self.btn_uninstall.setEnabled(False)
        self.btn_uninstall.clicked.connect(self._on_uninstall_clicked)
        cmd_layout.addWidget(self.btn_uninstall)

        self.btn_modify = QPushButton()
        self.btn_modify.setIcon(Win7Icons.dev_tools())
        self.btn_modify.setIconSize(QSize(16, 16))
        self.btn_modify.setEnabled(False)
        self.btn_modify.clicked.connect(self._on_modify_clicked)
        cmd_layout.addWidget(self.btn_modify)

        self.btn_open_loc = QPushButton()
        self.btn_open_loc.setIcon(Win7Icons.folder_win7())
        self.btn_open_loc.setIconSize(QSize(16, 16))
        self.btn_open_loc.setEnabled(False)
        self.btn_open_loc.clicked.connect(self._on_open_location_clicked)
        cmd_layout.addWidget(self.btn_open_loc)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(Win7Icons.refresh())
        self.btn_refresh.setIconSize(QSize(16, 16))
        self.btn_refresh.clicked.connect(self.start_scan)
        cmd_layout.addWidget(self.btn_refresh)

        cmd_layout.addStretch(1)

        self.chk_calc_sizes = QCheckBox()
        self.chk_calc_sizes.setChecked(True)
        cmd_layout.addWidget(self.chk_calc_sizes)

        self.lbl_filter = QLabel()
        cmd_layout.addWidget(self.lbl_filter)

        self.cmb_size_filter = QComboBox()
        for key, _ in self.SIZE_FILTER_KEYS:
            self.cmb_size_filter.addItem(tr(key))
        self.cmb_size_filter.currentIndexChanged.connect(self._apply_filters)
        cmd_layout.addWidget(self.cmb_size_filter)

        self.txt_search = QLineEdit()
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setFixedWidth(215)
        self.txt_search.textChanged.connect(self._apply_filters)
        cmd_layout.addWidget(self.txt_search)

        root.addWidget(cmd_bar)

        self.progress_frame = QFrame()
        prog_layout = QHBoxLayout(self.progress_frame)
        prog_layout.setContentsMargins(12, 5, 12, 5)
        prog_layout.setSpacing(10)

        self.lbl_progress = QLabel()
        prog_layout.addWidget(self.lbl_progress, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("Win7GreenProgress")
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setRange(0, 100)
        prog_layout.addWidget(self.progress_bar)

        self.progress_frame.setVisible(False)
        root.addWidget(self.progress_frame)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setIconSize(QSize(20, 20))
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(lambda *_: self._on_uninstall_clicked())

        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(1, 185)
        self.tree.setColumnWidth(2, 115)
        self.tree.setColumnWidth(3, 115)
        self.tree.setColumnWidth(4, 105)
        self.tree.setColumnWidth(5, 115)

        root.addWidget(self.tree, 1)

        self.details_pane = Win7DetailsPane(Win7Icons.programs_features(), "")
        root.addWidget(self.details_pane)

    def retranslate_ui(self) -> None:
        self.banner.set_texts(tr("apps_banner_title"), tr("apps_banner_sub"))
        self.btn_uninstall.setText(tr("btn_uninstall"))
        self.btn_modify.setText(tr("btn_modify"))
        self.btn_open_loc.setText(tr("btn_open_location"))
        self.btn_refresh.setText(tr("btn_refresh"))
        self.chk_calc_sizes.setText(tr("apps_chk_calc_sizes"))
        self.chk_calc_sizes.setToolTip(tr("apps_chk_calc_sizes_tip"))
        self.lbl_filter.setText(tr("apps_lbl_size_filter"))

        prev_idx = max(0, self.cmb_size_filter.currentIndex())
        self.cmb_size_filter.blockSignals(True)
        for idx, (key, _) in enumerate(self.SIZE_FILTER_KEYS):
            self.cmb_size_filter.setItemText(idx, tr(key))
        self.cmb_size_filter.setCurrentIndex(prev_idx)
        self.cmb_size_filter.blockSignals(False)

        self.txt_search.setPlaceholderText(tr("apps_search_ph"))
        self.tree.setHeaderLabels(
            [
                tr("apps_col_name"),
                tr("apps_col_publisher"),
                tr("apps_col_size"),
                tr("apps_col_date"),
                tr("apps_col_version"),
                tr("apps_col_scope"),
            ]
        )
        self.details_pane.set_default_title(tr("apps_det_default_title"))

        if self._apps:
            self._populate_tree()
        else:
            self._update_summary_details(0, 0)

    def start_scan(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        self.progress_frame.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.lbl_progress.setText(tr("apps_scanning"))
        self.status_message.emit(tr("apps_scanning"))

        self._worker = AppScanWorker(
            calculate_missing_sizes=self.chk_calc_sizes.isChecked(),
            include_system_components=False,
            parent=self,
        )
        self._worker.progress_changed.connect(self._on_scan_progress)
        self._worker.scan_completed.connect(self._on_scan_completed)
        self._worker.start()

    def stop_workers(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1500)

    def _on_scan_progress(self, current: int, total: int, message: str) -> None:
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        self.lbl_progress.setText(message)

    def _on_scan_completed(self, apps: list[InstalledApp]) -> None:
        self._apps = apps
        self.progress_frame.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self._populate_tree()
        total_sz = sum(a.size_bytes for a in apps)
        self.status_message.emit(
            tr("apps_scan_done_status", count=len(apps), size=format_bytes(total_sz))
        )

    def _populate_tree(self) -> None:
        sort_col = self.tree.sortColumn() if self.tree.topLevelItemCount() > 0 else 2
        sort_order = (
            self.tree.header().sortIndicatorOrder()
            if self.tree.topLevelItemCount() > 0
            else Qt.SortOrder.DescendingOrder
        )

        self.tree.setSortingEnabled(False)
        self.tree.clear()

        bold_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)

        for app in self._apps:
            item = SortableTreeItem()
            icon = resolve_app_icon(app.display_icon, app.install_location, self._fallback_icon)

            item.setIcon(0, icon)
            item.setText(0, app.name)
            item.setData(0, SORT_ROLE, app.name.lower())
            item.setData(0, APP_DATA_ROLE, app)

            pub = app.publisher
            item.setText(1, pub)
            item.setData(1, SORT_ROLE, pub.lower())

            size_text = format_bytes(app.size_bytes) if app.size_bytes > 0 else "—"
            item.setText(2, size_text)
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setData(2, SORT_ROLE, app.size_bytes)
            if app.size_bytes >= 1024 * 1024 * 1024:
                item.setFont(2, bold_font)

            item.setText(3, format_install_date(app.install_date))
            item.setData(3, SORT_ROLE, app.install_date or "00000000")

            item.setText(4, app.version)
            item.setData(4, SORT_ROLE, app.version.lower())

            sc = app.scope
            item.setText(5, sc)
            item.setData(5, SORT_ROLE, sc.lower())

            self.tree.addTopLevelItem(item)

        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(sort_col, sort_order)
        self._apply_filters()
        self._update_summary_details()

    def _apply_filters(self) -> None:
        query = self.txt_search.text().strip().lower()
        idx = self.cmb_size_filter.currentIndex()
        min_bytes = self.SIZE_FILTER_KEYS[idx][1] if 0 <= idx < len(self.SIZE_FILTER_KEYS) else 0

        visible_count = 0
        visible_bytes = 0

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is None:
                continue
            app: Optional[InstalledApp] = item.data(0, APP_DATA_ROLE)
            if app is None:
                continue

            matches_size = app.size_bytes >= min_bytes
            matches_query = (
                not query
                or query in app.name.lower()
                or query in app.publisher.lower()
                or query in app.install_location.lower()
            )
            visible = matches_size and matches_query
            item.setHidden(not visible)
            if visible:
                visible_count += 1
                visible_bytes += app.size_bytes

        if not self.tree.selectedItems():
            self._update_summary_details(visible_count, visible_bytes)

    def _selected_app(self) -> Optional[InstalledApp]:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, APP_DATA_ROLE)

    def _resolve_target_folder(self, app: InstalledApp) -> str:
        if app.install_location:
            return app.install_location
        ico_path, _ = parse_display_icon(app.display_icon)
        return ico_path

    def _on_selection_changed(self) -> None:
        app = self._selected_app()
        if app is None:
            self.btn_uninstall.setEnabled(False)
            self.btn_modify.setEnabled(False)
            self.btn_open_loc.setEnabled(False)
            self._update_summary_details()
            return

        self.btn_uninstall.setEnabled(bool(app.uninstall_string))
        self.btn_modify.setEnabled(bool(app.modify_path))
        self.btn_open_loc.setEnabled(bool(self._resolve_target_folder(app)))

        icon = resolve_app_icon(app.display_icon, app.install_location, self._fallback_icon)
        size_lbl = format_bytes(app.size_bytes) if app.size_bytes > 0 else tr("unspecified")
        if app.size_is_calculated:
            size_lbl += tr("apps_calculated_suffix")

        loc_lbl = app.install_location or tr("unspecified")
        self.details_pane.set_details(
            icon,
            app.name,
            [
                tr("apps_det_publisher", val=app.publisher),
                tr("apps_det_version", val=app.version),
                tr("apps_det_size", val=size_lbl),
                tr("apps_det_location", val=loc_lbl),
            ],
        )

    def _update_summary_details(
        self,
        visible_count: Optional[int] = None,
        visible_bytes: Optional[int] = None,
    ) -> None:
        if visible_count is None or visible_bytes is None:
            visible_count = 0
            visible_bytes = 0
            for i in range(self.tree.topLevelItemCount()):
                it = self.tree.topLevelItem(i)
                if it and not it.isHidden():
                    app: Optional[InstalledApp] = it.data(0, APP_DATA_ROLE)
                    visible_count += 1
                    if app:
                        visible_bytes += app.size_bytes

        self.details_pane.reset(
            [
                tr("apps_sum_count", count=visible_count),
                tr("apps_sum_size", size=format_bytes(visible_bytes)),
                tr("apps_sum_sort_tip"),
                tr("apps_sum_unins_tip"),
            ]
        )

    def _on_uninstall_clicked(self) -> None:
        app = self._selected_app()
        if app is None or not app.uninstall_string:
            return

        size_info = format_bytes(app.size_bytes) if app.size_bytes > 0 else tr("unknown")
        confirmed = ask_yes_no(
            self,
            tr("apps_confirm_title"),
            tr(
                "apps_confirm_body",
                name=app.name,
                publisher=app.publisher,
                size=size_info,
                cmd=app.uninstall_string,
            ),
        )
        if not confirmed:
            return

        ok, msg = launch_uninstaller(app.uninstall_string, prefer_uninstall_for_msi=True)
        self.status_message.emit(f"{app.name}: {msg}")
        if not ok:
            QMessageBox.warning(self, tr("apps_unins_err_title"), msg)
        else:
            self.disk_refresh_requested.emit()

    def _on_modify_clicked(self) -> None:
        app = self._selected_app()
        if app is None or not app.modify_path:
            return
        ok, msg = launch_uninstaller(app.modify_path, prefer_uninstall_for_msi=False)
        self.status_message.emit(f"{app.name}: {msg}")
        if not ok:
            QMessageBox.warning(self, tr("apps_mod_err_title"), msg)

    def _on_open_location_clicked(self) -> None:
        app = self._selected_app()
        if app is None:
            return
        target = self._resolve_target_folder(app)
        if not open_in_explorer(target):
            QMessageBox.information(self, "DevClean", tr("apps_no_loc_msg"))

    def _on_context_menu(self, pos) -> None:
        item: Optional[QTreeWidgetItem] = self.tree.itemAt(pos)
        if item is None:
            return
        self.tree.setCurrentItem(item)
        app = self._selected_app()
        if app is None:
            return

        menu = QMenu(self)
        act_uninstall = QAction(Win7Icons.uac_shield(), tr("btn_uninstall"), self)
        act_uninstall.setEnabled(bool(app.uninstall_string))
        act_uninstall.triggered.connect(self._on_uninstall_clicked)
        menu.addAction(act_uninstall)

        if app.modify_path:
            act_mod = QAction(Win7Icons.dev_tools(), tr("btn_modify_repair"), self)
            act_mod.triggered.connect(self._on_modify_clicked)
            menu.addAction(act_mod)

        menu.addSeparator()
        act_open = QAction(Win7Icons.folder_win7(), tr("btn_open_location"), self)
        act_open.setEnabled(bool(self._resolve_target_folder(app)))
        act_open.triggered.connect(self._on_open_location_clicked)
        menu.addAction(act_open)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

"""
Modül 3: Kodlama dillerini, IDE'leri ve SDK paketlerini
(Visual Studio, Python, PyCharm, VS SDKs, Android Studio) yönetme ve kaldırma görünümü.
"""

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QIcon
from PyQt6.QtWidgets import (
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

from core.dev_tools_manager import (
    CAT_ANDROID,
    CAT_OTHER,
    CAT_PYCHARM,
    CAT_PYTHON,
    CAT_VS,
    CAT_VS_SDKS,
    ORDERED_CATEGORIES,
    DevToolEntry,
    DevToolsScanWorker,
)
from core.i18n import i18n, tr
from core.utils import (
    delete_permanently,
    format_bytes,
    launch_uninstaller,
    open_in_explorer,
    send_to_recycle_bin,
)
from core.win32_icons import resolve_app_icon
from ui.win7_icons import Win7Icons
from ui.win7_theme import (
    SORT_ROLE,
    SortableTreeItem,
    Win7DetailsPane,
    Win7HeaderBanner,
    ask_yes_no,
)


DEVTOOL_DATA_ROLE = Qt.ItemDataRole.UserRole + 3
CAT_ID_ROLE = Qt.ItemDataRole.UserRole + 4


class DevToolsManagerTab(QWidget):
    """Visual Studio, VS SDKs, Python, PyCharm ve Android Studio yönetim görünümü."""

    status_message = pyqtSignal(str)
    disk_refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._grouped: dict[str, list[DevToolEntry]] = {}
        self._worker: Optional[DevToolsScanWorker] = None
        self._vs_installer_path = self._locate_vs_installer()
        self.btn_vs_installer: Optional[QPushButton] = None
        self._build_ui()
        self.retranslate_ui()
        i18n.language_changed.connect(lambda _lang: self.retranslate_ui())

    @staticmethod
    def _locate_vs_installer() -> str:
        pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        candidate = os.path.join(pf86, "Microsoft Visual Studio", "Installer", "vs_installer.exe")
        return candidate if os.path.isfile(candidate) else ""

    def _category_icon(self, category_id: str) -> QIcon:
        mapping = {
            CAT_VS: Win7Icons.category_vs(),
            CAT_VS_SDKS: Win7Icons.category_sdk(),
            CAT_PYTHON: Win7Icons.category_python(),
            CAT_PYCHARM: Win7Icons.category_pycharm(),
            CAT_ANDROID: Win7Icons.category_android(),
            CAT_OTHER: Win7Icons.dev_tools(),
        }
        return mapping.get(category_id, Win7Icons.dev_tools())

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.banner = Win7HeaderBanner(Win7Icons.dev_tools(), "", "")
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

        self.btn_remove_folder = QPushButton()
        self.btn_remove_folder.setIcon(Win7Icons.recycle_bin())
        self.btn_remove_folder.setIconSize(QSize(16, 16))
        self.btn_remove_folder.setEnabled(False)
        self.btn_remove_folder.clicked.connect(self._on_remove_component_folder)
        cmd_layout.addWidget(self.btn_remove_folder)

        if self._vs_installer_path:
            self.btn_vs_installer = QPushButton()
            self.btn_vs_installer.setIcon(Win7Icons.category_vs())
            self.btn_vs_installer.setIconSize(QSize(16, 16))
            self.btn_vs_installer.clicked.connect(self._on_open_vs_installer)
            cmd_layout.addWidget(self.btn_vs_installer)

        self.btn_open_loc = QPushButton()
        self.btn_open_loc.setIcon(Win7Icons.folder_win7())
        self.btn_open_loc.setIconSize(QSize(16, 16))
        self.btn_open_loc.setEnabled(False)
        self.btn_open_loc.clicked.connect(self._on_open_location)
        cmd_layout.addWidget(self.btn_open_loc)

        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(Win7Icons.refresh())
        self.btn_refresh.setIconSize(QSize(16, 16))
        self.btn_refresh.clicked.connect(self.start_scan)
        cmd_layout.addWidget(self.btn_refresh)

        cmd_layout.addStretch(1)

        self.cmb_category = QComboBox()
        self.cmb_category.addItem("")
        for cat_id in ORDERED_CATEGORIES:
            self.cmb_category.addItem(tr(cat_id), cat_id)
        self.cmb_category.currentIndexChanged.connect(self._apply_filters)
        cmd_layout.addWidget(self.cmb_category)

        self.txt_search = QLineEdit()
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setFixedWidth(185)
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
        self.progress_bar.setRange(0, 0)
        prog_layout.addWidget(self.progress_bar)

        self.progress_frame.setVisible(False)
        root.addWidget(self.progress_frame)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(20, 20))
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)

        header = self.tree.header()
        header.setStretchLastSection(True)
        for col in range(4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(0, 310)
        self.tree.setColumnWidth(1, 150)
        self.tree.setColumnWidth(2, 115)
        self.tree.setColumnWidth(3, 115)

        root.addWidget(self.tree, 1)

        self.details_pane = Win7DetailsPane(Win7Icons.dev_tools(), "")
        root.addWidget(self.details_pane)

    def retranslate_ui(self) -> None:
        self.banner.set_texts(tr("dev_banner_title"), tr("dev_banner_sub"))
        self.btn_uninstall.setText(tr("btn_uninstall"))
        self.btn_modify.setText(tr("dev_btn_modify_workloads"))
        self.btn_remove_folder.setText(tr("dev_btn_remove_folder"))
        self.btn_remove_folder.setToolTip(tr("dev_btn_remove_folder_tip"))
        if self.btn_vs_installer is not None:
            self.btn_vs_installer.setText(tr("dev_btn_vs_installer"))
            self.btn_vs_installer.setToolTip(tr("dev_btn_vs_installer_tip"))
        self.btn_open_loc.setText(tr("btn_open_location"))
        self.btn_refresh.setText(tr("btn_refresh"))

        prev_idx = max(0, self.cmb_category.currentIndex())
        self.cmb_category.blockSignals(True)
        self.cmb_category.setItemText(0, tr("dev_filter_all_cats"))
        for idx, cat_id in enumerate(ORDERED_CATEGORIES, start=1):
            self.cmb_category.setItemText(idx, tr(cat_id))
        self.cmb_category.setCurrentIndex(prev_idx)
        self.cmb_category.blockSignals(False)

        self.txt_search.setPlaceholderText(tr("dev_search_ph"))
        self.tree.setHeaderLabels(
            [
                tr("dev_col_name"),
                tr("dev_col_kind"),
                tr("dev_col_version"),
                tr("dev_col_size"),
                tr("dev_col_location"),
            ]
        )
        self.details_pane.set_default_title(tr("dev_det_default_title"))

        if self._grouped:
            self._populate_tree()
        else:
            self._update_summary_details()

    def start_scan(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        self.btn_refresh.setEnabled(False)
        self.progress_frame.setVisible(True)
        self.lbl_progress.setText(tr("dev_scanning_status"))
        self.status_message.emit(tr("dev_scanning_status"))

        self._worker = DevToolsScanWorker(parent=self)
        self._worker.progress_changed.connect(self._on_scan_progress)
        self._worker.scan_completed.connect(self._on_scan_completed)
        self._worker.start()

    def stop_workers(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1500)

    def _on_scan_progress(self, msg: str) -> None:
        self.lbl_progress.setText(msg)

    def _on_scan_completed(self, grouped: dict[str, list[DevToolEntry]]) -> None:
        self._grouped = grouped
        self.progress_frame.setVisible(False)
        self.btn_refresh.setEnabled(True)
        self._populate_tree()

        total_items = sum(len(v) for v in grouped.values())
        total_bytes = sum(e.size_bytes for v in grouped.values() for e in v)
        self.status_message.emit(
            tr("dev_scan_done_status", count=total_items, size=format_bytes(total_bytes))
        )

    def _populate_tree(self) -> None:
        self.tree.clear()

        cat_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        italic_font = QFont("Segoe UI", 9)
        italic_font.setItalic(True)
        muted_brush = QBrush(QColor("#6C7A89"))

        core_five = {CAT_VS, CAT_VS_SDKS, CAT_PYTHON, CAT_PYCHARM, CAT_ANDROID}

        for cat_idx, category_id in enumerate(ORDERED_CATEGORIES):
            entries = self._grouped.get(category_id, [])
            if not entries and category_id not in core_five:
                continue

            cat_label = tr(category_id)
            cat_icon = self._category_icon(category_id)
            cat_bytes = sum(e.size_bytes for e in entries)

            parent_node = SortableTreeItem()
            parent_node.setIcon(0, cat_icon)
            parent_node.setText(0, f"{cat_label} ({len(entries)})")
            parent_node.setFont(0, cat_font)
            parent_node.setData(0, SORT_ROLE, cat_idx)
            parent_node.setData(0, CAT_ID_ROLE, category_id)

            parent_node.setText(1, tr("category_word"))
            parent_node.setText(2, "—")
            parent_node.setText(3, format_bytes(cat_bytes))
            parent_node.setFont(3, cat_font)
            parent_node.setTextAlignment(3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            parent_node.setText(4, "")

            if not entries:
                empty_child = QTreeWidgetItem(parent_node)
                empty_child.setText(0, tr("dev_empty_category"))
                empty_child.setFont(0, italic_font)
                empty_child.setForeground(0, muted_brush)
                empty_child.setText(3, "—")
                empty_child.setTextAlignment(3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                for entry in entries:
                    child = SortableTreeItem(parent_node)
                    resolved_ico = resolve_app_icon(entry.display_icon, entry.location, cat_icon)
                    child.setIcon(0, resolved_ico)
                    label = entry.name
                    if entry.is_active_runtime:
                        label += f" {tr('active_tag')}"
                    child.setText(0, label)
                    child.setData(0, DEVTOOL_DATA_ROLE, entry)

                    child.setText(1, entry.kind)
                    child.setText(2, entry.version)

                    sz_str = format_bytes(entry.size_bytes) if entry.size_bytes > 0 else "—"
                    child.setText(3, sz_str)
                    child.setTextAlignment(3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    child.setData(3, SORT_ROLE, entry.size_bytes)

                    child.setText(4, entry.location or "—")

            self.tree.addTopLevelItem(parent_node)
            parent_node.setExpanded(True)

        self._apply_filters()
        self._update_summary_details()

    def _apply_filters(self) -> None:
        cat_idx = self.cmb_category.currentIndex()
        selected_cat_id = self.cmb_category.itemData(cat_idx) if cat_idx > 0 else None
        query = self.txt_search.text().strip().lower()

        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent is None:
                continue
            parent_cat_id = parent.data(0, CAT_ID_ROLE)
            cat_match = (selected_cat_id is None) or (parent_cat_id == selected_cat_id)
            if not cat_match:
                parent.setHidden(True)
                continue

            if not query:
                parent.setHidden(False)
                for j in range(parent.childCount()):
                    ch = parent.child(j)
                    if ch:
                        ch.setHidden(False)
                continue

            any_child_visible = False
            for j in range(parent.childCount()):
                ch = parent.child(j)
                if ch is None:
                    continue
                entry: Optional[DevToolEntry] = ch.data(0, DEVTOOL_DATA_ROLE)
                if entry is None:
                    ch.setHidden(True)
                    continue
                matched = (
                    query in entry.name.lower()
                    or query in entry.kind.lower()
                    or query in entry.version.lower()
                    or query in entry.location.lower()
                )
                ch.setHidden(not matched)
                if matched:
                    any_child_visible = True
            parent.setHidden(not any_child_visible)

    def _selected_entry(self) -> Optional[DevToolEntry]:
        items = self.tree.selectedItems()
        if not items:
            return None
        return items[0].data(0, DEVTOOL_DATA_ROLE)

    def _on_selection_changed(self) -> None:
        entry = self._selected_entry()
        if entry is None:
            self.btn_uninstall.setEnabled(False)
            self.btn_modify.setEnabled(False)
            self.btn_remove_folder.setEnabled(False)
            self.btn_open_loc.setEnabled(False)
            self._update_summary_details()
            return

        self.btn_uninstall.setEnabled(bool(entry.uninstall_command) and not entry.is_active_runtime)
        self.btn_modify.setEnabled(bool(entry.modify_command))
        self.btn_remove_folder.setEnabled(bool(entry.can_delete_folder) and not entry.is_active_runtime)
        self.btn_open_loc.setEnabled(bool(entry.location and os.path.exists(entry.location)))

        cat_icon = self._category_icon(entry.category_id)
        icon = resolve_app_icon(entry.display_icon, entry.location, cat_icon)
        sz_lbl = format_bytes(entry.size_bytes) if entry.size_bytes > 0 else tr("unspecified")

        self.details_pane.set_details(
            icon,
            entry.name,
            [
                tr("dev_det_cat_kind", cat=entry.category, kind=entry.kind),
                tr("dev_det_ver_pub", ver=entry.version, pub=entry.publisher),
                tr("dev_det_size_note", size=sz_lbl, note=entry.notes or "—"),
                tr("dev_det_location", loc=entry.location or tr("unspecified")),
            ],
        )

    def _update_summary_details(self) -> None:
        total_items = sum(len(v) for v in self._grouped.values())
        total_bytes = sum(e.size_bytes for v in self._grouped.values() for e in v)
        self.details_pane.reset(
            [
                tr("dev_sum_count", count=total_items),
                tr("dev_sum_size", size=format_bytes(total_bytes)),
                tr("dev_sum_envs"),
                tr("dev_sum_tip"),
            ]
        )

    def _on_uninstall_clicked(self) -> None:
        entry = self._selected_entry()
        if entry is None or not entry.uninstall_command or entry.is_active_runtime:
            return

        sz_lbl = format_bytes(entry.size_bytes) if entry.size_bytes > 0 else tr("unknown")
        confirmed = ask_yes_no(
            self,
            tr("dev_confirm_unins_title"),
            tr(
                "dev_confirm_unins_body",
                name=entry.name,
                cat=entry.category,
                size=sz_lbl,
                cmd=entry.uninstall_command,
            ),
        )
        if not confirmed:
            return

        ok, msg = launch_uninstaller(entry.uninstall_command, prefer_uninstall_for_msi=True)
        self.status_message.emit(f"{entry.name}: {msg}")
        if not ok:
            QMessageBox.warning(self, tr("apps_unins_err_title"), msg)
        else:
            self.disk_refresh_requested.emit()

    def _on_modify_clicked(self) -> None:
        entry = self._selected_entry()
        if entry is None or not entry.modify_command:
            return
        ok, msg = launch_uninstaller(entry.modify_command, prefer_uninstall_for_msi=False)
        self.status_message.emit(f"{entry.name}: {msg}")
        if not ok:
            QMessageBox.warning(self, tr("dev_mod_err_title"), msg)

    def _on_open_vs_installer(self) -> None:
        if not self._vs_installer_path:
            return
        ok, msg = launch_uninstaller(f'"{self._vs_installer_path}"', prefer_uninstall_for_msi=False)
        self.status_message.emit(f"Visual Studio Installer: {msg}")
        if not ok:
            QMessageBox.warning(self, "DevClean", msg)

    def _on_remove_component_folder(self) -> None:
        entry = self._selected_entry()
        if entry is None or not entry.can_delete_folder or not entry.location:
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(tr("dev_del_folder_title"))
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(tr("dev_del_folder_q", name=entry.name))
        msg_box.setInformativeText(
            tr(
                "dev_del_folder_info",
                loc=entry.location,
                size=format_bytes(entry.size_bytes),
                note=entry.notes or "—",
            )
        )
        btn_recycle = msg_box.addButton(tr("caches_btn_recycle"), QMessageBox.ButtonRole.AcceptRole)
        btn_perm = msg_box.addButton(tr("caches_btn_delete_perm"), QMessageBox.ButtonRole.DestructiveRole)
        btn_cancel = msg_box.addButton(tr("cancel"), QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(btn_recycle)
        msg_box.exec()

        clicked = msg_box.clickedButton()
        if clicked == btn_cancel or clicked is None:
            return

        if clicked == btn_recycle:
            ok, result_msg = send_to_recycle_bin(entry.location)
        elif clicked == btn_perm:
            ok, result_msg = delete_permanently(entry.location)
        else:
            return

        if ok:
            self.status_message.emit(f"{entry.name}: {result_msg}")
            self.disk_refresh_requested.emit()
            self.start_scan()
        else:
            QMessageBox.warning(self, tr("dev_del_err_title"), result_msg)

    def _on_open_location(self) -> None:
        entry = self._selected_entry()
        if entry is None or not entry.location:
            return
        if not open_in_explorer(entry.location):
            QMessageBox.information(self, "DevClean", tr("msg_folder_not_found"))

    def _on_context_menu(self, pos) -> None:
        node = self.tree.itemAt(pos)
        if node is None:
            return
        self.tree.setCurrentItem(node)
        entry = self._selected_entry()
        if entry is None:
            return

        menu = QMenu(self)
        if entry.uninstall_command and not entry.is_active_runtime:
            act_unins = QAction(Win7Icons.uac_shield(), tr("btn_uninstall"), self)
            act_unins.triggered.connect(self._on_uninstall_clicked)
            menu.addAction(act_unins)

        if entry.modify_command:
            act_mod = QAction(Win7Icons.dev_tools(), tr("dev_ctx_modify"), self)
            act_mod.triggered.connect(self._on_modify_clicked)
            menu.addAction(act_mod)

        if entry.can_delete_folder and not entry.is_active_runtime:
            act_del = QAction(Win7Icons.recycle_bin(), tr("dev_ctx_del_folder"), self)
            act_del.triggered.connect(self._on_remove_component_folder)
            menu.addAction(act_del)

        if menu.actions():
            menu.addSeparator()

        act_open = QAction(Win7Icons.folder_win7(), tr("btn_open_location"), self)
        act_open.setEnabled(bool(entry.location and os.path.exists(entry.location)))
        act_open.triggered.connect(self._on_open_location)
        menu.addAction(act_open)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

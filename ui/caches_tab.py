"""
Modül 2: Geçici kodlama dili dosyaları (.venv, .cache, .nuget, __pycache__,
node_modules, .gradle vb.) tarama ve temizleme görünümü.
"""

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.cache_scanner import (
    CacheCleanWorker,
    CacheItem,
    CacheScanWorker,
    get_default_workspace_roots,
)
from core.i18n import i18n, tr
from core.utils import format_bytes, format_timestamp, open_in_explorer
from ui.win7_icons import Win7Icons
from ui.win7_theme import (
    SORT_ROLE,
    SortableTreeItem,
    Win7DetailsPane,
    Win7HeaderBanner,
    ask_yes_no,
)


CACHE_DATA_ROLE = Qt.ItemDataRole.UserRole + 2


class WorkspaceRootsDialog(QDialog):
    """Taranacak proje çalışma alanı klasörlerini düzenleme penceresi."""

    def __init__(self, roots: list[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("roots_dlg_title"))
        self.setWindowIcon(Win7Icons.folder_win7())
        self.resize(540, 340)

        layout = QVBoxLayout(self)
        info = QLabel(tr("roots_dlg_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.list_widget = QListWidget()
        for r in roots:
            self.list_widget.addItem(r)
        layout.addWidget(self.list_widget, 1)

        btn_row = QHBoxLayout()
        btn_add = QPushButton(tr("roots_btn_add"))
        btn_add.setIcon(Win7Icons.folder_win7())
        btn_add.clicked.connect(self._add_folder)
        btn_row.addWidget(btn_add)

        btn_remove = QPushButton(tr("roots_btn_remove"))
        btn_remove.clicked.connect(self._remove_selected)
        btn_row.addWidget(btn_remove)

        btn_reset = QPushButton(tr("roots_btn_reset"))
        btn_reset.clicked.connect(self._reset_defaults)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText(tr("ok"))
        cancel_btn = box.button(QDialogButtonBox.StandardButton.Cancel)
        if cancel_btn:
            cancel_btn.setText(tr("cancel"))
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr("roots_pick_title"))
        if folder:
            norm = os.path.normpath(folder)
            existing = {
                os.path.normcase(self.list_widget.item(i).text())
                for i in range(self.list_widget.count())
            }
            if os.path.normcase(norm) not in existing:
                self.list_widget.addItem(norm)

    def _remove_selected(self) -> None:
        for item in self.list_widget.selectedItems():
            row = self.list_widget.row(item)
            self.list_widget.takeItem(row)

    def _reset_defaults(self) -> None:
        self.list_widget.clear()
        for r in get_default_workspace_roots():
            self.list_widget.addItem(r)

    def get_roots(self) -> list[str]:
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]


class DeveloperCachesTab(QWidget):
    """Windows 7 Disk Temizleme düzeninde geçici geliştirici dosyaları yöneticisi."""

    status_message = pyqtSignal(str)
    disk_refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._workspace_roots: list[str] = get_default_workspace_roots()
        self._items: list[CacheItem] = []
        self._scan_worker: Optional[CacheScanWorker] = None
        self._clean_worker: Optional[CacheCleanWorker] = None
        self._updating_checks = False
        self._build_ui()
        self.retranslate_ui()
        i18n.language_changed.connect(lambda _lang: self.retranslate_ui())

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.banner = Win7HeaderBanner(Win7Icons.folder_cache(), "", "")
        root.addWidget(self.banner)

        cmd_bar = QFrame()
        cmd_bar.setObjectName("Win7CommandBar")
        cmd_layout = QHBoxLayout(cmd_bar)
        cmd_layout.setContentsMargins(10, 4, 10, 4)
        cmd_layout.setSpacing(6)

        self.btn_scan = QPushButton()
        self.btn_scan.setIcon(Win7Icons.search_scan())
        self.btn_scan.setIconSize(QSize(16, 16))
        self.btn_scan.clicked.connect(self.start_scan)
        cmd_layout.addWidget(self.btn_scan)

        self.btn_roots = QPushButton()
        self.btn_roots.setIcon(Win7Icons.folder_win7())
        self.btn_roots.setIconSize(QSize(16, 16))
        self.btn_roots.clicked.connect(self._on_manage_roots)
        cmd_layout.addWidget(self.btn_roots)

        self.btn_recycle = QPushButton()
        self.btn_recycle.setIcon(Win7Icons.recycle_bin())
        self.btn_recycle.setIconSize(QSize(16, 16))
        self.btn_recycle.setEnabled(False)
        self.btn_recycle.clicked.connect(lambda: self._start_cleanup(use_recycle_bin=True))
        cmd_layout.addWidget(self.btn_recycle)

        self.btn_delete_perm = QPushButton()
        self.btn_delete_perm.setIcon(Win7Icons.delete_permanent())
        self.btn_delete_perm.setIconSize(QSize(16, 16))
        self.btn_delete_perm.setEnabled(False)
        self.btn_delete_perm.clicked.connect(lambda: self._start_cleanup(use_recycle_bin=False))
        cmd_layout.addWidget(self.btn_delete_perm)

        self.btn_select_all = QPushButton()
        self.btn_select_all.clicked.connect(lambda: self._set_all_checked(True))
        cmd_layout.addWidget(self.btn_select_all)

        self.btn_clear_sel = QPushButton()
        self.btn_clear_sel.clicked.connect(lambda: self._set_all_checked(False))
        cmd_layout.addWidget(self.btn_clear_sel)

        cmd_layout.addStretch(1)

        self.txt_search = QLineEdit()
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setFixedWidth(225)
        self.txt_search.textChanged.connect(self._apply_search_filter)
        cmd_layout.addWidget(self.txt_search)

        root.addWidget(cmd_bar)

        summary_strip = QFrame()
        summary_strip.setStyleSheet(
            "QFrame { background-color: #F7FAFE; border-bottom: 1px solid #DCE5F0; }"
        )
        sum_layout = QHBoxLayout(summary_strip)
        sum_layout.setContentsMargins(14, 6, 14, 6)
        sum_layout.setSpacing(16)

        self.lbl_selection_summary = QLabel()
        self.lbl_selection_summary.setStyleSheet("color: #003399; font-weight: 600;")
        sum_layout.addWidget(self.lbl_selection_summary)

        sum_layout.addStretch(1)

        self.lbl_roots_hint = QLabel()
        self.lbl_roots_hint.setStyleSheet("color: #4D5E73; font-size: 8.5pt;")
        sum_layout.addWidget(self.lbl_roots_hint)

        root.addWidget(summary_strip)

        self.progress_frame = QFrame()
        prog_layout = QHBoxLayout(self.progress_frame)
        prog_layout.setContentsMargins(12, 5, 12, 5)
        prog_layout.setSpacing(10)

        self.lbl_progress = QLabel()
        prog_layout.addWidget(self.lbl_progress, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("Win7GreenProgress")
        self.progress_bar.setFixedWidth(220)
        prog_layout.addWidget(self.progress_bar)

        self.progress_frame.setVisible(False)
        root.addWidget(self.progress_frame)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIconSize(QSize(18, 18))
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemChanged.connect(self._on_item_check_changed)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)

        header = self.tree.header()
        header.setStretchLastSection(True)
        for col in range(4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(0, 295)
        self.tree.setColumnWidth(1, 115)
        self.tree.setColumnWidth(2, 100)
        self.tree.setColumnWidth(3, 130)

        root.addWidget(self.tree, 1)

        self.details_pane = Win7DetailsPane(Win7Icons.folder_cache(), "")
        root.addWidget(self.details_pane)

    def retranslate_ui(self) -> None:
        # Mevcut işaretli öğeleri koru
        checked_paths = {os.path.normcase(ci.path) for ci in self._get_checked_items()}
        had_tree_items = self.tree.topLevelItemCount() > 0

        self.banner.set_texts(tr("caches_banner_title"), tr("caches_banner_sub"))
        self.btn_scan.setText(tr("caches_btn_rescan"))
        self.btn_roots.setText(tr("caches_btn_roots"))
        self.btn_recycle.setText(tr("caches_btn_recycle"))
        self.btn_delete_perm.setText(tr("caches_btn_delete_perm"))
        self.btn_select_all.setText(tr("caches_btn_select_all"))
        self.btn_clear_sel.setText(tr("caches_btn_clear_sel"))
        self.txt_search.setPlaceholderText(tr("caches_search_ph"))
        self._update_roots_hint()

        self.tree.setHeaderLabels(
            [
                tr("caches_col_name"),
                tr("caches_col_size"),
                tr("caches_col_files"),
                tr("caches_col_modified"),
                tr("caches_col_path"),
            ]
        )
        self.details_pane.set_default_title(tr("caches_det_default_title"))

        if self._items:
            self._populate_tree(preserve_checked=checked_paths if had_tree_items else None)
        else:
            self._recalculate_checked_summary()

    def _update_roots_hint(self) -> None:
        self.lbl_roots_hint.setText(tr("caches_roots_hint", count=len(self._workspace_roots)))

    def _on_manage_roots(self) -> None:
        dlg = WorkspaceRootsDialog(self._workspace_roots, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._workspace_roots = dlg.get_roots()
            self._update_roots_hint()
            self.start_scan()

    def start_scan(self) -> None:
        if (self._scan_worker and self._scan_worker.isRunning()) or (
            self._clean_worker and self._clean_worker.isRunning()
        ):
            return

        self._items.clear()
        self.tree.clear()
        self.btn_scan.setEnabled(False)
        self.btn_recycle.setEnabled(False)
        self.btn_delete_perm.setEnabled(False)
        self.progress_frame.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.lbl_progress.setText(tr("caches_scanning_status"))
        self.status_message.emit(tr("caches_scanning_status"))

        self._scan_worker = CacheScanWorker(
            workspace_roots=list(self._workspace_roots),
            include_global_caches=True,
            parent=self,
        )
        self._scan_worker.progress_changed.connect(self._on_scan_progress)
        self._scan_worker.scan_completed.connect(self._on_scan_completed)
        self._scan_worker.start()

    def stop_workers(self) -> None:
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
            self._scan_worker.wait(1500)
        if self._clean_worker and self._clean_worker.isRunning():
            self._clean_worker.cancel()
            self._clean_worker.wait(1500)

    def _on_scan_progress(self, msg: str) -> None:
        self.lbl_progress.setText(msg)

    def _on_scan_completed(self, items: list[CacheItem]) -> None:
        self._items = items
        self.progress_frame.setVisible(False)
        self.btn_scan.setEnabled(True)
        self._populate_tree()
        total_bytes = sum(i.size_bytes for i in items)
        self.status_message.emit(
            tr("caches_scan_done_status", count=len(items), size=format_bytes(total_bytes))
        )

    def _populate_tree(self, preserve_checked: Optional[set[str]] = None) -> None:
        self._updating_checks = True
        self.tree.setSortingEnabled(False)
        self.tree.clear()

        grouped: dict[str, list[CacheItem]] = {}
        for item in self._items:
            grouped.setdefault(item.category_key, []).append(item)

        cat_font = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        folder_icon = Win7Icons.folder_win7()
        cache_icon = Win7Icons.folder_cache()

        for cat_key, cat_items in grouped.items():
            cat_label = tr(cat_key)
            cat_bytes = sum(x.size_bytes for x in cat_items)
            cat_files = sum(x.file_count for x in cat_items)

            parent_node = SortableTreeItem()
            parent_node.setFlags(
                parent_node.flags()
                | Qt.ItemFlag.ItemIsAutoTristate
                | Qt.ItemFlag.ItemIsUserCheckable
            )
            parent_node.setIcon(0, cache_icon)
            parent_node.setText(0, f"{cat_label} ({len(cat_items)})")
            parent_node.setFont(0, cat_font)
            parent_node.setData(0, SORT_ROLE, cat_label.lower())

            parent_node.setText(1, format_bytes(cat_bytes))
            parent_node.setFont(1, cat_font)
            parent_node.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            parent_node.setData(1, SORT_ROLE, cat_bytes)

            parent_node.setText(2, i18n.format_int(cat_files))
            parent_node.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            parent_node.setData(2, SORT_ROLE, cat_files)

            parent_node.setText(3, "—")
            parent_node.setData(3, SORT_ROLE, 0.0)
            parent_node.setText(4, tr("caches_dirs_count", count=len(cat_items)))

            for ci in cat_items:
                child = SortableTreeItem(parent_node)
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                if preserve_checked is not None:
                    is_chk = os.path.normcase(ci.path) in preserve_checked
                else:
                    is_chk = ci.default_checked
                child.setCheckState(
                    0,
                    Qt.CheckState.Checked if is_chk else Qt.CheckState.Unchecked,
                )
                child.setIcon(0, folder_icon)
                child.setText(0, ci.name)
                child.setData(0, SORT_ROLE, ci.name.lower())
                child.setData(0, CACHE_DATA_ROLE, ci)

                child.setText(1, format_bytes(ci.size_bytes))
                child.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                child.setData(1, SORT_ROLE, ci.size_bytes)

                child.setText(2, i18n.format_int(ci.file_count))
                child.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                child.setData(2, SORT_ROLE, ci.file_count)

                child.setText(3, format_timestamp(ci.last_modified))
                child.setData(3, SORT_ROLE, ci.last_modified)

                child.setText(4, ci.path)
                child.setData(4, SORT_ROLE, ci.path.lower())

            self.tree.addTopLevelItem(parent_node)
            parent_node.setExpanded(True)

        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self._updating_checks = False

        self._apply_search_filter()
        self._recalculate_checked_summary()

    def _get_checked_items(self) -> list[CacheItem]:
        checked: list[CacheItem] = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent is None:
                continue
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child and child.checkState(0) == Qt.CheckState.Checked:
                    ci: Optional[CacheItem] = child.data(0, CACHE_DATA_ROLE)
                    if ci is not None:
                        checked.append(ci)
        return checked

    def _on_item_check_changed(self, _item: QTreeWidgetItem, column: int) -> None:
        if self._updating_checks or column != 0:
            return
        self._recalculate_checked_summary()

    def _recalculate_checked_summary(self) -> None:
        checked = self._get_checked_items()
        total_sel_bytes = sum(x.size_bytes for x in checked)
        self.lbl_selection_summary.setText(
            tr("caches_sel_summary", size=format_bytes(total_sel_bytes), count=len(checked))
        )
        has_sel = len(checked) > 0
        self.btn_recycle.setEnabled(has_sel)
        self.btn_delete_perm.setEnabled(has_sel)

        if not self.tree.selectedItems():
            all_bytes = sum(x.size_bytes for x in self._items)
            self.details_pane.reset(
                [
                    tr("caches_sum_total", size=format_bytes(all_bytes), count=len(self._items)),
                    tr("caches_sum_selected", size=format_bytes(total_sel_bytes), count=len(checked)),
                    tr("caches_sum_scope"),
                    tr("caches_sum_tip"),
                ]
            )

    def _set_all_checked(self, state: bool) -> None:
        self._updating_checks = True
        check_val = Qt.CheckState.Checked if state else Qt.CheckState.Unchecked
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent is None or parent.isHidden():
                continue
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child and not child.isHidden():
                    child.setCheckState(0, check_val)
        self._updating_checks = False
        self._recalculate_checked_summary()

    def _apply_search_filter(self) -> None:
        query = self.txt_search.text().strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            if parent is None:
                continue
            any_visible = False
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child is None:
                    continue
                ci: Optional[CacheItem] = child.data(0, CACHE_DATA_ROLE)
                if ci is None:
                    continue
                match = (
                    not query
                    or query in ci.name.lower()
                    or query in ci.category.lower()
                    or query in ci.path.lower()
                )
                child.setHidden(not match)
                if match:
                    any_visible = True
            parent.setHidden(not any_visible)

    def _on_selection_changed(self) -> None:
        sel = self.tree.selectedItems()
        if not sel:
            self._recalculate_checked_summary()
            return
        node = sel[0]
        ci: Optional[CacheItem] = node.data(0, CACHE_DATA_ROLE)
        if ci is None:
            self.details_pane.set_details(
                Win7Icons.folder_cache(),
                node.text(0),
                [
                    tr("caches_cat_det_size", size=node.text(1)),
                    tr("caches_cat_det_files", count=node.text(2)),
                    tr("caches_cat_det_dirs", count=node.childCount()),
                    tr("caches_cat_det_tip"),
                ],
            )
            return

        self.details_pane.set_details(
            Win7Icons.folder_win7(),
            ci.name,
            [
                tr("caches_item_det_cat", cat=ci.category, group=ci.group),
                tr(
                    "caches_item_det_size",
                    size=format_bytes(ci.size_bytes),
                    files=i18n.format_int(ci.file_count),
                ),
                tr("caches_item_det_desc", desc=ci.description),
                tr("caches_item_det_path", path=ci.path),
            ],
        )

    def _start_cleanup(self, use_recycle_bin: bool) -> None:
        checked = self._get_checked_items()
        if not checked:
            return

        total_bytes = sum(x.size_bytes for x in checked)
        mode_title = (
            tr("caches_confirm_recycle_title")
            if use_recycle_bin
            else tr("caches_confirm_perm_title")
        )
        mode_desc = (
            tr("caches_confirm_recycle_desc")
            if use_recycle_bin
            else tr("caches_confirm_perm_desc")
        )

        preview_lines = "\n".join(f"• {c.name} ({format_bytes(c.size_bytes)})" for c in checked[:6])
        if len(checked) > 6:
            preview_lines += "\n" + tr("caches_confirm_more", count=len(checked) - 6)

        confirmed = ask_yes_no(
            self,
            f"DevClean — {mode_title}",
            tr(
                "caches_confirm_body",
                desc=mode_desc,
                count=len(checked),
                size=format_bytes(total_bytes),
                preview=preview_lines,
            ),
        )
        if not confirmed:
            return

        self.btn_scan.setEnabled(False)
        self.btn_recycle.setEnabled(False)
        self.btn_delete_perm.setEnabled(False)
        self.progress_frame.setVisible(True)
        self.progress_bar.setRange(0, len(checked))
        self.progress_bar.setValue(0)

        self._clean_worker = CacheCleanWorker(checked, use_recycle_bin=use_recycle_bin, parent=self)
        self._clean_worker.progress_changed.connect(self._on_clean_progress)
        self._clean_worker.clean_completed.connect(self._on_clean_completed)
        self._clean_worker.start()

    def _on_clean_progress(self, current: int, total: int, msg: str) -> None:
        self.progress_bar.setRange(0, max(total, 1))
        self.progress_bar.setValue(current)
        self.lbl_progress.setText(msg)

    def _on_clean_completed(self, removed_count: int, freed_bytes: int, errors: list[str]) -> None:
        self.progress_frame.setVisible(False)
        self.btn_scan.setEnabled(True)
        self.disk_refresh_requested.emit()

        summary = tr("caches_done_summary", count=removed_count, size=format_bytes(freed_bytes))
        if errors:
            err_preview = "\n".join(errors[:5])
            if len(errors) > 5:
                err_preview += "\n" + tr("caches_done_more_err", count=len(errors) - 5)
            QMessageBox.warning(
                self,
                tr("caches_warn_title"),
                f"{summary}\n\n{tr('caches_done_skipped')}\n{err_preview}",
            )
        else:
            QMessageBox.information(self, tr("caches_done_title"), summary)

        self.start_scan()

    def _on_context_menu(self, pos) -> None:
        node = self.tree.itemAt(pos)
        if node is None:
            return
        self.tree.setCurrentItem(node)
        ci: Optional[CacheItem] = node.data(0, CACHE_DATA_ROLE)
        if ci is None:
            return

        menu = QMenu(self)
        act_open = QAction(Win7Icons.folder_win7(), tr("btn_open_location"), self)
        act_open.triggered.connect(lambda: open_in_explorer(ci.path))
        menu.addAction(act_open)
        menu.exec(self.tree.viewport().mapToGlobal(pos))

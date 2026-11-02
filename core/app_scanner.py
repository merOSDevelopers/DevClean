"""Yüklü uygulamaları Windows Kayıt Defteri üzerinden tarayan ve disk boyutlarını hesaplayan modül."""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys

from PyQt6.QtCore import QThread, pyqtSignal

from core.i18n import tr
from core.utils import calculate_dir_size, is_safe_dedicated_install_dir

if sys.platform == "win32":
    import winreg


@dataclass
class InstalledApp:
    """Kayıt defterinden okunan yüklü bir uygulamanın bilgilerini tutar."""

    key_id: str
    name: str
    raw_publisher: str
    version: str
    install_date: str
    install_location: str
    uninstall_string: str
    quiet_uninstall_string: str
    modify_path: str
    display_icon: str
    size_bytes: int
    size_is_calculated: bool
    scope_key: str  # "scope_sys64", "scope_sys32", "scope_user"
    is_msi: bool

    @property
    def publisher(self) -> str:
        return self.raw_publisher if self.raw_publisher else tr("unspecified")

    @property
    def scope(self) -> str:
        return tr(self.scope_key)


def _read_reg_value(key, value_name: str, default=None):
    try:
        val, _ = winreg.QueryValueEx(key, value_name)
        return val
    except OSError:
        return default


def _normalize_location(raw_loc: str) -> str:
    if not raw_loc:
        return ""
    cleaned = os.path.expandvars(str(raw_loc).strip().strip('"'))
    if not cleaned:
        return ""
    return os.path.normpath(cleaned)


def scan_registry_apps(include_system_components: bool = False) -> list[InstalledApp]:
    """Windows Uninstall kayıt defteri anahtarlarından tüm yüklü uygulamaları okur."""
    if sys.platform != "win32":
        return []

    uninstall_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    targets = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            uninstall_path,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            "scope_sys64",
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            uninstall_path,
            winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
            "scope_sys32",
        ),
        (
            winreg.HKEY_CURRENT_USER,
            uninstall_path,
            winreg.KEY_READ,
            "scope_user",
        ),
    ]

    seen_signatures: dict[str, InstalledApp] = {}

    for root_hive, sub_path, access_flags, scope_key in targets:
        try:
            parent_key = winreg.OpenKey(root_hive, sub_path, 0, access_flags)
        except OSError:
            continue

        try:
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(parent_key, index)
                    index += 1
                except OSError:
                    break

                try:
                    app_key = winreg.OpenKey(parent_key, subkey_name, 0, access_flags)
                except OSError:
                    continue

                try:
                    display_name = str(_read_reg_value(app_key, "DisplayName", "") or "").strip()
                    if not display_name:
                        continue

                    sys_comp = _read_reg_value(app_key, "SystemComponent", 0)
                    if not include_system_components and sys_comp == 1:
                        continue

                    release_type = str(_read_reg_value(app_key, "ReleaseType", "") or "").lower()
                    parent_display = str(_read_reg_value(app_key, "ParentDisplayName", "") or "").strip()
                    if not include_system_components and (
                        release_type in ("security update", "update", "hotfix") or parent_display
                    ):
                        continue

                    uninstall_str = str(_read_reg_value(app_key, "UninstallString", "") or "").strip()
                    quiet_uninstall = str(
                        _read_reg_value(app_key, "QuietUninstallString", "") or ""
                    ).strip()
                    modify_path = str(_read_reg_value(app_key, "ModifyPath", "") or "").strip()

                    if not uninstall_str and not quiet_uninstall and not modify_path:
                        continue

                    publisher = str(_read_reg_value(app_key, "Publisher", "") or "").strip()
                    version = str(_read_reg_value(app_key, "DisplayVersion", "") or "").strip()
                    install_date = str(_read_reg_value(app_key, "InstallDate", "") or "").strip()
                    install_loc = _normalize_location(
                        str(_read_reg_value(app_key, "InstallLocation", "") or "")
                    )
                    display_icon = str(_read_reg_value(app_key, "DisplayIcon", "") or "").strip()
                    win_installer = _read_reg_value(app_key, "WindowsInstaller", 0) == 1

                    est_kb = _read_reg_value(app_key, "EstimatedSize", 0)
                    try:
                        size_bytes = int(est_kb) * 1024 if est_kb and int(est_kb) > 0 else 0
                    except (ValueError, TypeError):
                        size_bytes = 0

                    if not install_loc and display_icon:
                        raw_ico = display_icon.split(",")[0].strip().strip('"')
                        ico_dir = os.path.dirname(os.path.expandvars(raw_ico))
                        if is_safe_dedicated_install_dir(ico_dir):
                            install_loc = os.path.normpath(ico_dir)

                    dedup_key = f"{display_name.lower()}|{version.lower()}|{install_loc.lower()}"
                    app_entry = InstalledApp(
                        key_id=f"{scope_key}:{subkey_name}",
                        name=display_name,
                        raw_publisher=publisher,
                        version=version or "—",
                        install_date=install_date,
                        install_location=install_loc,
                        uninstall_string=uninstall_str or quiet_uninstall,
                        quiet_uninstall_string=quiet_uninstall,
                        modify_path=modify_path,
                        display_icon=display_icon,
                        size_bytes=size_bytes,
                        size_is_calculated=False,
                        scope_key=scope_key,
                        is_msi=win_installer or ("msiexec" in uninstall_str.lower()),
                    )

                    existing = seen_signatures.get(dedup_key)
                    if existing is None or app_entry.size_bytes > existing.size_bytes:
                        seen_signatures[dedup_key] = app_entry
                finally:
                    winreg.CloseKey(app_key)
        finally:
            winreg.CloseKey(parent_key)

    apps = list(seen_signatures.values())
    apps.sort(key=lambda a: (a.size_bytes, a.name.lower()), reverse=True)
    return apps


class AppScanWorker(QThread):
    """
    Yüklü uygulamaları arka planda tarar ve boyutu kayıt defterinde eksik olan
    uygulamaların gerçek disk kullanımını hesaplar.
    """

    progress_changed = pyqtSignal(int, int, str)
    scan_completed = pyqtSignal(object)

    def __init__(
        self,
        calculate_missing_sizes: bool = True,
        include_system_components: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.calculate_missing_sizes = calculate_missing_sizes
        self.include_system_components = include_system_components
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        self.progress_changed.emit(0, 100, tr("apps_scanning_reg"))
        apps = scan_registry_apps(include_system_components=self.include_system_components)

        if self.calculate_missing_sizes and apps and not self._cancelled:
            dir_size_cache: dict[str, int] = {}
            candidates = [
                app
                for app in apps
                if app.size_bytes == 0 and is_safe_dedicated_install_dir(app.install_location)
            ]
            total = len(candidates)
            for idx, app in enumerate(candidates, start=1):
                if self._cancelled:
                    break
                self.progress_changed.emit(
                    idx,
                    max(total, 1),
                    tr("apps_calc_folder", name=app.name),
                )
                norm_dir = os.path.normcase(app.install_location)
                if norm_dir in dir_size_cache:
                    computed = dir_size_cache[norm_dir]
                else:
                    computed, _ = calculate_dir_size(
                        app.install_location,
                        cancel_check=self.is_cancelled,
                        max_files=80_000,
                    )
                    dir_size_cache[norm_dir] = computed

                if computed > 0:
                    app.size_bytes = computed
                    app.size_is_calculated = True

        apps.sort(key=lambda a: (a.size_bytes, a.name.lower()), reverse=True)
        self.scan_completed.emit(apps)

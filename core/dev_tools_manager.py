"""
Geliştirme araçlarını, programlama dillerini ve SDK paketlerini
(Visual Studio, VS SDKs, Python, PyCharm, Android Studio vb.) algılayan ve yöneten modül.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
import subprocess
import sys
from typing import Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.app_scanner import InstalledApp, scan_registry_apps
from core.i18n import tr
from core.utils import (
    calculate_dir_size,
    is_frozen_exe,
    is_protected_runtime_path,
    is_safe_dedicated_install_dir,
)

if sys.platform == "win32":
    import winreg


CAT_VS = "dcat_vs"
CAT_VS_SDKS = "dcat_vs_sdks"
CAT_PYTHON = "dcat_python"
CAT_PYCHARM = "dcat_pycharm"
CAT_ANDROID = "dcat_android"
CAT_OTHER = "dcat_other"

ORDERED_CATEGORIES = [
    CAT_VS,
    CAT_VS_SDKS,
    CAT_PYTHON,
    CAT_PYCHARM,
    CAT_ANDROID,
    CAT_OTHER,
]


@dataclass
class DevToolEntry:
    """Algılanan bir geliştirme ortamı, dil dağıtımı veya SDK bileşeni (çoklu dil destekli)."""

    category_id: str
    raw_name: str
    version: str
    kind_key: str
    raw_publisher: str
    location: str
    size_bytes: int
    uninstall_command: str
    modify_command: str
    display_icon: str
    can_delete_folder: bool
    name_key: str = ""
    name_kwargs: dict[str, Any] = field(default_factory=dict)
    pub_key: str = ""
    note_key: str = ""
    note_kwargs: dict[str, Any] = field(default_factory=dict)
    scope_key: str = ""
    is_active_runtime: bool = False

    @property
    def category(self) -> str:
        return tr(self.category_id)

    @property
    def name(self) -> str:
        if self.name_key:
            return tr(self.name_key, **self.name_kwargs)
        if self.scope_key and "{scope}" in self.raw_name:
            return self.raw_name.format(scope=tr(self.scope_key))
        return self.raw_name

    @property
    def kind(self) -> str:
        return tr(self.kind_key)

    @property
    def publisher(self) -> str:
        if self.pub_key:
            return tr(self.pub_key)
        return self.raw_publisher if self.raw_publisher else tr("unspecified")

    @property
    def notes(self) -> str:
        if self.note_key == "dnote_scope_prefix" and self.scope_key:
            return tr("dnote_scope_prefix", scope=tr(self.scope_key))
        if self.note_key:
            return tr(self.note_key, **self.note_kwargs)
        return ""


def _find_vs_installer() -> tuple[str, str]:
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    base = os.path.join(pf86, "Microsoft Visual Studio", "Installer")
    vs_inst = os.path.join(base, "vs_installer.exe")
    vswhere = os.path.join(base, "vswhere.exe")
    return (
        vs_inst if os.path.isfile(vs_inst) else "",
        vswhere if os.path.isfile(vswhere) else "",
    )


def _classify_registry_dev_app(app: InstalledApp) -> Optional[tuple[str, str]]:
    """
    Kayıt defterindeki bir uygulamanın geliştirici aracı kategorisini belirler.
    Dönüş: (category_id, kind_key) veya None
    """
    name_low = app.name.lower()
    pub_low = app.raw_publisher.lower()

    if "pycharm" in name_low:
        return CAT_PYCHARM, "dkind_ide"

    if "android studio" in name_low:
        return CAT_ANDROID, "dkind_ide"

    if (
        re.match(r"^python\s+\d", name_low)
        or name_low == "python launcher"
        or "python software foundation" in pub_low
        or "miniconda" in name_low
        or "anaconda" in name_low
    ):
        if "core interpreter" in name_low or "executables" in name_low or "standard library" in name_low:
            return None
        return CAT_PYTHON, "dkind_lang"

    if "visual studio" in name_low:
        if any(
            sdk_kw in name_low
            for sdk_kw in ("sdk", "targeting pack", "intellisense", "redistributable", "runtime")
        ):
            if "redistributable" in name_low:
                return None
            return CAT_VS_SDKS, "dkind_sdk"
        return CAT_VS, "dkind_ide_build"

    if (
        "windows software development kit" in name_low
        or "windows sdk" in name_low
        or "windows driver kit" in name_low
        or ("windows kits" in app.install_location.lower() if app.install_location else False)
        or re.search(r"\b\.net\s+sdk\b", name_low)
        or "microsoft .net sdk" in name_low
        or "targeting pack" in name_low
        or "msbuild" in name_low
    ):
        return CAT_VS_SDKS, "dkind_sdk"

    other_patterns = (
        ("adoptium", "dkind_jdk"),
        ("temurin", "dkind_jdk"),
        ("openjdk", "dkind_jdk"),
        ("java(tm) se development kit", "dkind_jdk"),
        ("jdk ", "dkind_jdk"),
        ("node.js", "dkind_lang"),
        ("golang", "dkind_lang"),
        ("go programming language", "dkind_lang"),
        ("rustup", "dkind_lang"),
        ("git", "dkind_vcs"),
        ("intellij idea", "dkind_ide"),
        ("clion", "dkind_ide"),
        ("webstorm", "dkind_ide"),
        ("goland", "dkind_ide"),
        ("rider", "dkind_ide"),
        ("cmake", "dkind_build"),
    )
    for pat, kind_key in other_patterns:
        if pat == "git":
            if name_low == "git" or name_low.startswith("git "):
                return CAT_OTHER, kind_key
        elif pat in name_low:
            return CAT_OTHER, kind_key

    return None


def _detect_vswhere_instances(cancel_check) -> list[DevToolEntry]:
    vs_installer, vswhere = _find_vs_installer()
    if not vswhere:
        return []

    entries: list[DevToolEntry] = []
    try:
        proc = subprocess.run(
            [vswhere, "-all", "-products", "*", "-format", "json", "-utf8"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return []
        data = json.loads(proc.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return []

    for inst in data:
        if cancel_check and cancel_check():
            break
        install_path = os.path.normpath(str(inst.get("installationPath", "") or ""))
        display_name = str(inst.get("displayName", "") or "Microsoft Visual Studio")
        version = str(inst.get("installationVersion", "") or "—")
        devenv = os.path.join(install_path, "Common7", "IDE", "devenv.exe")
        icon_path = devenv if os.path.isfile(devenv) else vs_installer

        uninstall_cmd = ""
        modify_cmd = ""
        if vs_installer and install_path:
            uninstall_cmd = f'"{vs_installer}" uninstall --installPath "{install_path}"'
            modify_cmd = f'"{vs_installer}" modify --installPath "{install_path}"'

        sz, _ = calculate_dir_size(install_path, cancel_check=cancel_check, max_files=120_000)
        entries.append(
            DevToolEntry(
                category_id=CAT_VS,
                raw_name=display_name,
                version=version,
                kind_key="dkind_ide",
                raw_publisher="Microsoft Corporation",
                location=install_path,
                size_bytes=sz,
                uninstall_command=uninstall_cmd,
                modify_command=modify_cmd,
                display_icon=icon_path,
                can_delete_folder=False,
                note_key="dnote_vswhere",
            )
        )
    return entries


def _detect_dotnet_and_windows_kits(seen_locations: set[str], cancel_check) -> list[DevToolEntry]:
    entries: list[DevToolEntry] = []

    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    dotnet_sdk_root = os.path.join(pf, "dotnet", "sdk")
    dotnet_exe = os.path.join(pf, "dotnet", "dotnet.exe")
    if os.path.isdir(dotnet_sdk_root):
        try:
            with os.scandir(dotnet_sdk_root) as it:
                for sub in it:
                    if cancel_check and cancel_check():
                        break
                    if not sub.is_dir() or not sub.name[0].isdigit():
                        continue
                    norm_loc = os.path.normcase(os.path.normpath(sub.path))
                    if norm_loc in seen_locations:
                        continue
                    sz, _ = calculate_dir_size(sub.path, cancel_check=cancel_check, max_files=40_000)
                    seen_locations.add(norm_loc)
                    entries.append(
                        DevToolEntry(
                            category_id=CAT_VS_SDKS,
                            raw_name=f".NET SDK {sub.name}",
                            version=sub.name,
                            kind_key="dkind_sdk_sub",
                            raw_publisher="Microsoft Corporation",
                            location=os.path.normpath(sub.path),
                            size_bytes=sz,
                            uninstall_command="",
                            modify_command="",
                            display_icon=dotnet_exe if os.path.isfile(dotnet_exe) else "",
                            can_delete_folder=False,
                            note_key="dnote_dotnet_sdk",
                        )
                    )
        except OSError:
            pass

    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    wk10 = os.path.join(pf86, "Windows Kits", "10")
    if os.path.isdir(wk10):
        inc_dir = os.path.join(wk10, "Include")
        if os.path.isdir(inc_dir):
            try:
                with os.scandir(inc_dir) as it:
                    for ver_entry in it:
                        if cancel_check and cancel_check():
                            break
                        if not ver_entry.is_dir() or not ver_entry.name[0].isdigit():
                            continue
                        ver = ver_entry.name
                        total_ver_sz = 0
                        for part in ("Include", "Lib", "bin"):
                            part_dir = os.path.join(wk10, part, ver)
                            if os.path.isdir(part_dir):
                                part_sz, _ = calculate_dir_size(
                                    part_dir, cancel_check=cancel_check, max_files=40_000
                                )
                                total_ver_sz += part_sz
                        norm_loc = os.path.normcase(os.path.normpath(ver_entry.path))
                        if norm_loc not in seen_locations and total_ver_sz > 0:
                            seen_locations.add(norm_loc)
                            entries.append(
                                DevToolEntry(
                                    category_id=CAT_VS_SDKS,
                                    raw_name="",
                                    name_key="dname_win_sdk_ver",
                                    name_kwargs={"ver": ver},
                                    version=ver,
                                    kind_key="dkind_sdk_sub",
                                    raw_publisher="Microsoft Corporation",
                                    location=os.path.normpath(wk10),
                                    size_bytes=total_ver_sz,
                                    uninstall_command="",
                                    modify_command="",
                                    display_icon="",
                                    can_delete_folder=False,
                                    note_key="dnote_win_sdk_ver",
                                    note_kwargs={"ver": ver},
                                )
                            )
            except OSError:
                pass
        else:
            norm_wk = os.path.normcase(os.path.normpath(wk10))
            if norm_wk not in seen_locations:
                sz, _ = calculate_dir_size(wk10, cancel_check=cancel_check, max_files=40_000)
                if sz > 0:
                    seen_locations.add(norm_wk)
                    entries.append(
                        DevToolEntry(
                            category_id=CAT_VS_SDKS,
                            raw_name="",
                            name_key="dname_win_kits10",
                            version="10",
                            kind_key="dkind_sdk",
                            raw_publisher="Microsoft Corporation",
                            location=os.path.normpath(wk10),
                            size_bytes=sz,
                            uninstall_command="",
                            modify_command="",
                            display_icon="",
                            can_delete_folder=False,
                            note_key="dnote_win_kits10",
                        )
                    )

    return entries


def _detect_python_installations(seen_locations: set[str], cancel_check) -> list[DevToolEntry]:
    entries: list[DevToolEntry] = []
    frozen = is_frozen_exe()

    if sys.platform == "win32":
        hives = [
            (winreg.HKEY_CURRENT_USER, r"Software\Python\PythonCore", winreg.KEY_READ, "scope_user"),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Python\PythonCore",
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
                "scope_sys64",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"Software\Python\PythonCore",
                winreg.KEY_READ | winreg.KEY_WOW64_32KEY,
                "scope_sys32",
            ),
        ]
        for hive, sub_path, flags, scope_key in hives:
            try:
                core_key = winreg.OpenKey(hive, sub_path, 0, flags)
            except OSError:
                continue
            try:
                idx = 0
                while True:
                    try:
                        tag = winreg.EnumKey(core_key, idx)
                        idx += 1
                    except OSError:
                        break
                    try:
                        ip_key = winreg.OpenKey(core_key, rf"{tag}\InstallPath", 0, flags)
                    except OSError:
                        continue
                    try:
                        install_dir, _ = winreg.QueryValueEx(ip_key, "")
                        exe_path = os.path.join(str(install_dir), "python.exe")
                        try:
                            exe_val, _ = winreg.QueryValueEx(ip_key, "ExecutablePath")
                            if exe_val:
                                exe_path = str(exe_val)
                        except OSError:
                            pass
                    except OSError:
                        install_dir = ""
                        exe_path = ""
                    finally:
                        winreg.CloseKey(ip_key)

                    if install_dir and os.path.isdir(str(install_dir)):
                        norm_dir = os.path.normpath(str(install_dir))
                        norm_key = os.path.normcase(norm_dir)
                        if norm_key not in seen_locations:
                            seen_locations.add(norm_key)
                            sz, _ = calculate_dir_size(norm_dir, cancel_check=cancel_check, max_files=60_000)
                            is_active = (not frozen) and is_protected_runtime_path(norm_dir)
                            entries.append(
                                DevToolEntry(
                                    category_id=CAT_PYTHON,
                                    raw_name=f"Python {tag} ({{scope}})",
                                    scope_key=scope_key,
                                    version=tag,
                                    kind_key="dkind_lang",
                                    raw_publisher="Python Software Foundation",
                                    location=norm_dir,
                                    size_bytes=sz,
                                    uninstall_command="",
                                    modify_command="",
                                    display_icon=exe_path if os.path.isfile(exe_path) else "",
                                    can_delete_folder=False,
                                    note_key="dnote_py_active" if is_active else "dnote_py_exe",
                                    note_kwargs={} if is_active else {"exe": exe_path},
                                    is_active_runtime=is_active,
                                )
                            )
            finally:
                winreg.CloseKey(core_key)

    local_app = os.environ.get("LOCALAPPDATA", "")
    pkgs_dir = os.path.join(local_app, "Packages") if local_app else ""
    if pkgs_dir and os.path.isdir(pkgs_dir):
        try:
            with os.scandir(pkgs_dir) as it:
                for entry in it:
                    if not entry.is_dir():
                        continue
                    if entry.name.startswith("PythonSoftwareFoundation.Python."):
                        norm_p = os.path.normpath(entry.path)
                        norm_key = os.path.normcase(norm_p)
                        if norm_key in seen_locations:
                            continue
                        seen_locations.add(norm_key)
                        ver_match = re.search(r"Python\.(\d+\.\d+)", entry.name)
                        ver_str = ver_match.group(1) if ver_match else "3.x"
                        sz, _ = calculate_dir_size(norm_p, cancel_check=cancel_check, max_files=60_000)
                        is_active = (not frozen) and (
                            is_protected_runtime_path(norm_p)
                            or ("WindowsApps\\PythonSoftwareFoundation.Python." + ver_str in sys.executable)
                        )
                        family_prefix = entry.name.split("_")[0]
                        ps_remove = (
                            f'powershell.exe -NoProfile -Command '
                            f'"Get-AppxPackage *{family_prefix}* | Remove-AppxPackage"'
                        )
                        entries.append(
                            DevToolEntry(
                                category_id=CAT_PYTHON,
                                raw_name="",
                                name_key="dname_py_store",
                                name_kwargs={"ver": ver_str},
                                version=ver_str,
                                kind_key="dkind_lang",
                                raw_publisher="Python Software Foundation",
                                location=norm_p,
                                size_bytes=sz,
                                uninstall_command="" if is_active else ps_remove,
                                modify_command="",
                                display_icon=sys.executable if (is_active and not frozen) else "",
                                can_delete_folder=False,
                                note_key="dnote_py_active" if is_active else "dnote_py_store",
                                is_active_runtime=is_active,
                            )
                        )
        except OSError:
            pass

    # Derlenmiş --onedir EXE çalışırken sys.base_prefix (_internal) Python kurulumu değildir!
    if not frozen:
        active_prefix = os.path.normpath(sys.base_prefix)
        if os.path.isdir(active_prefix) and os.path.normcase(active_prefix) not in seen_locations:
            has_active = any(e.is_active_runtime for e in entries)
            if not has_active:
                seen_locations.add(os.path.normcase(active_prefix))
                ver_str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                sz, _ = calculate_dir_size(active_prefix, cancel_check=cancel_check, max_files=50_000)
                entries.append(
                    DevToolEntry(
                        category_id=CAT_PYTHON,
                        raw_name="",
                        name_key="dname_py_active_interp",
                        name_kwargs={"ver": ver_str},
                        version=ver_str,
                        kind_key="dkind_lang",
                        raw_publisher="Python Software Foundation",
                        location=active_prefix,
                        size_bytes=sz,
                        uninstall_command="",
                        modify_command="",
                        display_icon=sys.executable,
                        can_delete_folder=False,
                        note_key="dnote_py_active",
                        is_active_runtime=True,
                    )
                )

    return entries


def _detect_pycharm_extras(seen_locations: set[str], cancel_check) -> list[DevToolEntry]:
    entries: list[DevToolEntry] = []
    home = os.path.expanduser("~")
    local_app = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    roaming_app = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))

    programs_dir = os.path.join(local_app, "Programs")
    if os.path.isdir(programs_dir):
        try:
            with os.scandir(programs_dir) as it:
                for entry in it:
                    if entry.is_dir() and "pycharm" in entry.name.lower():
                        norm_p = os.path.normpath(entry.path)
                        norm_key = os.path.normcase(norm_p)
                        if norm_key in seen_locations:
                            continue
                        seen_locations.add(norm_key)
                        exe_64 = os.path.join(norm_p, "bin", "pycharm64.exe")
                        unins = os.path.join(norm_p, "bin", "Uninstall.exe")
                        sz, _ = calculate_dir_size(norm_p, cancel_check=cancel_check, max_files=60_000)
                        entries.append(
                            DevToolEntry(
                                category_id=CAT_PYCHARM,
                                raw_name=entry.name,
                                version="—",
                                kind_key="dkind_ide",
                                raw_publisher="JetBrains s.r.o.",
                                location=norm_p,
                                size_bytes=sz,
                                uninstall_command=f'"{unins}"' if os.path.isfile(unins) else "",
                                modify_command="",
                                display_icon=exe_64 if os.path.isfile(exe_64) else "",
                                can_delete_folder=not os.path.isfile(unins),
                                note_key="dnote_pycharm_user",
                            )
                        )
        except OSError:
            pass

    for name_key, note_key, jb_root in (
        ("dname_pycharm_cache", "dnote_pycharm_cache", os.path.join(local_app, "JetBrains")),
        ("dname_pycharm_cfg", "dnote_pycharm_cfg", os.path.join(roaming_app, "JetBrains")),
    ):
        if not os.path.isdir(jb_root):
            continue
        try:
            with os.scandir(jb_root) as it:
                for entry in it:
                    if not entry.is_dir() or "pycharm" not in entry.name.lower():
                        continue
                    norm_p = os.path.normpath(entry.path)
                    norm_key = os.path.normcase(norm_p)
                    if norm_key in seen_locations:
                        continue
                    sz, _ = calculate_dir_size(norm_p, cancel_check=cancel_check, max_files=50_000)
                    if sz <= 0:
                        continue
                    seen_locations.add(norm_key)
                    ver_match = re.search(r"(\d{4}\.\d+)", entry.name)
                    ver_str = ver_match.group(1) if ver_match else "—"
                    entries.append(
                        DevToolEntry(
                            category_id=CAT_PYCHARM,
                            raw_name="",
                            name_key=name_key,
                            name_kwargs={"folder": entry.name},
                            version=ver_str,
                            kind_key="dkind_ide_data",
                            raw_publisher="JetBrains s.r.o.",
                            location=norm_p,
                            size_bytes=sz,
                            uninstall_command="",
                            modify_command="",
                            display_icon="",
                            can_delete_folder=True,
                            note_key=note_key,
                        )
                    )
        except OSError:
            pass

    return entries


def _detect_android_ecosystem(seen_locations: set[str], cancel_check) -> list[DevToolEntry]:
    entries: list[DevToolEntry] = []
    home = os.path.expanduser("~")
    local_app = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")

    for studio_dir in (
        os.path.join(pf, "Android", "Android Studio"),
        os.path.join(local_app, "Programs", "Android Studio"),
    ):
        if os.path.isdir(studio_dir):
            norm_s = os.path.normpath(studio_dir)
            norm_key = os.path.normcase(norm_s)
            if norm_key not in seen_locations:
                seen_locations.add(norm_key)
                exe_64 = os.path.join(norm_s, "bin", "studio64.exe")
                unins = os.path.join(norm_s, "uninstall.exe")
                sz, _ = calculate_dir_size(norm_s, cancel_check=cancel_check, max_files=70_000)
                entries.append(
                    DevToolEntry(
                        category_id=CAT_ANDROID,
                        raw_name="Android Studio",
                        version="—",
                        kind_key="dkind_ide",
                        raw_publisher="Google LLC",
                        location=norm_s,
                        size_bytes=sz,
                        uninstall_command=f'"{unins}"' if os.path.isfile(unins) else "",
                        modify_command="",
                        display_icon=exe_64 if os.path.isfile(exe_64) else "",
                        can_delete_folder=False,
                        note_key="dnote_android_studio",
                    )
                )

    sdk_candidates = [
        os.environ.get("ANDROID_HOME", ""),
        os.environ.get("ANDROID_SDK_ROOT", ""),
        os.path.join(local_app, "Android", "Sdk"),
    ]
    sdk_root = ""
    for cand in sdk_candidates:
        if cand and os.path.isdir(cand):
            sdk_root = os.path.normpath(cand)
            break

    if sdk_root:
        sub_specs = [
            ("system-images", "dname_android_sysimg"),
            ("ndk", "dname_android_ndk"),
            ("platforms", "dname_android_plat"),
            ("build-tools", "dname_android_bt"),
        ]
        for folder_name, name_key in sub_specs:
            sub_dir = os.path.join(sdk_root, folder_name)
            if not os.path.isdir(sub_dir):
                continue
            try:
                with os.scandir(sub_dir) as it:
                    for item in it:
                        if cancel_check and cancel_check():
                            break
                        if not item.is_dir():
                            continue
                        norm_item = os.path.normpath(item.path)
                        sz, _ = calculate_dir_size(norm_item, cancel_check=cancel_check, max_files=50_000)
                        if sz <= 0:
                            continue
                        seen_locations.add(os.path.normcase(norm_item))
                        entries.append(
                            DevToolEntry(
                                category_id=CAT_ANDROID,
                                raw_name="",
                                name_key=name_key,
                                name_kwargs={"ver": item.name},
                                version=item.name,
                                kind_key="dkind_sdk_sub",
                                raw_publisher="Google LLC",
                                location=norm_item,
                                size_bytes=sz,
                                uninstall_command="",
                                modify_command="",
                                display_icon="",
                                can_delete_folder=True,
                                note_key="dnote_android_sub",
                                note_kwargs={"folder": folder_name},
                            )
                        )
            except OSError:
                pass

        emu_dir = os.path.join(sdk_root, "emulator")
        if os.path.isdir(emu_dir):
            norm_emu = os.path.normpath(emu_dir)
            sz, _ = calculate_dir_size(norm_emu, cancel_check=cancel_check, max_files=30_000)
            if sz > 0:
                emu_exe = os.path.join(norm_emu, "emulator.exe")
                entries.append(
                    DevToolEntry(
                        category_id=CAT_ANDROID,
                        raw_name="",
                        name_key="dname_android_emu",
                        version="—",
                        kind_key="dkind_sdk_sub",
                        raw_publisher="Google LLC",
                        location=norm_emu,
                        size_bytes=sz,
                        uninstall_command="",
                        modify_command="",
                        display_icon=emu_exe if os.path.isfile(emu_exe) else "",
                        can_delete_folder=True,
                        note_key="dnote_android_emu",
                    )
                )

    avd_root = os.path.join(home, ".android", "avd")
    if os.path.isdir(avd_root):
        try:
            with os.scandir(avd_root) as it:
                for entry in it:
                    if entry.is_dir() and entry.name.lower().endswith(".avd"):
                        norm_avd = os.path.normpath(entry.path)
                        sz, _ = calculate_dir_size(norm_avd, cancel_check=cancel_check)
                        if sz > 0:
                            avd_title = entry.name[:-4]
                            entries.append(
                                DevToolEntry(
                                    category_id=CAT_ANDROID,
                                    raw_name="",
                                    name_key="dname_android_avd",
                                    name_kwargs={"name": avd_title},
                                    version="AVD",
                                    kind_key="dkind_avd",
                                    raw_publisher="",
                                    pub_key="dpub_user_avd",
                                    location=norm_avd,
                                    size_bytes=sz,
                                    uninstall_command="",
                                    modify_command="",
                                    display_icon="",
                                    can_delete_folder=True,
                                    note_key="dnote_android_avd",
                                )
                            )
        except OSError:
            pass

    return entries


def _detect_other_toolchains(seen_locations: set[str], cancel_check) -> list[DevToolEntry]:
    entries: list[DevToolEntry] = []
    home = os.path.expanduser("~")
    local_app = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))

    rustup_dir = os.path.join(home, ".rustup")
    cargo_bin_rustup = os.path.join(home, ".cargo", "bin", "rustup.exe")
    if os.path.isdir(rustup_dir):
        norm_r = os.path.normpath(rustup_dir)
        if os.path.normcase(norm_r) not in seen_locations:
            seen_locations.add(os.path.normcase(norm_r))
            sz, _ = calculate_dir_size(norm_r, cancel_check=cancel_check, max_files=60_000)
            if sz > 0:
                uninstall_cmd = f'"{cargo_bin_rustup}" self uninstall' if os.path.isfile(cargo_bin_rustup) else ""
                entries.append(
                    DevToolEntry(
                        category_id=CAT_OTHER,
                        raw_name="",
                        name_key="dname_rustup",
                        version="rustup",
                        kind_key="dkind_lang",
                        raw_publisher="The Rust Project Developers",
                        location=norm_r,
                        size_bytes=sz,
                        uninstall_command=uninstall_cmd,
                        modify_command="",
                        display_icon=cargo_bin_rustup if os.path.isfile(cargo_bin_rustup) else "",
                        can_delete_folder=not bool(uninstall_cmd),
                        note_key="dnote_rustup",
                    )
                )

    adoptium_dir = os.path.join(local_app, "Programs", "Eclipse Adoptium")
    if os.path.isdir(adoptium_dir):
        try:
            with os.scandir(adoptium_dir) as it:
                for sub in it:
                    if sub.is_dir():
                        norm_j = os.path.normpath(sub.path)
                        if os.path.normcase(norm_j) in seen_locations:
                            continue
                        seen_locations.add(os.path.normcase(norm_j))
                        java_exe = os.path.join(norm_j, "bin", "java.exe")
                        sz, _ = calculate_dir_size(norm_j, cancel_check=cancel_check, max_files=40_000)
                        entries.append(
                            DevToolEntry(
                                category_id=CAT_OTHER,
                                raw_name=f"Eclipse Adoptium JDK ({sub.name})",
                                version=sub.name,
                                kind_key="dkind_jdk",
                                raw_publisher="Eclipse Adoptium",
                                location=norm_j,
                                size_bytes=sz,
                                uninstall_command="",
                                modify_command="",
                                display_icon=java_exe if os.path.isfile(java_exe) else "",
                                can_delete_folder=False,
                                note_key="dnote_jdk",
                            )
                        )
        except OSError:
            pass

    return entries


class DevToolsScanWorker(QThread):
    """
    Visual Studio, VS SDKs, Python, PyCharm, Android Studio ve diğer kodlama dillerini
    arka planda tarayan iş parçacığı.
    """

    progress_changed = pyqtSignal(str)
    scan_completed = pyqtSignal(object)  # dict[str, list[DevToolEntry]]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        grouped: dict[str, list[DevToolEntry]] = {cat: [] for cat in ORDERED_CATEGORIES}
        seen_locations: set[str] = set()
        seen_names: set[str] = set()

        self.progress_changed.emit(tr("dev_scan_vs"))
        for entry in _detect_vswhere_instances(self.is_cancelled):
            grouped[entry.category_id].append(entry)
            if entry.location:
                seen_locations.add(os.path.normcase(entry.location))
            seen_names.add(f"{entry.category_id}|{entry.raw_name.lower()}")

        self.progress_changed.emit(tr("dev_scan_reg"))
        reg_apps = scan_registry_apps(include_system_components=True)
        vs_installer, _ = _find_vs_installer()
        frozen = is_frozen_exe()

        for app in reg_apps:
            if self._cancelled:
                break
            classified = _classify_registry_dev_app(app)
            if classified is None:
                continue
            category_id, kind_key = classified
            name_sig = f"{category_id}|{app.name.lower()}"
            if name_sig in seen_names:
                continue
            if app.install_location and os.path.normcase(app.install_location) in seen_locations:
                continue

            sz = app.size_bytes
            if sz == 0 and is_safe_dedicated_install_dir(app.install_location):
                self.progress_changed.emit(tr("caches_calc_size", path=app.name))
                sz, _ = calculate_dir_size(
                    app.install_location, cancel_check=self.is_cancelled, max_files=60_000
                )

            modify_cmd = app.modify_path
            if category_id == CAT_VS and not modify_cmd and vs_installer and "installer" not in app.name.lower():
                modify_cmd = f'"{vs_installer}"'

            is_active = bool(
                (not frozen) and app.install_location and is_protected_runtime_path(app.install_location)
            )
            seen_names.add(name_sig)
            if app.install_location:
                seen_locations.add(os.path.normcase(app.install_location))

            grouped[category_id].append(
                DevToolEntry(
                    category_id=category_id,
                    raw_name=app.name,
                    version=app.version,
                    kind_key=kind_key,
                    raw_publisher=app.raw_publisher,
                    location=app.install_location,
                    size_bytes=sz,
                    uninstall_command="" if is_active else app.uninstall_string,
                    modify_command=modify_cmd,
                    display_icon=app.display_icon,
                    can_delete_folder=False,
                    note_key="dnote_active_runtime" if is_active else "dnote_scope_prefix",
                    scope_key=app.scope_key,
                    is_active_runtime=is_active,
                )
            )

        if not self._cancelled:
            self.progress_changed.emit(tr("dev_scan_sdks"))
            grouped[CAT_VS_SDKS].extend(_detect_dotnet_and_windows_kits(seen_locations, self.is_cancelled))

        if not self._cancelled:
            self.progress_changed.emit(tr("dev_scan_python"))
            grouped[CAT_PYTHON].extend(_detect_python_installations(seen_locations, self.is_cancelled))

        if not self._cancelled:
            self.progress_changed.emit(tr("dev_scan_pycharm"))
            grouped[CAT_PYCHARM].extend(_detect_pycharm_extras(seen_locations, self.is_cancelled))

        if not self._cancelled:
            self.progress_changed.emit(tr("dev_scan_android"))
            grouped[CAT_ANDROID].extend(_detect_android_ecosystem(seen_locations, self.is_cancelled))

        if not self._cancelled:
            self.progress_changed.emit(tr("dev_scan_other"))
            grouped[CAT_OTHER].extend(_detect_other_toolchains(seen_locations, self.is_cancelled))

        for cat in grouped:
            grouped[cat].sort(key=lambda e: (e.size_bytes, e.name.lower()), reverse=True)

        self.scan_completed.emit(grouped)

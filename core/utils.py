"""Dosya boyutu hesaplama, biçimlendirme, kaynak yolu ve Windows kabuk yardımcı işlevleri."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import datetime
import os
import re
import shutil
import stat
import subprocess
import sys
from typing import Callable, Optional

from core.i18n import i18n, tr


FILE_ATTRIBUTE_REPARSE_POINT = 0x0400


def is_frozen_exe() -> bool:
    """Uygulamanın PyInstaller (--onedir / --onefile) ile derlenmiş EXE olup olmadığını döndürür."""
    return bool(getattr(sys, "frozen", False))


def get_app_base_dir() -> str:
    """Kaynak kodda proje kök dizinini, derlenmiş EXE'de yürütülebilir dosya dizinini döndürür."""
    if is_frozen_exe():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(relative_path: str) -> str:
    """
    Hem Python kaynak kodundan çalışırken hem de PyInstaller --onedir / --onefile
    derlemesinde varlık dosyalarının (örn. assets/devclean.ico) tam yolunu çözümler.
    """
    candidates: list[str] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, relative_path))
    if is_frozen_exe():
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, relative_path))
        candidates.append(os.path.join(exe_dir, "_internal", relative_path))
    src_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates.append(os.path.join(src_root, relative_path))

    for cand in candidates:
        if os.path.exists(cand):
            return cand
    return candidates[-1]


def format_bytes(num_bytes: int) -> str:
    """Bayt cinsinden boyutu etkin dile (Türkçe / İngilizce) uygun Windows biçimine dönüştürür."""
    if num_bytes < 0:
        return tr("unknown")
    if num_bytes == 0:
        return tr("unit_zero_bytes")
    units = [tr("unit_bytes"), "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    unit_idx = 0
    while value >= 1024.0 and unit_idx < len(units) - 1:
        value /= 1024.0
        unit_idx += 1
    if unit_idx == 0:
        return f"{int(value)} {units[unit_idx]}"
    formatted = f"{value:.2f}"
    if i18n.language == "tr":
        formatted = formatted.replace(".", ",")
    return f"{formatted} {units[unit_idx]}"


def format_install_date(raw_date: str) -> str:
    """YYYYMMDD biçimindeki kayıt defteri tarihini etkin dile uygun tarihe çevirir."""
    if not raw_date:
        return "—"
    cleaned = raw_date.strip()
    if len(cleaned) == 8 and cleaned.isdigit():
        try:
            dt = datetime.date(int(cleaned[:4]), int(cleaned[4:6]), int(cleaned[6:8]))
            if i18n.language == "en":
                return dt.strftime("%Y-%m-%d")
            return dt.strftime("%d.%m.%Y")
        except ValueError:
            pass
    return cleaned


def format_timestamp(ts: float) -> str:
    """Unix zaman damgasını okunabilir tarihe çevirir."""
    if ts <= 0:
        return "—"
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        if i18n.language == "en":
            return dt.strftime("%Y-%m-%d %H:%M")
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, OSError, OverflowError):
        return "—"


def is_reparse_point(entry: os.DirEntry) -> bool:
    """Sembolik bağlantı veya NTFS junction olup olmadığını denetler."""
    try:
        if entry.is_symlink():
            return True
        st = entry.stat(follow_symlinks=False)
        attrs = getattr(st, "st_file_attributes", 0)
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except OSError:
        return True


def calculate_dir_size(
    path: str,
    cancel_check: Optional[Callable[[], bool]] = None,
    max_files: int = 250_000,
) -> tuple[int, int]:
    """
    Bir dizinin toplam boyutunu ve dosya sayısını hesaplar.
    NTFS junction ve sembolik bağlantıları takip etmez (çift sayımı önler).
    Dönüş: (toplam_bayt, dosya_sayisi)
    """
    if not path or not os.path.exists(path):
        return 0, 0
    if os.path.isfile(path):
        try:
            return os.path.getsize(path), 1
        except OSError:
            return 0, 0

    total_bytes = 0
    file_count = 0
    stack = [path]

    while stack:
        if cancel_check and cancel_check():
            break
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if cancel_check and (file_count % 512 == 0) and cancel_check():
                        return total_bytes, file_count
                    if is_reparse_point(entry):
                        continue
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_bytes += entry.stat(follow_symlinks=False).st_size
                            file_count += 1
                            if file_count >= max_files:
                                return total_bytes, file_count
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                    except OSError:
                        continue
        except OSError:
            continue

    return total_bytes, file_count


def is_safe_dedicated_install_dir(path: str) -> bool:
    """
    InstallLocation değerinin paylaşılan üst sistem klasörü değil,
    uygulamaya ait özel bir dizin olup olmadığını doğrular.
    """
    if not path:
        return False
    norm = os.path.normcase(os.path.normpath(path.strip().strip('"')))
    if not os.path.isdir(norm):
        return False

    _drive, tail = os.path.splitdrive(norm)
    parts = [p for p in tail.split(os.sep) if p]
    if len(parts) < 2:
        return False

    forbidden_exact = set()
    for env_key in (
        "SystemRoot",
        "ProgramFiles",
        "ProgramFiles(x86)",
        "ProgramW6432",
        "CommonProgramFiles",
        "CommonProgramFiles(x86)",
        "USERPROFILE",
        "APPDATA",
        "LOCALAPPDATA",
    ):
        val = os.environ.get(env_key)
        if val:
            forbidden_exact.add(os.path.normcase(os.path.normpath(val)))
            forbidden_exact.add(os.path.normcase(os.path.normpath(os.path.join(val, "Programs"))))

    if norm in forbidden_exact:
        return False
    if norm.endswith(os.sep + "system32") or norm.endswith(os.sep + "syswow64"):
        return False
    return True


def open_in_explorer(path: str) -> bool:
    """Dosya veya klasörü Windows Gezgini içinde açar."""
    if not path:
        return False
    cleaned = os.path.normpath(path.strip().strip('"'))
    if not os.path.exists(cleaned):
        parent = os.path.dirname(cleaned)
        if parent and os.path.isdir(parent):
            cleaned = parent
        else:
            return False

    try:
        if os.path.isfile(cleaned):
            subprocess.Popen(["explorer.exe", f"/select,{cleaned}"])
        else:
            os.startfile(cleaned)  # type: ignore[attr-defined]
        return True
    except OSError:
        return False


def split_command_line(command: str) -> tuple[str, str]:
    """
    Windows kayıt defterindeki UninstallString komutunu (yürütülebilir_dosya, argümanlar)
    olarak güvenli biçimde ayırır. Tırnaksız boşluklu yolları destekler.
    """
    cmd = command.strip()
    if not cmd:
        return "", ""

    if cmd.startswith('"'):
        end_quote = cmd.find('"', 1)
        if end_quote != -1:
            exe = cmd[1:end_quote].strip()
            args = cmd[end_quote + 1 :].strip()
            return exe, args

    lower = cmd.lower()
    if lower.startswith("msiexec.exe ") or lower.startswith("msiexec "):
        first_space = cmd.find(" ")
        return cmd[:first_space], cmd[first_space + 1 :].strip()

    for match in re.finditer(r"\.exe\b", cmd, flags=re.IGNORECASE):
        candidate = cmd[: match.end()].strip()
        if os.path.isfile(candidate) or " " not in candidate:
            rest = cmd[match.end() :].strip()
            return candidate, rest

    parts = cmd.split(None, 1)
    exe = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    return exe, args


def launch_uninstaller(command: str, prefer_uninstall_for_msi: bool = True) -> tuple[bool, str]:
    """
    Kaldırma komutunu çalıştırır. Yönetici izni gerektiren (WinError 740)
    kaldırıcılar için Windows UAC (runas) istemini devreye sokar.
    """
    if not command or not command.strip():
        return False, tr("err_no_uninstall_cmd")

    cmd = command.strip()
    if prefer_uninstall_for_msi and "msiexec" in cmd.lower():
        if re.search(r"/i\s*\{", cmd, flags=re.IGNORECASE) and not re.search(
            r"/x\s*\{", cmd, flags=re.IGNORECASE
        ):
            cmd = re.sub(r"/i(\s*\{)", r"/X\1", cmd, count=1, flags=re.IGNORECASE)

    exe, args = split_command_line(cmd)
    if not exe:
        return False, tr("err_invalid_uninstaller")

    cwd = os.path.dirname(exe) if os.path.isabs(exe) and os.path.isdir(os.path.dirname(exe)) else None

    try:
        subprocess.Popen(cmd, cwd=cwd, shell=False)
        return True, tr("msg_uninstaller_started")
    except OSError as exc:
        winerr = getattr(exc, "winerror", None)
        if winerr == 740 or sys.platform == "win32":
            return _shell_execute_elevated(exe, args, cwd)
        return False, tr("err_uninstaller_failed", error=str(exc))


def _shell_execute_elevated(exe: str, args: str, cwd: Optional[str]) -> tuple[bool, str]:
    """ShellExecuteW ile UAC yükseltmeli işlem başlatır."""
    if sys.platform != "win32":
        return False, tr("err_elevated_win_only")

    shell32 = ctypes.windll.shell32
    shell32.ShellExecuteW.argtypes = [
        wintypes.HWND,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        ctypes.c_int,
    ]
    shell32.ShellExecuteW.restype = ctypes.c_void_p

    for verb in ("open", "runas"):
        result = shell32.ShellExecuteW(None, verb, exe, args or None, cwd, 1)
        if result is not None and int(result) > 32:
            return True, tr("msg_uninstaller_started")
        if verb == "open":
            continue

    return False, tr("err_uac_cancelled")


if ctypes.sizeof(ctypes.c_void_p) == 4:
    class _SHFILEOPSTRUCTW(ctypes.Structure):
        _pack_ = 1
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", ctypes.c_void_p),
            ("pTo", ctypes.c_void_p),
            ("fFlags", wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]
else:
    class _SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", ctypes.c_void_p),
            ("pTo", ctypes.c_void_p),
            ("fFlags", wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR),
        ]


def send_to_recycle_bin(path: str) -> tuple[bool, str]:
    """Dosya veya dizini Windows Geri Dönüşüm Kutusu'na taşır."""
    norm = os.path.abspath(os.path.normpath(path))
    if not os.path.exists(norm):
        return False, tr("err_path_missing")
    if is_protected_runtime_path(norm):
        return False, tr("err_protected_runtime")

    if sys.platform != "win32":
        return delete_permanently(norm)

    FO_DELETE = 0x0003
    FOF_SILENT = 0x0004
    FOF_NOCONFIRMATION = 0x0010
    FOF_ALLOWUNDO = 0x0040
    FOF_NOERRORUI = 0x0400

    buf = ctypes.create_unicode_buffer(norm + "\0\0")
    op = _SHFILEOPSTRUCTW()
    op.hwnd = None
    op.wFunc = FO_DELETE
    op.pFrom = ctypes.cast(buf, ctypes.c_void_p)
    op.pTo = None
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_NOERRORUI | FOF_SILENT
    op.fAnyOperationsAborted = False
    op.hNameMappings = None
    op.lpszProgressTitle = None

    shell32 = ctypes.windll.shell32
    shell32.SHFileOperationW.argtypes = [ctypes.POINTER(_SHFILEOPSTRUCTW)]
    shell32.SHFileOperationW.restype = ctypes.c_int

    rc = shell32.SHFileOperationW(ctypes.byref(op))
    if rc == 0 and not op.fAnyOperationsAborted:
        return True, tr("msg_moved_to_recycle")
    return False, tr("err_recycle_failed", code=rc)


def _handle_remove_readonly(func, path, _exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        raise


def delete_permanently(path: str) -> tuple[bool, str]:
    """Dosya veya dizini diskten kalıcı olarak siler."""
    norm = os.path.abspath(os.path.normpath(path))
    if not os.path.exists(norm):
        return False, tr("err_path_missing")
    if is_protected_runtime_path(norm):
        return False, tr("err_protected_runtime")

    try:
        if os.path.isfile(norm) or os.path.islink(norm):
            os.chmod(norm, stat.S_IWRITE)
            os.remove(norm)
        else:
            if sys.version_info >= (3, 12):
                shutil.rmtree(norm, onexc=lambda f, p, e: _handle_remove_readonly(f, p, e))
            else:
                shutil.rmtree(norm, onerror=_handle_remove_readonly)
        return True, tr("msg_deleted_perm")
    except OSError as exc:
        return False, tr("err_delete_failed", error=str(exc))


def is_protected_runtime_path(target_path: str) -> bool:
    """DevClean'in çalıştığı aktif yorumlayıcı veya derlenmiş --onedir dizininin silinmesini engeller."""
    norm_target = os.path.normcase(os.path.abspath(target_path))
    protected_dirs = [
        sys.prefix,
        sys.base_prefix,
        get_app_base_dir(),
        getattr(sys, "_MEIPASS", ""),
    ]
    if sys.executable:
        protected_dirs.append(os.path.dirname(os.path.abspath(sys.executable)))

    for runtime_dir in protected_dirs:
        if not runtime_dir:
            continue
        norm_runtime = os.path.normcase(os.path.abspath(runtime_dir))
        if norm_runtime == norm_target or norm_runtime.startswith(norm_target + os.sep):
            return True
    return False


def get_fixed_drives() -> list[tuple[str, int, int, int]]:
    """
    Sistemdeki sabit sürücüleri ve disk kullanım bilgilerini döndürür.
    Dönüş: [(sürücü_kökü, toplam_bayt, kullanılan_bayt, boş_bayt), ...]
    """
    drives: list[tuple[str, int, int, int]] = []
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        bitmask = kernel32.GetLogicalDrives()
        for idx in range(26):
            if bitmask & (1 << idx):
                letter = f"{chr(65 + idx)}:\\"
                dtype = kernel32.GetDriveTypeW(ctypes.c_wchar_p(letter))
                if dtype == 3:
                    try:
                        usage = shutil.disk_usage(letter)
                        drives.append((letter, usage.total, usage.used, usage.free))
                    except OSError:
                        continue
    if not drives:
        root = os.path.abspath(os.sep)
        try:
            usage = shutil.disk_usage(root)
            drives.append((root, usage.total, usage.used, usage.free))
        except OSError:
            pass
    return drives

"""Windows kayıt defteri DisplayIcon ve yürütülebilir dosyalarından yerel simge çıkarma modülü."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import sys
from typing import Optional

from PyQt6.QtCore import QFileInfo
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QFileIconProvider


class _ICONINFO(ctypes.Structure):
    _fields_ = [
        ("fIcon", wintypes.BOOL),
        ("xHotspot", wintypes.DWORD),
        ("yHotspot", wintypes.DWORD),
        ("hbmMask", wintypes.HBITMAP),
        ("hbmColor", wintypes.HBITMAP),
    ]


class _BITMAP(ctypes.Structure):
    _fields_ = [
        ("bmType", wintypes.LONG),
        ("bmWidth", wintypes.LONG),
        ("bmHeight", wintypes.LONG),
        ("bmWidthBytes", wintypes.LONG),
        ("bmPlanes", wintypes.WORD),
        ("bmBitsPixel", wintypes.WORD),
        ("bmBits", ctypes.c_void_p),
    ]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


_icon_cache: dict[str, QIcon] = {}
_provider: Optional[QFileIconProvider] = None


def _get_provider() -> QFileIconProvider:
    global _provider
    if _provider is None:
        _provider = QFileIconProvider()
    return _provider


def parse_display_icon(raw_icon: str) -> tuple[str, int]:
    """
    Kayıt defterindeki DisplayIcon değerini (dosya_yolu, simge_indeksi) olarak ayrıştırır.
    Örn: '"C:\\Program Files\\App\\app.exe",0' -> ('C:\\Program Files\\App\\app.exe', 0)
    """
    if not raw_icon:
        return "", 0
    text = raw_icon.strip()
    idx = 0

    if "," in text:
        left, right = text.rsplit(",", 1)
        right_clean = right.strip().strip('"')
        if right_clean.lstrip("-").isdigit():
            idx = int(right_clean)
            text = left.strip()

    text = os.path.expandvars(text.strip().strip('"'))
    # Bazı kayıtlar "app.exe /icon" şeklinde argüman içerebilir
    if not os.path.exists(text) and ".exe" in text.lower():
        pos = text.lower().find(".exe") + 4
        candidate = text[:pos].strip().strip('"')
        if os.path.exists(candidate):
            text = candidate

    return text, idx


def _hicon_to_qpixmap(hicon: int) -> Optional[QPixmap]:
    """Win32 HICON tutamacını 32-bit alfa kanallı QPixmap nesnesine dönüştürür."""
    if sys.platform != "win32" or not hicon:
        return None

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(_ICONINFO)]
    user32.GetIconInfo.restype = wintypes.BOOL
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteObject.restype = wintypes.BOOL
    gdi32.GetObjectW.argtypes = [wintypes.HGDIOBJ, ctypes.c_int, ctypes.c_void_p]
    gdi32.GetObjectW.restype = ctypes.c_int
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.DeleteDC.argtypes = [wintypes.HDC]
    gdi32.DeleteDC.restype = wintypes.BOOL
    gdi32.GetDIBits.argtypes = [
        wintypes.HDC,
        wintypes.HBITMAP,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.c_void_p,
        ctypes.POINTER(_BITMAPINFOHEADER),
        wintypes.UINT,
    ]
    gdi32.GetDIBits.restype = ctypes.c_int

    info = _ICONINFO()
    if not user32.GetIconInfo(wintypes.HICON(hicon), ctypes.byref(info)):
        return None

    try:
        hbm = info.hbmColor or info.hbmMask
        if not hbm:
            return None

        bmp = _BITMAP()
        if gdi32.GetObjectW(hbm, ctypes.sizeof(_BITMAP), ctypes.byref(bmp)) == 0:
            return None

        width = bmp.bmWidth
        height = bmp.bmHeight if info.hbmColor else bmp.bmHeight // 2
        if width <= 0 or height <= 0 or width > 256 or height > 256:
            return None

        bmi = _BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        bmi.biWidth = width
        bmi.biHeight = -height  # Üstten alta tarama (top-down DIB)
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0  # BI_RGB

        buf_size = width * height * 4
        buf = (ctypes.c_ubyte * buf_size)()

        hdc = gdi32.CreateCompatibleDC(None)
        if not hdc:
            return None
        try:
            lines = gdi32.GetDIBits(hdc, hbm, 0, height, buf, ctypes.byref(bmi), 0)
            if lines == 0:
                return None
        finally:
            gdi32.DeleteDC(hdc)

        raw_bytes = bytes(buf)
        # Bazı eski 24-bit simgelerde alfa kanalı tamamen 0 gelir; opaklığa yükselt
        has_alpha = any(raw_bytes[i] != 0 for i in range(3, len(raw_bytes), 4))
        if not has_alpha:
            arr = bytearray(raw_bytes)
            for i in range(0, len(arr), 4):
                if arr[i] or arr[i + 1] or arr[i + 2]:
                    arr[i + 3] = 255
            raw_bytes = bytes(arr)

        qimg = QImage(raw_bytes, width, height, width * 4, QImage.Format.Format_ARGB32).copy()
        return QPixmap.fromImage(qimg)
    finally:
        if info.hbmColor:
            gdi32.DeleteObject(info.hbmColor)
        if info.hbmMask:
            gdi32.DeleteObject(info.hbmMask)


def extract_dll_or_exe_icon(file_path: str, icon_index: int = 0) -> Optional[QIcon]:
    """Win32 ExtractIconExW kullanarak EXE/DLL/ICO içinden hem 16x16 hem 32x32 simge çıkarır."""
    if sys.platform != "win32" or not file_path or not os.path.exists(file_path):
        return None

    shell32 = ctypes.windll.shell32
    user32 = ctypes.windll.user32
    shell32.ExtractIconExW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_int,
        ctypes.POINTER(wintypes.HICON),
        ctypes.POINTER(wintypes.HICON),
        wintypes.UINT,
    ]
    shell32.ExtractIconExW.restype = wintypes.UINT
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.DestroyIcon.restype = wintypes.BOOL

    h_large = wintypes.HICON()
    h_small = wintypes.HICON()

    count = shell32.ExtractIconExW(file_path, icon_index, ctypes.byref(h_large), ctypes.byref(h_small), 1)
    if count == 0 and not h_large.value and not h_small.value:
        return None

    icon = QIcon()
    added = False
    try:
        if h_large.value:
            pix_l = _hicon_to_qpixmap(h_large.value)
            if pix_l and not pix_l.isNull():
                icon.addPixmap(pix_l)
                added = True
        if h_small.value:
            pix_s = _hicon_to_qpixmap(h_small.value)
            if pix_s and not pix_s.isNull():
                icon.addPixmap(pix_s)
                added = True
    finally:
        if h_large.value:
            user32.DestroyIcon(h_large)
        if h_small.value:
            user32.DestroyIcon(h_small)

    return icon if added else None


def find_primary_exe_in_dir(install_location: str) -> str:
    """DisplayIcon eksik olduğunda kurulum dizinindeki birincil .exe dosyasını bulur."""
    if not install_location or not os.path.isdir(install_location):
        return ""
    skip_prefixes = ("unins", "uninst", "crash", "update", "helper", "vc_redist", "setup")
    best_exe = ""
    best_size = -1
    try:
        with os.scandir(install_location) as it:
            for entry in it:
                if not entry.is_file():
                    continue
                low = entry.name.lower()
                if not low.endswith(".exe"):
                    continue
                if any(low.startswith(pref) for pref in skip_prefixes):
                    continue
                try:
                    sz = entry.stat().st_size
                except OSError:
                    sz = 0
                if sz > best_size:
                    best_size = sz
                    best_exe = entry.path
    except OSError:
        return ""
    return best_exe


def resolve_app_icon(
    display_icon: str,
    install_location: str,
    fallback_icon: QIcon,
) -> QIcon:
    """
    Yüklü bir uygulama için yerel Windows simgesini çözümler ve önbelleğe alır.
    Bulunamazsa veya genel msiexec simgesiyse sağlanan Windows 7 yedek simgesini döndürür.
    """
    cache_key = f"{display_icon}|{install_location}".lower()
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    path, idx = parse_display_icon(display_icon)

    # msiexec.exe genel simgesi yerine kurulum klasöründe gerçek uygulama EXE'si varsa onu tercih et
    if (not path or not os.path.exists(path) or path.lower().endswith("msiexec.exe")) and install_location:
        alt_exe = find_primary_exe_in_dir(install_location)
        if alt_exe:
            path, idx = alt_exe, 0

    if path and os.path.exists(path):
        low = path.lower()
        if low.endswith(".ico"):
            ico = QIcon(path)
            if not ico.isNull():
                _icon_cache[cache_key] = ico
                return ico

        extracted = extract_dll_or_exe_icon(path, idx)
        if extracted and not extracted.isNull():
            _icon_cache[cache_key] = extracted
            return extracted

        if idx == 0:
            prov_icon = _get_provider().icon(QFileInfo(path))
            if not prov_icon.isNull():
                _icon_cache[cache_key] = prov_icon
                return prov_icon

    _icon_cache[cache_key] = fallback_icon
    return fallback_icon

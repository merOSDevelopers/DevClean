"""DevClean — Geliştirici Disk Temizleme ve Uygulama Yönetimi başlangıç noktası."""

from __future__ import annotations

import ctypes
import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QStyleFactory

from ui.main_window import DevCleanMainWindow
from ui.win7_icons import Win7Icons


def _set_windows_app_id() -> None:
    """Windows görev çubuğunda DevClean simgesinin bağımsız görünmesini sağlar."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DevClean.DesktopUtility.1.1")
        except (AttributeError, OSError):
            pass


def main() -> int:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("DevClean")
    app.setApplicationVersion("1.1.0")

    available_styles = {s.lower(): s for s in QStyleFactory.keys()}
    if "windowsvista" in available_styles:
        app.setStyle(available_styles["windowsvista"])
    elif "windows" in available_styles:
        app.setStyle(available_styles["windows"])

    app.setFont(QFont("Segoe UI", 9))
    app.setWindowIcon(Win7Icons.app_icon())

    window = DevCleanMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

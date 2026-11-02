# DevClean

**DevClean** is a desktop disk cleanup, installed application, and developer environment management utility for Windows built with Python and PyQt6.

## Features

### 1. Installed Application Management
- Scans installed applications across Windows Registry hives (`HKLM` 64-bit, `HKLM` 32-bit, and `HKCU`).
- Calculates actual installation directory sizes on disk when size metadata is missing from the Registry.
- Sorts applications by disk space consumption and provides size threshold filtering (`100 MB`, `500 MB`, `1 GB`, `5 GB`) along with keyword search.
- Launches official application uninstallers and setup modification tools with Windows UAC elevation support when required.

### 2. Temporary Developer Files and Cache Cleanup
- Detects global package and build caches:
  - NuGet (`.nuget\packages`, HTTP v3 cache, temporary scratch folders)
  - Shared `.cache` directory (`~\.cache`)
  - Python package managers (`pip`, `uv`, `poetry`)
  - Node.js package managers (`npm`, `yarn`, `pnpm`)
  - Gradle and Maven (`~\.gradle\caches`, `~\.gradle\daemon`, `~\.m2\repository`)
  - Rust Cargo (`~\.cargo\registry\cache`) and Go (`go-build`)
  - Visual Studio and JetBrains temporary caches and log directories
- Scans configurable project workspace directories for recreatable artifacts:
  - Verified Python virtual environments (`.venv`, `venv`)
  - Python bytecode and tool caches (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.tox`)
  - Project-local `.cache`, `.nuget`, `.vs`, `.gradle`, and `node_modules` directories
  - Verified build output folders (`target` for Rust/Maven, `obj` for .NET/C++)
- Supports moving selected directories to the **Windows Recycle Bin** or **permanently deleting** them from disk.

### 3. Development Tools, Languages, and SDK Management
- **Visual Studio**: Detects installed editions via `vswhere.exe` and the Registry, with direct integration for modifying workloads or uninstalling through Visual Studio Installer.
- **VS SDKs**: Lists installed Windows 10/11 SDKs (`Windows Kits`) and `.NET SDK` versions with per-version disk usage.
- **Python**: Detects PEP 514 Registry installations and Microsoft Store distributions while protecting the active runtime environment from accidental removal.
- **PyCharm**: Lists IDE installations alongside remaining `JetBrains\PyCharm*` cache and configuration folders from current or previous versions.
- **Android Studio & Android SDK**: Detects Android Studio installations and breaks down individual `Android SDK` components (`system-images`, `ndk`, `platforms`, `build-tools`, `emulator`) and Android Virtual Devices (`AVD`) so unused SDK versions and emulator images can be removed selectively.
- **Additional Toolchains**: Detects installed JDK distributions, Rust toolchains (`.rustup`), Node.js, Go, and Git installations.

### 4. Multi-Language Support
- Supports **English** and **Turkish** with instant runtime switching from the sidebar or menu bar without restarting the application.

## Requirements

- Windows (64-bit)
- Python 3.10+
- `PyQt6 >= 6.6.0`

## Running from Source

```powershell
pip install -r requirements.txt
python main.py
```

## Building Executable (`--onedir`)

To compile a standalone directory distribution using PyInstaller:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean DevClean.spec
```

The compiled executable will be generated at `dist\DevClean\DevClean.exe`.

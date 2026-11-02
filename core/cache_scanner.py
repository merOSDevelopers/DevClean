"""Geçici geliştirici dosyalarını (.venv, .cache, .nuget vb.) tarayan ve temizleyen modül."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from core.i18n import tr
from core.utils import (
    calculate_dir_size,
    delete_permanently,
    is_protected_runtime_path,
    is_reparse_point,
    send_to_recycle_bin,
)


@dataclass
class CacheItem:
    """Bulunan geçici geliştirici klasörü veya önbellek öğesi (çoklu dil destekli)."""

    category_key: str
    group_key: str
    raw_name: str
    name_key: str
    name_kwargs: dict[str, Any] = field(default_factory=dict)
    path: str = ""
    project_name: str = ""
    size_bytes: int = 0
    file_count: int = 0
    last_modified: float = 0.0
    desc_key: str = ""
    desc_kwargs: dict[str, Any] = field(default_factory=dict)
    default_checked: bool = True

    @property
    def category(self) -> str:
        return tr(self.category_key)

    @property
    def group(self) -> str:
        return tr(self.group_key)

    @property
    def name(self) -> str:
        if self.name_key:
            return tr(self.name_key, **self.name_kwargs)
        return self.raw_name

    @property
    def description(self) -> str:
        if self.desc_key:
            return tr(self.desc_key, **self.desc_kwargs)
        return ""


def get_default_workspace_roots() -> list[str]:
    """Kullanıcının bilgisayarında mevcut olan yaygın proje dizinlerini döndürür."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "source", "repos"),
        os.path.join(home, "Projects"),
        os.path.join(home, "PycharmProjects"),
        os.path.join(home, "IdeaProjects"),
        os.path.join(home, "AndroidStudioProjects"),
        os.path.join(home, "dev"),
        os.path.join(home, "workspace"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Desktop"),
        os.path.join(home, ".gemini", "antigravity", "scratch"),
    ]
    roots: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        norm = os.path.normpath(path)
        key = os.path.normcase(norm)
        if os.path.isdir(norm) and key not in seen:
            seen.add(key)
            roots.append(norm)
    return roots


def _get_global_cache_definitions() -> list[tuple[str, str, dict[str, Any], str, str, dict[str, Any], bool]]:
    """
    Sistem genelindeki standart geliştirici önbellek konumları.
    Biçim: (cat_key, name_key, name_kwargs, tam_yol, desc_key, desc_kwargs, varsayılan_seçili)
    """
    home = os.path.expanduser("~")
    local_app = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    roaming_app = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))

    defs: list[tuple[str, str, dict[str, Any], str, str, dict[str, Any], bool]] = [
        ("ccat_nuget", "cname_nuget_pkgs", {}, os.path.join(home, ".nuget", "packages"), "cdesc_nuget_pkgs", {}, True),
        ("ccat_nuget", "cname_nuget_v3", {}, os.path.join(local_app, "NuGet", "v3-cache"), "cdesc_nuget_v3", {}, True),
        ("ccat_nuget", "cname_nuget_scratch", {}, os.path.join(local_app, "Temp", "NuGetScratch"), "cdesc_nuget_scratch", {}, True),
        ("ccat_cache", "cname_user_cache", {}, os.path.join(home, ".cache"), "cdesc_user_cache", {}, True),
        ("ccat_py_cache", "cname_pip_cache", {}, os.path.join(local_app, "pip", "Cache"), "cdesc_pip_cache", {}, True),
        ("ccat_py_cache", "cname_uv_cache", {}, os.path.join(local_app, "uv", "cache"), "cdesc_uv_cache", {}, True),
        ("ccat_py_cache", "cname_poetry_cache", {}, os.path.join(local_app, "pypoetry", "Cache"), "cdesc_poetry_cache", {}, True),
        ("ccat_node_cache", "cname_npm_local", {}, os.path.join(local_app, "npm-cache"), "cdesc_npm_local", {}, True),
        ("ccat_node_cache", "cname_npm_roaming", {}, os.path.join(roaming_app, "npm-cache"), "cdesc_npm_roaming", {}, True),
        ("ccat_node_cache", "cname_yarn_cache", {}, os.path.join(local_app, "Yarn", "Cache"), "cdesc_yarn_cache", {}, True),
        ("ccat_node_cache", "cname_pnpm_cache", {}, os.path.join(local_app, "pnpm-cache"), "cdesc_pnpm_cache", {}, True),
        ("ccat_gradle", "cname_gradle_caches", {}, os.path.join(home, ".gradle", "caches"), "cdesc_gradle_caches", {}, True),
        ("ccat_gradle", "cname_gradle_daemon", {}, os.path.join(home, ".gradle", "daemon"), "cdesc_gradle_daemon", {}, True),
        ("ccat_gradle", "cname_maven_repo", {}, os.path.join(home, ".m2", "repository"), "cdesc_maven_repo", {}, False),
        ("ccat_rust_go", "cname_cargo_cache", {}, os.path.join(home, ".cargo", "registry", "cache"), "cdesc_cargo_cache", {}, True),
        ("ccat_rust_go", "cname_go_build", {}, os.path.join(local_app, "go-build"), "cdesc_go_build", {}, True),
        ("ccat_ide", "cname_vs_pkgs", {}, os.path.join(local_app, "Microsoft", "VisualStudio", "Packages"), "cdesc_vs_pkgs", {}, False),
    ]

    jb_local = os.path.join(local_app, "JetBrains")
    if os.path.isdir(jb_local):
        try:
            with os.scandir(jb_local) as it:
                for entry in it:
                    if entry.is_dir():
                        caches_sub = os.path.join(entry.path, "caches")
                        log_sub = os.path.join(entry.path, "log")
                        kw = {"ide": entry.name}
                        if os.path.isdir(caches_sub):
                            defs.append(("ccat_ide", "cname_jb_caches", kw, caches_sub, "cdesc_jb_caches", kw, False))
                        if os.path.isdir(log_sub):
                            defs.append(("ccat_ide", "cname_jb_logs", kw, log_sub, "cdesc_jb_logs", kw, True))
        except OSError:
            pass

    return defs


def _is_verified_python_venv(dir_path: str) -> bool:
    if os.path.isfile(os.path.join(dir_path, "pyvenv.cfg")):
        return True
    if os.path.isfile(os.path.join(dir_path, "Scripts", "python.exe")):
        return True
    if os.path.isfile(os.path.join(dir_path, "bin", "python")):
        return True
    return False


def _parent_has_file_ext(parent_dir: str, extensions: tuple[str, ...], exact_names: tuple[str, ...] = ()) -> bool:
    try:
        for name in exact_names:
            if os.path.isfile(os.path.join(parent_dir, name)):
                return True
        if extensions:
            with os.scandir(parent_dir) as it:
                for entry in it:
                    if entry.is_file() and entry.name.lower().endswith(extensions):
                        return True
    except OSError:
        return False
    return False


def _classify_workspace_dir(
    entry_name: str, full_path: str, parent_dir: str
) -> Optional[tuple[str, str, dict[str, Any], bool]]:
    """
    Proje dizinindeki bir alt klasörün geçici geliştirici klasörü olup olmadığını belirler.
    Dönüş: (cat_key, desc_key, desc_kwargs, varsayılan_seçili) veya None
    """
    low = entry_name.lower()

    if low in (".venv", "venv", ".virtualenv", "env"):
        if _is_verified_python_venv(full_path):
            return ("ccat_py_venv", "cdesc_ws_venv", {}, low == ".venv")
        return None

    if low == ".cache":
        return ("ccat_cache", "cdesc_ws_cache", {}, True)

    if low == ".nuget":
        return ("ccat_nuget", "cdesc_ws_nuget", {}, True)

    if low in ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox"):
        return ("ccat_py_cache", "cdesc_ws_pycache", {"folder": entry_name}, True)

    if low == "node_modules":
        return ("ccat_node_modules", "cdesc_ws_nodemod", {}, False)

    if low == ".vs":
        return ("ccat_ide", "cdesc_ws_vs", {}, True)

    if low == ".gradle":
        return ("ccat_gradle", "cdesc_ws_gradle", {}, True)

    if low == "target":
        if _parent_has_file_ext(parent_dir, (), ("Cargo.toml", "pom.xml")):
            return ("ccat_build_out", "cdesc_ws_target", {}, False)
        return None

    if low == "obj":
        if _parent_has_file_ext(parent_dir, (".csproj", ".fsproj", ".vbproj", ".vcxproj")):
            return ("ccat_build_out", "cdesc_ws_obj", {}, True)
        return None

    return None


class CacheScanWorker(QThread):
    """Genel geliştirici önbelleklerini ve çalışma alanı proje klasörlerini arka planda tarar."""

    progress_changed = pyqtSignal(str)
    item_discovered = pyqtSignal(object)
    scan_completed = pyqtSignal(object)

    SKIP_DIRS = {
        ".git",
        ".svn",
        ".hg",
        "$recycle.bin",
        "system volume information",
        "windows",
        "appdata",
    }

    def __init__(
        self,
        workspace_roots: list[str],
        include_global_caches: bool = True,
        max_depth: int = 6,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.workspace_roots = workspace_roots
        self.include_global_caches = include_global_caches
        self.max_depth = max_depth
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def is_cancelled(self) -> bool:
        return self._cancelled

    def run(self) -> None:
        results: list[CacheItem] = []
        seen_paths: set[str] = set()

        if self.include_global_caches:
            for cat_key, name_key, name_kw, full_path, desc_key, desc_kw, def_checked in _get_global_cache_definitions():
                if self._cancelled:
                    break
                norm = os.path.normpath(full_path)
                norm_key = os.path.normcase(norm)
                if norm_key in seen_paths or not os.path.exists(norm):
                    continue
                if is_protected_runtime_path(norm):
                    continue

                label_now = tr(name_key, **name_kw)
                self.progress_changed.emit(tr("caches_scan_global", name=label_now))
                size_bytes, file_count = calculate_dir_size(norm, cancel_check=self.is_cancelled)
                if size_bytes <= 0:
                    continue

                try:
                    mtime = os.path.getmtime(norm)
                except OSError:
                    mtime = 0.0

                seen_paths.add(norm_key)
                item = CacheItem(
                    category_key=cat_key,
                    group_key="caches_group_global",
                    raw_name="",
                    name_key=name_key,
                    name_kwargs=name_kw,
                    path=norm,
                    project_name="System",
                    size_bytes=size_bytes,
                    file_count=file_count,
                    last_modified=mtime,
                    desc_key=desc_key,
                    desc_kwargs=desc_kw,
                    default_checked=def_checked,
                )
                results.append(item)
                self.item_discovered.emit(item)

        for root in self.workspace_roots:
            if self._cancelled:
                break
            norm_root = os.path.normpath(root)
            if not os.path.isdir(norm_root):
                continue
            self._scan_workspace_tree(norm_root, seen_paths, results)

        results.sort(key=lambda x: x.size_bytes, reverse=True)
        self.scan_completed.emit(results)

    def _scan_workspace_tree(
        self,
        root_dir: str,
        seen_paths: set[str],
        results: list[CacheItem],
    ) -> None:
        stack: list[tuple[str, int]] = [(root_dir, 0)]

        while stack and not self._cancelled:
            current_dir, depth = stack.pop()
            if depth > self.max_depth:
                continue

            self.progress_changed.emit(tr("caches_scan_dir", path=current_dir))
            try:
                with os.scandir(current_dir) as it:
                    entries = list(it)
            except OSError:
                continue

            for entry in entries:
                if self._cancelled:
                    return
                if is_reparse_point(entry):
                    continue
                try:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                except OSError:
                    continue

                low_name = entry.name.lower()
                if low_name in self.SKIP_DIRS:
                    continue

                full_path = os.path.normpath(entry.path)
                norm_key = os.path.normcase(full_path)
                if norm_key in seen_paths or is_protected_runtime_path(full_path):
                    continue

                match = _classify_workspace_dir(entry.name, full_path, current_dir)
                if match is not None:
                    cat_key, desc_key, desc_kw, def_checked = match
                    self.progress_changed.emit(tr("caches_calc_size", path=full_path))
                    size_bytes, file_count = calculate_dir_size(
                        full_path, cancel_check=self.is_cancelled
                    )
                    seen_paths.add(norm_key)
                    if size_bytes > 0:
                        try:
                            mtime = entry.stat(follow_symlinks=False).st_mtime
                        except OSError:
                            mtime = 0.0
                        project_name = os.path.basename(current_dir) or current_dir
                        item = CacheItem(
                            category_key=cat_key,
                            group_key="caches_group_project",
                            raw_name=f"{project_name} \\ {entry.name}",
                            name_key="",
                            path=full_path,
                            project_name=project_name,
                            size_bytes=size_bytes,
                            file_count=file_count,
                            last_modified=mtime,
                            desc_key=desc_key,
                            desc_kwargs=desc_kw,
                            default_checked=def_checked,
                        )
                        results.append(item)
                        self.item_discovered.emit(item)
                    continue

                if depth + 1 <= self.max_depth:
                    stack.append((full_path, depth + 1))


class CacheCleanWorker(QThread):
    """Seçilen geçici geliştirici klasörlerini arka planda temizler."""

    progress_changed = pyqtSignal(int, int, str)
    clean_completed = pyqtSignal(int, int, object)

    def __init__(self, items: list[CacheItem], use_recycle_bin: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.items = items
        self.use_recycle_bin = use_recycle_bin
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        removed_count = 0
        freed_bytes = 0
        errors: list[str] = []
        total = len(self.items)

        for idx, item in enumerate(self.items, start=1):
            if self._cancelled:
                break
            self.progress_changed.emit(idx, total, tr("caches_cleaning_item", path=item.path))
            if self.use_recycle_bin:
                ok, msg = send_to_recycle_bin(item.path)
            else:
                ok, msg = delete_permanently(item.path)

            if ok:
                removed_count += 1
                freed_bytes += item.size_bytes
            else:
                errors.append(f"{item.name}: {msg}")

        self.clean_completed.emit(removed_count, freed_bytes, errors)

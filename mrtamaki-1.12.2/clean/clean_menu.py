#!/usr/bin/env python3
"""Interactive system cleaner menu with two-column layout and enhanced features."""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Set

import readchar
import psutil
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box

from mrtamaki.ui_components import ui, set_theme, get_theme_names, get_theme

format_bytes = ui.format_bytes
from duplicate_finder import find_duplicates

# Commands list
COMMANDS = [
    ("pycache",  "Pycache",      "Find and delete all __pycache__ directories"),
    ("browser",  "Browser",      "Clear browser caches (Safari, Chrome, Firefox)"),
    ("appcache", "App Cache",    "Clear application cache directories"),
    ("xcode",    "Xcode",        "Clear Xcode DerivedData"),
    ("nodemod",  "node_modules", "Find and delete node_modules directories"),
    ("venvs",    "Venvs",        "Browse and delete virtual environments"),
    ("dupes",    "Duplicates",   "Find duplicate files (SHA256)"),
    ("trash",    "Trash",        "Show trash size and empty"),
    ("sizes",    "Sizes",        "View all reclaimable space overview"),
    ("return",   "Exit",         "Return to shell"),
]

ICONS = ["\uf0e8", "\uf0ac", "\uf187", "\uf013", "\ue718", "\uf423", "\uf0c5", "\uf1f8", "\uf200", "\uf2f5"]


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_dir_size(path: Path) -> int:
    """Calculate total size of directory."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError):
        pass
    return total


def find_pycache_dirs(max_depth: int = 6) -> List[Path]:
    """Find __pycache__ dirs in common dev locations with depth limit."""
    pycache_dirs = []
    home = Path.home()
    search_paths = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Projects",
    ]

    def _search(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in path.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name in ("node_modules", "Library", ".Trash", ".git"):
                    continue
                if entry.name == "__pycache__":
                    pycache_dirs.append(entry)
                else:
                    _search(entry, depth + 1)
        except (OSError, PermissionError):
            pass

    for sp in search_paths:
        if sp.exists():
            _search(sp, 0)
    return pycache_dirs


def find_venvs(search_paths: Optional[List[Path]] = None, max_depth: int = 5) -> List[Tuple[Path, int]]:
    """Find virtual environments with sizes."""
    venvs = []
 
    if search_paths is None:
        search_paths = [
            Path.home() / "Desktop",
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Projects",
        ]
        mrtamaki_dir_str = os.environ.get("MRTAMAKI_DIR")
        if mrtamaki_dir_str:
            mrtamaki_dir = Path(mrtamaki_dir_str)
            if mrtamaki_dir.is_dir():
                search_paths.append(mrtamaki_dir)
 
    def search_dir(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in path.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name.startswith(".") and entry.name != ".venv":
                    continue
                # Updated check to include venv-* for mrtamaki's own venvs
                if entry.name in ("venv", ".venv", "env", "pyenv") or entry.name.startswith("venv-"):
                    if (entry / "bin" / "activate").exists() and (entry / "bin" / "python").exists():
                        size = get_dir_size(entry)
                        venvs.append((entry, size))
                        continue  # Don't search inside a found venv
                if entry.name not in ("node_modules", "Library", ".Trash", ".git"):
                    search_dir(entry, depth + 1)
        except (OSError, PermissionError):
            pass
 
    for sp in search_paths:
        if sp.is_dir():
            search_dir(sp, 0)
 
    # Remove duplicates
    return list(dict.fromkeys(venvs))
 
 
def get_browser_cache_paths() -> dict:
    """Get browser cache directory paths."""
    home = Path.home()
    return {
        "Safari": home / "Library" / "Caches" / "com.apple.Safari",
        "Chrome": home / "Library" / "Caches" / "Google" / "Chrome",
        "Firefox": home / "Library" / "Caches" / "Firefox",
    }
 
 
def get_xcode_derived_data_path() -> Path:
    """Get path to Xcode DerivedData directory."""
    return Path.home() / "Library" / "Developer" / "Xcode" / "DerivedData"
 
 
def get_trash_path() -> Path:
    """Get path to user Trash directory."""
    return Path.home() / ".Trash"
 
 
def get_trash_size() -> int:
    """Calculate total size of Trash directory."""
    trash_path = get_trash_path()
    if not trash_path.exists():
        return 0
    return get_dir_size(trash_path)
 
 
def find_node_modules(max_depth: int = 5) -> List[Tuple[Path, int]]:
    """Find node_modules directories with sizes."""
    results = []
    home = Path.home()
    search_paths = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Projects",
    ]
 
    def _search(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in path.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name in ("Library", ".Trash", ".git", "__pycache__"):
                    continue
                if entry.name.startswith(".") and entry.name != ".venv":
                    continue
                if entry.name == "node_modules":
                    size = get_dir_size(entry)
                    results.append((entry, size))
                else:
                    _search(entry, depth + 1)
        except (OSError, PermissionError):
            pass
 
    for sp in search_paths:
        if sp.exists():
            _search(sp, 0)
    return results
 
 
def get_system_context() -> dict:
    """Get system status context info."""
    disk = psutil.disk_usage(str(Path.home()))
 
    # Count pycache dirs
    pycache_count = len(find_pycache_dirs())
 
    # Browser cache info
    browser_caches = get_browser_cache_paths()
    browser_found = []
    for name, cache_path in browser_caches.items():
        if cache_path.exists():
            browser_found.append(name)
 
    # Xcode DerivedData
    xcode_path = get_xcode_derived_data_path()
    xcode_exists = xcode_path.exists()
 
    # Trash size
    trash_size = get_trash_size()
 
    return {
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": disk.percent,
        "pycache_count": pycache_count,
        "browser_found": browser_found,
        "xcode_exists": xcode_exists,
        "trash_size": trash_size,
    }
 
 
def build_sizes_overview() -> Text:
    """Build reclaimable space overview."""
    theme = get_theme()
    content = Text()
 
    content.append("Reclaimable Space Overview\n\n", style=f"bold {theme['accent']}")
 
    # __pycache__
    pycache_dirs = find_pycache_dirs()
    pycache_size = sum(get_dir_size(d) for d in pycache_dirs)
    content.append("  __pycache__\n", style=f"bold {theme['highlight']}")
    content.append(f"    {len(pycache_dirs)} dirs, {format_bytes(pycache_size)}\n\n", style=theme["muted"])
 
    # Browser caches
    browser_caches = get_browser_cache_paths()
    browser_total = 0
    has_browser = False
    for name, cache_path in browser_caches.items():
        if cache_path.exists():
            has_browser = True
            size = get_dir_size(cache_path)
            browser_total += size
            content.append(f"  {name}\n", style=f"bold {theme['highlight']}")
            content.append(f"    {format_bytes(size)}\n", style=theme["muted"])
    if not has_browser:
        content.append("  Browser Caches\n", style=f"bold {theme['highlight']}")
        content.append("    (none found)\n", style=theme["muted"])
    content.append("\n")
 
    # Xcode DerivedData
    xcode_path = get_xcode_derived_data_path()
    xcode_size = 0
    if xcode_path.exists():
        xcode_size = get_dir_size(xcode_path)
        content.append("  Xcode DerivedData\n", style=f"bold {theme['highlight']}")
        content.append(f"    {format_bytes(xcode_size)}\n\n", style=theme["muted"])
    else:
        content.append("  Xcode DerivedData\n", style=f"bold {theme['highlight']}")
        content.append("    (not found)\n\n", style=theme["muted"])
 
    # node_modules
    node_dirs = find_node_modules(max_depth=3)
    node_size = sum(s for _, s in node_dirs)
    content.append("  node_modules\n", style=f"bold {theme['highlight']}")
    content.append(f"    {len(node_dirs)} dirs, {format_bytes(node_size)}\n\n", style=theme["muted"])
 
    # Virtual Envs
    venvs = find_venvs()
    venv_size = sum(s for _, s in venvs)
    content.append("  Virtual Envs\n", style=f"bold {theme['highlight']}")
    content.append(f"    {len(venvs)} venvs, {format_bytes(venv_size)}\n\n", style=theme["muted"])
 
    # Trash
    trash_size = get_trash_size()
    content.append("  Trash\n", style=f"bold {theme['highlight']}")
    content.append(f"    {format_bytes(trash_size)}\n\n", style=theme["muted"])
 
    total = pycache_size + browser_total + xcode_size + node_size + venv_size + trash_size
    content.append(f"  Total Reclaimable: {format_bytes(total)}\n", style=f"bold {theme['success']}")
 
    return content
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Menu class
# ─────────────────────────────────────────────────────────────────────────────
 
class CleanMenu:
    """Interactive system cleaner menu with two-column layout."""
 
    def __init__(self, console: Console):
        self.console = console
        self.selected = 0
        self.total = len(COMMANDS)
        self.context = get_system_context()
        self.mode = "main"  # main, venvs, sizes, dupes
        self.venv_selected = 0
        self.venvs: List[Tuple[Path, int]] = []
        self.sizes_content: Optional[Text] = None
        # Duplicate detection state
        self.dupes: List[Tuple[str, int, List[Path]]] = []
        self.dupe_group_idx = 0
        self.dupe_marks: Dict[int, Set[int]] = {}
        self.dupe_file_idx = 0
        self.dupe_scanning = False
 
    def render_header(self) -> Panel:
        """Render system context header."""
        theme = ui.theme
        format_bytes_func = ui.format_bytes
        ctx = self.context

        header = Text()
        header.append("\uf0e2  ", style=theme["accent"])
        header.append(" System Cleaner\n", style=f"bold {theme['accent']}")
        header.append(f"   {ctx['pycache_count']} pycache  ", style=theme["muted"])
        header.append(f" {len(ctx['browser_found'])} browsers  ", style=theme["muted"])
        header.append(f" \uf1f8 {format_bytes_func(ctx['trash_size'])} trash  ", style=theme["muted"])

        # Disk usage with color
        pct = ctx["disk_percent"]
        if pct > 90:
            pct_style = theme["error"]
        elif pct > 70:
            pct_style = theme["warning"]
        else:
            pct_style = theme["success"]
        header.append(f" {pct:.0f}% used", style=pct_style)
        header.append(f" ({format_bytes_func(ctx['disk_free'])} free)", style=theme["muted"])

        return Panel(
            header,
            border_style=theme["border"],
            padding=(0, 1),
            height=3,
        )
 
    def render_commands(self) -> Panel:
        """Render command list (left column)."""
        theme = get_theme()
        lines = Text()
 
        for idx, (cmd, name, _) in enumerate(COMMANDS):
            icon = ICONS[idx] if idx < len(ICONS) else ""
 
            if idx == self.selected and self.mode == "main":
                lines.append(" > ", style=f"bold {theme['accent']}")
                lines.append(f"{icon} ", style=f"bold {theme['accent']}")
                lines.append(f"{cmd:<8}", style=f"bold {theme['highlight']}")
                lines.append(f" {name}\n", style="bold white")
            else:
                lines.append("   ", style="")
                lines.append(f"{icon} ", style=theme["muted"])
                lines.append(f"{cmd:<8}", style=f"dim {theme['highlight']}")
                lines.append(f" {name}\n", style="dim white")
 
        return Panel(
            lines,
            title="[bold]Commands[/]",
            title_align="left",
            border_style=theme["accent"] if self.mode == "main" else theme["muted"],
            padding=(0, 1),
        )
 
    def render_info_panel(self) -> Panel:
        """Render info panel (right column) - context sensitive."""
        theme = get_theme()
 
        if self.mode == "sizes":
            if self.sizes_content is None:
                self.sizes_content = build_sizes_overview()
            content = self.sizes_content
            title = "Reclaimable Space"
        elif self.mode == "venvs":
            content = self.render_venvs_list()
            title = "Virtual Environments"
        elif self.mode == "dupes":
            content = self.render_dupes_list()
            title = "Duplicate Finder"
        else:
            content = self.render_default_info()
            title = "Info"
 
        return Panel(
            content,
            title=f"[bold]{title}[/]",
            title_align="left",
            border_style=theme["accent"] if self.mode != "main" else theme["border"],
            padding=(0, 1),
        )
 
    def render_default_info(self) -> Text:
        """Render default info panel content."""
        theme = get_theme()
        info = Text()
 
        # Command description
        desc = COMMANDS[self.selected][2]
        info.append(f"{desc}\n\n", style="italic")
 
        # Disk Usage
        info.append("Disk Usage\n", style=f"bold {theme['accent']}")
        ctx = self.context
        info.append(f"  Total: {format_bytes(ctx['disk_total'])}\n", style=theme["muted"])
        info.append(f"  Used:  {format_bytes(ctx['disk_used'])}\n", style=theme["muted"])
        info.append(f"  Free:  {format_bytes(ctx['disk_free'])}\n", style=theme["muted"])
 
        info.append("\n")
 
        # Browsers detected
        info.append("Browsers Detected\n", style=f"bold {theme['accent']}")
        if ctx["browser_found"]:
            for b in ctx["browser_found"]:
                info.append(f"  {b}\n", style=theme["muted"])
        else:
            info.append("  (none)\n", style=theme["muted"])
 
        info.append("\n")
 
        # Xcode status
        info.append("Xcode DerivedData\n", style=f"bold {theme['accent']}")
        if ctx["xcode_exists"]:
            info.append("  Found\n", style=theme["muted"])
        else:
            info.append("  (not found)\n", style=theme["muted"])
 
        return info
 
    def render_venvs_list(self) -> Text:
        """Render venvs for selection."""
        theme = get_theme()
        content = Text()
 
        if not self.venvs:
            content.append("No virtual environments found.\n\n", style=theme["muted"])
            content.append("Searched common locations and ", style=theme["muted"])
            content.append("$MRTAMAKI_DIR\n", style=theme["highlight"])
            return content
 
        for idx, (venv_path, size) in enumerate(self.venvs):
            # Shorten display path
            display = str(venv_path)
            home_str = str(Path.home())
            if display.startswith(home_str):
                display = "~" + display[len(home_str):]
            if len(display) > 35:
                display = "..." + display[-32:]
 
            if idx == self.venv_selected:
                content.append(" > ", style=f"bold {theme['accent']}")
                content.append(f"{display}\n", style="bold white")
                # Show size for selected
                content.append(f"   {format_bytes(size)}\n", style=theme["muted"])
            else:
                content.append(f"   {display}\n", style="dim white")
 
        total = sum(s for _, s in self.venvs)
        content.append(f"\n{len(self.venvs)} venvs, {format_bytes(total)} total", style=theme["muted"])
        content.append("\nEnter to go, x to delete, Esc to back", style=theme["muted"])
        return content
 
    def render_dupes_list(self) -> Text:
        """Render duplicate files for selection."""
        theme = get_theme()
        content = Text()
 
        if self.dupe_scanning:
            content.append("Scanning for duplicates...\n\n", style=f"bold {theme['accent']}")
            content.append("Checking ~/Desktop, ~/Documents, ~/Downloads\n", style=theme["muted"])
            content.append("Pass 1: grouping by size\n", style=theme["muted"])
            content.append("Pass 2: SHA256 hashing matches\n\n", style=theme["muted"])
            content.append("This may take a moment.", style=theme["muted"])
            return content
 
        if not self.dupes:
            content.append("No duplicate files found.\n\n", style=theme["muted"])
            content.append("Scanned ~/Desktop, ~/Documents, ~/Downloads\n", style=theme["muted"])
            content.append("(files >= 1 KB, SHA256 comparison)\n", style=theme["muted"])
            return content
 
        group_hash, group_size, group_paths = self.dupes[self.dupe_group_idx]
        wasted = group_size * (len(group_paths) - 1)
        marks = self.dupe_marks.get(self.dupe_group_idx, set())
 
        content.append(f"Group {self.dupe_group_idx + 1}/{len(self.dupes)}\n", style=f"bold {theme['accent']}")
        content.append(f"Size: {format_bytes(group_size)} each, ", style=theme["muted"])
        content.append(f"Wasted: {format_bytes(wasted)}\n\n", style=theme["warning"])
 
        for idx, filepath in enumerate(group_paths):
            display = str(filepath)
            home_str = str(Path.home())
            if display.startswith(home_str):
                display = "~" + display[len(home_str):]
            if len(display) > 40:
                display = "..." + display[-37:]
 
            is_marked = idx in marks
            is_selected = idx == self.dupe_file_idx
 
            if is_selected:
                marker = "[X]" if is_marked else "[ ]"
                content.append(f" > {marker} ", style=f"bold {theme['accent']}")
                content.append(f"{display}\n", style="bold white")
            else:
                marker = "[X]" if is_marked else "[ ]"
                style = theme["error"] if is_marked else "dim white"
                content.append(f"   {marker} {display}\n", style=style)
 
        total_wasted = sum(s * (len(p) - 1) for _, s, p in self.dupes)
        total_marked = sum(
            len(m) * self.dupes[gi][1]
            for gi, m in self.dupe_marks.items()
            if gi < len(self.dupes)
        )
        content.append(f"\nTotal wasted: {format_bytes(total_wasted)}", style=theme["muted"])
        content.append(f"\nMarked for deletion: {format_bytes(total_marked)}", style=theme["muted"])
        content.append("\nEnter=toggle  \u2190\u2192=groups  x=delete  Esc=back", style=theme["muted"])
        return content
 
    def render_footer(self) -> Panel:
        """Render controls footer."""
        theme = get_theme()
        controls = Text()
 
        if self.mode == "main":
            controls.append("  \u2191\u2193", style=f"bold {theme['accent']}")
            controls.append(" navigate  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("s", style=f"bold {theme['accent']}")
            controls.append(" sizes  ", style=theme["muted"])
            controls.append("v", style=f"bold {theme['accent']}")
            controls.append(" venvs  ", style=theme["muted"])
            controls.append("d", style=f"bold {theme['accent']}")
            controls.append(" dupes  ", style=theme["muted"])
            controls.append("q", style=f"bold {theme['accent']}")
            controls.append(" quit", style=theme["muted"])
        elif self.mode == "sizes":
            controls.append("  Esc", style=f"bold {theme['accent']}")
            controls.append(" back to menu", style=theme["muted"])
        elif self.mode == "venvs":
            controls.append("  \u2191\u2193", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" go  ", style=theme["muted"])
            controls.append("x", style=f"bold {theme['accent']}")
            controls.append(" delete  ", style=theme["muted"])
            controls.append("Esc", style=f"bold {theme['accent']}")
            controls.append(" back", style=theme["muted"])
        elif self.mode == "dupes":
            controls.append("  \u2191\u2193", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("\u2190\u2192", style=f"bold {theme['accent']}")
            controls.append(" groups  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" toggle  ", style=theme["muted"])
            controls.append("x", style=f"bold {theme['accent']}")
            controls.append(" delete  ", style=theme["muted"])
            controls.append("Esc", style=f"bold {theme['accent']}")
            controls.append(" back", style=theme["muted"])
 
        return Panel(controls, border_style=theme["border"], padding=(0, 0), height=3)
 
    def render(self) -> Layout:
        """Render the full two-column layout."""
        layout = Layout()
 
        # Main structure
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )
 
        # Body split into two columns
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )
 
        # Render components
        layout["header"].update(self.render_header())
        layout["left"].update(self.render_commands())
        layout["right"].update(self.render_info_panel())
        layout["footer"].update(self.render_footer())
 
        return layout
 
    def handle_main_input(self, key: str) -> Optional[str]:
        """Handle input in main mode."""
        if key in (readchar.key.UP, "k"):
            self.selected = (self.selected - 1) % self.total
        elif key in (readchar.key.DOWN, "j"):
            self.selected = (self.selected + 1) % self.total
        elif key in (readchar.key.ENTER, "\r"):
            cmd = COMMANDS[self.selected][0]
            if cmd == "return":
                return "__EXIT__"
            elif cmd == "sizes":
                self.sizes_content = None
                self.mode = "sizes"
            elif cmd == "venvs":
                self.venvs = find_venvs()
                self.venv_selected = 0
                self.mode = "venvs"
            elif cmd == "dupes":
                self.dupe_scanning = True
                self.mode = "dupes"
            else:
                # pycache, browser, appcache, xcode, nodemod, trash
                return cmd
        elif key == "s":
            self.sizes_content = None
            self.mode = "sizes"
        elif key == "v":
            self.venvs = find_venvs()
            self.venv_selected = 0
            self.mode = "venvs"
        elif key == "d":
            self.dupe_scanning = True
            self.mode = "dupes"
        elif key in ("q", readchar.key.ESC):
            return "__EXIT__"
        return None

    def handle_sizes_input(self, key: str) -> Optional[str]:
        """Handle input in sizes mode."""
        if key in (readchar.key.ESC, "q", readchar.key.ENTER):
            self.mode = "main"
        return None

    def handle_venvs_input(self, key: str) -> Optional[str]:
        """Handle input in venvs mode."""
        if key in (readchar.key.UP, "k"):
            if self.venvs:
                self.venv_selected = (self.venv_selected - 1) % len(self.venvs)
        elif key in (readchar.key.DOWN, "j"):
            if self.venvs:
                self.venv_selected = (self.venv_selected + 1) % len(self.venvs)
        elif key in (readchar.key.ENTER, "\r"):
            if self.venvs:
                venv_path = self.venvs[self.venv_selected][0]
                return f"__VENV_CD__:{venv_path.parent}"
        elif key == "x":
            # Delete venv
            if self.venvs:
                venv_path, _ = self.venvs[self.venv_selected]
                return f"__DELETE_VENV__:{venv_path}"
        elif key in (readchar.key.ESC, "q"):
            self.mode = "main"
        return None

    def handle_dupes_input(self, key: str) -> Optional[str]:
        """Handle input in dupes mode."""
        if not self.dupes:
            if key in (readchar.key.ESC, "q"):
                self.mode = "main"
            return None

        group_paths = self.dupes[self.dupe_group_idx][2]

        if key in (readchar.key.UP, "k"):
            self.dupe_file_idx = (self.dupe_file_idx - 1) % len(group_paths)
        elif key in (readchar.key.DOWN, "j"):
            self.dupe_file_idx = (self.dupe_file_idx + 1) % len(group_paths)
        elif key in (readchar.key.RIGHT, "l"):
            # Next group
            self.dupe_group_idx = (self.dupe_group_idx + 1) % len(self.dupes)
            self.dupe_file_idx = 0
        elif key in (readchar.key.LEFT, "h"):
            # Previous group
            self.dupe_group_idx = (self.dupe_group_idx - 1) % len(self.dupes)
            self.dupe_file_idx = 0
        elif key in (readchar.key.ENTER, "\r"):
            # Toggle mark (but don't allow marking all files in group)
            marks = self.dupe_marks.setdefault(self.dupe_group_idx, set())
            if self.dupe_file_idx in marks:
                marks.discard(self.dupe_file_idx)
            else:
                # Must keep at least 1 file per group
                if len(marks) < len(group_paths) - 1:
                    marks.add(self.dupe_file_idx)
        elif key == "x":
            # Delete all marked files across all groups
            deleted_any = False
            for gi, marks in list(self.dupe_marks.items()):
                if not marks or gi >= len(self.dupes):
                    continue
                _, _, paths = self.dupes[gi]
                for fi in sorted(marks, reverse=True):
                    if fi < len(paths):
                        try:
                            paths[fi].unlink()
                            deleted_any = True
                        except (OSError, PermissionError):
                            pass
            if deleted_any:
                # Re-scan after deletion
                self.dupes = find_duplicates()
                self.dupe_marks = {}
                self.dupe_group_idx = 0
                self.dupe_file_idx = 0
        elif key in (readchar.key.ESC, "q"):
            self.mode = "main"
        return None

    def run(self) -> Optional[str]:
        """Run the interactive menu."""
        if not self.console.is_terminal:
            return None

        with Live(self.render(), console=self.console, auto_refresh=False, screen=True) as live:
            while True:
                try:
                    key = readchar.readkey()
                except (KeyboardInterrupt, EOFError):
                    return None
                except Exception:
                    return None

                result = None
                if self.mode == "main":
                    result = self.handle_main_input(key)
                elif self.mode == "sizes":
                    result = self.handle_sizes_input(key)
                elif self.mode == "venvs":
                    result = self.handle_venvs_input(key)
                elif self.mode == "dupes":
                    result = self.handle_dupes_input(key)

                if result == "__EXIT__":
                    return None
                elif result:
                    return result

                # Handle deferred dupe scanning (show "scanning" then run)
                if self.mode == "dupes" and self.dupe_scanning:
                    live.update(self.render(), refresh=True)
                    self.dupes = find_duplicates()
                    self.dupe_marks = {}
                    self.dupe_group_idx = 0
                    self.dupe_file_idx = 0
                    self.dupe_scanning = False

                live.update(self.render(), refresh=True)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--result-file", help="File to write result to")
    args = parser.parse_args()

    console = Console()
    menu = CleanMenu(console)
    result = menu.run()

    def write_result(text: str):
        """Write result to file or stdout."""
        if args.result_file:
            with open(args.result_file, "w") as f:
                f.write(text)
        else:
            print(text)

    if result:
        if result.startswith("__DELETE_VENV__:"):
            venv_dir = result.split(":", 1)[1]
            write_result(f"__CLEAN_CMD__:__DELETE_VENV__:{venv_dir}")
        elif result.startswith("__VENV_CD__:"):
            cd_path = result.split(":", 1)[1]
            write_result(f"__CLEAN_CMD__:__CD__:{cd_path}")
        else:
            write_result(f"__CLEAN_CMD__:{result}")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()

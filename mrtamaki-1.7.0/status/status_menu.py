#!/usr/bin/env python3
"""Interactive system status and cleanup menu with two-column layout and enhanced features."""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

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

# Color themes
THEMES = {
    "default": {
        "accent": "cyan",
        "highlight": "yellow",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "bright_black",
    },
    "ocean": {
        "accent": "blue",
        "highlight": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "blue",
    },
    "sunset": {
        "accent": "magenta",
        "highlight": "yellow",
        "success": "green",
        "warning": "orange3",
        "error": "red",
        "muted": "bright_black",
        "border": "magenta",
    },
}

CURRENT_THEME = "default"

# Commands list
COMMANDS = [
    ("pycache", "Pycache", "Find and delete all __pycache__ directories"),
    ("browser", "Browser", "Clear browser caches (Safari, Chrome, Firefox)"),
    ("appcache", "App Cache", "Clear application cache directories"),
    ("venvs", "Venvs", "Browse and delete virtual environments"),
    ("sizes", "Sizes", "View cache directory sizes overview"),
    ("return", "Exit", "Return to shell"),
]

ICONS = ["", "", "", "", "", ""]


def get_theme():
    """Get current theme colors."""
    return THEMES.get(CURRENT_THEME, THEMES["default"])


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────

def format_bytes(bytes_val: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


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


def find_pycache_dirs() -> List[Path]:
    """Find __pycache__ dirs in common dev locations."""
    pycache_dirs = []
    home = Path.home()
    search_paths = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Projects",
    ]
    for sp in search_paths:
        if not sp.exists():
            continue
        try:
            for p in sp.rglob("__pycache__"):
                if p.is_dir():
                    pycache_dirs.append(p)
        except (OSError, PermissionError):
            pass
    return pycache_dirs


def find_venvs(search_root: Path = Path.home(), max_depth: int = 5) -> List[Tuple[Path, int]]:
    """Find virtual environments with sizes."""
    venvs = []

    def search_dir(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in path.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name.startswith(".") and entry.name != ".venv":
                    continue
                if entry.name in ("venv", ".venv", "env", "pyenv"):
                    if (entry / "bin" / "activate").exists() and (entry / "bin" / "python").exists():
                        size = get_dir_size(entry)
                        venvs.append((entry, size))
                        continue
                if entry.name not in ("node_modules", "Library", ".Trash", ".git"):
                    search_dir(entry, depth + 1)
        except (OSError, PermissionError):
            pass

    search_dir(search_root, 0)
    return venvs


def get_browser_cache_paths() -> dict:
    """Get browser cache directory paths."""
    home = Path.home()
    return {
        "Safari": home / "Library" / "Caches" / "com.apple.Safari",
        "Chrome": home / "Library" / "Caches" / "Google" / "Chrome",
        "Firefox": home / "Library" / "Caches" / "Firefox",
    }


def get_system_context() -> dict:
    """Get system status context info."""
    disk = psutil.disk_usage(str(Path.home()))

    # Count pycache dirs
    pycache_count = len(find_pycache_dirs())

    # Browser cache info
    browser_caches = get_browser_cache_paths()
    browser_found = []
    for name, path in browser_caches.items():
        if path.exists():
            browser_found.append(name)

    return {
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": disk.percent,
        "pycache_count": pycache_count,
        "browser_found": browser_found,
    }


def build_sizes_overview() -> Text:
    """Build cache sizes overview (like tree view in fmenu)."""
    theme = get_theme()
    content = Text()

    content.append("Cache Sizes Overview\n\n", style=f"bold {theme['accent']}")

    # __pycache__
    pycache_dirs = find_pycache_dirs()
    pycache_size = sum(get_dir_size(d) for d in pycache_dirs)
    content.append("  __pycache__\n", style=f"bold {theme['highlight']}")
    content.append(f"    {len(pycache_dirs)} dirs, {format_bytes(pycache_size)}\n\n", style=theme["muted"])

    # Browser
    browser_caches = get_browser_cache_paths()
    browser_total = 0
    has_browser = False
    for name, path in browser_caches.items():
        if path.exists():
            has_browser = True
            size = get_dir_size(path)
            browser_total += size
            content.append(f"  {name}\n", style=f"bold {theme['highlight']}")
            content.append(f"    {format_bytes(size)}\n", style=theme["muted"])
    if not has_browser:
        content.append("  Browser Caches\n", style=f"bold {theme['highlight']}")
        content.append("    (none found)\n", style=theme["muted"])
    content.append("\n")

    # Venvs
    venvs = find_venvs(max_depth=3)
    venv_size = sum(s for _, s in venvs)
    content.append("  Virtual Envs\n", style=f"bold {theme['highlight']}")
    content.append(f"    {len(venvs)} venvs, {format_bytes(venv_size)}\n\n", style=theme["muted"])

    total = pycache_size + browser_total + venv_size
    content.append(f"  Total Cleanable: {format_bytes(total)}\n", style=f"bold {theme['success']}")

    return content


# ─────────────────────────────────────────────────────────────────────────────
# Menu class
# ─────────────────────────────────────────────────────────────────────────────

class StatusMenu:
    """Interactive status menu with two-column layout."""

    def __init__(self, console: Console):
        self.console = console
        self.selected = 0
        self.total = len(COMMANDS)
        self.context = get_system_context()
        self.mode = "main"  # main, venvs, sizes
        self.venv_selected = 0
        self.venvs: List[Tuple[Path, int]] = []
        self.sizes_content: Optional[Text] = None

    def render_header(self) -> Panel:
        """Render system context header."""
        theme = get_theme()
        ctx = self.context

        header = Text()
        header.append("  ", style=theme["accent"])
        header.append(" System Status\n", style=f"bold {theme['accent']}")
        header.append(f"   {ctx['pycache_count']} pycache  ", style=theme["muted"])
        header.append(f" {len(ctx['browser_found'])} browsers  ", style=theme["muted"])

        # Disk usage with color
        pct = ctx["disk_percent"]
        if pct > 90:
            pct_style = theme["error"]
        elif pct > 70:
            pct_style = theme["warning"]
        else:
            pct_style = theme["success"]
        header.append(f" {pct:.0f}% used", style=pct_style)
        header.append(f" ({format_bytes(ctx['disk_free'])} free)", style=theme["muted"])

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
                lines.append(f"{cmd:<7}", style=f"bold {theme['highlight']}")
                lines.append(f" {name}\n", style="bold white")
            else:
                lines.append("   ", style="")
                lines.append(f"{icon} ", style=theme["muted"])
                lines.append(f"{cmd:<7}", style=f"dim {theme['highlight']}")
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
            title = "Cache Sizes"
        elif self.mode == "venvs":
            content = self.render_venvs_list()
            title = "Virtual Environments"
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

        # Disk Usage (like Recent Files in fmenu)
        info.append("Disk Usage\n", style=f"bold {theme['accent']}")
        ctx = self.context
        info.append(f"  Total: {format_bytes(ctx['disk_total'])}\n", style=theme["muted"])
        info.append(f"  Used:  {format_bytes(ctx['disk_used'])}\n", style=theme["muted"])
        info.append(f"  Free:  {format_bytes(ctx['disk_free'])}\n", style=theme["muted"])

        info.append("\n")

        # Browsers detected (like Bookmarks summary in fmenu)
        info.append("Browsers Detected\n", style=f"bold {theme['accent']}")
        if ctx["browser_found"]:
            for b in ctx["browser_found"]:
                info.append(f"  {b}\n", style=theme["muted"])
        else:
            info.append("  (none)\n", style=theme["muted"])

        return info

    def render_venvs_list(self) -> Text:
        """Render venvs for selection (like bookmarks in fmenu)."""
        theme = get_theme()
        content = Text()

        if not self.venvs:
            content.append("No virtual environments found.\n\n", style=theme["muted"])
            content.append("Searched ", style=theme["muted"])
            content.append("$HOME", style=theme["highlight"])
            content.append(" (depth 5).", style=theme["muted"])
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
        content.append(f"\n[{theme['muted']}]{len(self.venvs)} venvs, {format_bytes(total)} total[/]")
        content.append(f"\n[{theme['muted']}]Enter to go, x to delete, Esc to back[/]")
        return content

    def render_footer(self) -> Panel:
        """Render controls footer."""
        theme = get_theme()
        controls = Text()

        if self.mode == "main":
            controls.append("  ↑↓", style=f"bold {theme['accent']}")
            controls.append(" navigate  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("s", style=f"bold {theme['accent']}")
            controls.append(" sizes  ", style=theme["muted"])
            controls.append("v", style=f"bold {theme['accent']}")
            controls.append(" venvs  ", style=theme["muted"])
            controls.append("q", style=f"bold {theme['accent']}")
            controls.append(" quit", style=theme["muted"])
        elif self.mode == "sizes":
            controls.append("  Esc", style=f"bold {theme['accent']}")
            controls.append(" back to menu", style=theme["muted"])
        elif self.mode == "venvs":
            controls.append("  ↑↓", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" go  ", style=theme["muted"])
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
            else:
                return cmd
        elif key == "s":
            self.sizes_content = None
            self.mode = "sizes"
        elif key == "v":
            self.venvs = find_venvs()
            self.venv_selected = 0
            self.mode = "venvs"
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

    def run(self) -> Optional[str]:
        """Run the interactive menu."""
        if not self.console.is_terminal:
            return None

        self.console.clear()

        with Live(self.render(), console=self.console, refresh_per_second=30, screen=True) as live:
            while True:
                try:
                    key = readchar.readkey()
                except (KeyboardInterrupt, EOFError):
                    return None

                result = None
                if self.mode == "main":
                    result = self.handle_main_input(key)
                elif self.mode == "sizes":
                    result = self.handle_sizes_input(key)
                elif self.mode == "venvs":
                    result = self.handle_venvs_input(key)

                if result == "__EXIT__":
                    return None
                elif result:
                    return result

                live.update(self.render())


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--result-file", help="File to write result to")
    args = parser.parse_args()

    console = Console()
    menu = StatusMenu(console)
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
            path = result.split(":", 1)[1]
            write_result(f"__STATUSMENU_CMD__:__DELETE_VENV__:{path}")
        elif result.startswith("__VENV_CD__:"):
            path = result.split(":", 1)[1]
            write_result(f"__STATUSMENU_CMD__:__CD__:{path}")
        else:
            write_result(f"__STATUSMENU_CMD__:{result}")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()

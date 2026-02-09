#!/usr/bin/env python3
"""Interactive file operations menu with two-column layout and enhanced features."""

import sys
import os
import json
import shutil
from pathlib import Path
from typing import Optional

import readchar
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box

# Config paths
CONFIG_DIR = Path.home() / ".config" / "mrtamaki"
BOOKMARKS_FILE = CONFIG_DIR / "bookmarks.json"

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
    ("fa", "Edit .zshrc", "Edit .zshrc with backup and auto-reload"),
    ("fb", "Search Files", "Recursive grep search in current directory"),
    ("mkcd", "Make & Enter", "Create directory and cd into it"),
    ("flast", "Open Last", "Open the most recently modified file"),
    ("fe", "Large Files", "Find files larger than configured size"),
    ("tempdir", "Temp Dir", "Create and enter a temporary directory"),
    ("ff", "Backup File", "Create timestamped backup of a file"),
    ("fg", "Desktop Dir", "Create timestamped folder on Desktop"),
    ("ftree", "Tree View", "Show directory tree structure"),
    ("fbook", "Bookmark", "Save current directory as bookmark"),
    ("fgo", "Go to Bookmark", "Jump to a bookmarked directory"),
    ("return", "Exit", "Return to shell"),
]

ICONS = ["", "", "", "", "", "", "", "", "", "", "", ""]


def get_theme():
    """Get current theme colors."""
    return THEMES.get(CURRENT_THEME, THEMES["default"])


def load_bookmarks() -> dict:
    """Load bookmarks from config file."""
    if BOOKMARKS_FILE.exists():
        try:
            return json.loads(BOOKMARKS_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_bookmarks(bookmarks: dict):
    """Save bookmarks to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    BOOKMARKS_FILE.write_text(json.dumps(bookmarks, indent=2))


def get_dir_context() -> dict:
    """Get current directory context info."""
    cwd = Path.cwd()

    # File count
    try:
        files = list(cwd.iterdir())
        file_count = len([f for f in files if f.is_file()])
        dir_count = len([f for f in files if f.is_dir()])
    except PermissionError:
        file_count = dir_count = 0

    # Disk usage
    try:
        usage = shutil.disk_usage(cwd)
        used_pct = (usage.used / usage.total) * 100
        free_gb = usage.free / (1024**3)
    except (OSError, ZeroDivisionError):
        used_pct = 0
        free_gb = 0

    # Recent files (last 5)
    try:
        recent = sorted(
            [f for f in cwd.iterdir() if f.is_file()],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:5]
        recent_names = [f.name for f in recent]
    except (PermissionError, OSError):
        recent_names = []

    return {
        "path": str(cwd),
        "file_count": file_count,
        "dir_count": dir_count,
        "used_pct": used_pct,
        "free_gb": free_gb,
        "recent": recent_names,
    }


def build_file_tree(path: Path, depth: int = 2) -> Tree:
    """Build a Rich tree of directory contents."""
    theme = get_theme()
    tree = Tree(
        f"[bold {theme['accent']}]{path.name or path}[/]",
        guide_style=theme["muted"],
    )

    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

        for entry in entries[:15]:  # Limit entries
            if entry.name.startswith('.'):
                continue

            if entry.is_dir():
                if depth > 1:
                    subtree = build_file_tree(entry, depth - 1)
                    tree.add(subtree)
                else:
                    tree.add(f"[bold {theme['accent']}]{entry.name}/[/]")
            else:
                # Color by extension
                ext = entry.suffix.lower()
                if ext in ('.py', '.js', '.ts', '.sh', '.zsh'):
                    style = "green"
                elif ext in ('.md', '.txt', '.json', '.yaml', '.yml'):
                    style = "yellow"
                elif ext in ('.jpg', '.png', '.gif', '.svg'):
                    style = "magenta"
                else:
                    style = "white"
                tree.add(f"[{style}]{entry.name}[/]")

        remaining = len(list(path.iterdir())) - 15
        if remaining > 0:
            tree.add(f"[{theme['muted']}]... and {remaining} more[/]")

    except PermissionError:
        tree.add(f"[{theme['error']}]Permission denied[/]")

    return tree


class FileMenu:
    """Interactive file menu with two-column layout."""

    def __init__(self, console: Console):
        self.console = console
        self.selected = 0
        self.total = len(COMMANDS)
        self.context = get_dir_context()
        self.bookmarks = load_bookmarks()
        self.mode = "main"  # main, bookmarks, tree
        self.bookmark_selected = 0

    def render_header(self) -> Panel:
        """Render directory context header."""
        theme = get_theme()
        ctx = self.context

        # Truncate path if too long
        path = ctx["path"]
        if len(path) > 45:
            path = "..." + path[-42:]

        header = Text()
        header.append("  ", style=theme["accent"])
        header.append(f" {path}\n", style=f"bold {theme['accent']}")
        header.append(f"   {ctx['file_count']} files  ", style=theme["muted"])
        header.append(f" {ctx['dir_count']} dirs  ", style=theme["muted"])

        # Disk usage with color
        pct = ctx["used_pct"]
        if pct > 90:
            pct_style = theme["error"]
        elif pct > 70:
            pct_style = theme["warning"]
        else:
            pct_style = theme["success"]
        header.append(f" {pct:.0f}% used", style=pct_style)
        header.append(f" ({ctx['free_gb']:.1f}GB free)", style=theme["muted"])

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

        if self.mode == "tree":
            # Tree view
            tree = build_file_tree(Path.cwd(), depth=2)
            content = tree
            title = "Directory Tree"
        elif self.mode == "bookmarks":
            # Bookmarks list
            content = self.render_bookmarks_list()
            title = "Bookmarks"
        else:
            # Default: show description + recent files + bookmarks summary
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

        # Recent files
        info.append("Recent Files\n", style=f"bold {theme['accent']}")
        if self.context["recent"]:
            for f in self.context["recent"]:
                if len(f) > 25:
                    f = f[:22] + "..."
                info.append(f"  {f}\n", style=theme["muted"])
        else:
            info.append("  (none)\n", style=theme["muted"])

        info.append("\n")

        # Bookmarks summary
        info.append("Bookmarks\n", style=f"bold {theme['accent']}")
        if self.bookmarks:
            for name in list(self.bookmarks.keys())[:4]:
                info.append(f"  {name}\n", style=theme["muted"])
            if len(self.bookmarks) > 4:
                info.append(f"  ... +{len(self.bookmarks) - 4} more\n", style=theme["muted"])
        else:
            info.append("  (none)\n", style=theme["muted"])

        return info

    def render_bookmarks_list(self) -> Text:
        """Render bookmarks for selection."""
        theme = get_theme()
        content = Text()

        if not self.bookmarks:
            content.append("No bookmarks saved.\n\n", style=theme["muted"])
            content.append("Use ", style=theme["muted"])
            content.append("fbook", style=theme["highlight"])
            content.append(" to add one.", style=theme["muted"])
            return content

        bookmark_items = list(self.bookmarks.items())
        for idx, (name, path) in enumerate(bookmark_items):
            if idx == self.bookmark_selected:
                content.append(" > ", style=f"bold {theme['accent']}")
                content.append(f"{name}\n", style="bold white")
                # Show path for selected
                display_path = path if len(path) <= 30 else "..." + path[-27:]
                content.append(f"   {display_path}\n", style=theme["muted"])
            else:
                content.append(f"   {name}\n", style="dim white")

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
            controls.append("t", style=f"bold {theme['accent']}")
            controls.append(" tree  ", style=theme["muted"])
            controls.append("b", style=f"bold {theme['accent']}")
            controls.append(" bookmarks  ", style=theme["muted"])
            controls.append("q", style=f"bold {theme['accent']}")
            controls.append(" quit", style=theme["muted"])
        elif self.mode == "tree":
            controls.append("  Esc", style=f"bold {theme['accent']}")
            controls.append(" back to menu", style=theme["muted"])
        elif self.mode == "bookmarks":
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
            elif cmd == "ftree":
                self.mode = "tree"
            elif cmd == "fgo":
                if self.bookmarks:
                    self.mode = "bookmarks"
                    self.bookmark_selected = 0
            else:
                return cmd
        elif key == "t":
            self.mode = "tree"
        elif key == "b":
            if self.bookmarks:
                self.mode = "bookmarks"
                self.bookmark_selected = 0
        elif key in ("q", readchar.key.ESC):
            return "__EXIT__"
        return None

    def handle_tree_input(self, key: str) -> Optional[str]:
        """Handle input in tree mode."""
        if key in (readchar.key.ESC, "q", readchar.key.ENTER):
            self.mode = "main"
        return None

    def handle_bookmarks_input(self, key: str) -> Optional[str]:
        """Handle input in bookmarks mode."""
        bookmark_items = list(self.bookmarks.items())

        if key in (readchar.key.UP, "k"):
            if bookmark_items:
                self.bookmark_selected = (self.bookmark_selected - 1) % len(bookmark_items)
        elif key in (readchar.key.DOWN, "j"):
            if bookmark_items:
                self.bookmark_selected = (self.bookmark_selected + 1) % len(bookmark_items)
        elif key in (readchar.key.ENTER, "\r"):
            if bookmark_items:
                name, path = bookmark_items[self.bookmark_selected]
                return f"__GOTO__:{path}"
        elif key == "x":
            # Delete bookmark
            if bookmark_items:
                name = bookmark_items[self.bookmark_selected][0]
                del self.bookmarks[name]
                save_bookmarks(self.bookmarks)
                if self.bookmark_selected >= len(self.bookmarks):
                    self.bookmark_selected = max(0, len(self.bookmarks) - 1)
                if not self.bookmarks:
                    self.mode = "main"
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
                elif self.mode == "tree":
                    result = self.handle_tree_input(key)
                elif self.mode == "bookmarks":
                    result = self.handle_bookmarks_input(key)

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
    menu = FileMenu(console)
    result = menu.run()

    def write_result(text: str):
        """Write result to file or stdout."""
        if args.result_file:
            with open(args.result_file, "w") as f:
                f.write(text)
        else:
            print(text)

    if result:
        if result.startswith("__GOTO__:"):
            path = result.split(":", 1)[1]
            write_result(f"__FILEMENU_CMD__:__CD__:{path}")
        else:
            write_result(f"__FILEMENU_CMD__:{result}")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()

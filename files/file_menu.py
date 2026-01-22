#!/usr/bin/env python3
"""Interactive file operations menu with arrow key navigation."""

import sys
import os
import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

COMMANDS = [
    ("fa", "Edit & Reload .zshrc", "Edit .zshrc with backup and auto-reload on changes"),
    ("fb", "Search Files", "Recursive grep search in current directory"),
    ("mkcd", "Make & Enter Dir", "Create directory and cd into it"),
    ("flast", "Open Last File", "Open the most recently modified file"),
    ("fe", "Find Large Files", "Find files larger than configured size"),
    ("tempdir", "Create Temp Dir", "Create and enter a temporary directory"),
    ("ff", "Backup File", "Create timestamped backup of a file"),
    ("fg", "Desktop Folder", "Create timestamped folder on Desktop"),
    ("return", "Return", "Exit menu and return to shell"),
]

ICONS = ["", "", "", "", "", "", "", "", ""]

class ArrowMenu:
    """Interactive menu with arrow key navigation."""

    def __init__(self, console: Console):
        self.console = console
        self.selected = 0
        self.total = len(COMMANDS)

    def render(self) -> Panel:
        """Render the menu with current selection highlighted."""
        lines = Text()

        # Title
        lines.append("  File Operations\n\n", style="bold magenta")

        for idx, (cmd, name, desc) in enumerate(COMMANDS):
            icon = ICONS[idx] if idx < len(ICONS) else ""

            if idx == self.selected:
                # Highlighted row
                lines.append("  > ", style="bold cyan")
                lines.append(f"{icon} ", style="bold cyan")
                lines.append(f"{cmd:<8}", style="bold yellow")
                lines.append(f" {name}\n", style="bold white")
            else:
                # Normal row
                lines.append("    ", style="dim")
                lines.append(f"{icon} ", style="dim")
                lines.append(f"{cmd:<8}", style="dim yellow")
                lines.append(f" {name}\n", style="dim white")

        # Description of selected item
        lines.append("\n")
        lines.append(f"  {COMMANDS[self.selected][2]}", style="italic bright_black")

        # Controls hint
        lines.append("\n\n  ", style="")
        lines.append("↑↓", style="bold cyan")
        lines.append(" navigate  ", style="dim")
        lines.append("Enter", style="bold cyan")
        lines.append(" select  ", style="dim")
        lines.append("q", style="bold cyan")
        lines.append(" quit", style="dim")

        return Panel(
            lines,
            border_style="bright_black",
            padding=(1, 2),
            expand=False,
        )

    def move_up(self):
        """Move selection up."""
        self.selected = (self.selected - 1) % self.total

    def move_down(self):
        """Move selection down."""
        self.selected = (self.selected + 1) % self.total

    def run(self) -> str | None:
        """Run the interactive menu and return selected command."""
        if not self.console.is_terminal:
            return None

        self.console.clear()

        with Live(self.render(), console=self.console, refresh_per_second=30, transient=False) as live:
            while True:
                try:
                    key = readchar.readkey()
                except (KeyboardInterrupt, EOFError):
                    self.console.clear()
                    return None

                if key in (readchar.key.UP, "k"):
                    self.move_up()
                elif key in (readchar.key.DOWN, "j"):
                    self.move_down()
                elif key in (readchar.key.ENTER, readchar.key.ENTER_2):
                    self.console.clear()
                    selected_cmd = COMMANDS[self.selected][0]
                    if selected_cmd == "return":
                        return None
                    return selected_cmd
                elif key in ("q", readchar.key.ESC):
                    self.console.clear()
                    return None

                live.update(self.render())


def main():
    """Main entry point."""
    console = Console()

    menu = ArrowMenu(console)
    result = menu.run()

    if result:
        # Output the selected command for shell to execute
        print(f"__FILEMENU_CMD__:{result}")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()

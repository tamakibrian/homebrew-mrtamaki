"""Shared utilities for mrtamaki CLI."""
import os
import subprocess
import sys
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

# Constants (from utils.sh)
PORT_MIN = 1
PORT_MAX = 64900
NETWORK_TIMEOUT = 10
MAX_FILE_SIZE = "100M"
VENV_SEARCH_DEPTH = 5
SESSION_ID_LENGTH = 8

console = Console()
console_err = Console(stderr=True)


def print_success(msg: str) -> None:
    console.print(f"[green]✓[/green] {msg}")


def print_error(msg: str) -> None:
    console_err.print(f"[red]✗[/red] {msg}")


def print_warning(msg: str) -> None:
    console.print(f"[yellow]⚠[/yellow] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[cyan]ℹ[/cyan] {msg}")


def print_header(msg: str) -> None:
    console.print(f"\n[bold blue]═══ {msg} ═══[/bold blue]\n")


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard. Returns True on success."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    # Fallback: pbcopy (macOS), xclip, xsel
    for cmd in ["pbcopy", "xclip -selection clipboard", "xsel --clipboard --input"]:
        try:
            subprocess.run(cmd.split(), input=text.encode(), check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return False


def confirm(prompt: str, default: str = "n") -> bool:
    """Prompt for Y/N. Default 'y' or 'n'."""
    default_bool = default.lower() in ("y", "yes")
    return Confirm.ask(prompt, default=default_bool)


def human_size(blocks_512: int) -> str:
    """Convert du block count (512-byte blocks) to human-readable string."""
    b = blocks_512 * 512
    if b >= 1073741824:
        return f"{b / 1073741824:.1f} GB"
    if b >= 1048576:
        return f"{b / 1048576:.1f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"

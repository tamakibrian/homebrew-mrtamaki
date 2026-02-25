"""Shared utilities for mrtamaki CLI."""
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.prompt import Confirm, Prompt

# Import UI components
try:
    from .ui_components import ui, set_theme, get_theme_names
except ImportError:
    # Fallback for when ui_components is not available
    ui = None

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
    """Print a success message with consistent styling."""
    if ui:
        console.print(ui.create_status_message(msg, "success"))
    else:
        console.print(f"[green]✓[/green] {msg}")


def print_error(msg: str) -> None:
    """Print an error message with consistent styling."""
    if ui:
        console_err.print(ui.create_status_message(msg, "error"))
    else:
        console_err.print(f"[red]✗[/red] {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message with consistent styling."""
    if ui:
        console.print(ui.create_status_message(msg, "warning"))
    else:
        console.print(f"[yellow]⚠[/yellow] {msg}")


def print_info(msg: str) -> None:
    """Print an info message with consistent styling."""
    if ui:
        console.print(ui.create_status_message(msg, "info"))
    else:
        console.print(f"[cyan]ℹ[/cyan] {msg}")


def print_header(msg: str) -> None:
    """Print a header with consistent styling."""
    if ui:
        theme = ui.theme
        console.print(f"\n[bold {theme['accent']}]═══ {msg} ═══[/bold {theme['accent']}]\n")
    else:
        console.print(f"\n[bold blue]═══ {msg} ═══[/bold blue]\n")


def print_table(headers: List[str], rows: List[List[Any]], title: str = "") -> None:
    """Print a table with consistent styling."""
    if ui:
        table = ui.create_table(headers, rows)
        if title:
            panel = ui.create_panel(table, title)
            console.print(panel)
        else:
            console.print(table)
    else:
        # Fallback implementation
        from rich.table import Table
        table = Table(*headers)
        for row in rows:
            table.add_row(*[str(item) for item in row])
        console.print(table)


def validate_input(
    value: str,
    input_type: str = "generic",
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
    allowed_values: Optional[List[str]] = None,
) -> tuple[bool, str]:
    """
    Validate user input with comprehensive error messages.
    
    Args:
        value: Input value to validate
        input_type: Type of input (ip, email, port, path, etc.)
        min_length: Minimum length requirement
        max_length: Maximum length requirement
        pattern: Regex pattern to match
        allowed_values: List of allowed values
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    
    value = value.strip()
    
    # Check required
    if not value:
        return False, "Input cannot be empty"
    
    # Check length constraints
    if min_length and len(value) < min_length:
        return False, f"Input must be at least {min_length} characters"
    if max_length and len(value) > max_length:
        return False, f"Input must be at most {max_length} characters"
    
    # Type-specific validation
    if input_type == "ip":
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, value):
            return False, "Invalid IP address format (expected: xxx.xxx.xxx.xxx)"
    
    elif input_type == "email":
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            return False, "Invalid email address format"
    
    elif input_type == "port":
        try:
            port = int(value)
            if port < PORT_MIN or port > PORT_MAX:
                return False, f"Port must be between {PORT_MIN} and {PORT_MAX}"
        except ValueError:
            return False, "Port must be a valid number"
    
    elif input_type == "path":
        if not os.path.exists(value):
            return False, f"Path does not exist: {value}"
    
    # Check pattern if provided
    if pattern:
        if not re.match(pattern, value):
            return False, "Input does not match required format"
    
    # Check allowed values
    if allowed_values and value not in allowed_values:
        return False, f"Input must be one of: {', '.join(allowed_values)}"
    
    return True, ""


def prompt_with_validation(
    prompt_text: str,
    input_type: str = "generic",
    default: Optional[str] = None,
    **validation_kwargs,
) -> str:
    """
    Prompt user for input with validation.
    
    Args:
        prompt_text: Text to display as prompt
        input_type: Type of input for validation
        default: Default value if user enters nothing
        **validation_kwargs: Additional validation parameters
    
    Returns:
        Validated user input
    """
    while True:
        value = Prompt.ask(prompt_text, default=default)
        
        is_valid, error_msg = validate_input(value, input_type, **validation_kwargs)
        
        if is_valid:
            return value
        else:
            print_error(error_msg)
            print_info("Please try again.")


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
    """Prompt for Y/N with clear instructions. Default 'y' or 'n'."""
    default_bool = default.lower() in ("y", "yes")
    
    # Add hint about default
    hint = "(Y/n)" if default_bool else "(y/N)"
    full_prompt = f"{prompt} {hint}"
    
    return Confirm.ask(full_prompt, default=default_bool)


def confirm_destructive(prompt: str, item_name: str = "") -> bool:
    """
    Confirm destructive operation with extra warning.
    
    Args:
        prompt: The confirmation prompt
        item_name: Name of item being affected (for clarity)
    
    Returns:
        True if user confirms
    """
    print_warning(f"⚠  Destructive operation: {prompt}")
    if item_name:
        print_warning(f"   Item: {item_name}")
    
    # Require explicit confirmation
    confirmation = Prompt.ask(
        "Type 'YES' to confirm or anything else to cancel",
        default="NO"
    )
    
    return confirmation.upper() == "YES"


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


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def get_terminal_width() -> int:
    """Get current terminal width."""
    try:
        return os.get_terminal_size().columns
    except (AttributeError, OSError):
        return 80

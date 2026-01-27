#!/usr/bin/env python3
"""
Interactive menu UI for 1lookup API
Uses Rich for display and InquirerPy for interactive prompts

This module provides:
- print_result_table(): CLI summary output (used by cli.py)
- show_menu(): Legacy interactive menu (superseded by menu_v2)
"""

import sys
from typing import Dict, Any, Optional, Tuple

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("ERROR: 'rich' package not found. Reinstall cask to fix.", file=sys.stderr)
    sys.exit(2)

try:
    from InquirerPy import inquirer
    from InquirerPy.base.control import Choice
except ImportError:
    print("ERROR: 'InquirerPy' package not found. Reinstall cask to fix.", file=sys.stderr)
    sys.exit(2)

from .client import OneLookupClient
from .ui_utils import (
    format_value,
    format_key,
    extract_sections,
    get_status_info,
    get_error_message,
    Section,
)


class BackToMenu(Exception):
    """Raised when user wants to return to main menu."""
    pass


# Command definitions
COMMANDS = [
    {"name": "IP Lookup", "value": "ip", "description": "Look up IP address info"},
    {"name": "Email Verify", "value": "email", "description": "Verify email address"},
    {"name": "Exit", "value": "exit", "description": "Exit menu"},
]


def print_header(console: Console) -> None:
    """Display the menu header."""
    header = Text("1lookup API Menu", style="bold cyan")
    panel = Panel(header, border_style="cyan", padding=(0, 2))
    console.print(panel)
    console.print()


def create_section_table(section: Section) -> Table:
    """
    Create a styled Rich table for a section.

    Args:
        section: Section object with name, data, and color

    Returns:
        Rich Table object
    """
    table = Table(
        title=section.name,
        show_header=True,
        header_style=f"bold {section.color}",
        border_style=section.color,
        title_style=f"bold {section.color}",
        expand=True,
    )
    table.add_column("Field", style="dim", ratio=1)
    table.add_column("Value", ratio=2)

    for key, value in section.data.items():
        display_val, val_style = format_value(value, key)
        styled_val = Text(display_val, style=val_style)
        display_key = format_key(key)
        table.add_row(display_key, styled_val)

    return table


def print_result_table(console: Console, data: Dict[str, Any], title: str) -> None:
    """
    Print results in grouped sections with color-coded risk.

    This is the main output function used by cli.py for non-interactive display.

    Args:
        console: Rich Console instance
        data: API response dictionary
        title: Display title for the results
    """
    console.print(Panel(Text(title, style="bold white"), border_style="cyan"))
    console.print()

    # Check for error
    error_msg = get_error_message(data)
    if error_msg:
        console.print(f"[red]Error:[/red] {error_msg}")
        console.print()
        return

    # Status line
    status_info = get_status_info(data)
    if status_info:
        success, style = status_info
        status_text = "Success" if success else "Failed"
        console.print(f"[{style}]Status: {status_text}[/{style}]")
        console.print()

    # Extract and display sections (include low-priority sections for CLI)
    sections = extract_sections(data, include_low_priority=True)

    for section in sections:
        console.print(create_section_table(section))
        console.print()


def get_command_choices():
    """Build choices for the command selector."""
    choices = []
    for cmd in COMMANDS:
        # Format: "Name         - Description"
        name_padded = cmd["name"].ljust(14)
        display = f"{name_padded} - {cmd['description']}"
        choices.append(Choice(value=cmd["value"], name=display))
    return choices


def prompt_text(message: str, validate=None, optional: bool = False) -> str:
    """
    Prompt for text input with back-to-menu support.
    Raises BackToMenu if user presses Ctrl+C or types 'back'.
    """
    try:
        if optional:
            result = inquirer.text(message=message).execute()
        else:
            result = inquirer.text(
                message=message,
                validate=validate or (lambda x: len(x.strip()) > 0 or "This field is required"),
            ).execute()

        # Check for 'back' command
        if result and result.strip().lower() == "back":
            raise BackToMenu()

        return result
    except KeyboardInterrupt:
        raise BackToMenu()


def print_back_hint(console: Console) -> None:
    """Print hint about how to go back to menu."""
    console.print("[dim]Press Ctrl+C or type 'back' to return to menu[/dim]")
    console.print()


def prompt_ip_lookup(console: Console, client: OneLookupClient) -> Optional[Tuple[Dict[str, Any], str]]:
    """Prompt for IP lookup."""
    print_back_hint(console)

    ip = prompt_text(
        message="Enter IP address:",
        validate=lambda x: (len(x.strip()) > 0 and x.strip().lower() != "back") or "IP address is required",
    )

    if not ip or not ip.strip():
        return None

    console.print(f"[dim]Looking up IP: {ip}[/dim]")
    return client.ip_lookup(ip.strip()), f"IP Lookup: {ip.strip()}"


def prompt_email_verify(console: Console, client: OneLookupClient) -> Optional[Tuple[Dict[str, Any], str]]:
    """Prompt for email verification."""
    print_back_hint(console)

    email = prompt_text(
        message="Enter email address:",
        validate=lambda x: (("@" in x) or x.strip().lower() == "back") or "Valid email address required",
    )

    if not email or not email.strip():
        return None

    console.print(f"[dim]Verifying email: {email}[/dim]")
    return client.email_verify(email.strip()), f"Email Verification: {email.strip()}"


def show_menu() -> int:
    """
    Main interactive menu loop (legacy version).

    Note: This is superseded by menu_v2.show_menu() but kept for compatibility.
    The CLI now defaults to menu_v2.

    Returns:
        Exit code (0 for success)
    """
    console = Console()

    # Initialize client (will check for API key)
    try:
        client = OneLookupClient()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        return 2

    while True:
        # Clear screen and show header
        console.clear()
        print_header(console)

        # Show command selection
        try:
            command = inquirer.select(
                message="Select a command:",
                choices=get_command_choices(),
                pointer="❯",
            ).execute()
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
            return 0

        if command == "exit":
            console.print("[dim]Goodbye![/dim]")
            return 0

        # Execute selected command
        console.print()
        result = None
        title = ""

        try:
            if command == "ip":
                result, title = prompt_ip_lookup(console, client)
            elif command == "email":
                result, title = prompt_email_verify(console, client)

            if result:
                console.print()
                if result.get("error"):
                    console.print(f"[red]Error:[/red] {result.get('message', 'Unknown error')}")
                else:
                    print_result_table(console, result, title)

        except BackToMenu:
            # User pressed Ctrl+C or typed 'back' - return to main menu
            continue
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

        # Ask to continue
        console.print()
        try:
            continue_loop = inquirer.confirm(
                message="Run another lookup?",
                default=True,
            ).execute()

            if not continue_loop:
                console.print("[dim]Goodbye![/dim]")
                return 0
        except KeyboardInterrupt:
            # Ctrl+C on confirm prompt - return to menu
            continue


if __name__ == "__main__":
    sys.exit(show_menu())

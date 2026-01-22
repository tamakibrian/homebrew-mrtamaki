#!/usr/bin/env python3
"""
Interactive menu UI for 1lookup API
Uses Rich for display and InquirerPy for interactive prompts
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


class BackToMenu(Exception):
    """Raised when user wants to return to main menu."""
    pass


# Command definitions
COMMANDS = [
    {"name": "IP Lookup", "value": "ip", "description": "Look up IP address info"},
    {"name": "Email Verify", "value": "email", "description": "Verify email address"},
    {"name": "Email Append", "value": "email-append", "description": "Find email from name/address"},
    {"name": "Reverse Email", "value": "reverse-email", "description": "Find person from email"},
    {"name": "Reverse IP", "value": "reverse-ip", "description": "Find details from IP"},
    {"name": "Exit", "value": "exit", "description": "Exit menu"},
]


def print_header(console: Console) -> None:
    """Display the menu header."""
    header = Text("1lookup API Menu", style="bold cyan")
    panel = Panel(header, border_style="cyan", padding=(0, 2))
    console.print(panel)
    console.print()


def print_result_table(console: Console, data: Dict[str, Any], title: str) -> None:
    """Print results in a rich table."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Field", style="dim")
    table.add_column("Value")

    def add_rows(d: Dict[str, Any], prefix: str = ""):
        for key, value in d.items():
            if isinstance(value, dict):
                add_rows(value, f"{prefix}{key}.")
            elif isinstance(value, list):
                table.add_row(f"{prefix}{key}", str(value))
            else:
                table.add_row(f"{prefix}{key}", str(value) if value is not None else "-")

    add_rows(data)
    console.print(table)
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


def prompt_email_append(console: Console, client: OneLookupClient) -> Optional[Tuple[Dict[str, Any], str]]:
    """Prompt for email append (find email from personal info)."""
    print_back_hint(console)

    first_name = prompt_text(
        message="First name:",
        validate=lambda x: (len(x.strip()) > 0 and x.strip().lower() != "back") or "First name is required",
    )

    last_name = prompt_text(
        message="Last name:",
        validate=lambda x: (len(x.strip()) > 0 and x.strip().lower() != "back") or "Last name is required",
    )

    city = prompt_text(
        message="City:",
        validate=lambda x: (len(x.strip()) > 0 and x.strip().lower() != "back") or "City is required",
    )

    zip_code = prompt_text(
        message="ZIP code:",
        validate=lambda x: (len(x.strip()) > 0 and x.strip().lower() != "back") or "ZIP code is required",
    )

    address = prompt_text(
        message="Street address (optional, press Enter to skip):",
        optional=True,
    )

    console.print(f"[dim]Looking up email for: {first_name} {last_name} in {city}, {zip_code}[/dim]")
    result = client.email_append(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        city=city.strip(),
        zip_code=zip_code.strip(),
        address=address.strip() if address and address.strip() else None,
    )
    return result, f"Email Append: {first_name} {last_name}"


def prompt_reverse_email(console: Console, client: OneLookupClient) -> Optional[Tuple[Dict[str, Any], str]]:
    """Prompt for reverse email lookup."""
    print_back_hint(console)

    email = prompt_text(
        message="Enter email address:",
        validate=lambda x: (("@" in x) or x.strip().lower() == "back") or "Valid email address required",
    )

    if not email or not email.strip():
        return None

    console.print(f"[dim]Looking up details for: {email}[/dim]")
    return client.reverse_email_append(email.strip()), f"Reverse Email: {email.strip()}"


def prompt_reverse_ip(console: Console, client: OneLookupClient) -> Optional[Tuple[Dict[str, Any], str]]:
    """Prompt for reverse IP lookup."""
    print_back_hint(console)

    ip = prompt_text(
        message="Enter IP address:",
        validate=lambda x: (len(x.strip()) > 0 and x.strip().lower() != "back") or "IP address is required",
    )

    if not ip or not ip.strip():
        return None

    console.print(f"[dim]Looking up details for IP: {ip}[/dim]")
    return client.reverse_ip_append(ip.strip()), f"Reverse IP: {ip.strip()}"


def show_menu() -> int:
    """Main interactive menu loop."""
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
            elif command == "email-append":
                result, title = prompt_email_append(console, client)
            elif command == "reverse-email":
                result, title = prompt_reverse_email(console, client)
            elif command == "reverse-ip":
                result, title = prompt_reverse_ip(console, client)

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

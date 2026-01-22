#!/usr/bin/env python3
"""
Interactive menu UI for 1lookup API
Uses Rich for display and InquirerPy for interactive prompts
"""

import sys
from typing import Dict, Any, Optional

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


def prompt_ip_lookup(console: Console, client: OneLookupClient) -> Optional[Dict[str, Any]]:
    """Prompt for IP lookup."""
    ip = inquirer.text(
        message="Enter IP address:",
        validate=lambda x: len(x.strip()) > 0 or "IP address is required",
    ).execute()

    if not ip or not ip.strip():
        return None

    console.print(f"[dim]Looking up IP: {ip}[/dim]")
    return client.ip_lookup(ip.strip()), f"IP Lookup: {ip.strip()}"


def prompt_email_verify(console: Console, client: OneLookupClient) -> Optional[Dict[str, Any]]:
    """Prompt for email verification."""
    email = inquirer.text(
        message="Enter email address:",
        validate=lambda x: "@" in x or "Valid email address required",
    ).execute()

    if not email or not email.strip():
        return None

    console.print(f"[dim]Verifying email: {email}[/dim]")
    return client.email_verify(email.strip()), f"Email Verification: {email.strip()}"


def prompt_email_append(console: Console, client: OneLookupClient) -> Optional[Dict[str, Any]]:
    """Prompt for email append (find email from personal info)."""
    first_name = inquirer.text(
        message="First name:",
        validate=lambda x: len(x.strip()) > 0 or "First name is required",
    ).execute()

    last_name = inquirer.text(
        message="Last name:",
        validate=lambda x: len(x.strip()) > 0 or "Last name is required",
    ).execute()

    city = inquirer.text(
        message="City:",
        validate=lambda x: len(x.strip()) > 0 or "City is required",
    ).execute()

    zip_code = inquirer.text(
        message="ZIP code:",
        validate=lambda x: len(x.strip()) > 0 or "ZIP code is required",
    ).execute()

    address = inquirer.text(
        message="Street address (optional, press Enter to skip):",
    ).execute()

    console.print(f"[dim]Looking up email for: {first_name} {last_name} in {city}, {zip_code}[/dim]")
    result = client.email_append(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        city=city.strip(),
        zip_code=zip_code.strip(),
        address=address.strip() if address and address.strip() else None,
    )
    return result, f"Email Append: {first_name} {last_name}"


def prompt_reverse_email(console: Console, client: OneLookupClient) -> Optional[Dict[str, Any]]:
    """Prompt for reverse email lookup."""
    email = inquirer.text(
        message="Enter email address:",
        validate=lambda x: "@" in x or "Valid email address required",
    ).execute()

    if not email or not email.strip():
        return None

    console.print(f"[dim]Looking up details for: {email}[/dim]")
    return client.reverse_email_append(email.strip()), f"Reverse Email: {email.strip()}"


def prompt_reverse_ip(console: Console, client: OneLookupClient) -> Optional[Dict[str, Any]]:
    """Prompt for reverse IP lookup."""
    ip = inquirer.text(
        message="Enter IP address:",
        validate=lambda x: len(x.strip()) > 0 or "IP address is required",
    ).execute()

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
        command = inquirer.select(
            message="Select a command:",
            choices=get_command_choices(),
            pointer="❯",
        ).execute()

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

        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled[/dim]")
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
            console.print("\n[dim]Goodbye![/dim]")
            return 0


if __name__ == "__main__":
    sys.exit(show_menu())

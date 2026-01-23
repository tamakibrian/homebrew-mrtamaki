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


def get_risk_style(risk_level: str) -> str:
    """Get color style based on risk level."""
    risk_level = str(risk_level).lower()
    if risk_level in ("low", "none", "minimal"):
        return "green"
    elif risk_level in ("medium", "moderate"):
        return "yellow"
    elif risk_level in ("high", "elevated", "critical", "severe"):
        return "red"
    return "white"


def get_score_style(score: Any, inverse: bool = False) -> str:
    """Get color style based on numeric score (0-100). Set inverse=True for confidence scores."""
    try:
        score = float(score)
    except (ValueError, TypeError):
        return "white"

    if inverse:  # Higher is better (confidence)
        if score >= 70:
            return "green"
        elif score >= 40:
            return "yellow"
        return "red"
    else:  # Higher is worse (fraud/risk score)
        if score <= 30:
            return "green"
        elif score <= 60:
            return "yellow"
        return "red"


def format_value(value: Any, key: str = "") -> Tuple[str, str]:
    """Format a value and return (display_string, style)."""
    if value is None:
        return "-", "dim"

    key_lower = key.lower()
    str_val = str(value)

    # Risk level coloring
    if "risk_level" in key_lower or "threat_level" in key_lower:
        return str_val, get_risk_style(str_val)

    # Score coloring
    if "fraud_score" in key_lower or "risk_score" in key_lower:
        return str_val, get_score_style(value)
    if "confidence" in key_lower:
        return str_val, get_score_style(value, inverse=True)

    # Boolean coloring
    if isinstance(value, bool):
        if "is_threat" in key_lower or "is_proxy" in key_lower or "is_vpn" in key_lower or "is_tor" in key_lower:
            return str_val, "red" if value else "green"
        return str_val, "green" if value else "dim"

    # Lists
    if isinstance(value, list):
        if not value:
            return "-", "dim"
        return ", ".join(str(v) for v in value), "white"

    return str_val, "white"


def create_section_table(title: str, data: Dict[str, Any], style: str = "cyan") -> Table:
    """Create a styled table for a section."""
    table = Table(
        title=title,
        show_header=True,
        header_style=f"bold {style}",
        border_style=style,
        title_style=f"bold {style}",
        expand=True,
    )
    table.add_column("Field", style="dim", ratio=1)
    table.add_column("Value", ratio=2)

    for key, value in data.items():
        display_val, val_style = format_value(value, key)
        styled_val = Text(display_val, style=val_style)
        # Make key more readable
        display_key = key.replace("_", " ").title()
        table.add_row(display_key, styled_val)

    return table


def extract_nested(data: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    """Safely extract nested dictionary values."""
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, {})
        else:
            return {}
    return result if isinstance(result, dict) else {}


def print_result_table(console: Console, data: Dict[str, Any], title: str) -> None:
    """Print results in grouped sections with color-coded risk."""
    console.print(Panel(Text(title, style="bold white"), border_style="cyan"))
    console.print()

    # Detect lookup type from title
    is_ip_lookup = "IP Lookup" in title or "Reverse IP" in title
    is_email_lookup = "Email" in title

    # Extract common sections
    inner_data = data.get("data", data)
    request_info = extract_nested(data, "data", "request")
    metadata = extract_nested(data, "data", "metadata")
    risk_assessment = extract_nested(data, "data", "risk_assessment")
    geo_data = extract_nested(data, "data", "geo") or extract_nested(data, "data", "location")
    network_data = extract_nested(data, "data", "network") or extract_nested(data, "data", "asn")
    threat_data = extract_nested(data, "data", "threat") or extract_nested(data, "data", "threat_intel")

    # Top-level status
    if data.get("success") is not None:
        status_style = "green" if data.get("success") else "red"
        console.print(f"[{status_style}]Status: {'Success' if data.get('success') else 'Failed'}[/{status_style}]")
        console.print()

    # Risk Assessment Section (prioritize this at top for visibility)
    if risk_assessment:
        # Filter out deprecation-related fields
        risk_display = {k: v for k, v in risk_assessment.items()
                       if "deprecat" not in k.lower() and v is not None}
        if risk_display:
            console.print(create_section_table("Risk Assessment", risk_display, "red"))
            console.print()

    # Threat Intelligence
    if threat_data:
        threat_display = {k: v for k, v in threat_data.items() if v is not None}
        if threat_display:
            console.print(create_section_table("Threat Intelligence", threat_display, "yellow"))
            console.print()

    # Network/ASN Info
    if network_data:
        network_display = {k: v for k, v in network_data.items() if v is not None}
        if network_display:
            console.print(create_section_table("Network Info", network_display, "blue"))
            console.print()

    # Geolocation
    if geo_data:
        geo_display = {k: v for k, v in geo_data.items() if v is not None}
        if geo_display:
            console.print(create_section_table("Geolocation", geo_display, "magenta"))
            console.print()

    # Request Info (less important, show at bottom)
    if request_info:
        request_display = {k: v for k, v in request_info.items() if v is not None}
        if request_display:
            console.print(create_section_table("Request Info", request_display, "dim"))
            console.print()

    # Metadata (condensed, dimmed)
    if metadata:
        # Filter out verbose fields
        meta_display = {}
        skip_keys = {"deprecation_notice", "data_sources"}
        for k, v in metadata.items():
            if k not in skip_keys and not isinstance(v, dict) and v is not None:
                meta_display[k] = v
        if meta_display:
            console.print(create_section_table("Metadata", meta_display, "dim"))
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

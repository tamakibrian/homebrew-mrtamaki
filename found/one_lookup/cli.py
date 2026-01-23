#!/usr/bin/env python3
"""
CLI interface for 1lookup API
Called from zsh wrappers via: python -m one_lookup.cli <command> [args]
"""

import argparse
import json
import sys
from typing import Dict, Any

try:
    from rich.console import Console
    from rich import print as rprint

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .client import OneLookupClient
from .menu import show_menu, print_result_table


def print_error(message: str) -> None:
    """Print error message."""
    if RICH_AVAILABLE:
        console = Console(stderr=True)
        console.print(f"[red]Error:[/red] {message}")
    else:
        print(f"Error: {message}", file=sys.stderr)


def print_json(data: Dict[str, Any], raw: bool = False) -> None:
    """Print JSON data, optionally formatted."""
    if raw:
        print(json.dumps(data))
    else:
        if RICH_AVAILABLE:
            rprint(json.dumps(data, indent=2))
        else:
            print(json.dumps(data, indent=2))


def print_summary_table(data: Dict[str, Any], title: str) -> None:
    """Print a summary table using rich (grouped sections with color-coded risk)."""
    if not RICH_AVAILABLE:
        print_json(data)
        return

    console = Console()
    print_result_table(console, data, title)


def cmd_ip(args: argparse.Namespace) -> int:
    """Handle IP lookup command."""
    try:
        client = OneLookupClient(timeout=args.timeout)
        result = client.ip_lookup(args.ip)

        if result.get("error"):
            print_error(result.get("message", "Unknown error"))
            return 1

        if args.raw:
            print_json(result, raw=True)
        elif args.no_summary:
            print_json(result)
        else:
            print_summary_table(result, f"IP Lookup: {args.ip}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 2
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


def cmd_email(args: argparse.Namespace) -> int:
    """Handle email verification command."""
    try:
        client = OneLookupClient(timeout=args.timeout)
        result = client.email_verify(args.email)

        if result.get("error"):
            print_error(result.get("message", "Unknown error"))
            return 1

        if args.raw:
            print_json(result, raw=True)
        elif args.no_summary:
            print_json(result)
        else:
            print_summary_table(result, f"Email Verification: {args.email}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 2
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


def cmd_email_append(args: argparse.Namespace) -> int:
    """Handle email append command."""
    try:
        client = OneLookupClient(timeout=args.timeout)
        result = client.email_append(
            first_name=args.first,
            last_name=args.last,
            city=args.city,
            zip_code=args.zip,
            address=args.address,
        )

        if result.get("error"):
            print_error(result.get("message", "Unknown error"))
            return 1

        if args.raw:
            print_json(result, raw=True)
        elif args.no_summary:
            print_json(result)
        else:
            print_summary_table(result, f"Email Append: {args.first} {args.last}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 2
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


def cmd_reverse_email(args: argparse.Namespace) -> int:
    """Handle reverse email append command."""
    try:
        client = OneLookupClient(timeout=args.timeout)
        result = client.reverse_email_append(args.email)

        if result.get("error"):
            print_error(result.get("message", "Unknown error"))
            return 1

        if args.raw:
            print_json(result, raw=True)
        elif args.no_summary:
            print_json(result)
        else:
            print_summary_table(result, f"Reverse Email: {args.email}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 2
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


def cmd_reverse_ip(args: argparse.Namespace) -> int:
    """Handle reverse IP append command."""
    try:
        client = OneLookupClient(timeout=args.timeout)
        result = client.reverse_ip_append(args.ip)

        if result.get("error"):
            print_error(result.get("message", "Unknown error"))
            return 1

        if args.raw:
            print_json(result, raw=True)
        elif args.no_summary:
            print_json(result)
        else:
            print_summary_table(result, f"Reverse IP: {args.ip}")

        return 0

    except ValueError as e:
        print_error(str(e))
        return 2
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1


def cmd_menu(args: argparse.Namespace) -> int:
    """Launch interactive menu."""
    return show_menu()


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog="one_lookup", description="1lookup API CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Common arguments
    def add_common_args(p: argparse.ArgumentParser):
        p.add_argument("--raw", action="store_true", help="Output raw JSON")
        p.add_argument("--no-summary", action="store_true", help="Skip summary table")
        p.add_argument(
            "--timeout", type=int, default=10, help="Request timeout (seconds)"
        )

    # Menu (interactive mode)
    menu_parser = subparsers.add_parser("menu", help="Launch interactive menu")
    menu_parser.set_defaults(func=cmd_menu)

    # IP lookup
    ip_parser = subparsers.add_parser("ip", help="Look up IP address")
    ip_parser.add_argument("ip", help="IP address to look up")
    add_common_args(ip_parser)
    ip_parser.set_defaults(func=cmd_ip)

    # Email verification
    email_parser = subparsers.add_parser("email", help="Verify email address")
    email_parser.add_argument("email", help="Email address to verify")
    add_common_args(email_parser)
    email_parser.set_defaults(func=cmd_email)

    # Email append
    ea_parser = subparsers.add_parser(
        "email-append", help="Find email from personal info"
    )
    ea_parser.add_argument("--first", required=True, help="First name")
    ea_parser.add_argument("--last", required=True, help="Last name")
    ea_parser.add_argument("--city", required=True, help="City")
    ea_parser.add_argument("--zip", required=True, help="ZIP code")
    ea_parser.add_argument("--address", help="Street address (optional)")
    add_common_args(ea_parser)
    ea_parser.set_defaults(func=cmd_email_append)

    # Reverse email append
    re_parser = subparsers.add_parser("reverse-email", help="Find person from email")
    re_parser.add_argument("email", help="Email address to look up")
    add_common_args(re_parser)
    re_parser.set_defaults(func=cmd_reverse_email)

    # Reverse IP append
    ri_parser = subparsers.add_parser("reverse-ip", help="Find details from IP")
    ri_parser.add_argument("ip", help="IP address to look up")
    add_common_args(ri_parser)
    ri_parser.set_defaults(func=cmd_reverse_ip)

    args = parser.parse_args()

    # Default to menu if no command specified
    if args.command is None:
        return show_menu()

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

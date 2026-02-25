"""Lookup CLI: thin wrapper around one_lookup."""
import sys
from pathlib import Path

import typer

# Resolve found/ package (sibling to mrtamaki package)
_FOUND_DIR = Path(__file__).resolve().parents[2] / "found"
if str(_FOUND_DIR) not in sys.path:
    sys.path.insert(0, str(_FOUND_DIR))

app = typer.Typer(help="1Lookup API: IP, email, append lookups")


def _run_one_lookup(args: list) -> int:
    """Run one_lookup.cli with given args."""
    from one_lookup.cli import main
    return main(args)


@app.callback(invoke_without_command=True)
def lookup_callback(
    ctx: typer.Context,
):
    """1Lookup API — default: interactive menu."""
    if ctx.invoked_subcommand is None:
        raise typer.Exit(_run_one_lookup(["menu"]))


@app.command()
def menu():
    """Interactive 1Lookup menu."""
    raise typer.Exit(_run_one_lookup(["menu"]))


@app.command()
def ip(
    ip_addr: str = typer.Argument(...),
    raw: bool = typer.Option(False, "--raw"),
    no_summary: bool = typer.Option(False, "--no-summary"),
    timeout: int = typer.Option(10, "--timeout"),
):
    """IP lookup (iplookup)."""
    args = ["ip", ip_addr]
    if raw:
        args.append("--raw")
    if no_summary:
        args.append("--no-summary")
    args.extend(["--timeout", str(timeout)])
    raise typer.Exit(_run_one_lookup(args))


@app.command()
def email(
    email_addr: str = typer.Argument(...),
    raw: bool = typer.Option(False, "--raw"),
    no_summary: bool = typer.Option(False, "--no-summary"),
    timeout: int = typer.Option(10, "--timeout"),
):
    """Email verification (everify)."""
    args = ["email", email_addr]
    if raw:
        args.append("--raw")
    if no_summary:
        args.append("--no-summary")
    args.extend(["--timeout", str(timeout)])
    raise typer.Exit(_run_one_lookup(args))


@app.command()
def eappend(
    first_name: str = typer.Argument(...),
    last_name: str = typer.Argument(...),
    city: str = typer.Argument(...),
    zip_code: str = typer.Argument(...),
    address: str | None = typer.Option(None, "--address"),
):
    """Find email from person info."""
    args = ["eappend", first_name, last_name, city, zip_code]
    if address:
        args.extend(["--address", address])
    raise typer.Exit(_run_one_lookup(args))


@app.command()
def reappend(email: str = typer.Argument(...)):
    """Reverse email lookup."""
    raise typer.Exit(_run_one_lookup(["reappend", email]))


@app.command()
def ripappend(ip_addr: str = typer.Argument(...)):
    """Reverse IP lookup."""
    raise typer.Exit(_run_one_lookup(["ripappend", ip_addr]))

"""IP CLI: test, check, dnsleak (c3, d4, d6)."""
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import httpx
import typer

from mrtamaki._utils import (
    PORT_MAX,
    PORT_MIN,
    copy_to_clipboard,
    print_error,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(help="IP tools: test proxy, Scamalytics check, DNS leak")

_MRTAMAKI_ROOT = Path(__file__).resolve().parents[2]
NETWORK_TIMEOUT = 10


def _read_clipboard() -> str:
    try:
        return subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


@app.command()
def test(port: Optional[int] = typer.Argument(None, help="Proxy port; omit for system IP")):
    """Test proxy or system IP via ipinfo.io (c3)."""
    use_proxy = port is not None

    if use_proxy:
        if port < PORT_MIN or port > PORT_MAX:
            print_error(f"Invalid port. Must be between {PORT_MIN}-{PORT_MAX}")
            raise typer.Exit(1)
        print_info(f"Testing proxy on port {port}...")
    else:
        print_info("No port specified — checking system IP...")

    proxy = f"http://127.0.0.1:{port}" if use_proxy else None
    try:
        with httpx.Client(proxy=proxy, timeout=NETWORK_TIMEOUT) as client:
            r = client.get("https://ipinfo.io/json")
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        if use_proxy:
            print_error(f"No response from port {port}")
        else:
            print_error("No response from ipinfo.io")
        raise typer.Exit(1)
    except json.JSONDecodeError:
        print_error("Invalid response format")
        raise typer.Exit(1)

    ip = data.get("ip")
    if not ip:
        print_error("Could not parse IP from response")
        raise typer.Exit(1)

    # Display with Rich
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box

    console = Console()
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    fields = [
        ("ip", "IP Address"),
        ("hostname", "Hostname"),
        ("city", "City"),
        ("region", "Region"),
        ("country", "Country"),
        ("loc", "Location"),
        ("org", "Organization"),
        ("postal", "Postal"),
        ("timezone", "Timezone"),
    ]
    for key, label in fields:
        val = data.get(key)
        if val:
            table.add_row(label, str(val))

    title = "  Proxy IP Info" if use_proxy else "  System IP Info"
    console.print()
    console.print(Panel(table, title=f"[bold green]{title}[/]", border_style="green", box=box.ROUNDED))
    console.print()

    # Run DNS leak test
    typer.echo()
    _run_dnsleak(port)

    # Copy IP to clipboard
    typer.echo()
    if copy_to_clipboard(ip):
        print_info("Copied IP to clipboard ✓")


def _run_dnsleak(port: Optional[int]) -> None:
    """Run dnsleak subcommand (avoids circular import)."""
    dns_leak = _MRTAMAKI_ROOT / "dns_leak.py"
    if not dns_leak.exists():
        print_warning("dns_leak.py not found, skipping DNS leak test")
        return
    cmd = [sys.executable, str(dns_leak)]
    if port is not None:
        # With proxy: need proxychains4
        try:
            subprocess.run(["proxychains4", "--help"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_warning("proxychains4 not found — run without proxy or install: brew install proxychains-ng")
            return
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
            f.write("strict_chain\nproxy_dns\n[ProxyList]\n")
            f.write(f"http 127.0.0.1 {port}\n")
            f.flush()
            conf_path = f.name
        try:
            subprocess.run(["proxychains4", "-f", conf_path] + cmd, cwd=str(_MRTAMAKI_ROOT))
        finally:
            Path(conf_path).unlink(missing_ok=True)
    else:
        subprocess.run(cmd, cwd=str(_MRTAMAKI_ROOT))


@app.command()
def check(ip: Optional[str] = typer.Argument(None, help="IP to check; omit to use clipboard or system IP")):
    """Scamalytics IP reputation check (d4)."""
    api_key = os.environ.get("SCAMALYTICS_API_KEY")
    if not api_key:
        print_error("SCAMALYTICS_API_KEY not set")
        print_info("Add to ~/.zshenv: export SCAMALYTICS_API_KEY='your_key'")
        raise typer.Exit(1)

    if not ip:
        ip = _read_clipboard()
    if not ip:
        print_info("No IP specified — fetching system IP...")
        try:
            with httpx.Client(timeout=NETWORK_TIMEOUT) as client:
                r = client.get("https://ipinfo.io/json")
                r.raise_for_status()
                data = r.json()
                ip = data.get("ip", "")
        except Exception:
            print_error("Failed to fetch system IP from ipinfo.io")
            raise typer.Exit(1)
        if not ip:
            print_error("Could not parse system IP")
            raise typer.Exit(1)

    # Basic IP validation
    parts = ip.split(".")
    if len(parts) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
        print_error("Invalid IP address format")
        raise typer.Exit(1)

    print_info(f"Checking IP: {ip}")

    url = f"https://api11.scamalytics.com/v3/bradeysulley/?key={api_key}&ip={ip}"
    try:
        with httpx.Client(timeout=NETWORK_TIMEOUT) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError:
        print_error("Failed to retrieve IP information")
        raise typer.Exit(1)
    except json.JSONDecodeError:
        print_error("Invalid JSON response")
        raise typer.Exit(1)

    from rich.console import Console
    from rich import print as rprint
    rprint(json.dumps(data, indent=2))


@app.command()
def dnsleak(port: Optional[int] = typer.Argument(None, help="Proxy port; omit for system DNS")):
    """DNS leak test via dnscheck.tools (d6)."""
    _run_dnsleak(port)

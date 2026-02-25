"""IP CLI: test, check, dnsleak, iping."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import httpx
import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from mrtamaki import __version__
from mrtamaki._utils import (
    PORT_MAX,
    PORT_MIN,
    console,
    copy_to_clipboard,
    print_error,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(help="IP tools: test proxy, Scamalytics check, DNS leak")

_MRTAMAKI_ROOT = Path(__file__).resolve().parents[2]
NETWORK_TIMEOUT = 10
IPINFO_URL = "https://ipinfo.io/json"
IPING_URL = "https://api.iping.cc/v1/query"
IPING_HEADERS = {
    "Accept": "application/json",
    "User-Agent": f"mrtamaki/{__version__}",
}


def _read_clipboard() -> str:
    try:
        return subprocess.run(["pbpaste"], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _is_valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


# Panel style shared with proxy test flow (DNS Leak, Scamalytics)
_PROXY_TEST_ACCENT = "cyan"


def _render_info_panel(title: str, field_map: list[tuple[str, str]], data: dict) -> None:
    """Render a consistent bordered panel for IP metadata."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Field", style=f"bold {_PROXY_TEST_ACCENT}")
    table.add_column("Value", style="white")

    for key, label in field_map:
        value = data.get(key)
        if value not in (None, ""):
            table.add_row(label, str(value))

    console.print()
    console.print(Panel(table, title=f"[bold {_PROXY_TEST_ACCENT}]{title}[/]", border_style=_PROXY_TEST_ACCENT, box=box.ROUNDED))
    console.print()


def _fetch_ipinfo(proxy: Optional[str]) -> dict:
    with httpx.Client(proxy=proxy, timeout=NETWORK_TIMEOUT) as client:
        response = client.get(IPINFO_URL)
        response.raise_for_status()
        return response.json()


def _fetch_system_ip(proxy: Optional[str] = None) -> str:
    data = _fetch_ipinfo(proxy)
    ip = data.get("ip", "")
    if not ip:
        raise ValueError("Could not parse system IP")
    return ip


def _fetch_iping_data(ip: str, proxy: Optional[str]) -> dict:
    with httpx.Client(proxy=proxy, timeout=NETWORK_TIMEOUT, headers=IPING_HEADERS) as client:
        response = client.get(IPING_URL, params={"ip": ip, "language": "en"})
        response.raise_for_status()
        payload = response.json()

    if payload.get("code") != 200:
        raise ValueError(payload.get("msg") or "iping.cc returned non-success code")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("iping.cc returned invalid payload")
    return data


def _proxychains_binary() -> Optional[str]:
    for name in ("proxychains4", "proxychains"):
        if shutil.which(name):
            return name
    return None


@app.command()
def test(
    port: Optional[int] = typer.Argument(None, help="Proxy port; omit for system IP"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output results as JSON for export"),
):
    """Test proxy or system IP via ipinfo.io + iping.cc, then run DNS leak test."""
    use_proxy = port is not None

    if use_proxy:
        if port < PORT_MIN or port > PORT_MAX:
            print_error(f"Invalid port. Must be between {PORT_MIN}-{PORT_MAX}")
            raise typer.Exit(1)
        if not json_output:
            print_info(f"Testing proxy on port {port}...")
    else:
        if not json_output:
            print_info("No port specified — checking system IP...")

    proxy = f"http://127.0.0.1:{port}" if use_proxy else None
    try:
        ipinfo_data = _fetch_ipinfo(proxy)
    except httpx.HTTPError:
        if use_proxy:
            print_error(f"No response from port {port}")
        else:
            print_error("No response from ipinfo.io")
        raise typer.Exit(1)
    except json.JSONDecodeError:
        print_error("Invalid ipinfo.io response format")
        raise typer.Exit(1)

    ip = ipinfo_data.get("ip")
    if not ip:
        print_error("Could not parse IP from ipinfo.io response")
        raise typer.Exit(1)

    iping_data: Optional[dict] = None
    try:
        iping_data = _fetch_iping_data(ip, proxy)
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
        if not json_output:
            print_warning(f"iping.cc lookup unavailable: {exc}")

    if json_output:
        result: dict = {
            "port": port,
            "ipinfo": ipinfo_data,
            "iping": iping_data,
        }
        dns_result = _run_dnsleak_json(port)
        result["dns_leak"] = dns_result
        print(json.dumps(result, indent=2))
        return
    else:
        _render_info_panel(
            "Proxy IP Info" if use_proxy else "System IP Info",
            [
                ("ip", "IP Address"),
                ("hostname", "Hostname"),
                ("city", "City"),
                ("region", "Region"),
                ("country", "Country"),
                ("loc", "Location"),
                ("org", "Organization"),
                ("postal", "Postal"),
                ("timezone", "Timezone"),
            ],
            ipinfo_data,
        )

        if iping_data is not None:
            _render_info_panel(
                "Proxy IPing.cc Info" if use_proxy else "System IPing.cc Info",
                [
                    ("ip", "IP Address"),
                    ("continent", "Continent"),
                    ("country", "Country"),
                    ("region", "Region"),
                    ("city", "City"),
                    ("isp", "ISP"),
                    ("asn", "ASN"),
                    ("type", "Network Type"),
                    ("is_proxy", "Is Proxy"),
                    ("risk_score", "Risk Score"),
                    ("risk_tag", "Risk Tag"),
                    ("company", "Company"),
                ],
                iping_data,
            )

    # Run DNS leak test
    _run_dnsleak(port)

    # Copy IP to clipboard
    if copy_to_clipboard(ip):
        print_info("Copied IP to clipboard ✓")


def _run_dnsleak(port: Optional[int]) -> None:
    """Run dnsleak subcommand (avoids circular import)."""
    dns_leak = _MRTAMAKI_ROOT / "dns_leak.py"
    if not dns_leak.exists():
        print_warning("dns_leak.py not found, skipping DNS leak test")
        return

    cmd = [sys.executable, str(dns_leak)]
    result: Optional[subprocess.CompletedProcess] = None

    if port is not None:
        proxychains = _proxychains_binary()
        if not proxychains:
            print_error("proxychains-ng not found — install: brew install proxychains-ng")
            return

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as tmp:
            tmp.write("strict_chain\n")
            tmp.write("proxy_dns\n")
            tmp.write("quiet_mode\n")
            tmp.write("[ProxyList]\n")
            tmp.write(f"http 127.0.0.1 {port}\n")
            tmp.flush()
            conf_path = tmp.name

        print_info(f"Running DNS leak test via {proxychains} strict_chain on 127.0.0.1:{port}...")
        try:
            result = subprocess.run([proxychains, "-f", conf_path] + cmd, cwd=str(_MRTAMAKI_ROOT))
        finally:
            Path(conf_path).unlink(missing_ok=True)
    else:
        result = subprocess.run(cmd, cwd=str(_MRTAMAKI_ROOT))

    if result is not None and result.returncode != 0:
        print_warning("DNS leak test exited with non-zero status")


def _run_dnsleak_json(port: Optional[int]) -> dict:
    """Run dnsleak with --json, return parsed result dict."""
    dns_leak = _MRTAMAKI_ROOT / "dns_leak.py"
    if not dns_leak.exists():
        return {"error": "dns_leak.py not found"}

    cmd = [sys.executable, str(dns_leak), "--json"]
    result: Optional[subprocess.CompletedProcess] = None

    if port is not None:
        proxychains = _proxychains_binary()
        if not proxychains:
            return {"error": "proxychains-ng not found"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as tmp:
            tmp.write("strict_chain\n")
            tmp.write("proxy_dns\n")
            tmp.write("quiet_mode\n")
            tmp.write("[ProxyList]\n")
            tmp.write(f"http 127.0.0.1 {port}\n")
            tmp.flush()
            conf_path = tmp.name

        try:
            result = subprocess.run(
                [proxychains, "-f", conf_path] + cmd,
                cwd=str(_MRTAMAKI_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
        finally:
            Path(conf_path).unlink(missing_ok=True)
    else:
        result = subprocess.run(cmd, cwd=str(_MRTAMAKI_ROOT), capture_output=True, text=True, timeout=60)

    out = (result.stdout or "").strip() if result else ""
    if out:
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"error": out or "DNS leak test failed"}
    return {"error": "No output from DNS leak test"}


@app.command()
def check(
    ip: Optional[str] = typer.Argument(None, help="IP to check; omit to use clipboard or system IP"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output raw JSON for programmatic use"),
):
    """Scamalytics IP reputation check."""
    api_key = os.environ.get("SCAMALYTICS_API_KEY")
    if not api_key:
        print_error("SCAMALYTICS_API_KEY not set")
        print_info("Add to ~/.zshenv: export SCAMALYTICS_API_KEY='your_key'")
        raise typer.Exit(1)

    if not ip:
        ip = _read_clipboard()
    if not ip:
        if not json_output:
            print_info("No IP specified — fetching system IP...")
        try:
            ip = _fetch_system_ip()
        except Exception:
            print_error("Failed to fetch system IP from ipinfo.io")
            raise typer.Exit(1)

    if not _is_valid_ipv4(ip):
        print_error("Invalid IP address format")
        raise typer.Exit(1)

    if not json_output:
        print_info(f"Checking IP: {ip}")

    url = "https://api11.scamalytics.com/v3/bradeysulley/"
    try:
        with httpx.Client(timeout=NETWORK_TIMEOUT) as client:
            r = client.get(url, params={"key": api_key, "ip": ip})
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError:
        print_error("Failed to retrieve IP information")
        raise typer.Exit(1)
    except json.JSONDecodeError:
        print_error("Invalid JSON response")
        raise typer.Exit(1)

    if json_output:
        print(json.dumps(data, indent=2))
    else:
        from rich import print as rprint
        rprint(json.dumps(data, indent=2))


@app.command()
def dnsleak(port: Optional[int] = typer.Argument(None, help="Proxy port; omit for system DNS")):
    """DNS leak test via dnscheck.tools."""
    _run_dnsleak(port)


@app.command()
def iping(
    ip: Optional[str] = typer.Argument(None, help="IP to query; omit to use clipboard or system IP"),
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Optional local proxy port"),
):
    """Structured iping.cc lookup."""
    proxy = None
    if port is not None:
        if port < PORT_MIN or port > PORT_MAX:
            print_error(f"Invalid port. Must be between {PORT_MIN}-{PORT_MAX}")
            raise typer.Exit(1)
        proxy = f"http://127.0.0.1:{port}"

    if not ip:
        ip = _read_clipboard()
    if not ip:
        try:
            ip = _fetch_system_ip(proxy)
        except Exception:
            print_error("Failed to resolve IP for iping.cc query")
            raise typer.Exit(1)

    if not _is_valid_ipv4(ip):
        print_error("Invalid IP address format")
        raise typer.Exit(1)

    print_info(f"Querying iping.cc for {ip}...")
    try:
        data = _fetch_iping_data(ip, proxy)
    except (httpx.HTTPError, ValueError, json.JSONDecodeError) as exc:
        print_error(f"iping.cc lookup failed: {exc}")
        raise typer.Exit(1)

    _render_info_panel(
        "IPing.cc Info",
        [
            ("ip", "IP Address"),
            ("continent", "Continent"),
            ("country", "Country"),
            ("region", "Region"),
            ("city", "City"),
            ("isp", "ISP"),
            ("asn", "ASN"),
            ("type", "Network Type"),
            ("is_proxy", "Is Proxy"),
            ("risk_score", "Risk Score"),
            ("risk_tag", "Risk Tag"),
            ("company", "Company"),
            ("company_domain", "Company Domain"),
            ("as_owner", "AS Owner"),
            ("as_country", "AS Country"),
        ],
        data,
    )
    print_success("IPing.cc lookup complete")

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
        if value in (None, ""):
            continue
        if isinstance(value, str) and value.startswith("PREMIUM FIELD"):
            continue
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
    api_url = os.environ.get("SCAMALYTICS_API_KEY")
    if not api_url:
        print_error("SCAMALYTICS_API_KEY not set")
        print_info("Add to ~/.zshenv: export SCAMALYTICS_API_KEY='https://api11.scamalytics.com/v3/username/?key=your_key'")
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

    try:
        with httpx.Client(timeout=NETWORK_TIMEOUT) as client:
            r = client.get(f"{api_url}&ip={ip}")
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
        return

    sdata: dict = data.get("scamalytics", {})
    proxy_flags: dict = sdata.pop("scamalytics_proxy", {})
    sdata.pop("credits", None)
    display_data = {**sdata, **proxy_flags}

    # --- Scamalytics core ---
    _render_info_panel(
        "Scamalytics IP Check",
        [
            ("ip", "IP Address"),
            ("scamalytics_score", "Fraud Score"),
            ("scamalytics_risk", "Risk Level"),
            ("scamalytics_isp", "ISP"),
            ("scamalytics_org", "Organization"),
            ("scamalytics_isp_score", "ISP Score"),
            ("scamalytics_isp_risk", "ISP Risk"),
            ("scamalytics_url", "Report URL"),
            ("exec", "Query Time"),
        ],
        display_data,
    )

    external: dict = data.get("external_datasources", {}) if isinstance(data.get("external_datasources"), dict) else {}
    x4b: dict = external.get("x4bnet", {}) if isinstance(external.get("x4bnet"), dict) else {}
    firehol: dict = external.get("firehol", {}) if isinstance(external.get("firehol"), dict) else {}
    google_src: dict = external.get("google", {}) if isinstance(external.get("google"), dict) else {}

    # --- Proxy & Network Flags ---
    flag_data = {**proxy_flags}
    flag_data["is_tor"] = x4b.get("is_tor")
    flag_data["is_proxy_firehol"] = firehol.get("is_proxy")
    flag_data["x4b_datacenter"] = x4b.get("is_datacenter")
    flag_data["x4b_vpn"] = x4b.get("is_vpn")

    _render_info_panel(
        "Proxy & Network Flags",
        [
            ("is_datacenter", "Datacenter"),
            ("is_vpn", "VPN"),
            ("is_tor", "Tor"),
            ("is_apple_icloud_private_relay", "iCloud Relay"),
            ("is_amazon_aws", "Amazon AWS"),
            ("is_google", "Google"),
            ("is_proxy_firehol", "Proxy (FireHOL)"),
            ("x4b_datacenter", "Datacenter (x4bnet)"),
            ("x4b_vpn", "VPN (x4bnet)"),
        ],
        flag_data,
    )

    # --- Blacklist Status ---
    ipsum: dict = external.get("ipsum", {}) if isinstance(external.get("ipsum"), dict) else {}
    spamhaus: dict = external.get("spamhaus_drop", {}) if isinstance(external.get("spamhaus_drop"), dict) else {}
    ip2proxy_lite: dict = external.get("ip2proxy_lite", {}) if isinstance(external.get("ip2proxy_lite"), dict) else {}

    bl_data = {
        "is_blacklisted_external": display_data.get("is_blacklisted_external"),
        "firehol_30": firehol.get("ip_blacklisted_30"),
        "firehol_1day": firehol.get("ip_blacklisted_1day"),
        "ipsum_blacklisted": ipsum.get("ip_blacklisted"),
        "ipsum_count": ipsum.get("num_blacklists"),
        "spamhaus_blacklisted": spamhaus.get("ip_blacklisted"),
        "ip2proxy_blacklisted": ip2proxy_lite.get("ip_blacklisted"),
        "ip2proxy_type": ip2proxy_lite.get("proxy_type"),
        "x4b_spambot": x4b.get("is_blacklisted_spambot"),
    }

    _render_info_panel(
        "Blacklist Status",
        [
            ("is_blacklisted_external", "Blacklisted (Scamalytics)"),
            ("firehol_30", "FireHOL 30-day"),
            ("firehol_1day", "FireHOL 1-day"),
            ("ipsum_blacklisted", "IPsum"),
            ("ipsum_count", "IPsum Lists"),
            ("spamhaus_blacklisted", "Spamhaus DROP"),
            ("ip2proxy_blacklisted", "IP2Proxy"),
            ("ip2proxy_type", "IP2Proxy Type"),
            ("x4b_spambot", "Spambot (x4bnet)"),
        ],
        bl_data,
    )

    # --- Bot Detection ---
    bot_data = {
        "is_google_general": google_src.get("is_google_general"),
        "is_googlebot": google_src.get("is_googlebot"),
        "is_special_crawler": google_src.get("is_special_crawler"),
        "is_user_triggered_fetcher": google_src.get("is_user_triggered_fetcher"),
        "is_bot_operamini": x4b.get("is_bot_operamini"),
        "is_bot_semrush": x4b.get("is_bot_semrush"),
    }

    _render_info_panel(
        "Bot Detection",
        [
            ("is_google_general", "Google General"),
            ("is_googlebot", "Googlebot"),
            ("is_special_crawler", "Special Crawler"),
            ("is_user_triggered_fetcher", "User Fetcher"),
            ("is_bot_operamini", "OperaMini Bot"),
            ("is_bot_semrush", "SemRush Bot"),
        ],
        bot_data,
    )

    # --- Geolocation ---
    geo: dict = {}
    for src in ("maxmind_geolite2", "ipinfo", "ip2proxy_lite"):
        src_data = external.get(src, {})
        if isinstance(src_data, dict):
            geo.update({
                k: v for k, v in src_data.items()
                if v and not isinstance(v, dict)
                and not k.startswith(("datasource", "license", "last_updated", "history"))
            })

    if geo:
        _render_info_panel(
            "Geolocation",
            [
                ("ip_country_name", "Country"),
                ("ip_continent_name", "Continent"),
                ("ip_country_code", "Country Code"),
                ("ip_state_name", "State/Region"),
                ("ip_district_name", "District"),
                ("ip_city", "City"),
                ("ip_postcode", "Postcode"),
                ("asn", "ASN"),
                ("as_name", "AS Name"),
                ("as_domain", "AS Domain"),
                ("ip_range_from", "IP Range From"),
                ("ip_range_to", "IP Range To"),
                ("domain", "Domain"),
                ("usage_type", "Usage Type"),
                ("ip_geolocation", "Coordinates"),
                ("ip_location_accuracy_km", "Accuracy (km)"),
                ("ip_time_zone", "Timezone"),
            ],
            geo,
        )


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

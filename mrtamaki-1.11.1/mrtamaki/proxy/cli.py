"""Proxy CLI: iproyal, oxylabs, rapid, convert (a1, a2, a3, a4, a5, a6, b2)."""
import json
import os
import random
import re
import select
import secrets
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from typer.core import TyperGroup
from rich import box
from rich.panel import Panel
from rich.table import Table

from mrtamaki._utils import (
    console,
    copy_to_clipboard,
    print_error,
    print_info,
    print_success,
    print_warning,
)

class _ProxyGroup(TyperGroup):
    """Route unknown first arg (e.g. city) to convert: mt proxy auckland -> convert auckland."""

    def resolve_command(self, ctx, args):
        cmd_name = args[0] if args else None
        if cmd_name in self.commands:
            return super().resolve_command(ctx, args)
        if cmd_name and "convert" in self.commands:
            return ("convert", self.commands["convert"], args)
        return super().resolve_command(ctx, args)


app = typer.Typer(help="Proxy tools: IPRoyal, Oxylabs, Rapid, converter", cls=_ProxyGroup)

# Resolve mrtamaki source root (parent of mrtamaki package)
_MRTAMAKI_ROOT = Path(__file__).resolve().parents[2]
IPROYAL_PORTS = [51200, 32325, 12325]
OXYLABS_ENDPOINT = "pr.oxylabs.io:7777"
RAPIDPROXY_ENDPOINT = os.environ.get("RAPIDPROXY_ENDPOINT", "eu.rapidproxy.io:5001")
SUPPORTED_PROVIDERS = {"iproyal", "oxylabs", "rapid"}
_BIND_PORT_RE = re.compile(r"HTTP port (\d+)")


def _normalize_location(city: str, country: str) -> tuple[str, str]:
    """Normalize city/country for proxy provider URL formats."""
    city_norm = city.strip().lower().replace(" ", "-")
    country_norm = country.strip().lower()
    if not city_norm:
        raise ValueError("City cannot be empty")
    if not country_norm:
        raise ValueError("Country cannot be empty")
    return city_norm, country_norm


def _mask_proxy_url(proxy_url: str) -> str:
    """Mask credentials in proxy URL for safe terminal output."""
    if "@" not in proxy_url:
        return proxy_url
    creds, endpoint = proxy_url.rsplit("@", 1)
    if ":" not in creds:
        return f"********@{endpoint}"
    username = creds.split(":", 1)[0]
    return f"{username}:********@{endpoint}"


def _render_proxy_panel(title: str, rows: list[tuple[str, str]]) -> None:
    """Render a bordered panel for generated proxy output."""
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")
    for key, value in rows:
        table.add_row(key, value)

    console.print()
    console.print(Panel(table, title=f"[bold green]{title}[/]", border_style="green", box=box.ROUNDED))
    console.print()


def _render_generated_table(generated: list[dict], show_full: bool) -> None:
    """Show generated proxy URLs in a unified table."""
    table = Table(title="Generated Proxies", box=box.SIMPLE_HEAVY)
    table.add_column("#", style="bold cyan", no_wrap=True)
    table.add_column("Provider", style="green")
    table.add_column("City")
    table.add_column("Country")
    table.add_column("Session", style="magenta")
    table.add_column("Endpoint", style="cyan")
    table.add_column("Proxy", overflow="fold")

    for idx, item in enumerate(generated, start=1):
        proxy_value = item["proxy_url"] if show_full else _mask_proxy_url(item["proxy_url"])
        table.add_row(
            str(idx),
            item["provider"],
            item["city"],
            item["country"],
            item["session"],
            item["endpoint"],
            proxy_value,
        )
    console.print()
    console.print(table)
    console.print()


def _render_bound_table(bindings: list[dict]) -> None:
    """Show local bindings and related metadata."""
    table = Table(title="Bound Local Proxy Ports", box=box.SIMPLE_HEAVY)
    table.add_column("#", style="bold cyan", no_wrap=True)
    table.add_column("Provider", style="green")
    table.add_column("Port", style="bold yellow")
    table.add_column("City")
    table.add_column("Session", style="magenta")
    table.add_column("PID", style="cyan")

    for idx, item in enumerate(bindings, start=1):
        table.add_row(
            str(idx),
            item["provider"],
            str(item["port"]),
            item["city"],
            item["session"],
            str(item["proc"].pid),
        )

    console.print()
    console.print(table)
    console.print()


def _gen_iproyal_url(user: str, passwd: str, city: str, country: str = "nz") -> tuple[str, int]:
    """Generate IPRoyal proxy URL. Returns (url, port)."""
    lifetime = "168h"
    port = random.choice(IPROYAL_PORTS)
    endpoint = f"geo.iproyal.com:{port}"
    session = secrets.token_hex(4)  # 8 alphanumeric chars
    proxy_url = f"{user}:{passwd}_country-{country}_city-{city}_session-{session}_lifetime-{lifetime}@{endpoint}"
    return proxy_url, port


def _gen_oxylabs_url(user: str, passwd: str, city: str, country: str = "nz") -> str:
    """Generate Oxylabs proxy URL."""
    sesstime = "145"
    sessid = "".join(secrets.choice("0123456789") for _ in range(10))
    return f"customer-{user}-cc-{country}-city-{city}-sessid-{sessid}-sesstime-{sesstime}:{passwd}@{OXYLABS_ENDPOINT}"


def _gen_rapid_url(user: str, passwd: str, city: str, country: str = "nz") -> str:
    """Generate Rapid proxy URL. Format: USER-residential-NZ-state-Auckland-session-XXX-stime-180:PASS@endpoint"""
    session_id = "".join(secrets.choice("0123456789") for _ in range(8))
    stime = "180"
    country_upper = country.upper()
    state = city.replace("-", " ").title()
    return f"{user}-residential-{country_upper}-state-{state}-session-{session_id}-stime-{stime}:{passwd}@{RAPIDPROXY_ENDPOINT}"


def _run_proxy_converter(args: list[str]) -> int:
    """Run proxy_converter.py. Returns exit code."""
    converter_dir = _MRTAMAKI_ROOT / "proxy_converter"
    script = converter_dir / "proxy_converter.py"
    if not script.exists():
        print_error(f"proxy_converter.py not found: {script}")
        return 1
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        cwd=str(converter_dir),
    )
    return result.returncode


def _start_bound_proxy(proxy_url: str, debug: bool = False, timeout: int = 15) -> tuple[subprocess.Popen, int]:
    """Start converter with --wait and return (proc, local_port)."""
    converter_dir = _MRTAMAKI_ROOT / "proxy_converter"
    script = converter_dir / "proxy_converter.py"
    if not script.exists():
        raise RuntimeError(f"proxy_converter.py not found: {script}")

    cmd = [sys.executable, str(script), "--cli", "--bind", proxy_url, "--wait"]
    if debug:
        cmd.append("--debug")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        cmd,
        cwd=str(converter_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    assert proc.stdout is not None

    collected: list[str] = []
    deadline = time.time() + timeout
    while time.time() < deadline:
        remaining = max(0.0, deadline - time.time())
        ready, _, _ = select.select([proc.stdout], [], [], min(0.2, remaining))
        if not ready:
            if proc.poll() is not None:
                break
            continue

        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue

        collected.append(line.rstrip())
        match = _BIND_PORT_RE.search(line)
        if match:
            return proc, int(match.group(1))

    if proc.poll() is not None:
        # Drain any remaining output for diagnostics.
        tail = proc.stdout.read() or ""
        if tail.strip():
            collected.extend(tail.strip().splitlines())

    # Could not discover port; ensure process is not orphaned.
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    else:
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
    details = collected[-3:] if collected else ["no converter output"]
    raise RuntimeError("Failed to bind proxy and detect local port: " + " | ".join(details))


def _stop_processes(processes: list[subprocess.Popen]) -> None:
    """Terminate and reap running proxy converter processes."""
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
    for proc in processes:
        if proc.poll() is None:
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


def _read_clipboard() -> str:
    """Read from clipboard (macOS pbpaste)."""
    try:
        return subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def _run_mt_ip_test(port: int) -> int:
    """Run mt ip test <port>. Returns exit code."""
    return subprocess.run([sys.executable, "-m", "mrtamaki.cli", "ip", "test", str(port)]).returncode


def _run_ip_test_json(port: int) -> dict:
    """Run mt ip test --json <port>, return parsed result dict."""
    result = subprocess.run(
        [sys.executable, "-m", "mrtamaki.cli", "ip", "test", "--json", str(port)],
        capture_output=True,
        text=True,
        timeout=90,
    )
    out = (result.stdout or "").strip()
    if out:
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"error": out or "IP test failed"}
    return {"error": "No output from IP test"}


def _run_mt_ip_check(ip: Optional[str] = None) -> int:
    """Run mt ip check [ip]. Returns exit code."""
    cmd = [sys.executable, "-m", "mrtamaki.cli", "ip", "check"]
    if ip:
        cmd.append(ip)
    return subprocess.run(cmd).returncode


def _resolve_iproyal_credentials() -> tuple[str, str]:
    """Get IPRoyal credentials from env or prompt."""
    user = os.environ.get("IPROYAL_USER") or typer.prompt("IPRoyal username")
    passwd = os.environ.get("IPROYAL_PASS") or typer.prompt("IPRoyal password", hide_input=True)
    if not user or not passwd:
        raise RuntimeError("Credentials required. Set IPROYAL_USER and IPROYAL_PASS in ~/.zshenv")
    return user, passwd


def _resolve_oxylabs_credentials() -> tuple[str, str]:
    """Get Oxylabs credentials from env."""
    user = os.environ.get("OXYLABS_USER")
    passwd = os.environ.get("OXYLABS_PASS")
    if not user:
        raise RuntimeError("OXYLABS_USER not set in environment")
    if not passwd:
        raise RuntimeError("OXYLABS_PASS not set in environment")
    return user, passwd


def _resolve_rapid_credentials() -> tuple[str, str]:
    """Get Rapid proxy credentials from env or prompt."""
    user = os.environ.get("RAPIDPROXY_USER") or typer.prompt("Rapid proxy username")
    passwd = os.environ.get("RAPIDPROXY_PASS") or typer.prompt("Rapid proxy password", hide_input=True)
    if not user or not passwd:
        raise RuntimeError("Credentials required. Set RAPIDPROXY_USER and RAPIDPROXY_PASS in ~/.zshenv")
    return user, passwd


def _build_proxy(provider: str, city: str, country: str, creds: Optional[tuple[str, str]] = None) -> dict:
    """Generate one proxy URL payload for a provider."""
    if provider == "iproyal":
        user, passwd = creds or _resolve_iproyal_credentials()
        proxy_url, port = _gen_iproyal_url(user, passwd, city, country)
        session = proxy_url.split("_session-")[1][:8]
        endpoint = f"geo.iproyal.com:{port}"
    elif provider == "oxylabs":
        user, passwd = creds or _resolve_oxylabs_credentials()
        proxy_url = _gen_oxylabs_url(user, passwd, city, country)
        session = proxy_url.split("sessid-")[1].split("-")[0]
        endpoint = OXYLABS_ENDPOINT
    elif provider == "rapid":
        user, passwd = creds or _resolve_rapid_credentials()
        proxy_url = _gen_rapid_url(user, passwd, city, country)
        session = proxy_url.split("session-")[1].split("-")[0]
        endpoint = RAPIDPROXY_ENDPOINT
    else:
        raise RuntimeError(f"Unsupported provider: {provider}")
    return {
        "provider": provider,
        "city": city,
        "country": country,
        "session": session,
        "endpoint": endpoint,
        "proxy_url": proxy_url,
    }


def _do_speed_run(proxy_url: str) -> None:
    """Common speed run logic: bind proxy, test, check."""
    print_info("Binding proxy...")
    try:
        proc, port = _start_bound_proxy(proxy_url)
    except RuntimeError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    print_info(f"Proxy bound on port {port}")

    # Run mt ip test (includes ipinfo/iping + DNS leak)
    if _run_mt_ip_test(port) != 0:
        print_warning("IP test returned a non-zero status")

    # Run mt ip check with IP from clipboard (c3 puts it there)
    ip_from_clipboard = _read_clipboard()
    if ip_from_clipboard and _run_mt_ip_check(ip_from_clipboard) != 0:
        print_warning("Scamalytics IP check returned a non-zero status")

    http_proxy = f"127.0.0.1:{port}"
    copy_to_clipboard(http_proxy)
    print_success(f"HTTP proxy copied to clipboard: {http_proxy}")

    console.print(f"   Proxy PID: {proc.pid}")
    console.print(f"   Port:      {port}")
    console.print("   Press Ctrl+C to stop proxy server")
    console.print()

    try:
        proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        _stop_processes([proc])


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def iproyal(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City (default: christchurch)"),
    country: Optional[str] = typer.Argument(None, help="Country code (default: nz)"),
):
    """Generate IPRoyal proxy URL (a1)."""
    city = city or "christchurch"
    country = country or "nz"
    try:
        city, country = _normalize_location(city, country)
        user, passwd = _resolve_iproyal_credentials()
    except (RuntimeError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    proxy_url, port = _gen_iproyal_url(user, passwd, city, country)
    session = proxy_url.split("_session-")[1][:8]
    ok = copy_to_clipboard(proxy_url)
    if not ok:
        print_warning("Failed to copy to clipboard")

    _render_proxy_panel(
        "IPRoyal Proxy Generated",
        [
            ("Provider", "IPRoyal"),
            ("City", city),
            ("Country", country),
            ("Session", session),
            ("Port", str(port)),
            ("Proxy URL", _mask_proxy_url(proxy_url)),
        ],
    )

    if ok:
        print_success("Copied full proxy URL to clipboard")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def oxylabs(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City (default: auckland)"),
    country: Optional[str] = typer.Argument(None, help="Country code (default: nz)"),
    show_full: bool = typer.Option(False, "--show-full"),
):
    """Generate Oxylabs proxy URL (a2)."""
    city = city or "auckland"
    country = country or "nz"
    try:
        city, country = _normalize_location(city, country)
        user, passwd = _resolve_oxylabs_credentials()
    except (RuntimeError, ValueError) as exc:
        print_error(str(exc))
        if "OXYLABS_USER" in str(exc):
            print_info("Add to ~/.zshenv: export OXYLABS_USER='your_customer_id'")
        if "OXYLABS_PASS" in str(exc):
            print_info("Add to ~/.zshenv: export OXYLABS_PASS='your_password'")
        raise typer.Exit(1)

    proxy_url = _gen_oxylabs_url(user, passwd, city, country)
    session = proxy_url.split("sessid-")[1].split("-")[0]
    ok = copy_to_clipboard(proxy_url)
    if not ok:
        print_warning("Failed to copy to clipboard")

    _render_proxy_panel(
        "Oxylabs Proxy Generated",
        [
            ("Provider", "Oxylabs"),
            ("City", city),
            ("Country", country),
            ("Session", session),
            ("Port", "7777"),
            ("Proxy URL", proxy_url if show_full else _mask_proxy_url(proxy_url)),
        ],
    )

    if ok:
        print_success("Copied full proxy URL to clipboard")
    if not show_full:
        print_info("Use --show-full if you need the complete proxy URL in output")


@app.command("iproyal-speed", context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def iproyal_speed(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City (default: christchurch)"),
    country: Optional[str] = typer.Argument(None, help="Country code (default: nz)"),
):
    """IPRoyal speed run: generate → bind → test → check (a5)."""
    city = city or "christchurch"
    country = country or "nz"
    try:
        city, country = _normalize_location(city, country)
        user, passwd = _resolve_iproyal_credentials()
    except (RuntimeError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    proxy_url, port = _gen_iproyal_url(user, passwd, city, country)
    copy_to_clipboard(proxy_url)

    _render_proxy_panel(
        "IPRoyal Speed Run",
        [
            ("Provider", "IPRoyal"),
            ("City", city),
            ("Country", country),
            ("Session", proxy_url.split("_session-")[1][:8]),
            ("Port", str(port)),
            ("Proxy URL", _mask_proxy_url(proxy_url)),
        ],
    )

    _do_speed_run(proxy_url)


@app.command("oxylabs-speed", context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def oxylabs_speed(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City (default: auckland)"),
    country: Optional[str] = typer.Argument(None, help="Country code (default: nz)"),
    show_full: bool = typer.Option(False, "--show-full"),
):
    """Oxylabs speed run (a6)."""
    city = city or "auckland"
    country = country or "nz"
    try:
        city, country = _normalize_location(city, country)
        user, passwd = _resolve_oxylabs_credentials()
    except (RuntimeError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    proxy_url = _gen_oxylabs_url(user, passwd, city, country)
    copy_to_clipboard(proxy_url)

    _render_proxy_panel(
        "Oxylabs Speed Run",
        [
            ("Provider", "Oxylabs"),
            ("City", city),
            ("Country", country),
            ("Session", proxy_url.split("sessid-")[1].split("-")[0]),
            ("Port", "7777"),
            ("Proxy URL", proxy_url if show_full else _mask_proxy_url(proxy_url)),
        ],
    )

    _do_speed_run(proxy_url)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def rapid(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City (default: auckland)"),
    country: Optional[str] = typer.Argument(None, help="Country code (default: nz)"),
    show_full: bool = typer.Option(False, "--show-full"),
):
    """Generate Rapid proxy URL (residential format) (a3)."""
    city = city or "auckland"
    country = country or "nz"
    try:
        city, country = _normalize_location(city, country)
        user, passwd = _resolve_rapid_credentials()
    except (RuntimeError, ValueError) as exc:
        print_error(str(exc))
        if "RAPIDPROXY" in str(exc):
            print_info("Add to ~/.zshenv: export RAPIDPROXY_USER='...' RAPIDPROXY_PASS='...'")
        raise typer.Exit(1)

    proxy_url = _gen_rapid_url(user, passwd, city, country)
    session = proxy_url.split("session-")[1].split("-")[0]
    ok = copy_to_clipboard(proxy_url)
    if not ok:
        print_warning("Failed to copy to clipboard")

    _render_proxy_panel(
        "Rapid Proxy Generated",
        [
            ("Provider", "Rapid"),
            ("City", city),
            ("Country", country),
            ("Session", session),
            ("Endpoint", RAPIDPROXY_ENDPOINT),
            ("Proxy URL", proxy_url if show_full else _mask_proxy_url(proxy_url)),
        ],
    )

    if ok:
        print_success("Copied full proxy URL to clipboard")
    if not show_full:
        print_info("Use --show-full to print full proxy URL in output")


@app.command("rapid-speed", context_settings={"allow_extra_args": True, "ignore_unknown_options": False})
def rapid_speed(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City (default: auckland)"),
    country: Optional[str] = typer.Argument(None, help="Country code (default: nz)"),
):
    """Rapid speed run: generate → bind → test → check (a4)."""
    city = city or "auckland"
    country = country or "nz"
    try:
        city, country = _normalize_location(city, country)
        user, passwd = _resolve_rapid_credentials()
    except (RuntimeError, ValueError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    proxy_url = _gen_rapid_url(user, passwd, city, country)
    copy_to_clipboard(proxy_url)

    session = proxy_url.split("session-")[1].split("-")[0]
    _render_proxy_panel(
        "Rapid Speed Run",
        [
            ("Provider", "Rapid"),
            ("City", city),
            ("Country", country),
            ("Session", session),
            ("Endpoint", RAPIDPROXY_ENDPOINT),
            ("Proxy URL", _mask_proxy_url(proxy_url)),
        ],
    )

    _do_speed_run(proxy_url)


def _prompt_provider() -> str:
    """Prompt user to choose provider when city is given without -p."""
    choice = typer.prompt(
        "Provider (iproyal/oxylabs/rapid)",
        default="iproyal",
        show_default=True,
    )
    p = choice.strip().lower()
    if p not in SUPPORTED_PROVIDERS:
        raise typer.BadParameter(f"Use iproyal, oxylabs, or rapid, got: {choice}")
    return p


@app.command()
def convert(
    city_arg: Optional[str] = typer.Argument(None, help="City (prompts for provider if -p not set)"),
    count_arg: Optional[int] = typer.Argument(None, help="Count: bind N proxies (add -k to run checks)"),
    bind: Optional[str] = typer.Option(None, "--bind", "-b"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Generate proxy URL(s): iproyal, oxylabs, or rapid"),
    city: str = typer.Option("auckland", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
    count: int = typer.Option(1, "--count", "--bulk", "-n", min=1),
    bind_generated: bool = typer.Option(False, "--bind-generated", "-B"),
    list_proxies: bool = typer.Option(False, "--list", "--ls", "-l"),
    clean: bool = typer.Option(False, "--clean"),
    debug: bool = typer.Option(False, "--debug", "-d"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Keep bindings running until Ctrl+C (default: on)"),
    do_check: bool = typer.Option(False, "--check", "-k", help="Run IP/DNS checks (with -b or when count_arg given)"),
    show_full: bool = typer.Option(False, "--show-full"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save check results to JSON file (bulk mode)"),
):
    """Proxy converter (b2). Supports bind, bulk generation, and checks.

    Modes:
      (no args)      Interactive TUI
      <city>         City only → prompts for provider, then bind 1
      <city> <n>     City + count → prompts for provider, bind n (add -k to check)
      -l / --list    List bound proxies
      --clean        Remove ~/.bindproxy.json
      -b <url>       Bind proxy URL
      -p <provider> Bind 1 generated proxy (default)
      -p <provider> <city> <n>  Bind n (add -k to run checks)

    Bindings stay running until Ctrl+C by default. Use --no-wait to stop immediately.

    Examples:
      b2                    Interactive menu
      b2 wellington         City only → choose provider → bind 1
      b2 wellington 10      City + count → bind 10 (no checks)
      b2 wellington 10 -k   Bind 10 and run IP/DNS checks
      b2 -p iproyal wellington 10 -k   Bind 10 Wellington proxies and check
    """
    bindproxy_path = Path.home() / ".bindproxy.json"

    if clean:
        if bindproxy_path.exists():
            bindproxy_path.unlink()
            print_success("Removed ~/.bindproxy.json")
        else:
            print_info("No ~/.bindproxy.json found")
        raise typer.Exit(0)

    if provider and bind:
        print_error("Use either --provider or --bind, not both")
        raise typer.Exit(1)

    # city_arg overrides -c/--city when provided
    if city_arg:
        city = city_arg.strip()

    # b2 <city> [count]: prompt for provider, then bind (1 or count)
    if city_arg and not provider and not bind and not list_proxies:
        n = max(1, count_arg) if count_arg is not None else 1
        try:
            provider = _prompt_provider()
            city, country = _normalize_location(city, country)
        except (typer.BadParameter, ValueError) as exc:
            print_error(str(exc))
            raise typer.Exit(1)
        creds = None
        try:
            if provider == "iproyal":
                creds = _resolve_iproyal_credentials()
            elif provider == "oxylabs":
                creds = _resolve_oxylabs_credentials()
            elif provider == "rapid":
                creds = _resolve_rapid_credentials()
        except RuntimeError as exc:
            print_error(str(exc))
            raise typer.Exit(1)
        generated = [_build_proxy(provider, city, country, creds=creds) for _ in range(n)]
        _render_generated_table(generated, show_full=show_full)
        copy_to_clipboard("\n".join(item["proxy_url"] for item in generated))
        bindings: list[dict] = []
        try:
            for idx, item in enumerate(generated, start=1):
                print_info(f"Binding proxy {idx}/{n}...")
                proc, port = _start_bound_proxy(item["proxy_url"], debug=debug)
                bindings.append({"proc": proc, "port": port, "provider": item["provider"], "city": item["city"], "session": item["session"]})
        except RuntimeError as exc:
            _stop_processes([b["proc"] for b in bindings])
            print_error(str(exc))
            raise typer.Exit(1)
        _render_bound_table(bindings)
        if do_check:
            results = []
            for entry in bindings:
                port = entry["port"]
                print_info(f"Running IP + DNS checks on port {port}...")
                data = _run_ip_test_json(port)
                results.append({
                    "port": port,
                    "provider": entry["provider"],
                    "city": entry["city"],
                    "session": entry["session"],
                    "ipinfo": data.get("ipinfo"),
                    "iping": data.get("iping"),
                    "dns_leak": data.get("dns_leak"),
                    "error": data.get("error"),
                })
            out_path = output or str(Path.home() / "Desktop" / f"mrtamaki-proxy-checks-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
            Path(out_path).write_text(json.dumps({"checks": results}, indent=2), encoding="utf-8")
            print_success(f"Check results saved to {out_path}")
        if wait:
            print_info("Press Ctrl+C to stop proxy server(s).")
            try:
                while True:
                    time.sleep(1)
                    if all(b["proc"].poll() is not None for b in bindings):
                        break
            except KeyboardInterrupt:
                pass
        else:
            print_info("Stopping bindings (use -w to keep running).")
        _stop_processes([b["proc"] for b in bindings])
        raise typer.Exit(0)

    if provider:
        provider = provider.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            print_error(f"Unsupported provider '{provider}'. Use: iproyal, oxylabs, or rapid")
            raise typer.Exit(1)
        try:
            city, country = _normalize_location(city, country)
        except ValueError as exc:
            print_error(str(exc))
            raise typer.Exit(1)

        # <city> <n> or count_arg: bind n and check
        if count_arg is not None:
            count = max(1, count_arg)
            bind_generated = True
        # -p alone (no -B, no -n>1): bind 1
        elif not bind_generated and count == 1:
            bind_generated = True

        creds: Optional[tuple[str, str]] = None
        try:
            if provider == "iproyal":
                creds = _resolve_iproyal_credentials()
            elif provider == "oxylabs":
                creds = _resolve_oxylabs_credentials()
            elif provider == "rapid":
                creds = _resolve_rapid_credentials()
        except RuntimeError as exc:
            print_error(str(exc))
            raise typer.Exit(1)

        generated: list[dict] = []
        for _ in range(count):
            try:
                generated.append(_build_proxy(provider, city, country, creds=creds))
            except RuntimeError as exc:
                print_error(str(exc))
                raise typer.Exit(1)

        _render_generated_table(generated, show_full=show_full)

        payload = "\n".join(item["proxy_url"] for item in generated)
        copied = copy_to_clipboard(payload)
        if copied:
            if len(generated) == 1:
                print_success("Copied full proxy URL to clipboard")
            else:
                print_success(f"Copied {len(generated)} proxy URLs to clipboard")
        else:
            print_warning("Failed to copy generated proxy URL(s) to clipboard")

        if count_arg is not None and not bind_generated:
            bind_generated = True

        if not bind_generated:
            if not show_full:
                print_info("Use --show-full to print full proxy URL(s) in output")
            raise typer.Exit(0)

        bindings: list[dict] = []
        try:
            for idx, item in enumerate(generated, start=1):
                print_info(f"Binding generated proxy {idx}/{len(generated)}...")
                proc, port = _start_bound_proxy(item["proxy_url"], debug=debug)
                bindings.append(
                    {
                        "proc": proc,
                        "port": port,
                        "provider": item["provider"],
                        "city": item["city"],
                        "session": item["session"],
                    }
                )
        except RuntimeError as exc:
            _stop_processes([entry["proc"] for entry in bindings])
            print_error(str(exc))
            raise typer.Exit(1)

        _render_bound_table(bindings)

        if do_check:
            results = []
            for entry in bindings:
                port = entry["port"]
                print_info(f"Running IP + DNS checks on port {port}...")
                data = _run_ip_test_json(port)
                results.append({
                    "port": port,
                    "provider": entry["provider"],
                    "city": entry["city"],
                    "session": entry["session"],
                    "ipinfo": data.get("ipinfo"),
                    "iping": data.get("iping"),
                    "dns_leak": data.get("dns_leak"),
                    "error": data.get("error"),
                })
            out_path = output or str(Path.home() / "Desktop" / f"mrtamaki-proxy-checks-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
            Path(out_path).write_text(json.dumps({"checks": results}, indent=2), encoding="utf-8")
            print_success(f"Check results saved to {out_path}")

        if wait:
            print_info("Bindings are active. Press Ctrl+C to stop all bound proxies.")
            try:
                while True:
                    time.sleep(1)
                    if all(entry["proc"].poll() is not None for entry in bindings):
                        break
            except KeyboardInterrupt:
                pass
        else:
            print_info("Stopping bindings (use --no-wait to stop immediately next time).")

        _stop_processes([entry["proc"] for entry in bindings])
        raise typer.Exit(0)

    args: list[str] = []
    if debug:
        args.append("--debug")

    if list_proxies:
        args.extend(["--cli", "--list"])
        raise typer.Exit(_run_proxy_converter(args))

    if bind:
        if do_check or wait:
            try:
                proc, port = _start_bound_proxy(bind, debug=debug)
            except RuntimeError as exc:
                print_error(str(exc))
                raise typer.Exit(1)
            print_success(f"Proxy bound on local port {port}")
            if do_check:
                print_info(f"Running IP + DNS checks on port {port}...")
                if _run_mt_ip_test(port) != 0:
                    print_warning(f"Checks returned non-zero status on port {port}")

            if wait:
                print_info("Binding is active. Press Ctrl+C to stop proxy server.")
                try:
                    proc.wait()
                except KeyboardInterrupt:
                    pass
            _stop_processes([proc])
            raise typer.Exit(0)

        args.extend(["--cli", "--bind", bind])
        raise typer.Exit(_run_proxy_converter(args))

    if do_check and not bind and not provider:
        print_error("--check requires --bind or --provider")
        raise typer.Exit(1)

    # No flags — interactive TUI
    print_info("Launching proxy converter...")
    raise typer.Exit(_run_proxy_converter(args))

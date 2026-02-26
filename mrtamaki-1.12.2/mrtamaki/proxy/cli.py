"""Proxy CLI — unified proxy command (mt proxy)."""
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

import httpx
import typer
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
from mrtamaki.proxy.gen_menu import run_provider_menu


app = typer.Typer(help="Proxy tools: generate, bind, test, and check proxies", invoke_without_command=True, context_settings={"allow_interspersed_args": True})

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


PROXY_PROBE_URL = "https://ipinfo.io/json"
PROXY_PROBE_TIMEOUT = 15
PROXY_READY_MAX_WAIT = 45
PROXY_READY_POLL_INTERVAL = 2
CHECK_RETRY_ATTEMPTS = 3
CHECK_RETRY_DELAY = 3


def _probe_proxy_ready(port: int) -> bool:
    """Quick probe: can we reach ipinfo.io through the proxy?"""
    try:
        with httpx.Client(
            proxy=f"http://127.0.0.1:{port}",
            timeout=PROXY_PROBE_TIMEOUT,
        ) as client:
            r = client.get(PROXY_PROBE_URL)
            return r.status_code == 200
    except Exception:
        return False


def _wait_for_proxy_ready(port: int, max_wait_sec: int = PROXY_READY_MAX_WAIT) -> bool:
    """Poll until proxy accepts connections or timeout. Returns True if ready."""
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        if _probe_proxy_ready(port):
            return True
        time.sleep(PROXY_READY_POLL_INTERVAL)
    return False


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
            data = json.loads(out)
            if data.get("ipinfo") or data.get("error"):
                return data
        except json.JSONDecodeError:
            pass
        return {"error": out[:500] if len(out) > 500 else out}
    err = (result.stderr or "").strip()
    hint = f" (stderr: {err[:200]})" if err else ""
    return {"error": f"No output from IP test (exit {result.returncode}){hint}"}


def _run_ip_test_json_robust(port: int) -> dict:
    """Wait for proxy ready, then run IP test with retries. Foolproof bulk checks."""
    if not _wait_for_proxy_ready(port):
        return {"error": f"Proxy on port {port} not ready after {PROXY_READY_MAX_WAIT}s"}
    for attempt in range(1, CHECK_RETRY_ATTEMPTS + 1):
        data = _run_ip_test_json(port)
        if data.get("ipinfo"):
            return data
        if attempt < CHECK_RETRY_ATTEMPTS:
            time.sleep(CHECK_RETRY_DELAY)
    return data


def _run_mt_ip_check(ip: Optional[str] = None) -> int:
    """Run mt ip check [ip]. Returns exit code."""
    cmd = [sys.executable, "-m", "mrtamaki.cli", "ip", "check"]
    if ip:
        cmd.append(ip)
    return subprocess.run(cmd).returncode


def _run_scamalytics_json(ip: str) -> dict:
    """Run mt ip check --json <ip>, return parsed Scamalytics result dict."""
    result = subprocess.run(
        [sys.executable, "-m", "mrtamaki.cli", "ip", "check", "--json", ip],
        capture_output=True,
        text=True,
        timeout=30,
    )
    out = (result.stdout or "").strip()
    if out:
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"error": out or "Scamalytics check failed"}
    return {"error": "No output from Scamalytics check"}


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


def _do_speed_run(proxy_url: str, timeout: int = 15) -> None:
    """Common speed run logic: bind proxy, test, check."""
    print_info("Binding proxy...")
    try:
        proc, port = _start_bound_proxy(proxy_url, timeout=timeout)
    except RuntimeError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    print_info(f"Proxy bound on port {port}")

    # Run mt ip test (includes ipinfo/iping + DNS leak)
    if _run_mt_ip_test(port) != 0:
        print_warning("IP test returned a non-zero status")

    # Run mt ip check with IP from clipboard (ip test copies it there)
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


def _do_gen_from_provider(
    provider: str,
    city: str,
    country: str,
    speed_run: bool,
    count: int = 1,
    do_check: bool = False,
    output: Optional[str] = None,
    wait: bool = True,
    timeout: int = 15,
) -> None:
    """Generate proxy URL(s) for provider, optionally bind and run checks."""
    try:
        city, country = _normalize_location(city, country)
    except ValueError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

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

    n = max(1, count)
    generated = [_build_proxy(provider, city, country, creds=creds) for _ in range(n)]

    if n == 1 and not speed_run:
        item = generated[0]
        proxy_url = item["proxy_url"]
        copy_to_clipboard(proxy_url)
        provider_title = provider.replace("-", " ").title()
        port_str = (item.get("endpoint") or "").split(":")[-1] or "7777"
        _render_proxy_panel(
            f"{provider_title} Proxy Generated",
            [
                ("Provider", provider_title),
                ("City", city),
                ("Country", country),
                ("Session", item["session"]),
                ("Port", port_str),
                ("Proxy URL", _mask_proxy_url(proxy_url)),
            ],
        )
        print_success("Copied full proxy URL to clipboard")
        return

    if n == 1 and speed_run:
        item = generated[0]
        proxy_url = item["proxy_url"]
        copy_to_clipboard(proxy_url)
        provider_title = provider.replace("-", " ").title()
        port_str = (item.get("endpoint") or "").split(":")[-1] or "7777"
        _render_proxy_panel(
            f"{provider_title} Speed Run",
            [
                ("Provider", provider_title),
                ("City", city),
                ("Country", country),
                ("Session", item["session"]),
                ("Port", port_str),
                ("Proxy URL", _mask_proxy_url(proxy_url)),
            ],
        )
        _do_speed_run(proxy_url, timeout=timeout)
        return

    # Bulk: n > 1 with speed_run
    _render_generated_table(generated, show_full=False)
    copy_to_clipboard("\n".join(item["proxy_url"] for item in generated))

    bindings: list[dict] = []
    try:
        for idx, item in enumerate(generated, start=1):
            print_info(f"Binding proxy {idx}/{n}...")
            proc, port = _start_bound_proxy(item["proxy_url"], timeout=timeout)
            bindings.append({
                "proc": proc,
                "port": port,
                "provider": item["provider"],
                "city": item["city"],
                "session": item["session"],
            })
    except RuntimeError as exc:
        _stop_processes([b["proc"] for b in bindings])
        print_error(str(exc))
        raise typer.Exit(1)

    _render_bound_table(bindings)

    if do_check:
        results = []
        for entry in bindings:
            port = entry["port"]
            print_info(f"Running IP + DNS + Scamalytics checks on port {port}...")
            data = _run_ip_test_json_robust(port)
            ipinfo = data.get("ipinfo") or {}
            ip = ipinfo.get("ip")
            scamalytics = _run_scamalytics_json(ip) if ip else {"error": "No IP from ipinfo"}
            results.append({
                "port": port,
                "provider": entry["provider"],
                "city": entry["city"],
                "session": entry["session"],
                "ipinfo": data.get("ipinfo"),
                "iping": data.get("iping"),
                "dns_leak": data.get("dns_leak"),
                "scamalytics": scamalytics,
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
        print_info("Stopping bindings (use --wait to keep running).")
    _stop_processes([b["proc"] for b in bindings])


@app.callback(invoke_without_command=True)
def proxy_cmd(
    ctx: typer.Context,
    city: Optional[str] = typer.Argument(None, help="City to generate proxy for (e.g. auckland)"),
    count: Optional[int] = typer.Argument(None, help="Number of proxies to generate (with -s)"),
    speed: bool = typer.Option(False, "-s", "--speed", help="Speed run: generate + bind + test"),
    bind: Optional[str] = typer.Option(None, "-b", "--bind", help="Bind a proxy URL to localhost"),
    port: Optional[int] = typer.Option(None, "-p", "--port", help="Test proxy on given port", min=1, max=65535),
    check: bool = typer.Option(False, "--check", "-k", help="Run IP + DNS + Scamalytics checks"),
    provider: Optional[str] = typer.Option(None, "--provider", help="Skip provider menu: iproyal, oxylabs, rapid"),
    country: str = typer.Option("nz", "--country", help="Country code"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Save check results to JSON file"),
    list_proxies: bool = typer.Option(False, "-l", "--list", help="List bound proxies"),
    clean: bool = typer.Option(False, "--clean", help="Remove bound proxy config"),
    wait: bool = typer.Option(True, "--wait/--no-wait", help="Keep proxy running until Ctrl+C"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Debug output"),
    show_full: bool = typer.Option(False, "--show-full", help="Show full proxy URLs (unmasked)"),
    timeout: int = typer.Option(15, "-t", "--timeout", help="Connection timeout in seconds", min=1),
):
    """Proxy tools — generate, bind, test, and check proxies.

    \b
    Examples:
      mt proxy                            Proxy converter TUI
      mt proxy auckland                   Provider menu → generate for auckland
      mt proxy -s auckland                Speed run: gen → bind → test
      mt proxy -s auckland --check        Speed run + IP/DNS/Scamalytics checks
      mt proxy -s auckland 10 --check     Bulk: 10 proxies → bind → check
      mt proxy -b <url>                   Bind a proxy URL
      mt proxy -p 8080                    Test proxy on port 8080
      mt proxy -l                         List bound proxies
      mt proxy --clean                    Remove bound proxy config
      mt proxy --provider iproyal auckland  Skip provider menu
    """
    # --- Test proxy on port (-p) ---
    if port is not None:
        _run_mt_ip_test(port)
        if check:
            ip_from_clipboard = _read_clipboard()
            if ip_from_clipboard:
                _run_mt_ip_check(ip_from_clipboard)
        raise typer.Exit(0)

    # --- List bound proxies (-l) ---
    if list_proxies:
        args: list[str] = []
        if debug:
            args.append("--debug")
        args.extend(["--cli", "--list"])
        raise typer.Exit(_run_proxy_converter(args))

    # --- Clean bound proxy config (--clean) ---
    if clean:
        bindproxy_path = Path.home() / ".bindproxy.json"
        if bindproxy_path.exists():
            bindproxy_path.unlink()
            print_success("Removed ~/.bindproxy.json")
        else:
            print_info("No ~/.bindproxy.json found")
        raise typer.Exit(0)

    # --- Bind a user-provided proxy URL (-b) ---
    if bind:
        if provider:
            print_error("Use either --provider or -b, not both")
            raise typer.Exit(1)
        try:
            proc, local_port = _start_bound_proxy(bind, debug=debug, timeout=timeout)
        except RuntimeError as exc:
            print_error(str(exc))
            raise typer.Exit(1)
        print_success(f"Proxy bound on local port {local_port}")
        if check:
            print_info(f"Running IP + DNS checks on port {local_port}...")
            if _run_mt_ip_test(local_port) != 0:
                print_warning(f"IP test returned non-zero status on port {local_port}")
            ip_from_clipboard = _read_clipboard()
            if ip_from_clipboard:
                if _run_mt_ip_check(ip_from_clipboard) != 0:
                    print_warning("Scamalytics check returned non-zero status")
        if wait:
            print_info("Press Ctrl+C to stop proxy server.")
            try:
                proc.wait()
            except KeyboardInterrupt:
                pass
        _stop_processes([proc])
        raise typer.Exit(0)

    # --- No city → launch proxy converter TUI ---
    if city is None:
        args = []
        if debug:
            args.append("--debug")
        raise typer.Exit(_run_proxy_converter(args))

    # --- City given → generate proxy ---
    n = max(1, count) if count is not None else 1

    if n > 1 and not speed:
        print_error("Bulk count requires -s/--speed (e.g. mt proxy -s auckland 10)")
        raise typer.Exit(1)

    # Resolve provider (interactive menu or --provider flag)
    selected_provider: Optional[str] = None
    if provider:
        selected_provider = provider.strip().lower()
        if selected_provider not in SUPPORTED_PROVIDERS:
            print_error(f"Unknown provider '{selected_provider}'. Use: iproyal, oxylabs, rapid")
            raise typer.Exit(1)
    else:
        selected_provider = run_provider_menu(
            city=city,
            country=country,
            speed_run=speed or n > 1,
            console=console,
        )
        if not selected_provider:
            print_info("Cancelled")
            raise typer.Exit(0)

    _do_gen_from_provider(
        selected_provider,
        city,
        country,
        speed_run=speed,
        count=n,
        do_check=check,
        output=output,
        wait=wait,
        timeout=timeout,
    )

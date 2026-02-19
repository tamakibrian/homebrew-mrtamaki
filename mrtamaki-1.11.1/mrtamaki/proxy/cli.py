"""Proxy CLI: iproyal, oxylabs, convert (a1, a2, a3, a4, b2)."""
import os
import random
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import typer

from mrtamaki._utils import (
    copy_to_clipboard,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)

app = typer.Typer(help="Proxy tools: IPRoyal, Oxylabs, converter")

# Resolve mrtamaki source root (parent of mrtamaki package)
_MRTAMAKI_ROOT = Path(__file__).resolve().parents[2]
IPROYAL_PORTS = [51200, 32325, 12325]


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
    endpoint = "pr.oxylabs.io:7777"
    sessid = "".join(secrets.choice("0123456789") for _ in range(10))
    return f"customer-{user}-cc-{country}-city-{city}-sessid-{sessid}-sesstime-{sesstime}:{passwd}@{endpoint}"


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


def _run_mt_ip_check(ip: Optional[str] = None) -> int:
    """Run mt ip check [ip]. Returns exit code."""
    cmd = [sys.executable, "-m", "mrtamaki.cli", "ip", "check"]
    if ip:
        cmd.append(ip)
    return subprocess.run(cmd).returncode


@app.command()
def iproyal(
    city: str = typer.Option("christchurch", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
):
    """Generate IPRoyal proxy URL (a1)."""
    user = os.environ.get("IPROYAL_USER") or typer.prompt("IPRoyal username")
    passwd = os.environ.get("IPROYAL_PASS")
    if not passwd:
        passwd = typer.prompt("IPRoyal password", hide_input=True)

    if not user or not passwd:
        print_error("Credentials required. Set IPROYAL_USER and IPROYAL_PASS in ~/.zshenv")
        raise typer.Exit(1)

    proxy_url, port = _gen_iproyal_url(user, passwd, city, country)
    ok = copy_to_clipboard(proxy_url)
    if not ok:
        print_warning("Failed to copy to clipboard")

    print_header("IPRoyal Proxy Generated")
    typer.echo(f"   City:    {city}")
    typer.echo(f"   Session: {proxy_url.split('_session-')[1][:8]}")
    typer.echo(f"   Port:    {port}")
    typer.echo()
    typer.echo(proxy_url)
    typer.echo()
    if ok:
        print_success("Copied to clipboard!")


@app.command()
def oxylabs(
    city: str = typer.Option("auckland", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
):
    """Generate Oxylabs proxy URL (a2)."""
    user = os.environ.get("OXYLABS_USER")
    passwd = os.environ.get("OXYLABS_PASS")

    if not user:
        print_error("OXYLABS_USER not set in environment")
        print_info("Add to ~/.zshenv: export OXYLABS_USER='your_customer_id'")
        raise typer.Exit(1)
    if not passwd:
        print_error("OXYLABS_PASS not set in environment")
        print_info("Add to ~/.zshenv: export OXYLABS_PASS='your_password'")
        raise typer.Exit(1)

    proxy_url = _gen_oxylabs_url(user, passwd, city, country)
    ok = copy_to_clipboard(proxy_url)
    if not ok:
        print_warning("Failed to copy to clipboard")

    sessid = proxy_url.split("sessid-")[1].split("-")[0]
    print_header("Oxylabs Proxy Generated")
    typer.echo(f"   City:    {city}")
    typer.echo(f"   Session: {sessid}")
    typer.echo()
    typer.echo(proxy_url)
    typer.echo()
    if ok:
        print_success("Copied to clipboard!")


def _do_speed_run(proxy_url: str):
    """Common speed run logic: bind proxy, test, check."""
    print_info("Binding proxy...")
    proc = subprocess.Popen(
        [sys.executable, str(_MRTAMAKI_ROOT / "proxy_converter" / "proxy_converter.py"), "--cli", "--bind", proxy_url, "--wait"],
        cwd=str(_MRTAMAKI_ROOT / "proxy_converter"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(3)

    if proc.poll() is not None:
        print_error("Proxy converter failed to start")
        raise typer.Exit(1)

    port_str = _read_clipboard()
    if not port_str.isdigit():
        print_error(f"Expected port number on clipboard, got: {port_str}")
        proc.terminate()
        raise typer.Exit(1)

    port = int(port_str)
    print_info(f"Proxy bound on port {port}")

    # Run mt ip test
    _run_mt_ip_test(port)

    # Run mt ip check with IP from clipboard (c3 puts it there)
    ip_from_clipboard = _read_clipboard()
    _run_mt_ip_check(ip_from_clipboard)

    http_proxy = f"127.0.0.1:{port}"
    copy_to_clipboard(http_proxy)
    print_success(f"HTTP proxy copied to clipboard: {http_proxy}")

    typer.echo()
    typer.echo(f"   Proxy PID: {proc.pid}")
    typer.echo(f"   Port:      {port}")
    typer.echo("   Press Ctrl+C to stop proxy server")
    typer.echo()

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


@app.command("iproyal-speed")
def iproyal_speed(
    city: str = typer.Option("christchurch", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
):
    """IPRoyal speed run: generate → bind → test → check (a3)."""
    user = os.environ.get("IPROYAL_USER") or typer.prompt("IPRoyal username")
    passwd = os.environ.get("IPROYAL_PASS") or typer.prompt("IPRoyal password", hide_input=True)
    if not user or not passwd:
        print_error("Credentials required.")
        raise typer.Exit(1)

    proxy_url, port = _gen_iproyal_url(user, passwd, city, country)
    copy_to_clipboard(proxy_url)

    typer.echo()
    print_header("IPRoyal Speed Run")
    typer.echo(f"   City:    {city}")
    typer.echo(f"   Session: {proxy_url.split('_session-')[1][:8]}")
    typer.echo(f"   Port:    {port}")
    typer.echo()

    _do_speed_run(proxy_url)


@app.command("oxylabs-speed")
def oxylabs_speed(
    city: str = typer.Option("auckland", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
):
    """Oxylabs speed run (a4)."""
    user = os.environ.get("OXYLABS_USER")
    passwd = os.environ.get("OXYLABS_PASS")
    if not user or not passwd:
        print_error("OXYLABS_USER and OXYLABS_PASS required in ~/.zshenv")
        raise typer.Exit(1)

    proxy_url = _gen_oxylabs_url(user, passwd, city, country)
    sessid = proxy_url.split("sessid-")[1].split("-")[0]
    copy_to_clipboard(proxy_url)

    typer.echo()
    print_header("Oxylabs Speed Run")
    typer.echo(f"   City:    {city}")
    typer.echo(f"   Session: {sessid}")
    typer.echo()

    _do_speed_run(proxy_url)


@app.command()
def convert(
    bind: Optional[str] = typer.Option(None, "--bind", "-b"),
    list_proxies: bool = typer.Option(False, "--list", "--ls", "-l"),
    clean: bool = typer.Option(False, "--clean", "-c"),
    debug: bool = typer.Option(False, "--debug", "-d"),
    wait: bool = typer.Option(False, "--wait", "-w"),
    check: bool = typer.Option(False, "--check", "-k"),
):
    """Proxy converter (b2). No args = interactive TUI."""
    bindproxy_path = Path.home() / ".bindproxy.json"

    if clean:
        if bindproxy_path.exists():
            bindproxy_path.unlink()
            print_success("Removed ~/.bindproxy.json")
        else:
            print_info("No ~/.bindproxy.json found")
        raise typer.Exit(0)

    converter_dir = _MRTAMAKI_ROOT / "proxy_converter"
    script = converter_dir / "proxy_converter.py"
    if not script.exists():
        print_error(f"proxy_converter.py not found: {script}")
        raise typer.Exit(1)

    args: list[str] = []
    if debug:
        args.append("--debug")

    if list_proxies:
        args.extend(["--cli", "--list"])
        raise typer.Exit(_run_proxy_converter(args))

    if bind:
        args.extend(["--cli", "--bind", bind])
        if wait:
            args.append("--wait")
        raise typer.Exit(_run_proxy_converter(args))

    # No flags — interactive TUI
    print_info("Launching proxy converter...")
    raise typer.Exit(_run_proxy_converter(args))

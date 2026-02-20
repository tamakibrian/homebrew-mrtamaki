#!/usr/bin/env python3
"""DNS leak test using dnscheck.tools (addr.tools).

Connects to the dnscheck.tools WebSocket watcher, fires DNS queries via dig,
collects resolver IPs, and prints formatted results. Uses Rich for UI.
Use --json to output results as JSON for export.
"""

import argparse
import base64
import json
import os
import random
import socket
import ssl
import struct
import subprocess
import sys
import threading
import time
import urllib.request

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def _print_info(msg: str) -> None:
    console.print(f"[cyan]ℹ[/cyan] {msg}")


def _print_success(msg: str) -> None:
    console.print(f"[green]✓[/green] {msg}")


def _print_error(msg: str) -> None:
    console.print(f"[red]✗[/red] {msg}", style="red")


def _print_warning(msg: str) -> None:
    console.print(f"[yellow]⚠[/yellow] {msg}")


# ── Minimal WebSocket client (RFC 6455, stdlib only) ─────────────────────────

class WebSocket:
    """Minimal WebSocket client — connect, receive text frames, close."""

    def __init__(self, host, path, subprotocol=None, timeout=15):
        self._sock = socket.create_connection((host, 443), timeout=timeout)
        ctx = ssl.create_default_context()
        self._sock = ctx.wrap_socket(self._sock, server_hostname=host)
        self._sock.settimeout(timeout)

        # Perform HTTP upgrade handshake
        ws_key = base64.b64encode(os.urandom(16)).decode()
        lines = [
            f"GET {path} HTTP/1.1",
            f"Host: {host}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {ws_key}",
            "Sec-WebSocket-Version: 13",
        ]
        if subprotocol:
            lines.append(f"Sec-WebSocket-Protocol: {subprotocol}")
        lines += ["", ""]
        self._sock.sendall("\r\n".join(lines).encode())

        # Read response headers
        buf = b""
        while b"\r\n\r\n" not in buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed: connection closed")
            buf += chunk

        status_line = buf.split(b"\r\n", 1)[0].decode()
        if "101" not in status_line:
            raise ConnectionError(f"WebSocket handshake failed: {status_line}")

        # Any data after headers is part of the first frame
        self._pending = buf.split(b"\r\n\r\n", 1)[1]

    def _recv_exact(self, n):
        """Read exactly n bytes from socket + pending buffer."""
        data = b""
        if self._pending:
            take = min(n, len(self._pending))
            data = self._pending[:take]
            self._pending = self._pending[take:]
        while len(data) < n:
            chunk = self._sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data

    def recv(self):
        """Receive one text frame. Returns str or None on close."""
        header = self._recv_exact(2)
        opcode = header[0] & 0x0F
        masked = bool(header[1] & 0x80)
        length = header[1] & 0x7F

        if length == 126:
            length = struct.unpack(">H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._recv_exact(8))[0]

        if masked:
            mask = self._recv_exact(4)

        payload = self._recv_exact(length) if length else b""

        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

        if opcode == 0x8:  # Close
            return None
        if opcode == 0x9:  # Ping → send pong
            self._send_frame(0xA, payload)
            return self.recv()
        if opcode == 0x1:  # Text
            return payload.decode("utf-8", errors="replace")
        # Skip binary/continuation frames
        return self.recv()

    def _send_frame(self, opcode, payload=b""):
        """Send a masked WebSocket frame."""
        mask_key = os.urandom(4)
        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

        header = bytes([0x80 | opcode])
        plen = len(payload)
        if plen < 126:
            header += bytes([0x80 | plen])
        elif plen < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", plen)
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", plen)

        self._sock.sendall(header + mask_key + masked)

    def close(self):
        try:
            self._send_frame(0x8)
        except Exception:
            pass
        try:
            self._sock.close()
        except Exception:
            pass


# ── Resolver info lookup ─────────────────────────────────────────────────────

def lookup_resolver_info(ip, timeout=5):
    """Fetch resolver metadata via ipinfo.io (hostname, org, country)."""
    info = {"ip": ip, "hostname": "—", "org": "—", "country": "—"}
    try:
        req = urllib.request.Request(
            f"https://ipinfo.io/{ip}/json",
            headers={"Accept": "application/json", "User-Agent": "mrtamaki-dns-leak/1"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            info["hostname"] = data.get("hostname", "—")
            info["org"] = data.get("org", "—")
            info["country"] = data.get("country", "—")
    except Exception:
        pass
    return info


# ── Main DNS leak test ───────────────────────────────────────────────────────

def run_test(json_mode: bool = False):
    # Generate random client ID (up to 8 hex digits)
    client_id = format(random.randint(0, 0xFFFFFFFF), "x")
    resolvers = {}  # ip -> ws message data
    ws_ready = threading.Event()
    ws_error = [None]
    stop_flag = threading.Event()

    def ws_listener():
        try:
            ws = WebSocket(
                "ws.dnscheck.tools",
                f"/watch/{client_id}",
                subprotocol="full",
                timeout=30,
            )
            ws_ready.set()

            while not stop_flag.is_set():
                try:
                    ws._sock.settimeout(1.5)
                    msg = ws.recv()
                    if msg is None:
                        break
                    data = json.loads(msg)
                    ip = data.get("remoteIp", "")
                    if ip and ip not in resolvers:
                        resolvers[ip] = data
                except socket.timeout:
                    continue
                except Exception:
                    break
            ws.close()
        except Exception as e:
            ws_error[0] = str(e)
            ws_ready.set()

    # Start WebSocket listener in background
    listener = threading.Thread(target=ws_listener, daemon=True)
    listener.start()

    if not json_mode:
        _print_info("Connecting to dnscheck.tools...")

    if not ws_ready.wait(timeout=15):
        if json_mode:
            return 1, {"error": "Timed out connecting to dnscheck.tools"}
        _print_error("Timed out connecting to dnscheck.tools")
        return 1, None

    if ws_error[0]:
        if json_mode:
            return 1, {"error": f"WebSocket error: {ws_error[0]}"}
        _print_error(f"WebSocket error: {ws_error[0]}")
        return 1, None

    if not json_mode:
        _print_info("Running DNS queries...")

    # Fire DNS queries — each with a unique prefix label to avoid caching
    for i in range(10):
        try:
            subprocess.run(
                ["dig", f"{i}.{client_id}.test.dnscheck.tools", "+short"],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass
        time.sleep(0.15)

    # Wait for resolver responses to arrive
    if not json_mode:
        _print_info("Collecting results...")
    time.sleep(3)
    stop_flag.set()
    listener.join(timeout=5)

    if not resolvers:
        if json_mode:
            return 1, {"error": "No DNS resolvers detected"}
        _print_warning("No DNS resolvers detected. Try again.")
        return 1, None

    # Look up info for each resolver
    resolver_infos = []
    for ip in resolvers:
        info = lookup_resolver_info(ip)
        resolver_infos.append(info)

    # Determine leak status based on unique organizations
    unique_orgs = set()
    for info in resolver_infos:
        org = info["org"]
        if org and org != "—":
            unique_orgs.add(org)

    leak_detected = len(unique_orgs) > 1

    if json_mode:
        data = {
            "resolvers": resolver_infos,
            "unique_orgs": sorted(unique_orgs),
            "leak_detected": leak_detected,
        }
        return 0, data

    # Render resolver table in same style as ipinfo/iping (Panel + Table)
    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    table.add_column("IP", style="bold cyan")
    table.add_column("Hostname", style="white")
    table.add_column("Org", style="white")
    table.add_column("Country", style="white")

    for info in resolver_infos:
        table.add_row(
            info["ip"],
            info["hostname"] or "—",
            info["org"] or "—",
            info["country"] or "—",
        )

    console.print()
    console.print(Panel(table, title="[bold green]  DNS Leak Test  [/]", border_style="green", box=box.ROUNDED))
    console.print()

    if len(unique_orgs) <= 1:
        _print_success("No DNS leak — all queries through single provider")
    else:
        _print_warning(f"Possible DNS leak — {len(unique_orgs)} different DNS providers detected")
        for org in sorted(unique_orgs):
            console.print(f"  [dim]→[/dim] {org}")

    return 0, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DNS leak test via dnscheck.tools")
    parser.add_argument("--json", action="store_true", help="Output results as JSON (for export)")
    args = parser.parse_args()

    try:
        code, data = run_test(json_mode=args.json)
        if args.json and data is not None:
            print(json.dumps(data, indent=2))
        elif args.json and data is None and code != 0:
            print(json.dumps({"error": "DNS leak test failed"}), file=sys.stderr)
        sys.exit(code)
    except KeyboardInterrupt:
        print()
        sys.exit(130)

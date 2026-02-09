#!/usr/bin/env python3
"""
Proxy tool.
"""

import os
import sys
import re
import json
import random
import threading
import signal
import socket
import socks
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlparse
import base64
import argparse
import ssl
import select
import dns.resolver
import dns.name
import dns.query
import dns.message
import time
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

# UI menu import
from menu_ui import ProxyMenu

console = Console()

# Strict proxy pattern
PROXY_RE = re.compile(
    r'^(?P<user>[^:]+):(?P<pass>[^@]+)@(?P<host>(?:\[[0-9A-Fa-f:]+\]|[A-Za-z0-9.\-]+)):(?P<port>\d+)$'
)

PROXY_DATA_FILE = os.path.expanduser("~/.bindproxy.json")
PROXIES = {}
DEBUG = False
SOCKET_TIMEOUT = 30


def dprint(msg):
    if DEBUG:
        console.log(msg)


def copy_port_to_clipboard(port: int):
    """macOS clipboard + notification"""
    port_str = str(port)
    applescript = f'''
        set thePort to "{port_str}"
        set the clipboard to thePort
        display notification "Port " & thePort & " copied to clipboard" with title "Proxy Port"
    '''
    try:
        subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["pbcopy"],
                input=port_str,
                text=True,
                capture_output=True,
                check=True
            )
            subprocess.run(
                ["osascript", "-e", f'display notification "Port {port_str} copied to clipboard" with title "Proxy Port"']
            )
        except Exception as e:
            print(f"Clipboard/notification failed: {e}")


def cloudflare_dns_query(hostname):
    """Direct DNS query to Cloudflare"""
    try:
        query = dns.message.make_query(hostname, dns.rdatatype.A)
        query.flags |= dns.flags.RD
        query.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)
        query.want_dnssec = True

        response = dns.query.udp(query, '1.1.1.1', timeout=2)
        for answer in response.answer:
            for item in answer.items:
                if item.rdtype == dns.rdatatype.A:
                    return item.address
        return resolve_doh(hostname)
    except Exception:
        return resolve_doh(hostname)


def resolve_doh(hostname):
    """Cloudflare DoH"""
    try:
        import http.client
        import urllib.parse

        conn = http.client.HTTPSConnection("cloudflare-dns.com")
        params = urllib.parse.urlencode({
            'name': hostname,
            'type': 'A',
            'do': 'true',
            'cd': 'false'
        })

        headers = {
            'Accept': 'application/dns-json',
            'User-Agent': 'cloudflare-dns-client/1.0'
        }

        conn.request('GET', f'/dns-query?{params}', headers=headers)
        response = conn.getresponse()

        if response.status == 200:
            result = json.loads(response.read().decode())
            if 'Answer' in result:
                for ans in result['Answer']:
                    if ans['type'] == 1:
                        return ans['data']

        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['1.1.1.1', '1.0.0.1']
        answers = resolver.resolve(hostname, 'A')
        if answers:
            return answers[0].address

    except Exception:
        try:
            return socket.gethostbyname(hostname)
        except:
            return hostname


class CloudflareDNSSocket(socks.socksocket):
    """SOCKS socket with Cloudflare DNS resolution"""
    def resolve(self, destination):
        hostname, port = destination
        try:
            ip_address = cloudflare_dns_query(hostname)
            return (ip_address, port)
        except Exception:
            return super().resolve(destination)


class SocksHTTPConnection(HTTPConnection):
    def __init__(self, host, port=None, **kwargs):
        self.proxy_host = kwargs.pop('proxy_host', None)
        self.proxy_port = kwargs.pop('proxy_port', None)
        self.proxy_username = kwargs.pop('proxy_username', None)
        self.proxy_password = kwargs.pop('proxy_password', None)
        super().__init__(host, port, **kwargs)
        try:
            self._resolved_ip = cloudflare_dns_query(host)
        except:
            self._resolved_ip = None

    def connect(self):
        try:
            self.sock = CloudflareDNSSocket()
            self.sock.settimeout(SOCKET_TIMEOUT)
            self.sock.set_proxy(
                proxy_type=socks.SOCKS5,
                addr=self.proxy_host,
                port=self.proxy_port,
                username=self.proxy_username,
                password=self.proxy_password,
                rdns=False
            )
            if self._resolved_ip:
                self.sock.connect((self._resolved_ip, self.port))
            else:
                self.sock.connect((self.host, self.port))

        except Exception as e:
            dprint(f"SOCKS connection error: {e}")
            raise


class SocksHTTPSConnection(HTTPSConnection):
    def __init__(self, host, port=None, **kwargs):
        self.proxy_host = kwargs.pop('proxy_host', None)
        self.proxy_port = kwargs.pop('proxy_port', None)
        self.proxy_username = kwargs.pop('proxy_username', None)
        self.proxy_password = kwargs.pop('proxy_password', None)
        super().__init__(host, port, **kwargs)

        try:
            self._resolved_ip = cloudflare_dns_query(host)
        except:
            self._resolved_ip = None

    def connect(self):
        try:
            raw = CloudflareDNSSocket()
            raw.settimeout(SOCKET_TIMEOUT)
            raw.set_proxy(
                proxy_type=socks.SOCKS5,
                addr=self.proxy_host,
                port=self.proxy_port,
                username=self.proxy_username,
                password=self.proxy_password,
                rdns=False
            )
            if self._resolved_ip:
                raw.connect((self._resolved_ip, self.port))
            else:
                raw.connect((self.host, self.port))

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.sock = context.wrap_socket(raw, server_hostname=self.host)

        except Exception as e:
            dprint(f"SOCKS+SSL error: {e}")
            raise


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, proxy_string=None, **kwargs):
        self.proxy_string = proxy_string
        super().__init__(*args, **kwargs)

    def parse_proxy(self):
        match = re.match(r'^(.*?):(.*?)@(.*?):(\d+)$', self.proxy_string)
        if not match:
            return None
        username, password, server, port = match.groups()
        return {
            'username': username,
            'password': password,
            'server': server,
            'port': int(port)
        }

    def do_GET(self):
        self.do_method("GET")

    def do_POST(self):
        self.do_method("POST")

    def do_method(self, method):
        proxy = self.parse_proxy()
        if not proxy:
            self.send_error(400, "Invalid proxy format")
            return

        host = self.headers.get("Host")
        if not host:
            self.send_error(400, "Missing Host header")
            return

        if ":" in host:
            hostname, port = host.split(":")
            port = int(port)
        else:
            hostname = host
            port = 443 if self.path.startswith("https://") else 80

        url = f"http://{host}{self.path}" if not self.path.startswith("http") else self.path
        parsed = urlparse(url)

        if parsed.scheme == "https":
            conn = SocksHTTPSConnection(
                parsed.hostname,
                parsed.port or 443,
                proxy_host=proxy["server"],
                proxy_port=proxy["port"],
                proxy_username=proxy["username"],
                proxy_password=proxy["password"]
            )
        else:
            conn = SocksHTTPConnection(
                parsed.hostname,
                parsed.port or 80,
                proxy_host=proxy["server"],
                proxy_port=proxy["port"],
                proxy_username=proxy["username"],
                proxy_password=proxy["password"]
            )

        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query

        headers = {k: v for k, v in self.headers.items()}
        headers.pop("Connection", None)
        headers.pop("Proxy-Connection", None)

        body = None
        if "Content-Length" in self.headers:
            length = int(self.headers["Content-Length"])
            body = self.rfile.read(length)

        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()

            self.send_response(response.status, response.reason)
            for k, v in response.getheaders():
                if k.lower() not in ["connection", "transfer-encoding"]:
                    self.send_header(k, v)
            self.end_headers()

            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)

        except Exception as e:
            dprint(f"HTTP error: {e}")
            self.send_error(500, f"Proxy error: {e}")

    def do_CONNECT(self):
        try:
            host, port = self.path.split(":")
            port = int(port)
        except:
            self.send_error(400, "Invalid CONNECT request")
            return

        proxy = self.parse_proxy()
        if not proxy:
            self.send_error(400, "Invalid proxy format")
            return

        target_ip = cloudflare_dns_query(host)

        sock = CloudflareDNSSocket()
        sock.settimeout(SOCKET_TIMEOUT)
        sock.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=proxy["server"],
            port=proxy["port"],
            username=proxy["username"],
            password=proxy["password"],
            rdns=False
        )

        try:
            sock.connect((target_ip, port))
            self.send_response(200, "Connection Established")
            self.end_headers()

            browser = self.connection
            sockets = [browser, sock]

            while True:
                readable, _, _ = select.select(sockets, [], sockets, SOCKET_TIMEOUT)
                if not readable:
                    continue
                for s in readable:
                    other = sock if s is browser else browser
                    data = s.recv(16384)
                    if not data:
                        return
                    other.sendall(data)

        except Exception as e:
            dprint(f"CONNECT error: {e}")
            self.send_error(502, str(e))


def create_proxy_handler(proxy_string):
    return lambda *args, **kwargs: ProxyHandler(*args, proxy_string=proxy_string, **kwargs)


def start_proxy_server(proxy_string, port):
    handler = create_proxy_handler(proxy_string)
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    server.socket.settimeout(SOCKET_TIMEOUT)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return server, thread


def load_proxies():
    if not os.path.exists(PROXY_DATA_FILE):
        return {}
    try:
        with open(PROXY_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_proxies():
    data = {str(port): {"proxy": PROXIES[port]["proxy"]} for port in PROXIES}
    try:
        with open(PROXY_DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Failed to save: {e}")


def find_available_port():
    used = set(int(p) for p in PROXIES.keys())
    for i in range(6700, 6901):
        if i not in used:
            try:
                s = socket.socket()
                s.bind(("127.0.0.1", i))
                s.close()
                return i
            except:
                pass
    return None


def bind_proxy(proxy_string):
    m = PROXY_RE.match(proxy_string or "")
    if not m:
        console.print("[red]Invalid proxy format.[/red]")
        return

    port = find_available_port()
    if not port:
        console.print("[red]No free ports available.[/red]")
        return

    try:
        server, thread = start_proxy_server(proxy_string, port)
        PROXIES[port] = {
            "proxy": proxy_string,
            "server": server,
            "thread": thread
        }
        save_proxies()

        console.print(f"[green]Proxy running on 127.0.0.1:{port}[/green]")
        copy_port_to_clipboard(port)

    except Exception as e:
        console.print(f"[red]Error binding proxy: {e}[/red]")


def list_proxies():
    if not PROXIES:
        console.print(Panel.fit("[yellow]No proxies running[/yellow]", title="Proxies"))
        return

    table = Table(title="Active Proxies", box=box.SIMPLE_HEAVY)
    table.add_column("Port", style="bold cyan")
    table.add_column("Proxy String")

    for port, data in PROXIES.items():
        table.add_row(str(port), data["proxy"])

    console.print(table)


def restore_proxies():
    saved = load_proxies()
    for port, data in saved.items():
        port = int(port)
        try:
            server, thread = start_proxy_server(data["proxy"], port)
            PROXIES[port] = {
                "proxy": data["proxy"],
                "server": server,
                "thread": thread
            }
            console.print(f"[green]Restored proxy on {port}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to restore proxy on {port}: {e}[/red]")


def cleanup():
    for port, data in PROXIES.items():
        try:
            data["server"].shutdown()
        except:
            pass
    save_proxies()


def main():
    global DEBUG
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--bind")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()

    if args.debug:
        DEBUG = True

    restore_proxies()

    signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(0)))

    if args.cli:
        if args.bind:
            bind_proxy(args.bind)
            if args.wait:
                while True:
                    time.sleep(1)
        elif args.list:
            list_proxies()
        else:
            parser.print_help()
        return

    # UI menu
    while True:
        menu = ProxyMenu(console, PROXIES)
        result = menu.run()

        if result is None:
            cleanup()
            break
        elif result == "bind":
            console.clear()
            console.print(Panel.fit(
                "[bold cyan]Enter SOCKS5 proxy[/]\n"
                "[bright_black]Format: user:pass@host:port[/]",
                border_style="cyan",
            ))
            p = Prompt.ask("[cyan]Proxy[/]")
            bind_proxy(p)
            input("\nPress Enter to continue...")
        elif result.startswith("__COPY_PORT__:"):
            port = int(result.split(":", 1)[1])
            copy_port_to_clipboard(port)


if __name__ == "__main__":
    main()
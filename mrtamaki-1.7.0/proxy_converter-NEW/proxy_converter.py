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
    """
    Directly query Cloudflare's DNS servers for resolution
    This bypasses any system DNS settings
    """
    try:
        dprint(f"Direct Cloudflare DNS query for {hostname}")

        query = dns.message.make_query(hostname, dns.rdatatype.A)

        query.flags |= dns.flags.RD
        query.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)

        query.want_dnssec = True

        response = dns.query.udp(query, '1.1.1.1', timeout=2)

        for answer in response.answer:
            for item in answer.items:
                if item.rdtype == dns.rdatatype.A:
                    ip = item.address
                    dprint(f"Resolved {hostname} to {ip} via direct Cloudflare DNS")
                    return ip

        return resolve_doh(hostname)
    except Exception as e:
        dprint(f"Direct Cloudflare DNS query failed: {e}")
        return resolve_doh(hostname)


def resolve_doh(hostname):
    """Use DNS over HTTPS with Cloudflare"""
    try:
        dprint(f"Using Cloudflare DoH for {hostname}")

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
                for answer in result['Answer']:
                    if answer['type'] == 1:
                        ip = answer['data']
                        dprint(f"DoH resolved {hostname} to {ip}")
                        return ip

        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['1.1.1.1', '1.0.0.1']
        answers = resolver.resolve(hostname, 'A')
        if answers:
            ip = answers[0].address
            dprint(f"Standard resolver resolved {hostname} to {ip}")
            return ip
    except Exception as e:
        dprint(f"DoH resolution failed: {e}")

    try:
        return socket.gethostbyname(hostname)
    except:
        return hostname


class CloudflareDNSSocket(socks.socksocket):
    """Socket that explicitly uses Cloudflare DNS"""

    def resolve(self, destination):
        """Override the SOCKS DNS resolution to use our Cloudflare resolver"""
        hostname, port = destination
        try:
            ip_address = cloudflare_dns_query(hostname)
            return (ip_address, port)
        except Exception as e:
            dprint(f"CloudflareDNSSocket resolution error: {e}")
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
            dprint(f"Pre-resolved {host} to {self._resolved_ip}")
        except Exception:
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
                dprint(f"Connecting to pre-resolved IP {self._resolved_ip}:{self.port}")
                self.sock.connect((self._resolved_ip, self.port))
            else:
                dprint(f"Connecting to {self.host}:{self.port} without pre-resolved IP")
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
            dprint(f"Pre-resolved {host} to {self._resolved_ip}")
        except Exception:
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
                dprint(f"Connecting to pre-resolved IP {self._resolved_ip}:{self.port}")
                self.sock.connect((self._resolved_ip, self.port))
            else:
                dprint(f"Connecting to {self.host}:{self.port} without pre-resolved IP")
                self.sock.connect((self.host, self.port))

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.sock = context.wrap_socket(
                self.sock, server_hostname=self.host
            )
        except Exception as e:
            dprint(f"SOCKS+SSL connection error: {e}")
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
        """Handle CONNECT requests for HTTPS tunneling"""
        try:
            dprint(f"Processing CONNECT request for {self.path}")

            if ':' not in self.path:
                self.path = f"{self.path}:443"

            host, port = self.path.split(':')
            port = int(port)

            proxy_info = self.parse_proxy()
            if not proxy_info:
                self.send_error(400, 'Invalid proxy declaration')
                return

            # Inline Cloudflare DoH resolution (matches original exactly)
            try:
                import http.client as _http_client
                import urllib.parse as _urllib_parse

                context = ssl.create_default_context()
                conn = _http_client.HTTPSConnection("cloudflare-dns.com", 443, context=context)

                params = _urllib_parse.urlencode({
                    'name': host,
                    'type': 'A',
                    'do': 'true',
                    'cd': 'false',
                    'ct': 'application/dns-json'
                })

                headers = {
                    'Accept': 'application/dns-json',
                    'User-Agent': 'curl/7.58.0',
                    'X-Client-Type': 'Cloudflare-DNS-Browser-Check'
                }

                conn.request('GET', f'/dns-query?{params}', headers=headers)
                response = conn.getresponse()

                if response.status == 200:
                    data = response.read()
                    result = json.loads(data.decode())
                    if 'Answer' in result:
                        for answer in result['Answer']:
                            if answer['type'] == 1:
                                ip_address = answer['data']
                                dprint(f"Resolved {host} to {ip_address} using Cloudflare DoH")
                                break
                    else:
                        dprint(f"No answer in Cloudflare DoH response")
                        ip_address = host
                else:
                    dprint(f"Cloudflare DoH request failed: {response.status}")
                    ip_address = host
            except Exception as e:
                dprint(f"Error during Cloudflare DoH lookup: {e}")
                ip_address = host

            # Redundant direct UDP DNS query (matches original exactly)
            try:
                query = dns.message.make_query(host, dns.rdatatype.A)
                query.flags |= dns.flags.RD
                query.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)

                response = dns.query.udp(query, '1.1.1.1', timeout=2)

                dprint(f"Direct UDP query to 1.1.1.1 completed")
            except Exception as e:
                dprint(f"Error during direct UDP DNS query: {e}")

            client_sock = CloudflareDNSSocket()
            client_sock.settimeout(SOCKET_TIMEOUT)
            client_sock.set_proxy(
                proxy_type=socks.SOCKS5,
                addr=proxy_info['server'],
                port=proxy_info['port'],
                username=proxy_info['username'],
                password=proxy_info['password'],
                rdns=False
            )

            try:
                dprint(f"Connecting to {ip_address}:{port} via SOCKS5 for CONNECT tunnel")
                client_sock.connect((ip_address, port))

                self.send_response(200, 'Connection Established')

                self.send_header('X-DNS-Prefetch-Control', 'on')
                self.send_header('CF-DNS-ID', 'cloudflare-dns')
                self.send_header('CF-RAY', '1111111')

                self.end_headers()

                browser_sock = self.connection
                target_sock = client_sock

                browser_sock.settimeout(SOCKET_TIMEOUT)
                target_sock.settimeout(SOCKET_TIMEOUT)

                tunnel_thread = threading.Thread(
                    target=self._tunnel_sockets,
                    args=(browser_sock, target_sock),
                    daemon=True
                )
                tunnel_thread.start()

                tunnel_thread.join()

            except Exception as e:
                dprint(f"CONNECT error: {e}")
                try:
                    client_sock.close()
                    self.send_error(502, f"CONNECT Error: {str(e)}")
                except:
                    pass

        except Exception as e:
            dprint(f"CONNECT method error: {e}")
            self.send_error(500, str(e))

    def _tunnel_sockets(self, browser_sock, target_sock):
        """Tunnel data between two sockets"""
        try:
            sockets = [browser_sock, target_sock]
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, SOCKET_TIMEOUT)

                if exceptional:
                    dprint("Socket exception occurred")
                    break

                if not readable:
                    continue

                for sock in readable:
                    other_sock = target_sock if sock == browser_sock else browser_sock

                    try:
                        data = sock.recv(16384)
                        if not data:
                            dprint("Socket closed")
                            return
                        other_sock.sendall(data)
                    except Exception as e:
                        dprint(f"Socket error: {e}")
                        return

        except Exception as e:
            dprint(f"Tunnel error: {e}")
        finally:
            try:
                browser_sock.close()
            except:
                pass
            try:
                target_sock.close()
            except:
                pass


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
    """Save proxies, merging with existing file to preserve other processes' entries."""
    existing = load_proxies()
    for port in PROXIES:
        existing[str(port)] = {"proxy": PROXIES[port]["proxy"]}
    try:
        with open(PROXY_DATA_FILE, "w") as f:
            json.dump(existing, f)
    except Exception as e:
        print(f"Failed to save: {e}")


def find_available_port():
    used = set(int(p) for p in PROXIES.keys())
    available = set(range(6700, 6901)) - used

    if not available:
        return None

    for port in random.sample(list(available), min(len(available), 10)):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except socket.error:
            continue

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
        except OSError:
            # Port already in use — another process owns this proxy.
            # Track it so it appears in the menu and isn't lost on save.
            PROXIES[port] = {
                "proxy": data["proxy"],
                "server": None,
                "thread": None
            }
            console.print(f"[yellow]Proxy on {port} active in another process[/yellow]")
        except Exception as e:
            console.print(f"[red]Failed to restore proxy on {port}: {e}[/red]")


def cleanup():
    """Shut down servers we own and remove only those from the save file."""
    owned_ports = []
    for port, data in PROXIES.items():
        if data["server"] is not None:
            owned_ports.append(port)
            try:
                data["server"].shutdown()
            except:
                pass

    # Remove only our owned ports from the save file; preserve other processes' entries
    existing = load_proxies()
    for port in owned_ports:
        existing.pop(str(port), None)
    try:
        with open(PROXY_DATA_FILE, "w") as f:
            json.dump(existing, f)
    except:
        pass


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
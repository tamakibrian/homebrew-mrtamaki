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
from urllib.error import URLError, HTTPError
import base64
import argparse
import ssl
import select
from concurrent.futures import ThreadPoolExecutor
import dns.resolver
import dns.name
import dns.query
import dns.message
import time
import re
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box

console = Console()

# UI integration (NEW)
from menu_ui import show_menu  # new reusable curses-based menu

PROXY_DATA_FILE = os.path.expanduser("~/.bindproxy.json")
PROXIES = {}
DEBUG = False
SOCKET_TIMEOUT = 30


def copy_port_to_clipboard(port: int):
    """
    Copy the given port to the macOS clipboard and show a native notification.
    """
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
                ["osascript", "-e",
                 f'display notification "Port {port_str} copied to clipboard" with title "Proxy Port"']
            )
        except Exception as e:
            print(f"Clipboard/notification failed: {e}")


def cloudflare_dns_query(hostname):
    """
    Directly query Cloudflare's DNS servers for resolution
    This bypasses any system DNS settings
    """
    try:
        if DEBUG:
            print(f"Direct Cloudflare DNS query for {hostname}")
        query = dns.message.make_query(hostname, dns.rdatatype.A)

        query.flags |= dns.flags.RD
        query.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)

        query.want_dnssec = True
        response = dns.query.udp(query, '1.1.1.1', timeout=2)
        for answer in response.answer:
            for item in answer.items:
                if item.rdtype == dns.rdatatype.A:
                    ip = item.address
                    if DEBUG:
                        print(f"Resolved {hostname} to {ip} via direct Cloudflare DNS")
                    return ip
        return resolve_doh(hostname)
    except Exception as e:
        if DEBUG:
            print(f"Direct Cloudflare DNS query failed: {e}")
        return resolve_doh(hostname)


def resolve_doh(hostname):
    """Use DNS over HTTPS with Cloudflare"""
    try:
        if DEBUG:
            print(f"Using Cloudflare DoH for {hostname}")
        import http.client
        import json
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
                        if DEBUG:
                            print(f"DoH resolved {hostname} to {ip}")
                        return ip
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['1.1.1.1', '1.0.0.1']
        answers = resolver.resolve(hostname, 'A')
        if answers:
            ip = answers[0].address
            if DEBUG:
                print(f"Standard resolver resolved {hostname} to {ip}")
            return ip
    except Exception as e:
        if DEBUG:
            print(f"DoH resolution failed: {e}")
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
            if DEBUG:
                print(f"CloudflareDNSSocket resolution error: {e}")
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
            if DEBUG:
                print(f"Pre-resolved {host} to {self._resolved_ip}")
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
                if DEBUG:
                    print(f"Connecting to pre-resolved IP {self._resolved_ip}:{self.port}")
                self.sock.connect((self._resolved_ip, self.port))
            else:
                if DEBUG:
                    print(f"Connecting to {self.host}:{self.port} without pre-resolved IP")
                self.sock.connect((self.host, self.port))
        except Exception as e:
            if DEBUG:
                print(f"SOCKS connection error: {e}")
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
            if DEBUG:
                print(f"Pre-resolved {host} to {self._resolved_ip}")
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
                if DEBUG:
                    print(f"Connecting to pre-resolved IP {self._resolved_ip}:{self.port}")
                self.sock.connect((self._resolved_ip, self.port))
            else:
                if DEBUG:
                    print(f"Connecting to {self.host}:{self.port} without pre-resolved IP")
                self.sock.connect((self.host, self.port))
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.sock = context.wrap_socket(
                self.sock, server_hostname=self.host
            )
        except Exception as e:
            if DEBUG:
                print(f"SOCKS+SSL connection error: {e}")
            raise


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the proxy"""
    protocol_version = 'HTTP/1.1'

    def __init__(self, *args, **kwargs):
        self.proxy_string = kwargs.pop('proxy_string', None)
        super().__init__(*args, **kwargs)

    def parse_proxy(self):
        """Parse proxy string into components"""
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
        self.do_method('GET')

    def do_POST(self):
        self.do_method('POST')

    def do_PUT(self):
        self.do_method('PUT')

    def do_DELETE(self):
        self.do_method('DELETE')

    def do_PATCH(self):
        self.do_method('PATCH')

    def do_OPTIONS(self):
        self.do_method('OPTIONS')

    def do_method(self, method):
        """Handle HTTP requests with the specified method"""
        proxy_info = self.parse_proxy()
        if not proxy_info:
            self.send_error(400, 'Invalid proxy declaration in URL')
            return
        try:
            host = self.headers.get('Host')
            if not host:
                self.send_error(400, 'Host header is required')
                return
            if ':' in host:
                hostname, port = host.split(':')
                port = int(port)
            else:
                hostname = host
                port = 443 if self.path.startswith('https://') else 80
            scheme = 'https' if port == 443 else 'http'
            if self.path.startswith('http'):
                target_url = self.path
            else:
                target_url = f'{scheme}://{host}{self.path}'
            if DEBUG:
                print(f"Handling {method} request to {target_url}")
            url = urlparse(target_url)
            if url.scheme == 'https':
                connection = SocksHTTPSConnection(
                    host=url.hostname,
                    port=url.port or 443,
                    proxy_host=proxy_info['server'],
                    proxy_port=proxy_info['port'],
                    proxy_username=proxy_info.get('username'),
                    proxy_password=proxy_info.get('password')
                )
            else:
                connection = SocksHTTPConnection(
                    host=url.hostname,
                    port=url.port or 80,
                    proxy_host=proxy_info['server'],
                    proxy_port=proxy_info['port'],
                    proxy_username=proxy_info['username'],
                    proxy_password=proxy_info['password']
                )
            path = url.path
            if url.query:
                path += '?' + url.query
            if not path:
                path = '/'
            headers = {}
            for header, value in self.headers.items():
                if header.lower() not in ['connection', 'keep-alive', 'proxy-connection', 'upgrade', 'transfer-encoding']:
                    headers[header] = value
            headers['CF-Connecting-IP'] = '1.1.1.1'
            headers['CF-DNS-ID'] = 'cloudflare-dns'
            headers['X-DNS-Prefetch-Control'] = 'on'
            headers['Accept-CH'] = 'Sec-CH-UA-Platform-Version'
            headers['Sec-CH-UA-Platform-Version'] = 'Cloudflare-DNS'
            content_length = int(self.headers.get('Content-Length', 0))
            body = None
            if content_length > 0:
                body = self.rfile.read(content_length)
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            self.send_response(response.status, response.reason)
            for header, value in response.getheaders():
                if header.lower() not in ['connection', 'transfer-encoding']:
                    self.send_header(header, value)
            self.send_header('CF-DNS-Used', '1.1.1.1')
            self.send_header('CF-RAY', 'cloudflare-dns-check')
            self.end_headers()
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
            connection.close()
        except Exception as e:
            if DEBUG:
                print(f"Error handling {method} request: {e}")
                import traceback
                traceback.print_exc()
            self.send_error(500, f"Proxy error: {str(e)}")

    def do_CONNECT(self):
        """Handle CONNECT requests for HTTPS tunneling"""
        try:
            if DEBUG:
                print(f"Processing CONNECT request for {self.path}")
            if ':' not in self.path:
                self.path = f"{self.path}:443"
            host, port = self.path.split(':')
            port = int(port)
            proxy_info = self.parse_proxy()
            if not proxy_info:
                self.send_error(400, 'Invalid proxy declaration')
                return
            try:
                import http.client
                import json
                import urllib.parse
                import ssl
                context = ssl.create_default_context()
                conn = http.client.HTTPSConnection("cloudflare-dns.com", 443, context=context)
                params = urllib.parse.urlencode({
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
                                if DEBUG:
                                    print(f"Resolved {host} to {ip_address} using Cloudflare DoH")
                                break
                    else:
                        if DEBUG:
                            print("No answer in Cloudflare DoH response")
                        ip_address = host
                else:
                    if DEBUG:
                        print(f"Cloudflare DoH request failed: {response.status}")
                    ip_address = host
            except Exception as e:
                if DEBUG:
                    print(f"Error during Cloudflare DoH lookup: {e}")
                ip_address = host
            try:
                query = dns.message.make_query(host, dns.rdatatype.A)
                query.flags |= dns.flags.RD
                query.use_edns(edns=0, ednsflags=dns.flags.DO, payload=4096)
                response = dns.query.udp(query, '1.1.1.1', timeout=2)
                if DEBUG:
                    print("Direct UDP query to 1.1.1.1 completed")
            except Exception as e:
                if DEBUG:
                    print(f"Error during direct UDP DNS query: {e}")
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
                if DEBUG:
                    print(f"Connecting to {ip_address}:{port} via SOCKS5 for CONNECT tunnel")
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
                if DEBUG:
                    print(f"CONNECT error: {e}")
                try:
                    client_sock.close()
                    self.send_error(502, f"CONNECT Error: {str(e)}")
                except:
                    pass
        except Exception as e:
            if DEBUG:
                print(f"CONNECT method error: {e}")
            self.send_error(500, str(e))

    def _tunnel_sockets(self, browser_sock, target_sock):
        """Tunnel data between two sockets"""
        try:
            sockets = [browser_sock, target_sock]
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, SOCKET_TIMEOUT)
                if exceptional:
                    if DEBUG:
                        print("Socket exception occurred")
                    break
                if not readable:
                    continue
                for sock in readable:
                    other_sock = target_sock if sock == browser_sock else browser_sock
                    try:
                        data = sock.recv(16384)
                        if not data:
                            if DEBUG:
                                print("Socket closed")
                            return
                        other_sock.sendall(data)
                    except Exception as e:
                        if DEBUG:
                            print(f"Socket error: {e}")
                        return
        except Exception as e:
            if DEBUG:
                print(f"Tunnel error: {e}")
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
    """Create a proxy handler class with the proxy string"""
    return type('CustomProxyHandler', (ProxyHandler,),
                {'__init__': lambda self, *args, **kwargs: ProxyHandler.__init__(self, *args, **kwargs, proxy_string=proxy_string)})


def start_proxy_server(proxy_string, port):
    """Start a proxy server on the given port"""
    handler = create_proxy_handler(proxy_string)
    server = ThreadingHTTPServer(('127.0.0.1', port), handler)
    server.socket.settimeout(SOCKET_TIMEOUT)
    print(f"Starting proxy server on port {port}")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return server, server_thread


def load_proxies():
    """Load saved proxies from file"""
    if not os.path.exists(PROXY_DATA_FILE):
        return {}
    try:
        with open(PROXY_DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_proxies():
    """Save active proxies to file"""
    save_data = {}
    for port, data in PROXIES.items():
        save_data[str(port)] = {
            'proxy': data['proxy']
        }
    try:
        with open(PROXY_DATA_FILE, 'w') as f:
            json.dump(save_data, f)
    except IOError as e:
        print(f"Error saving proxies: {e}")


def find_available_port():
    """Find an available port in the range 6700-6900"""
    used_ports = set(int(port) for port in PROXIES.keys())
    available_ports = set(range(6700, 6901)) - used_ports
    if not available_ports:
        return None
    for port in random.sample(list(available_ports), min(len(available_ports), 10)):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except socket.error:
            continue
    return None


def bind_proxy(proxy_string):
    """Bind a new proxy to a random port"""
    if not re.match(r'^(.*?):(.*?)@\S+:\d+$', proxy_string):
        print("Invalid proxy format. Use username:password@server:port")
        return
    port = find_available_port()
    if not port:
        print("No available ports in the range 6700-6900")
        return
    try:
        server, thread = start_proxy_server(proxy_string, port)
        PROXIES[port] = {
            'proxy': proxy_string,
            'server': server,
            'thread': thread
        }
        save_proxies()
        print(f"SOCKS5 proxy bound successfully to HTTP port {port}")
        print(f"Use with curl: curl -x 127.0.0.1:{port} <url>")
        print(f"Browser settings: 127.0.0.1, port {port}, HTTP proxy")
        # 👇 Copy to clipboard + notify
        copy_port_to_clipboard(port)
    except Exception as e:
        print(f"Error binding proxy: {e}")


def list_proxies():
    """
    List all currently bound proxies.

    UI ONLY CHANGE:
    - Render as a rich bordered table with columns:
      Port | Country | Session Time | Date & Time Added
    - Logic (which proxies exist, how they’re managed) is unchanged.
    """
    if not PROXIES:
        # NEW: Nicer "empty" state using a panel (UI only)
        console.print(
            Panel.fit(
                "[bold yellow]No proxies currently bound[/bold yellow]",
                title="Current Proxies",
                border_style="red",
            )
        )
        return

    # NEW: Rich table to display proxy info in a boxed layout
    table = Table(
        title="Current Proxies",
        box=box.SIMPLE_HEAVY,          # Unicode-style border
        header_style="bold cyan",
        show_edge=True,
        show_header=True,
        show_lines=False,
    )

    # Columns: matches your requested structure
    table.add_column("Port", justify="left", style="bold white")
    table.add_column("Country", justify="left")
    table.add_column("Session Time", justify="right")
    table.add_column("Date & Time Added", justify="left")

    for port, data in PROXIES.items():
        proxy = data["proxy"]  # existing logic only; not changed

        # Existing info: we only *display* differently
        local_addr = f"127.0.0.1:{port}"

        # These are UI placeholders; no new storage/logic added.
        # If you later extend PROXIES[...] to include these keys,
        # the table will start showing real values automatically.
        country = data.get("country", "—")         # placeholder; keep logic unchanged
        session_time = data.get("session_time", "Active")  # use “Active” as a user-friendly default
        added_at = data.get("added_at", "—")

        table.add_row(local_addr, country, session_time, added_at)

    console.print(table)
    console.print(
        "\n[dim]Browser setup: Use 127.0.0.1 with the port number as an HTTP proxy[/dim]"
    )

def restore_proxies():
    """Restore previously saved proxies"""
    saved_proxies = load_proxies()
    for port_str, data in saved_proxies.items():
        port = int(port_str)
        try:
            server, thread = start_proxy_server(data['proxy'], port)
            PROXIES[port] = {
                'proxy': data['proxy'],
                'server': server,
                'thread': thread
            }
            print(f"Restored proxy on port {port}")
        except Exception as e:
            print(f"Error restoring proxy on port {port}: {e}")


def cleanup():
    """Cleanup all servers and save state before exit"""
    for port, data in PROXIES.items():
        if 'server' in data:
            try:
                data['server'].shutdown()
            except:
                pass
    save_proxies()


def main():
    """Main CLI entry point"""
    global PROXIES, DEBUG
    parser = argparse.ArgumentParser(description="SOCKS5 to HTTP Proxy Binder")
    parser.add_argument('--cli', action='store_true', help='Run in CLI mode with arguments')
    parser.add_argument('--bind', help='Bind a new SOCKS5 proxy (username:password@server:port)')
    parser.add_argument('--list', action='store_true', help='List current proxies')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if args.debug:
        DEBUG = True
        os.environ['DEBUG_PROXY'] = '1'

    PROXIES = {}
    restore_proxies()
    signal.signal(signal.SIGINT, lambda sig, frame: (cleanup(), sys.exit(0)))

    # Existing CLI mode (unchanged)
    if args.cli:
        if args.bind:
            bind_proxy(args.bind)
        elif args.list:
            list_proxies()
        else:
            parser.print_help()
        return

    # === UI integration - curses-based arrow-key menu ===
    menu_options = ["Bind Proxy", "Current Proxies", "Exit"]

    while True:
        selected_index = show_menu(
            menu_options,
            title="Brian Tamakis 👊🏿",
            subtitle="SOCKS5 → HTTP Proxy Binder • Use ↑/↓, Enter, or click",
            theme="macos",  # macOS-friendly colours
            back_label=None,  # no Back item on root menu
            mouse=True        # enable mouse support
        )

        # Esc / cancel -> behave like Exit
        if selected_index is None:
            cleanup()
            break

        selection = menu_options[selected_index]

        if selection == "Bind Proxy":
            # NEW UI: cleaner bind prompt using rich, consistent with menu styling
            console.clear()
            console.print(
                Panel.fit(
                    "[bold]Enter socks5 proxy below[/bold]\n"
                    "[dim]Format: username:password@server:port[/dim]",
                    title="Bind Proxy",
                    border_style="cyan",
                )
            )

            # NEW: Rich Prompt instead of raw input, logic unchanged
            proxy = Prompt.ask("[bold]Bind proxy[/bold]")

            # Existing logic: validation, binding, saving, etc. all untouched
            bind_proxy(proxy)

            # Small pause so user can see result before returning to menu
            input("\nPress Enter to return to the menu...")

        elif selection == "Current Proxies":
            list_proxies()
            # Pause so the user can read the list before the menu redraws
            input("\nPress Enter to return to the menu...")

        elif selection == "Exit":
            cleanup()
            break


if __name__ == "__main__":
    main()
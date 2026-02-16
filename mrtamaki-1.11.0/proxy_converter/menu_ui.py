#!/usr/bin/env python3
"""
menu_ui.py
Rich + readchar interactive proxy menu matching mrtamaki UI style.

Two-column layout with header, commands panel, info panel, and footer.
Uses the same design language as file_menu.py and status_menu.py.
"""

from typing import Optional, List, Dict
import re

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich import box


# ─────────────────────────────────────────────────────────────────────────────
# Color themes (matching mrtamaki)
# ─────────────────────────────────────────────────────────────────────────────

THEMES = {
    "default": {
        "accent": "cyan",
        "highlight": "yellow",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "bright_black",
    },
    "ocean": {
        "accent": "blue",
        "highlight": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "blue",
    },
    "sunset": {
        "accent": "magenta",
        "highlight": "yellow",
        "success": "green",
        "warning": "orange3",
        "error": "red",
        "muted": "bright_black",
        "border": "magenta",
    },
}

CURRENT_THEME = "default"

# ─────────────────────────────────────────────────────────────────────────────
# Commands
# ─────────────────────────────────────────────────────────────────────────────

COMMANDS = [
    ("bind", "Bind Proxy", "Add a new SOCKS5 proxy binding on a local port"),
    ("list", "Current Proxies", "View and manage active proxy connections"),
    ("return", "Exit", "Stop all proxies and return to shell"),
]

COMMAND_ICONS = {
    "bind": "\uf1e6",  # Icon for Bind Proxy
    "list": "\uf03a",  # Icon for Current Proxies
    "return": "\uf08b", # Icon for Exit
}


def get_theme():
    """Get current theme colors."""
    return THEMES.get(CURRENT_THEME, THEMES["default"])


def extract_city(proxy_string: str) -> str:
    """Extract city name from proxy URL string.

    Handles both formats:
      IPRoyal:  user:pass_country-nz_city-christchurch_session-...@host:port
      Oxylabs:  customer-user-cc-nz-city-auckland-sessid-...@host:port
    """
    # Split off the user:pass portion (before @)
    user_part = proxy_string.split("@")[0] if "@" in proxy_string else proxy_string
    # Match _city-<name>_ (IPRoyal) or -city-<name>- (Oxylabs)
    m = re.search(r"[_-]city[_-]([^_@-]+)", user_part)
    if m:
        return m.group(1).replace("_", " ").title()
    return "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# ProxyMenu class
# ─────────────────────────────────────────────────────────────────────────────

class ProxyMenu:
    """Interactive proxy menu with two-column layout."""

    def __init__(self, console: Console, proxies: dict):
        self.console = console
        self.selected = 0
        self.total = len(COMMANDS)
        self.proxies = proxies
        self.mode = "main"  # main, proxies
        self.proxy_selected = 0

    # ── Header ────────────────────────────────────────────────────────────

    def render_header(self) -> Panel:
        """Render proxy status header."""
        theme = get_theme()
        header = Text()

        header.append("  \uf1e6", style=theme["accent"])
        header.append("  mrtamaki", style=f"bold {theme['accent']}")
        header.append("  Proxy Binder\n", style=f"bold {theme['accent']}")

        count = len(self.proxies)
        header.append(f"   {count} active", style=theme["muted"])

        if self.proxies:
            ports = sorted(self.proxies.keys())
            if len(ports) > 1:
                header.append(f"  ports {ports[0]}\u2013{ports[-1]}", style=theme["muted"])
            else:
                header.append(f"  port {ports[0]}", style=theme["muted"])
        else:
            header.append("  range 6700\u20136900", style=theme["muted"])

        return Panel(
            header,
            border_style=theme["border"],
            padding=(0, 1),
            height=3,
        )

    # ── Left column: Commands ─────────────────────────────────────────────

    def render_commands(self) -> Panel:
        """Render command list (left column)."""
        theme = get_theme()
        lines = Text()

        for idx, (cmd, name, _) in enumerate(COMMANDS):
            icon = COMMAND_ICONS.get(cmd, "")

            if idx == self.selected and self.mode == "main":
                lines.append(" > ", style=f"bold {theme['accent']}")
                lines.append(f"{icon} ", style=f"bold {theme['accent']}")
                lines.append(f"{cmd:<7}", style=f"bold {theme['highlight']}")
                lines.append(f" {name}\n", style="bold white")
            else:
                lines.append("   ", style="")
                lines.append(f"{icon} ", style=theme["muted"])
                lines.append(f"{cmd:<7}", style=f"dim {theme['highlight']}")
                lines.append(f" {name}\n", style="dim white")

        return Panel(
            lines,
            title="[bold]Commands[/]",
            title_align="left",
            border_style=theme["accent"] if self.mode == "main" else theme["muted"],
            padding=(0, 1),
        )

    # ── Right column: Info panel ──────────────────────────────────────────

    def render_info_panel(self) -> Panel:
        """Render info panel (right column) - context sensitive."""
        theme = get_theme()

        if self.mode == "proxies":
            content = self._render_proxy_list()
            title = "Active Proxies"
        else:
            content = self._render_default_info()
            title = "Info"

        return Panel(
            content,
            title=f"[bold]{title}[/]",
            title_align="left",
            border_style=theme["accent"] if self.mode != "main" else theme["border"],
            padding=(0, 1),
        )

    def _render_default_info(self) -> Text:
        """Render default info panel content."""
        theme = get_theme()
        info = Text()

        # Command description
        desc = COMMANDS[self.selected][2]
        info.append(f"{desc}\n\n", style="italic")

        # Active proxies summary
        info.append("Active Proxies\n", style=f"bold {theme['accent']}")
        if self.proxies:
            for port in sorted(self.proxies.keys()):
                data = self.proxies[port]
                proxy_str = data["proxy"]
                city = extract_city(proxy_str)
                info.append(f"  {city:<14}", style=f"bold {theme['highlight']}")
                info.append(f" 127.0.0.1:{port}\n", style=theme["muted"])
        else:
            info.append("  (none running)\n", style=theme["muted"])

        info.append("\n")

        # Format help
        info.append("Proxy Format\n", style=f"bold {theme['accent']}")
        info.append("  user:pass@host:port\n", style=theme["muted"])

        return info

    def _render_proxy_list(self) -> Text:
        """Render interactive proxy list for selection."""
        theme = get_theme()
        content = Text()

        if not self.proxies:
            content.append("No proxies running.\n\n", style=theme["muted"])
            content.append("Use ", style=theme["muted"])
            content.append("Bind Proxy", style=theme["highlight"])
            content.append(" to add one.", style=theme["muted"])
            return content

        proxy_items = sorted(self.proxies.items())
        for idx, (port, data) in enumerate(proxy_items):
            proxy_str = data["proxy"]
            city = extract_city(proxy_str)

            if idx == self.proxy_selected:
                content.append(" > ", style=f"bold {theme['accent']}")
                content.append(f"{city:<14}", style=f"bold {theme['highlight']}")
                content.append(f"  127.0.0.1:{port}\n", style="bold white")
            else:
                content.append("   ", style="")
                content.append(f"{city:<14}", style=f"dim {theme['highlight']}")
                content.append(f"  127.0.0.1:{port}\n", style="dim white")

        content.append("\n")
        content.append(f"{len(self.proxies)} proxies active", style=theme["muted"])
        content.append("\n")
        content.append("Enter to copy port, Esc to back", style=theme["muted"])
        return content

    # ── Footer ────────────────────────────────────────────────────────────

    def render_footer(self) -> Panel:
        """Render controls footer."""
        theme = get_theme()
        controls = Text()

        if self.mode == "main":
            controls.append("  \u2191\u2193", style=f"bold {theme['accent']}")
            controls.append(" navigate  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("p", style=f"bold {theme['accent']}")
            controls.append(" proxies  ", style=theme["muted"])
            controls.append("q", style=f"bold {theme['accent']}")
            controls.append(" quit", style=theme["muted"])
        elif self.mode == "proxies":
            controls.append("  \u2191\u2193", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" copy port  ", style=theme["muted"])
            controls.append("Esc", style=f"bold {theme['accent']}")
            controls.append(" back", style=theme["muted"])

        return Panel(controls, border_style=theme["border"], padding=(0, 0), height=3)

    # ── Full layout ───────────────────────────────────────────────────────

    def render(self) -> Layout:
        """Render the full two-column layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )

        layout["header"].update(self.render_header())
        layout["left"].update(self.render_commands())
        layout["right"].update(self.render_info_panel())
        layout["footer"].update(self.render_footer())

        return layout

    # ── Input handling ────────────────────────────────────────────────────

    def handle_main_input(self, key: str) -> Optional[str]:
        """Handle input in main mode."""
        if key in (readchar.key.UP, "k"):
            self.selected = (self.selected - 1) % self.total
        elif key in (readchar.key.DOWN, "j"):
            self.selected = (self.selected + 1) % self.total
        elif key in (readchar.key.ENTER, "\r"):
            cmd = COMMANDS[self.selected][0]
            if cmd == "return":
                return "__EXIT__"
            elif cmd == "list":
                self.mode = "proxies"
                self.proxy_selected = 0 # Ensure selection starts at 0 when entering proxies mode
            else:
                return cmd
        elif key == "p":
            self.mode = "proxies"
            self.proxy_selected = 0 # Ensure selection starts at 0 when entering proxies mode
        elif key in ("q", readchar.key.ESC):
            return "__EXIT__"
        return None

    def handle_proxies_input(self, key: str) -> Optional[str]:
        """Handle input in proxies mode."""
        proxy_items = sorted(self.proxies.items())

        if key in (readchar.key.UP, "k"):
            if proxy_items:
                self.proxy_selected = (self.proxy_selected - 1) % len(proxy_items)
        elif key in (readchar.key.DOWN, "j"):
            if proxy_items:
                self.proxy_selected = (self.proxy_selected + 1) % len(proxy_items)
        elif key in (readchar.key.ENTER, "\r"):
            if proxy_items:
                port = proxy_items[self.proxy_selected][0]
                return f"__COPY_PORT__:{port}"
        elif key in (readchar.key.ESC, "q"):
            self.mode = "main"
        return None

    # ── Main loop ─────────────────────────────────────────────────────────

    def run(self) -> Optional[str]:
        """
        Run the interactive menu.

        Returns:
            - None: user chose Exit or pressed Esc/q
            - "bind": user chose Bind Proxy
            - "__COPY_PORT__:<port>": user selected a proxy to copy its port
        """
        if not self.console.is_terminal:
            return None

        with Live(self.render(), console=self.console, auto_refresh=False, screen=True) as live:
            while True:
                try:
                    key = readchar.readkey()
                except (KeyboardInterrupt, EOFError):
                    return None
                except Exception:
                    return None

                result = None
                if self.mode == "main":
                    result = self.handle_main_input(key)
                elif self.mode == "proxies":
                    result = self.handle_proxies_input(key)

                if result == "__EXIT__":
                    return None
                elif result:
                    return result

                live.update(self.render(), refresh=True)

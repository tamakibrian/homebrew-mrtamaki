#!/usr/bin/env python3
"""
Interactive menu UI for 1lookup API (v2)

Two-column Rich Live layout with readchar keyboard navigation.
Provides a full TUI experience with history, export, and JSON toggle.

Public entry point:
    show_menu() -> int
"""

import sys
import json
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import readchar
except ImportError:
    print("ERROR: 'readchar' package not found. Install with: pip install readchar", file=sys.stderr)
    sys.exit(2)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.layout import Layout
    from rich.live import Live
except ImportError:
    print("ERROR: 'rich' package not found. Install with: pip install rich", file=sys.stderr)
    sys.exit(2)

from .client import OneLookupClient
from .ui_utils import (
    THEME,
    format_value,
    format_key,
    extract_sections,
    get_status_info,
    get_error_message,
)


# ============================================================================
# Configuration
# ============================================================================

CONFIG_DIR = Path.home() / ".config" / "mrtamaki"
HISTORY_FILE = CONFIG_DIR / "onelookup_history.json"
MAX_HISTORY_ENTRIES = 50
MAX_JSON_LINES = 30

# Command definitions: (id, display_name, description, input_type)
# input_type: "ip", "email", "multi" (for email append), or None (no input)
COMMANDS = [
    ("ip", "IP Lookup", "Geolocation, risk, network info", "ip"),
    ("email", "Email Verify", "Email deliverability + risk", "email"),
    ("eappend", "Email Append", "Find email from person info", "multi"),
    ("reappend", "Rev Email", "Find person from email", "email"),
    ("ripappend", "Rev IP", "Enhanced IP lookup", "ip"),
    ("history", "History", "Browse recent lookups", None),
    ("exit", "Exit", "Return to shell", None),
]

ICONS = ["", "", "", "", "", "", ""]


# ============================================================================
# History Management
# ============================================================================

def load_history() -> List[Dict[str, Any]]:
    """Load lookup history from config file."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_history(history: List[Dict[str, Any]]) -> None:
    """Save lookup history to config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history[-MAX_HISTORY_ENTRIES:], indent=2, default=str))


def add_history_entry(command: str, query: str, result: Dict[str, Any]) -> None:
    """Add an entry to lookup history."""
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "query": query,
        "success": not result.get("error", False),
    })
    save_history(history)


# ============================================================================
# Input Validation
# ============================================================================

def validate_ip(ip: str) -> bool:
    """Validate IP address format (lenient)."""
    return bool(re.match(r'^[0-9.:a-fA-F]+$', ip.strip()))


def validate_email(email: str) -> bool:
    """Validate email format (basic)."""
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email.strip()))


# ============================================================================
# Menu Class
# ============================================================================

class OneLookupMenu:
    """
    Interactive 1lookup menu with two-column layout.

    Modes:
        - main: Command selection
        - input: Single-field input (IP or email)
        - multi_input: Multi-field input (email append)
        - results: Sectioned results view
        - json: Raw JSON view
        - history: History browser

    Keybindings:
        - j/k or arrows: Navigate
        - Enter: Select/Submit
        - Esc: Go back
        - t: Toggle JSON view (in results)
        - e: Export to file (in results)
        - c: Copy to clipboard (in results)
        - h: Open history (from main)
        - q: Quit
    """

    def __init__(self, console: Console):
        """Initialize the menu with a Rich console."""
        self.console = console
        self.history = load_history()

        # Navigation state
        self.selected = 0
        self.total = len(COMMANDS)
        self.mode = "main"

        # Input state
        self.input_buffer = ""
        self.input_cursor = 0
        self.input_error = ""
        self.current_command = ""

        # Multi-field input state (for email append)
        self.multi_fields = ["first_name", "last_name", "city", "zip", "address"]
        self.multi_labels = ["First Name", "Last Name", "City", "ZIP Code", "Address (opt)"]
        self.multi_values: Dict[str, str] = {}
        self.multi_field_idx = 0

        # Results state
        self.result_data: Optional[Dict[str, Any]] = None
        self.result_title = ""
        self.result_query = ""
        self.show_json = False

        # History state
        self.history_selected = 0

        # API client (lazy init)
        self._client: Optional[OneLookupClient] = None
        self.client_error = ""

        # Status message (shown briefly after actions)
        self.status_message = ""

    # ------------------------------------------------------------------------
    # API Client
    # ------------------------------------------------------------------------

    @property
    def client(self) -> Optional[OneLookupClient]:
        """Get or create API client (lazy initialization)."""
        if self._client is None and not self.client_error:
            try:
                self._client = OneLookupClient()
            except ValueError as e:
                self.client_error = str(e)
        return self._client

    # ------------------------------------------------------------------------
    # Rendering: Header
    # ------------------------------------------------------------------------

    def render_header(self) -> Panel:
        """Render header panel with title and last lookup status."""
        header = Text()
        header.append("  ", style=THEME["accent"])
        header.append(" 1lookup API", style=f"bold {THEME['accent']}")

        if self.client_error:
            header.append(f"\n  {self.client_error}", style=THEME["error"])
        elif self.status_message:
            header.append(f"\n  {self.status_message}", style=THEME["muted"])
        elif self.history:
            last = self.history[-1]
            status = "" if last.get("success") else ""
            header.append(f"\n  Last: {last.get('command', '?')} ", style=THEME["muted"])
            header.append(status, style=THEME["success"] if last.get("success") else THEME["error"])
        else:
            header.append("\n  Ready", style=THEME["muted"])

        return Panel(header, border_style=THEME["border"], padding=(0, 1), height=3)

    # ------------------------------------------------------------------------
    # Rendering: Command List (Left Column)
    # ------------------------------------------------------------------------

    def render_commands(self) -> Panel:
        """Render command list panel (left column)."""
        lines = Text()

        for idx, (cmd, name, desc, _) in enumerate(COMMANDS):
            icon = ICONS[idx] if idx < len(ICONS) else ""
            is_selected = idx == self.selected and self.mode == "main"

            if is_selected:
                lines.append(" > ", style=f"bold {THEME['accent']}")
                lines.append(f"{icon} ", style=f"bold {THEME['accent']}")
                lines.append(f"{name}\n", style="bold white")
            else:
                lines.append("   ", style="")
                lines.append(f"{icon} ", style=THEME["muted"])
                lines.append(f"{name}\n", style="dim white")

        border_style = THEME["accent"] if self.mode == "main" else THEME["muted"]
        return Panel(
            lines,
            title="[bold]Commands[/]",
            title_align="left",
            border_style=border_style,
            padding=(0, 1),
        )

    # ------------------------------------------------------------------------
    # Rendering: Info Panel (Right Column)
    # ------------------------------------------------------------------------

    def render_info_panel(self) -> Panel:
        """Render info panel (right column) - content depends on current mode."""
        if self.mode == "input":
            content = self._render_input_view()
            title = "Input"
        elif self.mode == "multi_input":
            content = self._render_multi_input_view()
            title = "Email Append"
        elif self.mode == "results":
            content = self._render_results_view()
            title = self.result_title
        elif self.mode == "json":
            content = self._render_json_view()
            title = "JSON View"
        elif self.mode == "history":
            content = self._render_history_view()
            title = "History"
        else:
            content = self._render_default_info()
            title = "Info"

        border_style = THEME["accent"] if self.mode != "main" else THEME["border"]
        return Panel(
            content,
            title=f"[bold]{title}[/]",
            title_align="left",
            border_style=border_style,
            padding=(0, 1),
        )

    def _render_default_info(self) -> Text:
        """Render default info panel showing command description and recent lookups."""
        info = Text()

        # Current command description
        _, name, desc, _ = COMMANDS[self.selected]
        info.append(f"{desc}\n\n", style="italic")

        # Recent lookups section
        info.append("Recent Lookups\n", style=f"bold {THEME['accent']}")
        if self.history:
            for entry in reversed(self.history[-5:]):
                ts = entry.get("timestamp", "")[:10]
                cmd_name = entry.get("command", "?")
                query = entry.get("query", "")[:20]
                status = "" if entry.get("success") else ""
                info.append(f"  {ts} ", style=THEME["muted"])
                info.append(f"{cmd_name}: ", style=THEME["highlight"])
                info.append(f"{query} ", style="white")
                info.append(f"{status}\n", style=THEME["success"] if entry.get("success") else THEME["error"])
        else:
            info.append("  (none yet)\n", style=THEME["muted"])

        return info

    def _render_input_view(self) -> Text:
        """Render single-field input mode."""
        content = Text()

        _, name, desc, _ = COMMANDS[self.selected]
        content.append(f"{desc}\n\n", style="italic")

        # Determine field type
        cmd = self.current_command
        if cmd in ("ip", "ripappend"):
            label = "IP Address"
            hint = "e.g., 8.8.8.8"
        elif cmd in ("email", "reappend"):
            label = "Email Address"
            hint = "e.g., user@example.com"
        else:
            label = "Input"
            hint = ""

        content.append(f"{label}:\n", style=f"bold {THEME['accent']}")

        # Input field with cursor
        content.append("  > ", style=THEME["accent"])
        self._append_text_with_cursor(content, self.input_buffer, self.input_cursor)
        content.append("\n")

        if hint:
            content.append(f"\n  {hint}\n", style=THEME["muted"])

        if self.input_error:
            content.append(f"\n  {self.input_error}\n", style=THEME["error"])

        return content

    def _render_multi_input_view(self) -> Text:
        """Render multi-field input mode for Email Append."""
        content = Text()
        content.append("Find email from person info\n\n", style="italic")

        for idx, (field, label) in enumerate(zip(self.multi_fields, self.multi_labels)):
            is_selected = idx == self.multi_field_idx
            value = self.multi_values.get(field, "")

            if is_selected:
                content.append(" > ", style=f"bold {THEME['accent']}")
                content.append(f"{label}: ", style=f"bold {THEME['accent']}")
                self._append_text_with_cursor(content, value, self.input_cursor)
                content.append("\n")
            else:
                content.append("   ", style="")
                content.append(f"{label}: ", style=THEME["muted"])
                content.append(f"{value or '-'}\n", style="dim white" if not value else "white")

        if self.input_error:
            content.append(f"\n  {self.input_error}\n", style=THEME["error"])

        content.append(f"\n[{THEME['muted']}]Tab: next field  Enter: submit[/]\n")

        return content

    def _render_results_view(self) -> Text:
        """
        Render results with sectioned display.

        Shows Risk/Threat sections prominently, followed by Network, Geo, etc.
        Uses shared section extraction for consistent formatting.
        """
        if not self.result_data:
            return Text("No results", style=THEME["muted"])

        content = Text()
        data = self.result_data

        # Check for error
        error_msg = get_error_message(data)
        if error_msg:
            content.append(f"Error: {error_msg}\n", style=THEME["error"])
            return content

        # Status line
        status_info = get_status_info(data)
        if status_info:
            success, style = status_info
            status_text = "Success" if success else "Failed"
            content.append(f"Status: {status_text}\n\n", style=style)

        # Extract sections using shared utility
        # Don't include low-priority sections (Request Info, Metadata) in TUI
        sections = extract_sections(data, include_low_priority=False)

        for section in sections:
            content.append(f"{section.name}\n", style=f"bold {section.color}")
            for key, value in section.data.items():
                display_key = format_key(key)
                display_val, val_style = format_value(value, key)
                content.append(f"  {display_key}: ", style=THEME["muted"])
                content.append(f"{display_val}\n", style=val_style)
            content.append("\n")

        # Footer hints
        content.append(f"[{THEME['muted']}]t: JSON  e: export  c: copy  Esc: back[/]")

        return content

    def _render_json_view(self) -> Text:
        """Render pretty-printed JSON view with syntax highlighting."""
        if not self.result_data:
            return Text("No results", style=THEME["muted"])

        content = Text()

        try:
            json_str = json.dumps(self.result_data, indent=2, default=str)
            lines = json_str.split("\n")

            # Truncate if too long
            if len(lines) > MAX_JSON_LINES:
                lines = lines[:MAX_JSON_LINES]
                lines.append(f"... ({len(json_str.split(chr(10))) - MAX_JSON_LINES} more lines)")

            for line in lines:
                self._append_json_line(content, line)

        except Exception:
            content.append(str(self.result_data), style="white")

        # Footer hints
        content.append(f"\n[{THEME['muted']}]t: table  e: export  c: copy  Esc: back[/]")

        return content

    def _render_history_view(self) -> Text:
        """Render history browser."""
        content = Text()

        if not self.history:
            content.append("No lookup history yet.\n\n", style=THEME["muted"])
            content.append("Run some lookups to build history.", style=THEME["muted"])
            return content

        # Show history entries (reversed, newest first)
        entries = list(reversed(self.history))
        visible_count = min(15, len(entries))

        for idx, entry in enumerate(entries[:visible_count]):
            is_selected = idx == self.history_selected
            ts = entry.get("timestamp", "")[:16].replace("T", " ")
            cmd_name = entry.get("command", "?")
            query = entry.get("query", "")
            if len(query) > 25:
                query = query[:22] + "..."
            status = "" if entry.get("success") else ""

            if is_selected:
                content.append(" > ", style=f"bold {THEME['accent']}")
                content.append(f"{ts} ", style=THEME["highlight"])
            else:
                content.append("   ", style="")
                content.append(f"{ts} ", style=THEME["muted"])

            content.append(f"{cmd_name}: ", style=THEME["accent"] if is_selected else "dim")
            content.append(f"{query} ", style="white" if is_selected else "dim white")
            content.append(f"{status}\n", style=THEME["success"] if entry.get("success") else THEME["error"])

        if len(entries) > visible_count:
            content.append(f"\n  ... +{len(entries) - visible_count} more\n", style=THEME["muted"])

        # Footer hints
        content.append(f"\n[{THEME['muted']}]Enter: replay  x: delete  Esc: back[/]")

        return content

    # ------------------------------------------------------------------------
    # Rendering: Footer
    # ------------------------------------------------------------------------

    def render_footer(self) -> Panel:
        """Render footer panel with context-sensitive keybinding hints."""
        controls = Text()

        if self.mode == "main":
            self._append_hint(controls, "j/k", "navigate")
            self._append_hint(controls, "Enter", "select")
            self._append_hint(controls, "h", "history")
            self._append_hint(controls, "q", "quit")
        elif self.mode in ("input", "multi_input"):
            self._append_hint(controls, "Type", "to enter")
            self._append_hint(controls, "Enter", "submit")
            self._append_hint(controls, "Esc", "back")
        elif self.mode in ("results", "json"):
            self._append_hint(controls, "t", "toggle JSON")
            self._append_hint(controls, "e", "export")
            self._append_hint(controls, "c", "copy")
            self._append_hint(controls, "Esc", "back")
        elif self.mode == "history":
            self._append_hint(controls, "j/k", "select")
            self._append_hint(controls, "Enter", "replay")
            self._append_hint(controls, "x", "delete")
            self._append_hint(controls, "Esc", "back")

        return Panel(controls, border_style=THEME["border"], padding=(0, 0), height=3)

    # ------------------------------------------------------------------------
    # Rendering: Helpers
    # ------------------------------------------------------------------------

    def _append_text_with_cursor(self, text: Text, value: str, cursor_pos: int) -> None:
        """Append text with cursor indicator at position."""
        if cursor_pos < len(value):
            text.append(value[:cursor_pos], style="white")
            text.append(value[cursor_pos], style="reverse")
            text.append(value[cursor_pos + 1:], style="white")
        else:
            text.append(value, style="white")
            text.append(" ", style="reverse")

    def _append_hint(self, text: Text, key: str, desc: str) -> None:
        """Append a keybinding hint to footer text."""
        text.append(f"  {key}", style=f"bold {THEME['accent']}")
        text.append(f" {desc}", style=THEME["muted"])

    def _append_json_line(self, content: Text, line: str) -> None:
        """Append a JSON line with syntax highlighting."""
        if '": ' in line:
            key_part, rest = line.split('": ', 1)
            content.append(key_part + '": ', style=THEME["accent"])
            # Color values by type
            rest_stripped = rest.strip().rstrip(",")
            if rest_stripped.startswith('"'):
                content.append(rest + "\n", style="green")
            elif rest_stripped in ("true", "false"):
                content.append(rest + "\n", style=THEME["warning"])
            elif rest_stripped.replace(".", "").replace("-", "").isdigit():
                content.append(rest + "\n", style="magenta")
            else:
                content.append(rest + "\n", style="white")
        else:
            content.append(line + "\n", style=THEME["muted"])

    # ------------------------------------------------------------------------
    # Rendering: Full Layout
    # ------------------------------------------------------------------------

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

    # ------------------------------------------------------------------------
    # Input Handling: Main Mode
    # ------------------------------------------------------------------------

    def handle_main_input(self, key: str) -> Optional[str]:
        """Handle keyboard input in main mode."""
        if key in (readchar.key.UP, "k"):
            self.selected = (self.selected - 1) % self.total
        elif key in (readchar.key.DOWN, "j"):
            self.selected = (self.selected + 1) % self.total
        elif key in (readchar.key.ENTER, "\r"):
            cmd, _, _, input_type = COMMANDS[self.selected]
            if cmd == "exit":
                return "__EXIT__"
            elif cmd == "history":
                if self.history:
                    self.mode = "history"
                    self.history_selected = 0
            elif input_type == "multi":
                self._enter_multi_input_mode(cmd)
            elif input_type:
                self._enter_input_mode(cmd)
        elif key == "h":
            if self.history:
                self.mode = "history"
                self.history_selected = 0
        elif key in ("q", readchar.key.ESC):
            return "__EXIT__"
        return None

    def _enter_input_mode(self, cmd: str) -> None:
        """Enter single-field input mode."""
        self.current_command = cmd
        self.mode = "input"
        self.input_buffer = ""
        self.input_cursor = 0
        self.input_error = ""

    def _enter_multi_input_mode(self, cmd: str) -> None:
        """Enter multi-field input mode."""
        self.current_command = cmd
        self.mode = "multi_input"
        self.multi_values = {f: "" for f in self.multi_fields}
        self.multi_field_idx = 0
        self.input_cursor = 0
        self.input_error = ""

    # ------------------------------------------------------------------------
    # Input Handling: Single-Field Input Mode
    # ------------------------------------------------------------------------

    def handle_input_mode(self, key: str) -> Optional[str]:
        """Handle keyboard input in single-field input mode."""
        if key == readchar.key.ESC:
            self.mode = "main"
            self.input_buffer = ""
            self.input_error = ""
        elif key in (readchar.key.ENTER, "\r"):
            self._submit_single_input()
        elif key == readchar.key.BACKSPACE:
            if self.input_cursor > 0:
                self.input_buffer = (
                    self.input_buffer[:self.input_cursor - 1] +
                    self.input_buffer[self.input_cursor:]
                )
                self.input_cursor -= 1
        elif key == readchar.key.LEFT:
            self.input_cursor = max(0, self.input_cursor - 1)
        elif key == readchar.key.RIGHT:
            self.input_cursor = min(len(self.input_buffer), self.input_cursor + 1)
        elif len(key) == 1 and key.isprintable():
            self.input_buffer = (
                self.input_buffer[:self.input_cursor] +
                key +
                self.input_buffer[self.input_cursor:]
            )
            self.input_cursor += 1
            self.input_error = ""
        return None

    def _submit_single_input(self) -> None:
        """Validate and submit single-field input."""
        value = self.input_buffer.strip()
        if not value:
            self.input_error = "Input required"
            return

        cmd = self.current_command
        if cmd in ("ip", "ripappend"):
            if not validate_ip(value):
                self.input_error = "Invalid IP format"
                return
        elif cmd in ("email", "reappend"):
            if not validate_email(value):
                self.input_error = "Invalid email format"
                return

        self.execute_lookup(cmd, value)

    # ------------------------------------------------------------------------
    # Input Handling: Multi-Field Input Mode
    # ------------------------------------------------------------------------

    def handle_multi_input_mode(self, key: str) -> Optional[str]:
        """Handle keyboard input in multi-field input mode."""
        if key == readchar.key.ESC:
            self.mode = "main"
            self.multi_values = {}
            self.input_error = ""
        elif key in (readchar.key.TAB, readchar.key.DOWN):
            self._move_to_field((self.multi_field_idx + 1) % len(self.multi_fields))
        elif key == readchar.key.UP:
            self._move_to_field((self.multi_field_idx - 1) % len(self.multi_fields))
        elif key in (readchar.key.ENTER, "\r"):
            self._submit_multi_input()
        elif key == readchar.key.BACKSPACE:
            self._backspace_in_current_field()
        elif key == readchar.key.LEFT:
            self.input_cursor = max(0, self.input_cursor - 1)
        elif key == readchar.key.RIGHT:
            current_field = self.multi_fields[self.multi_field_idx]
            value = self.multi_values.get(current_field, "")
            self.input_cursor = min(len(value), self.input_cursor + 1)
        elif len(key) == 1 and key.isprintable():
            self._insert_char_in_current_field(key)
        return None

    def _move_to_field(self, idx: int) -> None:
        """Move to a different field in multi-input mode."""
        self.multi_field_idx = idx
        current_field = self.multi_fields[self.multi_field_idx]
        self.input_cursor = len(self.multi_values.get(current_field, ""))

    def _backspace_in_current_field(self) -> None:
        """Handle backspace in current multi-input field."""
        current_field = self.multi_fields[self.multi_field_idx]
        value = self.multi_values.get(current_field, "")
        if self.input_cursor > 0:
            self.multi_values[current_field] = value[:self.input_cursor - 1] + value[self.input_cursor:]
            self.input_cursor -= 1

    def _insert_char_in_current_field(self, char: str) -> None:
        """Insert a character in current multi-input field."""
        current_field = self.multi_fields[self.multi_field_idx]
        value = self.multi_values.get(current_field, "")
        self.multi_values[current_field] = value[:self.input_cursor] + char + value[self.input_cursor:]
        self.input_cursor += 1
        self.input_error = ""

    def _submit_multi_input(self) -> None:
        """Validate and submit multi-field input (email append)."""
        first_name = self.multi_values.get("first_name", "").strip()
        last_name = self.multi_values.get("last_name", "").strip()
        city = self.multi_values.get("city", "").strip()
        zip_code = self.multi_values.get("zip", "").strip()
        address = self.multi_values.get("address", "").strip()

        # Validate required fields
        if not first_name:
            self.input_error = "First name required"
            self.multi_field_idx = 0
            return
        if not last_name:
            self.input_error = "Last name required"
            self.multi_field_idx = 1
            return
        if not city:
            self.input_error = "City required"
            self.multi_field_idx = 2
            return
        if not zip_code:
            self.input_error = "ZIP code required"
            self.multi_field_idx = 3
            return

        self.execute_email_append(first_name, last_name, city, zip_code, address)

    # ------------------------------------------------------------------------
    # Input Handling: Results Mode
    # ------------------------------------------------------------------------

    def handle_results_mode(self, key: str) -> Optional[str]:
        """Handle keyboard input in results/json mode."""
        if key == readchar.key.ESC:
            self.mode = "main"
            self.result_data = None
            self.show_json = False
            self.status_message = ""
        elif key == "t":
            self.mode = "json" if self.mode == "results" else "results"
        elif key == "e":
            self.export_results()
        elif key == "c":
            self.copy_to_clipboard()
        return None

    # ------------------------------------------------------------------------
    # Input Handling: History Mode
    # ------------------------------------------------------------------------

    def handle_history_mode(self, key: str) -> Optional[str]:
        """Handle keyboard input in history mode."""
        if key == readchar.key.ESC:
            self.mode = "main"
        elif key in (readchar.key.UP, "k"):
            if self.history:
                max_idx = min(15, len(self.history)) - 1
                self.history_selected = (self.history_selected - 1) % (max_idx + 1)
        elif key in (readchar.key.DOWN, "j"):
            if self.history:
                max_idx = min(15, len(self.history)) - 1
                self.history_selected = (self.history_selected + 1) % (max_idx + 1)
        elif key in (readchar.key.ENTER, "\r"):
            self._replay_history_entry()
        elif key == "x":
            self._delete_history_entry()
        return None

    def _replay_history_entry(self) -> None:
        """Replay the selected history entry."""
        if not self.history:
            return
        entries = list(reversed(self.history))
        if self.history_selected < len(entries):
            entry = entries[self.history_selected]
            cmd = entry.get("command", "")
            query = entry.get("query", "")

            # Re-execute the lookup
            if cmd and query:
                if cmd == "eappend":
                    # Can't easily replay multi-field - go back to main
                    self.mode = "main"
                else:
                    self.execute_lookup(cmd, query)

    def _delete_history_entry(self) -> None:
        """Delete the selected history entry."""
        if not self.history:
            return
        entries = list(reversed(self.history))
        if self.history_selected < len(entries):
            idx_to_remove = len(self.history) - 1 - self.history_selected
            self.history.pop(idx_to_remove)
            save_history(self.history)
            if self.history_selected >= len(self.history):
                self.history_selected = max(0, len(self.history) - 1)
            if not self.history:
                self.mode = "main"

    # ------------------------------------------------------------------------
    # Execution: API Lookups
    # ------------------------------------------------------------------------

    def execute_lookup(self, cmd: str, value: str) -> None:
        """
        Execute a single-field lookup.

        Args:
            cmd: Command name (ip, email, reappend, ripappend)
            value: Input value (IP address or email)
        """
        if not self.client:
            self.input_error = self.client_error or "No API client"
            return

        # Call appropriate API method
        if cmd == "ip":
            result = self.client.ip_lookup(value)
            title = f"IP Lookup: {value}"
        elif cmd == "email":
            result = self.client.email_verify(value)
            title = f"Email Verify: {value}"
        elif cmd == "reappend":
            result = self.client.reverse_email_append(value)
            title = f"Rev Email: {value}"
        elif cmd == "ripappend":
            result = self.client.reverse_ip_append(value)
            title = f"Rev IP: {value}"
        else:
            self.input_error = f"Unknown command: {cmd}"
            return

        # Store result and switch to results mode
        self.result_data = result
        self.result_title = title
        self.result_query = value
        self.mode = "results"
        self.show_json = False
        self.status_message = ""

        # Add to history
        add_history_entry(cmd, value, result)
        self.history = load_history()

    def execute_email_append(
        self, first_name: str, last_name: str, city: str, zip_code: str, address: str
    ) -> None:
        """
        Execute email append lookup.

        Args:
            first_name: First name
            last_name: Last name
            city: City
            zip_code: ZIP code
            address: Street address (optional)
        """
        if not self.client:
            self.input_error = self.client_error or "No API client"
            return

        result = self.client.email_append(first_name, last_name, city, zip_code, address or None)

        query = f"{first_name} {last_name}, {city} {zip_code}"
        self.result_data = result
        self.result_title = f"Email Append: {first_name} {last_name}"
        self.result_query = query
        self.mode = "results"
        self.show_json = False
        self.status_message = ""

        # Add to history
        add_history_entry("eappend", query, result)
        self.history = load_history()

    # ------------------------------------------------------------------------
    # Execution: Export/Copy
    # ------------------------------------------------------------------------

    def export_results(self) -> None:
        """Export current results to a JSON file on Desktop."""
        if not self.result_data:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"onelookup_{timestamp}.json"
        filepath = Path.home() / "Desktop" / filename

        try:
            filepath.write_text(json.dumps(self.result_data, indent=2, default=str))
            self.status_message = f"Saved: {filename}"
        except Exception as e:
            self.status_message = f"Export failed: {e}"

    def copy_to_clipboard(self) -> None:
        """Copy current results to clipboard (macOS pbcopy)."""
        if not self.result_data:
            return

        try:
            json_str = json.dumps(self.result_data, indent=2, default=str)
            subprocess.run(["pbcopy"], input=json_str.encode(), check=True)
            self.status_message = "Copied to clipboard"
        except Exception as e:
            self.status_message = f"Copy failed: {e}"

    # ------------------------------------------------------------------------
    # Main Loop
    # ------------------------------------------------------------------------

    def run(self) -> int:
        """
        Run the interactive menu loop.

        Returns:
            Exit code (0 for normal exit, 1 for error)
        """
        if not self.console.is_terminal:
            return 1

        self.console.clear()

        with Live(self.render(), console=self.console, refresh_per_second=30, screen=True) as live:
            while True:
                try:
                    key = readchar.readkey()
                except (KeyboardInterrupt, EOFError):
                    return 0

                result = None
                if self.mode == "main":
                    result = self.handle_main_input(key)
                elif self.mode == "input":
                    result = self.handle_input_mode(key)
                elif self.mode == "multi_input":
                    result = self.handle_multi_input_mode(key)
                elif self.mode in ("results", "json"):
                    result = self.handle_results_mode(key)
                elif self.mode == "history":
                    result = self.handle_history_mode(key)

                if result == "__EXIT__":
                    return 0

                live.update(self.render())


# ============================================================================
# Public Entry Point
# ============================================================================

def show_menu() -> int:
    """
    Main entry point for the interactive menu.

    Creates a console and menu instance, then runs the interactive loop.

    Returns:
        Exit code (0 for success)
    """
    console = Console()
    menu = OneLookupMenu(console)
    return menu.run()


if __name__ == "__main__":
    sys.exit(show_menu())

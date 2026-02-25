"""
Unified UI components for mrtamaki CLI tools.

Provides consistent panels, tables, and layouts across all modules.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

# Theme configuration - consistent across all modules
THEMES = {
    "default": {
        "accent": "cyan",
        "highlight": "yellow",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "bright_black",
        "info": "blue",
    },
    "ocean": {
        "accent": "blue",
        "highlight": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "blue",
        "info": "magenta",
    },
    "sunset": {
        "accent": "magenta",
        "highlight": "yellow",
        "success": "green",
        "warning": "orange3",
        "error": "red",
        "muted": "bright_black",
        "border": "magenta",
        "info": "cyan",
    },
}

# Global theme setting
_CURRENT_THEME = "default"


def set_theme(theme_name: str) -> None:
    """Set the global theme for all UI components."""
    global _CURRENT_THEME
    if theme_name in THEMES:
        _CURRENT_THEME = theme_name
    else:
        _CURRENT_THEME = "default"


def get_theme() -> Dict[str, str]:
    """Get the current theme colors."""
    return THEMES.get(_CURRENT_THEME, THEMES["default"])


def get_theme_names() -> List[str]:
    """Get list of available theme names."""
    return list(THEMES.keys())


def get_current_theme_name() -> str:
    """Get the name of the currently active theme."""
    return _CURRENT_THEME


class UIComponents:
    """Main UI component factory with consistent styling."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    @property
    def theme(self) -> Dict[str, str]:
        """Always returns the current theme — reflects calls to set_theme()."""
        return get_theme()

    def create_panel(
        self,
        content: Any,
        title: str = "",
        border_style: Optional[str] = None,
        padding: Tuple[int, int] = (0, 1),
        height: Optional[int] = None,
        box_style: box.Box = box.ROUNDED,
    ) -> Panel:
        """Create a consistently styled panel."""
        border = border_style or self.theme["border"]
        title_style = f"bold {self.theme['accent']}"
        
        return Panel(
            content,
            title=f"[{title_style}]{title}[/]" if title else None,
            border_style=border,
            padding=padding,
            height=height,
            box=box_style,
        )
    
    def create_table(
        self,
        headers: Optional[List[str]] = None,
        rows: Optional[List[List[Any]]] = None,
        show_header: bool = True,
        box_style: Optional[box.Box] = box.SIMPLE,
        expand: bool = False,
        padding: Tuple[int, int] = (0, 2),
    ) -> Table:
        """Create a consistently styled table."""
        table = Table(
            show_header=show_header,
            box=box_style,
            expand=expand,
            padding=padding,
        )
        
        if headers:
            for header in headers:
                table.add_column(
                    header,
                    style=f"bold {self.theme['accent']}",
                    no_wrap=False,
                )
        
        if rows:
            for row in rows:
                table.add_row(*[str(item) for item in row])
        
        return table
    
    def create_status_message(
        self,
        message: str,
        status_type: str = "info",  # info, success, warning, error
        icon: bool = True,
    ) -> Text:
        """Create a consistent status message."""
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✗",
        }
        
        color_map = {
            "info": self.theme["info"],
            "success": self.theme["success"],
            "warning": self.theme["warning"],
            "error": self.theme["error"],
        }
        
        text = Text()
        if icon and status_type in icons:
            text.append(f"{icons[status_type]} ", style=f"bold {color_map[status_type]}")
        text.append(message, style=color_map[status_type])
        
        return text
    
    def format_bytes(self, bytes_val: int) -> str:
        """Format bytes into human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"
    
    def format_speed(self, bytes_per_sec: float) -> str:
        """Format bytes/sec into human-readable speed."""
        for unit in ["B/s", "KB/s", "MB/s", "GB/s"]:
            if bytes_per_sec < 1024.0:
                return f"{bytes_per_sec:.1f} {unit}"
            bytes_per_sec /= 1024.0
        return f"{bytes_per_sec:.1f} TB/s"


# Global instance for easy access
ui = UIComponents()

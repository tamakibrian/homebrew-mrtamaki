"""
Unified UI components for mrtamaki CLI tools.

Provides consistent panels, tables, and layouts across all modules.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
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


class UIComponents:
    """Main UI component factory with consistent styling."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.theme = get_theme()
    
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
    
    def create_two_column_layout(
        self,
        left_content: Any,
        right_content: Any,
        header_content: Optional[Any] = None,
        footer_content: Optional[Any] = None,
        left_ratio: int = 1,
        right_ratio: int = 1,
        header_size: int = 3,
        footer_size: int = 3,
    ) -> Layout:
        """Create a consistent two-column layout."""
        layout = Layout()
        
        # Build layout structure
        if header_content:
            layout.split_column(
                Layout(name="header", size=header_size),
                Layout(name="body"),
            )
            if footer_content:
                layout["body"].split_column(
                    Layout(name="main"),
                    Layout(name="footer", size=footer_size),
                )
                layout["main"].split_row(
                    Layout(name="left", ratio=left_ratio),
                    Layout(name="right", ratio=right_ratio),
                )
                layout["footer"].update(footer_content)
            else:
                layout["body"].split_row(
                    Layout(name="left", ratio=left_ratio),
                    Layout(name="right", ratio=right_ratio),
                )
            layout["header"].update(header_content)
        else:
            layout.split_row(
                Layout(name="left", ratio=left_ratio),
                Layout(name="right", ratio=right_ratio),
            )
        
        # Set content
        layout["left"].update(left_content)
        layout["right"].update(right_content)
        
        return layout
    
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
    
    def create_progress_bar(
        self,
        percent: float,
        width: int = 20,
        show_percent: bool = True,
    ) -> Text:
        """Create a colored progress bar."""
        filled = int(width * percent / 100)
        empty = width - filled
        
        if percent > 90:
            color = self.theme["error"]
        elif percent > 70:
            color = self.theme["warning"]
        else:
            color = self.theme["success"]
        
        bar = Text()
        bar.append("█" * filled, style=color)
        bar.append("░" * empty, style=self.theme["muted"])
        if show_percent:
            bar.append(f" {percent:5.1f}%", style=color)
        
        return bar
    
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

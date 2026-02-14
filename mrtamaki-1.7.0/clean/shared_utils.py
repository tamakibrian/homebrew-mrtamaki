"""
Shared utilities for clean module Python scripts.

Provides theme configuration, byte formatting, and speed formatting
used by clean_menu.py and duplicate_finder.py.
"""

# ─── Themes ──────────────────────────────────────────────────────────────────

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

THEME_NAMES = list(THEMES.keys())
CURRENT_THEME = "default"


def get_theme():
    """Get current theme colors."""
    return THEMES.get(CURRENT_THEME, THEMES["default"])


# ─── Formatting Helpers ──────────────────────────────────────────────────────

def format_bytes(bytes_val: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """Format bytes/sec into human-readable speed."""
    for unit in ["B/s", "KB/s", "MB/s", "GB/s"]:
        if bytes_per_sec < 1024.0:
            return f"{bytes_per_sec:.1f} {unit}"
        bytes_per_sec /= 1024.0
    return f"{bytes_per_sec:.1f} TB/s"

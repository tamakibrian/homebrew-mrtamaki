"""Interactive provider submenu for proxy URL generation (a1) and convert (b2).

Rich + readchar TUI. Arrow keys, inline style. Shell-blended minimal look.
"""

from typing import Optional

import readchar
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich import box

# Provider (id, display name, Nerd Font icon)
PROVIDERS = [
    ("iproyal", "IPRoyal", "\uf0ac"),   # globe – international IPs
    ("oxylabs", "Oxylabs", "\uf0c3"),   # flask – lab/research
    ("rapid", "Rapid", "\uf0e7"),       # bolt – speed
]

THEME = {
    "accent": "green",
    "highlight": "cyan",
    "muted": "bright_black",
    "border": "bright_black",
}


def _render_menu(selected: int, prompt: str) -> Panel:
    """Rich panel with arrow-key selectable provider list. Shell-blended style."""
    t = Text()
    t.append("  ", style="")
    t.append("\uf1e6", style=THEME["accent"])  # bolt icon
    t.append(" ", style="")
    t.append(prompt, style=f"dim {THEME['muted']}")
    t.append("\n", style="")

    for idx, (pid, name, icon) in enumerate(PROVIDERS):
        if idx == selected:
            t.append("  ", style="")
            t.append("\u25b6 ", style=f"bold {THEME['accent']}")
            t.append(f"{icon} ", style=f"bold {THEME['accent']}")
            t.append(f"{name}\n", style=f"bold {THEME['highlight']}")
        else:
            t.append("    ", style="")
            t.append(f"{icon} ", style=f"dim {THEME['muted']}")
            t.append(f"{name}\n", style=f"dim {THEME['muted']}")

    t.append("  ", style="")
    t.append("\u2191\u2193", style=THEME["muted"])
    t.append(" move  ", style="dim")
    t.append("Enter", style=f"bold {THEME['accent']}")
    t.append(" select  ", style="dim")
    t.append("Esc", style="dim")
    t.append(" cancel", style=THEME["muted"])

    return Panel(
        t,
        border_style=THEME["border"],
        box=box.MINIMAL,
        padding=(0, 1),
    )


def run_provider_menu(
    city: str = "christchurch",
    country: str = "nz",
    speed_run: bool = False,
    console: Optional[Console] = None,
    prompt: Optional[str] = None,
) -> Optional[str]:
    """Interactive provider selection with Rich + readchar, arrow keys.

    Returns:
        Provider id ("iproyal", "oxylabs", "rapid") or None if cancelled.
    """
    con = console or Console()
    # Require terminal for readchar + Live
    if not con.is_terminal:
        return None

    selected = 0
    total = len(PROVIDERS)

    if prompt is None:
        prompt = f"Provider ({city}, {country})" if city else "Provider"
    if speed_run:
        prompt += " [speed run]"

    def render() -> Panel:
        return _render_menu(selected, prompt)

    # screen=False: inline in terminal, not full-screen app
    with Live(render(), console=con, auto_refresh=False, screen=False) as live:
        while True:
            try:
                key = readchar.readkey()
            except (KeyboardInterrupt, EOFError):
                return None
            except Exception:
                return None

            if key in (readchar.key.UP, "k"):
                selected = (selected - 1) % total
            elif key in (readchar.key.DOWN, "j"):
                selected = (selected + 1) % total
            elif key in (readchar.key.ENTER, "\r"):
                return PROVIDERS[selected][0]
            elif key in ("q", readchar.key.ESC):
                return None

            live.update(render(), refresh=True)

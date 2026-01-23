#!/usr/bin/env python3
"""Short intro banner using Rich library."""

import sys
import time
import random
from rich.console import Console
from rich.text import Text
from rich.align import Align
from rich.live import Live

BANNER_TEXT = "Brian ✓ Tamaki"
DURATION = 1.5  # seconds
FPS = 20

def scramble_char():
    """Return a random noise character."""
    return random.choice(".,:;!*#@+~")

def reveal_text(text: str, progress: float) -> Text:
    """Reveal text from center outward with scrambled characters."""
    length = len(text)
    center = length // 2
    radius = int(progress * (center + 1))

    result = Text()
    for i, char in enumerate(text):
        if char == " ":
            result.append(" ")
            continue
        dist = abs(i - center)
        if dist <= radius:
            result.append(char, style="bold magenta")
        else:
            result.append(scramble_char(), style="dim white")
    return result

def run_banner():
    """Run the animated banner."""
    console = Console()

    if not console.is_terminal:
        return

    frames = int(DURATION * FPS)
    delay = 1.0 / FPS

    console.clear()
    console.show_cursor(False)

    try:
        with Live(console=console, refresh_per_second=FPS, transient=True) as live:
            for frame in range(frames + 1):
                progress = frame / frames
                text = reveal_text(BANNER_TEXT, progress)
                centered = Align.center(text, vertical="middle", height=console.height)
                live.update(centered)
                time.sleep(delay)

        # Final clean frame
        console.clear()
        final = Text(BANNER_TEXT, style="bold magenta")
        console.print(Align.center(final, vertical="middle", height=console.height))
        time.sleep(0.3)
        console.clear()
    finally:
        console.show_cursor(True)

if __name__ == "__main__":
    try:
        run_banner()
    except KeyboardInterrupt:
        Console().show_cursor(True)
        sys.exit(0)

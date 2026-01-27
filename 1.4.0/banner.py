#!/usr/bin/env python3
"""Glitch Reveal style intro banner using Rich library."""

import sys
import time
import random
from rich.console import Console
from rich.text import Text
from rich.align import Align

# Configuration
BANNER_TEXT = "Brian Tamaki"
DURATION = 1.0
FPS = 30
GLITCH_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`0123456789"
FINAL_STYLE = "bold cyan"
GLITCH_STYLES = ["magenta", "green", "yellow", "red", "blue"]


def get_glitch_char():
    """Return a random glitch character."""
    return random.choice(GLITCH_CHARS)


def get_glitch_style():
    """Return a random glitch color style."""
    return random.choice(GLITCH_STYLES)


def render_frame(text: str, revealed: set, glitch_intensity: float) -> Text:
    """Render a frame with revealed and glitch characters."""
    result = Text()

    for i, char in enumerate(text):
        if char == " ":
            result.append(" ")
        elif i in revealed:
            # Revealed character - might still glitch occasionally
            if random.random() < glitch_intensity * 0.3:
                result.append(get_glitch_char(), style=get_glitch_style())
            else:
                result.append(char, style=FINAL_STYLE)
        else:
            # Not yet revealed - show glitch
            result.append(get_glitch_char(), style=get_glitch_style())

    return result


def run_banner():
    """Run the glitch reveal banner animation."""
    console = Console()

    if not console.is_terminal:
        return

    frames = int(DURATION * FPS)
    delay = 1.0 / FPS
    text_length = len(BANNER_TEXT)

    # Track which characters have been revealed
    revealed = set()
    # List of non-space character indices to reveal
    revealable = [i for i, c in enumerate(BANNER_TEXT) if c != " "]
    random.shuffle(revealable)

    # Calculate reveal schedule
    chars_per_frame = len(revealable) / (frames * 0.7)  # Reveal in first 70% of time

    console.clear()
    console.show_cursor(False)

    try:
        chars_revealed = 0
        for frame in range(frames):
            progress = frame / frames
            glitch_intensity = 1.0 - progress  # Decreases over time

            # Reveal characters progressively
            target_revealed = int(min(frame * chars_per_frame, len(revealable)))
            while chars_revealed < target_revealed:
                revealed.add(revealable[chars_revealed])
                chars_revealed += 1

            # Render and display
            text = render_frame(BANNER_TEXT, revealed, glitch_intensity)
            centered = Align.center(text, vertical="middle", height=console.height)

            console.clear()
            console.print(centered)
            time.sleep(delay)

        # Final clean frame - all revealed, no glitches
        revealed = set(range(text_length))
        final_text = Text(BANNER_TEXT, style=FINAL_STYLE)
        centered = Align.center(final_text, vertical="middle", height=console.height)
        console.clear()
        console.print(centered)
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

#!/usr/bin/env python3
"""
menu_ui.py
Reusable arrow-key-based terminal menu using curses.

Features:
- Arrow key navigation (↑/↓ or j/k)
- Enter to select
- Esc to cancel
- Optional mouse support (click to select)
- Optional "Back" item
- Simple colour themes, including a macOS-friendly theme
"""

import curses
from typing import List, Optional


# ---------- Internal helpers for layout / theme ----------

def _menu_start_y(title: str | None, subtitle: str | None) -> int:
    """
    Compute the starting Y coordinate for menu items
    based on whether title/subtitle are present.
    """
    y = 1
    if title:
        y += 2  # title + spacer
    if subtitle:
        y += 2  # subtitle + spacer
    return y


def _init_colors(theme: str) -> bool:
    """
    Initialize color pairs based on a simple theme name.
    Returns True if colors are enabled, False otherwise.
    """
    if not curses.has_colors():
        return False

    curses.start_color()
    curses.use_default_colors()

    if theme.lower() == "macos":
        # macOS-like: white highlight, magenta title
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)   # selection
        curses.init_pair(2, curses.COLOR_MAGENTA, -1)                 # title
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)   # back item (same as selection)
    else:
        # default: cyan highlight, cyan title
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)    # selection
        curses.init_pair(2, curses.COLOR_CYAN, -1)                    # title
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)    # back item

    return True


def _draw_menu(
    stdscr,
    options: List[str],
    current_index: int,
    title: str | None = None,
    subtitle: str | None = None,
    has_colors: bool = False,
    back_label: str | None = None,
) -> None:
    """
    Render the menu screen.
    """
    stdscr.clear()
    height, width = stdscr.getmaxyx()

    # Hide the cursor if possible
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    # Title
    y = 1
    if title:
        x = max(0, (width - len(title)) // 2)
        attr = curses.A_BOLD
        if has_colors:
            attr |= curses.color_pair(2)
        try:
            stdscr.addstr(y, x, title, attr)
        except curses.error:
            pass
        y += 2

    # Subtitle
    if subtitle:
        x = max(0, (width - len(subtitle)) // 2)
        try:
            stdscr.addstr(y, x, subtitle, curses.A_DIM)
        except curses.error:
            pass
        y += 2

    # Menu items
    start_y = y
    display_options = list(options)
    if back_label is not None:
        display_options.append(back_label)

    for idx, text in enumerate(display_options):
        menu_y = start_y + idx
        if menu_y >= height - 2:
            break  # Avoid drawing off bottom

        # Determine styling
        is_selected = (idx == current_index)
        is_back_item = (back_label is not None and idx == len(display_options) - 1)

        attr = curses.A_NORMAL
        if is_selected:
            if has_colors:
                attr = curses.color_pair(1) | curses.A_BOLD
            else:
                attr = curses.A_REVERSE | curses.A_BOLD
        elif is_back_item:
            # Back item slightly dim if not selected
            attr = curses.A_DIM

        prefix = "> " if is_selected else "  "
        line_text = f"{prefix}{text}"

        try:
            stdscr.addstr(menu_y, 4, line_text[: max(0, width - 5)], attr)
        except curses.error:
            pass

    # Footer
    footer = "↑/↓ or j/k to move • Enter to select • Esc to cancel • Click to select"
    fx = max(0, (width - len(footer)) // 2)
    fy = height - 2
    try:
        stdscr.addstr(fy, fx, footer, curses.A_DIM)
    except curses.error:
        pass

    stdscr.refresh()


# ---------- Core menu loop ----------

def _menu_loop(
    stdscr,
    options: List[str],
    title: str | None = None,
    subtitle: str | None = None,
    theme: str = "default",
    back_label: str | None = None,
    mouse: bool = True,
) -> Optional[int]:
    """
    Core curses-driven menu loop.
    Returns selected index, or None on Esc / Back.
    """
    stdscr.keypad(True)

    # Colors
    has_colors = _init_colors(theme)

    # Mouse support
    mouse_enabled = False
    if mouse:
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.mouseinterval(150)
            mouse_enabled = True
        except curses.error:
            mouse_enabled = False

    current_index = 0
    display_options = list(options)
    if back_label is not None:
        display_options.append(back_label)
    count = len(display_options)

    while True:
        _draw_menu(
            stdscr,
            options=options,
            current_index=current_index,
            title=title,
            subtitle=subtitle,
            has_colors=has_colors,
            back_label=back_label,
        )

        key = stdscr.getch()

        # --- Keyboard navigation ---
        if key in (curses.KEY_UP, ord("k")):
            current_index = (current_index - 1) % count
        elif key in (curses.KEY_DOWN, ord("j")):
            current_index = (current_index + 1) % count
        elif key in (curses.KEY_ENTER, 10, 13):
            # If "Back" is selected, treat as cancel
            if back_label is not None and current_index == len(display_options) - 1:
                return None
            return current_index
        elif key == 27:  # Esc
            return None

        # --- Mouse support ---
        elif mouse_enabled and key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                # Left-click (pressed / clicked / released)
                if bstate & (curses.BUTTON1_PRESSED
                             | curses.BUTTON1_CLICKED
                             | curses.BUTTON1_RELEASED):
                    # Map Y coordinate to menu index
                    start_y = _menu_start_y(title, subtitle)
                    idx = my - start_y
                    if 0 <= idx < count:
                        current_index = idx
                        # If "Back" clicked -> cancel
                        if back_label is not None and idx == len(display_options) - 1:
                            return None
                        # Treat click as selection
                        return current_index
            except curses.error:
                # Ignore mouse errors and continue
                pass


# ---------- Public API ----------

def show_menu(
    options: List[str],
    title: str | None = None,
    subtitle: str | None = None,
    theme: str = "default",
    back_label: str | None = None,
    mouse: bool = True,
) -> Optional[int]:
    """
    Show a curses-based menu and return the selected index.

    :param options: List of option labels to display.
    :param title: Optional title text (centered).
    :param subtitle: Optional subtitle / hint line.
    :param theme: Colour theme name ("default", "macos", ...).
    :param back_label: If provided, a "Back" item is added at bottom and
                       selecting it returns None.
    :param mouse: Enable mouse support (click to select) if True.
    :return: 0-based index of selected option, or None on Esc / Back.
    """
    if not options:
        return None

    def _wrapped(stdscr):
        return _menu_loop(
            stdscr,
            options=options,
            title=title,
            subtitle=subtitle,
            theme=theme,
            back_label=back_label,
            mouse=mouse,
        )

    return curses.wrapper(_wrapped)
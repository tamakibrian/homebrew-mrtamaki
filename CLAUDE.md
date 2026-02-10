# CLAUDE.md - mrtamaki Project Guide

## What is this project?

**mrtamaki** is a Zsh toolkit for macOS, distributed as a Homebrew cask. Users install it with `brew install --cask mrtamaki` and source a single file from `~/.zshrc`. It provides short terminal commands (a1, b2, h8, fmenu, etc.) for proxy management, system cleanup, file operations, and API lookups.

## Repository layout

```
TAMAKI/                          # Git repo root (branch: main)
├── CLAUDE.md                    # This file
├── README.md                    # User-facing docs
├── build-release.sh             # Creates release ZIP + SHA256 for cask
├── Casks/mrtamaki.rb            # Homebrew cask definition (Ruby)
├── .gitignore
└── mrtamaki-1.7.0/              # The source directory (version-named)
    ├── mrtamaki.sh              # ENTRYPOINT - sourced from ~/.zshrc, loads all modules
    ├── utils.sh                 # Shared utilities: print_*, confirm(), _ensure_module_venv()
    ├── core.sh                  # Main commands: a1-a4 (proxy), b2, c3, d4, e5, f6, g7
    ├── banner.py                # Startup banner (Rich)
    ├── status/                  # Status module (h8, h9)
    │   ├── status.sh            # Shell wrappers: h8(), h9(), cleanup functions
    │   ├── status_menu.py       # h8: interactive cleanup menu (Rich + readchar TUI)
    │   ├── health_dashboard.py  # h9: live system health dashboard (Rich + psutil TUI)
    │   └── requirements.txt     # rich, readchar, psutil
    ├── Files/                   # File operations module
    │   ├── files.sh             # Shell functions: fa-fg, fmenu, mkcd, tempdir, etc.
    │   ├── file_menu.py         # fmenu: interactive file menu (Rich + readchar TUI)
    │   └── requirements.txt     # rich, readchar
    ├── found/                   # 1Lookup API module
    │   ├── one_lookup.zsh       # Shell wrapper: d5/found command
    │   └── one_lookup/          # Python package
    │       ├── __init__.py
    │       ├── client.py        # API client for 1lookup.com
    │       ├── cli.py           # CLI argument parsing
    │       ├── menu_v2.py       # Interactive lookup menu (Rich TUI)
    │       └── ui_utils.py      # Shared UI helpers
    ├── proxy_converter-NEW/     # New proxy converter (Rich menu)
    │   ├── proxy_converter.py
    │   ├── menu_ui.py
    │   └── requirements.txt
    └── proxy_converter-OG/      # Legacy proxy converter
        ├── proxy_converter.py
        └── requirements.txt
```

## Architecture

### Module loading chain

```
~/.zshrc
  └─ source mrtamaki.sh       # Sets SHELL_V11_DIR, ZSH_THEME, loads banner
       ├─ source utils.sh      # Shared functions, venv manager
       ├─ source core.sh       # a1-g7 commands
       ├─ source files/files.sh
       ├─ source found/one_lookup.zsh
       ├─ source status/status.sh
       ├─ source zsh-syntax-highlighting (Homebrew formula)
       └─ source zsh-autosuggestions (Homebrew formula)
```

### Theme & font

- **Theme**: `light-zsh/light-zsh` ([InfinityUniverse0/light-zsh](https://github.com/InfinityUniverse0/light-zsh)) — requires Oh My Zsh. Cloned to `~/.oh-my-zsh/custom/themes/light-zsh/` during cask postflight.
- **Font**: `font-jetbrains-mono-nerd-font` — installed via Homebrew cask during postflight. Provides Nerd Font icons used by the theme.
- **Syntax highlighting**: `zsh-syntax-highlighting` Homebrew formula — sourced at end of `mrtamaki.sh`.
- **Autosuggestions**: `zsh-autosuggestions` Homebrew formula — sourced at end of `mrtamaki.sh`.

### Venv system

Each module gets its own isolated Python venv, created lazily on first use via `_ensure_module_venv <name> <base_dir>` in `utils.sh`. Venvs are stored at `<base_dir>/venv-<module>` (e.g., `venv-status`, `venv-files`, `venv-found`, `venv-banner`).

The function sets the global `$VENV_PYTHON` variable for the caller to use. The Homebrew cask (`Casks/mrtamaki.rb`) also pre-creates venvs during `postflight` install.

Package mapping (defined in `utils.sh` `_ensure_module_venv`):
- **banner**: `rich`
- **files**: `rich readchar`
- **found**: `rich requests InquirerPy readchar`
- **status**: `rich readchar psutil`

### TUI pattern (Rich + readchar)

All interactive menus (h8, fmenu, d5) follow the same pattern:
1. Shell function sets up venv, creates temp file for IPC
2. Runs Python TUI script with `--result-file <tmpfile>`
3. Python menu uses `rich.live.Live(screen=True, auto_refresh=False)` for alternate-screen TUI
4. User selection is written to temp file with protocol prefix `__MODULENAME_CMD__:<command>`
5. Shell reads temp file, parses command, dispatches to shell functions

**Critical**: `auto_refresh` MUST be `False` when using `readchar` inside a `Live` context. The Live refresh thread races with readchar's `TCSAFLUSH` terminal calls, causing multi-byte key sequences (arrow keys) to be silently dropped.

### h9 health dashboard (special case)

Unlike the menus, h9 needs periodic auto-refresh for live metrics. It does NOT use `readchar` or threading. Instead:
- Sets terminal to cbreak mode once via `tty.setcbreak()`
- Uses `select.select()` with timeouts for non-blocking stdin polling
- Reads single chars via `sys.stdin.read(1)` (all h9 controls are single-byte: q/c/m/p/t)
- Refreshes display manually via `live.update(render, refresh=True)`

## Shell conventions

- **Zsh-only** - Uses zsh-specific features: `${0:A:h}`, `typeset -g`, `(N)` glob qualifier, `local -A` (assoc arrays), `${var:t}` (tail), `${var/#pat/rep}`
- **Path resolution**: `SHELL_V11_DIR="${0:A:h}"` resolves the directory of the sourced script
- **Color output**: `print_success`, `print_error`, `print_warning`, `print_info`, `print_header` from utils.sh
- **Confirmation**: `confirm "message" "default"` returns 0 (yes) or 1 (no)
- **Command naming**: Short alphanumeric codes (a1, b2, c3...) chosen for fast typing

## Release process

1. Edit source in `mrtamaki-1.7.0/`
2. Run `./build-release.sh <version>` to create ZIP
3. Upload ZIP to GitHub release
4. Update `Casks/mrtamaki.rb` with new version + SHA256
5. Commit and push

## Environment variables (user-configured in ~/.zshenv)

- `IPROYAL_USER` / `IPROYAL_PASS` - IPRoyal proxy credentials (a1, a3)
- `OXYLABS_USER` / `OXYLABS_PASS` - Oxylabs proxy credentials (a2, a4)
- `SCAMALYTICS_API_KEY` - Scamalytics IP check (d4)
- `ONELOOKUP_API_KEY` - 1Lookup API (d5, iplookup, everify, etc.)

## Common pitfalls

- **Zsh reserved variable names**: Never use `path` as a local variable — in zsh it's a special array tied to `$PATH`. Assigning a scalar to it corrupts `PATH` and breaks all command lookups. Use `cache_path`, `file_path`, etc. Other reserved names to avoid: `path`, `fpath`, `cdpath`, `mailpath`, `manpath`.
- **readchar.key constants**: Use `readchar.key.ESC` (not `.ESCAPE`). Version 4.x has: `UP`, `DOWN`, `ENTER`, `ESC`, `BACKSPACE`, `DELETE`, etc.
- **readchar + Rich.Live threading**: Never use `auto_refresh=True` with `readchar.readkey()` in the same or sibling thread. The Live refresh thread's output causes `TCSADRAIN` waits, and readchar's `TCSAFLUSH` discards buffered escape sequence bytes.
- **macOS du**: Does not support `--apparent-size`. Use `du -sh` only.
- **build-release.sh**: Currently hardcodes `SOURCE_DIR` to `1.6.0` - must update when bumping versions.
- **Version string**: `MRTAMAKI_VERSION` in `mrtamaki.sh` (currently says `1.6.0`) should match the directory name and cask version.

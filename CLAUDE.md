# CLAUDE.md - mrtamaki Project Guide

## What is this project?

**mrtamaki** is a Zsh toolkit for macOS, distributed as a Homebrew cask. Users install it with `brew install --cask mrtamaki` and source a single file from `~/.zshrc`. It provides short terminal commands (a1, b2, h8, fmenu, etc.) for proxy management, system cleanup, file operations, and API lookups.

**Current version**: 1.7.10

## Repository layout

```
TAMAKI/                              # Git repo root (branch: main)
├── CLAUDE.md                        # This file — AI agent project guide
├── README.md                        # User-facing docs
├── build-release.sh                 # Creates release ZIP + SHA256 for cask
├── Casks/mrtamaki.rb                # Homebrew cask definition (Ruby)
├── .gitignore
└── mrtamaki-1.7.0/                  # Source directory (version-named — directory name does NOT change per release)
    ├── mrtamaki.sh                  # ENTRYPOINT — sourced from ~/.zshrc, loads all modules
    ├── utils.sh                     # Shared utilities: print_*, confirm(), _ensure_module_venv()
    ├── core.sh                      # Main commands: a1-a4 (proxy), b2, c3, d4, d6, e5, f6, g7
    ├── banner.py                    # Startup banner (Rich)
    ├── status_bar.py                # Persistent status bar helper (pycache info, system health)
    ├── ensure_venv_manager          # LEGACY — no longer sourced by core.sh (kept for reference only)
    ├── status/                      # Status module (h8/smenu, h9)
    │   ├── status.sh                # Shell wrappers: smenu/h8, h1-h5, h9, _human_size(), cleanup fns
    │   ├── status_menu.py           # smenu/h8: interactive cleanup menu (Rich + readchar TUI)
    │   ├── health_dashboard.py      # h9: live system health dashboard (Rich + psutil TUI)
    │   ├── shared_utils.py          # Shared Python utilities: themes, format_bytes(), format_speed()
    │   └── requirements.txt         # rich, readchar, psutil
    ├── Files/                       # File operations module (capital F)
    │   ├── files.sh                 # Shell functions: fa-fn, fmenu, mkcd, tempdir, etc.
    │   ├── file_menu.py             # fmenu: interactive file menu (Rich + readchar TUI)
    │   └── requirements.txt         # rich, readchar
    ├── found/                       # 1Lookup API module
    │   ├── one_lookup.zsh           # Shell wrapper: d5/found command
    │   └── one_lookup/              # Python package
    │       ├── __init__.py
    │       ├── client.py            # API client for 1lookup.com
    │       ├── cli.py               # CLI argument parsing
    │       ├── menu_v2.py           # Interactive lookup menu (Rich TUI)
    │       └── ui_utils.py          # Shared UI helpers
    ├── proxy_converter-NEW/         # New proxy converter (Rich menu)
    │   ├── proxy_converter.py
    │   ├── menu_ui.py
    │   └── requirements.txt
    └── proxy_converter-OG/          # Legacy proxy converter
        ├── proxy_converter.py
        └── requirements.txt
```

**Note**: The source directory is named `mrtamaki-1.7.0/` but the actual version is tracked by `MRTAMAKI_VERSION` in `mrtamaki.sh` and `Casks/mrtamaki.rb`. The directory name does not change on every release.

## Architecture

### Module loading chain

```
~/.zshrc
  └─ source mrtamaki.sh              # Sets SHELL_V11_DIR, ZSH_THEME, loads banner
       ├─ source utils.sh             # Shared functions, venv manager
       ├─ source core.sh              # a1-a4, b2, c3, d4, d6, e5, f6, g7
       ├─ source Files/files.sh       # File commands: fmenu, fa-fn
       ├─ source found/one_lookup.zsh # 1Lookup API: d5/found, iplookup, everify, etc.
       ├─ source status/status.sh     # smenu/h8, h1-h5, h9
       ├─ source zsh-syntax-highlighting (Homebrew formula)
       └─ source zsh-autosuggestions (Homebrew formula)
```

### Theme & font

- **Theme**: `light-zsh/light-zsh` ([InfinityUniverse0/light-zsh](https://github.com/InfinityUniverse0/light-zsh)) — requires Oh My Zsh. Cloned to `~/.oh-my-zsh/custom/themes/light-zsh/` during cask postflight.
- **Font**: `font-jetbrains-mono-nerd-font` — installed via Homebrew cask during postflight. Provides Nerd Font icons used by the theme.
- **Syntax highlighting**: `zsh-syntax-highlighting` Homebrew formula — sourced at end of `mrtamaki.sh`.
- **Autosuggestions**: `zsh-autosuggestions` Homebrew formula — sourced at end of `mrtamaki.sh`.

### Venv system

Each module gets its own isolated Python venv, created lazily on first use via `_ensure_module_venv <name> [base_dir]` in `utils.sh`. Venvs are stored at `<base_dir>/venv-<module>` (e.g., `venv-status`, `venv-files`, `venv-found`, `venv-banner`).

The function:
1. Looks up the module name in a hardcoded `module_packages` associative array
2. Creates the venv if missing, using an atomic `mkdir`-based lockfile (`${venv_path}.creating`) to prevent races when multiple shells start simultaneously
3. Installs pinned dependencies (e.g., `rich>=13`, `readchar>=4`)
4. Sets the global `$VENV_PYTHON` variable for the caller to use

The Homebrew cask (`Casks/mrtamaki.rb`) also pre-creates all venvs during `postflight` install for zero-wait first run.

**Package mapping** (defined in `utils.sh` `_ensure_module_venv`):

| Module     | Venv name       | Packages                                       |
|------------|-----------------|------------------------------------------------|
| banner     | `venv-banner`   | `rich>=13`                                     |
| files      | `venv-files`    | `rich>=13 readchar>=4`                         |
| found      | `venv-found`    | `rich>=13 requests>=2 InquirerPy>=0.3 readchar>=4` |
| status     | `venv-status`   | `rich>=13 readchar>=4 psutil>=5`               |
| proxy      | `venv-proxy`    | `PySocks>=1.7 rich>=13 readchar>=4 dnspython>=2` |
| proxy-og   | `venv-proxy-og` | `PySocks>=1.7 tabulate>=0.9 dnspython>=2`     |

### TUI pattern (Rich + readchar)

All interactive menus (h8/smenu, fmenu, d5, b2-new) follow the same pattern:
1. Shell function sets up venv via `_ensure_module_venv`, creates temp file for IPC
2. Runs Python TUI script with `--result-file <tmpfile>`
3. Python menu uses `rich.live.Live(screen=True, auto_refresh=False)` for alternate-screen TUI
4. User selection is written to temp file with protocol prefix `__MODULENAME_CMD__:<command>`
5. Shell reads temp file, parses command, dispatches to shell functions

**Critical**: `auto_refresh` MUST be `False` when using `readchar` inside a `Live` context. The Live refresh thread races with readchar's `TCSAFLUSH` terminal calls, causing multi-byte key sequences (arrow keys) to be silently dropped. All `live.update()` calls must use `refresh=True` for manual screen updates.

### h9 health dashboard (special case)

Unlike the menus, h9 needs periodic auto-refresh for live metrics. It does NOT use `readchar` or threading. Instead:
- Sets terminal to cbreak mode once via `tty.setcbreak()`
- Uses `select.select()` with timeouts for non-blocking stdin polling
- Reads single chars via `sys.stdin.read(1)` (all h9 controls are single-byte: q/c/m/p/t)
- Refreshes display manually via `live.update(render, refresh=True)`

### Shared Python utilities (status module)

`status/shared_utils.py` provides common code used by both `status_menu.py` and `health_dashboard.py`:
- `THEMES` dict, `THEME_NAMES` list, `CURRENT_THEME` global
- `get_theme()` — returns current theme color mapping
- `format_bytes(bytes_val)` — human-readable byte formatting
- `format_speed(bytes_per_sec)` — human-readable speed formatting

When `health_dashboard.py` cycles themes via the 't' key, it modifies `shared_utils.CURRENT_THEME` directly.

### Background proxy cleanup (a3/a4)

The speed-run commands `a3()` and `a4()` launch a background proxy converter process. They register a `trap` on `INT TERM` to kill the background PID on Ctrl+C, and unset the trap before normal exit. This prevents orphaned proxy processes.

## Command reference

| Command | Function | Description |
|---------|----------|-------------|
| `a1` | `a1()` in core.sh | Generate IPRoyal proxy URL (random port: 51200/32325/12325) |
| `a2` | `a2()` in core.sh | Generate Oxylabs proxy URL |
| `a3` | `a3()` in core.sh | IPRoyal speed run: generate -> bind -> test -> check (random port: 51200/32325/12325) |
| `a4` | `a4()` in core.sh | Oxylabs speed run: generate -> bind -> test -> check |
| `b2` | `b2()` in core.sh | Proxy converter (Legacy or New, interactive submenu) |
| `c3 <port>` | `c3()` in core.sh | Test proxy on port, get IP via ipinfo.io, run DNS leak test |
| `d4 <ip>` | `d4()` in core.sh | Scamalytics IP reputation check |
| `d5` / `found` | one_lookup.zsh | Interactive 1Lookup API menu |
| `d6 [port]` | `d6()` in core.sh | DNS leak test via bash.ws (optional proxy port) |
| `e5 [path]` | `e5()` in core.sh | Find and clean up virtual environments |
| `f6` | `f6()` in core.sh | Flush DNS cache (macOS) |
| `g7 [venv]` | `g7()` in core.sh | Pip purge — cache + packages (default: system) |
| `h8` / `smenu` | `smenu()` in status.sh | Interactive status menu (cleanup, caches, venvs) |
| `h9` / `health` | `h9()` in status.sh | Live system health dashboard (CPU, RAM, disk, net) |
| `fmenu` | `fmenu()` in files.sh | Interactive file operations menu |
| `fa`-`fn` | files.sh | Individual file operations (see README for full list) |

## Shell conventions

- **Zsh-only** — Uses zsh-specific features: `${0:A:h}`, `typeset -g`, `(N)` glob qualifier, `local -A` (assoc arrays), `${var:t}` (tail), `${var/#pat/rep}`
- **Path resolution**: `SHELL_V11_DIR="${0:A:h}"` resolves the directory of the sourced script. Modules one level deep use `"${0:A:h:h}"` to get the parent.
- **Color output**: `print_success`, `print_error`, `print_warning`, `print_info`, `print_header` from utils.sh
- **Confirmation**: `confirm "message" "default"` returns 0 (yes) or 1 (no)
- **Clipboard**: `copy_to_clipboard` pipes stdin to `pbcopy` (macOS) / `xclip` / `xsel`. Uses `${=_CLIPBOARD_CMD}` for safe word splitting (no `eval`).
- **Human-readable sizes**: `_human_size()` in status.sh converts `du` block counts (512-byte blocks) to KB/MB/GB
- **Command naming**: Short alphanumeric codes (a1, b2, c3...) chosen for fast typing
- **Variable safety**: All `read` commands use `-r` flag. Local variables declared with `local`. Passwords use `read -rs`.

## Release process

1. Edit source files in `mrtamaki-1.7.0/`
2. Update `MRTAMAKI_VERSION` in `mrtamaki.sh` and `VERSION_TEXT` in `banner.py`
3. Update `version` in `Casks/mrtamaki.rb`
4. Run `./build-release.sh` (auto-detects version from `mrtamaki.sh` if no argument given) — creates ZIP and prints SHA256
5. Create GitHub release: `gh release create v<version> ./mrtamaki-<version>.zip --title "v<version>" --notes "..."`
6. Update `sha256` in `Casks/mrtamaki.rb` with the value from step 4
7. Commit and push

**Three version strings must stay in sync**: `MRTAMAKI_VERSION` in `mrtamaki.sh`, `VERSION_TEXT` in `banner.py`, and `version` in `Casks/mrtamaki.rb`.

## Environment variables

### User-configured (in ~/.zshenv)

- `IPROYAL_USER` / `IPROYAL_PASS` — IPRoyal proxy credentials (a1, a3)
- `OXYLABS_USER` / `OXYLABS_PASS` — Oxylabs proxy credentials (a2, a4)
- `SCAMALYTICS_API_KEY` — Scamalytics IP check (d4)
- `ONELOOKUP_API_KEY` — 1Lookup API (d5, iplookup, everify, etc.)
- `MRTAMAKI_NO_BANNER` — Set to `1` to skip the startup banner animation

### Internal (set by mrtamaki.sh)

- `SHELL_V11_DIR` — Absolute path to the source directory (resolved via `${0:A:h}`)
- `MRTAMAKI_VERSION` — Current version string
- `VENV_PYTHON` — Set by `_ensure_module_venv()` to the active venv's Python path

## Common pitfalls

- **Zsh reserved variable names**: Never use `path` as a local variable — in zsh it's a special array tied to `$PATH`. Assigning a scalar to it corrupts `PATH` and breaks all command lookups. Use `cache_path`, `file_path`, etc. Other reserved names to avoid: `fpath`, `cdpath`, `mailpath`, `manpath`.
- **readchar.key constants**: Use `readchar.key.ESC` (not `.ESCAPE`). Version 4.x has: `UP`, `DOWN`, `ENTER`, `ESC`, `BACKSPACE`, `DELETE`, etc.
- **readchar + Rich.Live threading**: Never use `auto_refresh=True` with `readchar.readkey()` in the same or sibling thread. The Live refresh thread's output causes `TCSADRAIN` waits, and readchar's `TCSAFLUSH` discards buffered escape sequence bytes. Always use `auto_refresh=False` and call `live.update(..., refresh=True)` manually.
- **macOS du**: Does not support `--apparent-size`. Use `du -sh` only.
- **Source directory name**: The directory is `mrtamaki-1.7.0/` regardless of the actual release version. `build-release.sh` auto-detects it by looking for a `mrtamaki-*/` directory containing `mrtamaki.sh`.
- **Version strings**: Three files must be updated together when bumping versions: `mrtamaki.sh` (`MRTAMAKI_VERSION`), `banner.py` (`VERSION_TEXT`), and `Casks/mrtamaki.rb` (`version`).
- **Files/ capitalization**: The file operations module directory is `Files/` with a capital F. Shell source paths use `"${SHELL_V11_DIR}/Files/files.sh"` — note the mixed case.
- **Legacy files**: `ensure_venv_manager` and `status_bar.py` still exist in the source directory but are NOT sourced or used by any current code path. They are kept for reference only.

# mrtamaki Python CLI Migration Plan

Convert mrtamaki from a Zsh toolkit to a Python CLI with shell aliases for backward compatibility.

---

## Overview

| Phase | Scope | Est. Effort |
|-------|-------|-------------|
| 1 | Project scaffold + `mt` entry point | 1–2 hrs |
| 2 | `mt proxy` (a1, a2, a3, a4, b2) | 2–3 hrs |
| 3 | `mt ip` (c3, d4, d6) | 1–2 hrs |
| 4 | `mt sys` (h1–h10, smenu, h9, e5, g7) | 3–4 hrs |
| 5 | `mt lookup` (wire to one_lookup) | 1 hr |
| 6 | `mt file` (f command) | 2–3 hrs |
| 7 | Shell wrapper + aliases | 1 hr |
| 8 | Testing, docs, release | 2–3 hrs |

**Total: ~15–20 hours**

---

## Phase 1: Project Scaffold

### 1.1 Create `pyproject.toml` at repo root

```toml
[project]
name = "mrtamaki"
version = "1.12.0"
description = "CLI toolkit for proxy, IP, system, lookup, and file operations"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "typer[all]>=0.9",
    "rich>=13",
    "readchar>=4",
    "requests>=2",
    "httpx>=0.25",
    "pyperclip>=1.8",
    "psutil>=5",
    "PySocks>=1.7",
    "dnspython>=2",
]

[project.scripts]
mt = "mrtamaki.cli:app"
mrtamaki = "mrtamaki.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 1.2 Directory structure

```
mrtamaki-1.11.1/
├── pyproject.toml
├── mrtamaki/
│   ├── __init__.py          # __version__
│   ├── cli.py               # Typer app, subcommand groups
│   ├── _utils.py            # Shared: print_*, clipboard, Rich console
│   ├── proxy/
│   │   ├── __init__.py
│   │   ├── cli.py           # mt proxy subcommands
│   │   └── ...
│   ├── ip/
│   │   ├── __init__.py
│   │   └── cli.py
│   ├── sys/
│   │   ├── __init__.py
│   │   └── cli.py
│   ├── lookup/              # Reuse existing one_lookup package
│   │   └── cli.py           # Thin wrapper
│   └── file/
│       ├── __init__.py
│       └── cli.py
├── lookup/                  # Keep as-is (one_lookup package)
│   └── one_lookup/
├── proxy/
│   └── proxy_converter/     # Keep as-is
├── sys/
│   ├── clean_menu.py        # Keep as-is
│   └── health_dashboard.py  # Keep as-is (h9)
└── mrtamaki.sh              # Slim shell wrapper (Phase 7)
```

### 1.3 Minimal `mrtamaki/cli.py`

```python
import typer
from mrtamaki.proxy.cli import app as proxy_app
from mrtamaki.ip.cli import app as ip_app
from mrtamaki.sys.cli import app as sys_app
from mrtamaki.lookup.cli import app as lookup_app
from mrtamaki.file.cli import app as file_app

app = typer.Typer(
    name="mt",
    help="mrtamaki CLI — proxy, IP, system, lookup, file tools",
    no_args_is_help=True,
)

app.add_typer(proxy_app, name="proxy")
app.add_typer(ip_app, name="ip")
app.add_typer(sys_app, name="sys")
app.add_typer(lookup_app, name="lookup")
app.add_typer(file_app, name="file")

@app.callback()
def main(ctx: typer.Context):
    """mrtamaki v1.12.0 — Zsh toolkit as Python CLI"""
    pass
```

### 1.4 Shared utilities (`mrtamaki/_utils.py`)

```python
"""Shared utilities for mrtamaki CLI."""
import os
import subprocess
import sys
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

# Constants (from utils.sh)
PORT_MIN = 1
PORT_MAX = 64900
NETWORK_TIMEOUT = 10
MAX_FILE_SIZE = "100M"
VENV_SEARCH_DEPTH = 5
SESSION_ID_LENGTH = 8

console = Console()
console_err = Console(stderr=True)


def print_success(msg: str) -> None:
    console.print(f"[green]✓[/green] {msg}")


def print_error(msg: str) -> None:
    console_err.print(f"[red]✗[/red] {msg}")


def print_warning(msg: str) -> None:
    console.print(f"[yellow]⚠[/yellow] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[cyan]ℹ[/cyan] {msg}")


def print_header(msg: str) -> None:
    console.print(f"\n[bold blue]═══ {msg} ═══[/bold blue]\n")


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard. Returns True on success."""
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    # Fallback: pbcopy (macOS), xclip, xsel
    for cmd in ["pbcopy", "xclip -selection clipboard", "xsel --clipboard --input"]:
        try:
            subprocess.run(cmd.split(), input=text.encode(), check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return False


def confirm(prompt: str, default: str = "n") -> bool:
    """Prompt for Y/N. Default 'y' or 'n'."""
    default_bool = default.lower() in ("y", "yes")
    return Confirm.ask(prompt, default=default_bool)


def human_size(blocks_512: int) -> str:
    """Convert du block count (512-byte blocks) to human-readable string."""
    b = blocks_512 * 512
    if b >= 1073741824:
        return f"{b / 1073741824:.1f} GB"
    if b >= 1048576:
        return f"{b / 1048576:.1f} MB"
    if b >= 1024:
        return f"{b / 1024:.1f} KB"
    return f"{b} B"
```

---

## Phase 2: `mt proxy`

### 2.1 Commands to implement

| Shell | Python subcommand | Notes |
|-------|-------------------|-------|
| a1 | `mt proxy iproyal` | Generate IPRoyal URL, optional `--city`, `--country` |
| a2 | `mt proxy oxylabs` | Generate Oxylabs URL |
| a3 | `mt proxy iproyal-speed` | Generate → bind → test → check (interactive) |
| a4 | `mt proxy oxylabs-speed` | Same for Oxylabs |
| b2 | `mt proxy convert` | Delegate to `proxy_converter.py` |

### 2.2 Implementation details

- **a1/a2**: Pure Python — `secrets.token_hex()`, `random.choice(ports)`, build URL string
- **Credentials**: `os.environ.get("IPROYAL_USER")` etc.; prompt if missing (use `typer.prompt` with `hide_input=True` for password)
- **Clipboard**: `pyperclip.copy(proxy_url)`
- **a3/a4**: Subprocess `proxy_converter.py --cli --bind <url> --wait`; poll clipboard for port; call `mt ip test` and `mt ip check` internally
- **b2**: Subprocess or import `proxy_converter` main; preserve `--help` flags

### 2.3 Proxy URL formats

**IPRoyal (a1)**:
```
{user}:{pass}_country-{country}_city-{city}_session-{session}_lifetime-{lifetime}@{endpoint}
```
- Ports: `[51200, 32325, 12325]`
- Endpoint: `geo.iproyal.com:{port}`
- Country: `nz`, lifetime: `168h`
- Session: 8 alphanumeric chars

**Oxylabs (a2)**:
```
customer-{user}-cc-{country}-city-{city}-sessid-{sessid}-sesstime-{sesstime}:{pass}@{endpoint}
```
- Endpoint: `pr.oxylabs.io:7777`
- Country: `nz`, sesstime: `145`
- Sessid: 10 digits

### 2.4 proxy_converter.py CLI interface

```
--cli          Run in CLI mode
--bind <url>   Bind SOCKS5 proxy (user:pass@host:port)
--list         List current proxies
--debug        Enable debug mode
--wait         Keep running after --bind (for background use)
```

### 2.5 File: `mrtamaki/proxy/cli.py`

```python
import typer
app = typer.Typer(help="Proxy tools: IPRoyal, Oxylabs, converter")

@app.command()
def iproyal(
    city: str = typer.Option("christchurch", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
):
    """Generate IPRoyal proxy URL (a1)."""
    ...

@app.command()
def oxylabs(
    city: str = typer.Option("auckland", "--city", "-c"),
    country: str = typer.Option("nz", "--country"),
):
    """Generate Oxylabs proxy URL (a2)."""
    ...

@app.command("iproyal-speed")
def iproyal_speed(...):
    """IPRoyal speed run: generate → bind → test → check (a3)."""
    ...

@app.command("oxylabs-speed")
def oxylabs_speed(...):
    """Oxylabs speed run (a4)."""
    ...

@app.command()
def convert(
    bind: Optional[str] = typer.Option(None, "--bind", "-b"),
    list_proxies: bool = typer.Option(False, "--list", "--ls", "-l"),
    clean: bool = typer.Option(False, "--clean", "-c"),
    debug: bool = typer.Option(False, "--debug", "-d"),
    wait: bool = typer.Option(False, "--wait", "-w"),
    check: bool = typer.Option(False, "--check", "-k"),
):
    """Proxy converter (b2). No args = interactive TUI."""
    ...
```

---

## Phase 3: `mt ip`

### 3.1 Commands

| Shell | Python subcommand | Notes |
|-------|-------------------|-------|
| c3 | `mt ip test [port]` | No port = system IP; use httpx with proxy |
| d4 | `mt ip check [ip]` | Scamalytics API; auto-detect IP if omitted |
| d6 | `mt ip dnsleak [port]` | DNS leak test via dnscheck.tools |

### 3.2 Implementation

- **c3**: `httpx.get("https://ipinfo.io/json", proxy=...)` or no proxy
- **d4**: `httpx.get` Scamalytics API; parse JSON (no jq)
- **d6**: `dns_leak.py` exists — call as subprocess or import

### 3.3 API references

| Command | URL / Tool | Notes |
|---------|------------|-------|
| c3 | `https://ipinfo.io/json` | Proxy via `httpx` `proxy` param |
| d4 | `https://api11.scamalytics.com/v3/bradeysulley/?key={SCAMALYTICS_API_KEY}&ip={ip}` | Requires API key |
| d6 | `ip/dns_leak.py` | Stdlib only; with port: use proxychains4 + temp config |

### 3.4 dns_leak.py invocation

- **No port**: `python3 ip/dns_leak.py`
- **With port**: Create temp proxychains config, run `proxychains4 -f <config> python3 ip/dns_leak.py`
- Config format: `strict_chain`, `proxy_dns`, `[ProxyList]`, `http 127.0.0.1 {port}`

### 3.5 File: `mrtamaki/ip/cli.py`

```python
from typing import Optional
import typer
app = typer.Typer(help="IP tools: test proxy, Scamalytics check, DNS leak")

@app.command()
def test(port: Optional[int] = typer.Argument(None, help="Proxy port; omit for system IP")):
    """Test proxy or system IP via ipinfo.io (c3)."""
    ...

@app.command()
def check(ip: Optional[str] = typer.Argument(None, help="IP to check; omit to use system IP")):
    """Scamalytics IP reputation check (d4)."""
    ...

@app.command()
def dnsleak(port: Optional[int] = typer.Argument(None, help="Proxy port; omit for system DNS")):
    """DNS leak test via dnscheck.tools (d6)."""
    ...
```

---

## Phase 4: `mt sys`

### 4.1 Commands

| Shell | Python subcommand | Notes |
|-------|-------------------|-------|
| h1 | `mt sys pycache` | Clean `__pycache__` |
| h2 | `mt sys browser` | Clear browser caches |
| h3 | `mt sys app` | Clear app caches |
| h4 | `mt sys venv` | Clean venvs |
| h5 | `mt sys space` | Reclaimable space overview |
| h6 | `mt sys xcode` | Xcode DerivedData |
| h7 | `mt sys node` | node_modules |
| h8/smenu | `mt sys menu` | Run `clean_menu.py` (shell wrapper for cd/delete) |
| h9 | `mt sys health` | Run `health_dashboard.py` |
| h10 | `mt sys dns` | Flush DNS (subprocess `sudo dscacheutil...`) |
| (trash) | `mt sys trash` | Empty trash (from clean_menu) |
| e5 | `mt sys venv-purge [path]` | Find and purge venvs |
| g7 | `mt sys pip [venv]` | Pip purge |

### 4.2 Implementation strategy

- **h1–h7, h10**: Port shell logic to Python (`pathlib`, `shutil.rmtree`, `subprocess.run`)
- **h8, h9**: Subprocess to existing `clean_menu.py` and `health_dashboard.py`; pass `MRTAMAKI_DIR` or `--result-file` for IPC
- **Menu → command dispatch**: Currently shell reads `__CLEAN_CMD__:h1` and runs `h1()`. For Python CLI, either:
  - **Option A**: Menu writes command; Python CLI re-invokes itself: `mt sys pycache` (no cd support)
  - **Option B**: Menu returns exit code + path in stdout; wrapper script handles `cd`
- **e5, g7**: Port from sys.sh

### 4.3 macOS path constants

| Category | Paths |
|----------|-------|
| Search paths (h1, h4, h5, h7) | `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Projects` (+ `MRTAMAKI_DIR` for venvs) |
| Browser caches | Safari: `~/Library/Caches/com.apple.Safari`, Chrome: `~/Library/Caches/Google/Chrome`, Firefox: `~/Library/Caches/Firefox` |
| App cache | `~/Library/Caches` (all subdirs) |
| Xcode | `~/Library/Developer/Xcode/DerivedData` |
| Trash | `~/.Trash` |
| Venv names | `venv`, `.venv`, `env`, `pyenv`, `venv-*` |

### 4.4 clean_menu IPC protocol

**Invocation**: `clean_menu.py --result-file <tmpfile>`

**Result format** (written to file):
- `__CLEAN_CMD__:pycache` → run `mt sys pycache`
- `__CLEAN_CMD__:browser` → run `mt sys browser`
- `__CLEAN_CMD__:appcache` → run `mt sys app`
- `__CLEAN_CMD__:xcode` → run `mt sys xcode`
- `__CLEAN_CMD__:nodemod` → run `mt sys node`
- `__CLEAN_CMD__:trash` → run `mt sys trash` (add subcommand)
- `__CLEAN_CMD__:__DELETE_VENV__:{path}` → delete venv (confirm + rm -rf)
- `__CLEAN_CMD__:__CD__:{path}` → shell must `cd` (Python cannot)

**Note**: `venvs`, `dupes`, `sizes` are sub-modes; menu handles them internally. Only `pycache`, `browser`, `appcache`, `xcode`, `nodemod`, `trash` + venv actions produce result.

### 4.5 mt sys menu implementation

`mt sys menu` must:
1. Accept `--result-file <path>` (pass through to clean_menu.py)
2. Set `MRTAMAKI_DIR` env var (for clean_menu to find sys/ relative paths)
3. Run `clean_menu.py` via subprocess or direct import
4. Resolve paths: `MRTAMAKI_DIR = Path(__file__).resolve().parents[2]` (from mrtamaki.sys.cli)

### 4.6 smenu shell wrapper (required for cd/delete)

Keep `smenu` as a shell function that:
1. Runs `mt sys menu` (or `clean_menu.py --result-file`) with `MRTAMAKI_DIR` set
2. Reads result file
3. Dispatches: `__CD__:*` → `cd`, `__DELETE_VENV__:*` → confirm + rm, else → `mt sys <cmd>`

```zsh
smenu() {
    local tmp_result
    tmp_result=$(mktemp)
    trap "rm -f $tmp_result" EXIT INT TERM
    MRTAMAKI_DIR="$MRTAMAKI_DIR" mt sys menu --result-file "$tmp_result"
    local output
    [[ -f "$tmp_result" ]] && output=$(<"$tmp_result")
    # Parse __CLEAN_CMD__:... and dispatch
    ...
}
```

### 4.7 cd from menu

For `__CD__:path` from clean_menu: Python cannot change shell cwd. **Solution**: Keep `smenu` / `h8` as a shell function (see 4.6) that runs the menu and handles cd/delete locally.

---

## Phase 5: `mt lookup`

### 5.1 Commands

| Shell | Python subcommand | Notes |
|-------|-------------------|-------|
| d5/found | `mt lookup` (no args) | Menu |
| iplookup | `mt lookup ip <ip>` | |
| everify | `mt lookup email <email>` | |
| eappend | `mt lookup eappend ...` | |
| reappend | `mt lookup reappend <email>` | |
| ripappend | `mt lookup ripappend <ip>` | |

### 5.2 Implementation

Thin wrapper in `mrtamaki/lookup/cli.py` that forwards to `one_lookup.cli`. The existing `one_lookup.cli` uses argparse with subparsers: `menu`, `ip`, `email`, `eappend`, `reappend`, `ripappend`.

**Option A — subprocess**: Run `python -m one_lookup.cli` with args. Requires `lookup/` on PYTHONPATH or install one_lookup as dependency.

**Option B — import**: Add `lookup/` to `sys.path`, import `one_lookup.cli.main`, manipulate `sys.argv`, call it.

```python
# mrtamaki/lookup/cli.py
import sys
from pathlib import Path
import typer

# Resolve lookup package (sibling to mrtamaki package)
_LOOKUP_DIR = Path(__file__).resolve().parents[2] / "lookup"
if str(_LOOKUP_DIR) not in sys.path:
    sys.path.insert(0, str(_LOOKUP_DIR))

app = typer.Typer(help="1Lookup API: IP, email, append lookups")

def _run_one_lookup(args: list) -> int:
    from one_lookup.cli import main
    old_argv = sys.argv
    sys.argv = ["one_lookup"] + args
    try:
        return main()
    finally:
        sys.argv = old_argv

@app.command()
def menu():
    """Interactive 1Lookup menu (d5/found)."""
    raise typer.Exit(_run_one_lookup(["menu"]))

@app.command()
def ip(ip_addr: str = typer.Argument(...), raw: bool = False, no_summary: bool = False, timeout: int = 10):
    """IP lookup (iplookup)."""
    args = ["ip", ip_addr]
    if raw: args.append("--raw")
    if no_summary: args.append("--no-summary")
    args.extend(["--timeout", str(timeout)])
    raise typer.Exit(_run_one_lookup(args))

@app.command()
def email(email_addr: str = typer.Argument(...), raw: bool = False, no_summary: bool = False, timeout: int = 10):
    """Email verification (everify)."""
    args = ["email", email_addr]
    if raw: args.append("--raw")
    if no_summary: args.append("--no-summary")
    args.extend(["--timeout", str(timeout)])
    raise typer.Exit(_run_one_lookup(args))

@app.command()
def eappend(first_name: str, last_name: str, city: str, zip_code: str, address: Optional[str] = None, ...):
    """Find email from person info."""
    ...

@app.command()
def reappend(email: str, ...):
    """Reverse email lookup."""
    ...

@app.command()
def ripappend(ip_addr: str, ...):
    """Reverse IP lookup."""
    ...
```

**Default (no subcommand)**: `mt lookup` with no args → menu. Use `@app.callback(invoke_without_command=True)` and default to menu.

---

## Phase 6: `mt file`

### 6.1 Commands (map `f --x` to `mt file x`)

| f flag | mt file subcommand | Notes |
|--------|-------------------|-------|
| --ez | `mt file zshrc` | Edit .zshrc with backup |
| --s | `mt file search <term>` | Recursive search |
| --m | `mt file mkdir <dir>` | mkdir + cd (print path for cd) |
| --o | `mt file open-last` | Open last modified file |
| --l | `mt file large` | Find large files |
| --t | `mt file tempdir` | Create temp dir (print path) |
| --b | `mt file backup <file>` | Backup with timestamp |
| --d | `mt file desktop [name]` | Desktop folder |
| --tr | `mt file tree [depth]` | Directory tree |
| --ba | `mt file bookmark-add [name]` | |
| --bg | `mt file bookmark-go [name]` | |
| --bl | `mt file bookmark-list` | |
| --bd | `mt file bookmark-del [name]` | |

### 6.2 Modifiers

- `-D path` → `--directory` / `-d`
- `-N count` → `--limit` / `-n`

### 6.3 Bookmark config

- Path: `~/.config/mrtamaki/bookmarks.json`
- Format: `{"name": "/path/to/dir", ...}`
- Python: use `json` module (no jq dependency)

### 6.4 cd semantics

- `f --m`, `f --t`, `f --bg`: Change shell cwd. Python cannot do this.
- **Solution**: Commands print path to stdout only. Shell function `f()` handles cd:

```zsh
f() {
    case "$1" in
        --m)  cd "$(mt file mkdir "$2")" ;;
        --t)  cd "$(mt file tempdir)" ;;
        --bg) cd "$(mt file bookmark-go "$2")" ;;
        *)    mt file "$@" ;;
    esac
}
```

For `--m` and `--bg`, `mt file mkdir` and `mt file bookmark-go` must print the path and nothing else (no headers). Use `--quiet` or similar if needed.

### 6.5 Full f() shell function

```zsh
f() {
    [[ $# -eq 0 ]] && { mt file --help; return 0 }
    case "$1" in
        --m)  cd "$(mt file mkdir "$2")" ;;
        --t)  cd "$(mt file tempdir)" ;;
        --bg) cd "$(mt file bookmark-go "$2")" ;;
        --h|--help) mt file --help ;;
        *)    mt file "$@" ;;
    esac
}
```

All other flags (`--ez`, `--s`, `--o`, `--l`, `--b`, `--d`, `--tr`, `--ba`, `--bl`, `--bd`) pass through to `mt file` with appropriate arg mapping.`

---

## Phase 7: Shell Wrapper + Aliases

### 7.1 Slim `mrtamaki.sh`

Keep from current `mrtamaki.sh`:
- `MRTAMAKI_VERSION`, `SHELL_V11_DIR`, `HOMEBREW_PREFIX`
- `MRTAMAKI_THEMES` array, `tt()` function (theme toggle)
- `ZSH_THEME`, Oh My Zsh sourcing, p10k config
- Banner (optional: `banner.py` or skip)
- `mrtamaki` help function (or `mt --help`)
- Syntax highlighting, autosuggestions, `ls` aliases

Replace with aliases + shell functions:

```zsh
# mrtamaki - Shell integration (theme, OMZ, aliases)
# Tool logic lives in Python CLI: mt / mrtamaki

MRTAMAKI_VERSION="1.12.0"
SHELL_V11_DIR="${0:A:h}"
MRTAMAKI_DIR="$SHELL_V11_DIR"
HOMEBREW_PREFIX="${HOMEBREW_PREFIX:-$(brew --prefix)}"

#--- THEME (unchanged from current mrtamaki.sh) ---
# MRTAMAKI_THEMES, _mrtamaki_theme_idx, ZSH_THEME, tt(), OMZ, p10k
# ... copy lines 27-119 from mrtamaki.sh ...

#--- BANNER (optional) ---
# if [[ -o interactive ]] && [[ -z "$MRTAMAKI_NO_BANNER" ]]; then
#     banner.py or mt --version
# fi

#--- ALIASES: Shortcuts → mt subcommands ---
alias a1='mt proxy iproyal'
alias a2='mt proxy oxylabs'
alias a3='mt proxy iproyal-speed'
alias a4='mt proxy oxylabs-speed'
alias b2='mt proxy convert'

alias c3='mt ip test'
alias d4='mt ip check'
alias d6='mt ip dnsleak'

alias h1='mt sys pycache'
alias h2='mt sys browser'
alias h3='mt sys app'
alias h4='mt sys venv'
alias h5='mt sys space'
alias h6='mt sys xcode'
alias h7='mt sys node'
# h8, smenu: shell function (see below) for cd/delete from menu
alias h9='mt sys health'
alias health='mt sys health'
alias h10='mt sys dns'
alias flushdns='mt sys dns'
alias e5='mt sys venv-purge'
alias g7='mt sys pip'
alias f6='mt file --help'

# smenu: Shell wrapper for cd/delete from clean_menu (Python cannot change cwd)
smenu() {
    local tmp_result
    tmp_result=$(mktemp 2>/dev/null) || { echo "Failed to create temp file"; return 1 }
    trap "rm -f $tmp_result" EXIT INT TERM
    MRTAMAKI_DIR="${MRTAMAKI_DIR:-$SHELL_V11_DIR}" mt sys menu --result-file "$tmp_result"
    local output=""
    [[ -f "$tmp_result" && -s "$tmp_result" ]] && output=$(<"$tmp_result")
    rm -f "$tmp_result"
    trap - EXIT INT TERM
    [[ "$output" != __CLEAN_CMD__:* ]] && return 0
    local cmd="${output#__CLEAN_CMD__:}"
    cmd="${cmd%%$'\n'*}"
    if [[ "$cmd" == __CD__:* ]]; then
        cd "${cmd#__CD__:}" && echo "Changed to: $PWD"
    elif [[ "$cmd" == __DELETE_VENV__:* ]]; then
        local v="${cmd#__DELETE_VENV__:}"
        [[ -d "$v" && -f "$v/bin/activate" ]] && read "?Delete $v? [y/N] " r && [[ "$r" == [yY]* ]] && rm -rf "$v"
    else
        case "$cmd" in
            pycache)  mt sys pycache ;;
            browser)  mt sys browser ;;
            appcache) mt sys app ;;
            xcode)    mt sys xcode ;;
            nodemod)  mt sys node ;;
            trash)    mt sys trash ;;
            *)        echo "Unknown: $cmd" ;;
        esac
    fi
}
alias h8='smenu'

# f: Shell function for cd support on --m, --t, --bg; else delegate to mt file
f() {
    case "$1" in
        --m)  cd "$(mt file mkdir "$2")" ;;
        --t)  cd "$(mt file tempdir)" ;;
        --bg) cd "$(mt file bookmark-go "$2")" ;;
        --h|--help) mt file --help ;;
        *)   mt file "$@" ;;
    esac
}

# Lookup aliases
alias d5='mt lookup'
alias found='mt lookup'
alias 1l='mt lookup'
alias iplookup='mt lookup ip'
alias everify='mt lookup email'
alias eappend='mt lookup eappend'
alias reappend='mt lookup reappend'
alias ripappend='mt lookup ripappend'

# Central command
alias mrtamaki='mt'
```

### 7.2 `mt` availability

- **Homebrew**: Install Python package; `mt` and `mrtamaki` are console scripts
- **Cask**: Postflight runs `pip install -e .` or `uv pip install -e .` into a venv, symlinks `mt` into `bin/`

---

## Phase 8: Testing, Docs, Release

### 8.1 Testing checklist

| Test | Command | Expected |
|------|---------|----------|
| CLI help | `mt --help` | Shows proxy, ip, sys, lookup, file |
| Proxy help | `mt proxy --help` | Lists iproyal, oxylabs, convert |
| IPRoyal gen | `mt proxy iproyal --city auckland` | URL printed, copied to clipboard |
| Oxylabs gen | `mt proxy oxylabs` | URL (requires OXYLABS_*) |
| IP test (system) | `mt ip test` | ipinfo.io JSON, system IP |
| IP test (proxy) | `mt ip test 1080` | Proxy IP via ipinfo |
| IP check | `mt ip check 8.8.8.8` | Scamalytics JSON (requires SCAMALYTICS_*) |
| DNS leak | `mt ip dnsleak` | dnscheck.tools result |
| Sys pycache | `mt sys pycache` | Lists __pycache__, confirm before delete |
| Sys space | `mt sys space` | Reclaimable overview (read-only) |
| Sys menu | `mt sys menu` or `smenu` | clean_menu TUI |
| Sys health | `mt sys health` | health_dashboard TUI |
| Lookup menu | `mt lookup` | one_lookup menu |
| Lookup IP | `mt lookup ip 8.8.8.8` | IP lookup result |
| File tree | `mt file tree -d . -n 3` | Rich tree output |
| File tempdir | `mt file tempdir` | Prints path only |
| Aliases | `a1`, `h1`, `d5` | Same as mt proxy iproyal, mt sys pycache, mt lookup |
| f with cd | `f --m newdir` | Creates dir, cd into it |

### 8.2 Unit tests (pytest)

```
tests/
├── conftest.py      # Fixtures, mock env vars
├── test_utils.py    # _utils: print_*, clipboard, confirm
├── test_proxy.py    # URL generation (no credentials)
├── test_ip.py       # ipinfo parsing, Scamalytics mock
├── test_sys.py      # Path discovery (no deletion)
├── test_file.py     # Bookmark JSON, tree logic
└── test_lookup.py   # one_lookup forwarding
```

### 8.3 Docs

- Update README: Install via `pip install mrtamaki` or `brew install --cask mrtamaki`
- Document `mt --help`, `mt <module> --help`
- Env vars: `IPROYAL_USER`, `IPROYAL_PASS`, `OXYLABS_USER`, `OXYLABS_PASS`, `SCAMALYTICS_API_KEY`, `ONELOOKUP_API_KEY`
- Runtime deps: `jq` (optional for d4), `proxychains4` (for d6 with proxy), `dig` (for d6)

### 8.4 Release checklist

1. Bump version in: `pyproject.toml`, `mrtamaki/__init__.py`, `mrtamaki.sh`, `banner.py` (if used)
2. Run tests: `pytest tests/`
3. Build: `python -m build` or `hatch build`
4. If PyPI: `twine upload dist/*`
5. If Homebrew cask: Update `Casks/mrtamaki.rb` (version, sha256, postflight to `pip install` or `uv pip install`)
6. Tag: `git tag v1.12.0 && git push --tags`

### 8.5 Homebrew cask changes

- **Current**: Cask installs files to `$(brew --prefix)/share/mrtamaki/`, user sources `mrtamaki.sh`
- **New**: Cask installs Python package (or files + venv), creates `mt` / `mrtamaki` in PATH
- Postflight: `pip install -e <installed_path>` or `uv pip install` into a dedicated venv, symlink `mt` to `bin/`
- User still sources `mrtamaki.sh` for theme, aliases, smenu wrapper

---

## Command Mapping Reference

| Shortcut | mt equivalent |
|----------|---------------|
| a1 | mt proxy iproyal |
| a2 | mt proxy oxylabs |
| a3 | mt proxy iproyal-speed |
| a4 | mt proxy oxylabs-speed |
| b2 | mt proxy convert |
| c3 | mt ip test |
| d4 | mt ip check |
| d5, found | mt lookup |
| d6 | mt ip dnsleak |
| e5 | mt sys venv-purge |
| f, f6 | mt file |
| g7 | mt sys pip |
| h1 | mt sys pycache |
| h2 | mt sys browser |
| h3 | mt sys app |
| h4 | mt sys venv |
| h5 | mt sys space |
| h6 | mt sys xcode |
| h7 | mt sys node |
| h8, smenu | mt sys menu |
| h9, health | mt sys health |
| h10, flushdns | mt sys dns |
| iplookup | mt lookup ip |
| everify | mt lookup email |
| tt | (shell only) |

---

## Dependencies Summary

| Python package | Used for |
|----------------|----------|
| typer | CLI framework |
| rich | Colored output, panels, tables |
| readchar | TUI menus (clean_menu, health) |
| requests | 1lookup API |
| httpx | ipinfo, Scamalytics, proxy tests |
| pyperclip | Clipboard copy |
| psutil | Health dashboard |
| PySocks, dnspython | Proxy converter |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `cd` from menus | Shell wrapper for f --m, f --t, f --bg; smenu function for __CD__ |
| h10 (flush DNS) | Requires sudo; subprocess with user prompt |
| Proxy converter clipboard | a3/a4 expect port on clipboard; Python can pass via stdin or flag |
| OneLookup package path | Add lookup/ to sys.path in mrtamaki.lookup.cli |
| clean_menu shared_utils | sys/clean_menu.py imports shared_utils, duplicate_finder; ensure sys.path includes sys/ |

---

## Appendix A: Files to Create vs Reuse

| Action | Path |
|--------|------|
| Create | `pyproject.toml` |
| Create | `mrtamaki/__init__.py`, `cli.py`, `_utils.py` |
| Create | `mrtamaki/proxy/__init__.py`, `cli.py` |
| Create | `mrtamaki/ip/__init__.py`, `cli.py` |
| Create | `mrtamaki/sys/__init__.py`, `cli.py` |
| Create | `mrtamaki/lookup/__init__.py`, `cli.py` |
| Create | `mrtamaki/file/__init__.py`, `cli.py` |
| Reuse | `lookup/one_lookup/` (entire package) |
| Reuse | `proxy/proxy_converter/` (proxy_converter.py, menu_ui.py) |
| Reuse | `sys/clean_menu.py`, `health_dashboard.py`, `duplicate_finder.py`, `shared_utils.py` |
| Reuse | `ip/dns_leak.py` |
| Modify | `mrtamaki.sh` (slim down, add aliases + smenu) |

---

## Appendix B: clean_menu command → mt sys mapping

| clean_menu result | Shell action |
|-------------------|--------------|
| `pycache` | `mt sys pycache` |
| `browser` | `mt sys browser` |
| `appcache` | `mt sys app` |
| `xcode` | `mt sys xcode` |
| `nodemod` | `mt sys node` |
| `trash` | `mt sys trash` |
| `__DELETE_VENV__:{path}` | confirm + rm -rf |
| `__CD__:{path}` | cd {path} |

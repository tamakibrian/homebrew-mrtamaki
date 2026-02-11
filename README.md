# mrtamaki

A Zsh toolkit for macOS, installed via Homebrew. Provides proxy management, IP tools, file utilities, system cleanup, and API integrations — all accessible through short terminal commands.

## Install

```bash
brew tap tamakibrian/mrtamaki
brew install --cask mrtamaki
```

Add to `~/.zshrc` (one-time setup):

```bash
source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
```

The cask automatically installs:
- **JetBrains Mono Nerd Font** (`font-jetbrains-mono-nerd-font`)
- **light-zsh theme** (cloned to `~/.oh-my-zsh/custom/themes/`)
- **zsh-syntax-highlighting** and **zsh-autosuggestions**
- All Python virtual environments (zero-wait first run)

Set your terminal font to "JetBrains Mono Nerd Font" for icon support.

## Commands

Type `mrtamaki` in your terminal to see all available commands.

### Proxy & IP Tools

| Command | Description |
|---------|-------------|
| `a1` | Generate IPRoyal proxy URL (prompts for city) |
| `a2` | Generate Oxylabs proxy URL (prompts for city) |
| `a3` | Speed run: IPRoyal generate → bind → test → check |
| `a4` | Speed run: Oxylabs generate → bind → test → check |
| `b2` | Run proxy converter (Legacy or New, interactive submenu) |
| `c3 <port>` | Test proxy on port, get IP via ipinfo.io + DNS leak test |
| `d4 <ip>` | Scamalytics IP reputation check |
| `d6 [port]` | DNS leak test (check DNS resolver leaks, optional proxy port) |

### System

| Command | Description |
|---------|-------------|
| `h8` / `smenu` | Interactive status menu (cleanup, caches, venvs) |
| `h1` / `pycache` | Clean `__pycache__` directories |
| `h2` / `browsercache` | Clear browser caches (Safari, Chrome, Firefox) |
| `h3` / `appcache` | Clear `~/Library/Caches` |
| `h4` / `venvclean` | Find and delete virtual environments |
| `h5` / `cachesizes` | Cache sizes overview (read-only) |
| `h9` / `health` | Live system health dashboard (CPU, RAM, disk, net) |
| `e5 [path]` | Find and clean up virtual environments |
| `f6` | Flush DNS cache (macOS) |
| `g7 [venv]` | Pip purge — cache + packages (default: system) |

### File Commands

| Command | Description |
|---------|-------------|
| `fmenu` | Interactive file operations menu |
| `fa` | Edit `~/.zshrc` (creates backup, suggests `exec zsh` to reload) |
| `fb <term>` | Recursive file search |
| `fc <dir>` | Make directory and cd into it |
| `fd` | Open last created file |
| `fe` | Find large files (>100M) |
| `ff` | Create and cd into temp directory |
| `fg <file>` | Backup file with timestamp |
| `fh [name]` | Create timestamped folder on Desktop |
| `fj [depth]` | Show directory tree (Rich) |
| `fk [name]` | Bookmark current directory |
| `fl [name]` | Jump to bookmarked directory |
| `fm` | List all bookmarks |
| `fn [name]` | Delete a bookmark |

### 1Lookup API

| Command | Description |
|---------|-------------|
| `d5` / `found` | Interactive 1lookup menu |
| `iplookup <ip>` | IP address lookup |
| `everify <email>` | Email verification |
| `eappend` | Find email from personal info |
| `reappend <email>` | Reverse email lookup |
| `ripappend <ip>` | Reverse IP lookup |

### Aliases

| Alias | Description |
|-------|-------------|
| `cc` | Clear screen |
| `ll` | List files (long format) |
| `la` | List all files (including hidden) |

## Credentials

Add these to `~/.zshenv` as needed:

```bash
export IPROYAL_USER='username'         # for a1, a3
export IPROYAL_PASS='password'         # for a1, a3
export OXYLABS_USER='customer_id'      # for a2, a4
export OXYLABS_PASS='password'         # for a2, a4
export SCAMALYTICS_API_KEY='key'       # for d4
export ONELOOKUP_API_KEY='key'         # for 1lookup commands
```

### Optional settings

```bash
export MRTAMAKI_NO_BANNER=1            # skip startup banner animation
```

## Architecture

### Repository layout

```
TAMAKI/                              # Git repo root (branch: main)
├── README.md                        # This file
├── CLAUDE.md                        # AI agent project guide
├── build-release.sh                 # Creates release ZIP + SHA256 for cask
├── Casks/mrtamaki.rb                # Homebrew cask definition (Ruby)
└── mrtamaki-1.7.0/                  # Source directory
    ├── mrtamaki.sh                  # ENTRYPOINT — sourced from ~/.zshrc
    ├── utils.sh                     # Shared utilities, color helpers, venv manager
    ├── core.sh                      # Main commands: a1-a4, b2, c3, d4, d6, e5-g7
    ├── banner.py                    # Startup banner (Rich)
    ├── status/                      # Status module
    │   ├── status.sh                # Shell wrappers: smenu/h8, h1-h5, h9
    │   ├── status_menu.py           # smenu/h8: interactive cleanup menu (Rich + readchar)
    │   ├── health_dashboard.py      # h9: live system health dashboard (Rich + psutil)
    │   ├── shared_utils.py          # Shared Python utils: themes, byte/speed formatting
    │   └── requirements.txt         # rich, readchar, psutil
    ├── Files/                       # File operations module
    │   ├── files.sh                 # Shell wrappers: fmenu, fa-fn
    │   ├── file_menu.py             # fmenu: interactive file menu (Rich + readchar)
    │   └── requirements.txt         # rich, readchar
    ├── found/                       # 1Lookup API module
    │   ├── one_lookup.zsh           # Shell wrapper: d5/found command
    │   └── one_lookup/              # Python package
    │       ├── __init__.py
    │       ├── client.py            # API client for 1lookup.com
    │       ├── cli.py               # CLI argument parsing
    │       ├── menu_v2.py           # Interactive lookup menu (Rich TUI)
    │       └── ui_utils.py          # Shared UI helpers
    ├── proxy_converter-NEW/         # New proxy converter (Rich + readchar TUI)
    │   ├── proxy_converter.py       # Proxy binding engine + CLI
    │   ├── menu_ui.py               # Interactive two-column menu
    │   └── requirements.txt         # PySocks, rich, readchar, dnspython
    └── proxy_converter-OG/          # Legacy proxy converter
        ├── proxy_converter.py
        └── requirements.txt         # PySocks, tabulate, dnspython
```

### Module loading chain

```
~/.zshrc
 └─ source mrtamaki.sh          # Sets SHELL_V11_DIR, shows banner
    ├─ source utils.sh           # Shared functions, venv manager
    ├─ source core.sh            # a1-a4, b2, c3, d4, d6, e5-g7
    ├─ source Files/files.sh     # File commands: fmenu, fa-fn
    ├─ source found/one_lookup.zsh  # 1Lookup API
    └─ source status/status.sh   # smenu/h8, h1-h5, h9
```

### Virtual environment system

Each module gets its own isolated Python venv, managed by `_ensure_module_venv()` in `utils.sh`. Venvs are created lazily on first use and stored at `<base_dir>/venv-<module>` (e.g., `venv-status`, `venv-files`). Dependencies are pinned to compatible version ranges (e.g., `rich>=13`, `readchar>=4`).

A `mkdir`-based atomic lockfile prevents race conditions when multiple terminal sessions start simultaneously.

The Homebrew cask `postflight` also pre-creates all venvs during install for a zero-wait first run.

**Module → packages mapping** (defined in `utils.sh`):

| Module | Venv name | Packages |
|--------|-----------|----------|
| banner | `venv-banner` | `rich>=13` |
| files | `venv-files` | `rich>=13 readchar>=4` |
| found | `venv-found` | `rich>=13 requests>=2 InquirerPy>=0.3 readchar>=4` |
| status | `venv-status` | `rich>=13 readchar>=4 psutil>=5` |
| proxy | `venv-proxy` | `PySocks>=1.7 rich>=13 readchar>=4 dnspython>=2` |
| proxy-og | `venv-proxy-og` | `PySocks>=1.7 tabulate>=0.9 dnspython>=2` |

### TUI pattern (Rich + readchar)

All interactive menus (`smenu`/`h8`, `fmenu`, `d5`, `b2`) follow the same pattern:

1. Shell function creates venv, creates temp file for IPC
2. Runs Python TUI script with `--result-file <tmpfile>`
3. Python menu uses `rich.live.Live(screen=True, auto_refresh=False)` for alternate-screen rendering
4. User selection is written to temp file with protocol prefix (e.g., `__STATUSMENU_CMD__:<command>`)
5. Shell reads temp file, parses command, dispatches to shell functions

**Important**: `auto_refresh` MUST be `False` when using `readchar` inside a `Live` context. The Live refresh thread races with readchar's terminal calls, causing arrow key sequences to be silently dropped.

### Proxy converter workflow

The proxy converter binds SOCKS5 proxies to local HTTP ports (range 6700–6900). The proxy URL format contains city information:

- **IPRoyal**: `user:pass_country-nz_city-christchurch_session-xxx@geo.iproyal.com:12321`
- **Oxylabs**: `customer-user-cc-nz-city-auckland-sessid-xxx:pass@pr.oxylabs.io:7777`

The TUI displays active proxies by city name and local port (e.g., `Auckland  127.0.0.1:6705`). DNS resolution uses Cloudflare (1.1.1.1) with DoH fallback.

Speed-run commands (`a3`/`a4`) launch the proxy in the background and register a `trap` to kill the process on Ctrl+C, preventing orphaned proxy processes.

## Development

### Prerequisites

- macOS with Zsh
- Python 3 (`brew install python`)
- jq (`brew install jq`)
- Oh My Zsh (for light-zsh theme)

### Running locally (without Homebrew)

```bash
# Clone and source directly
git clone https://github.com/tamakibrian/homebrew-mrtamaki.git TAMAKI
cd TAMAKI
source mrtamaki-1.7.0/mrtamaki.sh
```

### Release process

1. Edit source files in `mrtamaki-1.7.0/`
2. Update version in three places:
   - `MRTAMAKI_VERSION` in `mrtamaki.sh`
   - `VERSION_TEXT` in `banner.py`
   - `version` in `Casks/mrtamaki.rb`
3. Run `./build-release.sh` to create ZIP and get SHA256
4. Create a GitHub release: `gh release create v<version> ./mrtamaki-<version>.zip`
5. Update `sha256` in `Casks/mrtamaki.rb` with the value from step 3
6. Commit and push

### Common pitfalls

- **Zsh reserved variable names**: Never use `path` as a local variable — it's tied to `$PATH`. Use `file_path`, `cache_path`, etc. Also avoid: `fpath`, `cdpath`, `mailpath`, `manpath`.
- **readchar + Rich.Live threading**: Never use `auto_refresh=True` with `readchar.readkey()`. The Live refresh thread's output causes terminal state conflicts. Use `auto_refresh=False` and `live.update(..., refresh=True)`.
- **readchar.key constants**: Use `readchar.key.ESC` (not `.ESCAPE`). Version 4.x has: `UP`, `DOWN`, `ENTER`, `ESC`, `BACKSPACE`, `DELETE`.
- **macOS du**: Does not support `--apparent-size`. Use `du -sh` only.
- **Source directory name**: `mrtamaki-1.7.0/` does not change per release. `build-release.sh` auto-detects it.
- **Version sync**: `mrtamaki.sh`, `banner.py`, and `Casks/mrtamaki.rb` must all have the same version string.

## Update

```bash
brew update && brew reinstall --cask mrtamaki && exec zsh
```

## Uninstall

```bash
brew uninstall --cask mrtamaki && brew untap tamakibrian/mrtamaki
```

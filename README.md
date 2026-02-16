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
| `b2 [flags]` | Proxy converter (`b2 --help` for all flags) |
| `c3 [port]` | Test proxy on port / check system IP + DNS leak test |
| `d4 [ip]` | Scamalytics IP reputation check (auto-detects system IP) |
| `d6` | DNS leak test via dnscheck.tools |

### System

| Command | Description |
|---------|-------------|
| `h8` / `smenu` | Interactive system cleaner TUI (caches, dupes, trash, venvs) |
| `h1` / `pycache` | Clean `__pycache__` directories |
| `h2` / `browsercache` | Clear browser caches (Safari, Chrome, Firefox) |
| `h3` / `appcache` | Clear `~/Library/Caches` |
| `h4` / `venvclean` | Find and delete virtual environments |
| `h5` / `cachesizes` | Reclaimable space overview (read-only) |
| `h6` / `xcodedata` | Clear Xcode DerivedData |
| `h7` / `nodemod` | Clean node_modules directories |
| `h9` / `health` | Live system health dashboard (CPU, RAM, disk, net) |
| `h10` / `flushdns` | Flush DNS cache (macOS) |
| `e5 [path]` | Find and clean up virtual environments |
| `f6` | Show file operations help |
| `g7 [venv]` | Pip purge — cache + packages (default: system) |

### File Commands

The `f` command provides flag-based file and directory operations. Run `f --h` or `f` with no arguments for full help.

| Command | Description |
|---------|-------------|
| `f --ez` | Edit `~/.zshrc` (creates backup, suggests `exec zsh` to reload) |
| `f --s <term>` | Recursive file search |
| `f --m <dir>` | Make directory and cd into it |
| `f --o` | Open last modified file |
| `f --l` | Find large files (>100M) |
| `f --t` | Create and cd into temp directory |
| `f --b <file>` | Backup file with timestamp |
| `f --d [name]` | Create timestamped folder on Desktop |
| `f --tr [depth]` | Show directory tree (Rich) |
| `f --ba [name]` | Bookmark: add current directory |
| `f --bg [name]` | Bookmark: go to a bookmark |
| `f --bl` | Bookmark: list all bookmarks |
| `f --bd [name]` | Bookmark: delete a bookmark |

**Modifiers** (for `--tr`, `--s`, `--l`):

| Modifier | Description |
|----------|-------------|
| `-D <path>` | Set target directory (default: current dir) |
| `-N <number>` | Set limit: tree depth / max results |

Examples:
```bash
f --tr -D ~/projects -N 4    # Tree of ~/projects, depth 4
f --s "TODO" -D ./src -N 20  # Search "TODO" in ./src, max 20 results
f --l -D ~/Downloads -N 10   # Large files in ~/Downloads, show top 10
```

### Proxy Converter (`b2`)

The `b2` command supports flag-based CLI usage alongside the interactive TUI. Run `b2 --help` for full help.

| Flag | Description |
|------|-------------|
| `b2` | Launch interactive TUI |
| `b2 --bind <proxy>` | Bind a SOCKS5 proxy (`user:pass@host:port`) |
| `b2 --a1 [count] [city]` | Generate & bind IPRoyal proxies |
| `b2 --a2 [count] [city]` | Generate & bind Oxylabs proxies |
| `b2 --list` | List active proxy bindings |
| `b2 --clean` | Remove `~/.bindproxy.json` |
| `b2 --debug` | Enable debug output (combine with other flags) |
| `b2 --wait` | Keep running after `--bind` (for background use) |

Examples:
```bash
b2 --a1 3 auckland          # 3 IPRoyal proxies in Auckland
b2 --a2 2                   # 2 Oxylabs proxies (default city)
b2 --bind user:pass@h:1080  # bind proxy directly
b2 --ls                     # show active proxies
b2 -d --a1 2 wellington     # 2 IPRoyal + debug output
```

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
└── mrtamaki-1.11.1/                  # Source directory
    ├── mrtamaki.sh                  # ENTRYPOINT — sourced from ~/.zshrc
    ├── utils.sh                     # Shared utilities, color helpers, venv manager
    ├── core.sh                      # Main commands: a1-a4, b2, c3, d4, d6, e5-g7
    ├── banner.py                    # Startup banner (Rich)
    ├── clean/                       # System cleaner module
    │   ├── clean.sh                 # Shell wrappers: smenu/h8, h1-h7, h10
    │   ├── clean_menu.py            # smenu/h8: interactive cleaner TUI (Rich + readchar)
    │   ├── duplicate_finder.py      # SHA256 duplicate file finder engine
    │   ├── shared_utils.py          # Shared Python utils: themes, byte/speed formatting
    │   └── requirements.txt         # rich, readchar, psutil
    ├── status/                      # Status module
    │   ├── status.sh                # Shell wrapper: h9 (health dashboard)
    │   ├── health_dashboard.py      # h9: live system health dashboard (Rich + psutil)
    │   ├── shared_utils.py          # Shared Python utils: themes, byte/speed formatting
    │   └── requirements.txt         # rich, readchar, psutil
    ├── files/                       # File operations module
    │   ├── f.sh                     # Shell functions: f command with --flags
    │   └── requirements.txt         # rich, readchar
    ├── found/                       # 1Lookup API module
    │   ├── one_lookup.zsh           # Shell wrapper: d5/found command
    │   └── one_lookup/              # Python package
    │       ├── __init__.py
    │       ├── client.py            # API client for 1lookup.com
    │       ├── cli.py               # CLI argument parsing
    │       ├── menu_v2.py           # Interactive lookup menu (Rich TUI)
    │       └── ui_utils.py          # Shared UI helpers
    ├── proxy_converter/             # Proxy converter
    │   ├── proxy_converter.py       # Proxy binding engine + CLI
    │   ├── menu_ui.py               # Interactive two-column menu
    │   └── requirements.txt         # PySocks, rich, readchar, dnspython
```

### Module loading chain

```
~/.zshrc
 └─ source mrtamaki.sh          # Sets SHELL_V11_DIR, shows banner
    ├─ source utils.sh           # Shared functions, venv manager
    ├─ source core.sh            # a1-a4, b2, c3, d4, d6, e5-g7
    ├─ source files/f.sh         # File commands: f --<flag>
    ├─ source found/one_lookup.zsh  # 1Lookup API
    ├─ source status/status.sh   # h9 (health dashboard)
    └─ source clean/clean.sh     # smenu/h8, h1-h7, h10 (system cleaner)
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
| clean | `venv-clean` | `rich>=13 readchar>=4 psutil>=5` |

### TUI pattern (Rich + readchar)

All interactive menus (`smenu`/`h8`, `d5`, `b2`) follow the same pattern:

1. Shell function creates venv, creates temp file for IPC
2. Runs Python TUI script with `--result-file <tmpfile>`
3. Python menu uses `rich.live.Live(screen=True, auto_refresh=False)` for alternate-screen rendering
4. User selection is written to temp file with protocol prefix (e.g., `__CLEAN_CMD__:<command>`)
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
source mrtamaki-1.11.1/mrtamaki.sh
```

### Release process

1. Edit source files in `mrtamaki-1.11.1/`
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
- **Source directory name**: `mrtamaki-1.11.1/` does not change per release. `build-release.sh` auto-detects it.
- **Version sync**: `mrtamaki.sh`, `banner.py`, and `Casks/mrtamaki.rb` must all have the same version string.

## Update

```bash
brew update && brew reinstall --cask mrtamaki && exec zsh
```

## Uninstall

```bash
brew uninstall --cask mrtamaki && brew untap tamakibrian/mrtamaki
```

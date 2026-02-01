# mrtamaki

A comprehensive Zsh toolkit for macOS that provides proxy management, IP tools, file operations, and API integrations.

## Version

**1.5.0**

## Features

- **Proxy Tools** - Generate proxy URLs for IPRoyal and Oxylabs, convert proxy formats, test proxies
- **IP Intelligence** - IP lookups, reputation checks via Scamalytics, reverse lookups
- **File Operations** - Interactive file menu, bookmarks, tree view, backups, search
- **1lookup API** - Email verification, IP lookups, reverse email/IP append
- **Virtual Environment Management** - Automatic venv creation and dependency handling
- **Shell Enhancements** - Syntax highlighting, autosuggestions, Powerlevel10k theme

## Installation

### Via Homebrew (Recommended)

```bash
brew tap tamakibrian/mrtamaki
brew install --cask mrtamaki
```

Then add to your `~/.zshrc`:

```bash
source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
```

Reload your shell:

```bash
exec zsh
```

### Manual Installation

1. Clone the repository
2. Source `mrtamaki.sh` in your `~/.zshrc`:

```bash
source "/path/to/mrtamaki/mrtamaki.sh"
```

## Commands

### Proxy & IP Tools

| Command | Description |
|---------|-------------|
| `a1` | Generate IPRoyal proxy URL with random session ID |
| `a2` | Generate Oxylabs proxy URL with random session ID |
| `b2` | Run proxy converter (Legacy or New version) |
| `c3 <port>` | Test proxy on port, retrieve and copy IP |
| `d4 <ip>` | Scamalytics IP reputation check |

### System

| Command | Description |
|---------|-------------|
| `e5 [path]` | Find and clean up virtual environments |
| `f6` | Flush DNS cache (macOS) |
| `g7 [venv]` | Pip purge - clear cache and uninstall packages |

### File Commands

| Command | Description |
|---------|-------------|
| `fmenu` | Interactive file operations menu |
| `fa` | Edit `~/.zshrc` with backup and auto-reload |
| `fb <term>` | Recursive file search |
| `mkcd <dir>` | Make directory and cd into it |
| `flast` | Open last created file |
| `fe` | Find large files (>100M) |
| `ff <file>` | Backup file with timestamp |
| `fg [name]` | Create timestamped folder on Desktop |
| `tempdir` | Create and cd into temp directory |
| `ftree [depth]` | Show directory tree (Rich-powered) |

### Bookmark System

| Command | Description |
|---------|-------------|
| `fbook [name]` | Bookmark current directory |
| `fgo [name]` | Jump to bookmarked directory |
| `flist` | List all bookmarks |
| `fdel [name]` | Delete a bookmark |

### 1lookup API

| Command | Description |
|---------|-------------|
| `d5` / `found` / `onelookup` | Interactive 1lookup menu |
| `iplookup <ip>` | IP address lookup |
| `everify <email>` | Email verification |
| `eappend <first> <last> <city> <zip>` | Find email from personal info |
| `reappend <email>` | Reverse email lookup |
| `ripappend <ip>` | Reverse IP lookup |
| `found --help` | Show detailed 1lookup help |

### Aliases

| Alias | Command |
|-------|---------|
| `cc` | `clear` |
| `ll` | `ls -lhG` |
| `la` | `ls -lahG` |
| `kk` | Edit `~/.p10k.zsh` |

## Configuration

### Required Credentials

Add these to your `~/.zshenv`:

```bash
# Proxy Services
export IPROYAL_USER='username'        # for a1
export IPROYAL_PASS='password'        # for a1
export OXYLABS_USER='customer_id'     # for a2
export OXYLABS_PASS='password'        # for a2

# API Keys
export SCAMALYTICS_API_KEY='key'      # for d4
export ONELOOKUP_API_KEY='key'        # for 1lookup commands
```

### File Paths

| Path | Purpose |
|------|---------|
| `~/.config/mrtamaki/` | Configuration directory |
| `~/.config/mrtamaki/bookmarks.json` | Bookmark storage |
| `~/.bindproxy.json` | Proxy converter configuration |
| `~/Documents/zshrc_backups/` | `.zshrc` backup directory |

## Project Structure

```
mrtamaki/
├── mrtamaki.sh              # Main entry point
├── core.sh                  # Core functions (a1-g7)
├── utils.sh                 # Shared utilities
├── banner.py                # Startup banner animation
├── ensure_venv_manager      # Virtual environment manager
├── files/
│   ├── files.sh             # File commands (fa-fg, bookmarks)
│   └── file_menu.py         # Interactive file menu
├── found/
│   ├── one_lookup.zsh       # 1lookup API wrapper
│   └── one_lookup/          # Python package for API calls
├── proxy_converter-NEW/
│   ├── proxy_converter.py   # New proxy converter
│   ├── menu_ui.py           # Menu interface
│   └── requirements.txt     # Dependencies
└── proxy_converter-OG/
    ├── proxy_converter.py   # Legacy proxy converter
    └── requirements.txt     # Dependencies
```

## Dependencies

### System Requirements

- macOS
- Zsh shell
- Python 3.8+
- Homebrew (recommended)

### Optional Homebrew Packages

These are automatically integrated if installed:

```bash
brew install powerlevel10k
brew install zsh-syntax-highlighting
brew install zsh-autosuggestions
```

### Python Dependencies

Managed automatically via virtual environments:

- **Banner**: `rich`
- **File Menu**: `rich`, `readchar`
- **1lookup**: `rich`, `requests`, `InquirerPy`
- **Proxy Converter**: `PySocks`, `rich`, `dnspython`

## Virtual Environment Management

mrtamaki automatically creates and manages virtual environments for Python-based features:

| Module | Venv Location |
|--------|---------------|
| Banner | `venv-banner/` |
| Files | `venv-files/` |
| 1lookup | `venv-found/` |
| Proxy Converter (Legacy) | `proxy_converter-OG/.venv/` |
| Proxy Converter (New) | `proxy_converter-NEW/.venv/` |

Virtual environments are created lazily on first use and dependencies are installed automatically.

## Updating

```bash
brew update && brew reinstall --cask mrtamaki && exec zsh
```

## Uninstalling

```bash
brew uninstall --cask mrtamaki && brew untap tamakibrian/mrtamaki
```

To clean up configuration files:

```bash
rm -rf ~/.config/mrtamaki
rm -f ~/.bindproxy.json
```

## License

MIT License

## Author

Brian Tamaki

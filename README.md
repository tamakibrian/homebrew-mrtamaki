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

### Required dependency

```bash
brew install romkatv/powerlevel10k/powerlevel10k
```

## Commands

Type `mrtamaki` in your terminal to see all available commands.

### Proxy & IP Tools

| Command | Description |
|---------|-------------|
| `a1` | Generate IPRoyal proxy URL |
| `a2` | Generate Oxylabs proxy URL |
| `a3` | Speed run: IPRoyal → bind → test → check |
| `a4` | Speed run: Oxylabs → bind → test → check |
| `b2` | Run proxy converter (Legacy or New) |
| `c3 <port>` | Test proxy on port, get IP |
| `d4 <ip>` | Scamalytics IP reputation check |

### System

| Command | Description |
|---------|-------------|
| `e5 [path]` | Find and clean up virtual environments |
| `f6` | Flush DNS cache (macOS) |
| `g7 [venv]` | Pip purge — cache + packages (default: system) |
| `h8` | Interactive status menu (cleanup, caches, venvs) |
| `h9` | Live system health dashboard (CPU, RAM, disk, net) |

### File Commands

| Command | Description |
|---------|-------------|
| `fmenu` | Interactive file operations menu |
| `fa` | Edit `~/.zshrc` (backup + reload) |
| `fb <term>` | Recursive file search |
| `mkcd <dir>` | Make directory and cd into it |
| `flast` | Open last created file |
| `fe` | Find large files (>100M) |
| `ff <file>` | Backup file with timestamp |
| `fg [name]` | Create timestamped folder on Desktop |
| `tempdir` | Create and cd into temp directory |
| `ftree [depth]` | Show directory tree |
| `fbook [name]` | Bookmark current directory |
| `fgo [name]` | Jump to bookmarked directory |
| `flist` | List all bookmarks |
| `fdel [name]` | Delete a bookmark |

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
| `kk` | Edit `~/.p10k.zsh` |

## Credentials

Add these to `~/.zshenv` as needed:

```bash
export IPROYAL_USER='username'         # for a1
export IPROYAL_PASS='password'         # for a1
export OXYLABS_USER='customer_id'      # for a2
export OXYLABS_PASS='password'         # for a2
export SCAMALYTICS_API_KEY='key'       # for d4
export ONELOOKUP_API_KEY='key'         # for 1lookup commands
```

## Update

```bash
brew update && brew reinstall --cask mrtamaki && exec zsh
```

## Uninstall

```bash
brew uninstall --cask mrtamaki && brew untap tamakibrian/mrtamaki
```

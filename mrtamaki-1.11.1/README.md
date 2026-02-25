# mrtamaki

Zsh toolkit for macOS — proxy generation, IP lookup, system cleanup, 1Lookup API, and file operations. All commands are available as short codes (`a1`, `h8`, `d5`, etc.) or through the `mt` / `mrtamaki` CLI.

---

## Contents

- [Prerequisites](#prerequisites)
- [Install — Homebrew (recommended)](#install--homebrew-recommended)
- [Install — Without Homebrew](#install--without-homebrew)
- [Post-install setup](#post-install-setup)
- [Update](#update)
- [Uninstall](#uninstall)
- [Command reference](#command-reference)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before installing, make sure you have:

| Requirement | Check | Install |
|-------------|-------|---------|
| macOS (Apple Silicon or Intel) | `uname -s` → `Darwin` | — |
| Zsh shell | `echo $SHELL` → `/bin/zsh` | Default on macOS 10.15+ |
| [Homebrew](https://brew.sh) | `brew --version` | See [brew.sh](https://brew.sh) |
| [Oh My Zsh](https://ohmyz.sh) | `ls ~/.oh-my-zsh` | See [ohmyz.sh](https://ohmyz.sh) |
| Python 3.10+ | `python3 --version` | `brew install python` |
| Git | `git --version` | Xcode Command Line Tools |

Oh My Zsh is required — mrtamaki sets `ZSH_THEME` and sources `oh-my-zsh.sh` during shell startup.

---

## Install — Homebrew (recommended)

### 1. Add the tap

```zsh
brew tap tamakibrian/mrtamaki
```

This tells Homebrew where to find the `mrtamaki` cask.

### 2. Install the cask

```zsh
brew install --cask mrtamaki
```

The cask automatically:
- Copies all source files to `$(brew --prefix)/share/mrtamaki/`
- Creates a Python virtualenv at `.../share/mrtamaki/venv-cli/` and installs the `mt` CLI into it
- Symlinks `mt` and `mrtamaki` into `$(brew --prefix)/bin/` (already in your `$PATH`)
- Creates a separate `venv-banner/` virtualenv for the startup banner (requires only `rich`)
- Installs **JetBrains Mono Nerd Font** via `brew install --cask font-jetbrains-mono-nerd-font`
- Clones the **light-zsh** Oh My Zsh theme to `~/.oh-my-zsh/custom/themes/light-zsh/`
- Installs **zsh-syntax-highlighting** and **zsh-autosuggestions** Homebrew formulae

### 3. Add the source line to `~/.zshrc`

Open `~/.zshrc` in your editor and add this line — ideally near the top, before any Oh My Zsh configuration:

```zsh
source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
```

This single line loads everything: the `mt` CLI wrapper, all short-code aliases (`a1`, `h8`, etc.), theme toggle, syntax highlighting, and autosuggestions.

> **Only add this line once.** The path `$(brew --prefix)/share/mrtamaki/mrtamaki.sh` stays the same across all future updates — you never need to edit `~/.zshrc` again after an upgrade.

### 4. Set your terminal font

The default theme (light-zsh) and status indicators use Nerd Font icons. In your terminal app:

- **iTerm2**: Preferences → Profiles → Text → Font → select **JetBrains Mono Nerd Font**
- **Terminal.app**: Settings → Profiles → Font → select **JetBrains Mono Nerd Font**
- **Warp**: Settings → Appearance → Terminal Font → select **JetBrains Mono Nerd Font**

### 5. Apply changes

```zsh
exec zsh
```

You should see the mrtamaki startup banner. Run `mt` or `mrtamaki` for the full command tree.

---

## Install — Without Homebrew

If you don't use Homebrew, you can install directly from source. This requires Python 3.10+, Git, and Zsh.

### 1. Clone the repository

```zsh
git clone https://github.com/tamakibrian/homebrew-mrtamaki.git ~/mrtamaki
cd ~/mrtamaki/mrtamaki-1.11.1
```

### 2. Run the install script

```zsh
zsh install-without-brew.sh
```

This script:
- Creates a Python virtualenv at `.venv/` and installs the `mt` CLI into it
- Downloads a `jq` binary into `.mrtamaki-deps/bin/` (needed for some proxy commands)
- Clones `zsh-syntax-highlighting` and `zsh-autosuggestions` into `.mrtamaki-deps/`
- Clones the light-zsh theme into `~/.oh-my-zsh/custom/themes/light-zsh/` if Oh My Zsh is present

At the end of the script, it prints the exact lines you need to add to `~/.zshrc`.

### 3. Add to `~/.zshrc`

The script will print something like:

```zsh
# mrtamaki (non-Homebrew)
export PATH="/path/to/mrtamaki/mrtamaki-1.11.1/.venv/bin:$PATH"
export PATH="/path/to/mrtamaki/mrtamaki-1.11.1/.mrtamaki-deps/bin:$PATH"
source "/path/to/mrtamaki/mrtamaki-1.11.1/mrtamaki.sh"
```

Copy those exact lines (with your real paths) into `~/.zshrc`.

### 4. Apply changes

```zsh
exec zsh
```

---

## Post-install setup

### Environment variables (credentials)

Several commands require API keys. Add these to `~/.zshenv` (not `~/.zshrc`) so they are available to all processes:

```zsh
# Proxy credentials
export IPROYAL_USER="your_username"
export IPROYAL_PASS="your_password"

export OXYLABS_USER="your_username"
export OXYLABS_PASS="your_password"

export RAPIDPROXY_USER="your_username"
export RAPIDPROXY_PASS="your_password"

# IP reputation check (d4)
export SCAMALYTICS_API_KEY="your_key"

# 1Lookup API (d5, iplookup, everify, etc.)
export ONELOOKUP_API_KEY="your_key"
```

After editing `~/.zshenv`, apply with:

```zsh
exec zsh
```

### Optional: disable the startup banner

The animated startup banner runs each time a new shell opens. To skip it:

```zsh
echo 'export MRTAMAKI_NO_BANNER=1' >> ~/.zshenv
exec zsh
```

### Optional: install proxychains-ng (for DNS leak test through proxy)

The `c3` and `d6` commands can route DNS queries through your proxy to verify no leak. This requires `proxychains-ng`:

```zsh
brew install proxychains-ng
```

---

## Update

```zsh
brew update && brew reinstall --cask mrtamaki && exec zsh
```

Your `~/.zshrc` source line stays the same — nothing else to change.

---

## Uninstall

```zsh
brew uninstall --cask mrtamaki
```

This removes:
- `$(brew --prefix)/share/mrtamaki/` (all source files and virtualenvs)
- `$(brew --prefix)/bin/mt`
- `$(brew --prefix)/bin/mrtamaki`

The following are **not** removed automatically (remove manually if desired):
- `~/.zshrc` source line
- `~/.zshenv` credential exports
- `~/.oh-my-zsh/custom/themes/light-zsh/`
- `~/.mrtamaki_theme` (theme state file)
- `~/.config/mrtamaki/bookmarks.json` (file bookmarks)

---

## Command reference

### Command naming

- **Short form**: Fast-typing codes (`a1`, `b2`, `h8`). Letter = category, number = subcommand.
- **Long form**: `mt <group> <command>` or just `mt` for the full help tree.

```zsh
mt             # Show all commands
mt proxy       # Proxy subcommands
mt ip          # IP subcommands
mt sys         # System subcommands
mt lookup      # Lookup subcommands
mt file        # File subcommands
```

### Proxy (`a`, `b`)

| Short | Long form | Description |
|-------|-----------|-------------|
| `a1` | `mt proxy gen` | Generate IPRoyal proxy URL. `a1 <city>` pins city; `a1 -u` opens interactive city picker; `a1 -b <url>` binds a proxy; `a1 -l` lists bound proxies; `a1 --clean` removes all |
| `a2` | — | Generate Oxylabs proxy URL |
| `a3` | `mt proxy rapid` | Generate Rapid proxy URL |
| `a4` | `mt proxy rapid-speed` | Rapid speed run: generate → bind → test → check |
| `a5` | `mt proxy iproyal-speed` | IPRoyal speed run: generate → bind → test → check |
| `a6` | `mt proxy oxylabs-speed` | Oxylabs speed run: generate → bind → test → check |
| `b2` | `mt proxy convert` | Proxy converter TUI |

### IP (`c`, `d`)

| Short | Long form | Description |
|-------|-----------|-------------|
| `c3 [port]` | `mt ip test [port]` | Test proxy on port via ipinfo.io + iping.cc, then DNS leak test. Omit port to check system IP |
| `d4 [ip]` | `mt ip check [ip]` | Scamalytics IP reputation check. Omit IP to use clipboard |
| `d5` / `found` / `1l` | `mt lookup` | Interactive 1Lookup API menu |
| `d6 [port]` | `mt ip dnsleak [port]` | DNS leak test via dnscheck.tools |
| `d7 [ip]` | `mt ip iping [ip]` | iping.cc structured IP lookup |
| `iplookup <ip>` | `mt lookup ip <ip>` | 1Lookup IP lookup |
| `everify <email>` | `mt lookup email <email>` | Email verification |
| `eappend` | `mt lookup eappend` | Find email from person info |
| `reappend` | `mt lookup reappend` | Reverse email lookup |
| `ripappend` | `mt lookup ripappend` | Reverse IP lookup |

### System (`e`, `g`, `h`)

| Short | Long form | Description |
|-------|-----------|-------------|
| `h1` / `pycache` | `mt sys pycache` | Find and delete `__pycache__` directories |
| `h2` / `browsercache` | `mt sys browser` | Clear Safari, Chrome, Firefox caches |
| `h3` / `appcache` | `mt sys app` | Clear `~/Library/Caches` |
| `h4` / `venvclean` | `mt sys venv` | Delete virtual environments in common search paths |
| `h5` / `space` | `mt sys space` | Show reclaimable disk space overview |
| `h6` / `deriveddata` | `mt sys xcode` | Clear Xcode DerivedData |
| `h7` / `nodemodules` | `mt sys node` | Delete `node_modules` directories |
| `h8` / `smenu` / `clean` | `mt sys menu` | Interactive system cleaner TUI (pycache, browser, venvs, duplicates, trash) |
| `h9` / `health` | `mt sys health` | Live system health dashboard (CPU, RAM, disk, network) |
| `h10` / `flushdns` | `mt sys dns` | Flush macOS DNS cache |
| `e5` | `mt sys venv-purge [path]` | Find and purge venvs under a path (pip cache, packages, directory) |
| `g7` / `pipclean` | `mt sys pip [venv]` | Purge pip cache and uninstall packages. Omit venv for system pip |

### File (`f`)

All file operations go through the `f` command using `--` flags. Run `f` with no arguments for help.

| Flag | Long form | Description |
|------|-----------|-------------|
| `f --ez` | `mt file zshrc` | Edit `~/.zshrc` with automatic backup |
| `f --s <term>` | `mt file search <term>` | Recursive file content search (`-D <dir>` to set path, `-N <n>` to limit results) |
| `f --m [dir]` | `mt file mkdir [dir]` | Make directory and `cd` into it |
| `f --o` | `mt file open-last` | Open last modified file in `$EDITOR` |
| `f --l` | `mt file large` | Find files larger than 100 MB (`-D <dir>`, `-N <n>`) |
| `f --b <file>` | `mt file backup <file>` | Backup file with timestamp suffix |
| `f --d [name]` | `mt file desktop [name]` | Create timestamped folder on Desktop |
| `f --tr [depth]` | `mt file tree [depth]` | Colour-coded directory tree (`-D <dir>`, `-N <depth>`) |
| `f --t` | `mt file tempdir` | Create temp directory and `cd` into it |
| `f --ba [name]` | `mt file bookmark-add [name]` | Bookmark current directory |
| `f --bg [name]` | `mt file bookmark-go [name]` | `cd` to a saved bookmark |
| `f --bl` | `mt file bookmark-list` | List all bookmarks |
| `f --bd [name]` | `mt file bookmark-del [name]` | Delete a bookmark |

### Theme & misc

| Command | Description |
|---------|-------------|
| `tt` | Cycle to next theme and restart shell |
| `tt --1` … `tt --6` | Jump directly to a numbered theme |
| `tt --help` | List all available themes |
| `cc` | Clear screen |
| `mt --version` | Show version |

---

## Troubleshooting

### `mt: command not found`

The `mt` binary is symlinked into `$(brew --prefix)/bin/`. If that directory isn't in your `$PATH`:

```zsh
echo 'export PATH="$(brew --prefix)/bin:$PATH"' >> ~/.zshenv
exec zsh
```

For non-Homebrew installs, make sure you added the `.venv/bin` path export to `~/.zshrc`.

### Icons appear as boxes or question marks

The Nerd Font isn't active in your terminal. Set your terminal font to **JetBrains Mono Nerd Font** (see step 4 of the Homebrew install). The font was installed by the cask automatically.

### Banner doesn't show / shell is slow to start

Check whether the `venv-banner` virtualenv exists:

```zsh
ls "$(brew --prefix)/share/mrtamaki/venv-banner/bin/python3"
```

If missing, recreate it:

```zsh
python3 -m venv "$(brew --prefix)/share/mrtamaki/venv-banner"
"$(brew --prefix)/share/mrtamaki/venv-banner/bin/pip" install rich
```

To permanently skip the banner instead:

```zsh
echo 'export MRTAMAKI_NO_BANNER=1' >> ~/.zshenv
```

### `h4` / `smenu` deleted my `mt` command

`h4` (`mt sys venv`) and `h8` (`smenu`) scan for virtualenvs and can delete `venv-cli/` — the virtualenv that contains the `mt` binary. If `mt` stops working, run this to regenerate it:

```zsh
python3 -m venv "$(brew --prefix)/share/mrtamaki/venv-cli"
"$(brew --prefix)/share/mrtamaki/venv-cli/bin/pip" install -e "$(brew --prefix)/share/mrtamaki"
ln -sf "$(brew --prefix)/share/mrtamaki/venv-cli/bin/mt" "$(brew --prefix)/bin/mt"
ln -sf "$(brew --prefix)/share/mrtamaki/venv-cli/bin/mrtamaki" "$(brew --prefix)/bin/mrtamaki"
exec zsh
```

The shell wrapper `mt()` in `mrtamaki.sh` detects this automatically and self-heals, but if you're running `mt` directly from PATH before sourcing `mrtamaki.sh`, the above manual fix is needed.

### `c3` / `d6` DNS leak test does nothing through proxy

Install `proxychains-ng`:

```zsh
brew install proxychains-ng
```

### Proxy commands (`a1`, `a5`, etc.) fail with credential errors

Make sure your credentials are exported in `~/.zshenv` (not `~/.zshrc`). Environment variables in `~/.zshrc` are not always visible to subprocesses:

```zsh
# ~/.zshenv
export IPROYAL_USER="..."
export IPROYAL_PASS="..."
```

After editing, apply with `exec zsh` and verify with `echo $IPROYAL_USER`.

### `d4` Scamalytics check fails

Ensure `SCAMALYTICS_API_KEY` is set in `~/.zshenv`. The key is your Scamalytics API key, not a username.

### Theme looks wrong after `tt`

If the theme doesn't apply after running `tt`, check that Oh My Zsh is installed and `~/.oh-my-zsh/oh-my-zsh.sh` exists. The `tt` command writes a theme index to `~/.mrtamaki_theme` and runs `exec zsh` to reload.

To reset to the default theme:

```zsh
rm ~/.mrtamaki_theme
exec zsh
```

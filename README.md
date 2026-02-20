# mrtamaki

`mrtamaki` is a Python CLI toolkit for macOS, distributed with Homebrew.
The main command is `mt`, with `mrtamaki` as an alias.

Shell shortcuts such as `a1`, `h1`, `d5`, `smenu`, and `f --...` are still supported through `mrtamaki.sh`.

## Install

```bash
brew tap tamakibrian/mrtamaki
brew install --cask mrtamaki
```

Add this once to `~/.zshrc`:

```bash
source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
```

Restart your shell:

```bash
exec zsh
```

### Install without Homebrew

If you prefer not to use Homebrew, run the install script from the source directory. It downloads jq, zsh-syntax-highlighting, zsh-autosuggestions, and creates a Python venv with mrtamaki:

```bash
git clone https://github.com/tamakibrian/homebrew-mrtamaki.git
cd homebrew-mrtamaki/mrtamaki-1.11.1
chmod +x install-without-brew.sh
./install-without-brew.sh
```

Then add the lines it prints to `~/.zshrc` (typically the venv bin, deps bin, and `source` of mrtamaki.sh), and run `exec zsh`.

## CLI usage

Show top-level help:

```bash
mt --help
```

Main command groups:

- `mt proxy` - proxy generation and proxy converter wrapper
- `mt ip` - proxy/system IP checks and DNS leak tests
- `mt sys` - cleanup, menu/health tools, DNS flush, venv and pip cleanup
- `mt lookup` - wrapper for `one_lookup`
- `mt file` - file and bookmark utilities

## Shortcut mapping

| Shortcut | Python CLI |
|----------|------------|
| `a1` | `mt proxy iproyal` |
| `a2` | `mt proxy oxylabs` |
| `a3` | `mt proxy rapid` |
| `a4` | `mt proxy rapid-speed` |
| `a5` | `mt proxy iproyal-speed` |
| `a6` | `mt proxy oxylabs-speed` |
| `b2` | `mt proxy convert` |
| `c3` | `mt ip test` |
| `d4` | `mt ip check` |
| `d5`, `found` | `mt lookup` |
| `d6` | `mt ip dnsleak` |
| `h1` | `mt sys pycache` |
| `h2` | `mt sys browser` |
| `h3` | `mt sys app` |
| `h4` | `mt sys venv` |
| `h5` | `mt sys space` |
| `h6` | `mt sys xcode` |
| `h7` | `mt sys node` |
| `h8`, `smenu` | `mt sys menu` (via shell wrapper for `cd`/delete actions) |
| `h9`, `health` | `mt sys health` |
| `h10`, `flushdns` | `mt sys dns` |
| `e5` | `mt sys venv-purge` |
| `g7` | `mt sys pip` |
| `iplookup` | `mt lookup ip` |
| `everify` | `mt lookup email` |

## Required environment variables

Add to `~/.zshenv` as needed:

```bash
export IPROYAL_USER="..."
export IPROYAL_PASS="..."
export OXYLABS_USER="..."
export OXYLABS_PASS="..."
export SCAMALYTICS_API_KEY="..."
export ONELOOKUP_API_KEY="..."
```

Optional (for a3/a4 Rapid proxy):

```bash
export RAPIDPROXY_USER="..."
export RAPIDPROXY_PASS="..."
```

Optional:

```bash
export MRTAMAKI_NO_BANNER=1
```

## Local development

```bash
cd mrtamaki-1.11.1
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
mt --help
pytest -q
```

## Repository layout

```text
homebrew-mrtamaki/
├── Casks/mrtamaki.rb
├── build-release.sh
├── README.md
└── mrtamaki-1.11.1/
    ├── pyproject.toml
    ├── mrtamaki.sh
    ├── install-without-brew.sh
    ├── banner.py
    ├── dns_leak.py
    ├── utils.sh
    ├── mrtamaki/
    │   ├── __init__.py
    │   ├── cli.py
    │   ├── _utils.py
    │   ├── proxy/cli.py
    │   ├── ip/cli.py
    │   ├── sys/cli.py
    │   ├── lookup/cli.py
    │   └── file/cli.py
    ├── found/one_lookup/
    ├── proxy_converter/
    ├── clean/
    ├── status/
    └── tests/
```

## Release flow

1. Update versions in `mrtamaki-1.11.1/pyproject.toml`, `mrtamaki-1.11.1/mrtamaki/__init__.py`, and `mrtamaki-1.11.1/mrtamaki.sh`.
2. Run tests: `cd mrtamaki-1.11.1 && pytest -q`.
3. Build release zip: `./build-release.sh <version>`.
4. Update `Casks/mrtamaki.rb` (`version` and `sha256`).
5. Create GitHub release with the generated zip.

## Update and uninstall

Update:

```bash
brew update && brew reinstall --cask mrtamaki && exec zsh
```

Uninstall:

```bash
brew uninstall --cask mrtamaki
brew untap tamakibrian/mrtamaki
```

# mrtamaki

Zsh toolkit for macOS — proxy, IP, system cleanup, lookup, and file operations.

## Command naming

- **Short form**: Fast-typing codes (`a1`, `b2`, `h8`, etc.) — letter = category, number = subcommand.
- **Long form**: `mt` / `mrtamaki` — central dispatcher. Run `mt` or `mrtamaki` with no args for the command tree.

### Categories

| Letter | Category | Examples |
|--------|----------|----------|
| a | Proxy generate | a1 (IPRoyal), a2 (Oxylabs), a3 (Rapid), a4 (Rapid speed), a5 (IPRoyal speed), a6 (Oxylabs speed) |
| b | Proxy tools | b2 (converter) |
| c | IP test | c3 (proxy test) |
| d | IP lookup | d4 (Scamalytics), d5 (1Lookup), d6 (DNS leak), d7 (iping) |
| e | Venv purge | e5 |
| f | File ops | `f --<flag>` (f with no args = help) |
| g | Pip | g7 (pip purge) |
| h | System | h1–h7 (cleaners), h8 (menu), h9 (health), h10 (DNS flush) |

### Semantic aliases

For discoverability, these long-form aliases map to the short codes:

| Alias | Maps to |
|-------|---------|
| pycache | mt sys pycache (h1) |
| browsercache | mt sys browser (h2) |
| appcache | mt sys app (h3) |
| venvclean | mt sys venv (h4) |
| space | mt sys space (h5) |
| deriveddata | mt sys xcode (h6) |
| nodemodules | mt sys node (h7) |
| clean | smenu (h8) |
| pipclean | mt sys pip (g7) |
| health | mt sys health (h9) |
| flushdns | mt sys dns (h10) |
| found | mt lookup (d5) |

## Quick start

```bash
# Install (Homebrew)
brew install --cask mrtamaki

# Add to ~/.zshrc
source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"

# Command tree
mt
mrtamaki

# Module help
mt proxy
mt sys
mt ip
mt file
```

## Update

```bash
brew update && brew reinstall --cask mrtamaki && exec zsh
```

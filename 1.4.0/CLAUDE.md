# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Homebrew cask (homebrew-mrtamaki) that provides a zsh toolkit for macOS. It installs shell functions and utilities for proxy management, IP lookups, file operations, and API integrations. Users source the main entry point from `~/.zshrc`.

## Repository Structure

```
1.4.0/
├── v1.4.1.sh              # Main entry point - sources all modules, defines aliases
├── core.sh                # Core functions: a1-a2 (proxy), b2-g7 (utilities)
├── utils.sh               # Shared utilities: colors, prompts, venv handlers
├── banner.py              # Python Rich-based startup banner
├── pc_helper.py           # Proxy converter helper
├── files/
│   ├── files.sh           # File operations: fa-fg, tempdir, mkcd, fbook
│   └── file_menu.py       # Rich Live two-column interactive menu
├── found/
│   ├── one_lookup.zsh     # 1lookup API zsh wrappers
│   └── one_lookup/        # Python package
│       ├── client.py      # API client (ip_lookup, email_verify, email_append, etc.)
│       ├── cli.py         # CLI entry point (python -m one_lookup.cli)
│       ├── menu.py        # Legacy InquirerPy menu
│       └── menu_v2.py     # New Rich Live two-column menu
└── Casks/mrtamaki.rb      # Homebrew cask definition
```

## Key Architecture

- **Module Loading**: `v1.4.1.sh` is the entry point that sources `core.sh`, `files/files.sh`, and `found/one_lookup.zsh`. Each module sources `utils.sh` for shared utilities.
- **Guard Pattern**: Modules use `[[ -n "$_MODULE_LOADED" ]] && return 0` to prevent double-sourcing.
- **Path Resolution**: Uses `${0:A:h}` (zsh-specific) to get the directory containing the sourced script.
- **Virtual Environments**: Each Python module has its own venv created by the cask installer:
  - `venv-banner/` - rich (for startup banner)
  - `venv-files/` - rich, readchar (for file menu)
  - `venv-found/` - rich, requests, InquirerPy, readchar (for 1lookup)
- **Venv Resolution**: `_ensure_module_venv` in utils.sh lazily creates/locates venvs and sets `$VENV_PYTHON`.

## Release Workflow

1. Update version in `v1.4.1.sh` (rename file), `Casks/mrtamaki.rb`, and the `mrtamaki()` help function
2. Create release zip, upload to GitHub releases
3. Calculate sha256: `shasum -a 256 mrtamaki-1.4.1.zip`
4. Update sha256 in `Casks/mrtamaki.rb`
5. Users update via: `brew update && brew reinstall --cask mrtamaki && exec zsh`

## Environment Variables (in ~/.zshenv)

```bash
export IPROYAL_USER='username'      # for a1
export IPROYAL_PASS='password'      # for a1
export OXYLABS_USER='customer_id'   # for a2
export OXYLABS_PASS='password'      # for a2
export SCAMALYTICS_API_KEY='key'    # for d4
export ONELOOKUP_API_KEY='key'      # for 1lookup commands
```

## Function Naming Convention

- **a1-a2**: Proxy URL generators (IPRoyal, Oxylabs)
- **b2-g7**: System utilities (proxy converter, IP query, scamalytics, venv cleanup, DNS flush, pip purge)
- **fa-fg**: File operations (zshrc edit, search, mkcd, last file, large files, backup, desktop folder)
- **fmenu/fbook/fgo**: Interactive file menu and bookmarks
- **1lookup**: iplookup, everify, eappend, reappend, ripappend

## Testing Changes Locally

```bash
# Source the entry point directly (without reinstalling cask)
source ~/Desktop/mrtamaki/1.4.0/v1.4.1.sh

# Test Python modules directly
cd ~/Desktop/mrtamaki/1.4.0
python3 -m venv venv-found
source venv-found/bin/activate
pip install rich requests readchar
python -m one_lookup.cli menu
```

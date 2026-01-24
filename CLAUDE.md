# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Homebrew cask (homebrew-mrtamaki) that provides a zsh toolkit for macOS. It installs shell functions and utilities for proxy management, IP lookups, file operations, and API integrations. Users source the main entry point from `~/.zshrc`.

## Repository Structure

```
homebrew-mrtamaki/
├── v1.3.5.sh          # Main entry point - sources all modules, defines aliases
├── core.sh            # Core functions: a1-a2 (proxy), b2-g7 (utilities)
├── utils.sh           # Shared utilities: colors, prompts, venv handlers
├── files/files.sh     # File operations: fa-fg, tempdir, mkcd
├── found/one_lookup.zsh   # 1lookup API integration (zsh wrappers)
├── banner.py          # Python Rich-based startup banner
└── Casks/mrtamaki.rb  # Homebrew cask definition
```

## Key Architecture

- **Module Loading Pattern**: `v1.3.0.sh` is the entry point that sources `core.sh` and `files/files.sh`. Each module sources `utils.sh` for shared utilities.
- **Guard Pattern**: Modules use `[[ -n "$_MODULE_LOADED" ]] && return 0` to prevent double-sourcing.
- **Path Resolution**: Uses `${0:A:h}` (zsh-specific) to get the directory containing the sourced script.
- **Environment Variables**: Credentials and API keys are expected in `~/.zshenv` (IPROYAL_USER, OXYLABS_USER, SCAMALYTICS_API_KEY, ONELOOKUP_API_KEY).

## Release Workflow

1. Update version in `v1.3.0.sh` (rename file for new versions), `Casks/mrtamaki.rb`, and the `mrtamaki()` help function
2. Create release zip, upload to GitHub releases
3. Update sha256 in `Casks/mrtamaki.rb`
4. Users update via: `brew update && brew reinstall --cask mrtamaki && exec zsh`

## Dependencies (defined in Casks/mrtamaki.rb)

- jq, python, zsh, zsh-syntax-highlighting, zsh-autosuggestions
- External: powerlevel10k (user must install separately)
- Python packages: rich (for banner), requests (for 1lookup)

## Function Naming Convention

- **a1-a2**: Proxy URL generators (IPRoyal, Oxylabs)
- **b2-g7**: System utilities (proxy converter, IP query, scamalytics, venv cleanup, DNS flush, pip purge)
- **fa-fg**: File operations (zshrc edit, search, mkcd, last file, large files, backup, desktop folder)
- **1lookup commands**: iplookup, everify, eappend, reappend, ripappend

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Homebrew cask (homebrew-mrtamaki) that provides a zsh toolkit for macOS. It installs shell functions and utilities for proxy management, IP lookups, file operations, and API integrations. Users source the main entry point from `~/.zshrc`.

## Repository Structure

```
homebrew-mrtamaki/
├── v1.4.2.sh              # Main entry point - sources all modules, defines aliases
├── core.sh                # Core functions: a1-a2 (proxy), b2-g7 (utilities)
├── utils.sh               # Shared utilities: colors, prompts, venv handlers
├── files/
│   ├── files.sh           # File operations: fa-fg, tempdir, mkcd, bookmarks
│   ├── file_menu.py       # Interactive TUI menu (Rich + readchar)
│   └── requirements.txt   # Python deps for file menu
├── found/one_lookup.zsh   # 1lookup API integration (zsh wrappers)
├── banner.py              # Python Rich-based startup banner
├── docs/                  # User documentation
└── Casks/mrtamaki.rb      # Homebrew cask definition
```

## Key Architecture

- **Module Loading Pattern**: `v1.4.2.sh` is the entry point that sources `core.sh`, `files/files.sh`, and `found/one_lookup.zsh`. Each module sources `utils.sh` for shared utilities.
- **Guard Pattern**: Modules use `[[ -n "$_MODULE_LOADED" ]] && return 0` to prevent double-sourcing.
- **Path Resolution**: Uses `${0:A:h}` (zsh-specific) to get the directory containing the sourced script.
- **Interactive Menu**: `fmenu` launches a Rich TUI (`file_menu.py`) that returns commands via stdout protocol (`__FILEMENU_CMD__:`).
- **Bookmarks**: Stored in `~/.config/mrtamaki/bookmarks.json`, managed by `fbook`, `fgo`, `flist`, `fdel`.
- **Environment Variables**: Credentials and API keys are expected in `~/.zshenv` (IPROYAL_USER, OXYLABS_USER, SCAMALYTICS_API_KEY, ONELOOKUP_API_KEY).

## Release Workflow

1. Update version in `v1.4.2.sh` (rename file for new versions), `Casks/mrtamaki.rb`, and the `mrtamaki()` help function
2. Create release zip, upload to GitHub releases
3. Update sha256 in `Casks/mrtamaki.rb`
4. Users update via: `brew update && brew reinstall --cask mrtamaki && exec zsh`

## Dependencies (defined in Casks/mrtamaki.rb)

- jq, python, zsh, zsh-syntax-highlighting, zsh-autosuggestions
- External: powerlevel10k (user must install separately)
- Python packages: rich, readchar (for file menu), requests (for 1lookup)

## Function Naming Convention

- **a1-a2**: Proxy URL generators (IPRoyal, Oxylabs)
- **b2-g7**: System utilities (proxy converter, IP query, scamalytics, venv cleanup, DNS flush, pip purge)
- **File commands**:
  - `fmenu`: Interactive file menu (TUI)
  - `fa`: Edit .zshrc with backup/reload
  - `fb`: Recursive file search
  - `mkcd`: Make directory and cd into it
  - `flast`: Open last modified file
  - `fe`: Find large files
  - `ff`: Backup file with timestamp
  - `fg`: Create timestamped folder on Desktop
  - `tempdir`: Create and cd into temp directory
  - `ftree`: Show directory tree
- **Bookmark commands**: `fbook` (save), `fgo` (jump), `flist` (list), `fdel` (delete)
- **1lookup commands**: iplookup, everify, eappend, reappend, ripappend

# Clean My Mac CLI — Design Document

**Date:** 2026-02-15
**Status:** Approved

## Summary

Evolve `smenu`/`h8` from a status/cleanup menu into a full "Clean My Mac CLI" experience. New `clean/` module replaces `status/` as the primary cleanup interface, adding duplicate file detection, trash management, Xcode DerivedData cleanup, and node_modules cleanup to the existing cache/venv features.

## Module Structure

```
mrtamaki-1.7.0/
└── clean/                        # New module directory
    ├── clean.sh                  # Shell wrapper: smenu/h8 dispatch, quick commands
    ├── clean_menu.py             # TUI: Rich + readchar menu (main interface)
    ├── duplicate_finder.py       # SHA256 duplicate detection engine
    ├── shared_utils.py           # Themes, format_bytes (copied from status/)
    └── requirements.txt          # rich>=13, readchar>=4, psutil>=5
```

### Relationship to `status/`

- `status/` stays intact — `health_dashboard.py` (h9) and `shared_utils.py` continue working.
- `smenu`/`h8` alias moves to `clean.sh` and launches `clean_menu.py`.
- `mrtamaki.sh` sources `clean/clean.sh` (in addition to `status/status.sh` for h9).

### Venv

New `venv-clean` with deps: `rich>=13 readchar>=4 psutil>=5`. Same as status but separate to keep modules independent.

## Menu Items

| # | Key | Label | Description | Handler |
|---|-----|-------|-------------|---------|
| 1 | pycache | Pycache | Find & delete `__pycache__` dirs | Shell dispatch |
| 2 | browser | Browser | Clear Safari/Chrome/Firefox caches | Shell dispatch |
| 3 | appcache | App Cache | Clear `~/Library/Caches` | Shell dispatch |
| 4 | xcode | Xcode | Clear DerivedData | Shell dispatch (new) |
| 5 | nodemod | node_modules | Find & delete node_modules dirs | Shell dispatch (new) |
| 6 | venvs | Venvs | Browse & delete virtual environments | TUI sub-screen |
| 7 | dupes | Duplicates | SHA256 duplicate scan | Python-handled (new) |
| 8 | trash | Trash | Show size & empty trash | Shell dispatch (new) |
| 9 | sizes | Sizes | Overview of all reclaimable space | TUI info panel |
| 0 | return | Exit | Return to shell | — |

### Quick Commands

Existing h1-h5 move to `clean.sh` and continue working:
- `h1` = pycache, `h2` = browser, `h3` = appcache, `h4` = venvs, `h5` = sizes
- New: `h6` = xcode, `h7` = node_modules
- `smenu`/`h8` = full TUI, `h9` = health dashboard (stays in status/)

## IPC Protocol

Same temp-file pattern as current smenu. Protocol prefix: `__CLEAN_CMD__:<command>`.

Commands dispatched to shell:
- `pycache`, `browser`, `appcache`, `xcode`, `nodemod`, `trash`
- `__CD__:<path>` — cd to venv directory
- `__DELETE_VENV__:<path>` — delete specific venv

Duplicate deletion is handled entirely within the Python TUI (no shell dispatch).

## New Shell Functions

### `_clean_xcode()`
- Check for `~/Library/Developer/Xcode/DerivedData`
- Show total size
- Confirm, then `rm -rf` contents (keep the DerivedData directory itself)

### `_clean_nodemodules()`
- Scan `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Projects` for `node_modules` dirs
- Skip nested node_modules (only top-level per project)
- Show each with size, confirm all-or-nothing, delete

### `_clean_trash()`
- Show `~/.Trash` total size
- Confirm, then `rm -rf ~/.Trash/*`

## Duplicate Finder Design

### Two-Pass Algorithm

**Pass 1 — Size grouping:** Group all files by file size. Files with unique sizes are eliminated immediately (can't be duplicates). This avoids hashing the vast majority of files.

**Pass 2 — SHA256 hashing:** For size-matched files, compute SHA256. Group by hash. Groups with 2+ files = confirmed duplicates.

### Filters
- Minimum file size: 1 KB (skip tiny files like `.DS_Store`)
- Skip hidden directories (`.git`, `.venv`, `.node_modules`, etc.)
- Skip symlinks
- Scan paths: `~/Desktop`, `~/Documents`, `~/Downloads`

### TUI for Duplicate Groups
- Show each group: file count, wasted space (size x (count - 1))
- For each group, list all file paths with modification dates
- User navigates groups, marks files for deletion (must keep at least 1 per group)
- Confirm & delete

### Performance
Size-first approach means only a small fraction of files get hashed. Typical user dirs (10-50 GB) should complete in seconds to under a minute.

## TUI Design

Follows the established Rich + readchar pattern:
- `Live(screen=True, auto_refresh=False)` for alternate-screen TUI
- Manual `live.update(..., refresh=True)` calls
- Two-column layout: menu on left, info panel on right (same as current status_menu.py)
- Rebranded header: "System Cleaner" or similar instead of "Status Menu"

## mrtamaki.sh Changes

- Add `source "${SHELL_V11_DIR}/clean/clean.sh"` to the loading chain
- `status/status.sh` continues to be sourced (for h9/health dashboard)
- `smenu`/`h8` alias defined in `clean.sh` (overrides the one in `status.sh`)

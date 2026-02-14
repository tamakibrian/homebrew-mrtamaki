# Design: Unified `f` command with flag-based dispatch

## Summary

Replace the `fmenu` TUI and individual `fa`-`fn` commands with a unified `f` command that uses single-letter flags. The interactive Rich menu (`file_menu.py`) is removed entirely. Existing `fa`-`fn` functions remain as-is and are called by the `f()` router.

## Approach

**Approach 1: Thin wrapper.** A single `f()` function parses flags and dispatches to existing `fa`-`fn` functions. No logic moves — `f` is purely a router.

## Flag mapping

| Flag | Arg      | Type     | Maps to | Description                        |
|------|----------|----------|---------|------------------------------------|
| `-a` | none     | no-arg   | `fa`    | Edit .zshrc (backup + edit)        |
| `-b` | `<term>` | required | `fb`    | Recursive file search              |
| `-c` | `<dir>`  | required | `fc`    | Make directory + cd into it        |
| `-d` | none     | no-arg   | `fd`    | Open last modified file            |
| `-e` | none     | no-arg   | `fe`    | Find large files                   |
| `-f` | none     | no-arg   | `ff`    | Create + enter temp dir            |
| `-g` | `<file>` | required | `fg`    | Backup a file                      |
| `-h` | `[name]` | optional | `fh`    | Create Desktop folder              |
| `-j` | `[depth]`| optional | `fj`    | Directory tree                     |
| `-k` | `[name]` | optional | `fk`    | Save bookmark                      |
| `-l` | `[name]` | optional | `fl`    | Jump to bookmark                   |
| `-m` | none     | no-arg   | `fm`    | List bookmarks                     |
| `-n` | `[name]` | optional | `fn`    | Delete bookmark                    |

## Combined flags

Flags can be combined: `f -ade` runs `fa`, `fd`, `fe` sequentially.

Argument consumption:
- **Required-arg flags** (`-b`, `-c`, `-g`): always consume the next positional argument.
- **Optional-arg flags** (`-h`, `-j`, `-k`, `-l`, `-n`): consume the next positional only when they are the **last flag in the combo**. In the middle of a combo, they are called with no argument.
- **No-arg flags** (`-a`, `-d`, `-e`, `-f`, `-m`): never consume positional arguments.

Examples:
- `f -ade` → `fa; fd; fe`
- `f -bg term file` → `fb "term"; fg "file"`
- `f -akh myname` → `fa; fk` (no arg); `fh "myname"` (last, gets arg)
- `f -b` (missing required arg) → `fb` handles its own error message

## Bare `f` (no flags)

Prints a compact help table via `print_info`:

```
  -a         Edit .zshrc (backup + edit)
  -b <term>  Recursive file search
  -c <dir>   Make & enter directory
  ...
```

## Changes

### Modified
- `files.sh`: Add `f()` router function. Remove `fmenu()` and `_files_setup_venv()`. Update `fj()` to call `_ensure_module_venv` directly.

### Deleted
- `Files/file_menu.py`: TUI no longer needed.

### Updated docs
- `CLAUDE.md`: Replace fmenu references with `f` command.
- `README.md`: Update file operations documentation (if applicable).

### Unchanged
- All `fa` through `fn` functions — untouched, still work standalone.
- `Files/requirements.txt` — still needed for `fj` tree view.
- Bookmark system, tree view, all existing behavior.

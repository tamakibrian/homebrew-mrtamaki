# mrtamaki File Commands

Interactive file operations for your shell.

## Quick Start

```bash
# Launch the interactive file menu
fmenu

# Or use commands directly
mkcd my-project      # Create directory and cd into it
fb "TODO"            # Search for "TODO" in files
fbook work           # Bookmark current directory as "work"
fgo work             # Jump to "work" bookmark
```

## Interactive Menu (`fmenu`)

Launch with `fmenu` to get a two-column TUI:

- **Left panel**: Command list with descriptions
- **Right panel**: Context info, recent files, bookmarks

### Key Bindings

| Mode | Keys | Action |
|------|------|--------|
| Main | `↑↓` or `j/k` | Navigate commands |
| Main | `Enter` | Select command |
| Main | `t` | Toggle tree view |
| Main | `b` | Open bookmarks |
| Main | `q` or `Esc` | Quit |
| Tree | `Enter`, `q`, or `Esc` | Back to menu |
| Bookmarks | `↑↓` or `j/k` | Navigate bookmarks |
| Bookmarks | `Enter` | Jump to bookmark |
| Bookmarks | `x` | Delete bookmark |
| Bookmarks | `q` or `Esc` | Back to menu |

## File Commands

| Command | Description |
|---------|-------------|
| `fa` | Edit ~/.zshrc with automatic backup and reload |
| `fb <term>` | Search file contents recursively |
| `mkcd <dir>` | Create directory and cd into it |
| `flast` | Open the most recently modified file |
| `fe` | Find files larger than 100MB |
| `tempdir` | Create and cd into a temp directory |
| `ff <file>` | Create timestamped backup of a file |
| `fg [name]` | Create timestamped folder on Desktop |
| `ftree [depth]` | Show directory tree (default depth: 2) |

## Bookmarks

Save and jump to frequently used directories:

| Command | Description |
|---------|-------------|
| `fbook [name]` | Bookmark current directory |
| `fgo [name]` | Jump to a bookmark |
| `flist` | List all bookmarks |
| `fdel [name]` | Delete a bookmark |

Bookmarks are stored in `~/.config/mrtamaki/bookmarks.json`.

## Tips

- Use `j/k` for vim-style navigation in the menu
- Press `t` anytime in the menu to preview the directory tree
- Press `b` to quickly access your bookmarks
- `fbook` without a name will prompt you for one
- `fgo` without a name shows all bookmarks and lets you pick

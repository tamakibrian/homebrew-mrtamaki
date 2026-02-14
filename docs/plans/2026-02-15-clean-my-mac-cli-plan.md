# Clean My Mac CLI — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace smenu/h8 with a full "System Cleaner" TUI that adds duplicate detection, trash management, Xcode DerivedData cleanup, and node_modules cleanup to the existing cache/venv features.

**Architecture:** New `clean/` module with its own `clean_menu.py` TUI (Rich + readchar), `duplicate_finder.py` engine, and `clean.sh` shell wrapper. Follows the exact same IPC pattern as `status/`. The `status/` module stays for h9/health dashboard only. `smenu`/`h8` alias moves to `clean.sh`.

**Tech Stack:** Zsh (shell wrapper), Python 3 (TUI + duplicate finder), Rich, readchar, psutil, hashlib (stdlib)

---

### Task 1: Create clean/ directory and shared_utils.py

**Files:**
- Create: `mrtamaki-1.7.0/clean/shared_utils.py`
- Create: `mrtamaki-1.7.0/clean/requirements.txt`

**Step 1: Create requirements.txt**

```
rich>=13.0.0
readchar>=4.0.0
psutil>=5.9.0
```

**Step 2: Copy shared_utils.py from status/**

Copy `mrtamaki-1.7.0/status/shared_utils.py` to `mrtamaki-1.7.0/clean/shared_utils.py` verbatim. This is the same file — themes, `format_bytes()`, `format_speed()`, `get_theme()`.

**Step 3: Verify**

```bash
ls -la mrtamaki-1.7.0/clean/
# Expected: shared_utils.py, requirements.txt
```

**Step 4: Commit**

```bash
git add mrtamaki-1.7.0/clean/
git commit -m "feat(clean): scaffold clean/ module with shared_utils and requirements"
```

---

### Task 2: Create duplicate_finder.py

**Files:**
- Create: `mrtamaki-1.7.0/clean/duplicate_finder.py`

This is a standalone engine module with no TUI dependency. It provides functions for the menu to call.

**Step 1: Write duplicate_finder.py**

```python
#!/usr/bin/env python3
"""SHA256-based duplicate file finder with two-pass algorithm."""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple


# Directories to skip during scanning
SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".Trash", "Library", ".cache", ".npm", ".nvm",
}

# Minimum file size to consider (1 KB)
MIN_FILE_SIZE = 1024

# Default scan paths
DEFAULT_SCAN_PATHS = [
    Path.home() / "Desktop",
    Path.home() / "Documents",
    Path.home() / "Downloads",
]


def _hash_file(filepath: Path, chunk_size: int = 8192) -> str:
    """Compute SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_files(
    scan_paths: List[Path] = None,
    min_size: int = MIN_FILE_SIZE,
    max_depth: int = 8,
) -> Dict[int, List[Path]]:
    """Pass 1: Group files by size. Returns {size: [path1, path2, ...]}."""
    if scan_paths is None:
        scan_paths = DEFAULT_SCAN_PATHS

    size_groups: Dict[int, List[Path]] = {}

    def _walk(directory: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in directory.iterdir():
                if entry.is_symlink():
                    continue
                if entry.is_dir():
                    if entry.name in SKIP_DIRS:
                        continue
                    _walk(entry, depth + 1)
                elif entry.is_file():
                    try:
                        size = entry.stat().st_size
                        if size >= min_size:
                            size_groups.setdefault(size, []).append(entry)
                    except (OSError, PermissionError):
                        pass
        except (OSError, PermissionError):
            pass

    for sp in scan_paths:
        if sp.exists():
            _walk(sp, 0)

    # Keep only sizes with 2+ files (potential duplicates)
    return {s: paths for s, paths in size_groups.items() if len(paths) >= 2}


def find_duplicates(
    scan_paths: List[Path] = None,
    min_size: int = MIN_FILE_SIZE,
    max_depth: int = 8,
    progress_callback=None,
) -> List[Tuple[str, int, List[Path]]]:
    """
    Two-pass duplicate finder.

    Returns list of (hash, file_size, [path1, path2, ...]) for each duplicate group.
    progress_callback(current, total) is called during hashing if provided.
    """
    # Pass 1: group by size
    size_groups = scan_files(scan_paths, min_size, max_depth)

    # Count total files to hash
    total_to_hash = sum(len(paths) for paths in size_groups.values())
    hashed = 0

    # Pass 2: hash files with same size
    hash_groups: Dict[str, Tuple[int, List[Path]]] = {}

    for size, paths in size_groups.items():
        for filepath in paths:
            try:
                file_hash = _hash_file(filepath)
                if file_hash in hash_groups:
                    hash_groups[file_hash][1].append(filepath)
                else:
                    hash_groups[file_hash] = (size, [filepath])
            except (OSError, PermissionError):
                pass
            hashed += 1
            if progress_callback:
                progress_callback(hashed, total_to_hash)

    # Return only groups with 2+ files (true duplicates)
    result = []
    for file_hash, (size, paths) in hash_groups.items():
        if len(paths) >= 2:
            result.append((file_hash, size, paths))

    # Sort by wasted space descending (size * (count - 1))
    result.sort(key=lambda x: x[1] * (len(x[2]) - 1), reverse=True)
    return result
```

**Step 2: Verify syntax**

```bash
cd mrtamaki-1.7.0 && python3 -c "import ast; ast.parse(open('clean/duplicate_finder.py').read()); print('OK')"
# Expected: OK
```

**Step 3: Commit**

```bash
git add mrtamaki-1.7.0/clean/duplicate_finder.py
git commit -m "feat(clean): add SHA256 duplicate file finder with two-pass algorithm"
```

---

### Task 3: Create clean_menu.py — Core TUI structure

**Files:**
- Create: `mrtamaki-1.7.0/clean/clean_menu.py`

This is the biggest file. Build it in stages. This task creates the skeleton with menu rendering and navigation — no sub-screens yet.

**Step 1: Write clean_menu.py skeleton**

Model this closely on `status/status_menu.py` (lines 1-488). The key differences:
- `COMMANDS` list has 10 items (pycache, browser, appcache, xcode, nodemod, venvs, dupes, trash, sizes, return)
- Protocol prefix is `__CLEAN_CMD__:` instead of `__STATUSMENU_CMD__:`
- Header says "System Cleaner" instead of "System Status"
- Class name is `CleanMenu` instead of `StatusMenu`

```python
#!/usr/bin/env python3
"""Interactive system cleaner menu — Clean My Mac CLI."""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

import readchar
import psutil
from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box

from shared_utils import THEMES, CURRENT_THEME, get_theme, format_bytes

# Commands list
COMMANDS = [
    ("pycache",  "Pycache",      "Find and delete all __pycache__ directories"),
    ("browser",  "Browser",      "Clear browser caches (Safari, Chrome, Firefox)"),
    ("appcache", "App Cache",    "Clear application cache directories"),
    ("xcode",    "Xcode",        "Clear Xcode DerivedData"),
    ("nodemod",  "node_modules", "Find and delete node_modules directories"),
    ("venvs",    "Venvs",        "Browse and delete virtual environments"),
    ("dupes",    "Duplicates",   "Find duplicate files (SHA256)"),
    ("trash",    "Trash",        "Show trash size and empty"),
    ("sizes",    "Sizes",        "View all reclaimable space overview"),
    ("return",   "Exit",         "Return to shell"),
]

ICONS = ["", "", "", "", "", "", "", "", "", ""]
```

The rest of the file follows the exact same pattern as `status_menu.py`:
- Data helper functions: `get_dir_size()`, `find_pycache_dirs()`, `find_venvs()`, `get_browser_cache_paths()`, `get_system_context()`, `build_sizes_overview()` — copy from status_menu.py
- Add new helpers: `get_xcode_derived_data_size()`, `get_node_modules_info()`, `get_trash_size()`
- `CleanMenu` class with all the same render methods but adapted for the expanded command list
- `main()` function using `__CLEAN_CMD__:` protocol prefix

**New data helpers to add (after the ones copied from status_menu.py):**

```python
def get_xcode_derived_data_path() -> Path:
    """Get Xcode DerivedData path."""
    return Path.home() / "Library" / "Developer" / "Xcode" / "DerivedData"


def get_trash_path() -> Path:
    """Get user trash path."""
    return Path.home() / ".Trash"


def get_trash_size() -> int:
    """Get total trash size in bytes."""
    trash = get_trash_path()
    if not trash.exists():
        return 0
    return get_dir_size(trash)


def find_node_modules(max_depth: int = 5) -> List[Tuple[Path, int]]:
    """Find node_modules directories with sizes."""
    results = []
    home = Path.home()
    search_paths = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Projects",
    ]

    def _search(directory: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for entry in directory.iterdir():
                if not entry.is_dir():
                    continue
                if entry.name == "node_modules":
                    size = get_dir_size(entry)
                    results.append((entry, size))
                    # Don't recurse into node_modules
                    continue
                if entry.name in (".git", ".venv", "venv", "Library", ".Trash", "__pycache__"):
                    continue
                _search(entry, depth + 1)
        except (OSError, PermissionError):
            pass

    for sp in search_paths:
        if sp.exists():
            _search(sp, 0)
    return results
```

**Updated `get_system_context()`** — add xcode, node_modules, trash info:

```python
def get_system_context() -> dict:
    """Get system status context info."""
    disk = psutil.disk_usage(str(Path.home()))
    pycache_count = len(find_pycache_dirs())
    browser_caches = get_browser_cache_paths()
    browser_found = [name for name, p in browser_caches.items() if p.exists()]

    # Xcode
    xcode_path = get_xcode_derived_data_path()
    xcode_exists = xcode_path.exists()

    # Trash
    trash_size = get_trash_size()

    return {
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": disk.percent,
        "pycache_count": pycache_count,
        "browser_found": browser_found,
        "xcode_exists": xcode_exists,
        "trash_size": trash_size,
    }
```

**Updated `build_sizes_overview()`** — add xcode, node_modules, trash to the sizes panel:

Add these sections after the existing pycache/browser/venvs sections:

```python
    # Xcode DerivedData
    xcode_path = get_xcode_derived_data_path()
    content.append("  Xcode DerivedData\n", style=f"bold {theme['highlight']}")
    if xcode_path.exists():
        xcode_size = get_dir_size(xcode_path)
        content.append(f"    {format_bytes(xcode_size)}\n\n", style=theme["muted"])
        total += xcode_size
    else:
        content.append("    (not found)\n\n", style=theme["muted"])

    # node_modules
    node_mods = find_node_modules(max_depth=3)
    node_size = sum(s for _, s in node_mods)
    content.append("  node_modules\n", style=f"bold {theme['highlight']}")
    content.append(f"    {len(node_mods)} dirs, {format_bytes(node_size)}\n\n", style=theme["muted"])
    total += node_size

    # Trash
    trash_size = get_trash_size()
    content.append("  Trash\n", style=f"bold {theme['highlight']}")
    content.append(f"    {format_bytes(trash_size)}\n\n", style=theme["muted"])
    total += trash_size
```

**CleanMenu class**: Copy the full `StatusMenu` class from `status_menu.py` and make these changes:
1. Rename `StatusMenu` → `CleanMenu`
2. Update `render_header()`: change icon/title to "System Cleaner"
3. `render_header()`: add trash size to the context line
4. `handle_main_input()`: add cases for `xcode`, `nodemod`, `trash`, `dupes` commands — all return the command string except `dupes` which enters a `"dupes"` mode, and `venvs`/`sizes` which enter their modes as before
5. Add `handle_dupes_input()` method and `render_dupes_list()` method (see Task 4)
6. `render_footer()`: add `"d"` shortcut for dupes, `"t"` for trash

**`main()` function:**

```python
def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--result-file", help="File to write result to")
    args = parser.parse_args()

    console = Console()
    menu = CleanMenu(console)
    result = menu.run()

    def write_result(text: str):
        if args.result_file:
            with open(args.result_file, "w") as f:
                f.write(text)
        else:
            print(text)

    if result:
        if result.startswith("__DELETE_VENV__:"):
            path = result.split(":", 1)[1]
            write_result(f"__CLEAN_CMD__:__DELETE_VENV__:{path}")
        elif result.startswith("__VENV_CD__:"):
            path = result.split(":", 1)[1]
            write_result(f"__CLEAN_CMD__:__CD__:{path}")
        else:
            write_result(f"__CLEAN_CMD__:{result}")
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Verify syntax**

```bash
cd mrtamaki-1.7.0 && python3 -c "import ast; ast.parse(open('clean/clean_menu.py').read()); print('OK')"
# Expected: OK
```

**Step 3: Commit**

```bash
git add mrtamaki-1.7.0/clean/clean_menu.py
git commit -m "feat(clean): add CleanMenu TUI with all menu items and data helpers"
```

---

### Task 4: Add duplicate detection TUI sub-screen to clean_menu.py

**Files:**
- Modify: `mrtamaki-1.7.0/clean/clean_menu.py`

Add the `"dupes"` mode to `CleanMenu`. When user selects "Duplicates", the menu enters dupe-scanning mode:
1. Runs `find_duplicates()` from `duplicate_finder.py`
2. Shows a progress indicator during scan
3. Displays groups in the right panel
4. User navigates groups, marks files for deletion (must keep at least 1)
5. Pressing `x` deletes marked files, `Enter` toggles mark, `Esc` goes back

**Step 1: Add import at top of clean_menu.py**

```python
from duplicate_finder import find_duplicates
```

**Step 2: Add state variables to `CleanMenu.__init__`**

```python
        # Duplicate detection state
        self.dupes: List[Tuple[str, int, List[Path]]] = []
        self.dupe_group_idx = 0
        self.dupe_marks: Dict[int, set] = {}  # group_idx -> set of file indices to delete
        self.dupe_file_idx = 0
        self.dupe_scanning = False
```

Also add `from typing import Dict` to the imports.

**Step 3: Add `render_dupes_list()` method**

```python
    def render_dupes_list(self) -> Text:
        """Render duplicate files for selection."""
        theme = get_theme()
        content = Text()

        if self.dupe_scanning:
            content.append("Scanning for duplicates...\n\n", style=f"bold {theme['accent']}")
            content.append("This may take a moment.\n", style=theme["muted"])
            return content

        if not self.dupes:
            content.append("No duplicate files found.\n\n", style=theme["muted"])
            content.append("Scanned ~/Desktop, ~/Documents, ~/Downloads\n", style=theme["muted"])
            content.append("(files >= 1 KB, SHA256 comparison)\n", style=theme["muted"])
            return content

        group_hash, group_size, group_paths = self.dupes[self.dupe_group_idx]
        wasted = group_size * (len(group_paths) - 1)
        marks = self.dupe_marks.get(self.dupe_group_idx, set())

        content.append(f"Group {self.dupe_group_idx + 1}/{len(self.dupes)}\n", style=f"bold {theme['accent']}")
        content.append(f"Size: {format_bytes(group_size)} each, ", style=theme["muted"])
        content.append(f"Wasted: {format_bytes(wasted)}\n\n", style=theme["warning"])

        for idx, filepath in enumerate(group_paths):
            display = str(filepath)
            home_str = str(Path.home())
            if display.startswith(home_str):
                display = "~" + display[len(home_str):]
            if len(display) > 40:
                display = "..." + display[-37:]

            is_marked = idx in marks
            is_selected = idx == self.dupe_file_idx

            if is_selected:
                marker = "[X]" if is_marked else "[ ]"
                content.append(f" > {marker} ", style=f"bold {theme['accent']}")
                content.append(f"{display}\n", style="bold white")
            else:
                marker = "[X]" if is_marked else "[ ]"
                style = theme["error"] if is_marked else "dim white"
                content.append(f"   {marker} {display}\n", style=style)

        total_wasted = sum(s * (len(p) - 1) for _, s, p in self.dupes)
        total_marked = sum(
            len(m) * self.dupes[gi][1]
            for gi, m in self.dupe_marks.items()
        )
        content.append(f"\n[{theme['muted']}]Total wasted: {format_bytes(total_wasted)}[/]")
        content.append(f"\n[{theme['muted']}]Marked for deletion: {format_bytes(total_marked)}[/]")
        content.append(f"\n[{theme['muted']}]Enter=toggle, ←→=groups, x=delete marked, Esc=back[/]")
        return content
```

**Step 4: Add `handle_dupes_input()` method**

```python
    def handle_dupes_input(self, key: str) -> Optional[str]:
        """Handle input in dupes mode."""
        if not self.dupes:
            if key in (readchar.key.ESC, "q"):
                self.mode = "main"
            return None

        group_paths = self.dupes[self.dupe_group_idx][2]

        if key in (readchar.key.UP, "k"):
            self.dupe_file_idx = (self.dupe_file_idx - 1) % len(group_paths)
        elif key in (readchar.key.DOWN, "j"):
            self.dupe_file_idx = (self.dupe_file_idx + 1) % len(group_paths)
        elif key in (readchar.key.RIGHT, "l"):
            # Next group
            self.dupe_group_idx = (self.dupe_group_idx + 1) % len(self.dupes)
            self.dupe_file_idx = 0
        elif key in (readchar.key.LEFT, "h"):
            # Previous group
            self.dupe_group_idx = (self.dupe_group_idx - 1) % len(self.dupes)
            self.dupe_file_idx = 0
        elif key in (readchar.key.ENTER, "\r"):
            # Toggle mark (but don't allow marking all files in group)
            marks = self.dupe_marks.setdefault(self.dupe_group_idx, set())
            if self.dupe_file_idx in marks:
                marks.discard(self.dupe_file_idx)
            else:
                # Don't allow marking all files (must keep at least 1)
                if len(marks) < len(group_paths) - 1:
                    marks.add(self.dupe_file_idx)
        elif key == "x":
            # Delete all marked files
            deleted_any = False
            for gi, marks in list(self.dupe_marks.items()):
                if not marks:
                    continue
                _, _, paths = self.dupes[gi]
                for fi in sorted(marks, reverse=True):
                    try:
                        paths[fi].unlink()
                        deleted_any = True
                    except (OSError, PermissionError):
                        pass
            if deleted_any:
                # Re-scan
                self.dupes = find_duplicates()
                self.dupe_marks = {}
                self.dupe_group_idx = 0
                self.dupe_file_idx = 0
        elif key in (readchar.key.ESC, "q"):
            self.mode = "main"
        return None
```

**Step 5: Update `handle_main_input()` to handle dupes entry**

In the `elif key in (readchar.key.ENTER, "\r"):` block, add before the `else: return cmd`:

```python
            elif cmd == "dupes":
                self.dupe_scanning = True
                # Will scan on first render
                self.mode = "dupes"
```

And in the `run()` method's main loop, after setting the mode to dupes and before `live.update()`, add the scanning logic:

```python
                # Handle deferred dupe scanning
                if self.mode == "dupes" and self.dupe_scanning:
                    live.update(self.render(), refresh=True)
                    self.dupes = find_duplicates()
                    self.dupe_marks = {}
                    self.dupe_group_idx = 0
                    self.dupe_file_idx = 0
                    self.dupe_scanning = False
```

**Step 6: Update `render_info_panel()` to handle dupes mode**

Add to the mode checks:

```python
        elif self.mode == "dupes":
            content = self.render_dupes_list()
            title = "Duplicate Files"
```

**Step 7: Update `render_footer()` for dupes mode**

Add a new elif for dupes:

```python
        elif self.mode == "dupes":
            controls.append("  ↑↓", style=f"bold {theme['accent']}")
            controls.append(" select  ", style=theme["muted"])
            controls.append("←→", style=f"bold {theme['accent']}")
            controls.append(" groups  ", style=theme["muted"])
            controls.append("Enter", style=f"bold {theme['accent']}")
            controls.append(" toggle  ", style=theme["muted"])
            controls.append("x", style=f"bold {theme['accent']}")
            controls.append(" delete  ", style=theme["muted"])
            controls.append("Esc", style=f"bold {theme['accent']}")
            controls.append(" back", style=theme["muted"])
```

**Step 8: Update the mode dispatcher in `run()`**

In the `while True` loop, add:

```python
                elif self.mode == "dupes":
                    result = self.handle_dupes_input(key)
```

**Step 9: Verify syntax**

```bash
cd mrtamaki-1.7.0 && python3 -c "import ast; ast.parse(open('clean/clean_menu.py').read()); print('OK')"
```

**Step 10: Commit**

```bash
git add mrtamaki-1.7.0/clean/clean_menu.py
git commit -m "feat(clean): add duplicate detection TUI sub-screen with mark-and-delete"
```

---

### Task 5: Create clean.sh — Shell wrapper

**Files:**
- Create: `mrtamaki-1.7.0/clean/clean.sh`

This is the shell wrapper. It contains:
1. The `smenu()` function (redirected to clean_menu.py)
2. All cleanup shell functions (migrated from status.sh)
3. New cleanup functions for xcode, node_modules, trash
4. Quick command aliases h1-h7

**Step 1: Write clean.sh**

Follow the exact pattern of `status/status.sh`. Key differences:
- `CLEAN_DIR="${0:A:h}"` instead of `STATUS_DIR`
- Sources `utils.sh` from parent: `source "${0:A:h:h}/utils.sh"`
- Uses `_ensure_module_venv clean` (requires adding `clean` to the module_packages map in utils.sh — see Task 6)
- Protocol prefix is `__CLEAN_CMD__:`
- Menu script path is `"${CLEAN_DIR}/clean_menu.py"`

The `smenu()` function follows the exact same pattern as in status.sh:
1. `_clean_setup_venv` → `_ensure_module_venv clean "$SHELL_V11_DIR"`
2. Create temp file
3. Run `$VENV_PYTHON clean_menu.py --result-file $tmp_result`
4. Parse `__CLEAN_CMD__:` prefix
5. Dispatch commands

Shell cleanup functions to include (copy from status.sh and rename prefix from `_status_` to `_clean_`):
- `_clean_pycache()` — same as `_status_clean_pycache()`
- `_clean_browser()` — same as `_status_clean_browser()`
- `_clean_appcache()` — same as `_status_clean_appcache()`
- `_clean_venvs()` — same as `_status_clean_venvs()`
- `_clean_show_sizes()` — same as `_status_show_sizes()` but add xcode/nodemod/trash sections

New shell functions:

```bash
# Clear Xcode DerivedData
_clean_xcode() {
    print_header "Clear Xcode DerivedData"

    local derived_data="$HOME/Library/Developer/Xcode/DerivedData"
    if [[ ! -d "$derived_data" ]]; then
        print_info "Xcode DerivedData not found (Xcode may not be installed)"
        return 0
    fi

    local total_size
    total_size=$(du -sh "$derived_data" 2>/dev/null | cut -f1)
    print_info "DerivedData size: ${COLOR_WARNING}${total_size}${COLOR_RESET}"

    # Count projects
    local project_count=0
    for entry in "$derived_data"/*(N); do
        [[ -d "$entry" ]] && ((project_count++))
    done
    print_info "$project_count project build caches\n"

    if ! confirm "Clear all DerivedData?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    # Remove contents but keep the directory
    rm -rf "$derived_data"/* 2>/dev/null
    print_success "Cleared DerivedData (freed ${total_size})"
}

# Find and delete node_modules directories
_clean_nodemodules() {
    print_header "Clean node_modules"

    local -a dirs=()
    local search_paths=("$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Projects")

    for search_path in "${search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            dirs+=("$dir")
        done < <(find "$search_path" -maxdepth 5 \
            \( -name ".git" -o -name "Library" -o -name ".Trash" -o -name "__pycache__" \) -prune \
            -o -type d -name "node_modules" -print0 2>/dev/null)
    done

    if (( ${#dirs[@]} == 0 )); then
        print_info "No node_modules directories found"
        return 0
    fi

    print_info "Found ${#dirs[@]} node_modules directories:\n"

    local total_bytes=0
    for dir in "${dirs[@]}"; do
        local size
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        local display="${dir/#$HOME/~}"
        echo "  ${COLOR_WARNING}${size}${COLOR_RESET}  $display"
        local bytes
        bytes=$(du -s "$dir" 2>/dev/null | cut -f1)
        (( total_bytes += bytes ))
    done

    local total_human
    total_human=$(_human_size "$total_bytes")
    echo "\n  ${COLOR_INFO}Total: ${total_human}${COLOR_RESET}\n"

    if ! confirm "Delete all ${#dirs[@]} node_modules directories?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    echo ""
    local count=0
    for dir in "${dirs[@]}"; do
        local display="${dir/#$HOME/~}"
        if rm -rf "$dir" 2>/dev/null; then
            echo "  ${COLOR_SUCCESS}${ICON_SUCCESS}${COLOR_RESET} Removed $display"
            ((count++))
        else
            echo "  ${COLOR_ERROR}${ICON_ERROR}${COLOR_RESET} Failed  $display"
        fi
    done

    echo ""
    print_success "Deleted $count / ${#dirs[@]} node_modules directories (freed ${total_human})"
}

# Empty trash
_clean_trash() {
    print_header "Empty Trash"

    local trash_dir="$HOME/.Trash"
    if [[ ! -d "$trash_dir" ]]; then
        print_info "Trash directory not found"
        return 0
    fi

    # Check if trash is empty
    local item_count=0
    for entry in "$trash_dir"/*(N); do
        ((item_count++))
    done

    if (( item_count == 0 )); then
        print_info "Trash is already empty"
        return 0
    fi

    local total_size
    total_size=$(du -sh "$trash_dir" 2>/dev/null | cut -f1)
    print_info "Trash size: ${COLOR_WARNING}${total_size}${COLOR_RESET} ($item_count items)\n"

    if ! confirm "Empty trash? This cannot be undone." "N"; then
        print_info "Cancelled"
        return 0
    fi

    rm -rf "$trash_dir"/* 2>/dev/null
    rm -rf "$trash_dir"/.* 2>/dev/null  # Hidden files too
    print_success "Trash emptied (freed ${total_size})"
}
```

**Command dispatch in smenu() case statement:**

```bash
    case "$cmd" in
        pycache)  _clean_pycache ;;
        browser)  _clean_browser ;;
        appcache) _clean_appcache ;;
        xcode)    _clean_xcode ;;
        nodemod)  _clean_nodemodules ;;
        trash)    _clean_trash ;;
        *)        print_error "Unknown command: $cmd"; return 1 ;;
    esac
```

**Quick commands and aliases at bottom of file:**

```bash
# Quick commands
h1() { _clean_pycache; }
h2() { _clean_browser; }
h3() { _clean_appcache; }
h4() { _clean_venvs; }
h5() { _clean_show_sizes; }
h6() { _clean_xcode; }
h7() { _clean_nodemodules; }

# Aliases
alias h8='smenu'
alias pycache='h1'
alias browsercache='h2'
alias appcache='h3'
alias venvclean='h4'
alias cachesizes='h5'
alias xcodedata='h6'
alias nodemod='h7'
alias status='smenu'
alias statusmenu='smenu'
alias clean='smenu'
```

**Step 2: Verify syntax**

```bash
zsh -n mrtamaki-1.7.0/clean/clean.sh
# Expected: no output (syntax OK)
```

**Step 3: Commit**

```bash
git add mrtamaki-1.7.0/clean/clean.sh
git commit -m "feat(clean): add shell wrapper with all cleanup functions and IPC dispatch"
```

---

### Task 6: Update utils.sh — Add clean module to venv packages

**Files:**
- Modify: `mrtamaki-1.7.0/utils.sh` (line ~120, the `module_packages` array)

**Step 1: Add clean to module_packages**

Add this line to the associative array in `_ensure_module_venv()`:

```bash
        [clean]="rich>=13 readchar>=4 psutil>=5"
```

This goes after the `[proxy]` line.

**Step 2: Verify**

```bash
zsh -n mrtamaki-1.7.0/utils.sh
```

**Step 3: Commit**

```bash
git add mrtamaki-1.7.0/utils.sh
git commit -m "feat(clean): register clean module venv in _ensure_module_venv"
```

---

### Task 7: Update mrtamaki.sh — Source clean module

**Files:**
- Modify: `mrtamaki-1.7.0/mrtamaki.sh` (around line 96)

**Step 1: Add clean module sourcing**

After the existing `source "${SHELL_V11_DIR}/status/status.sh"` line (line 96), add:

```bash
source "${SHELL_V11_DIR}/clean/clean.sh"        # System cleaner: smenu (clean menu), h1-h7
```

This means `clean.sh` is sourced AFTER `status.sh`, so its `smenu`/`h8` alias will override the one from status.sh. The `h9`/`health` alias stays from status.sh.

**Step 2: Remove h8/smenu aliases from status.sh**

In `mrtamaki-1.7.0/status/status.sh`, remove the alias lines at the bottom that define `h8`, `smenu`, `status`, `statusmenu`, and the h1-h5 quick command aliases. These are now all in `clean.sh`. Keep only the `h9`, `health`, `dashboard` aliases.

The bottom of status.sh should become:

```bash
# Aliases for easier access (h8/smenu moved to clean.sh)
alias h9='_status_h9'
alias health='h9'
alias dashboard='h9'
```

Also rename the `h9()` function to `_status_h9()` to avoid conflict, and keep the aliases pointing to it.

**Step 3: Update help text in mrtamaki()**

In the `mrtamaki()` help function (around line 102-130), update the SYSTEM section to include the new commands:

```bash
    echo "  SYSTEM"
    echo "    e5 [path]       Find and clean up virtual environments"
    echo "    f6              Flush DNS cache (macOS)"
    echo "    g7 [venv]       Pip purge (cache + packages, default: system)"
    echo "    h1              Clean __pycache__ directories"
    echo "    h2              Clear browser caches"
    echo "    h3              Clear app caches"
    echo "    h4              Clean virtual environments"
    echo "    h5              Cache sizes overview"
    echo "    h6              Clear Xcode DerivedData"
    echo "    h7              Clean node_modules"
    echo "    h8 / smenu      System cleaner (full TUI menu)"
    echo "    h9 / health     Live system health dashboard"
```

**Step 4: Verify**

```bash
zsh -n mrtamaki-1.7.0/mrtamaki.sh
```

**Step 5: Commit**

```bash
git add mrtamaki-1.7.0/mrtamaki.sh mrtamaki-1.7.0/status/status.sh
git commit -m "feat(clean): wire clean module into loading chain, update help text"
```

---

### Task 8: Update Cask postflight — Add clean venv pre-creation

**Files:**
- Modify: `Casks/mrtamaki.rb`

**Step 1: Check current postflight**

Read the cask file to see how venvs are pre-created.

**Step 2: Add clean venv creation**

Add a line in the postflight block that creates the clean venv, following the same pattern as the existing venv creation lines. Something like:

```ruby
system "#{staged_path}/mrtamaki-*/venv-clean/bin/pip", "install", ...
```

Or if it uses `_ensure_module_venv`, just add `clean` to the list.

**Step 3: Commit**

```bash
git add Casks/mrtamaki.rb
git commit -m "feat(clean): add clean venv pre-creation to Homebrew cask postflight"
```

---

### Task 9: Manual integration test

**No files changed — verification only.**

**Step 1: Create clean venv manually**

```bash
cd mrtamaki-1.7.0
python3 -m venv venv-clean
venv-clean/bin/pip install rich>=13 readchar>=4 psutil>=5
```

**Step 2: Test the TUI directly**

```bash
cd mrtamaki-1.7.0/clean
../venv-clean/bin/python clean_menu.py
```

- Verify all 10 menu items render
- Navigate up/down through all items
- Press `s` to enter sizes view — verify xcode/node_modules/trash sections appear
- Press `Esc` to go back
- Select "Duplicates" — verify scan runs and shows results (or "No duplicates found")
- Press `Esc` to go back
- Press `q` to exit

**Step 3: Test shell integration**

```bash
source mrtamaki-1.7.0/mrtamaki.sh
smenu    # Should launch the new clean menu
h6       # Should run Xcode cleanup
h7       # Should run node_modules cleanup
h9       # Should still launch health dashboard
```

**Step 4: Commit any fixes found during testing**

---

### Task 10: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update the repository layout** to include the `clean/` directory.

**Step 2: Update the module loading chain** to show `clean/clean.sh` being sourced.

**Step 3: Update the venv package mapping table** to include the `clean` module.

**Step 4: Update the command reference table** to include h6, h7, and note that smenu now launches the system cleaner.

**Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with clean module documentation"
```

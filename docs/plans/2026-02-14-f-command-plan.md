# `f` Command Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace `fmenu` TUI with a unified `f` CLI command that dispatches to existing `fa`-`fn` functions via single-letter flags, with support for combined flags.

**Architecture:** A thin `f()` router function in `files.sh` parses `-<flags>` and dispatches to existing shell functions. No logic moves. The Rich TUI (`file_menu.py`) is deleted entirely.

**Tech Stack:** Zsh (shell functions only — no new Python code)

**Design doc:** `docs/plans/2026-02-14-f-command-design.md`

---

### Task 1: Add `f()` router function to `files.sh`

**Files:**
- Modify: `mrtamaki-1.7.0/Files/files.sh` (insert after line 16, before the `fmenu()` function)

**Step 1: Write the `f()` function**

Add this function to `files.sh` after the venv setup section (line 16) and before `fmenu()`:

```zsh
# Unified file command: f -<flags> [args...]
# Flags: a(edit zshrc) b(search) c(mkdir+cd) d(open last) e(large files)
#        f(temp dir) g(backup) h(desktop dir) j(tree) k(bookmark)
#        l(jump) m(list bookmarks) n(delete bookmark)
f() {
    # No args: print help table
    if [[ $# -eq 0 ]]; then
        print_header "File Commands"
        echo "  -a          Edit .zshrc (backup + edit)"
        echo "  -b <term>   Recursive file search"
        echo "  -c <dir>    Make & enter directory"
        echo "  -d          Open last modified file"
        echo "  -e          Find large files"
        echo "  -f          Create + enter temp dir"
        echo "  -g <file>   Backup a file"
        echo "  -h [name]   Create Desktop folder"
        echo "  -j [depth]  Directory tree"
        echo "  -k [name]   Save bookmark"
        echo "  -l [name]   Jump to bookmark"
        echo "  -m          List bookmarks"
        echo "  -n [name]   Delete bookmark"
        echo ""
        echo "  Combine: f -ade  (runs fa, fd, fe)"
        echo "  Args:    f -bg term file  (fb term, fg file)"
        return 0
    fi

    local flags_str="$1"
    shift

    # Validate flags format
    if [[ "$flags_str" != -* ]]; then
        print_error "Usage: f -<flags> [args...]"
        return 1
    fi

    # Strip leading dash
    flags_str="${flags_str#-}"

    # Flag categories
    local required_arg_flags="bcg"
    local optional_arg_flags="hjkln"
    # no_arg_flags: a d e f m (implicit — anything not in the above)

    local flags_len=${#flags_str}
    local i

    for (( i=1; i<=flags_len; i++ )); do
        local flag="${flags_str[$i]}"
        local is_last=$(( i == flags_len ))

        case "$flag" in
            # --- No-arg flags ---
            a) fa ;;
            d) fd ;;
            e) fe ;;
            f) ff ;;  # Note: f -f calls ff()
            m) fm ;;

            # --- Required-arg flags (always consume next positional) ---
            b)
                fb "$1"
                shift 2>/dev/null
                ;;
            c)
                fc "$1"
                shift 2>/dev/null
                ;;
            g)
                fg "$1"
                shift 2>/dev/null
                ;;

            # --- Optional-arg flags (consume next positional only when last in combo) ---
            h)
                if (( is_last )) && [[ $# -gt 0 ]]; then
                    fh "$1"
                    shift
                else
                    fh
                fi
                ;;
            j)
                if (( is_last )) && [[ $# -gt 0 ]]; then
                    fj "$1"
                    shift
                else
                    fj
                fi
                ;;
            k)
                if (( is_last )) && [[ $# -gt 0 ]]; then
                    fk "$1"
                    shift
                else
                    fk
                fi
                ;;
            l)
                if (( is_last )) && [[ $# -gt 0 ]]; then
                    fl "$1"
                    shift
                else
                    fl
                fi
                ;;
            n)
                if (( is_last )) && [[ $# -gt 0 ]]; then
                    fn "$1"
                    shift
                else
                    fn
                fi
                ;;

            *)
                print_error "Unknown flag: -$flag"
                return 1
                ;;
        esac
    done
}
```

**Step 2: Verify syntax**

Run: `zsh -n mrtamaki-1.7.0/Files/files.sh`
Expected: No output (clean parse)

**Step 3: Manual smoke test**

Run: `source mrtamaki-1.7.0/Files/files.sh && f`
Expected: Prints the help table

Run: `f -m`
Expected: Same output as `fm` (list bookmarks)

Run: `f -e`
Expected: Same output as `fe` (find large files)

**Step 4: Commit**

```bash
git add mrtamaki-1.7.0/Files/files.sh
git commit -m "feat: add f() router function for flag-based file commands"
```

---

### Task 2: Remove `fmenu()` and `_files_setup_venv()` from `files.sh`

**Files:**
- Modify: `mrtamaki-1.7.0/Files/files.sh` (remove lines 14-135 — `_files_setup_venv` and `fmenu` functions)

**Step 1: Remove `_files_setup_venv()`**

Delete these lines from `files.sh`:

```zsh
#---------- VENV SETUP FOR FILE MENU ----------

# Setup venv for file menu (uses centralized venv function)
_files_setup_venv() {
    _ensure_module_venv files "$SHELL_V11_DIR"
}
```

**Step 2: Remove `fmenu()`**

Delete the entire `fmenu()` function (the function that creates a temp file, runs `file_menu.py`, parses the IPC protocol, and dispatches commands).

**Step 3: Update `fj()` to call `_ensure_module_venv` directly**

In the `fj()` function, replace:
```zsh
    # Ensure venv is setup
    _files_setup_venv || return 1
```
With:
```zsh
    # Ensure venv is setup
    _ensure_module_venv files "$SHELL_V11_DIR" || return 1
```

**Step 4: Verify syntax**

Run: `zsh -n mrtamaki-1.7.0/Files/files.sh`
Expected: No output (clean parse)

**Step 5: Commit**

```bash
git add mrtamaki-1.7.0/Files/files.sh
git commit -m "refactor: remove fmenu() and _files_setup_venv(), fj calls venv directly"
```

---

### Task 3: Delete `file_menu.py`

**Files:**
- Delete: `mrtamaki-1.7.0/Files/file_menu.py`

**Step 1: Delete the file**

```bash
rm mrtamaki-1.7.0/Files/file_menu.py
```

**Step 2: Verify no remaining references**

Run: `grep -r "file_menu" mrtamaki-1.7.0/`
Expected: No matches (the only reference was in `fmenu()` which was removed in Task 2)

**Step 3: Commit**

```bash
git rm mrtamaki-1.7.0/Files/file_menu.py
git commit -m "chore: delete file_menu.py TUI (replaced by f command)"
```

---

### Task 4: Update `CLAUDE.md` documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update all fmenu references**

Make these changes in `CLAUDE.md`:

1. **Line 5** (project description): Change `fmenu` to `f` in the list of commands
2. **Line 32** (repo layout): Change `files.sh` comment from `Shell functions: fa-fn, fmenu, mkcd, tempdir, etc.` to `Shell functions: f, fa-fn, mkcd, tempdir, etc.`
3. **Line 33** (repo layout): Remove the `file_menu.py` line entirely
4. **Line 63** (module loading): Change `File commands: fmenu, fa-fn` to `File commands: f, fa-fn`
5. **Line 102** (TUI pattern): Remove `fmenu` from the list of interactive menus: `(h8/smenu, fmenu, d5, b2-new)` → `(h8/smenu, d5, b2-new)`
6. **Line 152** (command reference table): Replace the fmenu row:
   - Old: `| fmenu | fmenu() in files.sh | Interactive file operations menu |`
   - New: `| f [-flags] | f() in files.sh | Unified file command (flag-based dispatch to fa-fn) |`

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md — replace fmenu with f command"
```

---

### Task 5: Update `README.md` documentation

**Files:**
- Modify: `README.md`

**Step 1: Update fmenu references**

Make these changes in `README.md`:

1. **Line 62** (command table): Replace `fmenu | Interactive file operations menu` with `f [-flags] | Unified file command (see f for usage)`
2. **Line 137** (repo layout): Change `files.sh` comment to remove fmenu reference
3. **Line 138** (repo layout): Remove the `file_menu.py` line
4. **Line 164** (module loading): Change `File commands: fmenu, fa-fn` to `File commands: f, fa-fn`
5. **Line 190** (TUI pattern): Remove `fmenu` from the list

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README.md — replace fmenu with f command"
```

---

### Task 6: Final verification

**Step 1: Verify no stale fmenu references remain**

Run: `grep -r "fmenu\|file_menu" mrtamaki-1.7.0/ CLAUDE.md README.md`
Expected: No matches

**Step 2: Verify files.sh parses cleanly**

Run: `zsh -n mrtamaki-1.7.0/Files/files.sh`
Expected: No output

**Step 3: Full smoke test**

Source the toolkit and test key scenarios:

```bash
source mrtamaki-1.7.0/mrtamaki.sh

# Help
f                    # Should print help table

# Single no-arg flags
f -m                 # List bookmarks
f -e                 # Find large files
f -d                 # Open last file

# Single required-arg flag
f -b "TODO"          # Search for TODO

# Combined no-arg flags
f -me                # List bookmarks, then find large files

# Tree still works (venv)
f -j                 # Directory tree
```

**Step 4: Commit any fixes if needed, then final commit**

```bash
git add -A
git commit -m "feat: v1.7.11 — replace fmenu TUI with unified f command"
```

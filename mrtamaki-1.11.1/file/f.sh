#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - f command
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities
source "${SHELL_V11_DIR}/utils.sh"

# Config directory for bookmarks
MRTAMAKI_CONFIG_DIR="$HOME/.config/mrtamaki"
MRTAMAKI_BOOKMARKS_FILE="$MRTAMAKI_CONFIG_DIR/bookmarks.json"

_f_help() {
    cat <<'EOF'
Usage: f --<action> [arguments] [-D path] [-N count]

A flag-based command for file and directory operations.
Flags are executed sequentially from left to right.

Options:
  --ez                Edit .zshrc with backup.
  --s <term>          Search for a term in files.
  --m <dir>           Make a directory and enter it.
  --o                 Open the last modified file.
  --l                 Find large files.
  --t                 Create and enter a temporary directory.
  --b <file>          Create a backup of a file.
  --d [name]          Create a desktop directory.
  --tr [depth]        Show a directory tree.
  --ba [name]         Bookmark: Add the current directory.
  --bg [name]         Bookmark: Go to a bookmark.
  --bl                Bookmark: List all bookmarks.
  --bd [name]         Bookmark: Delete a bookmark.
  --h                 Show this help message.

Modifiers (for --tr, --s, --l):
  -D <path>           Set target directory (default: current dir).
  -N <number>         Set limit: tree depth / max results (default: varies).

Examples:
  f --tr -D ~/projects -N 4    Tree of ~/projects, depth 4
  f --s "TODO" -D ./src -N 20  Search "TODO" in ./src, max 20 results
  f --l -D ~/Downloads -N 10   Large files in ~/Downloads, show top 10
EOF
}

# Reload and back up .zshrc with checksum verification
_f_edit_zshrc() {
    local timestamp
    timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local backup_dir="$HOME/Documents/zshrc_backups"
    local backup_file="$backup_dir/zshrc_backup_$timestamp"

    # Ensure backup directory exists
    mkdir -p "$backup_dir" || {
        print_error "Failed to create backup directory"
        return 1
    }

    # Create backup
    if cp ~/.zshrc "$backup_file"; then
        print_success "Backup created: $backup_file"
    else
        print_error "Failed to create backup"
        return 1
    fi

    # Compute checksum before editing (more reliable than mtime)
    local before
    before=$(shasum ~/.zshrc 2>/dev/null | cut -d' ' -f1)

    # Edit the file
    ${EDITOR:-nano} ~/.zshrc

    # Compute checksum after editing
    local after
    after=$(shasum ~/.zshrc 2>/dev/null | cut -d' ' -f1)

    # Notify if changed (don't re-source -- it triggers banner and full reload)
    if [[ "$before" != "$after" ]]; then
        print_success "Changes saved"
        print_info "Backup: $backup_file"
        print_info "Run 'exec zsh' to apply changes"
    else
        print_info "No changes detected"
    fi
}

f() {
    if [[ $# -eq 0 ]]; then
        _f_help
        return 0
    fi

    # Global modifiers (parsed first, available to all actions)
    local _f_dest=""   # -D <path>
    local _f_count=""  # -N <number>

    # Pre-scan for -D and -N modifiers, build remaining args
    local -a remaining=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -D)
                if [[ -n "$2" && "$2" != -* ]]; then
                    _f_dest="$2"
                    shift
                else
                    print_error "-D requires a path argument"
                    return 1
                fi
                ;;
            -N)
                if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                    _f_count="$2"
                    shift
                else
                    print_error "-N requires a numeric argument"
                    return 1
                fi
                ;;
            *)
                remaining+=("$1")
                ;;
        esac
        shift
    done

    # Validate destination if given
    if [[ -n "$_f_dest" && ! -d "$_f_dest" ]]; then
        print_error "Directory not found: $_f_dest"
        return 1
    fi

    # Process action flags from remaining args
    set -- "${remaining[@]}"
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --h|--help)
                _f_help
                return 0
                ;;
            --ez)
                _f_edit_zshrc
                ;;
            --s)
                _f_search "$2" "$_f_dest" "$_f_count"
                shift
                ;;
            --m)
                _f_mkdir "$2"
                shift
                ;;
            --o)
                _f_open_last
                ;;
            --l)
                _f_find_large "$_f_dest" "$_f_count"
                ;;
            --t)
                _f_tempdir
                ;;
            --b)
                _f_backup "$2"
                shift
                ;;
            --d)
                _f_desktop_dir "$2"
                if [[ -n "$2" && "$2" != --* ]]; then
                    shift
                fi
                ;;
            --tr)
                _f_tree "${2:-$_f_count}" "$_f_dest"
                if [[ -n "$2" && "$2" != --* ]]; then
                    shift
                fi
                ;;
            --ba)
                _f_bookmark_add "$2"
                if [[ -n "$2" && "$2" != --* ]]; then
                    shift
                fi
                ;;
            --bg)
                _f_bookmark_go "$2"
                if [[ -n "$2" && "$2" != --* ]]; then
                    shift
                fi
                ;;
            --bl)
                _f_bookmark_list
                ;;
            --bd)
                _f_bookmark_del "$2"
                if [[ -n "$2" && "$2" != --* ]]; then
                    shift
                fi
                ;;
            *)
                print_error "Unknown flag: $1"
                _f_help
                return 1
                ;;
        esac
        shift
    done
}

# Recursive file search with input sanitization
# Args: $1=term, $2=dest (optional), $3=count (optional)
_f_search() {
    if [[ -z "$1" ]]; then
        print_error "Usage: f --s <search_term> [-D path] [-N count]"
        return 1
    fi

    local term="$1"
    local dest="${2:-.}"
    local count="$3"

    local dest_label=""
    [[ "$dest" != "." ]] && dest_label=" in $dest"
    print_info "Searching for: $term${dest_label}${count:+ (max $count)}"
    # Use -F for literal matching (safer than regex)
    if [[ -n "$count" ]]; then
        grep -rnwF --color=always "$dest" -e "$term" 2>/dev/null | head -n "$count" || print_warning "No matches found"
    else
        grep -rnwF --color=always "$dest" -e "$term" 2>/dev/null || print_warning "No matches found"
    fi
}

# Make directory and cd into it
_f_mkdir() {
    if [[ -z "$1" ]]; then
        print_error "Usage: f --m <directory_name>"
        return 1
    fi

    if mkdir -p "$1" && cd "$1"; then
        print_success "Created and entered: $1"
    else
        print_error "Failed to create directory: $1"
        return 1
    fi
}

# Opens last file created
_f_open_last() {
    local latest
    latest=$(ls -t 2>/dev/null | head -n1)

    if [[ -z "$latest" ]]; then
        print_error "No files in current directory"
        return 1
    fi

    print_info "Opening: $latest"
    ${EDITOR:-vim} "$latest"
}

# Finds files larger than configured size
# Args: $1=dest (optional), $2=count (optional)
_f_find_large() {
    local dest="${1:-.}"
    local count="$2"

    local dest_label=""
    [[ "$dest" != "." ]] && dest_label=" in $dest"
    print_info "Searching for files larger than ${MAX_FILE_SIZE:-100M}${dest_label}${count:+ (top $count)}..."
    if [[ -n "$count" ]]; then
        find "$dest" -type f -size "+${MAX_FILE_SIZE:-100M}" -exec ls -lh {} + 2>/dev/null | \
            awk '{print $5 "\t" $9}' | sort -rh | head -n "$count" || print_info "No large files found"
    else
        find "$dest" -type f -size "+${MAX_FILE_SIZE:-100M}" -exec ls -lh {} + 2>/dev/null | \
            awk '{print $5 "\t" $9}' | sort -rh || print_info "No large files found"
    fi
}

# Create a temporary directory
_f_tempdir() {
    local tmpdir
    tmpdir=$(mktemp -d) || {
        print_error "Failed to create temporary directory"
        return 1
    }

    if cd "$tmpdir"; then
        print_success "Created temp directory: $tmpdir"
    else
        print_error "Failed to enter temp directory"
        return 1
    fi
}

# Backup file with path traversal protection
_f_backup() {
    if [[ -z "$1" ]]; then
        print_error "Usage: f --b <filename>"
        return 1
    fi

    # Strip any path components for security
    local filename
    filename=$(basename "$1")

    # Verify file exists in current directory only
    if [[ ! -f "./$filename" ]]; then
        print_error "File not found in current directory: $filename"
        return 1
    fi

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup="${filename}_backup_${timestamp}"

    if cp -a "./$filename" "./$backup"; then
        print_success "Backup created: $backup"
    else
        print_error "Failed to create backup"
        return 1
    fi
}

# Create timestamped folder on Desktop with input sanitization
_f_desktop_dir() {
    # Sanitize folder name (remove path components and special chars)
    local folder_name="${1:-folder}"
    folder_name=$(basename "$folder_name" | tr -cd '[:alnum:]_-')

    if [[ -z "$folder_name" ]]; then
        folder_name="folder"
    fi

    local dir_path="$HOME/Desktop/$(date +%F_%H-%M-%S)_${folder_name}"

    if mkdir -p "$dir_path"; then
        print_success "Created: $dir_path"
    else
        print_error "Failed to create directory"
        return 1
    fi
}

# Show directory tree (uses Python Rich for pretty output)
# Args: $1=depth (optional), $2=dest (optional)
_f_tree() {
    local depth="${1:-2}"
    local target="${2:-.}"

    # Setup venv for file menu (uses centralized venv function)
    _ensure_venv "$SHELL_V11_DIR"

    print_info "Tree: $target (depth $depth)"

    # Run inline Python script for tree view
    "$VENV_PYTHON" - "$target" "$depth" << 'PYTHON_SCRIPT'
import sys
from pathlib import Path
from rich.console import Console
from rich.tree import Tree

def build_tree(path: Path, tree: Tree, depth: int, current_depth: int = 0):
    if current_depth >= depth:
        return

    try:
        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        tree.add("[red]Permission denied[/]")
        return

    for entry in entries:
        if entry.name.startswith('.'):
            continue

        if entry.is_dir():
            style = "bold cyan"
            branch = tree.add(f"[{style}]{entry.name}/[/]")
            build_tree(entry, branch, depth, current_depth + 1)
        else:
            ext = entry.suffix.lower()
            if ext in ('.py', '.js', '.ts', '.sh', '.zsh'):
                style = "green"
            elif ext in ('.md', '.txt', '.json', '.yaml', '.yml'):
                style = "yellow"
            elif ext in ('.jpg', '.png', '.gif', '.svg'):
                style = "magenta"
            else:
                style = "white"
            tree.add(f"[{style}]{entry.name}[/]")

target = Path(sys.argv[1]).resolve()
depth = int(sys.argv[2])

console = Console()
tree = Tree(f"[bold blue]{target}[/]", guide_style="bright_black")
build_tree(target, tree, depth)
console.print(tree)
PYTHON_SCRIPT
}

# Save current directory as a bookmark
_f_bookmark_add() {
    local name="$1"

    # If no name provided, prompt for one
    if [[ -z "$name" ]]; then
        print_info "Enter bookmark name:"
        read -r name
    fi

    # Validate name
    if [[ -z "$name" ]]; then
        print_error "Bookmark name cannot be empty"
        return 1
    fi

    # Sanitize name (alphanumeric, underscore, dash only)
    name=$(echo "$name" | tr -cd '[:alnum:]_-')
    if [[ -z "$name" ]]; then
        print_error "Invalid bookmark name"
        return 1
    fi

    # Ensure config directory exists
    mkdir -p "$MRTAMAKI_CONFIG_DIR"

    # Load existing bookmarks or create empty object
    local bookmarks="{}"
    if [[ -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        bookmarks=$(cat "$MRTAMAKI_BOOKMARKS_FILE")
    fi

    # Add/update bookmark using jq
    local current_dir="$PWD"
    bookmarks=$(echo "$bookmarks" | jq --arg name "$name" --arg path "$current_dir" '. + {($name): $path}')

    # Save bookmarks
    echo "$bookmarks" > "$MRTAMAKI_BOOKMARKS_FILE"
    print_success "Bookmarked '$name' -> $current_dir"
}

# Jump to a bookmarked directory
_f_bookmark_go() {
    local name="$1"

    # Check if bookmarks file exists
    if [[ ! -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        print_error "No bookmarks saved. Use 'fk' to add one."
        return 1
    fi

    local bookmarks
    bookmarks=$(cat "$MRTAMAKI_BOOKMARKS_FILE")

    # If no name provided, list bookmarks and prompt
    if [[ -z "$name" ]]; then
        _f_bookmark_list
        echo
        print_info "Enter bookmark name:"
        read -r name
    fi

    if [[ -z "$name" ]]; then
        print_error "No bookmark selected"
        return 1
    fi

    # Get path for bookmark
    local target_path
    target_path=$(echo "$bookmarks" | jq -r --arg name "$name" '.[$name] // empty')

    if [[ -z "$target_path" ]]; then
        print_error "Bookmark not found: $name"
        return 1
    fi

    if [[ ! -d "$target_path" ]]; then
        print_error "Directory no longer exists: $target_path"
        return 1
    fi

    cd "$target_path" && print_success "Changed to: $target_path"
}

# List all bookmarks
_f_bookmark_list() {
    if [[ ! -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        print_info "No bookmarks saved."
        return 0
    fi

    print_info "Bookmarks:"
    cat "$MRTAMAKI_BOOKMARKS_FILE" | jq -r 'to_entries[] | "  \(.key) -> \(.value)"'
}

# Delete a bookmark
_f_bookmark_del() {
    local name="$1"

    if [[ ! -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        print_error "No bookmarks saved."
        return 1
    fi

    if [[ -z "$name" ]]; then
        _f_bookmark_list
        echo
        print_info "Enter bookmark name to delete:"
        read -r name
    fi

    if [[ -z "$name" ]]; then
        print_error "No bookmark selected"
        return 1
    fi

    local bookmarks
    bookmarks=$(cat "$MRTAMAKI_BOOKMARKS_FILE")

    # Check if bookmark exists
    local exists
    exists=$(echo "$bookmarks" | jq --arg name "$name" 'has($name)')

    if [[ "$exists" != "true" ]]; then
        print_error "Bookmark not found: $name"
        return 1
    fi

    # Remove bookmark
    bookmarks=$(echo "$bookmarks" | jq --arg name "$name" 'del(.[$name])')
    echo "$bookmarks" > "$MRTAMAKI_BOOKMARKS_FILE"
    print_success "Deleted bookmark: $name"
}



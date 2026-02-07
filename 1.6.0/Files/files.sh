# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Files Module
# File command functions: fa-fg, tempdir
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities (parent directory)
SHELL_V11_DIR="${0:A:h:h}"
FILES_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

#---------- VENV SETUP FOR FILE MENU ----------

# Setup venv for file menu (uses centralized venv function)
_files_setup_venv() {
    _ensure_module_venv files "$SHELL_V11_DIR"
}

# Interactive file operations menu
fmenu() {
    # Ensure venv is setup
    _files_setup_venv || return 1

    # Validate prerequisites
    local menu_script="${FILES_DIR}/file_menu.py"
    if [[ ! -f "$menu_script" ]]; then
        print_error "Menu script not found: $menu_script"
        return 1
    fi

    if [[ -z "$VENV_PYTHON" || ! -x "$VENV_PYTHON" ]]; then
        print_error "Python interpreter not available"
        return 1
    fi

    # Create temp file for result with error handling
    local tmp_result
    tmp_result=$(mktemp 2>/dev/null) || {
        print_error "Failed to create temporary file"
        return 1
    }

    # Cleanup function for robust temp file removal
    _fmenu_cleanup() {
        [[ -n "$tmp_result" && -f "$tmp_result" ]] && rm -f "$tmp_result"
    }
    trap '_fmenu_cleanup' EXIT INT TERM

    # Run menu normally, pass temp file for result
    "$VENV_PYTHON" "$menu_script" --result-file "$tmp_result"
    local exit_code=$?

    # Read result from temp file
    local output=""
    if [[ -f "$tmp_result" && -s "$tmp_result" ]]; then
        output=$(<"$tmp_result")
    fi

    # Cleanup now (before command execution which may change state)
    _fmenu_cleanup
    trap - EXIT INT TERM

    # Handle non-zero exit (user cancelled or error)
    if [[ $exit_code -ne 0 ]]; then
        return $exit_code
    fi

    # Validate output format (must start with protocol prefix)
    if [[ "$output" != __FILEMENU_CMD__:* ]]; then
        # No selection or empty output - not an error, user just exited
        return 0
    fi

    # Parse command from output
    local cmd="${output#__FILEMENU_CMD__:}"
    cmd="${cmd%%$'\n'*}"  # Remove any trailing newlines

    # Handle empty command
    if [[ -z "$cmd" ]]; then
        return 0
    fi

    # Handle special __CD__ command for bookmarks
    if [[ "$cmd" == __CD__:* ]]; then
        local target_path="${cmd#__CD__:}"
        if [[ -z "$target_path" ]]; then
            print_error "Empty target path"
            return 1
        fi
        if [[ ! -d "$target_path" ]]; then
            print_error "Directory not found: $target_path"
            return 1
        fi
        if cd "$target_path"; then
            print_success "Changed to: $target_path"
            return 0
        else
            print_error "Failed to change directory: $target_path"
            return 1
        fi
    fi

    # Execute the selected command
    case "$cmd" in
        fa) fa ;;
        fb)
            print_info "Enter search term:"
            read -r term || return 0  # Handle Ctrl+C gracefully
            [[ -n "$term" ]] && fb "$term"
            ;;
        mkcd)
            print_info "Enter directory name:"
            read -r dirname || return 0
            [[ -n "$dirname" ]] && mkcd "$dirname"
            ;;
        flast) flast ;;
        fe) fe ;;
        tempdir) tempdir ;;
        ff)
            print_info "Enter filename to backup:"
            read -r filename || return 0
            [[ -n "$filename" ]] && ff "$filename"
            ;;
        fg)
            print_info "Enter folder name (or press Enter for default):"
            read -r foldername || return 0
            fg "$foldername"
            ;;
        fbook) fbook ;;
        ftree) ftree ;;
        *)
            print_error "Unknown command: $cmd"
            return 1
            ;;
    esac
}

#---------- FILE COMMANDS -{ FA <> FG }---------------

# Reload and back up .zshrc with checksum verification
fa() {
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

    # Reload if changed
    if [[ "$before" != "$after" ]]; then
        if source ~/.zshrc 2>/dev/null; then
            print_success "zshrc reloaded"
            print_info "Backup: $backup_file"
        else
            print_error "Error reloading zshrc - syntax error?"
            return 1
        fi
    else
        print_info "No changes detected"
    fi
}

# Recursive file search with input sanitization
fb() {
    if [[ -z "$1" ]]; then
        print_error "Usage: fb <search_term>"
        return 1
    fi

    print_info "Searching for: $1"
    # Use -F for literal matching (safer than regex)
    grep -rnwF --color=always '.' -e "$1" 2>/dev/null || print_warning "No matches found"
}

# Make directory and cd into it
mkcd() {
    if [[ -z "$1" ]]; then
        print_error "Usage: mkcd <directory_name>"
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
flast() {
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
fe() {
    print_info "Searching for files larger than ${MAX_FILE_SIZE}..."
    find . -type f -size "+${MAX_FILE_SIZE}" -exec ls -lh {} + 2>/dev/null | \
        awk '{print $5 "\t" $9}' || print_info "No large files found"
}

# Create a temporary directory
tempdir() {
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
ff() {
    if [[ -z "$1" ]]; then
        print_error "Usage: ff <filename>"
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
fg() {
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

#---------- BOOKMARK SYSTEM ----------

# Config directory for bookmarks
MRTAMAKI_CONFIG_DIR="$HOME/.config/mrtamaki"
MRTAMAKI_BOOKMARKS_FILE="$MRTAMAKI_CONFIG_DIR/bookmarks.json"

# Save current directory as a bookmark
fbook() {
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
fgo() {
    local name="$1"

    # Check if bookmarks file exists
    if [[ ! -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        print_error "No bookmarks saved. Use 'fbook' to add one."
        return 1
    fi

    local bookmarks
    bookmarks=$(cat "$MRTAMAKI_BOOKMARKS_FILE")

    # If no name provided, list bookmarks and prompt
    if [[ -z "$name" ]]; then
        print_info "Available bookmarks:"
        echo "$bookmarks" | jq -r 'to_entries[] | "  \(.key) -> \(.value)"'
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
flist() {
    if [[ ! -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        print_info "No bookmarks saved."
        return 0
    fi

    print_info "Bookmarks:"
    cat "$MRTAMAKI_BOOKMARKS_FILE" | jq -r 'to_entries[] | "  \(.key) -> \(.value)"'
}

# Delete a bookmark
fdel() {
    local name="$1"

    if [[ ! -f "$MRTAMAKI_BOOKMARKS_FILE" ]]; then
        print_error "No bookmarks saved."
        return 1
    fi

    if [[ -z "$name" ]]; then
        flist
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

#---------- FILE TREE VIEW ----------

# Show directory tree (uses Python Rich for pretty output)
ftree() {
    local depth="${1:-2}"
    local target="${2:-.}"

    # Ensure venv is setup
    _files_setup_venv || return 1

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

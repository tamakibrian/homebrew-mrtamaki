# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Files Module
# File command functions: fa-fg, tempdir
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities (parent directory)
SHELL_V11_DIR="${0:A:h:h}"
source "${SHELL_V11_DIR}/utils.sh"

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
fc() {
    if [[ -z "$1" ]]; then
        print_error "Usage: fc <directory_name>"
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
fd() {
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

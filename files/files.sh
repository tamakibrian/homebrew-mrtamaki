# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Files Module
# File command functions: fa-fg, tempdir
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities (parent directory)
SHELL_V11_DIR="${0:A:h:h}"
FILES_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

#---------- VENV SETUP FOR FILE MENU ----------

# Setup venv for file menu (auto-creates on first run)
_files_setup_venv() {
    local venv_dir="${FILES_DIR}/.venv"
    local requirements="${FILES_DIR}/requirements.txt"

    # Create venv if it doesn't exist
    if [[ ! -d "$venv_dir" ]]; then
        print_info "Setting up file menu environment..."
        python3 -m venv "$venv_dir" || {
            print_error "Failed to create virtual environment"
            return 1
        }
    fi

    # Install/update requirements if needed
    local marker="${venv_dir}/.requirements_installed"
    if [[ ! -f "$marker" ]] || [[ "$requirements" -nt "$marker" ]]; then
        print_info "Installing file menu dependencies..."
        "${venv_dir}/bin/pip" install -q --upgrade pip >/dev/null 2>&1
        "${venv_dir}/bin/pip" install -q -r "$requirements" >/dev/null 2>&1 || {
            print_error "Failed to install dependencies"
            return 1
        }
        touch "$marker"
        print_success "File menu ready"
    fi

    return 0
}

# Interactive file operations menu
fmenu() {
    # Ensure venv is setup
    _files_setup_venv || return 1

    local venv_dir="${FILES_DIR}/.venv"
    local menu_script="${FILES_DIR}/file_menu.py"

    # Run menu and capture output
    local output
    output=$("${venv_dir}/bin/python" "$menu_script" 2>/dev/null)
    local exit_code=$?

    # Parse output for command
    if [[ $exit_code -eq 0 ]] && [[ "$output" =~ "__FILEMENU_CMD__:" ]]; then
        local cmd="${output#*__FILEMENU_CMD__:}"
        cmd="${cmd%%$'\n'*}"  # Remove any trailing newlines

        # Execute the selected command
        case "$cmd" in
            fa) fa ;;
            fb)
                print_info "Enter search term:"
                read -r term
                [[ -n "$term" ]] && fb "$term"
                ;;
            mkcd)
                print_info "Enter directory name:"
                read -r dirname
                [[ -n "$dirname" ]] && mkcd "$dirname"
                ;;
            flast) flast ;;
            fe) fe ;;
            tempdir) tempdir ;;
            ff)
                print_info "Enter filename to backup:"
                read -r filename
                [[ -n "$filename" ]] && ff "$filename"
                ;;
            fg)
                print_info "Enter folder name (or press Enter for default):"
                read -r foldername
                fg "$foldername"
                ;;
            *)
                print_error "Unknown command: $cmd"
                return 1
                ;;
        esac
    fi
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

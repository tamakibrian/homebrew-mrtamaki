# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Status Module
# System status and cleanup functions: h8 (status menu), h9 (health dashboard)
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities (parent directory)
SHELL_V11_DIR="${0:A:h:h}"
STATUS_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

#---------- VENV SETUP FOR STATUS MENU ----------

# Setup venv for status menu (uses centralized venv function)
_status_setup_venv() {
    _ensure_module_venv status "$SHELL_V11_DIR"
}

# Interactive system status and cleanup menu
h8() {
    # Ensure venv is setup
    _status_setup_venv || return 1

    # Validate prerequisites
    local menu_script="${STATUS_DIR}/status_menu.py"
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
    _h8_cleanup() {
        [[ -n "$tmp_result" && -f "$tmp_result" ]] && rm -f "$tmp_result"
    }
    trap '_h8_cleanup' EXIT INT TERM

    # Run menu normally, pass temp file for result
    "$VENV_PYTHON" "$menu_script" --result-file "$tmp_result"
    local exit_code=$?

    # Read result from temp file
    local output=""
    if [[ -f "$tmp_result" && -s "$tmp_result" ]]; then
        output=$(<"$tmp_result")
    fi

    # Cleanup now (before command execution which may change state)
    _h8_cleanup
    trap - EXIT INT TERM

    # Handle non-zero exit (user cancelled or error)
    if [[ $exit_code -ne 0 ]]; then
        return $exit_code
    fi

    # Validate output format (must start with protocol prefix)
    if [[ "$output" != __STATUSMENU_CMD__:* ]]; then
        # No selection or empty output - not an error, user just exited
        return 0
    fi

    # Parse command from output
    local cmd="${output#__STATUSMENU_CMD__:}"
    cmd="${cmd%%$'\n'*}"  # Remove any trailing newlines

    # Handle empty command
    if [[ -z "$cmd" ]]; then
        return 0
    fi

    # Handle special __CD__ command for venv navigation
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

    # Handle venv deletion
    if [[ "$cmd" == __DELETE_VENV__:* ]]; then
        local venv_path="${cmd#__DELETE_VENV__:}"
        if [[ -z "$venv_path" ]]; then
            print_error "Empty venv path"
            return 1
        fi
        if [[ ! -d "$venv_path" ]]; then
            print_error "Venv not found: $venv_path"
            return 1
        fi
        # Safety: verify it looks like a venv
        if [[ ! -f "$venv_path/bin/activate" ]]; then
            print_error "Not a valid venv: $venv_path"
            return 1
        fi
        if confirm "Delete venv: $venv_path?" "N"; then
            rm -rf "$venv_path"
            print_success "Deleted: $venv_path"
        else
            print_info "Cancelled"
        fi
        return 0
    fi

    # Execute the selected command
    case "$cmd" in
        pycache)
            _status_clean_pycache
            ;;
        browser)
            _status_clean_browser
            ;;
        appcache)
            _status_clean_appcache
            ;;
        *)
            print_error "Unknown command: $cmd"
            return 1
            ;;
    esac
}

#---------- CLEANUP COMMANDS ----------

# Find and delete all __pycache__ directories
_status_clean_pycache() {
    print_header "Clean __pycache__ Directories"

    local -a dirs=()
    local search_paths=("$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Projects")

    for search_path in "${search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            dirs+=("$dir")
        done < <(find "$search_path" -type d -name "__pycache__" -print0 2>/dev/null)
    done

    if (( ${#dirs[@]} == 0 )); then
        print_info "No __pycache__ directories found"
        return 0
    fi

    print_info "Found ${#dirs[@]} __pycache__ directories"

    # Show sample
    local i=0
    for dir in "${dirs[@]}"; do
        (( i >= 5 )) && break
        echo "  $dir"
        ((i++))
    done
    (( ${#dirs[@]} > 5 )) && echo "  ... and $(( ${#dirs[@]} - 5 )) more"
    echo ""

    if ! confirm "Delete all ${#dirs[@]} __pycache__ directories?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    local count=0
    for dir in "${dirs[@]}"; do
        rm -rf "$dir" 2>/dev/null && ((count++))
    done

    print_success "Deleted $count __pycache__ directories"
}

# Clear browser caches
_status_clean_browser() {
    print_header "Clear Browser Caches"

    local -A caches
    caches=(
        [Safari]="$HOME/Library/Caches/com.apple.Safari"
        [Chrome]="$HOME/Library/Caches/Google/Chrome"
        [Firefox]="$HOME/Library/Caches/Firefox"
    )

    local found=0
    for browser in Safari Chrome Firefox; do
        local path="${caches[$browser]}"
        if [[ -d "$path" ]]; then
            local size
            size=$(du -sh "$path" 2>/dev/null | cut -f1)
            print_info "$browser: $size"
            ((found++))
        fi
    done

    if (( found == 0 )); then
        print_info "No browser caches found"
        return 0
    fi

    echo ""
    if ! confirm "Clear all browser caches?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    for browser in Safari Chrome Firefox; do
        local path="${caches[$browser]}"
        if [[ -d "$path" ]]; then
            rm -rf "$path" 2>/dev/null && print_success "Cleared $browser cache"
        fi
    done
}

# Clear application caches
_status_clean_appcache() {
    print_header "Clear Application Cache"

    local cache_dir="$HOME/Library/Caches"
    if [[ ! -d "$cache_dir" ]]; then
        print_info "No cache directory found"
        return 0
    fi

    # Show total size
    local total_size
    total_size=$(du -sh "$cache_dir" 2>/dev/null | cut -f1)
    print_info "Total app cache: $total_size ($cache_dir)"
    echo ""

    if ! confirm "Clear all application caches?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    # Clear contents but keep the directory
    local count=0
    for entry in "$cache_dir"/*(N); do
        [[ -d "$entry" ]] || continue
        rm -rf "$entry" 2>/dev/null && ((count++))
    done

    print_success "Cleared $count application cache directories"
}

# Live system health dashboard
h9() {
    _status_setup_venv || return 1
    "$VENV_PYTHON" "${STATUS_DIR}/health_dashboard.py"
}

# Aliases for easier access
alias status='h8'
alias statusmenu='h8'
alias health='h9'
alias dashboard='h9'

# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Status Module
# System status and cleanup functions: h1-h5 (quick), smenu (menu), h9 (dashboard)
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

# NOTE: smenu() function moved to clean/clean.sh

#---------- HELPERS ----------

# Convert raw du block count to human-readable size
# Usage: _human_size <block_count>
# Example: size=$(_human_size 2048)  # → "1.0 MB"
_human_size() {
    echo "$1" | awk '{
        b=$1*512;
        if(b>=1073741824) printf "%.1f GB",b/1073741824;
        else if(b>=1048576) printf "%.1f MB",b/1048576;
        else if(b>=1024) printf "%.1f KB",b/1024;
        else printf "%d B",b
    }'
}

# NOTE: h1-h7 quick commands and smenu/h8 moved to clean/clean.sh

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

    print_info "Found ${#dirs[@]} __pycache__ directories:\n"

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

    if ! confirm "Delete all ${#dirs[@]} __pycache__ directories?" "N"; then
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
    print_success "Deleted $count / ${#dirs[@]} __pycache__ directories (freed ${total_human})"
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
    local -A sizes
    for browser in Safari Chrome Firefox; do
        local cache_path="${caches[$browser]}"
        if [[ -d "$cache_path" ]]; then
            local size
            size=$(du -sh "$cache_path" 2>/dev/null | cut -f1)
            sizes[$browser]="$size"
            print_info "$browser: ${COLOR_WARNING}${size}${COLOR_RESET}"

            # List top subdirectories
            local sub_count=0
            for entry in "$cache_path"/*(N); do
                [[ -d "$entry" ]] || continue
                local sub_size
                sub_size=$(du -sh "$entry" 2>/dev/null | cut -f1)
                local sub_name="${entry:t}"
                echo "    ${COLOR_WARNING}${sub_size}${COLOR_RESET}  $sub_name"
                (( ++sub_count >= 5 )) && break
            done
            local total_subs=0
            for entry in "$cache_path"/*(N); do [[ -d "$entry" ]] && ((total_subs++)); done
            (( total_subs > 5 )) && echo "    ... and $(( total_subs - 5 )) more"

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

    echo ""
    for browser in Safari Chrome Firefox; do
        local cache_path="${caches[$browser]}"
        if [[ -d "$cache_path" ]]; then
            local size="${sizes[$browser]}"
            if rm -rf "$cache_path" 2>/dev/null; then
                echo "  ${COLOR_SUCCESS}${ICON_SUCCESS}${COLOR_RESET} Cleared $browser cache (${size})"
            else
                echo "  ${COLOR_ERROR}${ICON_ERROR}${COLOR_RESET} Failed  $browser cache"
            fi
        fi
    done

    echo ""
    print_success "Browser caches cleared"
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
    print_info "Total app cache: $total_size ($cache_dir)\n"

    # List all cache directories with sizes
    local -a entries=()
    local -A entry_sizes
    for entry in "$cache_dir"/*(N); do
        [[ -d "$entry" ]] || continue
        entries+=("$entry")
        local size
        size=$(du -sh "$entry" 2>/dev/null | cut -f1)
        entry_sizes[${entry:t}]="$size"
        echo "  ${COLOR_WARNING}${size}${COLOR_RESET}  ${entry:t}"
    done

    if (( ${#entries[@]} == 0 )); then
        print_info "No cache directories found"
        return 0
    fi

    echo "\n  ${COLOR_INFO}${#entries[@]} cache directories${COLOR_RESET}\n"

    if ! confirm "Clear all application caches?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    # Clear contents but keep the directory
    echo ""
    local count=0
    local failed=0
    for entry in "${entries[@]}"; do
        local name="${entry:t}"
        local size="${entry_sizes[$name]}"
        if rm -rf "$entry" 2>/dev/null; then
            echo "  ${COLOR_SUCCESS}${ICON_SUCCESS}${COLOR_RESET} Removed $name (${size})"
            ((count++))
        else
            echo "  ${COLOR_ERROR}${ICON_ERROR}${COLOR_RESET} Failed  $name"
            ((failed++))
        fi
    done

    echo ""
    print_success "Cleared $count / ${#entries[@]} cache directories (was ${total_size} total)"
    (( failed > 0 )) && print_warning "$failed directories could not be removed (permission denied)"
}

# Find and list/delete virtual environments
_status_clean_venvs() {
    print_header "Virtual Environments"

    local -a venv_paths=()
    local -a venv_sizes=()
    local search_paths=("$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Projects")
    local max_depth=5

    print_info "Searching for virtual environments...\n"

    for search_path in "${search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            # Must have bin/activate and bin/python to be a real venv
            if [[ -f "$dir/bin/activate" && -f "$dir/bin/python" ]]; then
                venv_paths+=("$dir")
            fi
        done < <(find "$search_path" -maxdepth "$max_depth" \
            \( -name "node_modules" -o -name "Library" -o -name ".Trash" -o -name ".git" \) -prune \
            -o -type d \( -name "venv" -o -name ".venv" -o -name "env" -o -name "pyenv" \) -print0 2>/dev/null)
    done

    if (( ${#venv_paths[@]} == 0 )); then
        print_info "No virtual environments found"
        return 0
    fi

    local total_bytes=0
    for venv_dir in "${venv_paths[@]}"; do
        local size
        size=$(du -sh "$venv_dir" 2>/dev/null | cut -f1)
        local bytes
        bytes=$(du -s "$venv_dir" 2>/dev/null | cut -f1)
        (( total_bytes += bytes ))

        local display="${venv_dir/#$HOME/~}"
        echo "  ${COLOR_WARNING}${size}${COLOR_RESET}  $display"

        # Show Python version if available
        local py_version
        py_version=$("$venv_dir/bin/python" --version 2>/dev/null)
        if [[ -n "$py_version" ]]; then
            echo "       ${COLOR_INFO}${py_version}${COLOR_RESET}"
        fi
    done

    local total_human
    total_human=$(_human_size "$total_bytes")
    echo "\n  ${COLOR_INFO}Found ${#venv_paths[@]} virtual environments (${total_human} total)${COLOR_RESET}\n"

    if ! confirm "Delete all ${#venv_paths[@]} virtual environments?" "N"; then
        print_info "Cancelled"
        return 0
    fi

    echo ""
    local count=0
    local freed_bytes=0
    for venv_dir in "${venv_paths[@]}"; do
        local display="${venv_dir/#$HOME/~}"
        local size
        size=$(du -sh "$venv_dir" 2>/dev/null | cut -f1)
        local bytes
        bytes=$(du -s "$venv_dir" 2>/dev/null | cut -f1)
        if rm -rf "$venv_dir" 2>/dev/null; then
            echo "  ${COLOR_SUCCESS}${ICON_SUCCESS}${COLOR_RESET} Removed $display (${size})"
            ((count++))
            (( freed_bytes += bytes ))
        else
            echo "  ${COLOR_ERROR}${ICON_ERROR}${COLOR_RESET} Failed  $display"
        fi
    done

    local freed_human
    freed_human=$(_human_size "$freed_bytes")
    echo ""
    print_success "Deleted $count / ${#venv_paths[@]} virtual environments (freed ${freed_human})"
}

# Show cache sizes overview (read-only, no deletion)
_status_show_sizes() {
    print_header "Cache Sizes Overview"

    local grand_total_bytes=0

    # --- __pycache__ ---
    local -a pycache_dirs=()
    local search_paths=("$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Projects")

    for search_path in "${search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            pycache_dirs+=("$dir")
        done < <(find "$search_path" -type d -name "__pycache__" -print0 2>/dev/null)
    done

    local pycache_bytes=0
    for dir in "${pycache_dirs[@]}"; do
        local bytes
        bytes=$(du -s "$dir" 2>/dev/null | cut -f1)
        (( pycache_bytes += bytes ))
    done
    local pycache_human
    pycache_human=$(_human_size "$pycache_bytes")
    (( grand_total_bytes += pycache_bytes ))

    echo "  ${COLOR_WARNING}__pycache__${COLOR_RESET}"
    echo "    ${#pycache_dirs[@]} directories, ${pycache_human}"
    for dir in "${pycache_dirs[@]}"; do
        local display="${dir/#$HOME/~}"
        local size
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo "      ${COLOR_INFO}${size}${COLOR_RESET}  $display"
    done
    echo ""

    # --- Browser Caches ---
    local -A browser_caches
    browser_caches=(
        [Safari]="$HOME/Library/Caches/com.apple.Safari"
        [Chrome]="$HOME/Library/Caches/Google/Chrome"
        [Firefox]="$HOME/Library/Caches/Firefox"
    )

    local browser_total_bytes=0
    local browser_found=0
    echo "  ${COLOR_WARNING}Browser Caches${COLOR_RESET}"
    for browser in Safari Chrome Firefox; do
        local cache_path="${browser_caches[$browser]}"
        if [[ -d "$cache_path" ]]; then
            local size
            size=$(du -sh "$cache_path" 2>/dev/null | cut -f1)
            local bytes
            bytes=$(du -s "$cache_path" 2>/dev/null | cut -f1)
            (( browser_total_bytes += bytes ))
            echo "    ${COLOR_INFO}${size}${COLOR_RESET}  $browser  (${cache_path/#$HOME/~})"
            ((browser_found++))
        fi
    done
    if (( browser_found == 0 )); then
        echo "    (none found)"
    fi
    (( grand_total_bytes += browser_total_bytes ))
    echo ""

    # --- App Cache ---
    local app_cache_dir="$HOME/Library/Caches"
    local app_cache_bytes=0
    echo "  ${COLOR_WARNING}Application Cache${COLOR_RESET}"
    if [[ -d "$app_cache_dir" ]]; then
        local app_total
        app_total=$(du -sh "$app_cache_dir" 2>/dev/null | cut -f1)
        local app_bytes
        app_bytes=$(du -s "$app_cache_dir" 2>/dev/null | cut -f1)
        (( app_cache_bytes = app_bytes ))
        echo "    ${COLOR_INFO}${app_total}${COLOR_RESET}  ~/Library/Caches"

        # Top 5 largest subdirectories
        local -a sorted_entries=()
        for entry in "$app_cache_dir"/*(N); do
            [[ -d "$entry" ]] || continue
            local bytes
            bytes=$(du -s "$entry" 2>/dev/null | cut -f1)
            sorted_entries+=("$bytes $entry")
        done
        # Sort numerically descending, show top 5
        local shown=0
        for line in $(printf '%s\n' "${sorted_entries[@]}" | sort -rn); do
            local e_bytes="${line%% *}"
            local e_path="${line#* }"
            local e_size
            e_size=$(du -sh "$e_path" 2>/dev/null | cut -f1)
            echo "      ${COLOR_INFO}${e_size}${COLOR_RESET}  ${e_path:t}"
            (( ++shown >= 5 )) && break
        done
        (( ${#sorted_entries[@]} > 5 )) && echo "      ... and $(( ${#sorted_entries[@]} - 5 )) more directories"
    else
        echo "    (not found)"
    fi
    (( grand_total_bytes += app_cache_bytes ))
    echo ""

    # --- Virtual Environments ---
    local -a venv_paths=()
    local venv_total_bytes=0
    for search_path in "${search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            if [[ -f "$dir/bin/activate" && -f "$dir/bin/python" ]]; then
                venv_paths+=("$dir")
            fi
        done < <(find "$search_path" -maxdepth 5 \
            \( -name "node_modules" -o -name "Library" -o -name ".Trash" -o -name ".git" \) -prune \
            -o -type d \( -name "venv" -o -name ".venv" -o -name "env" -o -name "pyenv" \) -print0 2>/dev/null)
    done

    echo "  ${COLOR_WARNING}Virtual Environments${COLOR_RESET}"
    for venv_dir in "${venv_paths[@]}"; do
        local size
        size=$(du -sh "$venv_dir" 2>/dev/null | cut -f1)
        local bytes
        bytes=$(du -s "$venv_dir" 2>/dev/null | cut -f1)
        (( venv_total_bytes += bytes ))
        local display="${venv_dir/#$HOME/~}"
        echo "    ${COLOR_INFO}${size}${COLOR_RESET}  $display"
    done
    if (( ${#venv_paths[@]} == 0 )); then
        echo "    (none found)"
    else
        local venv_human
        venv_human=$(_human_size "$venv_total_bytes")
        echo "    ${#venv_paths[@]} venvs, ${venv_human} total"
    fi
    (( grand_total_bytes += venv_total_bytes ))
    echo ""

    # --- Grand Total ---
    local grand_human
    grand_human=$(_human_size "$grand_total_bytes")
    echo "  ${COLOR_SUCCESS}Total Cleanable: ${grand_human}${COLOR_RESET}"
    echo "  ${COLOR_INFO}Use h1-h4 to clean individual categories${COLOR_RESET}"
}

# Live system health dashboard
h9() {
    _status_setup_venv || return 1
    "$VENV_PYTHON" "${STATUS_DIR}/health_dashboard.py"
}

# Aliases (h8/smenu and h1-h7 moved to clean/clean.sh)
alias health='h9'
alias dashboard='h9'

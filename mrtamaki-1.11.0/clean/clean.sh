# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Clean Module
# System cleaner: smenu (full TUI), h1-h7 (quick commands)
# ═══════════════════════════════════════════════════════════════════════════
 
# The main mrtamaki.sh script should set MRTAMAKI_DIR.
# If not set, default to parent of the script's dir.
if [[ -z "$MRTAMAKI_DIR" ]]; then
    export MRTAMAKI_DIR="${0:A:h:h}"
fi
 
CLEAN_DIR="${MRTAMAKI_DIR}/clean"
 
# Source shared utilities
source "${MRTAMAKI_DIR}/utils.sh"
 
#---------- VENV SETUP ----------
 
_clean_setup_venv() {
    _ensure_module_venv clean "$MRTAMAKI_DIR"
}
 
#---------- INTERACTIVE MENU ----------
 
# Interactive system cleaner menu
smenu() {
    # Ensure venv is setup
    _clean_setup_venv || return 1
 
    # Validate prerequisites
    local menu_script="${CLEAN_DIR}/clean_menu.py"
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
    _clean_menu_cleanup() {
        [[ -n "$tmp_result" && -f "$tmp_result" ]] && rm -f "$tmp_result"
    }
    trap '_clean_menu_cleanup' EXIT INT TERM
 
    # Run menu, passing the mrtamaki dir and temp file for result
    MRTAMAKI_DIR="$MRTAMAKI_DIR" "$VENV_PYTHON" "$menu_script" --result-file "$tmp_result"
    local exit_code=$?
 
    # Read result from temp file
    local output=""
    if [[ -f "$tmp_result" && -s "$tmp_result" ]]; then
        output=$(<"$tmp_result")
    fi
 
    # Cleanup now (before command execution which may change state)
    _clean_menu_cleanup
    trap - EXIT INT TERM
 
    # Handle non-zero exit (user cancelled or error)
    if [[ $exit_code -ne 0 ]]; then
        return $exit_code
    fi
 
    # Validate output format (must start with protocol prefix)
    if [[ "$output" != __CLEAN_CMD__:* ]]; then
        # No selection or empty output - not an error, user just exited
        return 0
    fi
 
    # Parse command from output
    local cmd="${output#__CLEAN_CMD__:}"
    cmd="${cmd%%
\n'*}"  # Remove any trailing newlines
 
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
        pycache)  _clean_pycache ;;
        browser)  _clean_browser ;;
        appcache) _clean_appcache ;;
        xcode)    _clean_xcode ;;
        nodemod)  _clean_nodemodules ;;
        trash)    _clean_trash ;;
        *)        print_error "Unknown command: $cmd"; return 1 ;;
    esac
}
 
#---------- HELPERS ----------
 
# Convert raw du block count to human-readable size
_human_size() {
    echo "" | awk '{
        b=*512;
        if(b>=1073741824) printf "%.1f GB",b/1073741824;
        else if(b>=1048576) printf "%.1f MB",b/1048576;
        else if(b>=1024) printf "%.1f KB",b/1024;
        else printf "%d B",b
    }'
}
 
#---------- QUICK COMMANDS h1-h7, h10 ----------
 
h1() { _clean_pycache; }
h2() { _clean_browser; }
h3() { _clean_appcache; }
h4() { _clean_venvs; }
h5() { _clean_show_sizes; }
h6() { _clean_xcode; }
h7() { _clean_nodemodules; }
 
# Flush DNS cache (macOS)
h10() {
    print_info "Flushing DNS cache..."
    if sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder; then
        print_success "DNS cache cleared"
    else
        print_error "Failed to clear DNS cache"
        return 1
    fi
}
alias flushdns='h10'
 
#---------- CLEANUP COMMANDS ----------
 
# Find and delete all __pycache__ directories
_clean_pycache() {
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
_clean_browser() {
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
 
            if [[ "$browser" == "Safari" ]]; then
                # Verbose listing for Safari — show all entries with sizes
                for entry in "$cache_path"/*(N); do
                    local sub_size
                    sub_size=$(du -sh "$entry" 2>/dev/null | cut -f1)
                    local sub_name="${entry:t}"
                    if [[ -d "$entry" ]]; then
                        local file_count=0
                        for f in "$entry"/**(N.); do ((file_count++)); done
                        echo "    ${COLOR_WARNING}${sub_size}${COLOR_RESET}  $sub_name/ ($file_count files)"
                    else
                        echo "    ${COLOR_WARNING}${sub_size}${COLOR_RESET}  $sub_name"
                    fi
                done
            else
                # Compact listing for Chrome/Firefox — top 5 subdirectories
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
            fi
 
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
_clean_appcache() {
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
_clean_venvs() {
    print_header "Virtual Environments"
 
    local -a venv_paths=()
    local search_paths=("$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Projects")
    local max_depth=5
 
    # Also search the mrtamaki source directory for its own venv-* environments
    if [[ -n "$MRTAMAKI_DIR" && -d "$MRTAMAKI_DIR" ]]; then
        local already_covered=false
        for sp in "${search_paths[@]}"; do
            if [[ "$MRTAMAKI_DIR" == "$sp"/* ]]; then
                already_covered=true
                break
            fi
        done
        if ! $already_covered; then
            search_paths+=("$MRTAMAKI_DIR")
        fi
    fi
 
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
            -o -type d \( -name "venv" -o -name ".venv" -o -name "env" -o -name "pyenv" -o -name "venv-*" \) -print0 2>/dev/null)
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
 
# Show reclaimable space overview (read-only, no deletion)
_clean_show_sizes() {
    print_header "Reclaimable Space Overview"
 
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
            echo "    ${COLOR_INFO}${size}${COLOR_RESET}  $browser"
            ((browser_found++))
        fi
    done
    if (( browser_found == 0 )); then
        echo "    (none found)"
    fi
    (( grand_total_bytes += browser_total_bytes ))
    echo ""
 
    # --- Xcode DerivedData ---
    local derived_data="$HOME/Library/Developer/Xcode/DerivedData"
    echo "  ${COLOR_WARNING}Xcode DerivedData${COLOR_RESET}"
    if [[ -d "$derived_data" ]]; then
        local xcode_size
        xcode_size=$(du -sh "$derived_data" 2>/dev/null | cut -f1)
        local xcode_bytes
        xcode_bytes=$(du -s "$derived_data" 2>/dev/null | cut -f1)
        (( grand_total_bytes += xcode_bytes ))
        echo "    ${COLOR_INFO}${xcode_size}${COLOR_RESET}"
    else
        echo "    (not found)"
    fi
    echo ""
 
    # --- node_modules ---
    local -a node_dirs=()
    for search_path in "${search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            node_dirs+=("$dir")
        done < <(find "$search_path" -maxdepth 5 \
            \( -name ".git" -o -name "Library" -o -name ".Trash" -o -name "__pycache__" \) -prune \
            -o -type d -name "node_modules" -print0 2>/dev/null)
    done
 
    local node_bytes=0
    for dir in "${node_dirs[@]}"; do
        local bytes
        bytes=$(du -s "$dir" 2>/dev/null | cut -f1)
        (( node_bytes += bytes ))
    done
    local node_human
    node_human=$(_human_size "$node_bytes")
    (( grand_total_bytes += node_bytes ))
 
    echo "  ${COLOR_WARNING}node_modules${COLOR_RESET}"
    echo "    ${#node_dirs[@]} directories, ${node_human}"
    echo ""
 
    # --- Virtual Environments ---
    local -a venv_dirs=()
    local venv_total_bytes=0
    local venv_search_paths=("$HOME/Desktop" "$HOME/Documents" "$HOME/Downloads" "$HOME/Projects")
    if [[ -n "$MRTAMAKI_DIR" && -d "$MRTAMAKI_DIR" ]]; then
        venv_search_paths+=("$MRTAMAKI_DIR")
    fi
 
    for search_path in "${venv_search_paths[@]}"; do
        [[ -d "$search_path" ]] || continue
        while IFS= read -r -d '' dir; do
            if [[ -f "$dir/bin/activate" && -f "$dir/bin/python" ]]; then
                venv_dirs+=("$dir")
            fi
        done < <(find "$search_path" -maxdepth 5 \
            \( -name "node_modules" -o -name "Library" -o -name ".Trash" -o -name ".git" \) -prune \
            -o -type d \( -name "venv" -o -name ".venv" -o -name "env" -o -name "pyenv" -o -name "venv-*" \) -print0 2>/dev/null)
    done
 
    echo "  ${COLOR_WARNING}Virtual Environments${COLOR_RESET}"
    for venv_dir in "${venv_dirs[@]}"; do
        local size
        size=$(du -sh "$venv_dir" 2>/dev/null | cut -f1)
        local bytes
        bytes=$(du -s "$venv_dir" 2>/dev/null | cut -f1)
        (( venv_total_bytes += bytes ))
        local display="${venv_dir/#$HOME/~}"
        echo "    ${COLOR_INFO}${size}${COLOR_RESET}  $display"
    done
    if (( ${#venv_dirs[@]} == 0 )); then
        echo "    (none found)"
    else
        local venv_human
        venv_human=$(_human_size "$venv_total_bytes")
        echo "    ${#venv_dirs[@]} venvs, ${venv_human} total"
    fi
    (( grand_total_bytes += venv_total_bytes ))
    echo ""
 
    # --- Trash ---
    local trash_dir="$HOME/.Trash"
    echo "  ${COLOR_WARNING}Trash${COLOR_RESET}"
    if [[ -d "$trash_dir" ]]; then
        local trash_size
        trash_size=$(du -sh "$trash_dir" 2>/dev/null | cut -f1)
        local trash_bytes
        trash_bytes=$(du -s "$trash_dir" 2>/dev/null | cut -f1)
        (( grand_total_bytes += trash_bytes ))
        echo "    ${COLOR_INFO}${trash_size}${COLOR_RESET}"
    else
        echo "    (empty)"
    fi
    echo ""
 
    # --- Grand Total ---
    local grand_human
    grand_human=$(_human_size "$grand_total_bytes")
    echo "  ${COLOR_SUCCESS}Total Reclaimable: ${grand_human}${COLOR_RESET}"
    echo "  ${COLOR_INFO}Use h1-h7 to clean individual categories${COLOR_RESET}"
}
 
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
 
#---------- ALIASES ----------
 
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


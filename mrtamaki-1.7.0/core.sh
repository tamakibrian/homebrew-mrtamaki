# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Core Module
# Main functions: a1-a4, b2-g7 (proxy, IP, venv, DNS)
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities
SHELL_V11_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"
source "${SHELL_V11_DIR}/ensure_venv_manager"

#--- MAIN --{ A1 <> F6 }----

# IPRoyal URL generator
# Generates proxy URLs with secure random session IDs
a1() {
    # Load credentials from environment (set in ~/.zshenv)
    local user="${IPROYAL_USER:-}"
    local pass="${IPROYAL_PASS:-}"

    # Prompt for credentials if not set
    if [[ -z "$user" ]]; then
        echo -n "Enter IPRoyal username: "
        read user
    fi

    if [[ -z "$pass" ]]; then
        echo -n "Enter IPRoyal password: "
        read -s pass
        echo
    fi

    if [[ -z "$user" || -z "$pass" ]]; then
        print_error "Credentials required. Set IPROYAL_USER and IPROYAL_PASS in ~/.zshenv"
        return 1
    fi

    local country="nz"
    local lifetime="168h"
    local endpoint="geo.iproyal.com:12321"

    # Prompt for city
    echo -n "Enter city: "
    read city

    # Default to christchurch if empty
    [[ -z "$city" ]] && city="christchurch"

    # Generate secure random session ID (10 alphanumeric characters)
    local session
    session=$(LC_ALL=C tr -dc '0-9A-Za-z' < /dev/urandom | head -c "$SESSION_ID_LENGTH")

    # Build the proxy URL
    local proxy_url="${user}:${pass}_country-${country}_city-${city}_session-${session}_lifetime-${lifetime}@${endpoint}"

    # Copy to clipboard
    echo -n "$proxy_url" | copy_to_clipboard || {
        print_warning "Failed to copy to clipboard"
    }

    # Display result
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 IPRoyal Proxy Generated"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   City:    $city"
    echo "   Session: $session"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "$proxy_url"
    echo ""
    echo "✅ Copied to clipboard!"
}

# Oxylabs URL generator
# Generates proxy URLs with secure random session IDs
a2() {
    # Load credentials from environment (set in ~/.zshenv)
    local user="${OXYLABS_USER:-}"
    local pass="${OXYLABS_PASS:-}"

    # Validate credentials
    if [[ -z "$user" ]]; then
        print_error "OXYLABS_USER not set in environment"
        print_info "Add to ~/.zshenv: export OXYLABS_USER='your_customer_id'"
        return 1
    fi

    if [[ -z "$pass" ]]; then
        print_error "OXYLABS_PASS not set in environment"
        print_info "Add to ~/.zshenv: export OXYLABS_PASS='your_password'"
        return 1
    fi

    local country="nz"
    local sesstime="145"
    local endpoint="pr.oxylabs.io:7777"

    # Prompt for city
    echo -n "Enter city: "
    read city

    # Default to auckland if empty
    [[ -z "$city" ]] && city="auckland"

    # Generate secure random session ID (10 digits)
    local sessid
    sessid=$(LC_ALL=C tr -dc '0-9' < /dev/urandom | head -c 10)

    # Build the proxy URL
    local proxy_url="customer-${user}-cc-${country}-city-${city}-sessid-${sessid}-sesstime-${sesstime}:${pass}@${endpoint}"

    # Copy to clipboard
    echo -n "$proxy_url" | copy_to_clipboard || {
        print_warning "Failed to copy to clipboard"
    }

    # Display result
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🌐 Oxylabs Proxy Generated"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   City:    $city"
    echo "   Session: $sessid"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "$proxy_url"
    echo ""
    echo "✅ Copied to clipboard!"
}

# IPRoyal speed run: generate → bind → test → check
a3() {
    # Load credentials from environment (set in ~/.zshenv)
    local user="${IPROYAL_USER:-}"
    local pass="${IPROYAL_PASS:-}"

    if [[ -z "$user" ]]; then
        echo -n "Enter IPRoyal username: "
        read user
    fi

    if [[ -z "$pass" ]]; then
        echo -n "Enter IPRoyal password: "
        read -s pass
        echo
    fi

    if [[ -z "$user" || -z "$pass" ]]; then
        print_error "Credentials required. Set IPROYAL_USER and IPROYAL_PASS in ~/.zshenv"
        return 1
    fi

    local country="nz"
    local lifetime="168h"
    local endpoint="geo.iproyal.com:12321"

    # Prompt for city
    echo -n "Enter city: "
    read city
    [[ -z "$city" ]] && city="christchurch"

    # Generate secure random session ID (10 alphanumeric characters)
    local session
    session=$(LC_ALL=C tr -dc '0-9A-Za-z' < /dev/urandom | head -c "$SESSION_ID_LENGTH")

    # Build the proxy URL
    local proxy_url="${user}:${pass}_country-${country}_city-${city}_session-${session}_lifetime-${lifetime}@${endpoint}"

    # Copy proxy URL to clipboard
    echo -n "$proxy_url" | copy_to_clipboard || {
        print_warning "Failed to copy to clipboard"
    }

    # Display speed run banner
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 IPRoyal Speed Run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   City:    $city"
    echo "   Session: $session"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Set up proxy converter NEW venv
    local new_path="${SHELL_V11_DIR}/proxy_converter-NEW"
    if [[ ! -f "${new_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${new_path}/proxy_converter.py"
        return 1
    fi

    export MRTAMAKI_ROOT="$new_path"
    export VENV_DIR="${new_path}/venv"
    export REQUIREMENTS_FILE="${new_path}/requirements.txt"

    ensure_venv_exists || return 1

    # Launch proxy converter in background with --wait
    print_info "Binding proxy..."
    "${VENV_DIR}/bin/python" "${new_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait &
    local proxy_pid=$!

    # Wait for binding to complete and port to be copied to clipboard
    sleep 3

    # Check proxy converter is still running
    if ! kill -0 "$proxy_pid" 2>/dev/null; then
        print_error "Proxy converter failed to start"
        return 1
    fi

    # Read port from clipboard
    local port
    port=$(pbpaste)

    # Validate port is numeric
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        print_error "Expected port number on clipboard, got: $port"
        kill "$proxy_pid"
        return 1
    fi

    print_info "Proxy bound on port $port"

    # Build the HTTP proxy string for clipboard after checks
    local http_proxy="127.0.0.1:${port}"

    # Open new Terminal.app window to run c3 then d4, then copy HTTP proxy to clipboard
    local mrtamaki_sh="${SHELL_V11_DIR}/mrtamaki.sh"
    local shell_cmd="source '${mrtamaki_sh}' && c3 ${port} && d4 \$(pbpaste) && echo '' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && printf '%s' '${http_proxy}' | pbcopy && print_success 'HTTP proxy copied to clipboard: ${http_proxy}' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'"
    osascript \
        -e 'tell application "Terminal"' \
        -e 'activate' \
        -e "do script \"${shell_cmd}\"" \
        -e 'end tell'

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Proxy PID: $proxy_pid"
    echo "   Port:      $port"
    echo "   Press Ctrl+C to stop proxy server"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Wait for proxy process (keeps original terminal alive)
    wait "$proxy_pid" 2>/dev/null
}

# Oxylabs speed run: generate → bind → test → check
a4() {
    # Load credentials from environment (set in ~/.zshenv)
    local user="${OXYLABS_USER:-}"
    local pass="${OXYLABS_PASS:-}"

    if [[ -z "$user" ]]; then
        print_error "OXYLABS_USER not set in environment"
        print_info "Add to ~/.zshenv: export OXYLABS_USER='your_customer_id'"
        return 1
    fi

    if [[ -z "$pass" ]]; then
        print_error "OXYLABS_PASS not set in environment"
        print_info "Add to ~/.zshenv: export OXYLABS_PASS='your_password'"
        return 1
    fi

    local country="nz"
    local sesstime="145"
    local endpoint="pr.oxylabs.io:7777"

    # Prompt for city
    echo -n "Enter city: "
    read city
    [[ -z "$city" ]] && city="auckland"

    # Generate secure random session ID (10 digits)
    local sessid
    sessid=$(LC_ALL=C tr -dc '0-9' < /dev/urandom | head -c 10)

    # Build the proxy URL
    local proxy_url="customer-${user}-cc-${country}-city-${city}-sessid-${sessid}-sesstime-${sesstime}:${pass}@${endpoint}"

    # Copy proxy URL to clipboard
    echo -n "$proxy_url" | copy_to_clipboard || {
        print_warning "Failed to copy to clipboard"
    }

    # Display speed run banner
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Oxylabs Speed Run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   City:    $city"
    echo "   Session: $sessid"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Set up proxy converter NEW venv
    local new_path="${SHELL_V11_DIR}/proxy_converter-NEW"
    if [[ ! -f "${new_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${new_path}/proxy_converter.py"
        return 1
    fi

    export MRTAMAKI_ROOT="$new_path"
    export VENV_DIR="${new_path}/.venv"
    export REQUIREMENTS_FILE="${new_path}/requirements.txt"

    ensure_venv_exists || return 1

    # Launch proxy converter in background with --wait
    print_info "Binding proxy..."
    "${VENV_DIR}/bin/python" "${new_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait &
    local proxy_pid=$!

    # Wait for binding to complete and port to be copied to clipboard
    sleep 3

    # Check proxy converter is still running
    if ! kill -0 "$proxy_pid" 2>/dev/null; then
        print_error "Proxy converter failed to start"
        return 1
    fi

    # Read port from clipboard
    local port
    port=$(pbpaste)

    # Validate port is numeric
    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        print_error "Expected port number on clipboard, got: $port"
        kill "$proxy_pid" 2>/dev/null
        return 1
    fi

    print_info "Proxy bound on port $port"

    # Build the HTTP proxy string for clipboard after checks
    local http_proxy="127.0.0.1:${port}"

    # Open new Terminal.app window to run c3 then d4, then copy HTTP proxy to clipboard
    local mrtamaki_sh="${SHELL_V11_DIR}/mrtamaki.sh"
    local shell_cmd="source '${mrtamaki_sh}' && c3 ${port} && d4 \$(pbpaste) && echo '' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━' && printf '%s' '${http_proxy}' | pbcopy && print_success 'HTTP proxy copied to clipboard: ${http_proxy}' && echo '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'"
    osascript \
        -e 'tell application "Terminal"' \
        -e 'activate' \
        -e "do script \"${shell_cmd}\"" \
        -e 'end tell'

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Proxy PID: $proxy_pid"
    echo "   Port:      $port"
    echo "   Press Ctrl+C to stop proxy server"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Wait for proxy process (keeps original terminal alive)
    wait "$proxy_pid" 2>/dev/null
}

# Proxy converter - Uses ensure_venv_manager for lifecycle management
# Submenu to select between Legacy (OG) and New proxy converters
b2() {
    local legacy_path="${SHELL_V11_DIR}/proxy_converter-OG"
    local new_path="${SHELL_V11_DIR}/proxy_converter-NEW"

    print_header "Proxy Converter"

    # Show submenu
    echo ""
    echo "  Select proxy converter version:"
    echo ""
    echo "    [1] Legacy (OG)"
    echo "    [2] New"
    echo "    [0] Cancel"
    echo ""
    echo -n "  Choice: "
    read choice

    local project_path=""
    case "$choice" in
        1)
            project_path="$legacy_path"
            if [[ ! -d "$project_path" ]]; then
                print_error "Legacy proxy converter not found: $project_path"
                return 1
            fi
            print_info "Launching Legacy (OG) proxy converter..."
            ;;
        2)
            project_path="$new_path"
            if [[ ! -d "$project_path" ]]; then
                print_error "New proxy converter not found: $project_path"
                return 1
            fi
            print_info "Launching New proxy converter..."
            ;;
        0|q|Q)
            print_info "Cancelled"
            return 0
            ;;
        *)
            print_error "Invalid choice: $choice"
            return 1
            ;;
    esac

    # Validate proxy_converter.py exists before proceeding
    if [[ ! -f "${project_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${project_path}/proxy_converter.py"
        return 1
    fi

    # Set and export paths for ensure_venv_manager (override for this project)
    # Export ensures variables propagate to any subshells
    export MRTAMAKI_ROOT="$project_path"
    export VENV_DIR="${project_path}/.venv"
    export REQUIREMENTS_FILE="${project_path}/requirements.txt"
    export PROXY_CONVERTER_CMD="${VENV_DIR}/bin/python \"${project_path}/proxy_converter.py\""

    # Run via ensure_venv_manager (handles venv, deps, run, and cleanup prompts)
    proxy_converter_run
    return $?
}

# IP query via proxy with improved error handling and validation
c3() {
    if [[ -z "$1" ]]; then
        print_error "Usage: c3 <port>"
        print_info "Example: c3 8080"
        return 1
    fi

    local port="$1"

    # Validate port number
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [[ "$port" -lt "$PORT_MIN" || "$port" -gt "$PORT_MAX" ]]; then
        print_error "Invalid port number. Must be between ${PORT_MIN}-${PORT_MAX}"
        return 1
    fi

    print_info "Testing proxy on port $port..."

    # Fetch JSON via proxy with timeout and retry
    local json
    json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
        -x "127.0.0.1:$port" \
        https://ipinfo.io/json)" || {
        print_error "⚠️ No response from port $port"
        return 1
    }

    # Validate JSON structure
    if ! printf '%s' "$json" | grep -q '"ip"'; then
        print_error "Invalid response format (missing IP field)"
        print_info "Raw response:"
        printf '%s\n' "$json"
        return 1
    fi

    # Extract the IP field
    local ip
    ip="$(printf '%s' "$json" | sed -nE 's/.*"ip"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')"

    if [[ -z "$ip" ]]; then
        print_error "Could not parse IP from response"
        print_info "Raw response:"
        printf '%s\n' "$json"
        return 1
    fi

    # Print + copy just the IP
    print_info "IP: $ip"
    if printf '%s' "$ip" | copy_to_clipboard; then
        print_info "Copied IP to clipboard ✅"
    fi
}

# Scamalytics IP reputation check with improved error handling
d4() {
    if [[ -z "$1" ]]; then
        print_error "Usage: d4 <ip_address>"
        return 1
    fi

    local api_key="${SCAMALYTICS_API_KEY:-}"
    if [[ -z "$api_key" ]]; then
        print_error "SCAMALYTICS_API_KEY not set"
        print_info "Add to ~/.zshenv: export SCAMALYTICS_API_KEY='your_key'"
        return 1
    fi

    local ip="$1"

    # Basic IP validation
    if ! [[ "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        print_error "Invalid IP address format"
        return 1
    fi

    print_info "Checking IP: $ip"

    # Fetch with timeout and validate response
    local response
    response=$(curl -fsS --max-time "$NETWORK_TIMEOUT" \
        "https://api11.scamalytics.com/v3/bradeysulley/?key=${api_key}&ip=$ip") || {
        print_error "Failed to retrieve IP information"
        return 1
    }

    # Validate JSON before parsing
    if ! command -v jq &>/dev/null; then
        print_warning "jq not installed, showing raw response:"
        printf '%s\n' "$response"
        return 0
    fi

    if ! printf '%s' "$response" | jq -e . >/dev/null 2>&1; then
        print_error "Invalid JSON response"
        print_info "Raw response:"
        printf '%s\n' "$response"
        return 1
    fi

    printf '%s\n' "$response" | jq .
}

# Clean up virtual environments with dependency purge
e5() {
    local search_root="${1:-$HOME}"
    local -a venvs=()

    print_header "Virtual Environment Cleanup with Dependency Purge"
    print_info "Scanning for virtual environments under: $search_root"

    # Find directories with depth limit and targeted exclusions
    while IFS= read -r -d '' dir; do
        # Validate structure: must contain bin/activate and bin/python
        if [[ -f "$dir/bin/activate" && -x "$dir/bin/python" ]]; then
            # Additional safety: verify it's actually a venv
            if "$dir/bin/python" -c "import sys; exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>/dev/null; then
                venvs+=("$dir")
            fi
        fi
    done < <(find "$search_root" \
        -maxdepth "$VENV_SEARCH_DEPTH" \
        -type d \
        \( -name "venv" -o -name ".venv" -o -name "env" -o -name "pyenv" \) \
        -not -path "*/node_modules/*" \
        -not -path "*/Library/*" \
        -not -path "*/homebrew/*" \
        -not -path "*/.Trash/*" \
        -print0 2>/dev/null)

    if (( ${#venvs[@]} == 0 )); then
        print_info "No virtual environments found"
        return 0
    fi

    # Display found venvs with sizes
    print_info "Found ${#venvs[@]} virtual environments:"
    echo ""
    for v in "${venvs[@]}"; do
        local size
        size=$(du -sh "$v" 2>/dev/null | cut -f1)
        printf '  - %s (%s)\n' "$v" "${size:-unknown}"
    done
    echo ""

    if ! confirm "Purge dependencies and delete ALL of these virtual environments?" "N"; then
        print_info "Cleanup cancelled"
        return 0
    fi

    local success_count=0
    local fail_count=0

    for v in "${venvs[@]}"; do
        # Safety: never delete system Python or brew prefixes
        case "$v" in
            /usr/*|/opt/homebrew/*|/System/*|/Library/*)
                print_warning "⚠️  Skipping system path: $v"
                ((fail_count++))
                continue
                ;;
        esac

        print_info "Processing: $v"

        # Step 1: Purge pip cache and dependencies
        local pip_cmd="$v/bin/pip"
        if [[ -x "$pip_cmd" ]]; then
            echo "  → Purging pip cache..."
            "$pip_cmd" cache purge 2>/dev/null || print_warning "  ⚠️  Cache purge failed"
            
            echo "  → Uninstalling packages..."
            local packages
            packages=$("$pip_cmd" freeze 2>/dev/null)
            if [[ -n "$packages" ]]; then
                echo "$packages" | xargs -r "$pip_cmd" uninstall -y 2>/dev/null || print_warning "  ⚠️  Some packages failed to uninstall"
            fi
        fi

        # Step 2: Delete venv directory
        echo "  → Deleting venv..."
        if rm -rf -- "$v" 2>/dev/null; then
            print_success "✅ Removed: $v"
            ((success_count++))
        else
            print_error "❌ Failed to remove: $v"
            ((fail_count++))
        fi
        echo ""
    done

    # Summary
    print_header "Cleanup Summary"
    echo "  Total processed: ${#venvs[@]}"
    echo "  Successful:      $success_count"
    echo "  Failed:          $fail_count"
    
    if (( success_count > 0 )); then
        print_success "Virtual environment cleanup complete"
    fi
}

# Flush DNS cache (macOS)
f6() {
    print_info "Flushing DNS cache..."
    if sudo dscacheutil -flushcache && sudo killall -HUP mDNSResponder; then
        print_success "DNS cache cleared"
    else
        print_error "Failed to clear DNS cache"
        return 1
    fi
}

# Pip purge - clear cache and uninstall all packages
g7() {
    local target="${1:-system}"

    print_header "Pip Purge"

    if [[ "$target" == "system" ]]; then
        # System pip
        local pip_cmd="pip3"
        if ! command -v "$pip_cmd" &>/dev/null; then
            print_error "pip3 not found"
            return 1
        fi

        print_info "Target: system pip"

        # Show what will be removed
        local packages
        packages=$("$pip_cmd" list --user --format=freeze 2>/dev/null)
        if [[ -z "$packages" ]]; then
            print_info "No user-installed packages found"
            print_info "Clearing pip cache..."
            "$pip_cmd" cache purge 2>/dev/null && print_success "Pip cache cleared"
            return 0
        fi

        echo "$packages"
        echo ""

        if ! confirm "Uninstall all user packages and clear cache?" "N"; then
            print_info "Cancelled"
            return 0
        fi

        print_info "Clearing pip cache..."
        "$pip_cmd" cache purge 2>/dev/null

        print_info "Uninstalling user packages..."
        "$pip_cmd" list --user --format=freeze | cut -d= -f1 | xargs -r "$pip_cmd" uninstall -y 2>/dev/null

    else
        # Venv path provided
        local venv_pip="$target/bin/pip"
        if [[ ! -x "$venv_pip" ]]; then
            print_error "Venv pip not found: $venv_pip"
            return 1
        fi

        print_info "Target: $target"

        local packages
        packages=$("$venv_pip" freeze 2>/dev/null)
        if [[ -z "$packages" ]]; then
            print_info "No packages found in venv"
            print_info "Clearing pip cache..."
            "$venv_pip" cache purge 2>/dev/null && print_success "Pip cache cleared"
            return 0
        fi

        echo "$packages"
        echo ""

        if ! confirm "Uninstall all packages and clear cache?" "N"; then
            print_info "Cancelled"
            return 0
        fi

        print_info "Clearing pip cache..."
        "$venv_pip" cache purge 2>/dev/null

        print_info "Uninstalling packages..."
        "$venv_pip" freeze | xargs -r "$venv_pip" uninstall -y 2>/dev/null
    fi

    print_success "Pip purge complete"
}

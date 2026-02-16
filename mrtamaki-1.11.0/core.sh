# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Core Module
# Main functions: a1-a4, b2-g7 (proxy, IP, venv, DNS)
# ═══════════════════════════════════════════════════════════════════════════

# Source shared utilities
SHELL_V11_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

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
        read -r user
    fi

    if [[ -z "$pass" ]]; then
        echo -n "Enter IPRoyal password: "
        read -rs pass
        echo
    fi

    if [[ -z "$user" || -z "$pass" ]]; then
        print_error "Credentials required. Set IPROYAL_USER and IPROYAL_PASS in ~/.zshenv"
        return 1
    fi

    local country="nz"
    local lifetime="168h"
    local -a ports=(51200 32325 12325)
    local rand_port=${ports[$((RANDOM % ${#ports[@]} + 1))]}
    local endpoint="geo.iproyal.com:${rand_port}"

    # Prompt for city
    local city
    echo -n "Enter city: "
    read -r city

    # Default to christchurch if empty
    [[ -z "$city" ]] && city="christchurch"

    # Generate secure random session ID (8 random alphanumeric characters)
    local session
    session=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 8)

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
    echo "   Port:    $rand_port"
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
    local city
    echo -n "Enter city: "
    read -r city

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
        read -r user
    fi

    if [[ -z "$pass" ]]; then
        echo -n "Enter IPRoyal password: "
        read -rs pass
        echo
    fi

    if [[ -z "$user" || -z "$pass" ]]; then
        print_error "Credentials required. Set IPROYAL_USER and IPROYAL_PASS in ~/.zshenv"
        return 1
    fi

    local country="nz"
    local lifetime="168h"
    local -a ports=(51200 32325 12325)
    local rand_port=${ports[$((RANDOM % ${#ports[@]} + 1))]}
    local endpoint="geo.iproyal.com:${rand_port}"

    # Prompt for city
    local city
    echo -n "Enter city: "
    read -r city
    [[ -z "$city" ]] && city="auckland"

    # Generate secure random session ID (8 random alphanumeric characters)
    local session
    session=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 8)

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
    echo "   Port:    $rand_port"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Set up proxy converter venv (centralized)
    local new_path="${SHELL_V11_DIR}/proxy_converter"
    if [[ ! -f "${new_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${new_path}/proxy_converter.py"
        return 1
    fi

    _ensure_module_venv proxy "$SHELL_V11_DIR" || return 1

    # Launch proxy converter in background with --wait
    print_info "Binding proxy..."
    "$VENV_PYTHON" "${new_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait &
    local proxy_pid=$!

    # Cleanup trap: kill background proxy on Ctrl+C
    trap "kill $proxy_pid 2>/dev/null; trap - INT TERM; return 130" INT TERM

    # Wait for binding to complete and port to be copied to clipboard
    sleep 3

    # Check proxy converter is still running
    if ! kill -0 "$proxy_pid" 2>/dev/null; then
        trap - INT TERM
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
        trap - INT TERM
        return 1
    fi

    print_info "Proxy bound on port $port"

    # Build the HTTP proxy string for clipboard after checks
    local http_proxy="127.0.0.1:${port}"

    # Run IP check and DNS leak test in the same terminal
    c3 "$port"
    d4 "$(pbpaste)"

    # Copy HTTP proxy to clipboard for easy use
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf '%s' "$http_proxy" | pbcopy
    print_success "HTTP proxy copied to clipboard: $http_proxy"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Proxy PID: $proxy_pid"
    echo "   Port:      $port"
    echo "   Press Ctrl+C to stop proxy server"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Wait for proxy process (keeps original terminal alive)
    wait "$proxy_pid" 2>/dev/null
    trap - INT TERM
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
    local city
    echo -n "Enter city: "
    read -r city
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

    # Set up proxy converter venv (centralized)
    local new_path="${SHELL_V11_DIR}/proxy_converter"
    if [[ ! -f "${new_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${new_path}/proxy_converter.py"
        return 1
    fi

    _ensure_module_venv proxy "$SHELL_V11_DIR" || return 1

    # Launch proxy converter in background with --wait
    print_info "Binding proxy..."
    "$VENV_PYTHON" "${new_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait &
    local proxy_pid=$!

    # Cleanup trap: kill background proxy on Ctrl+C
    trap "kill $proxy_pid 2>/dev/null; trap - INT TERM; return 130" INT TERM

    # Wait for binding to complete and port to be copied to clipboard
    sleep 3

    # Check proxy converter is still running
    if ! kill -0 "$proxy_pid" 2>/dev/null; then
        trap - INT TERM
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
        trap - INT TERM
        return 1
    fi

    print_info "Proxy bound on port $port"

    # Build the HTTP proxy string for clipboard after checks
    local http_proxy="127.0.0.1:${port}"

    # Run IP check and DNS leak test in the same terminal
    c3 "$port"
    d4 "$(pbpaste)"

    # Copy HTTP proxy to clipboard for easy use
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf '%s' "$http_proxy" | pbcopy
    print_success "HTTP proxy copied to clipboard: $http_proxy"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Proxy PID: $proxy_pid"
    echo "   Port:      $port"
    echo "   Press Ctrl+C to stop proxy server"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Wait for proxy process (keeps original terminal alive)
    wait "$proxy_pid" 2>/dev/null
    trap - INT TERM
}

# Proxy converter - Uses centralized venv management
# ── Helper: generate proxy URLs ──────────────────────────────────────────
# Generates proxy URLs without prompts or clipboard side-effects.
# Usage: _gen_iproyal_url <city>  → prints URL to stdout
#        _gen_oxylabs_url <city>  → prints URL to stdout

_gen_iproyal_url() {
    local city="${1:-christchurch}"
    local user="${IPROYAL_USER:-}"
    local pass="${IPROYAL_PASS:-}"
    local country="nz"
    local lifetime="168h"
    local -a ports=(51200 32325 12325)
    local rand_port=${ports[$((RANDOM % ${#ports[@]} + 1))]}
    local endpoint="geo.iproyal.com:${rand_port}"
    local session
    session=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 8)
    printf '%s' "${user}:${pass}_country-${country}_city-${city}_session-${session}_lifetime-${lifetime}@${endpoint}"
}

_gen_oxylabs_url() {
    local city="${1:-auckland}"
    local user="${OXYLABS_USER:-}"
    local pass="${OXYLABS_PASS:-}"
    local country="nz"
    local sesstime="145"
    local endpoint="pr.oxylabs.io:7777"
    local sessid
    sessid=$(LC_ALL=C tr -dc '0-9' < /dev/urandom | head -c 10)
    printf '%s' "customer-${user}-cc-${country}-city-${city}-sessid-${sessid}-sesstime-${sesstime}:${pass}@${endpoint}"
}

# ── Helper: batch generate + bind ────────────────────────────────────────
# Usage: _b2_gen_and_bind <provider> <count> <city> <project_path> [debug_flag] [do_check]
#   provider: "a1" (IPRoyal) or "a2" (Oxylabs)

_b2_gen_and_bind() {
    local provider="$1"
    local count="$2"
    local city="$3"
    local project_path="$4"
    local debug_flag="${5:-}"
    local do_check="${6:-false}"

    # Validate credentials
    if [[ "$provider" == "a1" ]]; then
        if [[ -z "${IPROYAL_USER:-}" || -z "${IPROYAL_PASS:-}" ]]; then
            print_error "IPROYAL_USER / IPROYAL_PASS not set"
            print_info "Add to ~/.zshenv: export IPROYAL_USER='...' IPROYAL_PASS='...'"
            return 1
        fi
        local provider_name="IPRoyal"
        local default_city="christchurch"
    else
        if [[ -z "${OXYLABS_USER:-}" || -z "${OXYLABS_PASS:-}" ]]; then
            print_error "OXYLABS_USER / OXYLABS_PASS not set"
            print_info "Add to ~/.zshenv: export OXYLABS_USER='...' OXYLABS_PASS='...'"
            return 1
        fi
        local provider_name="Oxylabs"
        local default_city="auckland"
    fi

    [[ -z "$city" ]] && city="$default_city"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 $provider_name Batch Generate & Bind"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Provider: $provider_name"
    echo "   City:     $city"
    echo "   Count:    $count"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local -a bg_pids=()
    local -a bound_ports=()
    local -a output_files=()

    # Comprehensive cleanup trap
    trap '
        print_info "\nCleaning up background processes and temp files..."
        for p in "${bg_pids[@]}"; do kill "$p" 2>/dev/null; done
        for f in "${output_files[@]}"; do rm -f "$f"; done
        trap - INT TERM
        return 130
    ' INT TERM

    for i in $(seq 1 "$count"); do
        local proxy_url
        if [[ "$provider" == "a1" ]]; then
            proxy_url=$(_gen_iproyal_url "$city")
        else
            proxy_url=$(_gen_oxylabs_url "$city")
        fi

        print_info "[$i/$count] Binding proxy..."
        
        local output_file
        output_file=$(mktemp) || {
            print_error "[$i/$count] Failed to create temp output file"
            continue
        }
        output_files+=("$output_file")

        # Launch proxy converter in unbuffered mode (-u) and redirect output
        "$VENV_PYTHON" -u "${project_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait $debug_flag &> "$output_file" &
        local pid=$!
        bg_pids+=($pid)

        # Poll the output file for the port number
        local port_val=""
        local retries=10 # Wait up to 5 seconds (10 * 0.5s)
        while [[ $retries -gt 0 ]]; do
            port_val=$(grep -oE 'HTTP port [0-9]+' "$output_file" | cut -d' ' -f3)
            if [[ -n "$port_val" ]]; then
                break
            fi
            # Check if the process died before it could bind
            if ! kill -0 "$pid" 2>/dev/null; then
                print_error "[$i/$count] Proxy converter failed to start. Log:"
                cat "$output_file" # Show what went wrong
                break
            fi
            sleep 0.5
            ((retries--))
        done

        if [[ -n "$port_val" ]]; then
            bound_ports+=($port_val)
            print_success "[$i/$count] Bound on port $port_val (PID $pid)"
        else
            print_warning "[$i/$count] Timed out waiting for port from PID $pid"
            kill "$pid" 2>/dev/null
        fi
    done
    
    # Cleanup temp files now that we have the ports
    for f in "${output_files[@]}"; do rm -f "$f"; done

    # ── Summary ───────────────────────────────────────────────────────
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ $provider_name — ${#bound_ports[@]}/${count} proxies bound"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    local idx=0
    for port_val in "${bound_ports[@]}"; do
        idx=$((idx + 1))
        echo "   [$idx]  127.0.0.1:${port_val}"
    done
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [[ ${#bg_pids[@]} -eq 0 ]]; then
        print_error "No proxies were started"
        trap - INT TERM # Disarm trap
        return 1
    fi

    # Export bound ports for --check flag
    typeset -ga _B2_BOUND_PORTS=("${bound_ports[@]}")

    # ── Batch check (runs while proxies are still alive) ───────────────
    if [[ "$do_check" == "true" && ${#_B2_BOUND_PORTS[@]} -gt 0 ]]; then
        _b2_batch_check
    fi
    unset _B2_BOUND_PORTS

    echo "   PIDs: ${bg_pids[*]}"
    echo "   Press Ctrl+C to stop all proxy servers"
    echo ""

    # Wait for all background processes
    for pid in "${bg_pids[@]}"; do
        wait "$pid" 2>/dev/null
    done
    
    # Disarm the trap now that we're done
    trap - INT TERM
}

# ── Helper: batch check IPs after bind ──────────────────────────────────
# Iterates over _B2_BOUND_PORTS, runs c3 (IP fetch + DNS leak) for each.
# Skips ports where the proxy is unreachable.

_b2_batch_check() {
    local -a ports=("${_B2_BOUND_PORTS[@]}")
    local total=${#ports[@]}

    if [[ $total -eq 0 ]]; then
        print_warning "No bound ports to check"
        return 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Batch IP Check — $total port(s)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local idx=0
    local passed=0
    local failed=0

    for port_val in "${ports[@]}"; do
        idx=$((idx + 1))
        print_header "[$idx/$total] Checking port $port_val"

        if c3 "$port_val"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
            print_warning "[$idx/$total] Port $port_val — check failed, skipping"
        fi

        # Separator between checks (skip after last)
        if [[ $idx -lt $total ]]; then
            echo ""
            echo "───────────────────────────────────────────────────"
            echo ""
        fi
    done

    # ── Summary ───────────────────────────────────────────────────────
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Batch Check Complete — $passed passed, $failed failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

b2() {
    local project_path="${SHELL_V11_DIR}/proxy_converter"
    local module_name="proxy"

    if [[ ! -d "$project_path" ]]; then
        print_error "Proxy converter not found: $project_path"
        return 1
    fi

    # Validate proxy_converter.py exists before proceeding
    if [[ ! -f "${project_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${project_path}/proxy_converter.py"
        return 1
    fi

    # ── Flag parsing ──────────────────────────────────────────────────────
    local flag=""
    local bind_proxy_str=""
    local debug_flag=""
    local wait_flag=""
    local skip_cleanup=false
    local gen_count=1
    local gen_city=""
    local do_check=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --bind|-b)
                flag="bind"
                if [[ -n "$2" && ! "$2" =~ ^-- ]]; then
                    bind_proxy_str="$2"
                    shift
                fi
                ;;
            --a1)
                flag="gen_a1"
                # Peek for optional count (numeric)
                if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                    gen_count="$2"
                    shift
                fi
                # Peek for optional city (non-flag string)
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                    gen_city="$2"
                    shift
                fi
                ;;
            --a2)
                flag="gen_a2"
                if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                    gen_count="$2"
                    shift
                fi
                if [[ -n "$2" && ! "$2" =~ ^- ]]; then
                    gen_city="$2"
                    shift
                fi
                ;;
            --list|--ls|-l)
                flag="list"
                skip_cleanup=true
                ;;
            --clean|-c)
                flag="clean"
                ;;
            --debug|-d)
                debug_flag="--debug"
                ;;
            --wait|-w)
                wait_flag="--wait"
                ;;
            --check|-k)
                do_check=true
                ;;
            --help|--h|-h)
                flag="help"
                ;;
            *)
                print_error "Unknown flag: $1"
                print_info "Run b2 --help for usage"
                return 1
                ;;
        esac
        shift
    done

    # ── Help ──────────────────────────────────────────────────────────────
    if [[ "$flag" == "help" ]]; then
        print_header "b2 — Proxy Converter"
        echo ""
        print_info "Usage: b2 [flags]"
        echo ""
        printf "  %-28s %s\n" "(no flags)" "Launch interactive TUI"
        printf "  %-28s %s\n" "--bind, -b <proxy>" "Bind a SOCKS5 proxy (user:pass@host:port)"
        printf "  %-28s %s\n" "--a1 [count] [city]" "Generate & bind IPRoyal proxies"
        printf "  %-28s %s\n" "--a2 [count] [city]" "Generate & bind Oxylabs proxies"
        printf "  %-28s %s\n" "--list, --ls, -l" "List active proxy bindings"
        printf "  %-28s %s\n" "--clean, -c" "Remove ~/.bindproxy.json"
        printf "  %-28s %s\n" "--debug, -d" "Enable debug output (combine with other flags)"
        printf "  %-28s %s\n" "--wait, -w" "Keep running after --bind (for background use)"
        printf "  %-28s %s\n" "--check, -k" "Check IPs + DNS leak after batch bind"
        printf "  %-28s %s\n" "--help, --h, -h" "Show this help"
        echo ""
        print_info "Examples:"
        printf "  b2                          # open TUI\n"
        printf "  b2 --bind user:pass@h:1080  # bind proxy directly\n"
        printf "  b2 --a1 3 auckland          # 3 IPRoyal proxies in Auckland\n"
        printf "  b2 --a2 2                   # 2 Oxylabs proxies (default city)\n"
        printf "  b2 --a1                     # 1 IPRoyal proxy (default city)\n"
        printf "  b2 --ls                     # show active proxies\n"
        printf "  b2 -d --a1 2 wellington     # 2 IPRoyal + debug output\n"
        printf "  b2 --a1 3 --check               # 3 IPRoyal + check all IPs\n"
        printf "  b2 --a2 2 auckland --check       # 2 Oxylabs Auckland + check\n"
        return 0
    fi

    # ── Clean ─────────────────────────────────────────────────────────────
    if [[ "$flag" == "clean" ]]; then
        if [[ -f "$HOME/.bindproxy.json" ]]; then
            rm -f "$HOME/.bindproxy.json" && print_success "Removed ~/.bindproxy.json"
        else
            print_info "No ~/.bindproxy.json found"
        fi
        return 0
    fi

    # Set up centralized venv
    _ensure_module_venv "$module_name" "$SHELL_V11_DIR" || return 1

    # ── Dispatch ──────────────────────────────────────────────────────────
    local exit_code=0

    if [[ "$flag" == "gen_a1" ]]; then
        _b2_gen_and_bind "a1" "$gen_count" "$gen_city" "$project_path" "$debug_flag" "$do_check"
        exit_code=$?

    elif [[ "$flag" == "gen_a2" ]]; then
        _b2_gen_and_bind "a2" "$gen_count" "$gen_city" "$project_path" "$debug_flag" "$do_check"
        exit_code=$?

    elif [[ "$flag" == "bind" ]]; then
        # Prompt for proxy string if not provided inline
        if [[ -z "$bind_proxy_str" ]]; then
            printf "%s" "Proxy (user:pass@host:port): "
            read -r bind_proxy_str
            if [[ -z "$bind_proxy_str" ]]; then
                print_error "No proxy string provided"
                return 1
            fi
        fi
        "$VENV_PYTHON" "${project_path}/proxy_converter.py" --cli --bind "$bind_proxy_str" $debug_flag $wait_flag
        exit_code=$?

    elif [[ "$flag" == "list" ]]; then
        "$VENV_PYTHON" "${project_path}/proxy_converter.py" --cli --list $debug_flag
        exit_code=$?

    else
        # No flags — launch interactive TUI
        print_info "Launching proxy converter..."
        "$VENV_PYTHON" "${project_path}/proxy_converter.py" $debug_flag
        exit_code=$?
    fi

    # ── Batch check warning (--check without --a1/--a2) ────────────────
    if $do_check && [[ "$flag" != "gen_a1" && "$flag" != "gen_a2" ]]; then
        print_warning "--check requires --a1 or --a2 (batch gen)"
    fi

    # Batch gen handled everything internally (bind + check + wait); exit now
    if [[ "$flag" == "gen_a1" || "$flag" == "gen_a2" ]]; then
        return $exit_code
    fi

    if [[ $exit_code -ne 0 ]]; then
        print_warning "Proxy converter exited with code: $exit_code"
    fi

    # Post-run cleanup: offer to remove bindproxy config (skip for --list, --clean, --help)
    if ! $skip_cleanup && [[ "$flag" != "bind" || -z "$wait_flag" ]]; then
        echo ""
        if [[ -f "$HOME/.bindproxy.json" ]]; then
            if confirm "Remove ~/.bindproxy.json?" "N"; then
                rm -f "$HOME/.bindproxy.json" && print_success "Removed ~/.bindproxy.json"
            fi
        fi
    fi

    return $exit_code
}

# IP query via proxy with improved error handling and validation
c3() {
    local port="$1"
    local use_proxy=true

    if [[ -z "$port" ]]; then
        use_proxy=false
        print_info "No port specified — checking system IP..."
    else
        # Validate port number
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [[ "$port" -lt "$PORT_MIN" || "$port" -gt "$PORT_MAX" ]]; then
            print_error "Invalid port number. Must be between ${PORT_MIN}-${PORT_MAX}"
            return 1
        fi
        print_info "Testing proxy on port $port..."
    fi

    # Fetch JSON with timeout and retry (proxy only if port given)
    local json
    if $use_proxy; then
        json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
            -x "127.0.0.1:$port" \
            https://ipinfo.io/json)" || {
            print_error "⚠️ No response from port $port"
            return 1
        }
    else
        json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
            https://ipinfo.io/json)" || {
            print_error "⚠️ No response from ipinfo.io"
            return 1
        }
    fi

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

    # Display full IP info with Rich panels
    local panel_title
    if $use_proxy; then
        panel_title="  Proxy IP Info"
    else
        panel_title="  System IP Info"
    fi

    _ensure_module_venv banner "$SHELL_V11_DIR" 2>/dev/null
    if [[ -n "$VENV_PYTHON" ]] && "$VENV_PYTHON" -c "import rich" 2>/dev/null; then
        _IPINFO_JSON="$json" _PANEL_TITLE="$panel_title" "$VENV_PYTHON" - <<'PYEOF'
import os, json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()
data = json.loads(os.environ['_IPINFO_JSON'])

table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
table.add_column("Field", style="bold cyan")
table.add_column("Value", style="white")

fields = [
    ("ip",       "IP Address"),
    ("hostname", "Hostname"),
    ("city",     "City"),
    ("region",   "Region"),
    ("country",  "Country"),
    ("loc",      "Location"),
    ("org",      "Organization"),
    ("postal",   "Postal"),
    ("timezone", "Timezone"),
]

for key, label in fields:
    val = data.get(key)
    if val:
        table.add_row(label, str(val))

console.print()
title = os.environ.get('_PANEL_TITLE', '  IP Info')
console.print(Panel(table, title=f"[bold green]{title}[/]", border_style="green", box=box.ROUNDED))
console.print()
PYEOF
    else
        # Fallback: plain text display
        print_info "IP: $ip"
        printf '%s\n' "$json"
    fi

    # Run DNS leak test (checks which DNS resolvers your system uses)
    echo ""
    d6 "$port"

    # Copy IP to clipboard
    echo ""
    if printf '%s' "$ip" | copy_to_clipboard; then
        print_info "Copied IP to clipboard ✅"
    fi
}

# Scamalytics IP reputation check with improved error handling
d4() {
    local api_key="${SCAMALYTICS_API_KEY:-}"
    if [[ -z "$api_key" ]]; then
        print_error "SCAMALYTICS_API_KEY not set"
        print_info "Add to ~/.zshenv: export SCAMALYTICS_API_KEY='your_key'"
        return 1
    fi

    local ip="$1"

    # If no IP provided, silently fetch system IP
    if [[ -z "$ip" ]]; then
        print_info "No IP specified — fetching system IP..."
        local sys_json
        sys_json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
            https://ipinfo.io/json)" || {
            print_error "⚠️ Failed to fetch system IP from ipinfo.io"
            return 1
        }
        ip="$(printf '%s' "$sys_json" | sed -nE 's/.*"ip"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')"
        if [[ -z "$ip" ]]; then
            print_error "Could not parse system IP"
            return 1
        fi
    fi

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

# DNS leak test using dnscheck.tools (addr.tools)
# Now supports proxying via proxychains4 if a port is provided.
d6() {
    local port="$1"

    # Prerequisite checks
    if ! command -v python3 &>/dev/null; then
        print_error "python3 is required for DNS leak test"
        return 1
    fi
    if ! command -v dig &>/dev/null; then
        print_error "dig is required for DNS leak test"
        return 1
    fi

    # Run via proxy if port is provided
    if [[ -n "$port" ]]; then
        if ! command -v proxychains4 &>/dev/null; then
            print_error "proxychains4 not found. Please run 'brew install proxychains-ng' (it installs as proxychains4)"
            return 1
        fi

        # Create a temporary config file for proxychains
        local conf_file
        conf_file=$(mktemp) || {
            print_error "Failed to create temp file for proxychains config"
            return 1
        }
        # Ensure cleanup
        trap 'rm -f "$conf_file"' RETURN

        # Write proxy config
        {
            echo "strict_chain"
            echo "proxy_dns"
            echo "[ProxyList]"
            echo "http 127.0.0.1 $port"
        } > "$conf_file"

        print_info "Running DNS leak test via proxy on port $port..."
        proxychains4 -f "$conf_file" python3 "${SHELL_V11_DIR}/dns_leak.py"
    else
        # Run on system directly if no port
        print_info "Running DNS leak test on system..."
        python3 "${SHELL_V11_DIR}/dns_leak.py"
    fi
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

# File commands help (delegates to f module)
f6() {
    f --h
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

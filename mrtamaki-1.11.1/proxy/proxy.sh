# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Proxy Module (mt proxy)
# a1-a4 (IPRoyal/Oxylabs generate & speed run), b2 (proxy converter)
# ═══════════════════════════════════════════════════════════════════════════

PROXY_DIR="${0:A:h}"
MRTAMAKI_DIR="${PROXY_DIR:h}"
source "${MRTAMAKI_DIR}/utils.sh"

#--- IPRoyal URL generator ---
a1() {
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

    local city
    echo -n "Enter city: "
    read -r city
    [[ -z "$city" ]] && city="christchurch"

    local session
    session=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 8)
    local proxy_url="${user}:${pass}_country-${country}_city-${city}_session-${session}_lifetime-${lifetime}@${endpoint}"

    echo -n "$proxy_url" | copy_to_clipboard || print_warning "Failed to copy to clipboard"

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

#--- Oxylabs URL generator ---
a2() {
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

    local city
    echo -n "Enter city: "
    read -r city
    [[ -z "$city" ]] && city="auckland"

    local sessid
    sessid=$(LC_ALL=C tr -dc '0-9' < /dev/urandom | head -c 10)
    local proxy_url="customer-${user}-cc-${country}-city-${city}-sessid-${sessid}-sesstime-${sesstime}:${pass}@${endpoint}"

    echo -n "$proxy_url" | copy_to_clipboard || print_warning "Failed to copy to clipboard"

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

#--- IPRoyal speed run ---
a3() {
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

    local city
    echo -n "Enter city: "
    read -r city
    [[ -z "$city" ]] && city="auckland"

    local session
    session=$(LC_ALL=C tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 8)
    local proxy_url="${user}:${pass}_country-${country}_city-${city}_session-${session}_lifetime-${lifetime}@${endpoint}"

    echo -n "$proxy_url" | copy_to_clipboard || print_warning "Failed to copy to clipboard"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 IPRoyal Speed Run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   City:    $city"
    echo "   Session: $session"
    echo "   Port:    $rand_port"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local project_path="${PROXY_DIR}/proxy_converter"
    if [[ ! -f "${project_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${project_path}/proxy_converter.py"
        return 1
    fi

    _ensure_venv "$MRTAMAKI_DIR" || return 1

    print_info "Binding proxy..."
    "$VENV_PYTHON" "${project_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait &
    local proxy_pid=$!
    trap "kill $proxy_pid 2>/dev/null; trap - INT TERM; return 130" INT TERM

    sleep 3

    if ! kill -0 "$proxy_pid" 2>/dev/null; then
        trap - INT TERM
        print_error "Proxy converter failed to start"
        return 1
    fi

    local port
    port=$(pbpaste)

    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        print_error "Expected port number on clipboard, got: $port"
        kill "$proxy_pid" 2>/dev/null
        trap - INT TERM
        return 1
    fi

    print_info "Proxy bound on port $port"

    local http_proxy="127.0.0.1:${port}"

    c3 "$port"
    d4 "$(pbpaste)"

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

    wait "$proxy_pid" 2>/dev/null
    trap - INT TERM
}

#--- Oxylabs speed run ---
a4() {
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

    local city
    echo -n "Enter city: "
    read -r city
    [[ -z "$city" ]] && city="auckland"

    local sessid
    sessid=$(LC_ALL=C tr -dc '0-9' < /dev/urandom | head -c 10)
    local proxy_url="customer-${user}-cc-${country}-city-${city}-sessid-${sessid}-sesstime-${sesstime}:${pass}@${endpoint}"

    echo -n "$proxy_url" | copy_to_clipboard || print_warning "Failed to copy to clipboard"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Oxylabs Speed Run"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   City:    $city"
    echo "   Session: $sessid"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local project_path="${PROXY_DIR}/proxy_converter"
    if [[ ! -f "${project_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${project_path}/proxy_converter.py"
        return 1
    fi

    _ensure_venv "$MRTAMAKI_DIR" || return 1

    print_info "Binding proxy..."
    "$VENV_PYTHON" "${project_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait &
    local proxy_pid=$!
    trap "kill $proxy_pid 2>/dev/null; trap - INT TERM; return 130" INT TERM

    sleep 3

    if ! kill -0 "$proxy_pid" 2>/dev/null; then
        trap - INT TERM
        print_error "Proxy converter failed to start"
        return 1
    fi

    local port
    port=$(pbpaste)

    if ! [[ "$port" =~ ^[0-9]+$ ]]; then
        print_error "Expected port number on clipboard, got: $port"
        kill "$proxy_pid" 2>/dev/null
        trap - INT TERM
        return 1
    fi

    print_info "Proxy bound on port $port"

    local http_proxy="127.0.0.1:${port}"

    c3 "$port"
    d4 "$(pbpaste)"

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

    wait "$proxy_pid" 2>/dev/null
    trap - INT TERM
}

#--- Helpers ---
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

_b2_gen_and_bind() {
    local provider="$1"
    local count="$2"
    local city="$3"
    local project_path="$4"
    local debug_flag="${5:-}"
    local do_check="${6:-false}"

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

        "$VENV_PYTHON" -u "${project_path}/proxy_converter.py" --cli --bind "$proxy_url" --wait $debug_flag &> "$output_file" &
        local pid=$!
        bg_pids+=($pid)

        local port_val=""
        local retries=10
        while [[ $retries -gt 0 ]]; do
            port_val=$(grep -oE 'HTTP port [0-9]+' "$output_file" | cut -d' ' -f3)
            if [[ -n "$port_val" ]]; then
                break
            fi
            if ! kill -0 "$pid" 2>/dev/null; then
                print_error "[$i/$count] Proxy converter failed to start. Log:"
                cat "$output_file"
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

    for f in "${output_files[@]}"; do rm -f "$f"; done

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
        trap - INT TERM
        return 1
    fi

    typeset -ga _B2_BOUND_PORTS=("${bound_ports[@]}")

    if [[ "$do_check" == "true" && ${#_B2_BOUND_PORTS[@]} -gt 0 ]]; then
        _b2_batch_check
    fi
    unset _B2_BOUND_PORTS

    echo "   PIDs: ${bg_pids[*]}"
    echo "   Press Ctrl+C to stop all proxy servers"
    echo ""

    for pid in "${bg_pids[@]}"; do
        wait "$pid" 2>/dev/null
    done

    trap - INT TERM
}

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

        if [[ $idx -lt $total ]]; then
            echo ""
            echo "───────────────────────────────────────────────────"
            echo ""
        fi
    done

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Batch Check Complete — $passed passed, $failed failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

#--- Proxy converter (b2) ---
b2() {
    local project_path="${PROXY_DIR}/proxy_converter"
    local module_name="proxy"

    if [[ ! -d "$project_path" ]]; then
        print_error "Proxy converter not found: $project_path"
        return 1
    fi

    if [[ ! -f "${project_path}/proxy_converter.py" ]]; then
        print_error "proxy_converter.py not found: ${project_path}/proxy_converter.py"
        return 1
    fi

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
                if [[ -n "$2" && "$2" =~ ^[0-9]+$ ]]; then
                    gen_count="$2"
                    shift
                fi
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

    if [[ "$flag" == "clean" ]]; then
        if [[ -f "$HOME/.bindproxy.json" ]]; then
            rm -f "$HOME/.bindproxy.json" && print_success "Removed ~/.bindproxy.json"
        else
            print_info "No ~/.bindproxy.json found"
        fi
        return 0
    fi

    _ensure_venv "$MRTAMAKI_DIR" || return 1

    local exit_code=0

    if [[ "$flag" == "gen_a1" ]]; then
        _b2_gen_and_bind "a1" "$gen_count" "$gen_city" "$project_path" "$debug_flag" "$do_check"
        exit_code=$?

    elif [[ "$flag" == "gen_a2" ]]; then
        _b2_gen_and_bind "a2" "$gen_count" "$gen_city" "$project_path" "$debug_flag" "$do_check"
        exit_code=$?

    elif [[ "$flag" == "bind" ]]; then
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
        print_info "Launching proxy converter..."
        "$VENV_PYTHON" "${project_path}/proxy_converter.py" $debug_flag
        exit_code=$?
    fi

    if $do_check && [[ "$flag" != "gen_a1" && "$flag" != "gen_a2" ]]; then
        print_warning "--check requires --a1 or --a2 (batch gen)"
    fi

    if [[ "$flag" == "gen_a1" || "$flag" == "gen_a2" ]]; then
        return $exit_code
    fi

    if [[ $exit_code -ne 0 ]]; then
        print_warning "Proxy converter exited with code: $exit_code"
    fi

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

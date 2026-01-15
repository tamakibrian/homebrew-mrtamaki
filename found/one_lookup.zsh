#!/usr/bin/env zsh
# ═══════════════════════════════════════════════════════════════════════════
# 1lookup API Integration Module
# Thin Zsh wrappers for Python-based 1lookup API calls
# ═══════════════════════════════════════════════════════════════════════════

# Guard against double-sourcing
[[ -n "$_ONELOOKUP_MODULE_LOADED" ]] && return 0
_ONELOOKUP_MODULE_LOADED=1

# Module configuration
ONELOOKUP_MODULE_DIR="${HOME}/.shell-v1.1"
ONELOOKUP_PYTHON_PKG="${ONELOOKUP_MODULE_DIR}/py"
ONELOOKUP_VENV="${ONELOOKUP_MODULE_DIR}/.venv-one-lookup"
# Aliases for functions below
alias d4.1='iplookup'
alias d4.2='everify'
alias d4.3='eappend'
alias d4.4='reappend'
alias d4.5='ripappend'

# "found --help" command (can't use alias with space, so use a function)
found() {
    case "$1" in
        --help|-h|help) onelookup_help ;;
        *) onelookup_help ;;
    esac
}
# ─────────────────────────────────────────────────────────────────────────────
# Helper: Ensure Python environment is ready
# ─────────────────────────────────────────────────────────────────────────────
_onelookup_ensure_python() {
    # Check if venv exists and use it
    if [[ -d "$ONELOOKUP_VENV" ]]; then
        if [[ -z "$VIRTUAL_ENV" ]] || [[ "$VIRTUAL_ENV" != "$ONELOOKUP_VENV" ]]; then
            source "${ONELOOKUP_VENV}/bin/activate" 2>/dev/null
        fi
    fi
    
    # Verify Python and required packages
    if ! command -v python3 &>/dev/null; then
        print_error "Python 3 not found. Please install Python 3."
        return 1
    fi
    
    # Check for required modules (quick check, not exhaustive)
    if ! python3 -c "import rich, requests" 2>/dev/null; then
        print_error "Required Python packages not found."
        print_info "Install with: pip install rich requests"
        return 1
    fi
    
    return 0
}

# ─────────────────────────────────────────────────────────────────────────────
# Helper: Execute Python CLI
# ─────────────────────────────────────────────────────────────────────────────
_onelookup_exec() {
    _onelookup_ensure_python || return $?
    
    # Add py directory to PYTHONPATH and execute
    PYTHONPATH="${ONELOOKUP_PYTHON_PKG}:${PYTHONPATH}" \
        python3 -m one_lookup.cli "$@"
    
    return $?
}

# ─────────────────────────────────────────────────────────────────────────────
# IP Lookup: Get information about an IP address
# Usage: iplookup <ip> [--raw] [--no-summary] [--timeout N]
# ─────────────────────────────────────────────────────────────────────────────
iplookup() {
    if [[ $# -eq 0 ]]; then
        print_error "Missing IP address"
        print_info "Usage: iplookup <ip> [--raw] [--no-summary] [--timeout N]"
        print_info "Example: iplookup 8.8.8.8"
        return 2
    fi
    
    local ip="$1"
    shift
    
    # Basic IP validation (very lenient, let API do full validation)
    if [[ ! "$ip" =~ ^[0-9.:a-fA-F]+$ ]]; then
        print_error "Invalid IP address format: $ip"
        return 2
    fi
    
    print_info "Looking up IP: $ip"
    _onelookup_exec ip "$ip" "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# Email Verification: Verify an email address
# Usage: everify <email> [--raw] [--no-summary] [--timeout N]
# ─────────────────────────────────────────────────────────────────────────────
everify() {
    if [[ $# -eq 0 ]]; then
        print_error "Missing email address"
        print_info "Usage: everify <email> [--raw] [--no-summary] [--timeout N]"
        print_info "Example: everify user@example.com"
        return 2
    fi
    
    local email="$1"
    shift
    
    # Basic email validation
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        print_error "Invalid email format: $email"
        return 2
    fi
    
    print_info "Verifying email: $email"
    _onelookup_exec email "$email" "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# Email Append: Find email from personal information
# Usage: eappend --first NAME --last NAME [--address ADDR] --city CITY --zip ZIP [flags]
# ─────────────────────────────────────────────────────────────────────────────
eappend() {
    if [[ $# -eq 0 ]]; then
        print_error "Missing required arguments"
        print_info "Usage: eappend --first FIRST --last LAST [--address ADDR] --city CITY --zip ZIP"
        print_info "Example: eappend --first John --last Doe --city Boston --zip 02101"
        return 2
    fi
    
    # Parse arguments
    local first="" last="" address="" city="" zip=""
    local -a extra_args
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --first)
                first="$2"
                shift 2
                ;;
            --last)
                last="$2"
                shift 2
                ;;
            --address)
                address="$2"
                shift 2
                ;;
            --city)
                city="$2"
                shift 2
                ;;
            --zip)
                zip="$2"
                shift 2
                ;;
            --raw|--no-summary|--timeout)
                extra_args+=("$1")
                if [[ "$1" == "--timeout" ]]; then
                    extra_args+=("$2")
                    shift
                fi
                shift
                ;;
            *)
                print_error "Unknown argument: $1"
                return 2
                ;;
        esac
    done
    
    # Validate required fields
    if [[ -z "$first" || -z "$last" || -z "$city" || -z "$zip" ]]; then
        print_error "Missing required fields: --first, --last, --city, and --zip are required"
        return 2
    fi
    
    print_info "Looking up email for: $first $last in $city, $zip"
    _onelookup_exec email-append \
        --first "$first" \
        --last "$last" \
        ${address:+--address "$address"} \
        --city "$city" \
        --zip "$zip" \
        "${extra_args[@]}"
}

# ─────────────────────────────────────────────────────────────────────────────
# Reverse Email Append: Find person details from email
# Usage: reappend <email> [--raw] [--no-summary] [--timeout N]
# ─────────────────────────────────────────────────────────────────────────────
reappend() {
    if [[ $# -eq 0 ]]; then
        print_error "Missing email address"
        print_info "Usage: reappend <email> [--raw] [--no-summary] [--timeout N]"
        print_info "Example: reappend user@example.com"
        return 2
    fi
    
    local email="$1"
    shift
    
    # Basic email validation
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        print_error "Invalid email format: $email"
        return 2
    fi
    
    print_info "Looking up details for: $email"
    _onelookup_exec reverse-email "$email" "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# Reverse IP Append: Find details from IP address
# Usage: ripappend <ip> [--raw] [--no-summary] [--timeout N]
# ─────────────────────────────────────────────────────────────────────────────
ripappend() {
    if [[ $# -eq 0 ]]; then
        print_error "Missing IP address"
        print_info "Usage: ripappend <ip> [--raw] [--no-summary] [--timeout N]"
        print_info "Example: ripappend 1.2.3.4"
        return 2
    fi
    
    local ip="$1"
    shift
    
    # Basic IP validation
    if [[ ! "$ip" =~ ^[0-9.:a-fA-F]+$ ]]; then
        print_error "Invalid IP address format: $ip"
        return 2
    fi
    
    print_info "Looking up details for IP: $ip"
    _onelookup_exec reverse-ip "$ip" "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# Help: Display usage information for all commands
# ─────────────────────────────────────────────────────────────────────────────
onelookup_help() {
    print_header "1lookup API Commands"
    
    echo "${COLOR_INFO}IP Lookup:${COLOR_RESET}"
    echo "  iplookup <ip> [flags]"
    echo "  Example: iplookup 8.8.8.8"
    echo ""
    
    echo "${COLOR_INFO}Email Verification:${COLOR_RESET}"
    echo "  everify <email> [flags]"
    echo "  Example: everify user@example.com"
    echo ""
    
    echo "${COLOR_INFO}Email Append (find email from info):${COLOR_RESET}"
    echo "  eappend --first FIRST --last LAST [--address ADDR] --city CITY --zip ZIP [flags]"
    echo "  Example: eappend --first John --last Doe --city Boston --zip 02101"
    echo ""
    
    echo "${COLOR_INFO}Reverse Email Append (find person from email):${COLOR_RESET}"
    echo "  reappend <email> [flags]"
    echo "  Example: reappend contact@company.com"
    echo ""
    
    echo "${COLOR_INFO}Reverse IP Append (find details from IP):${COLOR_RESET}"
    echo "  ripappend <ip> [flags]"
    echo "  Example: ripappend 1.2.3.4"
    echo ""
    
    echo "${COLOR_INFO}Available flags:${COLOR_RESET}"
    echo "  --raw          Output raw JSON (for piping)"
    echo "  --no-summary   Skip summary table, show only full JSON"
    echo "  --timeout N    Set request timeout in seconds (default: 10)"
    echo ""
    
    echo "${COLOR_WARNING}Configuration:${COLOR_RESET}"
    echo "  Set ONELOOKUP_API_KEY environment variable"
    echo "  Or create ~/.shell-v1.1/one_lookup.toml"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Module loaded confirmation
# ─────────────────────────────────────────────────────────────────────────────
# Uncomment for debugging:
# print_success "1lookup module loaded"

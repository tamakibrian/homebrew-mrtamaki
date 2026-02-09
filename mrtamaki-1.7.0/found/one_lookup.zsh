#!/usr/bin/env zsh
# ═══════════════════════════════════════════════════════════════════════════
# 1lookup API Integration Module
# Thin Zsh wrappers for Python-based 1lookup API calls
# ═══════════════════════════════════════════════════════════════════════════

# Guard against double-sourcing
[[ -n "$_ONELOOKUP_MODULE_LOADED" ]] && return 0
_ONELOOKUP_MODULE_LOADED=1

# Module configuration - use script's directory (set by zsh)
ONELOOKUP_MODULE_DIR="${0:A:h}"
ONELOOKUP_PARENT_DIR="${ONELOOKUP_MODULE_DIR:h}"
ONELOOKUP_PYTHON_PKG="${ONELOOKUP_MODULE_DIR}"

# Source shared utilities for _ensure_module_venv
source "${ONELOOKUP_PARENT_DIR}/utils.sh"
# Aliases for functions below
alias d4.1='iplookup'
alias d4.2='everify'
alias d4.3='eappend'
alias d4.4='reappend'
alias d4.5='ripappend'
alias d5='onelookup'

# Launch interactive menu
onelookup() {
    _onelookup_exec menu
}
alias 1l='onelookup'

# "found" command - launches menu, or shows help with --help flag
found() {
    case "$1" in
        --help|-h|help) onelookup_help ;;
        *) onelookup ;;
    esac
}
# ─────────────────────────────────────────────────────────────────────────────
# Helper: Execute Python CLI using venv
# ─────────────────────────────────────────────────────────────────────────────
_onelookup_exec() {
    # Ensure venv exists (lazy creation if missing)
    _ensure_module_venv found "$ONELOOKUP_PARENT_DIR" || return 1

    # Execute using venv Python with correct PYTHONPATH
    PYTHONPATH="${ONELOOKUP_PYTHON_PKG}:${PYTHONPATH}" \
        "$VENV_PYTHON" -m one_lookup.cli "$@"

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
# Email Append: Find email from person info
# Usage: eappend <first> <last> <city> <zip> [--address "addr"]
# ─────────────────────────────────────────────────────────────────────────────
eappend() {
    if [[ $# -lt 4 ]]; then
        print_error "Missing required arguments"
        print_info "Usage: eappend <first_name> <last_name> <city> <zip> [--address \"addr\"]"
        print_info "Example: eappend John Doe Austin 78701"
        return 2
    fi

    print_info "Looking up email for: $1 $2, $3 $4"
    _onelookup_exec eappend "$@"
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

    print_info "Reverse lookup for: $email"
    _onelookup_exec reappend "$email" "$@"
}

# ─────────────────────────────────────────────────────────────────────────────
# Reverse IP Append: Enhanced IP lookup
# Usage: ripappend <ip> [--raw] [--no-summary] [--timeout N]
# ─────────────────────────────────────────────────────────────────────────────
ripappend() {
    if [[ $# -eq 0 ]]; then
        print_error "Missing IP address"
        print_info "Usage: ripappend <ip> [--raw] [--no-summary] [--timeout N]"
        print_info "Example: ripappend 8.8.8.8"
        return 2
    fi

    local ip="$1"
    shift

    # Basic IP validation
    if [[ ! "$ip" =~ ^[0-9.:a-fA-F]+$ ]]; then
        print_error "Invalid IP address format: $ip"
        return 2
    fi

    print_info "Reverse IP lookup for: $ip"
    _onelookup_exec ripappend "$ip" "$@"
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

    echo "${COLOR_INFO}Email Append (find email from person):${COLOR_RESET}"
    echo "  eappend <first> <last> <city> <zip> [--address \"addr\"]"
    echo "  Example: eappend John Doe Austin 78701"
    echo ""

    echo "${COLOR_INFO}Reverse Email Append (find person from email):${COLOR_RESET}"
    echo "  reappend <email> [flags]"
    echo "  Example: reappend user@example.com"
    echo ""

    echo "${COLOR_INFO}Reverse IP Append (enhanced IP lookup):${COLOR_RESET}"
    echo "  ripappend <ip> [flags]"
    echo "  Example: ripappend 8.8.8.8"
    echo ""

    echo "${COLOR_INFO}Interactive Menu:${COLOR_RESET}"
    echo "  onelookup  or  1l"
    echo ""

    echo "${COLOR_INFO}Available flags:${COLOR_RESET}"
    echo "  --raw          Output raw JSON (for piping)"
    echo "  --no-summary   Skip summary table, show only full JSON"
    echo "  --timeout N    Set request timeout in seconds (default: 10)"
    echo ""

    echo "${COLOR_WARNING}Configuration:${COLOR_RESET}"
    echo "  Set ONELOOKUP_API_KEY in ~/.zshenv"
    echo ""
}

# ─────────────────────────────────────────────────────────────────────────────
# Module loaded confirmation
# ─────────────────────────────────────────────────────────────────────────────
# Uncomment for debugging:
# print_success "1lookup module loaded"

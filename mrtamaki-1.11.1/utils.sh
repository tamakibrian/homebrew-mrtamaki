# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Shared Utilities
# Common functions used across all modules
# ═══════════════════════════════════════════════════════════════════════════

# Guard against double-sourcing
[[ -n "$_SHELL_V11_UTILS_LOADED" ]] && return 0
_SHELL_V11_UTILS_LOADED=1

#--- CONFIGURATION CONSTANTS ---
readonly MAX_FILE_SIZE="100M"          # Maximum file size for fe() function
readonly PORT_MIN=1                     # Minimum valid port number
readonly PORT_MAX=64900                 # Maximum valid port number
readonly VENV_SEARCH_DEPTH=5            # Maximum depth for venv search
readonly NETWORK_TIMEOUT=10             # Timeout for network operations (seconds)
readonly SESSION_ID_LENGTH=8            # Length of session IDs (7 letters + 1 digit)

#--- UI & HANDLERS ---
autoload -U colors && colors

# Color definitions for consistent UI
readonly COLOR_SUCCESS='\033[0;32m'
readonly COLOR_ERROR='\033[0;31m'
readonly COLOR_WARNING='\033[0;33m'
readonly COLOR_INFO='\033[0;34m'
readonly COLOR_PROMPT='\033[0;36m'
readonly COLOR_RESET='\033[0m'

# UI Elements
readonly ICON_SUCCESS="✓"
readonly ICON_ERROR="✗"
readonly ICON_WARNING="⚠"
readonly ICON_INFO="ℹ"
readonly ICON_ROCKET="🚀"
readonly ICON_FOLDER="📁"

# 🛠️ UTILITY FUNCTIONS
# Enhanced print functions with consistent formatting
print_success() { echo "${COLOR_SUCCESS}${ICON_SUCCESS} $@${COLOR_RESET}"; }
print_error() { echo "${COLOR_ERROR}${ICON_ERROR} $@${COLOR_RESET}" >&2; }
print_warning() { echo "${COLOR_WARNING}${ICON_WARNING} $@${COLOR_RESET}"; }
print_info() { echo "${COLOR_INFO}${ICON_INFO} $@${COLOR_RESET}"; }
print_header() { echo "\n${COLOR_INFO}═══ $@ ═══${COLOR_RESET}\n"; }

# Confirmation prompt with error handling
confirm() {
    local prompt="${1:-Continue?}"
    local default="${2:-N}"

    while true; do
        echo -n "${COLOR_PROMPT}${prompt} [Y/N] (default: ${default}): ${COLOR_RESET}"
        read -r response
        response="${response:-$default}"

        case "${response:u}" in
            Y|YES) return 0 ;;
            N|NO) return 1 ;;
            *) print_warning "Please answer Y or N" ;;
        esac
    done
}

# Cross-platform clipboard copy (cached for performance)
_CLIPBOARD_CMD=""
copy_to_clipboard() {
    # Cache clipboard command on first run
    if [[ -z "$_CLIPBOARD_CMD" ]]; then
        if command -v pbcopy &>/dev/null; then
            _CLIPBOARD_CMD="pbcopy"
        elif command -v xclip &>/dev/null; then
            _CLIPBOARD_CMD="xclip -selection clipboard"
        elif command -v xsel &>/dev/null; then
            _CLIPBOARD_CMD="xsel --clipboard --input"
        else
            print_error "No clipboard utility found (pbcopy, xclip, or xsel)"
            return 1
        fi
    fi

    # Use ${=...} for word splitting instead of eval (safer)
    ${=_CLIPBOARD_CMD}
}

# Progress spinner with timeout (30 seconds max)
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local elapsed=0
    local max_time=30

    while ps -p "$pid" &>/dev/null; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep "$delay"
        printf "\b\b\b\b\b\b"

        elapsed=$((elapsed + 1))
        if [[ $elapsed -gt $((max_time * 10)) ]]; then
            print_warning "Operation timed out after ${max_time}s"
            return 1
        fi
    done
    printf "    \b\b\b\b"
}

# Centralized venv handler with lazy creation
# Usage: _ensure_venv [base_dir]
# Sets VENV_PYTHON variable for caller to use
# Union of all module dependencies: banner, files, found, status, proxy, clean, mcp
_ensure_venv() {
    local base_dir="${1:-$SHELL_V11_DIR}"
    local venv_path="${base_dir}/venv"

    # Union of all module packages (pinned to compatible ranges)
    local packages="rich>=13 readchar>=4 requests>=2 InquirerPy>=0.3 psutil>=5 PySocks>=1.7 dnspython>=2 mcp"

    # Create venv if missing (with lock to prevent concurrent creation)
    if [[ ! -d "$venv_path" ]]; then
        local lock_dir="${venv_path}.creating"

        # Atomic lock via mkdir
        if ! mkdir "$lock_dir" 2>/dev/null; then
            # Another process is creating this venv -- wait for it
            print_info "Waiting for venv creation..."
            local wait_count=0
            while [[ -d "$lock_dir" ]] && [[ $wait_count -lt 30 ]]; do
                sleep 2
                ((wait_count++))
            done
            # If lock is stale (>60s), remove it and retry
            if [[ -d "$lock_dir" ]]; then
                rmdir "$lock_dir" 2>/dev/null
            fi
        fi

        # Double-check after acquiring lock (another process may have finished)
        if [[ ! -d "$venv_path" ]]; then
            print_info "Creating venv environment..."
            python3 -m venv "$venv_path" 2>/dev/null || {
                rmdir "$lock_dir" 2>/dev/null
                print_error "Failed to create virtual environment"
                return 1
            }

            # Install packages
            print_info "Installing dependencies..."
            "${venv_path}/bin/pip" install --upgrade pip >/dev/null 2>&1
            "${venv_path}/bin/pip" install ${=packages} >/dev/null 2>&1 || {
                rmdir "$lock_dir" 2>/dev/null
                print_error "Failed to install dependencies"
                return 1
            }
            print_success "venv ready"
        fi

        # Release lock
        rmdir "$lock_dir" 2>/dev/null
    fi

    # Set VENV_PYTHON for caller
    typeset -g VENV_PYTHON="${venv_path}/bin/python3"

    # Verify Python executable exists
    if [[ ! -x "$VENV_PYTHON" ]]; then
        print_error "Python not found in venv: $VENV_PYTHON"
        return 1
    fi

    return 0
}

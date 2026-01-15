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
readonly SESSION_ID_LENGTH=10           # Length of session IDs

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

    eval "$_CLIPBOARD_CMD"
}

# Progress spinner with timeout (30 seconds max)
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local elapsed=0
    local max_time=30

    while ps -p "$pid" > /dev/null 2>&1; do
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

# Universal venv handler with error checking
_ensure_venv() {
    local venv_path="${1:-venv}"

    if [[ ! -d "$venv_path" ]]; then
        print_info "Creating virtual environment..."
        python3 -m venv "$venv_path" || {
            print_error "Failed to create virtual environment"
            return 1
        }
    fi

    source "$venv_path/bin/activate" || {
        print_error "Failed to activate virtual environment"
        return 1
    }

    if [[ -f requirements.txt ]]; then
        print_info "Installing/updating dependencies..."
        pip install --upgrade pip || {
            print_warning "Failed to upgrade pip"
        }
        pip install -r requirements.txt || {
            print_warning "Some dependencies failed to install"
        }
    fi

    return 0
}

# PURGE - Improved cleanup with better error handling
_cleanup_venv() {
    local venv_path="${1:-venv}"

    if [[ ! -d "$venv_path" ]]; then
        return 0
    fi

    if ! confirm "Delete virtual environment ($venv_path)?" "N"; then
        print_info "Virtual environment preserved"
        return 0
    fi

    # Use pip from venv directly (no need to activate)
    if [[ -f "$venv_path/bin/pip" ]]; then
        print_info "Clearing pip cache..."
        "$venv_path/bin/pip" cache purge >/dev/null 2>&1

        print_info "Purging all packages inside the virtual environment..."
        "$venv_path/bin/pip" freeze | xargs -r "$venv_path/bin/pip" uninstall -y >/dev/null 2>&1
    fi

    print_info "Removing virtual environment directory..."
    rm -rf "$venv_path" || {
        print_error "Failed to remove virtual environment"
        return 1
    }

    print_success "Virtual environment fully purged and deleted"
    return 0
}

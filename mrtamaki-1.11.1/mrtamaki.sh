# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Zsh Toolkit
# Source this file from ~/.zshrc:
#   source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
# ═══════════════════════════════════════════════════════════════════════════

#--- VERSION ---
MRTAMAKI_VERSION="1.11.1"

#--- HOMEBREW PREFIX ---
HOMEBREW_PREFIX="${HOMEBREW_PREFIX:-$(brew --prefix)}"

#--- INIT ---
SHELL_V11_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"
 
#--- BANNER ---
# Set MRTAMAKI_NO_BANNER=1 in ~/.zshenv to skip the startup animation
if [[ -o interactive ]] && [[ -z "$MRTAMAKI_NO_BANNER" ]]; then
    if [[ -f "${SHELL_V11_DIR}/banner.py" ]]; then
        if _ensure_venv "$SHELL_V11_DIR" 2>/dev/null; then
            "$VENV_PYTHON" "${SHELL_V11_DIR}/banner.py" 2>/dev/null
        fi
    fi
fi
#--- THEME TOGGLE ---
# Theme list for tt() cycling
typeset -ga MRTAMAKI_THEMES=(
    "light-zsh/light-zsh"
    "powerlevel10k/powerlevel10k"
    "robbyrussell"
    "agnoster"
    "af-magic"
    "half-life"
)

# Read saved theme index from state file (default: 0 = light-zsh)
_mrtamaki_theme_idx=0
if [[ -f "$HOME/.mrtamaki_theme" ]]; then
    _mrtamaki_theme_idx=$(<"$HOME/.mrtamaki_theme")
    if ! [[ "$_mrtamaki_theme_idx" =~ ^[0-9]+$ ]] || (( _mrtamaki_theme_idx < 0 || _mrtamaki_theme_idx >= ${#MRTAMAKI_THEMES[@]} )); then
        _mrtamaki_theme_idx=0
    fi
fi
ZSH_THEME="${MRTAMAKI_THEMES[$((_mrtamaki_theme_idx + 1))]}"

# Ensure p10k is available as an OMZ custom theme
if [[ ! -e "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" ]] && \
   [[ -d "${HOMEBREW_PREFIX}/opt/powerlevel10k/share/powerlevel10k" ]]; then
    ln -sfn "${HOMEBREW_PREFIX}/opt/powerlevel10k/share/powerlevel10k" \
        "$HOME/.oh-my-zsh/custom/themes/powerlevel10k"
fi

# Source Oh My Zsh (applies ZSH_THEME)
export ZSH="$HOME/.oh-my-zsh"
if [[ -f "$ZSH/oh-my-zsh.sh" ]]; then
    source "$ZSH/oh-my-zsh.sh"
fi

# Source p10k config when using powerlevel10k theme
if [[ "$ZSH_THEME" == "powerlevel10k/powerlevel10k" ]] && [[ -f "$HOME/.p10k.zsh" ]]; then
    source "$HOME/.p10k.zsh"
fi

# Toggle theme: cycles through MRTAMAKI_THEMES and restarts shell
tt() {
    local state_file="$HOME/.mrtamaki_theme"
    local total=${#MRTAMAKI_THEMES[@]}
    local next

    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  tt - Theme Toggle"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "  Usage: tt [--N]"
        echo ""
        echo "  tt          Cycle to next theme"
        local i
        for i in {1..$total}; do
            echo "  tt --${i}      ${MRTAMAKI_THEMES[$i]}"
        done
        echo ""
        return 0
    fi

    if [[ -n "$1" ]]; then
        if [[ "$1" =~ ^--([0-9]+)$ ]]; then
            local pick=${match[1]}
            if (( pick < 1 || pick > total )); then
                echo "tt: invalid theme number --${pick} (choose 1-${total})"
                return 1
            fi
            next=$(( pick - 1 ))
        else
            echo "tt: unknown option '$1' (try tt --help)"
            return 1
        fi
    else
        local current=0
        if [[ -f "$state_file" ]]; then
            current=$(<"$state_file")
            [[ "$current" =~ ^[0-9]+$ ]] || current=0
        fi
        next=$(( (current + 1) % total ))
    fi

    local theme_name="${MRTAMAKI_THEMES[$((next + 1))]}"
    echo "$next" > "$state_file"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Theme: ${theme_name}"
    echo "  ($((next + 1))/${total})"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    exec zsh
}

#--- MODULE LOADING ---
# Source modules (aligned with mt: proxy, ip, sys, lookup, file)
export MRTAMAKI_DIR="$SHELL_V11_DIR"
source "${SHELL_V11_DIR}/ip/ip.sh"           # c3, d4, d6 (IP tools)
source "${SHELL_V11_DIR}/proxy/proxy.sh"     # a1-a4, b2 (proxy)
source "${SHELL_V11_DIR}/sys/sys.sh"         # h1-h10, smenu, h9, e5, g7, f6, health
source "${SHELL_V11_DIR}/lookup/one_lookup.zsh" # d5, found, iplookup, everify, etc.
source "${SHELL_V11_DIR}/file/f.sh"          # f command (file operations)

#--- ALIASES ---
alias cc='clear'

#--- MT (Centralised Command) ---
_mt_proxy_help() {
    echo "  mt proxy <action>"
    echo "    iproyal        Generate IPRoyal proxy URL"
    echo "    oxylabs        Generate Oxylabs proxy URL"
    echo "    iproyal-speed  IPRoyal speed run"
    echo "    oxylabs-speed  Oxylabs speed run"
    echo "    convert        Proxy converter (b2)"
}

_mt_sys_help() {
    echo "  mt sys <action>"
    echo "    pycache      Clean __pycache__ directories"
    echo "    browser      Clear browser caches"
    echo "    app          Clear app caches"
    echo "    venv         Clean virtual environments"
    echo "    space        Reclaimable space overview"
    echo "    xcode        Clear Xcode DerivedData"
    echo "    node         Clean node_modules"
    echo "    menu         System cleaner TUI"
    echo "    health       Live system health dashboard"
    echo "    dns          Flush DNS cache"
    echo "    venv-purge   Find and purge venvs"
    echo "    pip          Pip purge"
}

_mt_ip_help() {
    echo "  mt ip <action> [args]"
    echo "    test [port]   Test proxy / check system IP"
    echo "    check [ip]   Scamalytics IP reputation"
    echo "    dnsleak [port] DNS leak test"
}

mt() {
    local module="$1"
    local action="$2"
    shift 2 2>/dev/null || true

    # No args or global flags: show help
    if [[ -z "$module" ]]; then
        mrtamaki
        return 0
    fi
    if [[ "$module" == -h || "$module" == --help ]]; then
        mrtamaki
        return 0
    fi
    if [[ "$module" == --version ]]; then
        echo "mrtamaki v${MRTAMAKI_VERSION}"
        return 0
    fi

    # Module dispatch
    case "$module" in
        proxy)
            case "$action" in
                iproyal) a1 ;;
                oxylabs) a2 ;;
                iproyal-speed) a3 ;;
                oxylabs-speed) a4 ;;
                convert) b2 "$@" ;;
                '') print_error "mt proxy requires an action"; _mt_proxy_help; return 1 ;;
                *) print_error "Unknown action: $action"; _mt_proxy_help; return 1 ;;
            esac ;;
        sys)
            case "$action" in
                pycache) h1 ;;
                browser) h2 ;;
                app) h3 ;;
                venv) h4 ;;
                space) h5 ;;
                xcode) h6 ;;
                node) h7 ;;
                menu) smenu ;;
                health) h9 ;;
                dns) h10 ;;
                venv-purge) e5 "$@" ;;
                pip) g7 "$@" ;;
                '') print_error "mt sys requires an action"; _mt_sys_help; return 1 ;;
                *) print_error "Unknown action: $action"; _mt_sys_help; return 1 ;;
            esac ;;
        ip)
            case "$action" in
                test) c3 "$@" ;;
                check) d4 "$@" ;;
                dnsleak) d6 "$@" ;;
                '') print_error "mt ip requires an action"; _mt_ip_help; return 1 ;;
                *) print_error "Unknown action: $action"; _mt_ip_help; return 1 ;;
            esac ;;
        lookup)
            case "$action" in
                '') onelookup ;;
                ip) iplookup "$@" ;;
                email) everify "$@" ;;
                eappend) eappend "$@" ;;
                reappend) reappend "$@" ;;
                ripappend) ripappend "$@" ;;
                *) onelookup "$action" "$@" ;;
            esac ;;
        file)
            if [[ -z "$action" ]]; then
                f --h
            else
                f "$action" "$@"
            fi ;;
        theme)
            tt "$action" "$@" ;;
        *)
            # Legacy fallback: module is a function (a1, b2, h1, etc.)
            if typeset -f "$module" &>/dev/null; then
                "$module" "$action" "$@"
            else
                print_error "Unknown module: $module"
                print_info "Run 'mt' or 'mrtamaki' for help"
                return 1
            fi ;;
    esac
}

#--- HELP ---
mrtamaki() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  mrtamaki v${MRTAMAKI_VERSION} - Zsh Toolkit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  MT — Centralised command (mt <module> <action>)"
    echo "    mt proxy oxylabs    Generate Oxylabs proxy"
    echo "    mt proxy iproyal    Generate IPRoyal proxy"
    echo "    mt sys pycache      Clean __pycache__"
    echo "    mt sys menu         System cleaner TUI"
    echo "    mt sys health       Health dashboard"
    echo "    mt ip test [port]   Test proxy"
    echo "    mt lookup           1Lookup menu"
    echo "    mt file --tr        File operations (f --h for all)"
    echo "    mt theme            Cycle theme"
    echo "    Run 'mt proxy', 'mt sys', 'mt ip' for module help"
    echo ""
    echo "  Shortcuts (a1, b2, h1, etc.) still work"
    echo ""
    echo "  PROXY & IP TOOLS"
    echo "    a1              Generate IPRoyal proxy URL"
    echo "    a2              Generate Oxylabs proxy URL"
    echo "    a3              Speed run: IPRoyal → bind → test → check"
    echo "    a4              Speed run: Oxylabs → bind → test → check"
    echo "    b2 [flags]      Proxy converter (run b2 --help for flags)"
    echo "    c3 [port]       Test proxy on port / check system IP"
    echo "    d4 [ip]         Scamalytics IP reputation check (auto-detects IP)"
    echo "    d6              DNS leak test via dnscheck.tools"
    echo ""
    echo "  SYSTEM"
    echo "    e5 [path]       Find and clean up virtual environments"
    echo "    f6              Show file operations help"
    echo "    g7 [venv]       Pip purge (cache + packages, default: system)"
    echo "    h1              Clean __pycache__ directories"
    echo "    h2              Clear browser caches"
    echo "    h3              Clear app caches"
    echo "    h4              Clean virtual environments"
    echo "    h5              Reclaimable space overview"
    echo "    h6              Clear Xcode DerivedData"
    echo "    h7              Clean node_modules"
    echo "    h8 / smenu      System cleaner (full TUI menu)"
    echo "    h9 / health     Live system health dashboard (CPU, RAM, disk, net)"
    echo "    h10 / flushdns  Flush DNS cache (macOS)"
    echo ""
    echo "  FILE COMMANDS"
    echo "    f --h           Show all file operations"
    echo ""
    echo "  1LOOKUP API"
    echo "    d5 / found      Interactive 1lookup menu"
    echo "    iplookup <ip>   IP address lookup"
    echo "    everify <email> Email verification"
    echo "    eappend         Find email from personal info"
    echo "    reappend <email> Reverse email lookup"
    echo "    ripappend <ip>  Reverse IP lookup"
    echo "    found --help    Show 1lookup detailed help"
    echo ""
    echo "  THEME"
    echo "    tt              Toggle Zsh theme (cycles through ${#MRTAMAKI_THEMES[@]} themes)"
    echo "    tt --N          Jump to theme N (e.g. tt --1 for light-zsh, tt --help for list)"
    echo ""
    echo "  ALIASES"
    echo "    cc              Clear screen"
    echo "    ll              List files (long format)"
    echo "    la              List all files (including hidden)"
    echo ""
    echo "  CREDENTIALS (add to ~/.zshenv)"
    echo "    export IPROYAL_USER='username'        # for a1"
    echo "    export IPROYAL_PASS='password'        # for a1"
    echo "    export OXYLABS_USER='customer_id'     # for a2"
    echo "    export OXYLABS_PASS='password'        # for a2"
    echo "    export SCAMALYTICS_API_KEY='key'      # for d4"
    echo "    export ONELOOKUP_API_KEY='key'        # for 1lookup commands"
    echo ""
    echo "  RUNTIME DEPENDENCIES"
    echo "    jq              Required for some IP checks (d4). Install: brew install jq"
    echo "    proxychains4    Required for proxy DNS leak test (c3). Install: brew install proxychains-ng"
    echo ""
    echo "  UPDATE"
    echo "    brew update && brew reinstall --cask mrtamaki && exec zsh"
    echo ""
    echo "  UNINSTALL"
    echo "    brew uninstall --cask mrtamaki && brew untap tamakibrian/mrtamaki"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}
 
#--- SYNTAX HIGHLIGHTING & AUTOSUGGESTIONS ---
# Syntax highlighting (must be sourced after all other plugins)
[[ -f "${HOMEBREW_PREFIX}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] && \
    source "${HOMEBREW_PREFIX}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
 
# Autosuggestions (fish-like suggestions based on history)
[[ -f "${HOMEBREW_PREFIX}/share/zsh-autosuggestions/zsh-autosuggestions.zsh" ]] && \
    source "${HOMEBREW_PREFIX}/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
# Autosuggestion settings
ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=#666666"
ZSH_AUTOSUGGEST_STRATEGY=(history completion)

#--- DIRECTORY COLORS ---
# Enable colored ls output
export CLICOLOR=1
export LSCOLORS="GxFxCxDxBxegedabagaced"

# Better ls aliases with colors
alias ls='ls -G'
alias ll='ls -lhG'
alias la='ls -lahG'

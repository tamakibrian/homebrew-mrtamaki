# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Zsh Toolkit
# Source this file from ~/.zshrc:
#   source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
# ═══════════════════════════════════════════════════════════════════════════

#--- VERSION ---
MRTAMAKI_VERSION="1.9.0"

#--- HOMEBREW PREFIX ---
HOMEBREW_PREFIX="${HOMEBREW_PREFIX:-$(brew --prefix)}"

#--- INIT ---
SHELL_V11_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

#--- BANNER ---
# Set MRTAMAKI_NO_BANNER=1 in ~/.zshenv to skip the startup animation
if [[ -o interactive ]] && [[ -z "$MRTAMAKI_NO_BANNER" ]]; then
    if [[ -f "${SHELL_V11_DIR}/banner.py" ]]; then
        if _ensure_module_venv banner "$SHELL_V11_DIR" 2>/dev/null; then
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
    local current=0

    if [[ -f "$state_file" ]]; then
        current=$(<"$state_file")
        [[ "$current" =~ ^[0-9]+$ ]] || current=0
    fi

    local next=$(( (current + 1) % ${#MRTAMAKI_THEMES[@]} ))
    local theme_name="${MRTAMAKI_THEMES[$((next + 1))]}"

    echo "$next" > "$state_file"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Theme: ${theme_name}"
    echo "  (${next}/${#MRTAMAKI_THEMES[@]})"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    exec zsh
}

#--- MODULE LOADING ---
# Source modules
source "${SHELL_V11_DIR}/core.sh"              # Main functions: a1-a4, b2-g7
source "${SHELL_V11_DIR}/files/f.sh"       # File functions: f command
source "${SHELL_V11_DIR}/found/one_lookup.zsh" # 1lookup API: iplookup, everify, etc.
source "${SHELL_V11_DIR}/status/status.sh"     # Status functions: h9 (health dashboard)
source "${SHELL_V11_DIR}/clean/clean.sh"       # System cleaner: smenu (clean menu), h1-h7, h10

#--- ALIASES ---
alias cc='clear'

#--- HELP ---
mrtamaki() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  mrtamaki v${MRTAMAKI_VERSION} - Zsh Toolkit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  PROXY & IP TOOLS"
    echo "    a1              Generate IPRoyal proxy URL"
    echo "    a2              Generate Oxylabs proxy URL"
    echo "    a3              Speed run: IPRoyal → bind → test → check"
    echo "    a4              Speed run: Oxylabs → bind → test → check"
    echo "    b2 [flags]      Proxy converter (run b2 --help for flags)"
    echo "    c3 [port]       Test proxy on port / check system IP"
    echo "    d4 [ip]         Scamalytics IP reputation check (auto-detects IP)"
    echo "    d6 [port]       DNS leak test (check DNS resolver leaks)"
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

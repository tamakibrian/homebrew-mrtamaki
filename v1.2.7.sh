# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Main Entry Point
# Source this file from ~/.zshrc
# ═══════════════════════════════════════════════════════════════════════════

#--- HOMEBREW PREFIX ---
HOMEBREW_PREFIX="${HOMEBREW_PREFIX:-$(brew --prefix)}"

#--- BANNER ---
SHELL_V11_DIR="${0:A:h}"
if [[ -o interactive && -z "${__MRTAMAKI_BANNER_DONE:-}" ]]; then
    typeset -g __MRTAMAKI_BANNER_DONE=1
    if [[ -f "${SHELL_V11_DIR}/banner.py" ]]; then
        # Use venv python if available, fallback to system python3
        local _venv_py="${SHELL_V11_DIR}/.venv/bin/python3"
        if [[ -x "$_venv_py" ]]; then
            "$_venv_py" "${SHELL_V11_DIR}/banner.py" 2>/dev/null
        else
            python3 "${SHELL_V11_DIR}/banner.py" 2>/dev/null
        fi
    fi
fi

#--- THEME ---
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi
ZSH_THEME=""

#--- MODULE LOADING ---
# Source modules
source "${SHELL_V11_DIR}/core.sh"              # Main functions: a1-f6
source "${SHELL_V11_DIR}/files/files.sh"       # File functions: fa-fg, tempdir
source "${SHELL_V11_DIR}/found/one_lookup.zsh" # 1lookup API: iplookup, everify, etc.

#--- ALIASES ---
alias cc='clear'

#--- HELP ---
mrtamaki() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  mrtamaki v1.2.7 - Zsh Toolkit"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  PROXY & IP TOOLS"
    echo "    a1              Generate IPRoyal proxy URL"
    echo "    b2              Run proxy converter"
    echo "    c3 <port>       Test proxy on port, get IP"
    echo "    d4 <ip>         Scamalytics IP reputation check"
    echo ""
    echo "  SYSTEM"
    echo "    e5 [path]       Find and clean up virtual environments"
    echo "    f6              Flush DNS cache (macOS)"
    echo ""
    echo "  FILE COMMANDS"
    echo "    fa              Edit ~/.zshrc (backup + reload)"
    echo "    fb <term>       Recursive file search"
    echo "    fc <dir>        Make directory and cd into it"
    echo "    fd              Open last created file"
    echo "    fe              Find large files (>100M)"
    echo "    ff <file>       Backup file with timestamp"
    echo "    fg [name]       Create timestamped folder on Desktop"
    echo "    tempdir         Create and cd into temp directory"
    echo ""
    echo "  1LOOKUP API"
    echo "    iplookup <ip>   IP address lookup"
    echo "    everify <email> Email verification"
    echo "    eappend         Find email from personal info"
    echo "    reappend <email> Reverse email lookup"
    echo "    ripappend <ip>  Reverse IP lookup"
    echo "    found --help    Show 1lookup detailed help"
    echo ""
    echo "  ALIASES"
    echo "    cc              Clear screen"
    echo "    ll              List files (long format)"
    echo "    la              List all files (including hidden)"
    echo "    kk              Edit ~/.p10k.zsh"
    echo ""
    echo "  CREDENTIALS (add to ~/.zshenv)"
    echo "    export IPROYAL_USER='username'        # for a1"
    echo "    export IPROYAL_PASS='password'        # for a1"
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

#--- POWERLEVEL10K ---
[[ -f "${HOMEBREW_PREFIX}/share/powerlevel10k/powerlevel10k.zsh-theme" ]] && \
    source "${HOMEBREW_PREFIX}/share/powerlevel10k/powerlevel10k.zsh-theme"
# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
alias kk='edit ~/.p10k.zsh'

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

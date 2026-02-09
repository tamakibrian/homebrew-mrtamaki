# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Zsh Toolkit
# Source this file from ~/.zshrc:
#   source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
# ═══════════════════════════════════════════════════════════════════════════

#--- VERSION ---
MRTAMAKI_VERSION="1.7.1"

#--- HOMEBREW PREFIX ---
HOMEBREW_PREFIX="${HOMEBREW_PREFIX:-$(brew --prefix)}"

#--- INIT ---
SHELL_V11_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

#--- BANNER ---
if [[ -o interactive ]]; then
    if [[ -f "${SHELL_V11_DIR}/banner.py" ]]; then
        if _ensure_module_venv banner "$SHELL_V11_DIR" 2>/dev/null; then
            "$VENV_PYTHON" "${SHELL_V11_DIR}/banner.py" 2>/dev/null
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
source "${SHELL_V11_DIR}/core.sh"              # Main functions: a1-a4, b2-g7
source "${SHELL_V11_DIR}/files/files.sh"       # File functions: fa-fn
source "${SHELL_V11_DIR}/found/one_lookup.zsh" # 1lookup API: iplookup, everify, etc.
source "${SHELL_V11_DIR}/status/status.sh"     # Status functions: smenu (status menu), h9 (health dashboard)

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
    echo "    b2              Run proxy converter"
    echo "    c3 <port>       Test proxy on port, get IP"
    echo "    d4 <ip>         Scamalytics IP reputation check"
    echo ""
    echo "  SYSTEM"
    echo "    e5 [path]       Find and clean up virtual environments"
    echo "    f6              Flush DNS cache (macOS)"
    echo "    g7 [venv]       Pip purge (cache + packages, default: system)"
    echo "    smenu           Interactive status menu (cleanup, caches, venvs)"
    echo "    h9              Live system health dashboard (CPU, RAM, disk, net)"
    echo ""
    echo "  FILE COMMANDS"
    echo "    fmenu           Interactive file operations menu"
    echo "    fa              Edit ~/.zshrc (backup + reload)"
    echo "    fb <term>       Recursive file search"
    echo "    fc <dir>        Make directory and cd into it"
    echo "    fd              Open last created file"
    echo "    fe              Find large files (>100M)"
    echo "    ff              Create and cd into temp directory"
    echo "    fg <file>       Backup file with timestamp"
    echo "    fh [name]       Create timestamped folder on Desktop"
    echo "    fj [depth]      Show directory tree"
    echo "    fk [name]       Bookmark current directory"
    echo "    fl [name]       Jump to bookmarked directory"
    echo "    fm              List all bookmarks"
    echo "    fn [name]       Delete a bookmark"
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
    echo "  ALIASES"
    echo "    cc              Clear screen"
    echo "    ll              List files (long format)"
    echo "    la              List all files (including hidden)"
    echo "    kk              Edit ~/.p10k.zsh"
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

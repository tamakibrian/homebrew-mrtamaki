# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Zsh Toolkit
# Source this file from ~/.zshrc:
#   source "$(brew --prefix)/share/mrtamaki/mrtamaki.sh"
# ═══════════════════════════════════════════════════════════════════════════

#--- VERSION ---
MRTAMAKI_VERSION="1.12.0"

#--- INIT ---
SHELL_V11_DIR="${0:A:h}"
source "${SHELL_V11_DIR}/utils.sh"

#--- HOMEBREW PREFIX (fallback to install dir when brew not used) ---
if command -v brew &>/dev/null; then
    HOMEBREW_PREFIX="${HOMEBREW_PREFIX:-$(brew --prefix)}"
else
    HOMEBREW_PREFIX="${SHELL_V11_DIR}"
fi
 
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

#--- MRTAMAKI_DIR (for mt sys menu, clean_menu.py) ---
export MRTAMAKI_DIR="${MRTAMAKI_DIR:-$SHELL_V11_DIR}"

#--- mt: Self-healing wrapper — regenerates venv-cli if h4/smenu deleted it ---
# Uses mt from PATH when it works (preserves venv search scope); regenerates only when broken.
mt() {
    local mt_bin
    mt_bin=$(whence -p mt 2>/dev/null)
    if [[ -n "$mt_bin" ]] && [[ -x "$mt_bin" ]]; then
        "$mt_bin" "$@"
        return
    fi

    local venv_cli="${SHELL_V11_DIR}/venv-cli"
    local venv_alt="${SHELL_V11_DIR}/.venv"
    mt_bin=""

    if [[ -x "${venv_cli}/bin/mt" ]]; then
        mt_bin="${venv_cli}/bin/mt"
    elif [[ -x "${venv_alt}/bin/mt" ]]; then
        mt_bin="${venv_alt}/bin/mt"
    fi

    if [[ -z "$mt_bin" ]]; then
        _mrtamaki_regenerate_venvs "$SHELL_V11_DIR" || return 1
        mt_bin="${venv_cli}/bin/mt"
    fi

    "$mt_bin" "$@"
}

#--- ALIASES: Shortcuts → mt subcommands ---
alias a1='mt proxy iproyal'
alias a2='mt proxy oxylabs'
alias a3='mt proxy rapid'
alias a4='mt proxy rapid-speed'
alias a5='mt proxy iproyal-speed'
alias a6='mt proxy oxylabs-speed'
alias b2='mt proxy convert'

alias c3='mt ip test'
alias d4='mt ip check'
alias d6='mt ip dnsleak'
alias d7='mt ip iping'

alias h1='mt sys pycache'
alias h2='mt sys browser'
alias h3='mt sys app'
alias h4='mt sys venv'
alias h5='mt sys space'
alias h6='mt sys xcode'
alias h7='mt sys node'
alias h9='mt sys health'
alias health='mt sys health'
alias h10='mt sys dns'
alias flushdns='mt sys dns'
alias e5='mt sys venv-purge'
alias g7='mt sys pip'
alias f6='mt file --help'

alias d5='mt lookup'
alias found='mt lookup'
alias 1l='mt lookup'
alias iplookup='mt lookup ip'
alias everify='mt lookup email'
alias eappend='mt lookup eappend'
alias reappend='mt lookup reappend'
alias ripappend='mt lookup ripappend'

# mrtamaki = mt (long-form alias for central command)
mrtamaki() { mt "$@" }

#--- Semantic aliases (long-form discoverability) ---
alias pycache='mt sys pycache'
alias browsercache='mt sys browser'
alias appcache='mt sys app'
alias venvclean='mt sys venv'
alias space='mt sys space'
alias deriveddata='mt sys xcode'
alias nodemodules='mt sys node'
alias clean='smenu'
alias pipclean='mt sys pip'

#--- smenu: Shell wrapper for cd/delete from clean_menu (Python cannot change cwd) ---
smenu() {
    local tmp_result
    tmp_result=$(mktemp 2>/dev/null) || { print_error "Failed to create temp file"; return 1 }
    trap "rm -f $tmp_result" EXIT INT TERM
    MRTAMAKI_DIR="${MRTAMAKI_DIR:-$SHELL_V11_DIR}" mt sys menu --result-file "$tmp_result"
    local output=""
    [[ -f "$tmp_result" && -s "$tmp_result" ]] && output=$(<"$tmp_result")
    rm -f "$tmp_result"
    trap - EXIT INT TERM
    [[ "$output" != __CLEAN_CMD__:* ]] && return 0
    local cmd="${output#__CLEAN_CMD__:}"
    cmd="${cmd%%$'\n'*}"
    if [[ "$cmd" == __CD__:* ]]; then
        cd "${cmd#__CD__:}" && print_success "Changed to: $PWD"
    elif [[ "$cmd" == __DELETE_VENV__:* ]]; then
        local v="${cmd#__DELETE_VENV__:}"
        if [[ -d "$v" && -f "$v/bin/activate" ]]; then
            if confirm "Delete $v?" "N"; then
                rm -rf "$v"
                print_success "Deleted: $v"
            else
                print_info "Cancelled"
            fi
        else
            print_error "Not a valid venv: $v"
        fi
    else
        case "$cmd" in
            pycache)  mt sys pycache ;;
            browser)  mt sys browser ;;
            appcache) mt sys app ;;
            xcode)    mt sys xcode ;;
            nodemod)  mt sys node ;;
            trash)    mt sys trash ;;
            *)        print_error "Unknown command: $cmd"; return 1 ;;
        esac
    fi
}
alias h8='smenu'

#--- f: Shell function for cd support on --m, --t, --bg; else delegate to mt file ---
f() {
    [[ $# -eq 0 ]] && { mt file --help; return 0 }
    local flag="$1"
    shift
    case "$flag" in
        --m)  cd "$(mt file mkdir "${1:-}")" ;;
        --t)  cd "$(mt file tempdir)" ;;
        --bg) cd "$(mt file bookmark-go "${1:-}")" ;;
        --h|--help) mt file --help ;;
        --ez) mt file zshrc "$@" ;;
        --s)  mt file search "$@" ;;
        --o)  mt file open-last "$@" ;;
        --l)  mt file large "$@" ;;
        --b)  mt file backup "$@" ;;
        --d)  mt file desktop "$@" ;;
        --tr) mt file tree "$@" ;;
        --ba) mt file bookmark-add "$@" ;;
        --bl) mt file bookmark-list "$@" ;;
        --bd) mt file bookmark-del "$@" ;;
        *)   print_error "Unknown flag: $flag"; mt file --help; return 1 ;;
    esac
}

#--- ALIASES ---
alias cc='clear'

#--- HELP ---
# mrtamaki = mt (long-form). Run 'mt' or 'mrtamaki' with no args for command tree.
# Run 'mt --help' for full CLI help.
 
#--- SYNTAX HIGHLIGHTING & AUTOSUGGESTIONS ---
# Syntax highlighting (must be sourced after all other plugins)
# Try Homebrew path first, then local .mrtamaki-deps (install-without-brew.sh)
if [[ -f "${HOMEBREW_PREFIX}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    source "${HOMEBREW_PREFIX}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
elif [[ -f "${SHELL_V11_DIR}/.mrtamaki-deps/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]]; then
    source "${SHELL_V11_DIR}/.mrtamaki-deps/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi

# Autosuggestions (fish-like suggestions based on history)
if [[ -f "${HOMEBREW_PREFIX}/share/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
    source "${HOMEBREW_PREFIX}/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
elif [[ -f "${SHELL_V11_DIR}/.mrtamaki-deps/zsh-autosuggestions/zsh-autosuggestions.zsh" ]]; then
    source "${SHELL_V11_DIR}/.mrtamaki-deps/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi
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

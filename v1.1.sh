# ═══════════════════════════════════════════════════════════════════════════
# Shell V1.1 - Main Entry Point
# Source this file from ~/.zshrc
# ═══════════════════════════════════════════════════════════════════════════

#--- THEME ---
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi
ZSH_THEME=""

#--- MODULE LOADING ---
# Get the directory where this script is located
SHELL_V11_DIR="${0:A:h}"

# Source modules
source "${SHELL_V11_DIR}/core.sh"              # Main functions: a1-f6
source "${SHELL_V11_DIR}/files/files.sh"       # File functions: fa-fg, tempdir
source "${SHELL_V11_DIR}/found/one_lookup.zsh" # 1lookup API: iplookup, everify, etc.

#--- ALIASES ---
alias cc='clear'

#--- POWERLEVEL10K ---
source /opt/homebrew/share/powerlevel10k/powerlevel10k.zsh-theme
# To customize prompt, run `p10k configure` or edit ~/.p10k.zsh
[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh
alias kk='edit ~/.p10k.zsh'

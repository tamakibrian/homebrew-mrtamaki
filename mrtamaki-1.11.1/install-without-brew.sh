#!/usr/bin/env zsh
# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Install without Homebrew
# Downloads all dependencies (jq, zsh plugins, Python venv) without brew.
# Run from the mrtamaki source directory.
# ═══════════════════════════════════════════════════════════════════════════

set -e

INSTALL_DIR="${0:A:h}"
DEPS_DIR="${INSTALL_DIR}/.mrtamaki-deps"
JQ_VERSION="1.8.1"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  mrtamaki — Install without Homebrew"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Install dir: ${INSTALL_DIR}"
echo "  Deps dir:    ${DEPS_DIR}"
echo ""

#--- 1. Python venv + mrtamaki ---
echo "  [1/4] Creating Python venv and installing mrtamaki..."
if ! command -v python3 &>/dev/null; then
    echo "  ERROR: python3 not found. Install Python 3.10+ from python.org"
    exit 1
fi

VENV_DIR="${INSTALL_DIR}/.venv"
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi
"${VENV_DIR}/bin/pip" install -q --upgrade pip
"${VENV_DIR}/bin/pip" install -q -e "${INSTALL_DIR}"
echo "  ✓ Python venv ready (mt, mrtamaki in ${VENV_DIR}/bin)"
echo ""

#--- 2. jq binary ---
echo "  [2/4] Downloading jq..."
mkdir -p "${DEPS_DIR}/bin"
ARCH=$(uname -m)
OS=$(uname -s)

JQ_BIN="${DEPS_DIR}/bin/jq"
if [[ ! -x "$JQ_BIN" ]]; then
    case "$OS" in
        Darwin)
            if [[ "$ARCH" == "arm64" ]]; then
                JQ_URL="https://github.com/jqlang/jq/releases/download/jq-${JQ_VERSION}/jq-macos-arm64"
            else
                JQ_URL="https://github.com/jqlang/jq/releases/download/jq-${JQ_VERSION}/jq-macos-amd64"
            fi
            ;;
        Linux)
            if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
                JQ_URL="https://github.com/jqlang/jq/releases/download/jq-${JQ_VERSION}/jq-linux-arm64"
            else
                JQ_URL="https://github.com/jqlang/jq/releases/download/jq-${JQ_VERSION}/jq-linux-amd64"
            fi
            ;;
        *)
            echo "  WARN: Unsupported OS ($OS). Skipping jq. Install manually for d4."
            JQ_URL=""
            ;;
    esac

    if [[ -n "$JQ_URL" ]]; then
        if curl -sSL "$JQ_URL" -o "$JQ_BIN" 2>/dev/null; then
            chmod +x "$JQ_BIN"
            echo "  ✓ jq installed at ${JQ_BIN}"
        else
            echo "  WARN: jq download failed. Install manually for d4 (Scamalytics check)."
            rm -f "$JQ_BIN"
        fi
    fi
else
    echo "  ✓ jq already present"
fi
echo ""

#--- 3. zsh-syntax-highlighting ---
echo "  [3/4] Cloning zsh-syntax-highlighting..."
ZSH_SYNTAX_DIR="${DEPS_DIR}/zsh-syntax-highlighting"
if [[ ! -d "$ZSH_SYNTAX_DIR" ]]; then
    git clone -q --depth 1 https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_SYNTAX_DIR"
    echo "  ✓ zsh-syntax-highlighting at ${ZSH_SYNTAX_DIR}"
else
    echo "  ✓ zsh-syntax-highlighting already present"
fi
echo ""

#--- 4. zsh-autosuggestions ---
echo "  [4/4] Cloning zsh-autosuggestions..."
ZSH_AUTOSUG_DIR="${DEPS_DIR}/zsh-autosuggestions"
if [[ ! -d "$ZSH_AUTOSUG_DIR" ]]; then
    git clone -q --depth 1 https://github.com/zsh-users/zsh-autosuggestions.git "$ZSH_AUTOSUG_DIR"
    echo "  ✓ zsh-autosuggestions at ${ZSH_AUTOSUG_DIR}"
else
    echo "  ✓ zsh-autosuggestions already present"
fi
echo ""

#--- Optional: light-zsh theme (if Oh My Zsh exists) ---
OMZ_THEMES="${HOME}/.oh-my-zsh/custom/themes"
if [[ -d "$OMZ_THEMES" ]] && [[ ! -d "${OMZ_THEMES}/light-zsh" ]]; then
    echo "  [Optional] Cloning light-zsh theme..."
    git clone -q --depth 1 https://github.com/InfinityUniverse0/light-zsh.git "${OMZ_THEMES}/light-zsh"
    echo "  ✓ light-zsh theme installed"
    echo ""
fi

#--- Summary ---
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Install complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Add these lines to ~/.zshrc:"
echo ""
echo "  # mrtamaki (non-Homebrew)"
echo "  export PATH=\"${VENV_DIR}/bin:\$PATH\""
if [[ -x "$JQ_BIN" ]]; then
echo "  export PATH=\"${DEPS_DIR}/bin:\$PATH\""
fi
echo "  source \"${INSTALL_DIR}/mrtamaki.sh\""
echo ""
echo "  Then run: exec zsh"
echo ""

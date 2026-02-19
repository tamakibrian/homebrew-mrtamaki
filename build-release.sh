#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# build-release.sh - Create release ZIP for mrtamaki Homebrew cask
# Usage: ./build-release.sh [version]
# Example: ./build-release.sh 1.7.0
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Get version from argument or extract from mrtamaki.sh
VERSION="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}"

# Auto-detect source directory (find mrtamaki-* directory)
SOURCE_DIR=""
for dir in "${SCRIPT_DIR}"/mrtamaki-*/; do
    if [[ -f "${dir}mrtamaki.sh" ]]; then
        SOURCE_DIR="${dir%/}"
        break
    fi
done

if [[ -z "$SOURCE_DIR" || ! -d "$SOURCE_DIR" ]]; then
    echo "Error: Could not find mrtamaki-* source directory containing mrtamaki.sh"
    exit 1
fi

if [[ -z "$VERSION" ]]; then
    # Try to extract version from mrtamaki.sh
    VERSION=$(grep -m1 'MRTAMAKI_VERSION=' "${SOURCE_DIR}/mrtamaki.sh" | cut -d'"' -f2)
fi

if [[ -z "$VERSION" ]]; then
    echo "Error: Could not determine version. Pass it as argument: ./build-release.sh 1.5.0"
    exit 1
fi

ZIP_NAME="mrtamaki-${VERSION}.zip"
ZIP_PATH="${OUTPUT_DIR}/${ZIP_NAME}"

echo "═══════════════════════════════════════════════════════════════"
echo "Building mrtamaki release v${VERSION}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Source directory: ${SOURCE_DIR}"
echo "Output file:      ${ZIP_PATH}"
echo ""

# Remove old ZIP if exists
rm -f "${ZIP_PATH}"

# Create ZIP from source directory (files at root level)
cd "${SOURCE_DIR}"

zip -r "${ZIP_PATH}" . \
    -x "*.DS_Store" \
    -x "*__pycache__*" \
    -x "*/venv-*/*" \
    -x "venv-*/*" \
    -x "*/.venv/*" \
    -x ".venv/*" \
    -x "*/venv/*" \
    -x "venv/*" \
    -x ".pytest_cache/*" \
    -x "testdir/*" \
    -x "*.git*" \
    -x "Casks/*" \
    -x "docs/*" \
    -x "CLAUDE.md" \
    -x ".gitignore" \
    -x "v1.*.sh" \
    -x "pc_helper.py"


echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Release ZIP created: ${ZIP_PATH}"
echo ""

# Show contents
echo "ZIP contents:"
unzip -l "${ZIP_PATH}" | head -40
echo "..."
echo ""

# Calculate SHA256
SHA256=$(shasum -a 256 "${ZIP_PATH}" | cut -d' ' -f1)
echo "SHA256: ${SHA256}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Next steps:"
echo "1. Update Casks/mrtamaki.rb with:"
echo "   version \"${VERSION}\""
echo "   sha256 \"${SHA256}\""
echo ""
echo "2. Upload ${ZIP_NAME} to GitHub release v${VERSION}"
echo "3. Commit and push cask changes"
echo "═══════════════════════════════════════════════════════════════"

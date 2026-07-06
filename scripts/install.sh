#!/usr/bin/env sh
#
# Install deepbiology-lab CLI and MCP server.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/DeepBiology/deepbiology-lab/main/scripts/install.sh | sh
#
# Or with pip directly:
#   pip install git+https://github.com/DeepBiology/deepbiology-lab.git
#

set -eu

REPO="DeepBiology/deepbiology-lab"
INSTALL_DIR="${DEEPBIOLOGY_INSTALL_DIR:-}"
GITHUB_BASE="https://raw.githubusercontent.com/${REPO}/main"

# ── Color helpers ──────────────────────────────────────────────────
green='\033[0;32m'
yellow='\033[1;33m'
cyan='\033[0;36m'
red='\033[0;31m'
nc='\033[0m' # No Color
info()  { printf "${green}%s${nc}\n" "$*"; }
warn()  { printf "${yellow}Warning: %s${nc}\n" "$*"; }
note()  { printf "${cyan}%s${nc}\n" "$*"; }
error() { printf "${red}Error: %s${nc}\n" "$*"; }

# ── Requirements ───────────────────────────────────────────────────

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    error "$1 is required but not found"
    exit 1
  fi
}

need curl
need python3

# Check Python version (need 3.9+)
python_major="$(python3 -c 'import sys; print(sys.version_info.major)' 2>/dev/null || echo 0)"
python_minor="$(python3 -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || echo 0)"
if [ "$python_major" -lt 3 ] || { [ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]; }; then
  error "Python 3.9+ is required (found $python_major.$python_minor)"
  exit 1
fi
info "✓ Python $python_major.$python_minor"

# Check for pip
if ! command -v pip3 >/dev/null 2>&1 && ! command -v pip >/dev/null 2>&1; then
  error "pip is required but not found"
  error "Install pip: https://pip.pypa.io/en/stable/installation/"
  exit 1
fi
PIP="pip3"
command -v pip3 >/dev/null 2>&1 || PIP="pip"
info "✓ $(command -v $PIP)"

# ── Install ────────────────────────────────────────────────────────

info ""
info "Installing deepbiology-lab from GitHub..."
info ""

$PIP install "git+https://github.com/${REPO}.git" 2>&1

info ""
info "✓ deepbiology-lab installed successfully!"
info ""

# ── Verify ─────────────────────────────────────────────────────────

if command -v deepbiology-lab >/dev/null 2>&1; then
  version="$(deepbiology-lab --help 2>&1 | head -1 || true)"
  info "  CLI:      deepbiology-lab  $(echo "$version" | grep -o 'deepbiology-lab' || echo 'installed')"
else
  warn "deepbiology-lab not found on PATH after install"
  warn "You may need to add ~/.local/bin to your PATH or restart your shell"
fi

if command -v deepbiology-lab-mcp >/dev/null 2>&1; then
  info "  MCP:      deepbiology-lab-mcp"
else
  warn "deepbiology-lab-mcp not found on PATH"
fi

# ── Next steps ─────────────────────────────────────────────────────

info ""
note "═══════════════════════════════════════════════════════════════"
note "  Next steps"
note ""
note "  1. Configure your API key:"
note "     deepbiology-lab config --api-key dbio_your_api_key_here"
note ""
note "  2. Start the MCP server (for Claude Desktop, Cursor, VS Code):"
note "     deepbiology-lab-mcp"
note ""
note "  3. Install the Codex plugin (for OpenAI Codex):"
note "     codex plugin marketplace add ${REPO}"
note "     codex plugin add deepbiology@deepbiology-marketplace"
note ""
note "  4. Follow the full guide:"
note "     https://github.com/${REPO}"
note ""
note "  See: https://github.com/${REPO} for full docs"
note "═══════════════════════════════════════════════════════════════"

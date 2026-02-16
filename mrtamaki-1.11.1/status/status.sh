# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - Status Module
# System health dashboard: h9/health
# ═══════════════════════════════════════════════════════════════════════════
 
# The main mrtamaki.sh script should set MRTAMAKI_DIR.
# If not set, default to parent of the script's dir.
if [[ -z "$MRTAMAKI_DIR" ]]; then
    export MRTAMAKI_DIR="${0:A:h:h}"
fi
 
STATUS_DIR="${MRTAMAKI_DIR}/status"
 
# Source shared utilities
source "${MRTAMAKI_DIR}/utils.sh"
 
#---------- VENV SETUP FOR HEALTH DASHBOARD ----------
 
# Setup venv for the health dashboard (uses centralized venv function)
_status_setup_venv() {
    _ensure_module_venv status "$MRTAMAKI_DIR"
}
 
#---------- LIVE HEALTH DASHBOARD (h9) ----------
 
# Live system health dashboard
h9() {
    _status_setup_venv || return 1
    "$VENV_PYTHON" "${STATUS_DIR}/health_dashboard.py"
}
 
#---------- ALIASES ----------
 
alias health='h9'
alias dashboard='h9'


# ═══════════════════════════════════════════════════════════════════════════
# mrtamaki - IP Module (mt ip)
# c3 (test proxy), d4 (Scamalytics check), d6 (DNS leak test)
# ═══════════════════════════════════════════════════════════════════════════

IP_DIR="${0:A:h}"
MRTAMAKI_DIR="${IP_DIR:h}"
source "${MRTAMAKI_DIR}/utils.sh"

#--- Test proxy / check system IP (c3) ---
c3() {
    local port="$1"
    local use_proxy=true

    if [[ -z "$port" ]]; then
        use_proxy=false
        print_info "No port specified — checking system IP..."
    else
        if ! [[ "$port" =~ ^[0-9]+$ ]] || [[ "$port" -lt "$PORT_MIN" || "$port" -gt "$PORT_MAX" ]]; then
            print_error "Invalid port number. Must be between ${PORT_MIN}-${PORT_MAX}"
            return 1
        fi
        print_info "Testing proxy on port $port..."
    fi

    local json
    if $use_proxy; then
        json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
            -x "127.0.0.1:$port" \
            https://ipinfo.io/json)" || {
            print_error "⚠️ No response from port $port"
            return 1
        }
    else
        json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
            https://ipinfo.io/json)" || {
            print_error "⚠️ No response from ipinfo.io"
            return 1
        }
    fi

    if ! printf '%s' "$json" | grep -q '"ip"'; then
        print_error "Invalid response format (missing IP field)"
        print_info "Raw response:"
        printf '%s\n' "$json"
        return 1
    fi

    local ip
    ip="$(printf '%s' "$json" | sed -nE 's/.*"ip"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')"

    if [[ -z "$ip" ]]; then
        print_error "Could not parse IP from response"
        print_info "Raw response:"
        printf '%s\n' "$json"
        return 1
    fi

    local panel_title
    if $use_proxy; then
        panel_title="  Proxy IP Info"
    else
        panel_title="  System IP Info"
    fi

    _ensure_venv "$MRTAMAKI_DIR" 2>/dev/null
    if [[ -n "$VENV_PYTHON" ]] && "$VENV_PYTHON" -c "import rich" 2>/dev/null; then
        _IPINFO_JSON="$json" _PANEL_TITLE="$panel_title" "$VENV_PYTHON" - <<'PYEOF'
import os, json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()
data = json.loads(os.environ['_IPINFO_JSON'])

table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
table.add_column("Field", style="bold cyan")
table.add_column("Value", style="white")

fields = [
    ("ip",       "IP Address"),
    ("hostname", "Hostname"),
    ("city",     "City"),
    ("region",   "Region"),
    ("country",  "Country"),
    ("loc",      "Location"),
    ("org",      "Organization"),
    ("postal",   "Postal"),
    ("timezone", "Timezone"),
]

for key, label in fields:
    val = data.get(key)
    if val:
        table.add_row(label, str(val))

console.print()
title = os.environ.get('_PANEL_TITLE', '  IP Info')
console.print(Panel(table, title=f"[bold green]{title}[/]", border_style="green", box=box.ROUNDED))
console.print()
PYEOF
    else
        print_info "IP: $ip"
        printf '%s\n' "$json"
    fi

    echo ""
    d6 "$port"

    echo ""
    if printf '%s' "$ip" | copy_to_clipboard; then
        print_info "Copied IP to clipboard ✅"
    fi
}

#--- Scamalytics IP reputation check (d4) ---
d4() {
    local api_key="${SCAMALYTICS_API_KEY:-}"
    if [[ -z "$api_key" ]]; then
        print_error "SCAMALYTICS_API_KEY not set"
        print_info "Add to ~/.zshenv: export SCAMALYTICS_API_KEY='your_key'"
        return 1
    fi

    local ip="$1"

    if [[ -z "$ip" ]]; then
        print_info "No IP specified — fetching system IP..."
        local sys_json
        sys_json="$(curl -fsS --max-time "$NETWORK_TIMEOUT" --retry 2 \
            https://ipinfo.io/json)" || {
            print_error "⚠️ Failed to fetch system IP from ipinfo.io"
            return 1
        }
        ip="$(printf '%s' "$sys_json" | sed -nE 's/.*"ip"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p')"
        if [[ -z "$ip" ]]; then
            print_error "Could not parse system IP"
            return 1
        fi
    fi

    if ! [[ "$ip" =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        print_error "Invalid IP address format"
        return 1
    fi

    print_info "Checking IP: $ip"

    local response
    response=$(curl -fsS --max-time "$NETWORK_TIMEOUT" \
        "https://api11.scamalytics.com/v3/bradeysulley/?key=${api_key}&ip=$ip") || {
        print_error "Failed to retrieve IP information"
        return 1
    }

    if ! command -v jq &>/dev/null; then
        print_warning "jq not installed, showing raw response:"
        printf '%s\n' "$response"
        return 0
    fi

    if ! printf '%s' "$response" | jq -e . >/dev/null 2>&1; then
        print_error "Invalid JSON response"
        print_info "Raw response:"
        printf '%s\n' "$response"
        return 1
    fi

    printf '%s\n' "$response" | jq .
}

#--- DNS leak test (d6) ---
d6() {
    local port="$1"

    if ! command -v python3 &>/dev/null; then
        print_error "python3 is required for DNS leak test"
        return 1
    fi
    if ! command -v dig &>/dev/null; then
        print_error "dig is required for DNS leak test"
        return 1
    fi

    local dns_leak_script="${IP_DIR}/dns_leak.py"

    if [[ -n "$port" ]]; then
        if ! command -v proxychains4 &>/dev/null; then
            print_error "proxychains4 not found. Please run 'brew install proxychains-ng' (it installs as proxychains4)"
            return 1
        fi

        local conf_file
        conf_file=$(mktemp) || {
            print_error "Failed to create temp file for proxychains config"
            return 1
        }
        trap 'rm -f "$conf_file"' RETURN

        {
            echo "strict_chain"
            echo "proxy_dns"
            echo "[ProxyList]"
            echo "http 127.0.0.1 $port"
        } > "$conf_file"

        print_info "Running DNS leak test via proxy on port $port..."
        proxychains4 -f "$conf_file" python3 "$dns_leak_script"
    else
        print_info "Running DNS leak test on system..."
        python3 "$dns_leak_script"
    fi
}

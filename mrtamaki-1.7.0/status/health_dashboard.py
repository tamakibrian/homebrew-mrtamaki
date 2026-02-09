#!/usr/bin/env python3
"""Live system health dashboard - CPU, memory, disk, network, processes, battery."""

import sys
import os
import time
import socket
import threading
from datetime import datetime

import readchar
import psutil
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich import box

# ─── Themes (same as status_menu.py) ────────────────────────────────────────

THEMES = {
    "default": {
        "accent": "cyan",
        "highlight": "yellow",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "bright_black",
    },
    "ocean": {
        "accent": "blue",
        "highlight": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
        "muted": "bright_black",
        "border": "blue",
    },
    "sunset": {
        "accent": "magenta",
        "highlight": "yellow",
        "success": "green",
        "warning": "orange3",
        "error": "red",
        "muted": "bright_black",
        "border": "magenta",
    },
}

THEME_NAMES = list(THEMES.keys())
CURRENT_THEME = "default"


def get_theme():
    """Get current theme colors."""
    return THEMES.get(CURRENT_THEME, THEMES["default"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def format_bytes(bytes_val: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """Format bytes/sec into human-readable speed."""
    for unit in ["B/s", "KB/s", "MB/s", "GB/s"]:
        if bytes_per_sec < 1024.0:
            return f"{bytes_per_sec:.1f} {unit}"
        bytes_per_sec /= 1024.0
    return f"{bytes_per_sec:.1f} TB/s"


def format_uptime(boot_time: float) -> str:
    """Format uptime from boot time."""
    delta = int(time.time() - boot_time)
    days, remainder = divmod(delta, 86400)
    hours, remainder = divmod(remainder, 3600)
    mins, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")
    return " ".join(parts)


def make_bar(percent: float, width: int = 20) -> Text:
    """Create a colored progress bar using block characters."""
    filled = int(width * percent / 100)
    empty = width - filled

    if percent > 90:
        color = "red"
    elif percent > 70:
        color = "yellow"
    else:
        color = "green"

    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty, style="bright_black")
    bar.append(f" {percent:5.1f}%", style=color)
    return bar


# ─── Metrics Collector ───────────────────────────────────────────────────────

class MetricsCollector:
    """Collects system metrics for the dashboard."""

    def __init__(self):
        self._prev_net = psutil.net_io_counters()
        self._prev_time = time.time()
        self._net_up = 0.0
        self._net_down = 0.0

    def collect(self) -> dict:
        """Collect all system metrics."""
        return {
            "cpu": self._cpu(),
            "memory": self._memory(),
            "disk": self._disk(),
            "network": self._network(),
            "processes": self._processes(),
            "battery": self._battery(),
            "hostname": socket.gethostname(),
            "boot_time": psutil.boot_time(),
        }

    def _cpu(self) -> dict:
        per_core = psutil.cpu_percent(interval=0, percpu=True)
        load = os.getloadavg()
        return {
            "per_core": per_core,
            "total": sum(per_core) / max(len(per_core), 1),
            "load_avg": load,
            "core_count": len(per_core),
        }

    def _memory(self) -> dict:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            "ram_used": mem.used,
            "ram_total": mem.total,
            "ram_percent": mem.percent,
            "swap_used": swap.used,
            "swap_total": swap.total,
            "swap_percent": swap.percent,
        }

    def _disk(self) -> list:
        disks = []
        for part in psutil.disk_partitions():
            # Skip special filesystems
            if part.fstype in ("devfs", "autofs", "nullfs", "vmhgfs-fuse"):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "mount": part.mountpoint,
                    "used": usage.used,
                    "total": usage.total,
                    "free": usage.free,
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                continue
        return disks

    def _network(self) -> dict:
        now = time.time()
        net = psutil.net_io_counters()
        dt = now - self._prev_time
        if dt > 0:
            self._net_up = (net.bytes_sent - self._prev_net.bytes_sent) / dt
            self._net_down = (net.bytes_recv - self._prev_net.bytes_recv) / dt
        self._prev_net = net
        self._prev_time = now
        return {
            "upload_speed": self._net_up,
            "download_speed": self._net_down,
            "total_sent": net.bytes_sent,
            "total_recv": net.bytes_recv,
        }

    def _processes(self) -> list:
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                procs.append({
                    "pid": info["pid"],
                    "name": (info["name"] or "")[:20],
                    "cpu": info["cpu_percent"] or 0.0,
                    "mem": info["memory_percent"] or 0.0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return procs

    def _battery(self) -> dict:
        bat = psutil.sensors_battery()
        if bat is None:
            return {"available": False}
        return {
            "available": True,
            "percent": bat.percent,
            "plugged": bat.power_plugged,
            "secs_left": bat.secsleft if bat.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
        }


# ─── Dashboard Renderer ─────────────────────────────────────────────────────

class HealthDashboard:
    """Rich TUI health dashboard."""

    def __init__(self):
        self.console = Console()
        self.collector = MetricsCollector()
        self.sort_by = "cpu"  # cpu, mem, pid
        self.running = True
        self._quit_event = threading.Event()
        self.metrics = self.collector.collect()

    # ── Panels ───────────────────────────────────────────────────────────

    def render_header(self) -> Panel:
        """Render header with hostname, uptime, and time."""
        theme = get_theme()
        m = self.metrics

        header = Text()
        header.append("  ", style=theme["accent"])
        header.append(" Health Dashboard", style=f"bold {theme['accent']}")
        header.append("   ", style=theme["muted"])
        header.append(f"{m['hostname']}", style=theme["highlight"])
        header.append("   ⏱ ", style=theme["muted"])
        header.append(f"up {format_uptime(m['boot_time'])}", style=theme["muted"])
        header.append("    ", style=theme["muted"])
        header.append(datetime.now().strftime("%H:%M:%S"), style=theme["accent"])

        return Panel(header, border_style=theme["border"], padding=(0, 1), height=3)

    def render_cpu(self) -> Panel:
        """Render CPU panel with per-core bars and load average."""
        theme = get_theme()
        cpu = self.metrics["cpu"]

        content = Text()
        for i, pct in enumerate(cpu["per_core"]):
            label = f"  Core {i:<2d} "
            content.append(label, style=theme["muted"])
            content.append_text(make_bar(pct, width=16))
            if i < len(cpu["per_core"]) - 1:
                content.append("\n")

        content.append("\n")
        load = cpu["load_avg"]
        content.append(f"  Load Avg: ", style=theme["muted"])
        content.append(f"{load[0]:.2f}", style=theme["accent"])
        content.append(f"  {load[1]:.2f}", style=theme["accent"])
        content.append(f"  {load[2]:.2f}", style=theme["accent"])
        content.append(f"  (1m  5m  15m)", style=theme["muted"])

        return Panel(
            content,
            title="CPU",
            title_align="left",
            border_style=theme["border"],
            padding=(0, 0),
        )

    def render_memory(self) -> Panel:
        """Render memory panel with RAM and swap bars."""
        theme = get_theme()
        mem = self.metrics["memory"]

        content = Text()
        content.append("  RAM   ", style=theme["muted"])
        content.append_text(make_bar(mem["ram_percent"], width=18))
        content.append(f"\n        {format_bytes(mem['ram_used'])} / {format_bytes(mem['ram_total'])}", style=theme["muted"])

        if mem["swap_total"] > 0:
            content.append("\n  Swap  ", style=theme["muted"])
            content.append_text(make_bar(mem["swap_percent"], width=18))
            content.append(f"\n        {format_bytes(mem['swap_used'])} / {format_bytes(mem['swap_total'])}", style=theme["muted"])

        return Panel(
            content,
            title="Memory",
            title_align="left",
            border_style=theme["border"],
            padding=(0, 0),
        )

    def render_disk(self) -> Panel:
        """Render disk panel with mount point bars."""
        theme = get_theme()
        disks = self.metrics["disk"]

        content = Text()
        for i, d in enumerate(disks):
            # Truncate long mount paths
            mount = d["mount"]
            if len(mount) > 12:
                mount = "…" + mount[-11:]
            content.append(f"  {mount:<12s} ", style=theme["muted"])
            content.append_text(make_bar(d["percent"], width=14))
            content.append(f"\n    {format_bytes(d['used'])} / {format_bytes(d['total'])}  ({format_bytes(d['free'])} free)", style=theme["muted"])
            if i < len(disks) - 1:
                content.append("\n")

        if not disks:
            content.append("  No disks found", style=theme["muted"])

        return Panel(
            content,
            title="Disk",
            title_align="left",
            border_style=theme["border"],
            padding=(0, 0),
        )

    def render_network(self) -> Panel:
        """Render network panel with speeds and totals."""
        theme = get_theme()
        net = self.metrics["network"]

        content = Text()
        content.append("  ↑ Upload    ", style=theme["muted"])
        content.append(f"{format_speed(net['upload_speed'])}", style=theme["success"])
        content.append("\n  ↓ Download  ", style=theme["muted"])
        content.append(f"{format_speed(net['download_speed'])}", style=theme["accent"])
        content.append("\n")
        content.append(f"\n  Total sent  ", style=theme["muted"])
        content.append(f"{format_bytes(net['total_sent'])}", style=theme["muted"])
        content.append(f"\n  Total recv  ", style=theme["muted"])
        content.append(f"{format_bytes(net['total_recv'])}", style=theme["muted"])

        return Panel(
            content,
            title="Network",
            title_align="left",
            border_style=theme["border"],
            padding=(0, 0),
        )

    def render_processes(self) -> Panel:
        """Render top processes table."""
        theme = get_theme()
        procs = self.metrics["processes"]

        # Sort
        if self.sort_by == "cpu":
            procs.sort(key=lambda p: p["cpu"], reverse=True)
        elif self.sort_by == "mem":
            procs.sort(key=lambda p: p["mem"], reverse=True)
        elif self.sort_by == "pid":
            procs.sort(key=lambda p: p["pid"])

        top = procs[:6]

        table = Table(
            box=None,
            show_header=True,
            header_style=f"bold {theme['accent']}",
            padding=(0, 1),
            expand=True,
        )
        table.add_column("PID", justify="right", style=theme["muted"], width=7)
        table.add_column("Name", style=theme["highlight"], width=16, no_wrap=True)

        # Highlight active sort column
        cpu_style = f"bold {theme['accent']}" if self.sort_by == "cpu" else theme["muted"]
        mem_style = f"bold {theme['accent']}" if self.sort_by == "mem" else theme["muted"]
        table.add_column("CPU%", justify="right", style=cpu_style, width=6)
        table.add_column("MEM%", justify="right", style=mem_style, width=6)

        for p in top:
            table.add_row(
                str(p["pid"]),
                p["name"],
                f"{p['cpu']:.1f}",
                f"{p['mem']:.1f}",
            )

        sort_label = f"  [sort: {self.sort_by}]"
        return Panel(
            table,
            title=f"Top Processes{sort_label}",
            title_align="left",
            border_style=theme["border"],
            padding=(0, 0),
        )

    def render_battery(self) -> Panel:
        """Render battery panel."""
        theme = get_theme()
        bat = self.metrics["battery"]

        content = Text()
        if not bat["available"]:
            content.append("  No battery (desktop)", style=theme["muted"])
        else:
            icon = "⚡" if bat["plugged"] else "🔋"
            status = "Charging" if bat["plugged"] else "On Battery"
            content.append(f"  {icon} {status}  ", style=theme["muted"])
            content.append_text(make_bar(bat["percent"], width=16))

            if not bat["plugged"] and bat["secs_left"] > 0:
                hrs, rem = divmod(int(bat["secs_left"]), 3600)
                mins, _ = divmod(rem, 60)
                content.append(f"\n  {hrs}h {mins}m remaining", style=theme["muted"])

        return Panel(
            content,
            title="Battery",
            title_align="left",
            border_style=theme["border"],
            padding=(0, 0),
        )

    def render_footer(self) -> Panel:
        """Render controls footer."""
        theme = get_theme()
        controls = Text()
        controls.append("  q", style=f"bold {theme['accent']}")
        controls.append(" quit  ", style=theme["muted"])
        controls.append("c", style=f"bold {theme['accent']}")
        controls.append(" sort CPU  ", style=theme["muted"])
        controls.append("m", style=f"bold {theme['accent']}")
        controls.append(" sort MEM  ", style=theme["muted"])
        controls.append("p", style=f"bold {theme['accent']}")
        controls.append(" sort PID  ", style=theme["muted"])
        controls.append("t", style=f"bold {theme['accent']}")
        controls.append(" theme", style=theme["muted"])

        return Panel(controls, border_style=theme["border"], padding=(0, 0), height=3)

    # ── Full Layout ──────────────────────────────────────────────────────

    def render(self) -> Layout:
        """Render the full two-column dashboard layout."""
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1),
        )

        # Left column: CPU, Memory, Disk stacked
        layout["left"].split_column(
            Layout(name="cpu"),
            Layout(name="memory"),
            Layout(name="disk"),
        )

        # Right column: Network, Processes, Battery stacked
        layout["right"].split_column(
            Layout(name="network"),
            Layout(name="processes"),
            Layout(name="battery"),
        )

        layout["header"].update(self.render_header())
        layout["cpu"].update(self.render_cpu())
        layout["memory"].update(self.render_memory())
        layout["disk"].update(self.render_disk())
        layout["network"].update(self.render_network())
        layout["processes"].update(self.render_processes())
        layout["battery"].update(self.render_battery())
        layout["footer"].update(self.render_footer())

        return layout

    # ── Input & Run ──────────────────────────────────────────────────────

    def _input_thread(self):
        """Daemon thread for non-blocking keyboard input."""
        global CURRENT_THEME
        while self.running:
            try:
                key = readchar.readkey()
            except (KeyboardInterrupt, EOFError):
                self.running = False
                self._quit_event.set()
                break

            if key in ("q", "Q", readchar.key.ESCAPE):
                self.running = False
                self._quit_event.set()
            elif key in ("c", "C"):
                self.sort_by = "cpu"
            elif key in ("m", "M"):
                self.sort_by = "mem"
            elif key in ("p", "P"):
                self.sort_by = "pid"
            elif key in ("t", "T"):
                idx = THEME_NAMES.index(CURRENT_THEME)
                CURRENT_THEME = THEME_NAMES[(idx + 1) % len(THEME_NAMES)]

    def run(self):
        """Run the live dashboard."""
        if not self.console.is_terminal:
            return

        # Start input listener
        input_thread = threading.Thread(target=self._input_thread, daemon=True)
        input_thread.start()

        self.console.clear()

        try:
            with Live(
                self.render(),
                console=self.console,
                refresh_per_second=4,
                screen=True,
            ) as live:
                while self.running:
                    self.metrics = self.collector.collect()
                    live.update(self.render())
                    # Use Event.wait instead of time.sleep so quit is instant
                    self._quit_event.wait(timeout=1.5)
        except KeyboardInterrupt:
            pass


def main():
    """Main entry point."""
    dashboard = HealthDashboard()
    dashboard.run()


if __name__ == "__main__":
    main()

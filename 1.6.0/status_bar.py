#!/usr/bin/env python3
"""
status_bar.py
Persistent status bar providing __pycache__ info and system health.
Works with both curses (menu_ui) and rich (proxy_converter) displays.
"""

import os
import shutil
import subprocess
import time
import threading

# --------------- Data Collection ---------------

def _get_pycache_info(root: str | None = None) -> dict:
    """
    Walk from *root* (default: directory of this script) and collect
    __pycache__ stats: directory count, total files, total size in bytes.
    """
    if root is None:
        root = os.path.dirname(os.path.abspath(__file__))

    dirs = 0
    files = 0
    total_bytes = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # skip virtualenvs and hidden dirs
        dirnames[:] = [
            d for d in dirnames
            if d not in {"venv", ".venv", "node_modules", ".git"}
        ]
        if os.path.basename(dirpath) == "__pycache__":
            dirs += 1
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_bytes += os.path.getsize(fp)
                    files += 1
                except OSError:
                    pass

    return {"dirs": dirs, "files": files, "bytes": total_bytes}


def _get_memory_info() -> dict:
    """Parse macOS vm_stat to get memory usage."""
    try:
        out = subprocess.check_output(["vm_stat"], text=True, timeout=2)
        page_size = 16384  # default on Apple Silicon
        for line in out.splitlines():
            if "page size" in line.lower():
                parts = line.split()
                for p in parts:
                    if p.isdigit():
                        page_size = int(p)
                        break

        stats = {}
        for line in out.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip().rstrip(".")
                if val.isdigit():
                    stats[key.strip()] = int(val) * page_size

        free = stats.get("Pages free", 0)
        active = stats.get("Pages active", 0)
        inactive = stats.get("Pages inactive", 0)
        wired = stats.get("Pages wired down", 0)
        speculative = stats.get("Pages speculative", 0)
        compressed = stats.get("Pages occupied by compressor", 0)

        used = active + wired + compressed
        total = free + active + inactive + wired + speculative + compressed
        if total == 0:
            total = 1  # avoid division by zero
        pct = (used / total) * 100

        return {"used_gb": used / (1024 ** 3), "total_gb": total / (1024 ** 3), "pct": pct}
    except Exception:
        return {"used_gb": 0, "total_gb": 0, "pct": 0}


def _get_cpu_load() -> tuple:
    """Return 1m, 5m, 15m load averages."""
    try:
        return os.getloadavg()
    except OSError:
        return (0.0, 0.0, 0.0)


def _get_disk_info(path: str = "/") -> dict:
    """Disk usage for the given mount point."""
    usage = shutil.disk_usage(path)
    pct = (usage.used / usage.total) * 100 if usage.total else 0
    return {
        "used_gb": usage.used / (1024 ** 3),
        "total_gb": usage.total / (1024 ** 3),
        "free_gb": usage.free / (1024 ** 3),
        "pct": pct,
    }


def _fmt_bytes(n: int) -> str:
    """Human-friendly byte size."""
    if n < 1024:
        return f"{n}B"
    elif n < 1024 ** 2:
        return f"{n / 1024:.1f}KB"
    elif n < 1024 ** 3:
        return f"{n / (1024 ** 2):.1f}MB"
    else:
        return f"{n / (1024 ** 3):.1f}GB"


# --------------- Snapshot (cached) ---------------

_cache_lock = threading.Lock()
_cached: dict | None = None
_cached_at: float = 0
_CACHE_TTL = 3  # seconds


def snapshot(root: str | None = None) -> dict:
    """
    Return a dict with all status-bar data.
    Results are cached for _CACHE_TTL seconds to avoid hammering the OS.
    """
    global _cached, _cached_at
    now = time.monotonic()
    with _cache_lock:
        if _cached is not None and (now - _cached_at) < _CACHE_TTL:
            return _cached

    pc = _get_pycache_info(root)
    mem = _get_memory_info()
    cpu = _get_cpu_load()
    disk = _get_disk_info()

    data = {
        "pycache_dirs": pc["dirs"],
        "pycache_files": pc["files"],
        "pycache_size": pc["bytes"],
        "pycache_size_fmt": _fmt_bytes(pc["bytes"]),
        "cpu_1m": cpu[0],
        "cpu_5m": cpu[1],
        "cpu_15m": cpu[2],
        "mem_used_gb": mem["used_gb"],
        "mem_total_gb": mem["total_gb"],
        "mem_pct": mem["pct"],
        "disk_used_gb": disk["used_gb"],
        "disk_total_gb": disk["total_gb"],
        "disk_free_gb": disk["free_gb"],
        "disk_pct": disk["pct"],
    }

    with _cache_lock:
        _cached = data
        _cached_at = time.monotonic()

    return data


# --------------- Formatted Strings ---------------

def curses_lines(root: str | None = None) -> tuple[str, str]:
    """
    Return two plain-text lines suitable for a curses status bar.
    Line 1: pycache info
    Line 2: system health
    """
    d = snapshot(root)
    line1 = (
        f" PYCACHE  dirs:{d['pycache_dirs']}  "
        f"files:{d['pycache_files']}  "
        f"size:{d['pycache_size_fmt']}"
        f"          [c] Clear PyCache"
    )
    line2 = (
        f" SYSTEM  "
        f"CPU:{d['cpu_1m']:.1f}  "
        f"MEM:{d['mem_used_gb']:.1f}/{d['mem_total_gb']:.1f}GB ({d['mem_pct']:.0f}%)  "
        f"DISK:{d['disk_used_gb']:.0f}/{d['disk_total_gb']:.0f}GB ({d['disk_pct']:.0f}%)"
        f"    [d] Flush DNS"
    )
    return line1, line2


# --------------- Actions ---------------

def clear_pycache(root: str | None = None) -> dict:
    """
    Delete all __pycache__ directories under *root*.
    Returns stats about what was removed.
    Invalidates snapshot cache so the status bar updates immediately.
    """
    import shutil as _shutil

    if root is None:
        root = os.path.dirname(os.path.abspath(__file__))

    dirs_removed = 0
    files_removed = 0
    bytes_freed = 0

    targets = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if d not in {"venv", ".venv", "node_modules", ".git"}
        ]
        if os.path.basename(dirpath) == "__pycache__":
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    bytes_freed += os.path.getsize(fp)
                    files_removed += 1
                except OSError:
                    pass
            targets.append(dirpath)

    for t in targets:
        try:
            _shutil.rmtree(t)
            dirs_removed += 1
        except OSError:
            pass

    # invalidate cache so status bar updates immediately
    global _cached, _cached_at
    with _cache_lock:
        _cached = None
        _cached_at = 0

    return {
        "dirs_removed": dirs_removed,
        "files_removed": files_removed,
        "bytes_freed": bytes_freed,
        "bytes_freed_fmt": _fmt_bytes(bytes_freed),
    }


def flush_dns_cache() -> dict:
    """
    Flush the macOS DNS cache.
    Temporarily drops curses so sudo can prompt for a password in the real terminal.
    Returns {"success": bool, "message": str}.
    """
    cmds = [
        ["sudo", "dscacheutil", "-flushcache"],
        ["sudo", "killall", "-HUP", "mDNSResponder"],
    ]
    errors = []
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=True, timeout=30)
        except subprocess.CalledProcessError as e:
            errors.append(f"{' '.join(cmd)}: exit {e.returncode}")
        except subprocess.TimeoutExpired:
            errors.append(f"{' '.join(cmd)}: timed out")
        except FileNotFoundError:
            errors.append(f"{' '.join(cmd)}: command not found")

    if errors:
        return {"success": False, "message": "Errors: " + "; ".join(errors)}
    return {"success": True, "message": "DNS cache flushed"}


def rich_bar(root: str | None = None) -> str:
    """
    Return a rich-markup string for a single-panel status bar.
    """
    d = snapshot(root)

    mem_color = "green" if d["mem_pct"] < 60 else ("yellow" if d["mem_pct"] < 85 else "red")
    disk_color = "green" if d["disk_pct"] < 70 else ("yellow" if d["disk_pct"] < 90 else "red")
    cpu_color = "green" if d["cpu_1m"] < 4.0 else ("yellow" if d["cpu_1m"] < 8.0 else "red")

    return (
        f"[bold cyan]PYCACHE[/]  "
        f"dirs:[white]{d['pycache_dirs']}[/]  "
        f"files:[white]{d['pycache_files']}[/]  "
        f"size:[white]{d['pycache_size_fmt']}[/]"
        f"  [dim]|[/]  "
        f"[bold cyan]SYSTEM[/]  "
        f"CPU:[{cpu_color}]{d['cpu_1m']:.1f}[/]  "
        f"MEM:[{mem_color}]{d['mem_used_gb']:.1f}/{d['mem_total_gb']:.1f}GB "
        f"({d['mem_pct']:.0f}%)[/]  "
        f"DISK:[{disk_color}]{d['disk_used_gb']:.0f}/{d['disk_total_gb']:.0f}GB "
        f"({d['disk_pct']:.0f}%)[/]"
    )

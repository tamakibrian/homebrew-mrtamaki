"""System CLI: pycache, browser, app, venv, space, xcode, node, menu, health, dns (h1-h10, e5, g7)."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.table import Table

from mrtamaki._utils import confirm, console, human_size, print_error, print_info, print_success, print_warning

app = typer.Typer(help="System tools: cleanup, health, DNS flush")

_MRTAMAKI_ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
SEARCH_PATHS = [HOME / "Desktop", HOME / "Documents", HOME / "Downloads", HOME / "Projects"]
VENV_NAMES = ("venv", ".venv", "env", "pyenv")
VENV_PATTERNS = ["venv", ".venv", "env", "pyenv", "venv-*"]

# Sys UI: distinct from proxy (blue/cyan vs green). All sys commands use this.
_SYS_BORDER = "blue"
_SYS_TITLE_STYLE = "bold blue"


def _sys_panel(title: str, content) -> None:
    """Render a sys-styled panel (blue border, distinct from proxy green)."""
    console.print()
    console.print(Panel(content, title=f"[{_SYS_TITLE_STYLE}]{title}[/]", border_style=_SYS_BORDER, box=box.ROUNDED))
    console.print()


def _sys_table(rows: list[tuple[str, str]], columns: tuple[str, str] = ("Size", "Path")) -> Table:
    """Build a sys-styled table for item listings."""
    t = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    t.add_column(columns[0], style="bold cyan")
    t.add_column(columns[1], style="white")
    for row in rows:
        t.add_row(*row)
    return t


def _sys_table_simple(rows: list[tuple[str, str]]) -> Table:
    """Two-column table without header."""
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column("", style="bold cyan")
    t.add_column("", style="white")
    for row in rows:
        t.add_row(*row)
    return t


def _du_blocks(path: Path) -> int:
    """Get du -s block count (512-byte blocks) for path."""
    try:
        r = subprocess.run(["du", "-s", str(path)], capture_output=True, text=True, check=True)
        return int(r.stdout.split()[0])
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return 0


def _du_human(path: Path) -> str:
    """Get du -sh human-readable size for path."""
    try:
        r = subprocess.run(["du", "-sh", str(path)], capture_output=True, text=True, check=True)
        return r.stdout.split()[0]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "?"


def _find_pycache() -> list[Path]:
    dirs = []
    for sp in SEARCH_PATHS:
        if not sp.exists():
            continue
        for d in sp.rglob("__pycache__"):
            if d.is_dir():
                dirs.append(d)
    return dirs


def _find_node_modules() -> list[Path]:
    dirs = []
    for sp in SEARCH_PATHS:
        if not sp.exists():
            continue
        for d in sp.rglob("node_modules"):
            if d.is_dir() and d.name == "node_modules" and len(d.relative_to(sp).parts) <= 5:
                if "node_modules" not in d.relative_to(sp).parts[:-1]:
                    dirs.append(d)
    return dirs


def _find_venvs() -> list[Path]:
    venvs = []
    search_paths = list(SEARCH_PATHS)
    if _MRTAMAKI_ROOT.exists() and _MRTAMAKI_ROOT not in search_paths:
        search_paths.append(_MRTAMAKI_ROOT)
    exclude = {"node_modules", "Library", ".Trash", ".git"}
    for sp in search_paths:
        if not sp.exists():
            continue
        for d in sp.rglob("*"):
            if not d.is_dir():
                continue
            try:
                rel = d.relative_to(sp)
            except ValueError:
                continue
            if len(rel.parts) > 5:
                continue
            if exclude & set(rel.parts):
                continue
            if d.name in VENV_NAMES or d.name.startswith("venv-"):
                if (d / "bin" / "activate").exists() and (d / "bin" / "python").exists():
                    venvs.append(d)
    return venvs


def _find_venvs_e5(search_root: Path) -> list[Path]:
    """Find venvs for e5 (venv-purge) - venv, .venv, env, pyenv only (no venv-*)."""
    venvs = []
    exclude = {"node_modules", "Library", ".Trash", "homebrew"}
    for d in search_root.rglob("*"):
        if not d.is_dir():
            continue
        try:
            rel = d.relative_to(search_root)
        except ValueError:
            continue
        if len(rel.parts) > 5:
            continue
        if exclude & set(rel.parts):
            continue
        if d.name not in VENV_NAMES:
            continue
        if not (d / "bin" / "activate").exists() or not (d / "bin" / "python").exists():
            continue
        try:
            r = subprocess.run(
                [str(d / "bin" / "python"), "-c",
                 "import sys; exit(0 if hasattr(sys,'real_prefix') or (hasattr(sys,'base_prefix') and sys.base_prefix!=sys.prefix) else 1)"],
                capture_output=True,
            )
            if r.returncode == 0:
                venvs.append(d)
        except Exception:
            pass
    return venvs


@app.command()
def pycache():
    """Clean __pycache__ directories (h1)."""
    dirs = _find_pycache()
    if not dirs:
        print_info("No __pycache__ directories found")
        return
    total_blocks = 0
    rows = []
    for d in dirs:
        size = _du_human(d)
        total_blocks += _du_blocks(d)
        display = str(d).replace(str(HOME), "~")
        rows.append((f"[yellow]{size:>6}[/yellow]", display))
    total_human = human_size(total_blocks)
    table = _sys_table(rows)
    _sys_panel("  __pycache__ Cleanup  ", table)
    console.print(f"  [cyan]Total: {total_human} • {len(dirs)} directories[/cyan]\n")
    if not confirm(f"Delete all {len(dirs)} __pycache__ directories?", "n"):
        print_info("Cancelled")
        return
    import shutil
    count = 0
    for d in dirs:
        display = str(d).replace(str(HOME), "~")
        try:
            shutil.rmtree(d)
            console.print(f"  [green]✓[/green] Removed {display}")
            count += 1
        except Exception:
            console.print(f"  [red]✗[/red] Failed  {display}")
    console.print()
    print_success(f"Deleted {count} / {len(dirs)} __pycache__ directories (freed {total_human})")


@app.command()
def browser():
    """Clear browser caches (h2)."""
    caches = {
        "Safari": HOME / "Library" / "Caches" / "com.apple.Safari",
        "Chrome": HOME / "Library" / "Caches" / "Google" / "Chrome",
        "Firefox": HOME / "Library" / "Caches" / "Firefox",
    }
    import shutil
    rows = []
    for name, path in caches.items():
        if path.exists():
            size = _du_human(path)
            rows.append((f"[yellow]{size:>6}[/yellow]", name))
    if not rows:
        print_info("No browser caches found")
        return
    table = _sys_table(rows, ("Size", "Cache"))
    _sys_panel("  Browser Cache Cleanup  ", table)
    if not confirm("Clear all browser caches?", "n"):
        print_info("Cancelled")
        return
    console.print()
    for name, path in caches.items():
        if path.exists():
            size = _du_human(path)
            try:
                shutil.rmtree(path)
                console.print(f"  [green]✓[/green] Cleared {name} cache ({size})")
            except Exception:
                console.print(f"  [red]✗[/red] Failed  {name} cache")
    console.print()
    print_success("Browser caches cleared")


@app.command("app")
def appcache():
    """Clear app caches (h3)."""
    cache_dir = HOME / "Library" / "Caches"
    if not cache_dir.exists():
        print_info("No cache directory found")
        return
    entries = [e for e in cache_dir.iterdir() if e.is_dir()]
    if not entries:
        print_info("No cache directories found")
        return
    total_size = _du_human(cache_dir)
    rows = []
    entry_sizes = {}
    for e in entries:
        size = _du_human(e)
        entry_sizes[e.name] = size
        rows.append((f"[yellow]{size:>6}[/yellow]", e.name))
    table = _sys_table(rows, ("Size", "Cache"))
    _sys_panel("  Application Cache Cleanup  ", table)
    console.print(f"  [cyan]Total: {total_size} • {len(entries)} directories[/cyan]\n")
    if not confirm("Clear all application caches?", "n"):
        print_info("Cancelled")
        return
    import shutil
    console.print()
    count = 0
    for e in entries:
        try:
            shutil.rmtree(e)
            console.print(f"  [green]✓[/green] Removed {e.name} ({entry_sizes[e.name]})")
            count += 1
        except Exception:
            console.print(f"  [red]✗[/red] Failed  {e.name}")
    console.print()
    print_success(f"Cleared {count} / {len(entries)} cache directories (was {total_size} total)")


@app.command()
def venv():
    """Clean venvs (h4)."""
    venvs = _find_venvs()
    if not venvs:
        print_info("No virtual environments found")
        return
    total_blocks = 0
    rows = []
    for v in venvs:
        size = _du_human(v)
        total_blocks += _du_blocks(v)
        display = str(v).replace(str(HOME), "~")
        py_ver = ""
        try:
            ver = subprocess.run([str(v / "bin" / "python"), "--version"], capture_output=True, text=True)
            if ver.returncode == 0:
                py_ver = f"  [dim]({ver.stdout.strip()})[/dim]"
        except Exception:
            pass
        rows.append((f"[yellow]{size:>6}[/yellow]", display + py_ver))
    total_human = human_size(total_blocks)
    table = _sys_table(rows)
    _sys_panel("  Virtual Environment Cleanup  ", table)
    console.print(f"  [cyan]Total: {total_human} • {len(venvs)} venvs[/cyan]\n")
    if not confirm(f"Delete all {len(venvs)} virtual environments?", "n"):
        print_info("Cancelled")
        return
    import shutil
    console.print()
    count = 0
    for v in venvs:
        display = str(v).replace(str(HOME), "~")
        try:
            shutil.rmtree(v)
            console.print(f"  [green]✓[/green] Removed {display}")
            count += 1
        except Exception:
            console.print(f"  [red]✗[/red] Failed  {display}")
    console.print()
    print_success(f"Deleted {count} / {len(venvs)} virtual environments")


@app.command()
def space():
    """Reclaimable space overview (h5)."""
    grand_total = 0
    rows = []

    pycache_dirs = _find_pycache()
    pycache_blocks = sum(_du_blocks(d) for d in pycache_dirs)
    grand_total += pycache_blocks
    rows.append((f"[yellow]{human_size(pycache_blocks):>8}[/yellow]", f"__pycache__ ({len(pycache_dirs)} dirs)"))

    browser_caches = [
        ("Safari", HOME / "Library" / "Caches" / "com.apple.Safari"),
        ("Chrome", HOME / "Library" / "Caches" / "Google" / "Chrome"),
        ("Firefox", HOME / "Library" / "Caches" / "Firefox"),
    ]
    for name, p in browser_caches:
        if p.exists():
            b = _du_blocks(p)
            grand_total += b
            rows.append((f"[cyan]{_du_human(p):>8}[/cyan]", name))

    derived = HOME / "Library" / "Developer" / "Xcode" / "DerivedData"
    if derived.exists():
        b = _du_blocks(derived)
        grand_total += b
        rows.append((f"[cyan]{_du_human(derived):>8}[/cyan]", "Xcode DerivedData"))
    else:
        rows.append(("[dim]—[/dim]", "Xcode DerivedData (not found)"))

    node_dirs = _find_node_modules()
    node_blocks = sum(_du_blocks(d) for d in node_dirs)
    grand_total += node_blocks
    rows.append((f"[cyan]{human_size(node_blocks):>8}[/cyan]", f"node_modules ({len(node_dirs)} dirs)"))

    venvs = _find_venvs()
    venv_blocks = sum(_du_blocks(v) for v in venvs)
    grand_total += venv_blocks
    venv_label = f"Virtual Environments ({len(venvs)} venvs)" if venvs else "Virtual Environments (none)"
    rows.append((f"[cyan]{human_size(venv_blocks):>8}[/cyan]", venv_label))

    trash = HOME / ".Trash"
    if trash.exists():
        b = _du_blocks(trash)
        grand_total += b
        rows.append((f"[cyan]{_du_human(trash):>8}[/cyan]", "Trash"))
    else:
        rows.append(("[dim]—[/dim]", "Trash (empty)"))

    table = _sys_table(rows, ("Size", "Category"))
    _sys_panel("  Reclaimable Space Overview  ", table)
    console.print(f"  [bold green]Total Reclaimable: {human_size(grand_total)}[/bold green]")
    console.print("  [dim]Use mt sys pycache, browser, etc. to clean individual categories[/dim]\n")


@app.command()
def xcode():
    """Clear Xcode DerivedData (h6)."""
    derived = HOME / "Library" / "Developer" / "Xcode" / "DerivedData"
    if not derived.exists():
        print_info("Xcode DerivedData not found (Xcode may not be installed)")
        return
    total_size = _du_human(derived)
    project_count = sum(1 for e in derived.iterdir() if e.is_dir())
    table = _sys_table_simple([
        ("Size", f"[yellow]{total_size}[/yellow]"),
        ("Project caches", str(project_count)),
    ])
    _sys_panel("  Xcode DerivedData Cleanup  ", table)
    if not confirm("Clear all DerivedData?", "n"):
        print_info("Cancelled")
        return
    import shutil
    for e in derived.iterdir():
        try:
            shutil.rmtree(e) if e.is_dir() else e.unlink()
        except Exception:
            pass
    print_success(f"Cleared DerivedData (freed {total_size})")


@app.command()
def node():
    """Clean node_modules directories (h7)."""
    dirs = _find_node_modules()
    if not dirs:
        print_info("No node_modules directories found")
        return
    total_blocks = 0
    rows = []
    for d in dirs:
        size = _du_human(d)
        total_blocks += _du_blocks(d)
        display = str(d).replace(str(HOME), "~")
        rows.append((f"[yellow]{size:>6}[/yellow]", display))
    total_human = human_size(total_blocks)
    table = _sys_table(rows)
    _sys_panel("  node_modules Cleanup  ", table)
    console.print(f"  [cyan]Total: {total_human} • {len(dirs)} directories[/cyan]\n")
    if not confirm(f"Delete all {len(dirs)} node_modules directories?", "n"):
        print_info("Cancelled")
        return
    import shutil
    console.print()
    count = 0
    for d in dirs:
        display = str(d).replace(str(HOME), "~")
        try:
            shutil.rmtree(d)
            console.print(f"  [green]✓[/green] Removed {display}")
            count += 1
        except Exception:
            console.print(f"  [red]✗[/red] Failed  {display}")
    console.print()
    print_success(f"Deleted {count} / {len(dirs)} node_modules directories (freed {total_human})")


@app.command()
def menu(result_file: Optional[str] = typer.Option(None, "--result-file")):
    """Interactive system cleaner TUI (h8/smenu)."""
    clean_dir = _MRTAMAKI_ROOT / "clean"
    script = clean_dir / "clean_menu.py"
    if not script.exists():
        print_error(f"clean_menu.py not found: {script}")
        raise typer.Exit(1)
    env = os.environ.copy()
    env["MRTAMAKI_DIR"] = str(_MRTAMAKI_ROOT)
    cmd = [sys.executable, str(script)]
    if result_file:
        cmd.extend(["--result-file", result_file])
    raise typer.Exit(subprocess.run(cmd, cwd=str(clean_dir), env=env).returncode)


@app.command()
def health():
    """Live system health dashboard (h9)."""
    status_dir = _MRTAMAKI_ROOT / "status"
    script = status_dir / "health_dashboard.py"
    if not script.exists():
        print_error(f"health_dashboard.py not found: {script}")
        raise typer.Exit(1)
    raise typer.Exit(subprocess.run([sys.executable, str(script)], cwd=str(status_dir)).returncode)


@app.command()
def dns():
    """Flush DNS cache (h10)."""
    table = _sys_table_simple([("Action", "Flush macOS DNS cache (dscacheutil + mDNSResponder)")])
    _sys_panel("  DNS Cache Flush  ", table)
    print_info("Flushing DNS cache...")
    try:
        subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=True, capture_output=True)
        subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True, capture_output=True)
        print_success("DNS cache cleared")
    except subprocess.CalledProcessError:
        print_error("Failed to clear DNS cache")
        raise typer.Exit(1)


@app.command()
def trash():
    """Empty trash."""
    trash_dir = HOME / ".Trash"
    if not trash_dir.exists():
        print_info("Trash directory not found")
        return
    items = list(trash_dir.iterdir())
    if not items:
        print_info("Trash is already empty")
        return
    total_size = _du_human(trash_dir)
    table = _sys_table_simple([
        ("Size", f"[yellow]{total_size}[/yellow]"),
        ("Items", str(len(items))),
    ])
    _sys_panel("  Empty Trash  ", table)
    if not confirm("Empty trash? This cannot be undone.", "n"):
        print_info("Cancelled")
        return
    import shutil
    for item in trash_dir.iterdir():
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        except Exception:
            pass
    print_success(f"Trash emptied (freed {total_size})")


@app.command("venv-purge")
def venv_purge(path: Optional[str] = typer.Argument(None)):
    """Find and purge venvs (e5)."""
    from mrtamaki._utils import confirm_destructive, prompt_with_validation, validate_input
    
    # Validate path if provided
    if path:
        is_valid, error_msg = validate_input(path, "path")
        if not is_valid:
            print_error(f"Invalid path: {error_msg}")
            print_info("Using home directory instead")
            search_root = HOME
        else:
            search_root = Path(path)
    else:
        search_root = HOME
    
    venvs = _find_venvs_e5(search_root)
    if not venvs:
        print_info("No virtual environments found")
        return
    
    total_blocks = 0
    rows = []
    for v in venvs:
        size = _du_human(v)
        total_blocks += _du_blocks(v)
        display = str(v).replace(str(HOME), "~")
        py_ver = ""
        try:
            ver = subprocess.run([str(v / "bin" / "python"), "--version"], capture_output=True, text=True)
            if ver.returncode == 0:
                py_ver = f"  [dim]({ver.stdout.strip()})[/dim]"
        except Exception:
            pass
        rows.append((f"[yellow]{size:>6}[/yellow]", display + py_ver))
    
    total_human = human_size(total_blocks)
    table = _sys_table(rows)
    _sys_panel("  Virtual Environment Purge (e5)  ", table)
    console.print(f"  [cyan]Scan path: {search_root}[/cyan]")
    console.print(f"  [cyan]Total: {total_human} • {len(venvs)} venvs[/cyan]\n")
    
    # Show warning about destructive operation
    print_warning("⚠  This operation will:")
    print_warning("   • Purge pip cache for each venv")
    print_warning("   • Uninstall all packages")
    print_warning("   • Delete the virtual environment directory")
    print_warning("   • This cannot be undone!")
    console.print()
    
    # Use enhanced confirmation
    if not confirm_destructive("Purge ALL virtual environments?", f"{len(venvs)} venvs"):
        print_info("Cleanup cancelled")
        return
    
    success = 0
    fail = 0
    skip_prefixes = ("/usr/", "/opt/homebrew/", "/System/", "/Library/")
    
    for v in venvs:
        vstr = str(v)
        if any(vstr.startswith(p) for p in skip_prefixes):
            print_warning(f"Skipping system path: {v}")
            fail += 1
            continue
        
        print_info(f"Processing: {v}")
        
        # Purge pip cache
        pip_cmd = v / "bin" / "pip"
        if pip_cmd.exists():
            print_info("  Purging pip cache...")
            subprocess.run([str(pip_cmd), "cache", "purge"], capture_output=True)
            
            # Uninstall packages
            print_info("  Uninstalling packages...")
            pkgs = subprocess.run([str(pip_cmd), "freeze"], capture_output=True, text=True)
            if pkgs.stdout.strip():
                packages = []
                for line in pkgs.stdout.strip().split("\n"):
                    pkg = line.split("==")[0] if "==" in line else line.split("@")[0]
                    if pkg:
                        packages.append(pkg)
                
                if packages:
                    # Uninstall in batches to avoid command line length issues
                    batch_size = 10
                    for i in range(0, len(packages), batch_size):
                        batch = packages[i:i + batch_size]
                        subprocess.run([str(pip_cmd), "uninstall", "-y"] + batch, capture_output=True)
        
        # Delete directory
        import shutil
        try:
            shutil.rmtree(v)
            print_success(f"  Removed: {v}")
            success += 1
        except Exception as e:
            print_error(f"  Failed to remove {v}: {e}")
            fail += 1
        
        console.print()
    
    # Summary
    summary_rows = [
        ("Total processed", str(len(venvs))),
        ("Successfully removed", f"[green]{success}[/green]"),
        ("Failed", f"[red]{fail}[/red]" if fail else str(fail)),
        ("Space reclaimed", total_human),
    ]
    summary_table = _sys_table_simple(summary_rows)
    _sys_panel("  Cleanup Summary  ", summary_table)
    
    if success:
        print_success(f"Virtual environment cleanup complete ({success}/{len(venvs)} successful)")
    else:
        print_warning("No virtual environments were removed")


@app.command()
def pip(venv_path: Optional[str] = typer.Argument(None)):
    """Pip purge — cache + packages (g7)."""
    target = venv_path or "system"
    if target == "system":
        pip_cmd = "pip3"
        try:
            subprocess.run([pip_cmd, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("pip3 not found")
            raise typer.Exit(1)
        table = _sys_table_simple([("Target", "system pip (--user)")])
        _sys_panel("  Pip Purge (g7)  ", table)
        pkgs = subprocess.run([pip_cmd, "list", "--user", "--format=freeze"], capture_output=True, text=True)
        if not pkgs.stdout.strip():
            print_info("No user-installed packages found")
            print_info("Clearing pip cache...")
            subprocess.run([pip_cmd, "cache", "purge"], capture_output=True)
            print_success("Pip cache cleared")
            return
        console.print(pkgs.stdout)
        console.print("")
        if not confirm("Uninstall all user packages and clear cache?", "n"):
            print_info("Cancelled")
            return
        print_info("Clearing pip cache...")
        subprocess.run([pip_cmd, "cache", "purge"], capture_output=True)
        print_info("Uninstalling user packages...")
        for line in pkgs.stdout.strip().split("\n"):
            pkg = line.split("==")[0] if "==" in line else line.split("@")[0]
            if pkg:
                subprocess.run([pip_cmd, "uninstall", "-y", pkg], capture_output=True)
    else:
        venv_pip = Path(target) / "bin" / "pip"
        if not venv_pip.exists():
            print_error(f"Venv pip not found: {venv_pip}")
            raise typer.Exit(1)
        table = _sys_table_simple([("Target", str(target))])
        _sys_panel("  Pip Purge (g7)  ", table)
        pkgs = subprocess.run([str(venv_pip), "freeze"], capture_output=True, text=True)
        if not pkgs.stdout.strip():
            print_info("No packages found in venv")
            subprocess.run([str(venv_pip), "cache", "purge"], capture_output=True)
            print_success("Pip cache cleared")
            return
        console.print(pkgs.stdout)
        console.print("")
        if not confirm("Uninstall all packages and clear cache?", "n"):
            print_info("Cancelled")
            return
        print_info("Clearing pip cache...")
        subprocess.run([str(venv_pip), "cache", "purge"], capture_output=True)
        print_info("Uninstalling packages...")
        for line in pkgs.stdout.strip().split("\n"):
            pkg = line.split("==")[0] if "==" in line else line.split("@")[0]
            if pkg:
                subprocess.run([str(venv_pip), "uninstall", "-y", pkg], capture_output=True)
    print_success("Pip purge complete")

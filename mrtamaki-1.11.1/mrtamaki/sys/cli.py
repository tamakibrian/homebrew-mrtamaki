"""System CLI: pycache, browser, app, venv, space, xcode, node, menu, health, dns (h1-h10, e5, g7)."""
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

from mrtamaki._utils import confirm, human_size, print_error, print_header, print_info, print_success, print_warning

app = typer.Typer(help="System tools: cleanup, health, DNS flush")

_MRTAMAKI_ROOT = Path(__file__).resolve().parents[2]
HOME = Path.home()
SEARCH_PATHS = [HOME / "Desktop", HOME / "Documents", HOME / "Downloads", HOME / "Projects"]
VENV_NAMES = ("venv", ".venv", "env", "pyenv")
VENV_PATTERNS = ["venv", ".venv", "env", "pyenv", "venv-*"]


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
    print_header("Clean __pycache__ Directories")
    dirs = _find_pycache()
    if not dirs:
        print_info("No __pycache__ directories found")
        return
    total_blocks = 0
    for d in dirs:
        size = _du_human(d)
        blocks = _du_blocks(d)
        total_blocks += blocks
        display = str(d).replace(str(HOME), "~")
        typer.echo(f"  [yellow]{size}[/yellow]  {display}")
    total_human = human_size(total_blocks)
    typer.echo(f"\n  [cyan]Total: {total_human}[/cyan]\n")
    if not confirm(f"Delete all {len(dirs)} __pycache__ directories?", "n"):
        print_info("Cancelled")
        return
    typer.echo("")
    count = 0
    for d in dirs:
        display = str(d).replace(str(HOME), "~")
        try:
            import shutil
            shutil.rmtree(d)
            typer.echo(f"  [green]✓[/green] Removed {display}")
            count += 1
        except Exception:
            typer.echo(f"  [red]✗[/red] Failed  {display}")
    typer.echo("")
    print_success(f"Deleted {count} / {len(dirs)} __pycache__ directories (freed {total_human})")


@app.command()
def browser():
    """Clear browser caches (h2)."""
    print_header("Clear Browser Caches")
    caches = {
        "Safari": HOME / "Library" / "Caches" / "com.apple.Safari",
        "Chrome": HOME / "Library" / "Caches" / "Google" / "Chrome",
        "Firefox": HOME / "Library" / "Caches" / "Firefox",
    }
    import shutil
    found = 0
    sizes = {}
    for name, path in caches.items():
        if path.exists():
            sizes[name] = _du_human(path)
            print_info(f"{name}: [yellow]{sizes[name]}[/yellow]")
            found += 1
    if not found:
        print_info("No browser caches found")
        return
    typer.echo("")
    if not confirm("Clear all browser caches?", "n"):
        print_info("Cancelled")
        return
    typer.echo("")
    for name, path in caches.items():
        if path.exists():
            try:
                shutil.rmtree(path)
                typer.echo(f"  [green]✓[/green] Cleared {name} cache ({sizes[name]})")
            except Exception:
                typer.echo(f"  [red]✗[/red] Failed  {name} cache")
    typer.echo("")
    print_success("Browser caches cleared")


@app.command("app")
def appcache():
    """Clear app caches (h3)."""
    print_header("Clear Application Cache")
    cache_dir = HOME / "Library" / "Caches"
    if not cache_dir.exists():
        print_info("No cache directory found")
        return
    total_size = _du_human(cache_dir)
    print_info(f"Total app cache: {total_size} ({cache_dir})\n")
    entries = [e for e in cache_dir.iterdir() if e.is_dir()]
    if not entries:
        print_info("No cache directories found")
        return
    entry_sizes = {}
    for e in entries:
        entry_sizes[e.name] = _du_human(e)
        typer.echo(f"  [yellow]{entry_sizes[e.name]}[/yellow]  {e.name}")
    typer.echo(f"\n  [cyan]{len(entries)} cache directories[/cyan]\n")
    if not confirm("Clear all application caches?", "n"):
        print_info("Cancelled")
        return
    typer.echo("")
    import shutil
    count = 0
    for e in entries:
        try:
            shutil.rmtree(e)
            typer.echo(f"  [green]✓[/green] Removed {e.name} ({entry_sizes[e.name]})")
            count += 1
        except Exception:
            typer.echo(f"  [red]✗[/red] Failed  {e.name}")
    typer.echo("")
    print_success(f"Cleared {count} / {len(entries)} cache directories (was {total_size} total)")


@app.command()
def venv():
    """Clean venvs (h4)."""
    print_header("Virtual Environments")
    venvs = _find_venvs()
    if not venvs:
        print_info("No virtual environments found")
        return
    print_info("Searching for virtual environments...\n")
    total_blocks = 0
    for v in venvs:
        size = _du_human(v)
        total_blocks += _du_blocks(v)
        display = str(v).replace(str(HOME), "~")
        typer.echo(f"  [yellow]{size}[/yellow]  {display}")
        try:
            ver = subprocess.run([str(v / "bin" / "python"), "--version"], capture_output=True, text=True)
            if ver.returncode == 0:
                typer.echo(f"       [cyan]{ver.stdout.strip()}[/cyan]")
        except Exception:
            pass
    total_human = human_size(total_blocks)
    typer.echo(f"\n  [cyan]Found {len(venvs)} virtual environments ({total_human} total)[/cyan]\n")
    if not confirm(f"Delete all {len(venvs)} virtual environments?", "n"):
        print_info("Cancelled")
        return
    typer.echo("")
    import shutil
    count = 0
    for v in venvs:
        display = str(v).replace(str(HOME), "~")
        try:
            shutil.rmtree(v)
            typer.echo(f"  [green]✓[/green] Removed {display}")
            count += 1
        except Exception:
            typer.echo(f"  [red]✗[/red] Failed  {display}")
    typer.echo("")
    print_success(f"Deleted {count} / {len(venvs)} virtual environments")


@app.command()
def space():
    """Reclaimable space overview (h5)."""
    print_header("Reclaimable Space Overview")
    grand_total = 0

    pycache_dirs = _find_pycache()
    pycache_blocks = sum(_du_blocks(d) for d in pycache_dirs)
    grand_total += pycache_blocks
    typer.echo("  [yellow]__pycache__[/yellow]")
    typer.echo(f"    {len(pycache_dirs)} directories, {human_size(pycache_blocks)}")
    typer.echo("")

    browser_caches = [
        ("Safari", HOME / "Library" / "Caches" / "com.apple.Safari"),
        ("Chrome", HOME / "Library" / "Caches" / "Google" / "Chrome"),
        ("Firefox", HOME / "Library" / "Caches" / "Firefox"),
    ]
    typer.echo("  [yellow]Browser Caches[/yellow]")
    for name, p in browser_caches:
        if p.exists():
            b = _du_blocks(p)
            grand_total += b
            typer.echo(f"    [cyan]{_du_human(p)}[/cyan]  {name}")
    typer.echo("")

    derived = HOME / "Library" / "Developer" / "Xcode" / "DerivedData"
    typer.echo("  [yellow]Xcode DerivedData[/yellow]")
    if derived.exists():
        b = _du_blocks(derived)
        grand_total += b
        typer.echo(f"    [cyan]{_du_human(derived)}[/cyan]")
    else:
        typer.echo("    (not found)")
    typer.echo("")

    node_dirs = _find_node_modules()
    node_blocks = sum(_du_blocks(d) for d in node_dirs)
    grand_total += node_blocks
    typer.echo("  [yellow]node_modules[/yellow]")
    typer.echo(f"    {len(node_dirs)} directories, {human_size(node_blocks)}")
    typer.echo("")

    venvs = _find_venvs()
    venv_blocks = sum(_du_blocks(v) for v in venvs)
    grand_total += venv_blocks
    typer.echo("  [yellow]Virtual Environments[/yellow]")
    for v in venvs:
        typer.echo(f"    [cyan]{_du_human(v)}[/cyan]  {str(v).replace(str(HOME), '~')}")
    if venvs:
        typer.echo(f"    {len(venvs)} venvs, {human_size(venv_blocks)} total")
    else:
        typer.echo("    (none found)")
    typer.echo("")

    trash = HOME / ".Trash"
    typer.echo("  [yellow]Trash[/yellow]")
    if trash.exists():
        b = _du_blocks(trash)
        grand_total += b
        typer.echo(f"    [cyan]{_du_human(trash)}[/cyan]")
    else:
        typer.echo("    (empty)")
    typer.echo("")

    typer.echo(f"  [green]Total Reclaimable: {human_size(grand_total)}[/green]")
    typer.echo("  [cyan]Use mt sys pycache, browser, etc. to clean individual categories[/cyan]")


@app.command()
def xcode():
    """Clear Xcode DerivedData (h6)."""
    print_header("Clear Xcode DerivedData")
    derived = HOME / "Library" / "Developer" / "Xcode" / "DerivedData"
    if not derived.exists():
        print_info("Xcode DerivedData not found (Xcode may not be installed)")
        return
    total_size = _du_human(derived)
    project_count = sum(1 for e in derived.iterdir() if e.is_dir())
    print_info(f"DerivedData size: [yellow]{total_size}[/yellow]")
    print_info(f"{project_count} project build caches\n")
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
    print_header("Clean node_modules")
    dirs = _find_node_modules()
    if not dirs:
        print_info("No node_modules directories found")
        return
    total_blocks = 0
    for d in dirs:
        size = _du_human(d)
        total_blocks += _du_blocks(d)
        display = str(d).replace(str(HOME), "~")
        typer.echo(f"  [yellow]{size}[/yellow]  {display}")
    total_human = human_size(total_blocks)
    typer.echo(f"\n  [cyan]Total: {total_human}[/cyan]\n")
    if not confirm(f"Delete all {len(dirs)} node_modules directories?", "n"):
        print_info("Cancelled")
        return
    typer.echo("")
    import shutil
    count = 0
    for d in dirs:
        display = str(d).replace(str(HOME), "~")
        try:
            shutil.rmtree(d)
            typer.echo(f"  [green]✓[/green] Removed {display}")
            count += 1
        except Exception:
            typer.echo(f"  [red]✗[/red] Failed  {display}")
    typer.echo("")
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
    print_header("Empty Trash")
    trash_dir = HOME / ".Trash"
    if not trash_dir.exists():
        print_info("Trash directory not found")
        return
    items = list(trash_dir.iterdir())
    if not items:
        print_info("Trash is already empty")
        return
    total_size = _du_human(trash_dir)
    print_info(f"Trash size: [yellow]{total_size}[/yellow] ({len(items)} items)\n")
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
    print_success("Trash emptied (freed " + total_size + ")")


@app.command("venv-purge")
def venv_purge(path: Optional[str] = typer.Argument(None)):
    """Find and purge venvs (e5)."""
    search_root = Path(path) if path else HOME
    print_header("Virtual Environment Cleanup with Dependency Purge")
    print_info(f"Scanning for virtual environments under: {search_root}")
    venvs = _find_venvs_e5(search_root)
    if not venvs:
        print_info("No virtual environments found")
        return
    print_info(f"Found {len(venvs)} virtual environments:")
    typer.echo("")
    for v in venvs:
        size = _du_human(v)
        typer.echo(f"  - {v} ({size})")
    typer.echo("")
    if not confirm("Purge dependencies and delete ALL of these virtual environments?", "n"):
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
        pip_cmd = v / "bin" / "pip"
        if pip_cmd.exists():
            subprocess.run([str(pip_cmd), "cache", "purge"], capture_output=True)
            pkgs = subprocess.run([str(pip_cmd), "freeze"], capture_output=True, text=True)
            if pkgs.stdout.strip():
                for line in pkgs.stdout.strip().split("\n"):
                    pkg = line.split("==")[0] if "==" in line else line.split("@")[0]
                    if pkg:
                        subprocess.run([str(pip_cmd), "uninstall", "-y", pkg], capture_output=True)
        import shutil
        try:
            shutil.rmtree(v)
            print_success(f"Removed: {v}")
            success += 1
        except Exception:
            print_error(f"Failed to remove: {v}")
            fail += 1
        typer.echo("")
    print_header("Cleanup Summary")
    typer.echo(f"  Total processed: {len(venvs)}")
    typer.echo(f"  Successful:      {success}")
    typer.echo(f"  Failed:          {fail}")
    if success:
        print_success("Virtual environment cleanup complete")


@app.command()
def pip(venv_path: Optional[str] = typer.Argument(None)):
    """Pip purge — cache + packages (g7)."""
    print_header("Pip Purge")
    target = venv_path or "system"
    if target == "system":
        pip_cmd = "pip3"
        try:
            subprocess.run([pip_cmd, "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("pip3 not found")
            raise typer.Exit(1)
        print_info("Target: system pip")
        pkgs = subprocess.run([pip_cmd, "list", "--user", "--format=freeze"], capture_output=True, text=True)
        if not pkgs.stdout.strip():
            print_info("No user-installed packages found")
            print_info("Clearing pip cache...")
            subprocess.run([pip_cmd, "cache", "purge"], capture_output=True)
            print_success("Pip cache cleared")
            return
        typer.echo(pkgs.stdout)
        typer.echo("")
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
        print_info(f"Target: {target}")
        pkgs = subprocess.run([str(venv_pip), "freeze"], capture_output=True, text=True)
        if not pkgs.stdout.strip():
            print_info("No packages found in venv")
            subprocess.run([str(venv_pip), "cache", "purge"], capture_output=True)
            print_success("Pip cache cleared")
            return
        typer.echo(pkgs.stdout)
        typer.echo("")
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

"""File CLI: zshrc, search, mkdir, open-last, large, tempdir, backup, desktop, tree, bookmarks (f command)."""
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from mrtamaki._utils import print_error, print_info, print_success, print_warning

app = typer.Typer(help="File operations: search, tree, bookmarks, backup")

BOOKMARKS_FILE = Path.home() / ".config" / "mrtamaki" / "bookmarks.json"
MAX_FILE_SIZE = "100M"


def _get_bookmarks() -> dict[str, str]:
    """Load bookmarks from JSON file."""
    if not BOOKMARKS_FILE.exists():
        return {}
    try:
        with open(BOOKMARKS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_bookmarks(bookmarks: dict[str, str]) -> None:
    """Save bookmarks to JSON file."""
    BOOKMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BOOKMARKS_FILE, "w") as f:
        json.dump(bookmarks, f, indent=2)


def _sanitize_bookmark_name(name: str) -> str:
    """Sanitize bookmark name to alphanumeric, underscore, dash only."""
    return re.sub(r"[^\w\-]", "", name)


@app.command()
def zshrc():
    """Edit .zshrc with backup (f --ez)."""
    zshrc_path = Path.home() / ".zshrc"
    if not zshrc_path.exists():
        print_error(".zshrc not found")
        raise typer.Exit(1)

    backup_dir = Path.home() / "Documents" / "zshrc_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = backup_dir / f"zshrc_backup_{timestamp}"

    shutil.copy2(zshrc_path, backup_file)
    print_success(f"Backup created: {backup_file}")

    editor = os.environ.get("EDITOR", "nano")
    subprocess.run([editor, str(zshrc_path)])
    print_info("Run 'exec zsh' to apply changes")


@app.command()
def search(
    term: str = typer.Argument(...),
    directory: Optional[str] = typer.Option(None, "--directory", "-d", "-D"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n", "-N"),
):
    """Recursive file search (f --s)."""
    target = Path(directory).resolve() if directory else Path.cwd()
    if not target.is_dir():
        print_error(f"Directory not found: {target}")
        raise typer.Exit(1)

    dest_label = f" in {target}" if directory else ""
    limit_label = f" (max {limit})" if limit else ""
    print_info(f"Searching for: {term}{dest_label}{limit_label}")

    cmd = ["grep", "-rnwF", "-e", term, str(target)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(target))
        lines = result.stdout.strip().split("\n") if result.stdout else []
        if limit:
            lines = lines[:limit]
        for line in lines:
            typer.echo(line)
        if not lines:
            print_warning("No matches found")
    except FileNotFoundError:
        print_error("grep not found")
        raise typer.Exit(1)


@app.command()
def mkdir(dir_name: str = typer.Argument(...)):
    """Make directory and print path for cd (f --m). Prints path only."""
    path = Path(dir_name).resolve()
    try:
        path.mkdir(parents=True, exist_ok=True)
        typer.echo(str(path))
    except OSError as e:
        print_error(f"Failed to create directory: {e}")
        raise typer.Exit(1)


@app.command("open-last")
def open_last(directory: Optional[str] = typer.Option(None, "--directory", "-d")):
    """Open last modified file (f --o)."""
    target = Path(directory).resolve() if directory else Path.cwd()
    if not target.is_dir():
        print_error(f"Directory not found: {target}")
        raise typer.Exit(1)

    files = [f for f in target.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        print_error("No files in current directory")
        raise typer.Exit(1)

    latest = max(files, key=lambda p: p.stat().st_mtime)
    editor = os.environ.get("EDITOR", "vim")
    print_info(f"Opening: {latest.name}")
    subprocess.run([editor, str(latest)])


def _format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string."""
    for unit, suffix in [(1024**3, "G"), (1024**2, "M"), (1024, "K")]:
        if size_bytes >= unit:
            return f"{size_bytes / unit:.1f}{suffix}"
    return f"{size_bytes}B"


@app.command()
def large(
    directory: Optional[str] = typer.Option(None, "--directory", "-d"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n"),
):
    """Find large files >100M (f --l)."""
    target = Path(directory).resolve() if directory else Path.cwd()
    if not target.is_dir():
        print_error(f"Directory not found: {target}")
        raise typer.Exit(1)

    limit_label = f" (top {limit})" if limit else ""
    print_info(f"Searching for files larger than {MAX_FILE_SIZE}{limit_label}...")

    cmd = ["find", str(target), "-type", "f", "-size", f"+{MAX_FILE_SIZE}", "-print0"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=False)
        paths = result.stdout.decode().rstrip("\0").split("\0") if result.stdout else []
        paths = [p for p in paths if p]
    except FileNotFoundError:
        print_error("find not found")
        raise typer.Exit(1)

    files_with_size = []
    for p in paths:
        try:
            size = Path(p).stat().st_size
            files_with_size.append((size, p))
        except OSError:
            pass
    files_with_size.sort(key=lambda x: x[0], reverse=True)
    if limit:
        files_with_size = files_with_size[:limit]

    for size, path in files_with_size:
        typer.echo(f"{_format_size(size)}\t{path}")
    if not files_with_size:
        print_info("No large files found")


@app.command()
def tempdir():
    """Create temp dir and print path (f --t). Prints path only."""
    tmpdir = tempfile.mkdtemp()
    typer.echo(tmpdir)


@app.command()
def backup(file_path: str = typer.Argument(...)):
    """Backup file with timestamp (f --b)."""
    filename = Path(file_path).name
    base = Path.cwd() / filename
    if not base.exists() or not base.is_file():
        print_error(f"File not found in current directory: {filename}")
        raise typer.Exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{base.stem}_backup_{timestamp}{base.suffix}"
    backup_path = base.parent / backup_name
    shutil.copy2(base, backup_path)
    print_success(f"Backup created: {backup_path}")


@app.command()
def desktop(name: Optional[str] = typer.Argument(None)):
    """Create timestamped folder on Desktop (f --d)."""
    folder_name = _sanitize_bookmark_name(name or "folder") or "folder"
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dir_path = Path.home() / "Desktop" / f"{timestamp}_{folder_name}"
    dir_path.mkdir(parents=True, exist_ok=True)
    print_success(f"Created: {dir_path}")


@app.command()
def tree(
    depth: Optional[int] = typer.Argument(None),
    directory: Optional[str] = typer.Option(None, "--directory", "-d"),
    limit: Optional[int] = typer.Option(None, "--limit", "-n"),
):
    """Directory tree (f --tr)."""
    from rich.console import Console
    from rich.tree import Tree

    target = Path(directory).resolve() if directory else Path.cwd()
    depth_val = depth or limit or 2
    if not target.is_dir():
        print_error(f"Directory not found: {target}")
        raise typer.Exit(1)

    print_info(f"Tree: {target} (depth {depth_val})")

    def build_tree(path: Path, tree: Tree, max_depth: int, current: int = 0) -> None:
        if current >= max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            tree.add("[red]Permission denied[/]")
            return
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                branch = tree.add(f"[bold cyan]{entry.name}/[/]")
                build_tree(entry, branch, max_depth, current + 1)
            else:
                ext = entry.suffix.lower()
                if ext in (".py", ".js", ".ts", ".sh", ".zsh"):
                    style = "green"
                elif ext in (".md", ".txt", ".json", ".yaml", ".yml"):
                    style = "yellow"
                elif ext in (".jpg", ".png", ".gif", ".svg"):
                    style = "magenta"
                else:
                    style = "white"
                tree.add(f"[{style}]{entry.name}[/]")

    console = Console()
    tree_obj = Tree(f"[bold blue]{target}[/]", guide_style="bright_black")
    build_tree(target, tree_obj, depth_val)
    console.print(tree_obj)


@app.command("bookmark-add")
def bookmark_add(name: Optional[str] = typer.Argument(None)):
    """Add current directory to bookmarks (f --ba)."""
    current_dir = str(Path.cwd())
    resolved_name = name or typer.prompt("Bookmark name")
    resolved_name = _sanitize_bookmark_name(resolved_name)
    if not resolved_name:
        print_error("Invalid bookmark name")
        raise typer.Exit(1)

    bookmarks = _get_bookmarks()
    bookmarks[resolved_name] = current_dir
    _save_bookmarks(bookmarks)
    print_success(f"Bookmarked '{resolved_name}' -> {current_dir}")


@app.command("bookmark-go")
def bookmark_go(name: Optional[str] = typer.Argument(None)):
    """Go to bookmark — prints path only for shell cd (f --bg)."""
    bookmarks = _get_bookmarks()
    if not bookmarks:
        print_error("No bookmarks saved. Use 'mt file bookmark-add' to add one.")
        raise typer.Exit(1)

    resolved_name = name
    if not resolved_name:
        for k, v in bookmarks.items():
            typer.echo(f"  {k} -> {v}")
        resolved_name = typer.prompt("Bookmark name")

    path = bookmarks.get(resolved_name)
    if not path:
        print_error(f"Bookmark not found: {resolved_name}")
        raise typer.Exit(1)
    if not Path(path).is_dir():
        print_error(f"Directory no longer exists: {path}")
        raise typer.Exit(1)
    typer.echo(path)


@app.command("bookmark-list")
def bookmark_list():
    """List all bookmarks (f --bl)."""
    bookmarks = _get_bookmarks()
    if not bookmarks:
        print_info("No bookmarks saved.")
        return
    print_info("Bookmarks:")
    for k, v in bookmarks.items():
        typer.echo(f"  {k} -> {v}")


@app.command("bookmark-del")
def bookmark_del(name: Optional[str] = typer.Argument(None)):
    """Delete a bookmark (f --bd)."""
    bookmarks = _get_bookmarks()
    if not bookmarks:
        print_error("No bookmarks saved.")
        raise typer.Exit(1)

    resolved_name = name
    if not resolved_name:
        for k, v in bookmarks.items():
            typer.echo(f"  {k} -> {v}")
        resolved_name = typer.prompt("Bookmark name to delete")

    if resolved_name not in bookmarks:
        print_error(f"Bookmark not found: {resolved_name}")
        raise typer.Exit(1)
    del bookmarks[resolved_name]
    _save_bookmarks(bookmarks)
    print_success(f"Deleted bookmark: {resolved_name}")

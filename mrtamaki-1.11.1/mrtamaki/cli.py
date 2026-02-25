"""mrtamaki CLI — proxy, IP, system, lookup, file tools."""
import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

from mrtamaki import __version__
from mrtamaki.file.cli import app as file_app
from mrtamaki.ip.cli import app as ip_app
from mrtamaki.lookup.cli import app as lookup_app
from mrtamaki.proxy.cli import app as proxy_app
from mrtamaki.sys.cli import app as sys_app
from mrtamaki._utils import print_info, print_error, print_success, print_warning

app = typer.Typer(
    name="mt",
    help="mrtamaki CLI — proxy, IP, system, lookup, file tools",
    no_args_is_help=False,
    invoke_without_command=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)

app.add_typer(proxy_app, name="proxy")
app.add_typer(ip_app, name="ip")
app.add_typer(sys_app, name="sys")
app.add_typer(lookup_app, name="lookup")
app.add_typer(file_app, name="file")


def _unified_help() -> None:
    """Print unified help menu for mt / mrtamaki (all commands and f flags)."""
    from rich import box
    
    try:
        from mrtamaki.ui_components import ui
        use_ui = True
    except ImportError:
        use_ui = False
    
    console = Console()
    sections = []

    # ─── Proxy ───
    proxy_rows = [
        ["a1", "Proxy: gen, -u UI, -b bind, -l list, --clean"],
        ["", "  (mt proxy gen [city] [-s] [-b <url>] [-l] [--clean])"],
    ]
    sections.append(("Proxy", "green", proxy_rows))

    # ─── IP ───
    ip_rows = [
        ["c3", "Test proxy on port → IP + DNS leak"],
        ["", "  (mt ip test [port])"],
        ["d4", "Scamalytics IP reputation"],
        ["", "  (mt ip check [ip])"],
        ["d6", "DNS leak test"],
        ["", "  (mt ip dnsleak [port])"],
        ["d7", "IPing.cc lookup"],
        ["", "  (mt ip iping [ip])"],
    ]
    sections.append(("IP", "cyan", ip_rows))

    # ─── Lookup ───
    lookup_rows = [
        ["d5 / found / 1l", "1Lookup interactive menu"],
        ["", "  (mt lookup)"],
        ["iplookup", "IP lookup"],
        ["", "  (mt lookup ip <ip>)"],
        ["everify", "Email verification"],
        ["", "  (mt lookup email <email>)"],
        ["eappend / reappend / ripappend", "1Lookup append APIs"],
    ]
    sections.append(("Lookup", "magenta", lookup_rows))

    # ─── System ───
    sys_rows = [
        ["h1", "Clean __pycache__"],
        ["", "  (mt sys pycache)"],
        ["h2", "Clear browser caches"],
        ["", "  (mt sys browser)"],
        ["h3", "Clear app caches"],
        ["", "  (mt sys app)"],
        ["h4", "Clean venvs"],
        ["", "  (mt sys venv)"],
        ["h5", "Reclaimable space"],
        ["", "  (mt sys space)"],
        ["h6", "Clear Xcode DerivedData"],
        ["", "  (mt sys xcode)"],
        ["h7", "Clean node_modules"],
        ["", "  (mt sys node)"],
        ["h8 / smenu / clean", "System cleaner TUI"],
        ["", "  (mt sys menu)"],
        ["h9 / health", "Live health dashboard"],
        ["", "  (mt sys health)"],
        ["h10 / flushdns", "Flush DNS cache"],
        ["", "  (mt sys dns)"],
        ["e5", "Find & clean venvs"],
        ["", "  (mt sys venv-purge [path])"],
        ["g7", "Pip purge cache + packages"],
        ["", "  (mt sys pip [venv])"],
    ]
    sections.append(("System", "blue", sys_rows))

    # ─── File (f) ───
    file_rows = [
        ["f --ez", "Edit ~/.zshrc with backup"],
        ["f --s <term>", "Recursive file search (-D dir, -N limit)"],
        ["f --m [dir]", "Make directory and cd"],
        ["f --o [-d dir]", "Open last modified file"],
        ["f --l [-D dir] [-N n]", "Find large files (>100M)"],
        ["f --b <file>", "Backup file with timestamp"],
        ["f --d [name]", "Timestamped folder on Desktop"],
        ["f --tr [-D dir] [-N depth]", "Directory tree"],
        ["f --ba [name]", "Bookmark: add current dir"],
        ["f --bg [name]", "Bookmark: go"],
        ["f --bl", "Bookmark: list"],
        ["f --bd [name]", "Bookmark: delete"],
        ["f --t", "Create temp dir and cd"],
        ["f --h", "File help (mt file --help)"],
    ]
    sections.append(("File (f)", "yellow", file_rows))

    # ─── Theme & misc ───
    misc_rows = [
        ["tt", "Toggle theme (cycle); tt --help"],
        ["cc", "Clear screen"],
        ["mt --version", "Show version"],
        ["mt --help", "Show this help"],
    ]
    sections.append(("Theme & Misc", "white", misc_rows))

    # Create columns for better layout
    column_tables = []
    
    for title, color, rows in sections:
        if use_ui:
            table = ui.create_table(["Command", "Description"], rows)
            panel = ui.create_panel(table, title, border_style=color)
            column_tables.append(panel)
        else:
            # Fallback
            table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
            table.add_column("Command", style=f"bold {color}", no_wrap=True)
            table.add_column("Description", style="white")
            
            for command, description in rows:
                table.add_row(command, description)
            
            panel = Panel(
                table,
                title=f"[bold {color}]{title}[/]",
                border_style=color,
                box=box.ROUNDED,
                padding=(0, 1),
            )
            column_tables.append(panel)
    
    # Display in columns for better use of screen space
    console.print()
    console.print(
        Panel.fit(
            Columns(column_tables, equal=True, expand=True),
            title=f"[bold]mrtamaki v{__version__}[/] — unified help",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 1),
        )
    )
    console.print()
    
    # Quick start tips
    tips = [
        "💡 Tip: Use 'mt <command> --help' for detailed help on any command",
        "💡 Tip: Most destructive operations ask for confirmation",
        "💡 Tip: Press Ctrl+C to cancel any operation",
        "💡 Tip: Use 'tt' to cycle through themes in your shell",
    ]
    
    console.print("[dim]Quick Tips:[/dim]")
    for tip in tips:
        console.print(f"  {tip}")


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
):
    """mrtamaki — Zsh toolkit as Python CLI. Run 'mt' or 'mt help' for unified help."""
    if version:
        from mrtamaki import __version__
        print_success(f"mrtamaki v{__version__}")
        raise typer.Exit(0)
    
    if ctx.invoked_subcommand is None:
        _unified_help()
        raise typer.Exit(0)


@app.command("help")
def help_cmd():
    """Show unified help (all commands and f flags)."""
    _unified_help()


@app.command("version")
def version_cmd():
    """Show version information."""
    from mrtamaki import __version__
    print_success(f"mrtamaki v{__version__}")
    
    # Show Python version
    import sys
    print_info(f"Python {sys.version.split()[0]}")
    
    # Show system info
    import platform
    print_info(f"Platform: {platform.system()} {platform.release()}")

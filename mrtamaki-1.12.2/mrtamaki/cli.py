"""mrtamaki CLI — proxy, IP, system, lookup, file tools."""
import typer
from rich.console import Console
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
        ["mt proxy", "Proxy converter TUI"],
        ["mt proxy <city>", "Generate proxy (provider menu)"],
        ["mt proxy -s <city>", "Speed run: gen + bind + test"],
        ["mt proxy -s <city> <n> --check", "Bulk: bind N + run checks"],
        ["mt proxy -b <url>", "Bind a proxy URL"],
        ["mt proxy -p <port>", "Test proxy on port"],
        ["mt proxy -l / --clean", "List or clean bound proxies"],
    ]
    sections.append(("Proxy", "green", proxy_rows))

    # ─── IP ───
    ip_rows = [
        ["mt ip test [port]", "Test proxy/system IP + DNS leak"],
        ["mt ip check [ip]", "Scamalytics IP reputation"],
        ["mt ip dnsleak [port]", "DNS leak test"],
        ["mt ip iping [ip]", "IPing.cc lookup"],
    ]
    sections.append(("IP", "cyan", ip_rows))

    # ─── Lookup ───
    lookup_rows = [
        ["mt lookup", "1Lookup interactive menu"],
        ["mt lookup ip <ip>", "IP lookup"],
        ["mt lookup email <email>", "Email verification"],
        ["mt lookup eappend", "Find email from person info"],
        ["mt lookup reappend", "Reverse email lookup"],
        ["mt lookup ripappend", "Reverse IP lookup"],
    ]
    sections.append(("Lookup", "magenta", lookup_rows))

    # ─── System ───
    sys_rows = [
        ["mt sys pycache", "Clean __pycache__"],
        ["mt sys browser", "Clear browser caches"],
        ["mt sys app", "Clear app caches"],
        ["mt sys venv", "Clean venvs"],
        ["mt sys space", "Reclaimable disk space"],
        ["mt sys xcode", "Clear Xcode DerivedData"],
        ["mt sys node", "Clean node_modules"],
        ["mt sys menu", "System cleaner TUI"],
        ["mt sys health", "Live health dashboard"],
        ["mt sys dns", "Flush DNS cache"],
        ["mt sys venv-purge [path]", "Find & purge venvs"],
        ["mt sys pip [venv]", "Pip purge cache + packages"],
    ]
    sections.append(("System", "blue", sys_rows))

    # ─── File ───
    file_rows = [
        ["mt file zshrc", "Edit ~/.zshrc with backup"],
        ["mt file search <term>", "Recursive file search"],
        ["mt file mkdir [dir]", "Make directory and cd"],
        ["mt file open-last", "Open last modified file"],
        ["mt file large", "Find large files (>100M)"],
        ["mt file backup <file>", "Backup file with timestamp"],
        ["mt file desktop [name]", "Timestamped folder on Desktop"],
        ["mt file tree [depth]", "Directory tree"],
        ["mt file tempdir", "Create temp dir and cd"],
        ["mt file bookmark-add", "Bookmark current dir"],
        ["mt file bookmark-go", "Go to bookmark"],
        ["mt file bookmark-list", "List bookmarks"],
        ["mt file bookmark-del", "Delete bookmark"],
    ]
    sections.append(("File", "yellow", file_rows))

    # ─── Theme & misc ───
    misc_rows = [
        ["tt", "Toggle theme (cycle); tt --help"],
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


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(app())

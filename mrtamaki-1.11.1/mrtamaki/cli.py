"""mrtamaki CLI — proxy, IP, system, lookup, file tools."""
import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from mrtamaki import __version__
from mrtamaki.file.cli import app as file_app
from mrtamaki.ip.cli import app as ip_app
from mrtamaki.lookup.cli import app as lookup_app
from mrtamaki.proxy.cli import app as proxy_app
from mrtamaki.sys.cli import app as sys_app

app = typer.Typer(
    name="mt",
    help="mrtamaki CLI — proxy, IP, system, lookup, file tools",
    no_args_is_help=False,
    invoke_without_command=True,
)

app.add_typer(proxy_app, name="proxy")
app.add_typer(ip_app, name="ip")
app.add_typer(sys_app, name="sys")
app.add_typer(lookup_app, name="lookup")
app.add_typer(file_app, name="file")


def _unified_help() -> None:
    """Print unified help menu for mt / mrtamaki (all commands and f flags)."""
    from rich import box

    console = Console()
    sections = []

    # ─── Proxy ───
    t1 = Table.grid(expand=True)
    t1.add_column(style="bold green", no_wrap=True)
    t1.add_column(style="white")
    t1.add_row("a1", "Proxy: gen, -u UI, -b bind, -l list, --clean  (mt proxy gen [city] [-s] [-b <url>] [-l] [--clean])")
    sections.append(("[bold green]Proxy[/]", t1))

    # ─── IP ───
    t2 = Table.grid(expand=True)
    t2.add_column(style="bold cyan", no_wrap=True)
    t2.add_column(style="white")
    t2.add_row("c3", "Test proxy on port → IP + DNS leak  (mt ip test [port])")
    t2.add_row("d4", "Scamalytics IP reputation  (mt ip check [ip])")
    t2.add_row("d6", "DNS leak test  (mt ip dnsleak [port])")
    t2.add_row("d7", "IPing.cc lookup  (mt ip iping [ip])")
    sections.append(("[bold cyan]IP[/]", t2))

    # ─── Lookup ───
    t3 = Table.grid(expand=True)
    t3.add_column(style="bold magenta", no_wrap=True)
    t3.add_column(style="white")
    t3.add_row("d5 / found / 1l", "1Lookup interactive menu  (mt lookup)")
    t3.add_row("iplookup", "IP lookup  (mt lookup ip <ip>)")
    t3.add_row("everify", "Email verification  (mt lookup email <email>)")
    t3.add_row("eappend / reappend / ripappend", "1Lookup append APIs")
    sections.append(("[bold magenta]Lookup[/]", t3))

    # ─── System ───
    t4 = Table.grid(expand=True)
    t4.add_column(style="bold blue", no_wrap=True)
    t4.add_column(style="white")
    t4.add_row("h1", "Clean __pycache__  (mt sys pycache)")
    t4.add_row("h2", "Clear browser caches  (mt sys browser)")
    t4.add_row("h3", "Clear app caches  (mt sys app)")
    t4.add_row("h4", "Clean venvs  (mt sys venv)")
    t4.add_row("h5", "Reclaimable space  (mt sys space)")
    t4.add_row("h6", "Clear Xcode DerivedData  (mt sys xcode)")
    t4.add_row("h7", "Clean node_modules  (mt sys node)")
    t4.add_row("h8 / smenu / clean", "System cleaner TUI  (mt sys menu)")
    t4.add_row("h9 / health", "Live health dashboard  (mt sys health)")
    t4.add_row("h10 / flushdns", "Flush DNS cache  (mt sys dns)")
    t4.add_row("e5", "Find & clean venvs  (mt sys venv-purge [path])")
    t4.add_row("g7", "Pip purge cache + packages  (mt sys pip [venv])")
    sections.append(("[bold blue]System[/]", t4))

    # ─── File (f) ───
    t5 = Table.grid(expand=True)
    t5.add_column(style="bold yellow", no_wrap=True)
    t5.add_column(style="white")
    t5.add_row("f --ez", "Edit ~/.zshrc with backup")
    t5.add_row("f --s <term>", "Recursive file search  (-D dir, -N limit)")
    t5.add_row("f --m [dir]", "Make directory and cd")
    t5.add_row("f --o [-d dir]", "Open last modified file")
    t5.add_row("f --l [-D dir] [-N n]", "Find large files (>100M)")
    t5.add_row("f --b <file>", "Backup file with timestamp")
    t5.add_row("f --d [name]", "Timestamped folder on Desktop")
    t5.add_row("f --tr [-D dir] [-N depth]", "Directory tree")
    t5.add_row("f --ba [name]", "Bookmark: add current dir")
    t5.add_row("f --bg [name]", "Bookmark: go")
    t5.add_row("f --bl", "Bookmark: list")
    t5.add_row("f --bd [name]", "Bookmark: delete")
    t5.add_row("f --t", "Create temp dir and cd")
    t5.add_row("f --h", "File help  (mt file --help)")
    sections.append(("[bold yellow]File (f)[/]", t5))

    # ─── Theme & misc ───
    t6 = Table.grid(expand=True)
    t6.add_column(style="bold white", no_wrap=True)
    t6.add_column(style="white")
    t6.add_row("tt", "Toggle theme (cycle); tt --help")
    t6.add_row("cc", "Clear screen")
    sections.append(("[bold white]Theme & misc[/]", t6))

    # ─── Module help ───
    t7 = Table.grid(expand=True)
    t7.add_column(style="dim", no_wrap=True)
    t7.add_column(style="white")
    t7.add_row("mt proxy --help", "Proxy options (gen, -u, -b, -l, -s, --check, ...)")
    t7.add_row("mt ip --help", "IP test, check, dnsleak, iping")
    t7.add_row("mt sys --help", "System cleanup & health")
    t7.add_row("mt file --help", "File operations & bookmarks")
    t7.add_row("mt lookup", "1Lookup menu (or mt lookup ip/email/...)")
    sections.append(("[bold]Module help[/]", t7))

    # Build a single renderable so tables render inside the panel
    parts = []
    for title, table in sections:
        parts.append(Text.from_markup(title))
        parts.append(table)
        parts.append(Text(""))
    content = Group(*parts)

    console.print()
    console.print(
        Panel(
            content,
            title=f"[bold]mrtamaki v{__version__}[/] — unified help",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    console.print()


@app.callback()
def main(ctx: typer.Context):
    """mrtamaki — Zsh toolkit as Python CLI. Run 'mt' or 'mt help' for unified help."""
    if ctx.invoked_subcommand is None:
        _unified_help()
        raise typer.Exit(0)


@app.command("help")
def help_cmd():
    """Show unified help (all commands and f flags)."""
    _unified_help()

"""mrtamaki CLI — proxy, IP, system, lookup, file tools."""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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


def _command_tree() -> None:
    """Print compact command tree for mt / mrtamaki."""
    console = Console()
    table = Table.grid(expand=True)
    table.add_column(style="bold cyan")
    table.add_column(style="white")

    table.add_row("Proxy:", "a1 (gen menu) | b2 (convert)  (mt proxy gen|convert)")
    table.add_row("IP:", "c3 d4 d6 d7  (mt ip <action>)")
    table.add_row("Lookup:", "d5 found 1l  (mt lookup)")
    table.add_row("System:", "h1-h7 h8 h9 h10 e5 g7  (mt sys <action>)")
    table.add_row("File:", "f --<flag>  (mt file <action>)")
    table.add_row("Theme:", "tt  (mt theme)")
    table.add_row("", "")
    table.add_row("Shortcuts", "a1, b2, h8, smenu, health, flushdns, etc.")
    table.add_row("Help", "mt proxy, mt sys, mt ip, mt file  — module help")
    table.add_row("", "mt --help  — full CLI help")

    console.print()
    console.print(
        Panel(
            table,
            title=f"[bold]mrtamaki v{__version__}[/] — Command tree",
            border_style="blue",
        )
    )
    console.print()


@app.callback()
def main(ctx: typer.Context):
    """mrtamaki — Zsh toolkit as Python CLI. Run 'mt' for command tree."""
    if ctx.invoked_subcommand is None:
        _command_tree()
        raise typer.Exit(0)

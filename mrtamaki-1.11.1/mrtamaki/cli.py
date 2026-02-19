"""mrtamaki CLI — proxy, IP, system, lookup, file tools."""
import typer

from mrtamaki.file.cli import app as file_app
from mrtamaki.ip.cli import app as ip_app
from mrtamaki.lookup.cli import app as lookup_app
from mrtamaki.proxy.cli import app as proxy_app
from mrtamaki.sys.cli import app as sys_app

app = typer.Typer(
    name="mt",
    help="mrtamaki CLI — proxy, IP, system, lookup, file tools",
    no_args_is_help=True,
)

app.add_typer(proxy_app, name="proxy")
app.add_typer(ip_app, name="ip")
app.add_typer(sys_app, name="sys")
app.add_typer(lookup_app, name="lookup")
app.add_typer(file_app, name="file")


@app.callback()
def main(ctx: typer.Context):
    """mrtamaki v1.12.0 — Zsh toolkit as Python CLI"""
    pass

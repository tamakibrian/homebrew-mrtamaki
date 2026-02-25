"""Tests for mrtamaki.lookup.cli."""
from typer.testing import CliRunner

from mrtamaki.lookup import cli as lookup_cli

runner = CliRunner()


def test_lookup_defaults_to_menu(monkeypatch):
    called: list[list[str]] = []

    def fake_run(args: list[str]) -> int:
        called.append(args)
        return 0

    monkeypatch.setattr(lookup_cli, "_run_one_lookup", fake_run)

    result = runner.invoke(lookup_cli.app, [])

    assert result.exit_code == 0
    assert called == [["menu"]]


def test_lookup_ip_forwards_options(monkeypatch):
    called: list[list[str]] = []

    def fake_run(args: list[str]) -> int:
        called.append(args)
        return 0

    monkeypatch.setattr(lookup_cli, "_run_one_lookup", fake_run)

    result = runner.invoke(
        lookup_cli.app,
        ["ip", "8.8.8.8", "--raw", "--no-summary", "--timeout", "5"],
    )

    assert result.exit_code == 0
    assert called == [["ip", "8.8.8.8", "--raw", "--no-summary", "--timeout", "5"]]


def test_lookup_eappend_forwards_optional_address(monkeypatch):
    called: list[list[str]] = []

    def fake_run(args: list[str]) -> int:
        called.append(args)
        return 0

    monkeypatch.setattr(lookup_cli, "_run_one_lookup", fake_run)

    result = runner.invoke(
        lookup_cli.app,
        [
            "eappend",
            "John",
            "Doe",
            "Auckland",
            "1010",
            "--address",
            "1 Example St",
        ],
    )

    assert result.exit_code == 0
    assert called == [
        [
            "eappend",
            "John",
            "Doe",
            "Auckland",
            "1010",
            "--address",
            "1 Example St",
        ]
    ]


def test_lookup_reappend_forwards_email(monkeypatch):
    called: list[list[str]] = []

    def fake_run(args: list[str]) -> int:
        called.append(args)
        return 0

    monkeypatch.setattr(lookup_cli, "_run_one_lookup", fake_run)

    result = runner.invoke(lookup_cli.app, ["reappend", "user@example.com"])

    assert result.exit_code == 0
    assert called == [["reappend", "user@example.com"]]

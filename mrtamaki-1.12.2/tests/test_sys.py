"""Tests for mrtamaki.sys.cli."""
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from mrtamaki.sys import cli as sys_cli

runner = CliRunner()


def test_sys_menu_runs_clean_menu_with_result_file(monkeypatch, tmp_path):
    root = tmp_path / "project"
    clean_dir = root / "clean"
    clean_dir.mkdir(parents=True)
    (clean_dir / "clean_menu.py").write_text("# placeholder\n")

    captured: dict = {}

    def fake_run(cmd, cwd=None, env=None):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["env"] = env

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(sys_cli, "_MRTAMAKI_ROOT", root)
    monkeypatch.setattr(sys_cli.subprocess, "run", fake_run)

    result_file = tmp_path / "result.txt"
    result = runner.invoke(sys_cli.app, ["menu", "--result-file", str(result_file)])

    assert result.exit_code == 0
    assert captured["cmd"][1] == str(clean_dir / "clean_menu.py")
    assert "--result-file" in captured["cmd"]
    assert str(result_file) in captured["cmd"]
    assert captured["cwd"] == str(clean_dir)
    assert captured["env"]["MRTAMAKI_DIR"] == str(root)


def test_sys_menu_errors_when_script_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(sys_cli, "_MRTAMAKI_ROOT", tmp_path)

    result = runner.invoke(sys_cli.app, ["menu"])

    assert result.exit_code == 1


def test_sys_dns_runs_expected_commands(monkeypatch):
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)

        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr(sys_cli.subprocess, "run", fake_run)

    result = runner.invoke(sys_cli.app, ["dns"])

    assert result.exit_code == 0
    assert calls == [
        ["sudo", "dscacheutil", "-flushcache"],
        ["sudo", "killall", "-HUP", "mDNSResponder"],
    ]


def test_sys_dns_returns_error_when_command_fails(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=cmd)

    monkeypatch.setattr(sys_cli.subprocess, "run", fake_run)

    result = runner.invoke(sys_cli.app, ["dns"])

    assert result.exit_code == 1


def test_sys_trash_handles_empty_trash(monkeypatch, tmp_path):
    fake_home = tmp_path / "home"
    trash_dir = fake_home / ".Trash"
    trash_dir.mkdir(parents=True)

    monkeypatch.setattr(sys_cli, "HOME", fake_home)
    monkeypatch.setattr(sys_cli, "_du_human", lambda p: "0B")

    result = runner.invoke(sys_cli.app, ["trash"])

    assert result.exit_code == 0
    assert "Trash is already empty" in result.stdout

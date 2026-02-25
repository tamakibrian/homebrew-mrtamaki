"""Tests for mrtamaki.file.cli."""
import json
from pathlib import Path

from typer.testing import CliRunner

from mrtamaki.file.cli import app

runner = CliRunner()


def test_file_mkdir(tmp_path):
    subdir = tmp_path / "subdir"
    result = runner.invoke(app, ["mkdir", str(subdir)])
    assert result.exit_code == 0
    created = Path(result.stdout.strip())
    assert created.exists()
    assert created.is_dir()
    assert created == subdir.resolve()


def test_file_tempdir():
    result = runner.invoke(app, ["tempdir"])
    assert result.exit_code == 0
    path = Path(result.stdout.strip())
    assert path.exists()
    assert path.is_dir()


def test_file_bookmark_add_del(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_dir = tmp_path / ".config" / "mrtamaki"
    config_dir.mkdir(parents=True)
    bookmarks_file = config_dir / "bookmarks.json"
    monkeypatch.setattr("mrtamaki.file.cli.BOOKMARKS_FILE", bookmarks_file)

    result = runner.invoke(app, ["bookmark-add", "testbm"])
    assert result.exit_code == 0
    assert bookmarks_file.exists()
    data = json.loads(bookmarks_file.read_text())
    assert "testbm" in data

    result = runner.invoke(app, ["bookmark-del", "testbm"])
    assert result.exit_code == 0
    data = json.loads(bookmarks_file.read_text())
    assert "testbm" not in data


def test_file_desktop(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    desktop = home / "Desktop"
    desktop.mkdir()
    monkeypatch.setenv("HOME", str(home))

    result = runner.invoke(app, ["desktop", "mytest"])
    assert result.exit_code == 0
    dirs = list(desktop.iterdir())
    assert len(dirs) == 1
    assert "mytest" in dirs[0].name

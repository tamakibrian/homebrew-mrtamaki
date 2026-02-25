"""Tests for mrtamaki._utils."""
import pytest

from mrtamaki._utils import (
    human_size,
    print_error,
    print_header,
    print_info,
    print_success,
    print_warning,
)


def test_human_size():
    assert human_size(0) == "0 B"
    assert human_size(2) == "1.0 KB"
    assert human_size(2048) == "1.0 MB"
    assert human_size(2097152) == "1.0 GB"


def test_print_functions(capsys):
    print_success("ok")
    print_warning("warn")
    print_info("info")
    print_header("hdr")
    out, err = capsys.readouterr()
    assert "ok" in out
    assert "warn" in out
    assert "info" in out
    assert "hdr" in out

    print_error("err")
    _, err_out = capsys.readouterr()
    assert "err" in err_out

"""Tests for mrtamaki.proxy.cli (URL generation only, no credentials)."""
from typer.testing import CliRunner

from mrtamaki.proxy.cli import _gen_iproyal_url, _gen_oxylabs_url, app

runner = CliRunner()


def test_gen_iproyal_url():
    url, port = _gen_iproyal_url("user", "pass", "auckland", "nz")
    assert "user:pass" in url
    assert "country-nz" in url
    assert "city-auckland" in url
    assert "session-" in url
    assert "lifetime-168h" in url
    assert port in (51200, 32325, 12325)


def test_gen_oxylabs_url():
    url = _gen_oxylabs_url("cust123", "pass", "christchurch", "nz")
    assert "customer-cust123" in url
    assert "cc-nz" in url
    assert "city-christchurch" in url
    assert "sessid-" in url
    assert "pr.oxylabs.io:7777" in url


def test_proxy_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "iproyal" in result.stdout
    assert "oxylabs" in result.stdout
    assert "convert" in result.stdout

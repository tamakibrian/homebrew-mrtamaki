"""Tests for mrtamaki.proxy.cli (URL generation only, no credentials)."""
import json
from typer.testing import CliRunner

from mrtamaki.proxy.cli import _gen_iproyal_url, _gen_oxylabs_url, _gen_rapid_url, app

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


def test_gen_rapid_url():
    url = _gen_rapid_url("user", "pass", "auckland", "nz")
    assert "user-residential" in url
    assert "NZ" in url
    assert "state-Auckland" in url
    assert "session-" in url
    assert "stime-180" in url
    assert "pass@" in url
    assert "rapidproxy.io" in url


def test_proxy_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "iproyal" in result.stdout
    assert "oxylabs" in result.stdout
    assert "convert" in result.stdout


def test_convert_wellington_10_binds_without_checks(monkeypatch):
    """b2 -p iproyal wellington 10 - bind 10, no checks by default."""
    monkeypatch.setenv("OXYLABS_USER", "cust")
    monkeypatch.setenv("OXYLABS_PASS", "pass")
    procs_started: list = []

    def fake_start(proxy_url, **kwargs):
        class FakeProc:
            pid = 999
            def poll(self): return None
            def wait(self): pass
            def terminate(self): pass
        procs_started.append(proxy_url)
        return FakeProc(), 12345

    monkeypatch.setattr("mrtamaki.proxy.cli._start_bound_proxy", fake_start)
    monkeypatch.setattr("mrtamaki.proxy.cli._stop_processes", lambda _: None)

    result = runner.invoke(app, ["convert", "-p", "oxylabs", "wellington", "10", "--no-wait"])

    assert result.exit_code == 0
    assert len(procs_started) == 10
    assert all("city-wellington" in u for u in procs_started)


def test_convert_help_includes_bulk_generation_flags():
    result = runner.invoke(app, ["convert", "--help"])
    assert result.exit_code == 0
    assert "--provider" in result.stdout
    assert "--count" in result.stdout
    assert "--bulk" in result.stdout
    assert "--bind-generated" in result.stdout


def test_convert_city_shorthand(monkeypatch):
    """-c is city (consistent with iproyal/oxylabs), not --clean."""
    monkeypatch.setenv("OXYLABS_USER", "cust")
    monkeypatch.setenv("OXYLABS_PASS", "pass")
    copied: list[str] = []
    monkeypatch.setattr("mrtamaki.proxy.cli.copy_to_clipboard", lambda t: copied.append(t) or True)

    result = runner.invoke(app, ["convert", "-p", "oxylabs", "-c", "sydney", "--no-wait"])

    assert result.exit_code == 0
    assert "city-sydney" in copied[0]


def test_convert_check_requires_bind_or_provider():
    """--check without --bind or --provider exits with error."""
    result = runner.invoke(app, ["convert", "--check"])
    assert result.exit_code == 1
    assert "requires" in (result.stdout + result.stderr)


def test_convert_accepts_positional_city():
    """b2 <city> accepts city as positional argument."""
    result = runner.invoke(app, ["convert", "sydney", "--help"])
    assert result.exit_code == 0


def test_mt_proxy_city_routes_to_convert(monkeypatch):
    """mt proxy auckland routes to convert (city as shortcut, no 'convert' subcommand)."""
    monkeypatch.setenv("OXYLABS_USER", "cust")
    monkeypatch.setenv("OXYLABS_PASS", "pass")
    procs_started: list = []

    def fake_start(proxy_url, **kwargs):
        class FakeProc:
            pid = 999
            def poll(self): return None
            def wait(self): pass
            def terminate(self): pass
        procs_started.append(proxy_url)
        return FakeProc(), 12345

    monkeypatch.setattr("mrtamaki.proxy.cli._start_bound_proxy", fake_start)
    monkeypatch.setattr("mrtamaki.proxy.cli._stop_processes", lambda _: None)
    monkeypatch.setattr("mrtamaki.proxy.cli._prompt_provider", lambda *a, **kw: "oxylabs")

    # Invoke proxy app with "auckland" as first arg (simulates mt proxy auckland)
    result = runner.invoke(app, ["auckland", "--no-wait"])

    assert result.exit_code == 0
    assert len(procs_started) == 1
    assert "city-auckland" in procs_started[0]


def test_convert_provider_binds_one_by_default(monkeypatch):
    """b2 -p iproyal binds 1 proxy (no -B needed)."""
    monkeypatch.setenv("OXYLABS_USER", "cust")
    monkeypatch.setenv("OXYLABS_PASS", "pass")
    procs_started: list = []

    def fake_start(proxy_url, **kwargs):
        class FakeProc:
            pid = 999
            def poll(self): return None
            def wait(self): pass
            def terminate(self): pass
        procs_started.append(proxy_url)
        return FakeProc(), 12345

    monkeypatch.setattr("mrtamaki.proxy.cli._start_bound_proxy", fake_start)
    monkeypatch.setattr("mrtamaki.proxy.cli._stop_processes", lambda _: None)

    result = runner.invoke(app, ["convert", "-p", "oxylabs", "--no-wait"])

    assert result.exit_code == 0
    assert len(procs_started) == 1
    assert "city-auckland" in procs_started[0]


def test_convert_provider_bulk_generates_and_copies(monkeypatch):
    copied: list[str] = []
    monkeypatch.setenv("OXYLABS_USER", "customer123")
    monkeypatch.setenv("OXYLABS_PASS", "password456")
    monkeypatch.setattr("mrtamaki.proxy.cli.copy_to_clipboard", lambda text: copied.append(text) or True)

    result = runner.invoke(app, ["convert", "--provider", "oxylabs", "--count", "2"])

    assert result.exit_code == 0
    assert len(copied) == 1
    assert copied[0].count("\n") == 1
    assert "customer-customer123" in copied[0]


def test_gen_bulk_speed_run_with_check(monkeypatch, tmp_path):
    """a1 -s wellington 10 --check: bind 10, run full checks, save to JSON."""
    monkeypatch.setenv("OXYLABS_USER", "cust")
    monkeypatch.setenv("OXYLABS_PASS", "pass")
    monkeypatch.setattr("mrtamaki.proxy.cli.run_provider_menu", lambda *a, **kw: "oxylabs")
    procs_started: list = []

    def fake_start(proxy_url, **kwargs):
        class FakeProc:
            pid = 999
            def poll(self): return None
            def wait(self): pass
            def terminate(self): pass
        procs_started.append(proxy_url)
        return FakeProc(), 12345

    def fake_stop(_): pass

    def fake_ip_test(port):
        return {"ipinfo": {"ip": "1.2.3.4"}, "iping": {}, "dns_leak": {}}

    def fake_scamalytics(ip):
        return {"score": 0.1} if ip else {"error": "no ip"}

    monkeypatch.setattr("mrtamaki.proxy.cli._start_bound_proxy", fake_start)
    monkeypatch.setattr("mrtamaki.proxy.cli._stop_processes", fake_stop)
    monkeypatch.setattr("mrtamaki.proxy.cli._wait_for_proxy_ready", lambda port: True)
    monkeypatch.setattr("mrtamaki.proxy.cli._run_ip_test_json", fake_ip_test)
    monkeypatch.setattr("mrtamaki.proxy.cli._run_scamalytics_json", fake_scamalytics)

    out_file = tmp_path / "checks.json"
    result = runner.invoke(app, ["gen", "-s", "wellington", "10", "--check", "-o", str(out_file), "--no-wait"])

    assert result.exit_code == 0
    assert len(procs_started) == 10
    assert all("city-wellington" in u for u in procs_started)
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert "checks" in data
    assert len(data["checks"]) == 10
    assert "scamalytics" in data["checks"][0]
    assert data["checks"][0]["scamalytics"].get("score") == 0.1


def test_gen_help_includes_bulk_and_check():
    """a1 --help shows bulk count and --check."""
    result = runner.invoke(app, ["gen", "--help"])
    assert result.exit_code == 0
    assert "COUNT" in result.stdout
    assert "--check" in result.stdout
    assert "wellington 10" in result.stdout


def test_gen_bulk_requires_speed():
    """a1 wellington 10 without -s exits with error."""
    result = runner.invoke(app, ["gen", "wellington", "10"])
    assert result.exit_code == 1
    assert "requires" in (result.stdout + result.stderr)


def test_iproyal_accepts_positional_city_country(monkeypatch):
    """iproyal [city] [country] - positional args."""
    copied: list[str] = []
    monkeypatch.setenv("IPROYAL_USER", "user")
    monkeypatch.setenv("IPROYAL_PASS", "pass")
    monkeypatch.setattr("mrtamaki.proxy.cli.copy_to_clipboard", lambda text: copied.append(text) or True)

    result = runner.invoke(app, ["iproyal", "sydney", "au"])

    assert result.exit_code == 0
    assert copied
    assert "_city-sydney_" in copied[0]
    assert "_country-au_" in copied[0]

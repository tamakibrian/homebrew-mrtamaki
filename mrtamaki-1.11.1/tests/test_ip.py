"""Tests for mrtamaki.ip.cli."""
from typer.testing import CliRunner

from mrtamaki.ip import cli as ip_cli

runner = CliRunner()


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_ip_test_rejects_invalid_port():
    result = runner.invoke(ip_cli.app, ["test", "70000"])
    assert result.exit_code == 1


def test_ip_test_uses_ipinfo_and_runs_dnsleak(monkeypatch):
    captured: dict = {}
    dns_calls: list[int | None] = []
    copied: list[str] = []

    class FakeClient:
        def __init__(self, proxy=None, timeout=None):
            captured["proxy"] = proxy
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str):
            captured["url"] = url
            return _FakeResponse({"ip": "1.2.3.4", "city": "Auckland"})

    monkeypatch.setattr(ip_cli.httpx, "Client", FakeClient)
    monkeypatch.setattr(ip_cli, "_run_dnsleak", lambda port: dns_calls.append(port))
    monkeypatch.setattr(ip_cli, "copy_to_clipboard", lambda text: copied.append(text) or True)

    result = runner.invoke(ip_cli.app, ["test"])

    assert result.exit_code == 0
    assert captured["proxy"] is None
    assert captured["url"] == "https://ipinfo.io/json"
    assert dns_calls == [None]
    assert copied == ["1.2.3.4"]


def test_ip_check_uses_clipboard_when_ip_omitted(monkeypatch):
    captured: dict = {}

    class FakeClient:
        def __init__(self, timeout=None):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str):
            captured["url"] = url
            return _FakeResponse({"status": "ok"})

    monkeypatch.setenv("SCAMALYTICS_API_KEY", "test-key")
    monkeypatch.setattr(ip_cli, "_read_clipboard", lambda: "8.8.8.8")
    monkeypatch.setattr(ip_cli.httpx, "Client", FakeClient)

    result = runner.invoke(ip_cli.app, ["check"])

    assert result.exit_code == 0
    assert "api11.scamalytics.com" in captured["url"]
    assert "key=test-key" in captured["url"]
    assert "ip=8.8.8.8" in captured["url"]


def test_ip_dnsleak_delegates_to_helper(monkeypatch):
    called: list[int | None] = []
    monkeypatch.setattr(ip_cli, "_run_dnsleak", lambda port: called.append(port))

    result = runner.invoke(ip_cli.app, ["dnsleak", "1080"])

    assert result.exit_code == 0
    assert called == [1080]

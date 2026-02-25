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
    inits: list[dict] = []
    calls: list[dict] = []
    dns_calls: list[int | None] = []
    copied: list[str] = []

    class FakeClient:
        def __init__(self, proxy=None, timeout=None, headers=None):
            inits.append({"proxy": proxy, "timeout": timeout, "headers": headers})

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, params=None):
            calls.append({"url": url, "params": params})
            if "ipinfo.io" in url:
                return _FakeResponse({"ip": "1.2.3.4", "city": "Auckland"})
            if "api.iping.cc" in url:
                return _FakeResponse({"code": 200, "data": {"ip": "1.2.3.4", "city": "Auckland"}})
            raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(ip_cli.httpx, "Client", FakeClient)
    monkeypatch.setattr(ip_cli, "_run_dnsleak", lambda port: dns_calls.append(port))
    monkeypatch.setattr(ip_cli, "copy_to_clipboard", lambda text: copied.append(text) or True)

    result = runner.invoke(ip_cli.app, ["test"])

    assert result.exit_code == 0
    assert all(item["proxy"] is None for item in inits)
    assert any(item["url"] == "https://ipinfo.io/json" for item in calls)
    assert any(item["url"] == ip_cli.IPING_URL for item in calls)
    assert dns_calls == [None]
    assert copied == ["1.2.3.4"]


def test_ip_check_uses_clipboard_when_ip_omitted(monkeypatch):
    captured: dict = {}

    class FakeClient:
        def __init__(self, timeout=None, **kwargs):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, params: dict | None = None):
            captured["url"] = url
            captured["params"] = params or {}
            return _FakeResponse({"status": "ok"})

    monkeypatch.setenv("SCAMALYTICS_API_KEY", "test-key")
    monkeypatch.setattr(ip_cli, "_read_clipboard", lambda: "8.8.8.8")
    monkeypatch.setattr(ip_cli.httpx, "Client", FakeClient)

    result = runner.invoke(ip_cli.app, ["check"])

    assert result.exit_code == 0
    assert "api11.scamalytics.com" in captured["url"]
    assert captured["params"]["key"] == "test-key"
    assert captured["params"]["ip"] == "8.8.8.8"


def test_ip_dnsleak_delegates_to_helper(monkeypatch):
    called: list[int | None] = []
    monkeypatch.setattr(ip_cli, "_run_dnsleak", lambda port: called.append(port))

    result = runner.invoke(ip_cli.app, ["dnsleak", "1080"])

    assert result.exit_code == 0
    assert called == [1080]


def test_iping_uses_clipboard_when_ip_omitted(monkeypatch):
    captured: dict = {}

    class FakeClient:
        def __init__(self, proxy=None, timeout=None, headers=None):
            captured["proxy"] = proxy
            captured["timeout"] = timeout
            captured["headers"] = headers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url: str, params=None):
            captured["url"] = url
            captured["params"] = params
            return _FakeResponse({"code": 200, "data": {"ip": "8.8.8.8", "country": "US"}})

    monkeypatch.setattr(ip_cli, "_read_clipboard", lambda: "8.8.8.8")
    monkeypatch.setattr(ip_cli.httpx, "Client", FakeClient)

    result = runner.invoke(ip_cli.app, ["iping"])

    assert result.exit_code == 0
    assert captured["url"] == ip_cli.IPING_URL
    assert captured["params"] == {"ip": "8.8.8.8", "language": "en"}

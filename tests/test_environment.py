"""Exercise configuration and startup with synthetic credentials and no services."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def load_app(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "main.py"
    copied = tmp_path / "main.py"
    copied.write_bytes(source.read_bytes())
    for name in ("NGROK_AUTH_TOKEN", "WEBHOOK_AUTH_TOKEN", "NGROK_DOMAIN", "WEBHOOK_PORT"):
        monkeypatch.delenv(name, raising=False)

    def load(dotenv):
        (tmp_path / ".env").write_text(dotenv)
        spec = importlib.util.spec_from_file_location("popdesk_fixture", copied)
        application = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(application)
        return application

    return load


@pytest.mark.parametrize("explicit", [True, False])
def test_environment_precedence_and_token_free_startup(load_app, monkeypatch, capsys, explicit):
    if explicit:
        monkeypatch.setenv("NGROK_AUTH_TOKEN", "env-ngrok-canary")
        monkeypatch.setenv("WEBHOOK_AUTH_TOKEN", "env-webhook-canary")
    application = load_app(
        "NGROK_AUTH_TOKEN=file-ngrok-canary\nWEBHOOK_AUTH_TOKEN=file-webhook-canary\n"
    )
    prefix = "env" if explicit else "file"
    assert application.NGROK_AUTH_TOKEN == prefix + "-ngrok-canary"
    assert application.WEBHOOK_AUTH_TOKEN == prefix + "-webhook-canary"

    authenticated = []
    monkeypatch.setattr(application.ngrok, "set_auth_token", authenticated.append)
    monkeypatch.setattr(application.ngrok, "connect", lambda **options:
                        SimpleNamespace(public_url="https://fixture.example"))
    monkeypatch.setattr(application.uvicorn, "run", lambda *args, **options: None)
    application.start()
    output = capsys.readouterr()
    assert authenticated == [prefix + "-ngrok-canary"]
    assert "<your-webhook-token>" in output.out
    assert "https://fixture.example" in output.out
    assert all(canary not in output.out + output.err for canary in (
        "env-ngrok-canary", "env-webhook-canary", "file-ngrok-canary", "file-webhook-canary"
    ))


def test_external_tunnel_uses_only_webhook_authentication(load_app, monkeypatch):
    notices = []
    application = load_app("WEBHOOK_AUTH_TOKEN=synthetic-webhook-canary\n")
    monkeypatch.setattr(application, "notify_windows", lambda **payload: notices.append(payload))
    with TestClient(application.app) as client:
        assert client.get("/").status_code == 200
        assert client.post("/", json={}).status_code == 401
        accepted = client.post("/", json={"title": "fixture", "message": "synthetic"},
                               headers={"Authorization": "Bearer synthetic-webhook-canary"})
    assert accepted.status_code == 200
    assert notices == [{"title": "fixture", "message": "synthetic"}]
    with pytest.raises(SystemExit, match="NGROK_AUTH_TOKEN is required"):
        application.start()


def test_ngrok_configuration_failure_stops_without_provider_output(load_app, monkeypatch):
    application = load_app("WEBHOOK_AUTH_TOKEN=synthetic\nNGROK_AUTH_TOKEN=fixture\n")

    def reject(_token):
        raise RuntimeError("provider-details-canary")

    def no_connection(**_options):
        pytest.fail("Must not open the tunnel after token configuration fails")

    monkeypatch.setattr(application.ngrok, "set_auth_token", reject)
    monkeypatch.setattr(application.ngrok, "connect", no_connection)
    with pytest.raises(SystemExit, match="Failed to configure or start") as stopped:
        application.start()
    assert str(stopped.value) == "Failed to configure or start the ngrok tunnel."
    assert stopped.value.__suppress_context__

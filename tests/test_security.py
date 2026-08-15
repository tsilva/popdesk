import os
from importlib.metadata import version
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from packaging.version import Version
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route

os.environ.setdefault("NGROK_AUTH_TOKEN", "test-ngrok-token")
os.environ.setdefault("WEBHOOK_AUTH_TOKEN", "test-webhook-token")

from main import app  # noqa: E402


@pytest.mark.parametrize(
    ("package", "minimum"),
    [("fastapi", "0.141.1"), ("starlette", "1.3.1")],
)
def test_web_stack_uses_patched_versions(package, minimum):
    assert Version(version(package)) >= Version(minimum)


def test_urlencoded_form_field_limit_is_enforced():
    async def parse_form(request: Request):
        await request.form(max_fields=2)
        return PlainTextResponse("accepted")

    client = TestClient(Starlette(routes=[Route("/", parse_form, methods=["POST"])]))

    response = client.post(
        "/",
        content="first=1&second=2&third=3",
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 400
    assert "Too many fields" in response.text


def test_arbitrary_http_method_is_not_dispatched_to_endpoint_attributes():
    class SafeEndpoint(HTTPEndpoint):
        async def get(self, request: Request):
            return JSONResponse({"ok": True})

    client = TestClient(Starlette(routes=[Route("/", SafeEndpoint)]))

    assert client.get("/").json() == {"ok": True}
    assert client.request("__class__", "/").status_code == 405


def test_request_hostname_uses_the_validated_host_header():
    async def hostname(request: Request):
        return JSONResponse({"hostname": request.url.hostname, "path": request.url.path})

    client = TestClient(Starlette(routes=[Route("/notify", hostname)]))
    response = client.get("/notify", headers={"host": "popdesk.example:8443"})

    assert response.json() == {"hostname": "popdesk.example", "path": "/notify"}


def test_webhook_rejects_bad_auth_and_preserves_valid_notification_flow():
    client = TestClient(app)
    payload = {"title": "Build complete", "message": "The valid control passed"}

    with patch("main.notify_windows") as notify:
        assert client.post("/", json=payload).status_code == 401
        response = client.post(
            "/",
            json=payload,
            headers={"authorization": "Bearer test-webhook-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    notify.assert_called_once_with(title=payload["title"], message=payload["message"])

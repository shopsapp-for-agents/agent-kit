import asyncio
import json

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

import mcp_server


def mock_client(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(
        mcp_server,
        "_client",
        lambda base_url: httpx.Client(base_url=base_url, transport=transport, follow_redirects=False),
    )


def test_public_profile_never_sends_configured_token(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "https://shopsapp.com")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "sa_private")

    def handler(request):
        assert request.url.path == "/v1/people/alice"
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"alias": "alice", "lists": []})

    mock_client(monkeypatch, handler)
    assert mcp_server.get_public_profile("alice")["alias"] == "alice"


def test_agent_signup_sends_email_request_without_account_token(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "https://shopsapp.com")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "sa_private")

    def handler(request):
        assert request.url.path == "/v1/agent-signups"
        assert "Authorization" not in request.headers
        assert json.loads(request.content) == {"email": "alice@example.com"}
        return httpx.Response(202, json={"status": "check_email"})

    mock_client(monkeypatch, handler)
    assert mcp_server.start_account_signup("alice@example.com") == {"status": "check_email"}


def test_agent_pairing_starts_without_owner_token(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "https://shopsapp.com")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "sa_private")

    def handler(request):
        assert request.url.path == "/v1/agent-pairings"
        assert "Authorization" not in request.headers
        assert json.loads(request.content) == {"agent_name": "My assistant", "requested_access": "write"}
        return httpx.Response(
            201, json={"approval_url": "https://shopsapp.com/app?pair=1", "request_secret": "pr_secret"}
        )

    mock_client(monkeypatch, handler)
    assert mcp_server.start_agent_pairing("My assistant", "write")["request_secret"] == "pr_secret"


def test_private_capture_preserves_exact_url_and_idempotency(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "http://127.0.0.1:5174")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "sa_owner")
    original_url = "https://shop.example/item?tag=creator-20&variant=M%2Fblue#details"

    def handler(request):
        assert request.url.path == "/v1/captures"
        assert request.headers["Authorization"] == "Bearer sa_owner"
        assert request.headers["Idempotency-Key"] == "same-save"
        assert json.loads(request.content)["url"] == original_url
        return httpx.Response(201, json={"item": {"url": original_url}})

    mock_client(monkeypatch, handler)
    result = mcp_server.capture_url("list-id", original_url, "A product", idempotency_key="same-save")
    assert result["item"]["url"] == original_url


def test_trending_is_public_and_capture_passes_product_identity(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "https://shopsapp.com")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_agent")

    def handler(request):
        if request.url.path == "/v1/trending":
            assert "Authorization" not in request.headers
            assert request.url.params["days"] == "30"
            assert request.url.params["category"] == "home"
            return httpx.Response(200, json={"total_saves": 1, "items": []})
        if request.url.path == "/v1/products/036000291452":
            assert "Authorization" not in request.headers
            return httpx.Response(200, json={"gtin14": "00036000291452", "public_save_count": 2})
        assert request.url.path == "/v1/captures"
        assert request.headers["Authorization"] == "Bearer ak_agent"
        assert json.loads(request.content)["category"] == "home"
        assert json.loads(request.content)["gtin"] == "036000291452"
        assert json.loads(request.content)["page_type"] == "product"
        return httpx.Response(201, json={"item": {"product": {"gtin14": "00036000291452"}}})

    mock_client(monkeypatch, handler)
    assert mcp_server.get_trending(30, "home")["total_saves"] == 1
    assert mcp_server.get_public_product("036000291452")["public_save_count"] == 2
    assert (
        mcp_server.capture_url(
            "list-id", "https://shop.example/item", "A lamp", category="home", gtin="036000291452", page_type="product"
        )["item"]["product"]["gtin14"]
        == "00036000291452"
    )


def test_private_access_requires_secret_in_host_environment(monkeypatch):
    monkeypatch.delenv("SHOPSAPP_TOKEN", raising=False)
    with pytest.raises(ToolError, match="SHOPSAPP_TOKEN"):
        mcp_server.list_my_lists()


def test_bridge_refuses_plain_http_to_remote_host(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "http://shopsapp.com")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "sa_owner")
    with pytest.raises(ToolError, match="HTTPS origin"):
        mcp_server.list_my_lists()


def test_bridge_does_not_follow_redirects_with_credential(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_BASE_URL", "https://shopsapp.com")
    monkeypatch.setenv("SHOPSAPP_TOKEN", "sa_owner")
    mock_client(monkeypatch, lambda request: httpx.Response(302, headers={"Location": "https://other.example"}))
    with pytest.raises(ToolError, match="redirected"):
        mcp_server.list_my_lists()


def test_mcp_exposes_core_tools():
    names = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    assert {
        "start_account_signup",
        "start_agent_pairing",
        "exchange_agent_pairing",
        "get_public_profile",
        "list_my_lists",
        "capture_url",
        "search_my_recipes",
        "update_recipe",
        "get_recipe_grocery_handoff",
        "reserve_item",
        "get_handoff",
    } <= names

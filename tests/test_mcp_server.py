import asyncio
import json

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

import mcp_server


def test_google_sheets_status_is_read_only_and_uses_only_the_shopsapp_credential(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_all_owned_reader")
    expected = {"available": True, "connected": True, "job_state": "up_to_date", "lists": []}

    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/v1/me/google-sheets"
        assert request.headers["Authorization"] == "Bearer ak_all_owned_reader"
        return httpx.Response(200, json=expected)

    mock_client(monkeypatch, handler)
    assert mcp_server.get_google_sheets_sync_status() == expected
    tool = next(tool for tool in asyncio.run(mcp_server.mcp.list_tools())
                if tool.name == "get_google_sheets_sync_status")
    assert tool.annotations.model_dump(by_alias=True)["readOnlyHint"] is True


def test_google_sheets_status_preserves_the_server_all_owned_lists_boundary(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_one_list_reader")
    mock_client(monkeypatch, lambda request: httpx.Response(
        403, json={"detail": "Google Sheets status needs access to all owned lists"},
    ))
    with pytest.raises(ToolError, match="403.*all owned lists"):
        mcp_server.get_google_sheets_sync_status()


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
        assert json.loads(request.content) == {
            "agent_name": "My assistant",
            "requested_access": "write",
            "requested_dashboard_access": "write",
        }
        return httpx.Response(
            201, json={"approval_url": "https://shopsapp.com/app?pair=1", "request_secret": "pr_secret"}
        )

    mock_client(monkeypatch, handler)
    assert mcp_server.start_agent_pairing("My assistant", "write", "write")["request_secret"] == "pr_secret"


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
        "execute_dashboard_action",
        "get_public_profile",
        "list_my_lists",
        "export_my_lists_csv",
        "get_google_sheets_sync_status",
        "capture_url",
        "search_my_recipes",
        "update_recipe",
        "get_recipe_grocery_handoff",
        "reserve_item",
        "get_handoff",
    } <= names


def test_dashboard_workflow_uses_configured_credential_for_permission_discovery(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_agent")

    def handler(request):
        if request.url.path == "/v1/agent-dashboard/capabilities":
            assert request.headers["Authorization"] == "Bearer ak_agent"
            assert request.url.params["category"] == "sharing"
            return httpx.Response(200, json={"operations": []})
        assert request.headers["Authorization"] == "Bearer ak_agent"
        if request.method == "POST":
            assert json.loads(request.content) == {
                "operation": "edit_list",
                "arguments": {"list_id": "list", "body": {"title": "Holiday"}},
            }
            return httpx.Response(
                201,
                json={
                    "id": "action",
                    "status": "pending",
                    "approval_url": "https://shopsapp.com/app?agent_action=action",
                },
            )
        assert request.url.path == "/v1/agent-dashboard/actions/action"
        return httpx.Response(200, json={"status": "completed", "result": {"data": {"title": "Holiday"}}})

    mock_client(monkeypatch, handler)
    mcp_server.get_dashboard_capabilities("sharing")
    assert (
        mcp_server.request_dashboard_action("edit_list", {"list_id": "list", "body": {"title": "Holiday"}})["status"]
        == "pending"
    )
    assert mcp_server.get_dashboard_action_result("action")["status"] == "completed"
    names = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    assert {
        "get_dashboard_capabilities",
        "request_dashboard_action",
        "get_dashboard_action_result",
        "search_list_emojis",
        "lookup_barcode",
        "get_public_list_leaderboard",
    } <= names


def test_credential_issuing_helpers_are_not_model_tools():
    names = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}
    assert "start_agent_pairing" not in names
    assert "exchange_agent_pairing" not in names


def test_delegated_execution_keeps_token_in_header_and_passes_exact_arguments(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_agent")

    def handler(request):
        assert request.url.path == "/v1/agent-dashboard/execute"
        assert request.headers["Authorization"] == "Bearer ak_agent"
        assert json.loads(request.content) == {
            "operation": "edit_list",
            "arguments": {"list_id": "one", "body": {"title": "New"}},
        }
        assert "ak_agent" not in str(request.url)
        assert b"ak_agent" not in request.content
        return httpx.Response(200, json={"operation": "edit_list", "data": {"title": "New"}})

    mock_client(monkeypatch, handler)
    assert (
        mcp_server.execute_dashboard_action("edit_list", {"list_id": "one", "body": {"title": "New"}})["data"]["title"]
        == "New"
    )


def test_catalog_without_a_configured_credential_remains_public(monkeypatch):
    monkeypatch.delenv("SHOPSAPP_TOKEN", raising=False)

    def handler(request):
        assert "Authorization" not in request.headers
        return httpx.Response(200, json={"operations": []})

    mock_client(monkeypatch, handler)
    assert mcp_server.get_dashboard_capabilities() == {"operations": []}


def test_csv_export_preserves_bom_unicode_and_checks_with_private_header(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_agent")
    csv_text = "\ufeffList name,Item name,Ingredient checked\r\nCafé,2 eggs,True\r\n"

    def handler(request):
        assert request.url.path == "/v1/me/lists/export"
        assert request.headers["Authorization"] == "Bearer ak_agent"
        assert request.headers["Accept"] == "text/csv"
        assert "ak_agent" not in str(request.url)
        return httpx.Response(
            200,
            text=csv_text,
            headers={
                "Content-Type": "text/csv; charset=utf-8",
                "Content-Disposition": 'attachment; filename="shopsapp-lists-2026-10-14.csv"',
            },
        )

    mock_client(monkeypatch, handler)
    assert mcp_server.export_my_lists_csv() == {
        "mime_type": "text/csv",
        "filename": "shopsapp-lists-2026-10-14.csv",
        "csv": csv_text,
    }


def test_csv_export_rejects_redirect_and_unexpected_html(monkeypatch):
    monkeypatch.setenv("SHOPSAPP_TOKEN", "ak_agent")
    mock_client(monkeypatch, lambda request: httpx.Response(302, headers={"Location": "https://other.example"}))
    with pytest.raises(ToolError, match="redirected"):
        mcp_server.export_my_lists_csv()
    mock_client(monkeypatch, lambda request: httpx.Response(200, text="Login", headers={"Content-Type": "text/html"}))
    with pytest.raises(ToolError, match="unexpected CSV response"):
        mcp_server.export_my_lists_csv()

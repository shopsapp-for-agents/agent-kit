"""Local stdio MCP bridge to the ShopsApp JSON API.

The hosted ShopsApp service already serves Streamable HTTP MCP at /mcp/. This
bridge exists for clients that can launch a local MCP process but cannot use a
remote MCP endpoint. It holds no database and never performs checkout.
"""

import os
from typing import Any, Literal
from urllib.parse import quote, urlsplit

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

mcp = MCPServer(
    name="ShopsApp",
    title="ShopsApp lists",
    description="Save and read permitted ShopsApp lists; coordinate gifts and return original merchant links.",
    instructions=(
        "Read https://shopsapp.com/skill.md before acting. Preserve saved URLs and attribution. "
        "Ask before reserving a gift. This server cannot purchase an item or handle a wallet."
    ),
)


def _base_url() -> str:
    value = os.getenv("SHOPSAPP_BASE_URL", "https://shopsapp.com").rstrip("/")
    parsed = urlsplit(value)
    loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (
        parsed.scheme not in ({"http", "https"} if loopback else {"https"})
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ToolError("SHOPSAPP_BASE_URL must be an HTTPS origin or a local loopback origin")
    return value


def _client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=20, follow_redirects=False)


def _segment(value: str) -> str:
    return quote(value, safe="")


def _request(
    method: str,
    path: str,
    *,
    private: bool = False,
    body: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    base_url = _base_url()
    headers = {"Accept": "application/json", "User-Agent": "shopsapp-agent-kit/0.1"}
    if private:
        token = os.getenv("SHOPSAPP_TOKEN", "").strip()
        if not token:
            raise ToolError("Private list access requires SHOPSAPP_TOKEN in the MCP host environment")
        headers["Authorization"] = f"Bearer {token}"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    try:
        with _client(base_url) as client:
            response = client.request(method, path, headers=headers, json=body)
    except httpx.RequestError as exc:
        raise ToolError(f"ShopsApp is unreachable: {type(exc).__name__}") from exc
    if response.is_redirect:
        raise ToolError("ShopsApp redirected the request; check SHOPSAPP_BASE_URL")
    if response.status_code >= 400:
        detail = "Request failed"
        try:
            value = response.json().get("detail")
            if isinstance(value, str):
                detail = value[:180]
        except (ValueError, AttributeError):
            pass
        raise ToolError(f"ShopsApp {response.status_code}: {detail}")
    if response.status_code == 204:
        return {}
    try:
        result = response.json()
    except ValueError as exc:
        raise ToolError("ShopsApp returned a non-JSON response") from exc
    if not isinstance(result, dict):
        raise ToolError("ShopsApp returned an unexpected JSON response")
    return result


@mcp.tool(
    structured_output=True,
    description=(
        "Start email-verified signup after the person approves sending an email. "
        "Only the person can finish; no credential is returned."
    ),
)
def start_account_signup(email: str) -> dict[str, Any]:
    return _request("POST", "/v1/agent-signups", body={"email": email})


@mcp.tool(
    structured_output=True,
    description=(
        "Request owner approval for this agent. Show only approval_url to the person; keep request_secret private."
    ),
)
def start_agent_pairing(agent_name: str, requested_access: Literal["read", "write"] = "read") -> dict[str, Any]:
    return _request(
        "POST",
        "/v1/agent-pairings",
        body={"agent_name": agent_name, "requested_access": requested_access},
    )


@mcp.tool(
    structured_output=True,
    description=(
        "Exchange a private pairing request secret after the person approves. "
        "Store the returned agent credential securely."
    ),
)
def exchange_agent_pairing(request_secret: str) -> dict[str, Any]:
    return _request("POST", "/v1/agent-pairings/exchange", body={"request_secret": request_secret})


@mcp.tool(structured_output=True, description="Read a person's public profile and public lists by alias.")
def get_public_profile(alias: str) -> dict[str, Any]:
    return _request("GET", f"/v1/people/{_segment(alias)}")


@mcp.tool(structured_output=True, description="Read a public list by slug.")
def get_public_list(slug: str) -> dict[str, Any]:
    return _request("GET", f"/v1/public/lists/{_segment(slug)}")


@mcp.tool(
    structured_output=True,
    description=(
        "Explore opt-in public saves. Days: 7 or 30; optional category: fashion, home, "
        "tech, beauty, books, hobbies, food, or other. Counts are saves, not sales."
    ),
)
def get_trending(days: int = 7, category: str | None = None) -> dict[str, Any]:
    params = f"days={days}"
    if category:
        params += f"&category={_segment(category)}"
    return _request("GET", f"/v1/trending?{params}")


@mcp.tool(
    structured_output=True,
    description=(
        "Find opt-in public saves linked by a submitted, checksum-valid UPC/EAN/GTIN. These are not verified offers."
    ),
)
def get_public_product(gtin: str) -> dict[str, Any]:
    return _request("GET", f"/v1/products/{_segment(gtin)}")


@mcp.tool(structured_output=True, description="List the authenticated owner's shopping, wish, and recipe lists.")
def list_my_lists() -> dict[str, Any]:
    return _request("GET", "/v1/lists", private=True)


@mcp.tool(structured_output=True, description="Read a list when the configured account or grant permits it.")
def get_list(list_id: str) -> dict[str, Any]:
    return _request("GET", f"/v1/lists/{_segment(list_id)}", private=True)


@mcp.tool(structured_output=True, description="Read the authenticated account's alias and profile URL.")
def get_my_profile() -> dict[str, Any]:
    return _request("GET", "/v1/me", private=True)


@mcp.tool(structured_output=True, description="Create a shopping, wish, or recipe list for the owner.")
def create_list(
    title: str,
    mode: Literal["wishlist", "shopping", "recipe"] = "wishlist",
    visibility: Literal["private", "public"] = "private",
) -> dict[str, Any]:
    return _request(
        "POST",
        "/v1/lists",
        private=True,
        body={"title": title, "mode": mode, "visibility": visibility},
    )


@mcp.tool(
    structured_output=True,
    description=(
        "Save the exact URL, including referral tags. Optional GTIN must come from product data, never a guess."
    ),
)
def capture_url(
    list_id: str,
    url: str,
    title: str,
    variant: str | None = None,
    category: str = "other",
    gtin: str | None = None,
    quantity: int = 1,
    idempotency_key: str | None = None,
    recipe_ingredients: list[str] | None = None,
    recipe_servings: str | None = None,
) -> dict[str, Any]:
    return _request(
        "POST",
        "/v1/captures",
        private=True,
        body={
            "list_id": list_id,
            "url": url,
            "title": title,
            "variant": variant,
            "category": category,
            "gtin": gtin,
            "quantity": quantity,
            "recipe": (
                {"ingredients": recipe_ingredients, "servings": recipe_servings}
                if recipe_ingredients is not None
                else None
            ),
        },
        idempotency_key=idempotency_key,
    )


@mcp.tool(structured_output=True, description="Search accessible saved recipes by title or ingredient.")
def search_my_recipes(query: str = "") -> dict[str, Any]:
    return _request("GET", f"/v1/recipes?q={_segment(query)}", private=True)


@mcp.tool(structured_output=True, description="Add or correct ingredients for a saved recipe.")
def update_recipe(item_id: str, ingredients: list[str], servings: str | None = None) -> dict[str, Any]:
    return _request(
        "PUT",
        f"/v1/recipes/{_segment(item_id)}",
        private=True,
        body={"ingredients": ingredients, "servings": servings},
    )


@mcp.tool(
    structured_output=True,
    description="Get ingredient JSON for an external grocery agent. Does not place an order.",
)
def get_recipe_grocery_handoff(item_id: str) -> dict[str, Any]:
    return _request("GET", f"/v1/recipes/{_segment(item_id)}/grocery-handoff", private=True)


@mcp.tool(structured_output=True, description="Invite a named ShopsApp user to one list.")
def invite_person(list_id: str, recipient_alias: str, can_reserve: bool = False) -> dict[str, Any]:
    return _request(
        "POST",
        f"/v1/lists/{_segment(list_id)}/shares",
        private=True,
        body={"recipient_alias": recipient_alias, "can_reserve": can_reserve},
    )


@mcp.tool(structured_output=True, description="Read invitations addressed to the authenticated account.")
def list_my_invites() -> dict[str, Any]:
    return _request("GET", "/v1/me/invites", private=True)


@mcp.tool(structured_output=True, description="Accept an invitation addressed to the authenticated account.")
def accept_list_invite(share_id: str) -> dict[str, Any]:
    return _request("POST", f"/v1/invites/{_segment(share_id)}/accept", private=True)


@mcp.tool(structured_output=True, description="Read lists shared with the authenticated account.")
def list_shared_with_me() -> dict[str, Any]:
    return _request("GET", "/v1/me/shared-lists", private=True)


@mcp.tool(structured_output=True, description="Reserve one gift unit after the buyer chooses; does not purchase it.")
def reserve_item(item_id: str, idempotency_key: str | None = None) -> dict[str, Any]:
    return _request(
        "POST",
        f"/v1/items/{_segment(item_id)}/reservations",
        private=True,
        body={"quantity": 1},
        idempotency_key=idempotency_key,
    )


@mcp.tool(structured_output=True, description="Release an abandoned gift reservation.")
def release_reservation(reservation_id: str) -> dict[str, Any]:
    return _request("DELETE", f"/v1/reservations/{_segment(reservation_id)}", private=True)


@mcp.tool(structured_output=True, description="Get the original saved merchant URL without rewriting it.")
def get_handoff(item_id: str) -> dict[str, Any]:
    return _request("GET", f"/v1/items/{_segment(item_id)}/handoff", private=True)


if __name__ == "__main__":
    mcp.run(transport="stdio")

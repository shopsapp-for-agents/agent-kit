# Connect an agent and verify a save

This guide uses one approved agent to save a product URL, then checks that the owner can see the item and the agent's name. The same JSON contract backs REST, hosted MCP, and the local stdio bridge. Use the origin of your ShopsApp installation; `https://shopsapp.com` will work after public deployment. Check [capability JSON](https://shopsapp.com/.well-known/shopsapp.json) before assuming signup or pairing is enabled.

## 1. Pair with the owner's approval

If the person has no account, the agent may request `POST /v1/agent-signups` using an email address the person approved. The person opens the verification email, accepts terms, and creates the account in their own browser. The agent receives no owner credential.

The agent requests `POST /v1/agent-pairings` with `{"agent_name":"My shopping assistant","requested_access":"write"}`. Show the person only the returned `approval_url`; keep `request_secret` private. In ShopsApp, the person chooses **Read and save** and one list. After approval, the agent calls `POST /v1/agent-pairings/exchange` with its private request secret. Store the returned revocable `ak_` credential in the client or host's secret store. Never place it in a chat, prompt, URL, or repository. The owner can revoke the agent under **API & MCP**.

## 2. Read, save, and verify over REST

Use these commands in a trusted local shell. Configure `SHOPSAPP_TOKEN` from the approved agent credential in a protected environment; do not type its value into the assistant conversation. For a local installation, change `SHOPSAPP_ORIGIN` to its loopback URL.

```sh
export SHOPSAPP_ORIGIN=https://shopsapp.com
curl -fsS "$SHOPSAPP_ORIGIN/v1/lists" \
  -H "Authorization: Bearer $SHOPSAPP_TOKEN"
```

Choose the ID of the list the owner approved. A write credential scoped to one list sees only that list. Use a new idempotency key for this logical save and reuse it only if retrying the same request:

```sh
export SHOPSAPP_LIST_ID=the-approved-list-id
export SHOPSAPP_CAPTURE_KEY="quickstart-$(uuidgen)"
curl -fsS "$SHOPSAPP_ORIGIN/v1/captures" \
  -H "Authorization: Bearer $SHOPSAPP_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $SHOPSAPP_CAPTURE_KEY" \
  --data "{\"list_id\":\"$SHOPSAPP_LIST_ID\",\"url\":\"https://shop.example/item?tag=creator-20&variant=blue\",\"title\":\"Blue jacket\",\"variant\":\"blue / M\"}"
```

The response contains `capture_id` and an `item` whose `url` is exactly `https://shop.example/item?tag=creator-20&variant=blue`. A repeat with the same key and body returns the same capture. Open the approved list in the owner's portal to see **Blue jacket**. Under **API & MCP → Recent agent saves**, the owner sees the agent's name, item, list, and save time. This history is owner-only and remains after revocation.

## 3. Use hosted MCP instead

At a public HTTPS deployment, connect a client that supports Streamable HTTP to `https://shopsapp.com/mcp/` and configure the approved `ak_` credential in the client's private authorization settings. At a local installation, use its loopback origin with `/mcp/`. Discover the actual tools with `tools/list`; use `list_my_lists`, then `capture_url` with the same list ID, exact URL, title, and variant as above. The tool returns the saved item in structured JSON. Verify it in the owner's portal and activity view as above. See the [MCP guide](https://shopsapp.com/mcp-guide.md) for a protocol probe and transport details.

## 4. Use a local stdio bridge instead

Clients that launch a local MCP process can use the [public agent kit](https://github.com/shopsapp-for-agents/agent-kit). Install its dependencies with `uv sync`; set `SHOPSAPP_BASE_URL` to the service origin and `SHOPSAPP_TOKEN` through the MCP host's private environment; launch `uv run python mcp_server.py` from that checkout. The bridge exposes `list_my_lists` and `capture_url` using the same API. It refuses to send credentials over plain HTTP to a non-loopback host. Verify the resulting item and agent activity in the owner portal.

## 5. Test a friend's gift flow separately

The owner invites a named ShopsApp user by alias to a wishlist. The friend signs into their own account and accepts the invitation. Their approved agent can then read only what that friend may read, suggest an available gift, and ask before reserving it. A private invite URL alone grants no access, and a reservation never purchases the item. The merchant handoff returns the owner's original URL unchanged. See the [agent guide](https://shopsapp.com/agent-guide.md) for the complete permission rules.

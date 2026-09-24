# ShopsApp MCP

The human-facing [MCP setup guide](https://shopsapp.com/docs/mcp) starts with connection, permissions, and examples. This Markdown version is available to agent clients.

ShopsApp provides Streamable HTTP MCP at `https://mcp.shopsapp.com/mcp/`, with `https://shopsapp.com/mcp/` retained for existing clients. Use the trailing slash. For a local deployment, use its local origin, such as `http://127.0.0.1:5174/mcp/`. The server uses the same authorization and list permissions as REST.

The [public agent kit](https://github.com/shopsapp-for-agents/agent-kit) also contains a small **stdio MCP bridge** for clients that can launch a local process but cannot connect to a remote MCP URL. The bridge calls the ShopsApp JSON API; it does not store lists or credentials itself.

Follow the [quickstart](QUICKSTART.md) to pair an agent, save one exact URL, and verify the result in the owner's list and agent activity view.

## Connect securely

- OAuth-capable clients discover the authorization server when a private tool returns HTTP 401. ShopsApp supports authorization code with S256 PKCE, dynamic public-client registration, short-lived access tokens, rotating refresh tokens, and owner revocation. The person approves read/write access, one list or all owned lists, and separately whether to include accepted shared lists. Use the exact OAuth resource returned by protected-resource metadata; it matches the MCP hostname you connected to. A token issued for one MCP hostname is not accepted on the other.
- Choose **Streamable HTTP** in a client that supports remote MCP and enter the endpoint URL above. Configure an owner-approved agent or scoped list-grant bearer credential through the client's secure authorization settings. Do not paste a token into the assistant conversation.
- For a local stdio client, install the [agent kit](https://github.com/shopsapp-for-agents/agent-kit), set `SHOPSAPP_BASE_URL` to the service origin, and set `SHOPSAPP_TOKEN` through the host's secret or environment configuration. Launch `uv run python mcp_server.py` from that checkout. The bridge refuses to send a token over plain HTTP to a non-loopback host.
- Public profile and list tools can be used without a token. Private tools return an access error if no authorized credential is configured.

The API's `/.well-known/shopsapp.json` lists the current MCP path. To verify that a server is reachable, request `tools/list` using any MCP client. A raw HTTP probe can use:

```sh
curl -sS https://shopsapp.com/mcp/ \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

The hosted server exposes owner, public, sharing, grant, reservation, and handoff tools. The stdio bridge includes the main save, read, sharing, reservation, and handoff paths. Read the tool descriptions returned by your connected server rather than assuming that every client can authorize every tool.

## Start with these tools

| Intent | Hosted MCP tools |
| --- | --- |
| Open a ShopsApp link without rendering HTML | `resolve_shopsapp_url` |
| Find a friend's permitted list | `search_people_and_lists`, `list_shared_with_me` |
| Find saved items or birthday preferences | `search_accessible_items`, `get_list` |
| Save a find | `capture_url` |
| Coordinate a gift | `reserve_item`, `release_reservation`, `get_commerce_handoff` |
| Prepare groceries | `set_recipe_ingredients`, `create_grocery_handoff` |

The legacy read/save tools remain for compatibility. Price and stock checks, scheduling, and notifications belong to the person's own agent. ShopsApp does not run watches or alerts. Grocery handoffs contain ingredients and provider mappings, not local prices, product images, or an existing cart. An Instacart `products_link` mapping creates a shopping-page link only; a user's own integration must handle matching and cart creation. `find_products` reports affiliate feeds as coming soon, not fabricated search results.

Both servers expose `get_trending` for opt-in public saves and `get_public_product` for public saves sharing a submitted GTIN. `capture_url` accepts optional `category` and `gtin` arguments. Use a GTIN only when it comes from product data, not a guess based on the URL. A matching number is a research lead, not a verified retailer offer.

## Permission and attribution rules

An `sa_` account token belongs to the person and stays in their browser. Agents request pairing and receive an `ak_` credential with owner-approved read/write and optional list scope. The owner can revoke it. An `sg_` guest grant is scoped to one list and may permit reservations. Share or grant revocation stops later reads and actions. Never place either credential in a URL or prompt. `get_handoff` returns the original saved merchant URL, including existing affiliate attribution; do not replace it or simulate a referral click. ShopsApp has no payment or wallet tool.

# ShopsApp agent kit

This repository is an optional distribution package for ShopsApp agents. The [ShopsApp website](https://shopsapp.com/docs) is the source of truth for connection steps, permissions, and examples; the [MCP guide](https://shopsapp.com/docs/mcp) points to live tool discovery. You do not need to clone this repository to connect a remote MCP client.

The kit contains an [installable agent skill](skills/shopsapp/SKILL.md), a [local stdio MCP bridge](mcp_server.py) for clients without remote MCP support, a [read → save → verify quickstart](docs/QUICKSTART.md), and an [MCP Registry manifest](server.json). The [JSON API guide](docs/API.md) and [MCP notes](docs/MCP.md) serve clients that need local, text-based instructions; they are not a second live tool catalog.

## Choose a connection

**Remote MCP:** Connect to `https://mcp.shopsapp.com/mcp/` using Streamable HTTP. The original `https://shopsapp.com/mcp/` remains supported. OAuth-capable clients discover PKCE consent automatically; legacy approved bearer credentials are also supported. See [MCP setup](docs/MCP.md) for authorization and a protocol probe. The hosted endpoint exposes the current toolset; this local bridge retains the core save/read/gift/recipe paths.

**JSON API:** Use the [interactive REST reference](https://shopsapp.com/docs/api) or [OpenAPI JSON](https://shopsapp.com/openapi.json). The [API guide](docs/API.md) maps common tasks to routes. Someone who simply wants to connect an assistant can use [Connectors](https://shopsapp.com/connectors).

**Local stdio MCP bridge:** If an MCP client launches a local process, run this bridge. It calls the ShopsApp JSON API and never stores list data:

```sh
uv sync
SHOPSAPP_BASE_URL=http://127.0.0.1:5174 uv run python mcp_server.py
```

For private access, the connector host performs OAuth or secure REST pairing outside model-visible tools. It shows only the approval URL and keeps request secrets and exchanged credentials in protected storage. Pairing/exchange helpers are not exposed as MCP tools. Set the resulting revocable `ak_` token as `SHOPSAPP_TOKEN` in the MCP host’s secret or environment configuration. Do not paste a token into a chat, prompt, URL, or repository. The bridge allows plain HTTP only for loopback origins and does not follow redirects with credentials. It exposes public profile/list reads plus owner and permitted sharing, save, reservation, and handoff tools. The hosted server remains the full MCP interface.

## Use the skill

Point an assistant at [SKILL.md](skills/shopsapp/SKILL.md), or copy that file into its skill directory. The service also serves the same skill at `/skill.md` and a directly readable agent page at `/for-agents`. The [starter prompt](connect.md) is client-neutral; replace `{{SHOPSAPP_ORIGIN}}` with the origin the agent can reach.

The skill's central rules are simple: read only permitted lists, preserve saved URLs and attribution, ask before reserving, and leave checkout to separate authorized tools. Price and stock checks, scheduling, and alerts use the person's own agent tools; ShopsApp does not run watches. Grocery handoffs supply ingredients, not selected products or a cart. The buyer's connected shopping provider handles local selection, prices, images, and cart creation. Product search returns only enabled, current catalog sources separately licensed for agents, plus labelled samples.

## MCP registry metadata

[`server.json`](server.json) describes the v0.5 hosted Streamable HTTP endpoint for the official MCP Registry. On 24 September 2026, the official publisher validated the manifest and an MCP SDK client verified HTTPS, tool discovery and rejection of unauthenticated private calls on both hosted endpoints. Registry publication is pending GitHub authorization for the `shopsapp-for-agents` organization. This manifest describes the remote server only; the local Python bridge remains a smaller compatibility adapter and is not published to a package registry. No agent token belongs in the manifest.

## Development

Use Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```sh
uv sync --extra dev
uv run pytest -q
uv run ruff check .
```

The bridge's tests cover token isolation, exact URL preservation, transport security, and exposed tool names. For the ShopsApp service implementation and API behavior, use the live discovery JSON and OpenAPI schema at the deployed origin.

## Dashboard parity

The bridge exposes `execute_dashboard_action`, backed by the same server-validated workflow catalog as hosted MCP. With a configured token, `get_dashboard_capabilities` sends it securely to return this connection's permissions; without one it returns public schemas. Explicit `dashboard:read` or `dashboard:write` consent at connection time permits account workflows without repeated UI approval. Existing credentials do not expand. The optional one-time request/result tools remain for ungranted actions.

The website is the live source of truth. The v0.5 integration adds Groceries workflows and the named `export_my_lists_csv` adapter. Production delivery is being verified. A synthetic approved connection verified direct REST, hosted MCP and stdio MCP workflows without subsequent UI approval on 14 October 2026. Updating source or the manifest does not publish to the MCP Registry. Read [the workflow contract](docs/DASHBOARD.md).

The Groceries tab has corresponding `get_my_groceries`, `add_my_groceries`, and `empty_groceries` workflows in the live catalog. CSV exports use `export_my_lists_csv` with existing list-read permissions; a one-list credential stays within that list. Exported CSV is returned to the requesting assistant and is not uploaded or shared. The bridge preserves UTF-8 ingredient text and shopping checks, rejects redirects, and keeps the credential only in its request header.

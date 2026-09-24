# ShopsApp agent kit

ShopsApp is a shopping-list service for people and independent assistants. This public kit contains the [ShopsApp skill](skills/shopsapp/SKILL.md), [agent guide](docs/AGENT-GUIDE.md), [JSON API guide](docs/API.md), [MCP guide](docs/MCP.md), a [shared starter prompt](connect.md), and a local stdio MCP bridge for clients that cannot connect to remote MCP servers.

An assistant can save exact product URLs, search permitted lists, coordinate gifts, watch supported non-grocery products, and prepare structured grocery ingredients. Affiliate product feeds and cross-store comparisons are coming soon. ShopsApp never creates carts, buys products, processes payments, or manages wallets; grocery selection, images, local prices and checkout belong to the buyer's own provider connection.

Recipe lists store exact source URLs and ingredient strings. `search_my_recipes` finds accessible recipes by title or ingredient, and `get_recipe_grocery_handoff` returns JSON for an authorized external grocery agent. An approved write agent can add verified ingredients with `update_recipe`. Instacart's hosted recipe page is one possible external handoff; ShopsApp does not create a cart or order.

`get_trending` reads 7- or 30-day saves by category from public lists whose owners explicitly enabled discovery. `capture_url` accepts an optional category and a GTIN/UPC/EAN supplied by reliable product data. A checksum-valid GTIN is stored as a zero-padded GTIN-14 so saves from different merchants can refer to one product identity; each saved merchant URL remains unchanged. `get_public_product` retrieves matching saves from opted-in public lists. See the [API guide](docs/API.md) for the limits of this matching.

Start with the [read → save → verify quickstart](docs/QUICKSTART.md). It covers REST, hosted MCP, and this repo's stdio bridge, then shows where the owner can confirm which approved agent saved an item.

## Choose a connection

**Remote MCP:** Connect to `https://mcp.shopsapp.com/mcp/` using Streamable HTTP. The original `https://shopsapp.com/mcp/` remains supported. OAuth-capable clients discover PKCE consent automatically; legacy approved bearer credentials are also supported. See [MCP setup](docs/MCP.md) for authorization and a protocol probe. The hosted endpoint exposes the full v0.2 toolset; this local bridge retains the core save/read/gift/recipe paths.

**JSON API:** Read `/.well-known/shopsapp.json` for discovery and `/openapi.json` for the schema. The [API guide](docs/API.md) maps common tasks to routes.

**Local stdio MCP bridge:** If an MCP client launches a local process, run this bridge. It calls the ShopsApp JSON API and never stores list data:

```sh
uv sync
SHOPSAPP_BASE_URL=http://127.0.0.1:5174 uv run python mcp_server.py
```

For private access, first request owner pairing with `start_agent_pairing`, show the person the approval URL, then exchange the private request secret after approval. Set the resulting revocable `ak_` token as `SHOPSAPP_TOKEN` in the MCP host’s secret or environment configuration. Do not paste a token into a chat, prompt, URL, or repository. The bridge allows plain HTTP only for loopback origins and does not follow redirects with credentials. It exposes public profile/list reads plus owner and permitted sharing, save, reservation, and handoff tools. The hosted server remains the full MCP interface.

## Use the skill

Point an assistant at [SKILL.md](skills/shopsapp/SKILL.md), or copy that file into its skill directory. The service also serves the same skill at `/skill.md` and a directly readable agent page at `/for-agents`. The [starter prompt](connect.md) is client-neutral; replace `{{SHOPSAPP_ORIGIN}}` with the origin the agent can reach.

The skill's central rules are simple: read only permitted lists, preserve saved URLs and attribution, ask before reserving, and leave checkout to separate authorized tools. Automatic watches support exact Shopify variants in the merchant's default market; other stores need observations from the agent's own tools. Alerts appear in-app, not email. Human recipients must accept invitations, and agents need separate shared-list consent.

## MCP registry metadata

[`server.json`](server.json) describes the live v0.2 hosted Streamable HTTP endpoint for the official MCP Registry. On 24 September 2026, the official publisher validated the manifest and an MCP SDK client verified HTTPS, tool discovery and rejection of unauthenticated private calls on both hosted endpoints. Registry publication is pending GitHub authorization for the `shopsapp-for-agents` organization. This manifest describes the remote server only; the local Python bridge remains a smaller compatibility adapter and is not published to a package registry. No agent token belongs in the manifest.

If the person asks an assistant to set up a new account, the `start_account_signup` tool can request a verification email after the person approves it. The person opens that email and finishes signup in their own browser. The assistant never receives the emailed link or owner credential. An agent starts a separate pairing request; the person approves the agent’s read or write access and list scope in ShopsApp, and the agent receives a revocable credential. This works only where ShopsApp has signup email delivery configured.

## Development

Use Python 3.12+ and [uv](https://docs.astral.sh/uv/):

```sh
uv sync --extra dev
uv run pytest -q
uv run ruff check .
```

The bridge's tests cover token isolation, exact URL preservation, transport security, and exposed tool names. For the ShopsApp service implementation and API behavior, use the live discovery JSON and OpenAPI schema at the deployed origin.

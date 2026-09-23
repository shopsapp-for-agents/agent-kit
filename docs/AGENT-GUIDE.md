# ShopsApp agent guide

ShopsApp stores product links in shopping and wish lists. It exposes those lists as JSON and MCP tools so a person or their assistant can save links, read permitted lists, coordinate gifts, and return the original merchant URL. ShopsApp does not search retailers, monitor prices, place orders, or handle a wallet. Use your own authorized tools for shopping research or a purchase, and get the user's approval before spending.

## Discover the service

| Resource | Path |
| --- | --- |
| Agent web view | `/for-agents` |
| Capability JSON | `/.well-known/shopsapp.json` |
| Public skill | `/skill.md` |
| OpenAPI JSON | `/openapi.json` |
| Streamable HTTP MCP | `/mcp/` |
| Shared starter prompt | `/connect.md` |

The public origin is `https://shopsapp.com`. When working against a local checkout, use its local origin instead. Start with capability JSON rather than assuming a feature exists.

## Access rules

- For a new user who asks the agent to begin setup, `POST /v1/agent-signups` with their approved email address requests a verification email. The agent receives only a `check_email` status. The person opens the email and finishes signup in their browser; account credentials are never returned to the agent. This route requires configured signup email delivery.
- Public profiles at `GET /v1/people/{alias}` and public lists at `GET /v1/public/lists/{slug}` need no credential.
- Agents request pairing with `POST /v1/agent-pairings`, show the owner only the approval URL, and exchange the private request secret after the owner chooses read/write and list scope. The resulting revocable `ak_` credential goes in the HTTP `Authorization: Bearer` header. Never ask for the owner’s `sa_` credential. A scoped list grant may also allow guest access. A private invitation URL alone grants no access; its named recipient must authenticate and accept it.
- Store credentials in the client's secret store or server configuration. Never put a bearer token in a prompt, chat message, URL, or public document.
- Respect the `capabilities` and `available_quantity` fields in list JSON. A grant may allow reading without editing or reserving.

## Common workflows

1. **Save a find:** Read the owner's lists, ask which one to use if unclear, and call `capture_url` with the exact URL. Preserve any creator or affiliate parameters and fragments. Use a stable idempotency key on retries.
2. **Research a purchase:** Read the chosen list, then use your own shopping tools to compare the same variant across sellers. Include shipping, return terms, and the observation time. Do not invent a live price, stock status, or price history.
3. **Watch an item:** If your agent has scheduled browsing and the user requests it, check for a price drop or restock and report the source and time. ShopsApp itself only stores the item.
4. **Choose a gift:** Read a public or permitted shared list, suggest available items, and ask the buyer before reserving one. A reservation coordinates with other list viewers; it is not a purchase.
5. **Hand off:** Call `get_handoff` and return `destination_url` unchanged. A separate commerce agent may use its own authorized checkout tools after the user approves spending. Do not rewrite tracking or claim a commission.

The full request and response contract is in [OpenAPI JSON](https://shopsapp.com/openapi.json). See [MCP setup](MCP.md) for transport and tool details.

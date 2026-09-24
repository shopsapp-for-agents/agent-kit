# ShopsApp agent guide

ShopsApp stores product links in shopping and wish lists. JSON and MCP tools let assistants resolve links, search permitted lists, coordinate gifts, and prepare groceries. It never creates orders or handles a wallet. Affiliate product feeds and cross-store comparisons are coming soon. Use your own authorized tools for broader shopping research or a purchase, and get the user's approval before spending.

## Discover the service

| Resource | Path |
| --- | --- |
| Agent web view | `/for-agents` |
| Read/save/verify quickstart | `/quickstart.md` |
| Capability JSON | `/.well-known/shopsapp.json` |
| Public skill | `/skill.md` |
| OpenAPI JSON | `/openapi.json` |
| Streamable HTTP MCP | `/mcp/` |
| Opt-in public trends | `/v1/trending` |
| Public GTIN matches | `/v1/products/{gtin}` |
| Shared starter prompt | `/connect.md` |

The public origin is `https://shopsapp.com`. When working against a local checkout, use its local origin instead. Start with capability JSON rather than assuming a feature exists.

## Access rules

- For a new user who asks the agent to begin setup, `POST /v1/agent-signups` with their approved email address requests a verification email. The agent receives only a `check_email` status. The person opens the email and finishes signup in their browser; account credentials are never returned to the agent. This route requires configured signup email delivery.
- Public profiles at `GET /v1/people/{alias}` and public lists at `GET /v1/public/lists/{slug}` need no credential.
- Agents request pairing with `POST /v1/agent-pairings`, show the owner only the approval URL, and exchange the private request secret after the owner chooses read/write and list scope. The resulting revocable `ak_` credential goes in the HTTP `Authorization: Bearer` header. Never ask for the owner’s `sa_` credential. A scoped list grant may also allow guest access. A private invitation URL alone grants no access; its named recipient must authenticate and accept it.
- Store credentials in the client's secret store or server configuration. Never put a bearer token in a prompt, chat message, URL, or public document.
- Respect the `capabilities` and `available_quantity` fields in list JSON. A grant may allow reading without editing or reserving.
- A newly saved item appears in the owner's list. The owner-only `GET /v1/me/agent-activity` shows which approved agent saved it, even if that agent is later revoked.

## Common workflows

1. **Save a find:** Read the owner's lists, ask which one to use if unclear, and call `capture_url` with the exact URL. Preserve any creator or affiliate parameters and fragments. Include a category if known; use `other` when uncertain. Include a GTIN/UPC/EAN only when the retailer or product data actually provides it. A valid check digit supports product matching across stores but does not verify the merchant's product claim. Use a stable idempotency key on retries.
2. **Research a purchase:** Read the chosen list, then use your own shopping tools to compare the same variant across sellers. Include shipping, return terms, and the observation time. Do not invent a live price, stock status, or price history.
3. **Watch an item:** At the user's request, use your own shopping tools and scheduler to monitor the saved exact variant in their local market. Send alerts through your agent. Confirm that your scheduler accepted the task before promising ongoing checks. ShopsApp does not check merchants or send alerts; report source, currency, shipping and observation time.
4. **Choose a gift:** Read a public or permitted shared list, suggest available items, and ask the buyer before reserving one. A reservation coordinates with other list viewers; it is not a purchase.
5. **Hand off:** Call `get_handoff` and return `destination_url` unchanged. A separate commerce agent may use its own authorized checkout tools after the user approves spending. Do not rewrite tracking or claim a commission.
6. **Explore trends:** Call `get_trending` or `GET /v1/trending` for the last 7 or 30 days. The results contain only saves from public lists whose owners opted into discovery; counts represent saved links, not sales.
7. **Prepare a recipe for groceries:** Preserve exact source ingredient strings. Use `set_recipe_ingredients` to record verified names, quantities, units, pantry flags, substitution preferences, and numeric base servings. `create_grocery_handoff` scales only explicit quantities and keeps the source text. Missing measurements require review. Your own authorized grocery integration supplies local product selection, images, prices, cart creation, and checkout. A provider shopping-page link is not a cart. ShopsApp always reports `cart_created:false` and `order_created:false`.

OAuth clients discover consent through `/.well-known/oauth-protected-resource`. Legacy pairing remains supported. Agents may use accepted friends' shares only if the user explicitly enabled shared-list access during consent; invitations must be accepted by the human recipient. `resolve_shopsapp_url` reads known ShopsApp URLs without browsing pages. Search includes only authorized lists and separately opted-in public lists; a private denial does not reveal whether a list exists. List context can record an occasion, date, and preferences; item priority is 0–5, with 0 unspecified.

The full request and response contract is in [OpenAPI JSON](https://shopsapp.com/openapi.json). See [MCP setup](MCP.md) for transport and tool details.

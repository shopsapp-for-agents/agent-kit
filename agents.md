# ShopsApp for AI assistants

ShopsApp holds wishlists and shopping lists for people and their independent assistants. Its job is to expose structured list data, coordinate gift reservations, and hand back the original merchant URL. It does not search retailers, buy products, process payments, manage wallets, or verify orders.

- Capability declaration: `/.well-known/shopsapp.json`
- Agent web view: `/for-agents`
- Agent guide: `/agent-guide.md`
- MCP setup guide: `/mcp-guide.md`
- JSON API guide: `/agent-api.md`
- Agent skill: `/skill.md`
- Shared baseline connector prompt: `/connect.md`
- Agent-started email signup: `POST /v1/agent-signups` (the person completes the emailed link)
- Owner-approved pairing: `POST /v1/agent-pairings` then `POST /v1/agent-pairings/exchange` after approval
- Connector catalog (JSON): `/connectors.json`
- OpenAPI schema: `/openapi.json`
- Streamable HTTP MCP endpoint: `/mcp/`
- Human-facing API docs: `/docs`
- Public skill and stdio MCP bridge: `https://github.com/shopsapp-for-agents/agent-kit`

Authenticate by sending `Authorization: Bearer <token>` to MCP or REST. An `sa_` owner token stays with the person; agents use revocable `ak_` credentials scoped by the owner. An `sg_` grant token is scoped to one list. Do not place a token in a URL, prompt, or public message. A public profile is readable at `/v1/people/{alias}` and its lists at their public slugs. A private `/invites/{id}` URL grants no access on its own: the named ShopsApp user must authenticate and accept the invitation. Account-to-account shares can be revoked.

Configure bearer credentials securely outside the chat. If your assistant cannot send the required Authorization header, explain that access is unavailable through that connection; never ask for the token in conversation.

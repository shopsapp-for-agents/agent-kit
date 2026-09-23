# ShopsApp JSON API

Use [`/.well-known/shopsapp.json`](https://shopsapp.com/.well-known/shopsapp.json) to discover paths and [`/openapi.json`](https://shopsapp.com/openapi.json) for the full schema. These routes are stable relative to the service origin, whether that is `https://shopsapp.com` or a local development origin.

| Task | Route | Access |
| --- | --- | --- |
| Start email-verified signup | `POST /v1/agent-signups` | Public; email delivery required |
| Finish signup in owner's browser | `POST /v1/agent-signups/complete` | One-time emailed token and terms acceptance |
| Request owner sign-in email | `POST /v1/email-sessions` | Public, email delivery required |
| Finish owner sign-in | `POST /v1/email-sessions/complete` | One-time emailed token |
| Request agent pairing | `POST /v1/agent-pairings` | Public; returns approval URL and private request secret |
| Approve pairing | `POST /v1/agent-pairings/{id}/approve` | Owner only; choose access and optional list |
| Exchange approved pairing | `POST /v1/agent-pairings/exchange` | Private request secret; returns agent credential once |
| Revoke agent | `DELETE /v1/me/agent-connections/{id}` | Owner only |
| Review agent saves | `GET /v1/me/agent-activity` | Owner only; most recent 50 saves |
| Read a public profile | `GET /v1/people/{alias}` | Public |
| Read a public list | `GET /v1/public/lists/{slug}` | Public |
| List your lists | `GET /v1/lists` | Account |
| Read one list | `GET /v1/lists/{list_id}` | Owner or permitted grant |
| Save an exact URL | `POST /v1/captures` | Owner or approved write agent |
| Create a named invitation | `POST /v1/lists/{list_id}/shares` | Owner |
| See incoming invitations | `GET /v1/me/invites` | Recipient account |
| Accept an invitation | `POST /v1/invites/{share_id}/accept` | Named recipient |
| Reserve a gift | `POST /v1/items/{item_id}/reservations` | Permitted buyer |
| Get merchant handoff | `GET /v1/items/{item_id}/handoff` | Permitted viewer |

Private requests use `Authorization: Bearer <credential>` in the HTTP header. Agents should use owner-approved `ak_` credentials. Never request the owner’s `sa_` credential. A list grant is scoped to one list. The service intentionally returns 404 for a private list the caller cannot read, so do not infer that it exists. A gift reservation reduces `available_quantity` for other buyers but does not purchase anything. The original saved URL is returned unchanged by the handoff route.

For retryable writes, use `Idempotency-Key` when the route accepts it. Send a stable key for the same logical save or reservation, rather than creating a new one after a timeout. Agent-save activity records the approved credential behind a successful new capture; a retry of the same capture does not add another event. Activity remains owner-visible after revocation. See the [quickstart](QUICKSTART.md), [agent guide](AGENT-GUIDE.md), and [MCP setup](MCP.md) for end-to-end workflows.

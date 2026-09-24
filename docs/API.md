# ShopsApp JSON API

Use the interactive [REST API reference](https://shopsapp.com/docs/api), [`/.well-known/shopsapp.json`](https://shopsapp.com/.well-known/shopsapp.json) to discover paths, and [`/openapi.json`](https://shopsapp.com/openapi.json) for the full machine-readable schema. These routes are stable relative to the service origin, whether that is `https://shopsapp.com` or a local development origin. Start with the [agent connection guide](https://shopsapp.com/docs) if you are connecting an MCP client rather than building a direct REST integration.

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
| Explore opt-in public saves | `GET /v1/trending?days=7&category=home` | Public; `days` is 7 or 30, category optional |
| Find matching public saves by GTIN | `GET /v1/products/{gtin}` | Public; only separately opted-in lists, format-checked identifier |
| List your lists | `GET /v1/lists` | Account |
| Change public list discovery | `PATCH /v1/lists/{list_id}/discovery` | Owner only; body `{"discoverable":true}`; public list only |
| Read one list | `GET /v1/lists/{list_id}` | Owner or permitted grant |
| Save an exact URL | `POST /v1/captures` | Owner or approved write agent |
| Search saved recipes | `GET /v1/recipes?q=lemon` | Owner or approved read agent; only accessible owned lists |
| Correct recipe ingredients | `PUT /v1/recipes/{item_id}` | Owner or approved write agent |
| Get grocery handoff JSON | `GET /v1/recipes/{item_id}/grocery-handoff` | Permitted list viewer |
| Create a named invitation | `POST /v1/lists/{list_id}/shares` | Owner |
| See incoming invitations | `GET /v1/me/invites` | Recipient account |
| Accept an invitation | `POST /v1/invites/{share_id}/accept` | Named recipient |
| Reserve a gift | `POST /v1/items/{item_id}/reservations` | Permitted buyer |
| Get merchant handoff | `GET /v1/items/{item_id}/handoff` | Permitted viewer |
| Resolve a ShopsApp URL without HTML | `GET /v1/resolve?url=...` | Public or permission-scoped |
| Search accessible or opted-in public lists | `GET /v1/search/lists?query=...` | Permission-scoped |
| Search accessible items | `GET /v1/search/items?query=...&list_id=...` | Permission-scoped |
| Add occasion/date/preferences | `PATCH /v1/lists/{list_id}/context` | Owner or scoped write agent |
| Set item priority (0–5) | `PATCH /v1/items/{item_id}/priority` | Owner or scoped write agent |
| Store verified structured ingredients | `PUT /v1/recipes/{item_id}/ingredients` | Owner or scoped write agent |
| Scale and prepare grocery ingredients | `POST /v1/recipes/{item_id}/grocery-handoff` | Permitted viewer; no cart mutation |
| Affiliate product discovery | `GET /v1/discovery/products` | Coming soon; no offers returned |

OAuth metadata is at `/.well-known/oauth-protected-resource` and `/.well-known/oauth-authorization-server`. Public clients use S256 PKCE and exact registered callback URLs. Legacy `ak_` pairing remains available. OAuth access tokens are short-lived and refresh tokens rotate. The owner can decline consent or revoke the underlying agent grant. Shared lists require separate consent plus a human-accepted invitation. No agent receives the owner's credential.

Price and stock monitoring, scheduling, and notifications use the person's own agent. ShopsApp has no watch or alert API. Structured grocery handoffs contain source text, quantities, pantry and substitution preferences, but delegate product images, local prices and cart creation to the user's grocery provider. An Instacart shopping-page mapping is not an existing cart. No Instacart credential is configured in ShopsApp.

Private requests use `Authorization: Bearer <credential>` in the HTTP header. Agents should use owner-approved `ak_` credentials. Never request the owner’s `sa_` credential. A list grant is scoped to one list. The service intentionally returns 404 for a private list the caller cannot read, so do not infer that it exists. A gift reservation reduces `available_quantity` for other buyers but does not purchase anything. The original saved URL is returned unchanged by the handoff route.

`POST /v1/captures` accepts optional `category` (`fashion`, `home`, `tech`, `beauty`, `books`, `hobbies`, `food`, `other`) and `gtin` (8, 12, 13, or 14 digits with a valid check digit). A supplied GTIN is zero-padded to GTIN-14 and links saves to one product identity across merchants. The item JSON includes a product reference with a `/v1/products/{gtin}` URL for opted-in public matches. ShopsApp checks the number's format, not whether the merchant's claim is genuine. Do not guess a GTIN from a URL or title. Items without one remain separate, and the exact saved merchant URLs are never replaced. Older items default to `other`.

Every item includes `link_assessment: {status, reason_code, checked_live:false}`. The statuses are `likely_product` (a product path, supplied identifier, or observed Schema.org Product), `inspiration` (a recognized social post/video or an explicitly identified inspiration page), `unverified` (the URL gives insufficient evidence), and `recipe`. A capture may include `page_type: "product"` only when the client actually observed Product structured data; `page_type: "inspiration"` marks content that is not a direct offer. These are cheap hints, not a fetch, availability check, or guarantee of a purchasable item. Older captures remain `unverified`. `GET /v1/items/{item_id}/handoff` includes the assessment and `next_step` (`research_product`, `resolve_inspiration`, `verify_link`, or `read_recipe`). For inspiration or unverified links, investigate before treating the destination as a store. Saving always keeps the exact URL and existing referral parameters.

Lists may use `mode: "recipe"`. A capture in a recipe list, a recipe-shaped URL, or a capture with `recipe` data becomes a recipe item. Send `"recipe":{"ingredients":["200 g pasta","1 lemon"],"servings":"2 servings"}` when ingredients are available. The extension reads Schema.org Recipe JSON-LD on the current page and sends its ingredient strings; the API does not fetch submitted URLs. A URL alone is saved with `status: "needs_ingredients"`. The user or a write-approved agent can add or correct ingredients later. Recipe title and ingredient words are indexed for permission-scoped search. The grocery handoff returns those strings, the unchanged source URL, and an Instacart developer recipe-page pointer. It never places an order; an external agent must review ingredients and obtain shopping approval.

Trending includes only saves on public lists whose owners separately enabled discovery. New lists are not discoverable by default. Its JSON gives total saves, category counts, and the latest 24 opted-in items for the requested window and category. It is a view of saves, not orders or verified demand.

For retryable writes, use `Idempotency-Key` when the route accepts it. Send a stable key for the same logical save or reservation, rather than creating a new one after a timeout. Agent-save activity records the approved credential behind a successful new capture; a retry of the same capture does not add another event. Activity remains owner-visible after revocation. See the [quickstart](QUICKSTART.md), [agent guide](AGENT-GUIDE.md), and [MCP setup](MCP.md) for end-to-end workflows.

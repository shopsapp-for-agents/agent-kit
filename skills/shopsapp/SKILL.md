---
name: shopsapp
description: Use when saving product URLs to ShopsApp lists, reading permitted wishlists, coordinating gifts, or handing original merchant links to separate shopping tools.
---

# ShopsApp agent skill

Use this skill when a user asks you to save a product URL to their list, inspect a permitted friend's list, compare items, choose a gift, reserve it, or get the merchant link. ShopsApp does not perform checkout or use a wallet. If the user explicitly asks you to buy and you have separate authorized shopping tools, use those tools outside ShopsApp after getting approval to spend.

For shopping research, use your own authorized search or browsing tools to compare the same variant across sellers, including shipping and return terms. If the user asks for price-drop or restock monitoring, do so only if you have a scheduled browsing capability; ShopsApp stores the list but does not monitor prices. Report the source and observation time, and never invent a live price or availability.

## Discover and connect

The public origin is `https://shopsapp.com`; use the local deployment's origin when testing locally. Fetch `/.well-known/shopsapp.json` for capability URLs. The REST schema is `/openapi.json`; MCP Streamable HTTP is `/mcp/`. The agent web view is `/for-agents`, the shared starter prompt is `/connect.md`, and `/connectors.json` lists prompt targets. The [agent guide](https://shopsapp.com/agent-guide.md), [MCP setup guide](https://shopsapp.com/mcp-guide.md), and [public agent kit](https://github.com/shopsapp-for-agents/agent-kit) provide connection details and a local stdio MCP bridge. A person's `@alias` link points to a human profile, and `get_public_profile` (or `GET /v1/people/{alias}`) returns their public lists as JSON. Private access requires a bearer credential configured in the connector's HTTP Authorization header. Never ask for or paste a bearer token into conversation, tool arguments, URL query parameters, or a prompt. `sa_` is an account token; `sg_` is a one-list grant. Private lists are hidden unless the credential allows access. A `can_reserve` capability in list JSON tells you whether you may reserve.

## Owner workflow

1. Use `list_my_lists` to find the owner's list, or `create_list` when asked to make one.
2. When the user shares a URL, call `capture_url` with the exact URL, an accurate title, optional variant and quantity, and a stable idempotency key if retrying. Preserve the original URL, including any existing affiliate or tracking code. Do not follow it and substitute a canonical URL.
3. Prefer `invite_person` with the recipient's claimed alias for another ShopsApp user. The invite URL contains only an opaque invitation ID; the recipient must authenticate and accept it before their account or agent can read the list. Share that URL with the intended recipient, but do not imply that possession of the link grants access. Use `can_reserve=true` only for a wishlist when the recipient should be able to claim gifts. The owner can revoke a share.
4. For a guest without an account, create a one-list grant with the narrowest useful capability and deliver its one-time secret through a secure channel. The owner can revoke a grant.

## Gift buyer workflow

1. For a public `@alias` link, call `get_public_profile` and choose a list. For a private account invitation, call `list_my_invites`, accept the intended invitation, and then call `list_shared_with_me` or `get_list` using the buyer's account credential. A scoped grant or public slug also works. Use titles, variants, quantity, `available_quantity` when present, and any preferences explicitly supplied by the recipient. Do not invent prices, availability at the retailer, shipping, or product metadata.
2. Suggest a short set of suitable items. Ask the buyer to choose before reserving. Reserve one available unit with `reserve_item`; use an idempotency key if retrying.
3. Call `get_handoff` and pass `destination_url` unchanged to the buyer or their separate commerce agent. If you are also the commerce agent, use your own authorized tools and get the buyer's approval before spending. ShopsApp never executes checkout. The URL may already credit a creator or another referrer. Do not append ShopsApp tracking parameters, overwrite cookies, run a simulated click, or imply that ShopsApp receives a commission.
4. `report_acquired` is only a buyer's unverified coordination report. Call it after the buyer tells you the item was acquired. `release_reservation` frees an abandoned claim.

If a tool reports access denied or unavailable quantity, explain the limit and ask for a valid grant or another item. Never infer private list existence from a denial.

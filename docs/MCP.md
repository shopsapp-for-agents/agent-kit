# ShopsApp MCP

ShopsApp provides a Streamable HTTP MCP endpoint at `https://shopsapp.com/mcp/`. Use the trailing slash. For a local deployment, use its local origin, such as `http://127.0.0.1:5174/mcp/`. The server is part of the ShopsApp API and uses the same authorization and list permissions as REST.

The [public agent kit](https://github.com/shopsapp-for-agents/agent-kit) also contains a small **stdio MCP bridge** for clients that can launch a local process but cannot connect to a remote MCP URL. The bridge calls the ShopsApp JSON API; it does not store lists or credentials itself.

## Connect securely

- Choose **Streamable HTTP** in a client that supports remote MCP and enter the endpoint URL above. Configure an account or scoped list-grant bearer credential through the client's secure authorization settings. Do not paste a token into the assistant conversation.
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

## Permission and attribution rules

An `sa_` account token accesses one user's account. An `sg_` grant token is scoped to one list and may permit reservations. Share or grant revocation stops later reads and actions. Never place either credential in a URL or prompt. `get_handoff` returns the original saved merchant URL, including existing affiliate attribution; do not replace it or simulate a referral click. ShopsApp has no payment or wallet tool.

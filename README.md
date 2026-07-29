# LearnToBuildMCPServers

Phase 2 of learning MCP hands-on: **building** servers, not just calling them (that was [`LearnToCallMCPServers`](../LearnToCallMCPServers), Phase 1). Same shallow-to-deep approach — each script adds exactly one new concept on top of the last.

## Setup

```bash
uv sync
```

Create a `.env` file with:

```bash
GITHUB_OAUTH_CLIENT_ID=...      # same OAuth App from LearnToCallMCPServers -- reused, not a new one
GITHUB_OAUTH_CLIENT_SECRET=...
GITHUB_PAT=...                  # a GitHub Personal Access Token, for quickly testing script 6 without a full browser flow

# Only if you're behind a proxy:
http_proxy=http://127.0.0.1:PORT
https_proxy=http://127.0.0.1:PORT
no_proxy=localhost,127.0.0.1
```

## The scripts, in order

### 1-2. [`1_calculator_server.py`](1_calculator_server.py) + [`2_test_calculator_client.py`](2_test_calculator_client.py) — your first server
Three tools (`add`, `word_count`, `reverse_list`) via `FastMCP`, stdio transport, schema generated automatically from type hints + docstrings. The test client spawns it and calls each tool, same stdio pattern as Phase 1.

**Key lesson**: tool results carry two representations — `content` (display-oriented; a `list` return value becomes *one block per element*, not one block with the whole list) and `structuredContent` (the actual typed value). Always read `structuredContent` for real data.

### 3-4. [`3_remote_calculator_server.py`](3_remote_calculator_server.py) + [`4_test_remote_calculator_client.py`](4_test_remote_calculator_client.py) — same server, remote transport
Identical tools to script 1 — the only change is `mcp.run(transport="streamable-http")` instead of stdio. Deliberately isolates "local vs remote" down to the one line that actually differs. This server doesn't get spawned by the client; you start it yourself and the client connects to `http://127.0.0.1:8000/mcp`.

### 5-7. GitHub-authenticated server
- [`5_github_auth_calculator_server.py`](5_github_auth_calculator_server.py) — the server requires a valid bearer token. Implements `TokenVerifier` (checks incoming tokens against `api.github.com/user` — GitHub is the authorization server, this server holds no user database, no secrets about *users* at all) plus `AuthSettings`, which makes the server publish RFC 9728 Protected Resource Metadata at `/.well-known/oauth-protected-resource/mcp` — the same kind of document GitHub's own real MCP server publishes.
- [`6_test_github_auth_calculator_client.py`](6_test_github_auth_calculator_client.py) — quick verification: an unauthenticated request (expect `401` + `WWW-Authenticate`), then an authenticated one using a plain PAT from `.env`.
- [`7_real_oauth_calculator_client.py`](7_real_oauth_calculator_client.py) — the realistic version of script 6's client: instead of a manually-supplied PAT, it runs the actual PKCE authorization-code flow (reusing `GitHubOAuthClientProvider` from `LearnToCallMCPServers/5_remote_github_oauth_client.py` verbatim), discovering GitHub as the trusted authorization server *from our own server's* metadata rather than hardcoding it.

**Key lesson**: `client_id` on an `AccessToken` means the OAuth *application*, not the user — `subject` is where user identity belongs. Also: opaque tokens (what GitHub uses) require a live check per request; JWTs would allow local signature verification instead, at the cost of instant revocation.

### 8-9. [`8_calculator_with_resources_and_prompts.py`](8_calculator_with_resources_and_prompts.py) + [`9_test_resources_prompts_client.py`](9_test_resources_prompts_client.py) — all three MCP primitives
Adds a **Resource** (`calc://history`, addressable by URI, read-only, populated by the tools' side effects) and a **Prompt** (`explain_calculation`, a parameterized template).

**Key lesson** — the real distinction between the three primitives isn't mechanical, it's about *who decides when it's used*:
- **Tools** = model-controlled (the LLM decides mid-conversation to call it — even a pure "go get some data" operation like `fetch` or `get_me` is a Tool if the *AI* is the one deciding to invoke it)
- **Resources** = client/application-controlled (addressable data a host app or user decides to pull into context — the AI doesn't autonomously "call" these the way it calls Tools)
- **Prompts** = user-controlled (a human explicitly picks a pre-written template, like a slash command)

## Suggested path

**1/2 → 3/4 → 5/6/7 → 8/9**, in order — each stage assumes the previous one's concepts. Scripts 5-7 need the GitHub OAuth App from `LearnToCallMCPServers` set up first (see that repo's README).

import os

import httpx
from dotenv import load_dotenv
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

load_dotenv()

PORT = 8001
RESOURCE_URL = f"http://127.0.0.1:{PORT}/mcp"

# GitHub is the authorization server -- we never issue or store tokens
# ourselves, we just check whatever bearer token a client sends us against
# GitHub's own API. Same OAuth App / trust relationship as Phase 1's
# scripts 5-7, just from the resource-server side this time.
ISSUER_URL = "https://github.com/login/oauth"


class GitHubTokenVerifier(TokenVerifier):
    """Delegates all verification to GitHub -- we hold no secrets, no user
    database, nothing. A valid response from GitHub's API IS the proof."""

    async def verify_token(self, token: str) -> AccessToken | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code != 200:
            return None

        user = resp.json()
        return AccessToken(
            token=token,
            # client_id = which OAuth CLIENT (application) is presenting this
            # token -- not the user. GitHub's plain /user check doesn't tell
            # us which app a bare token belongs to (that needs a separate,
            # differently-authenticated "check a token" API call), so we use
            # our own registered OAuth App's id as the best available answer
            # -- defensible here since every token this server will ever see
            # was obtained through our one app, but not a general solution.
            client_id=os.environ["GITHUB_OAUTH_CLIENT_ID"],
            scopes=[],
            # subject = the resource OWNER (the actual human) -- this is what
            # user["login"] belongs in. A tool that needs "which user is
            # calling me right now" (e.g. "list MY notes") would read this
            # via the request context, not client_id.
            subject=user.get("login"),
        )


mcp = FastMCP(
    "calculator",
    host="127.0.0.1",
    port=PORT,
    token_verifier=GitHubTokenVerifier(),
    auth=AuthSettings(
        issuer_url=ISSUER_URL,
        resource_server_url=RESOURCE_URL,
    ),
)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool()
def word_count(text: str) -> int:
    """Count the number of whitespace-separated words in a string."""
    return len(text.split())


@mcp.tool()
def reverse_list(items: list[str]) -> list[str]:
    """Reverse the order of a list of strings."""
    return list(reversed(items))


if __name__ == "__main__":
    # This also makes the server publish RFC 9728 Protected Resource
    # Metadata at /.well-known/oauth-protected-resource -- the exact same
    # kind of document we fetched from GitHub's real MCP server earlier.
    mcp.run(transport="streamable-http")

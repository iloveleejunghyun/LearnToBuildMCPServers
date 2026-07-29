"""
A real OAuth client -- same PKCE + local-callback-server machinery as
LearnToCallMCPServers/5_remote_github_oauth_client.py, just pointed at OUR
OWN server instead of GitHub's. This is what actually exercises the
discovery flow: 401 -> Protected Resource Metadata -> GitHub's OAuth
endpoints -> browser consent -> token -> our server's verify_token.
"""

import asyncio
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata, OAuthToken

load_dotenv()

# Our own server, not GitHub's -- everything downstream of this URL is
# discovered dynamically from what OUR server's Protected Resource Metadata
# declares (which happens to point back at GitHub, same as before).
SERVER_URL = "http://127.0.0.1:8001/mcp"

REDIRECT_PORT = 3030
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

CLIENT_ID = os.environ["GITHUB_OAUTH_CLIENT_ID"]
CLIENT_SECRET = os.environ["GITHUB_OAUTH_CLIENT_SECRET"]


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        if "code" in params:
            self.server.auth_code = params["code"][0]  # type: ignore[attr-defined]
            self.server.auth_state = params.get("state", [None])[0]  # type: ignore[attr-defined]
            body = b"<html><body>Authorized! You can close this tab and return to the terminal.</body></html>"
            self.send_response(200)
        else:
            self.server.auth_error = params.get("error", ["unknown_error"])[0]  # type: ignore[attr-defined]
            body = b"<html><body>Authorization failed. Check the terminal.</body></html>"
            self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


class InMemoryTokenStorage(TokenStorage):
    def __init__(self, client_id: str, client_secret: str):
        self._tokens: OAuthToken | None = None
        self._client_info = OAuthClientInformationFull(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uris=[REDIRECT_URI],  # type: ignore[list-item]
            token_endpoint_auth_method="client_secret_post",
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
        )

    async def get_tokens(self) -> OAuthToken | None:
        return self._tokens

    async def set_tokens(self, tokens: OAuthToken) -> None:
        self._tokens = tokens

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        return self._client_info

    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        self._client_info = client_info


class GitHubOAuthClientProvider(OAuthClientProvider):
    """Same fix as before: GitHub's token endpoint returns form-encoded
    data by default; ask for JSON explicitly."""

    async def _exchange_token_authorization_code(self, *args, **kwargs) -> httpx.Request:
        request = await super()._exchange_token_authorization_code(*args, **kwargs)
        request.headers["Accept"] = "application/json"
        return request

    async def _refresh_token(self) -> httpx.Request:
        request = await super()._refresh_token()
        request.headers["Accept"] = "application/json"
        return request


async def redirect_handler(auth_url: str) -> None:
    print(f"\nOpening your browser to authorize with GitHub:\n{auth_url}\n")
    webbrowser.open(auth_url)


async def callback_handler() -> tuple[str, str | None]:
    server = HTTPServer(("localhost", REDIRECT_PORT), _CallbackHandler)
    server.auth_code = None  # type: ignore[attr-defined]
    server.auth_state = None  # type: ignore[attr-defined]
    server.auth_error = None  # type: ignore[attr-defined]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Listening for GitHub's OAuth callback on {REDIRECT_URI} ...")

    try:
        deadline = time.time() + 120
        while time.time() < deadline:
            if server.auth_code:  # type: ignore[attr-defined]
                return server.auth_code, server.auth_state  # type: ignore[attr-defined]
            if server.auth_error:  # type: ignore[attr-defined]
                raise RuntimeError(f"OAuth error from GitHub: {server.auth_error}")  # type: ignore[attr-defined]
            await asyncio.sleep(0.2)
        raise TimeoutError("Timed out waiting for you to authorize in the browser")
    finally:
        server.shutdown()
        thread.join(timeout=1)


async def main() -> None:
    oauth_provider = GitHubOAuthClientProvider(
        server_url=SERVER_URL,
        client_metadata=OAuthClientMetadata(
            client_name="LearnToBuildMCPServers demo",
            redirect_uris=[REDIRECT_URI],  # type: ignore[list-item]
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_post",
        ),
        storage=InMemoryTokenStorage(CLIENT_ID, CLIENT_SECRET),
        redirect_handler=redirect_handler,
        callback_handler=callback_handler,
    )

    # The new streamable_http_client takes a pre-configured httpx.AsyncClient
    # for auth, rather than an `auth=` kwarg directly -- OAuthClientProvider
    # is an httpx.Auth, so this is a straight drop-in.
    authed_client = httpx.AsyncClient(auth=oauth_provider)

    async with streamable_http_client(SERVER_URL, http_client=authed_client) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Authorized against our OWN server, via a real GitHub OAuth flow!")

            tools = await session.list_tools()
            print(f"Tools: {[t.name for t in tools.tools]}")

            result = await session.call_tool("add", {"a": 10, "b": 32})
            print(f"add(10, 32) -> {result.structuredContent['result']}")


if __name__ == "__main__":
    asyncio.run(main())

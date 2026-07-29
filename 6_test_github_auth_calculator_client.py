import asyncio
import os

import httpx
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

load_dotenv()

URL = "http://127.0.0.1:8001/mcp"


async def try_without_token() -> None:
    print("--- Attempt 1: no token at all ---")
    try:
        async with streamable_http_client(URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("Connected with no token?! (unexpected)")
    except Exception as e:
        print(f"Rejected as expected: {type(e).__name__}: {str(e)[:300]}")


async def try_with_token() -> None:
    print("\n--- Attempt 2: with a real GitHub token ---")
    token = os.environ["GITHUB_PAT"]
    authed_client = httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"})

    async with streamable_http_client(URL, http_client=authed_client) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Authorized!")

            result = await session.call_tool("add", {"a": 2, "b": 5})
            print(f"add(2, 5) -> {result.structuredContent['result']}")


async def main() -> None:
    await try_without_token()
    await try_with_token()


if __name__ == "__main__":
    asyncio.run(main())

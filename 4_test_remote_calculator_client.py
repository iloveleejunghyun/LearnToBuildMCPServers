import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv

load_dotenv()
# Same Streamable HTTP transport we used against DeepWiki and GitHub's
# remote servers in Phase 1 -- except this time we're pointing it at our
# own server instead of someone else's.
URL = "http://127.0.0.1:8000/mcp"


async def main() -> None:
    async with streamable_http_client(URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools exposed by our remote calculator server:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

            add_result = await session.call_tool("add", {"a": 3, "b": 4.5})
            print(f"\nadd(3, 4.5) -> {add_result.structuredContent['result']}")

            wc_result = await session.call_tool("word_count", {"text": "the quick brown fox"})
            print(f"word_count('the quick brown fox') -> {wc_result.structuredContent['result']}")

            rev_result = await session.call_tool("reverse_list", {"items": ["a", "b", "c"]})
            print(f"reverse_list(['a', 'b', 'c']) -> {rev_result.structuredContent['result']}")


if __name__ == "__main__":
    asyncio.run(main())

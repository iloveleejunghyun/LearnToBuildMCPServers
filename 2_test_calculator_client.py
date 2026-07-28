import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Same stdio pattern as LearnToCallMCPServers/1_local_fetch_client.py, except
# this time we're spawning OUR OWN server instead of someone else's --
# the client side doesn't care who wrote the server it's talking to.
server_params = StdioServerParameters(
    command="uv",
    args=["run", "1_calculator_server.py"],
)


async def main() -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools exposed by our calculator server:")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
                print(f"  schema: {tool.inputSchema}")

            add_result = await session.call_tool("add", {"a": 3, "b": 4.5})
            print(f"\nadd(3, 4.5) -> {add_result.structuredContent['result']}")

            wc_result = await session.call_tool("word_count", {"text": "the quick brown fox"})
            print(f"word_count('the quick brown fox') -> {wc_result.structuredContent['result']}")

            rev_result = await session.call_tool("reverse_list", {"items": ["a", "b", "c"]})
            # A list return value becomes MULTIPLE content blocks (one per
            # element, meant for display), not one block with the whole list
            # -- content[0].text would only ever be the first element.
            # structuredContent carries the actual typed value instead.
            print(f"reverse_list(['a', 'b', 'c']) -> {rev_result.structuredContent['result']}")


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="uv",
    args=["run", "8_calculator_with_resources_and_prompts.py"],
)


async def main() -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call a couple of tools first so the history resource has
            # something to show -- this is the tool -> resource link.
            await session.call_tool("add", {"a": 2, "b": 2})
            await session.call_tool("word_count", {"text": "hello there world"})

            print("=== Tools ===")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f"- {tool.name}")

            print("\n=== Resources ===")
            resources = await session.list_resources()
            for resource in resources.resources:
                print(f"- {resource.uri}: {resource.name}")

            history = await session.read_resource("calc://history")
            print("\ncalc://history contents:")
            print(history.contents[0].text)

            print("\n=== Prompts ===")
            prompts = await session.list_prompts()
            for prompt in prompts.prompts:
                print(f"- {prompt.name}: {prompt.description}")
                for arg in prompt.arguments or []:
                    print(f"    arg: {arg.name} (required={arg.required})")

            rendered = await session.get_prompt(
                "explain_calculation", {"expression": "(3 + 4) * 2"}
            )
            print("\nexplain_calculation('(3 + 4) * 2') renders to:")
            for message in rendered.messages:
                print(f"  [{message.role}] {message.content.text}")


if __name__ == "__main__":
    asyncio.run(main())

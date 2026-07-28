from mcp.server.fastmcp import FastMCP

# FastMCP builds the tool schema straight from each function's type hints and
# docstring -- no manual JSON Schema like we wrote by hand for Gemini back in
# LearnToCallMCPServers/2_agent_fetch_client.py. This is the server-side
# mirror of that: instead of consuming a schema, we're now the one producing it.
mcp = FastMCP("calculator") # Why does it need a name?


@mcp.tool()
def add(a: float, b: float) -> float: # I see similar structure in a guide of tool calling.
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
    mcp.run()  # defaults to stdio transport -- same as every local server we used in Phase 1

from mcp.server.fastmcp import FastMCP

# Same three tools as 1_calculator_server.py, unchanged -- the only thing
# that's actually different in this file is the transport at the bottom.
# That's deliberate: it isolates "local vs remote" down to exactly the one
# thing that's really different, same as DeepWiki vs the fetch server back
# in LearnToCallMCPServers Phase 1.
mcp = FastMCP("calculator")


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
    # Defaults: host="127.0.0.1", port=8000, path="/mcp" -- so the server
    # will be reachable at http://127.0.0.1:8000/mcp. No process to spawn
    # this time -- a client connects to an address instead of us starting it.
    mcp.run(transport="streamable-http")

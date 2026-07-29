from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calculator")

# In-memory calculation history. Tools WRITE to this (the model actively
# doing something); the Resource below READS it (passive, addressable
# data). That link is the whole point of this file.
_history: list[str] = []


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    result = a + b
    _history.append(f"add({a}, {b}) = {result}")
    return result


@mcp.tool()
def word_count(text: str) -> int:
    """Count the number of whitespace-separated words in a string."""
    result = len(text.split())
    _history.append(f"word_count({text!r}) = {result}")
    return result


@mcp.tool()
def reverse_list(items: list[str]) -> list[str]:
    """Reverse the order of a list of strings."""
    result = list(reversed(items))
    _history.append(f"reverse_list({items}) = {result}")
    return result


# A Resource: addressable, readable data (identified by a URI, same idea as
# a file path) that a CLIENT decides to pull in -- the model never "calls"
# this the way it calls a tool above. Nothing about reading this causes any
# computation; it just reports state that already exists.
@mcp.resource("calc://history") # Why do we need this param? "calc://history"
def get_history() -> str:
    """The log of every calculation performed so far, most recent last."""
    if not _history:
        return "No calculations yet."
    return "\n".join(_history)


# A Prompt: a reusable, parameterized template meant for a HUMAN to
# explicitly pick (like a slash command in a chat client), not something
# the model reaches for on its own mid-conversation.
@mcp.prompt()
def explain_calculation(expression: str) -> list[dict]:
    """Ask the model to explain, step by step, how to compute an expression."""
    return [
        {
            "role": "user",
            "content": f"Explain step by step how to compute: {expression}",
        }
    ]


if __name__ == "__main__":
    mcp.run()

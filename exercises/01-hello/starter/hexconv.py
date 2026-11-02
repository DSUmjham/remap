"""Exercise 1: your first MCP tool. Work through the TODOs, top to bottom."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hexconv")


# TODO 1: register this function as a tool by adding the @mcp.tool() decorator.
def to_hex(value: int) -> str:
    # TODO 2: replace this comment with a docstring. The model reads it to decide
    #         when to call the tool, so say what it does and what it returns.
    # TODO 3: raise ValueError if value is negative; otherwise return hex(value).
    raise NotImplementedError("finish to_hex")


# TODO 4: add a second tool, from_hex(text: str) -> int, that accepts text with or
#         without a 0x prefix (and with stray spaces) and returns the integer.
#         Hint: int(text, 16), str.strip(), str.removeprefix().


if __name__ == "__main__":
    mcp.run()  # stdio transport: the lab's mcpo launches this file and talks to it

"""Minimal MCP tool. Served at http://localhost:8001/hello (Swagger at /hello/docs)."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


if __name__ == "__main__":
    mcp.run()  # stdio; mcpo launches this file

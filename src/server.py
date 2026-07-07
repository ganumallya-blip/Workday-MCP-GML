"""FastMCP server entry point for Workday MCP Phase 1."""
from mcp.server.fastmcp import FastMCP
from src.tools.auth_tools import authenticate_workday as authenticate_workday_impl

mcp = FastMCP("workday-mcp")

@mcp.tool()
async def authenticate_workday(user_id: str) -> dict[str, str]:
    """Authenticate an employee with their own Workday account."""
    return await authenticate_workday_impl(user_id)

if __name__ == "__main__":
    mcp.run()

from mcp.server import MCPServer

from cinii_research_mcp import server as cinii_server
from kaken_mcp import server as kaken_server


def create_server() -> MCPServer:
    mcp = MCPServer("nii-research-mcp")
    mcp.tool(annotations=cinii_server.READ_ONLY)(
        cinii_server._tool_errors(cinii_server.search_articles)
    )
    mcp.tool(annotations=cinii_server.READ_ONLY)(
        cinii_server._tool_errors(cinii_server.search_records)
    )
    mcp.tool(annotations=cinii_server.READ_ONLY)(cinii_server._tool_errors(cinii_server.get_record))
    mcp.tool(annotations=kaken_server.READ_ONLY)(
        kaken_server._tool_errors(kaken_server.search_projects)
    )
    mcp.tool(annotations=kaken_server.READ_ONLY)(
        kaken_server._tool_errors(kaken_server.search_researchers)
    )
    mcp.tool(annotations=kaken_server.READ_ONLY)(
        kaken_server._tool_errors(kaken_server.get_project)
    )
    return mcp

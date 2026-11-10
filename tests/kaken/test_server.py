import sys

import pytest
from mcp import Client, StdioServerParameters
from mcp.types import TextContent


@pytest.mark.asyncio
async def test_stdio_tool_contract() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "kaken_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {
        "get_project",
        "search_projects",
        "search_researchers",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
async def test_missing_application_id_is_actionable() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "kaken_mcp"], env={"KAKEN_APP_ID": ""}
    )
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.call_tool("search_projects", {"query": "検索"})
    assert result.is_error and isinstance(result.content[0], TextContent)
    assert "KAKEN_APP_ID" in result.content[0].text

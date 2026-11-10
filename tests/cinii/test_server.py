import sys

import pytest
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from cinii_research_mcp import create_server


@pytest.mark.asyncio
async def test_stdio_tool_contract() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "cinii_research_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {
        "get_record",
        "search_articles",
        "search_records",
    }
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)
    assert len(await create_server().list_tools()) == 3


@pytest.mark.asyncio
async def test_missing_application_id_is_actionable() -> None:
    params = StdioServerParameters(
        command=sys.executable, args=["-m", "cinii_research_mcp"], env={"CINII_APP_ID": ""}
    )
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.call_tool("search_articles", {"query": "試験"})
    assert result.is_error and isinstance(result.content[0], TextContent)
    assert "CINII_APP_ID" in result.content[0].text

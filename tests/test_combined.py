import subprocess
import sys

import pytest
from mcp import Client, StdioServerParameters

from cinii_research_mcp import cli as cinii_cli
from cinii_research_mcp.server import create_server as cinii_server
from kaken_mcp import cli as kaken_cli
from kaken_mcp.server import create_server as kaken_server
from nii_research_mcp import create_server
from nii_research_mcp.cli import run_cli


@pytest.mark.asyncio
async def test_combined_tools_preserve_source_schemas() -> None:
    expected = []
    for factory in (
        cinii_server,
        kaken_server,
    ):
        expected.extend(await factory().list_tools())
    actual = await create_server().list_tools()
    assert len(actual) == 6
    assert len({tool.name for tool in actual}) == len(actual)
    assert {tool.name: tool.model_dump(exclude_none=True) for tool in actual} == {
        tool.name: tool.model_dump(exclude_none=True) for tool in expected
    }


@pytest.mark.asyncio
async def test_combined_stdio_lists_all_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "nii_research_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert len(result.tools) == 6
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.parametrize("group, module", [("cinii", cinii_cli), ("kaken", kaken_cli)])
def test_cli_dispatches_without_changing_arguments(monkeypatch, group, module) -> None:
    calls = []
    monkeypatch.setattr(module, "run_cli", lambda args: calls.append(list(args)))
    from nii_research_mcp import cli

    monkeypatch.setattr(cli, group.replace("-", "_") + "_cli", module.run_cli)
    run_cli([group, "query", "--limit", "2"])
    assert calls == [["query", "--limit", "2"]]


def test_command_help() -> None:
    for group in ["cinii", "kaken"]:
        result = subprocess.run(
            [sys.executable, "-m", "nii_research_mcp", group, "--help"],
            capture_output=True,
            check=True,
        )
        assert b"usage:" in result.stdout

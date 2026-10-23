from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server import AgentTask, tools_for_task
from tests.conftest import example_server


@pytest.mark.asyncio
async def test_list_tools_includes_mcp_server_meta() -> None:
    """MCP tools/list exposes ``_meta.mcp_server.task`` for every decorated tool."""
    mcp = example_server()
    async with Client(mcp) as client:
        tools = await client.list_tools()

    by_name = {tool.name: tool for tool in tools}
    assert by_name['policies'].meta['mcp_server']['task'] == 'context'
    assert by_name['echo'].meta['mcp_server']['task'] == 'completion'
    assert by_name['grounded'].meta['mcp_server']['task'] == 'evaluation'
    assert by_name['audit'].meta['mcp_server']['task'] == 'post_tool'
    assert by_name['style'].meta['mcp_server']['task'] == 'skill'
    assert by_name['ping'].meta['mcp_server']['task'] == 'none'
    assert 'context' in by_name['policies'].meta['fastmcp']['tags']


@pytest.mark.asyncio
async def test_tools_by_task_and_client_filter() -> None:
    """In-process and client-side filters return only the requested task."""
    mcp = example_server()
    context_tools = await mcp.tools_by_task(AgentTask.CONTEXT)
    assert {tool.name for tool in context_tools} == {'policies', 'ticket'}

    async with Client(mcp) as client:
        listed = await client.list_tools()

    eval_tools = tools_for_task(listed, 'evaluation')
    assert [tool.name for tool in eval_tools] == ['grounded']
    completion_tools = tools_for_task(listed, AgentTask.COMPLETION)
    assert [tool.name for tool in completion_tools] == ['echo']


@pytest.mark.asyncio
async def test_untagged_tools_are_completion() -> None:
    """A tool without mcp_server meta is treated as completion."""

    class Plain:
        name = 'legacy'
        meta = None
        tags: frozenset[str] = frozenset()

    tool = Plain()
    assert tools_for_task([tool], AgentTask.COMPLETION)[0] is tool

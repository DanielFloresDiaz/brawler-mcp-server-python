from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server import META_NAMESPACE, AgentTask, BrawlerMCP, tools_for_task
from brawler_mcp_server.testkit import example_server
from brawler_mcp_server.utils import tool_task


@pytest.mark.asyncio
async def test_task_decorators_stamp_meta_and_tags() -> None:
    """Each task decorator stamps ``mcp_server.task`` and a matching FastMCP tag."""
    mcp = BrawlerMCP('StampServer')

    @mcp.context_tool
    def policies() -> str:
        return 'policy'

    @mcp.tool
    def echo(text: str) -> str:
        return text

    @mcp.eval_tool
    def grounded(answer: str) -> tuple[bool, float, str | None]:
        return True, 1.0, None

    @mcp.post_tool
    def audit(answer: str) -> None:
        return None

    @mcp.none_tool
    def ping() -> str:
        return 'pong'

    tools = {tool.name: tool for tool in await mcp.list_tools()}
    expected = {
        'policies': AgentTask.CONTEXT,
        'echo': AgentTask.COMPLETION,
        'grounded': AgentTask.EVALUATION,
        'audit': AgentTask.POST_TOOL,
        'ping': AgentTask.NONE,
    }
    for name, task in expected.items():
        tool = tools[name]
        assert tool_task(tool) is task
        meta = tool.get_meta() if hasattr(tool, 'get_meta') else tool.meta
        payload = meta[META_NAMESPACE]
        assert payload['task'] == task.value
        assert task.value in set(tool.tags)

    assert tools['policies'].get_meta()[META_NAMESPACE]['as_user_message'] is False


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
async def test_bare_and_called_decorators_register() -> None:
    """Decorators work bare, with parentheses, and with an explicit name."""
    mcp = BrawlerMCP('Patterns')

    @mcp.context_tool
    def bare() -> str:
        return 'bare'

    @mcp.context_tool()
    def called() -> str:
        return 'called'

    @mcp.context_tool('named_context')
    def renamed() -> str:
        return 'named'

    @mcp.tool(name='renamed_echo')
    def echo() -> str:
        return 'echo'

    names = {tool.name for tool in await mcp.list_tools()}
    assert names >= {'bare', 'called', 'named_context', 'renamed_echo'}

from __future__ import annotations

import pytest

from brawler_mcp_server import META_NAMESPACE, AgentTask, BrawlerMCP
from brawler_mcp_server.tasks import tool_task


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

    @mcp.skill_tool(mode='auto')
    def lookup() -> str:
        return '# Lookup\nLook it up.'

    @mcp.none_tool
    def ping() -> str:
        return 'pong'

    tools = {tool.name: tool for tool in await mcp.list_tools()}
    expected = {
        'policies': AgentTask.CONTEXT,
        'echo': AgentTask.COMPLETION,
        'grounded': AgentTask.EVALUATION,
        'audit': AgentTask.POST_TOOL,
        'lookup': AgentTask.SKILL,
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
    assert tools['lookup'].get_meta()[META_NAMESPACE]['mode'] == 'auto'


@pytest.mark.asyncio
async def test_context_tool_as_user_message_is_stamped() -> None:
    """``as_user_message=True`` is stored on the context tool meta payload."""
    mcp = BrawlerMCP('UserMessageServer')

    @mcp.context_tool(as_user_message=True)
    def ticket() -> str:
        return 'open'

    tool = next(t for t in await mcp.list_tools() if t.name == 'ticket')
    assert tool.get_meta()[META_NAMESPACE]['as_user_message'] is True


def test_context_tool_rejects_non_str_return() -> None:
    """Context tools must be annotated to return str."""
    mcp = BrawlerMCP('BadContext')

    with pytest.raises(TypeError, match='Context tool'):

        @mcp.context_tool
        def bad() -> int:
            return 1


def test_eval_tool_rejects_wrong_return() -> None:
    """Eval tools must return tuple[bool, float, str | None]."""
    mcp = BrawlerMCP('BadEval')

    with pytest.raises(TypeError, match='Eval tool'):

        @mcp.eval_tool
        def bad(answer: str) -> str:
            return answer


def test_post_tool_rejects_non_none_return() -> None:
    """Post tools must be annotated to return None."""
    mcp = BrawlerMCP('BadPost')

    with pytest.raises(TypeError, match='Post tool'):

        @mcp.post_tool
        def bad() -> str:
            return 'no'


def test_skill_tool_rejects_unknown_mode() -> None:
    """Skill mode must be always-on or auto."""
    mcp = BrawlerMCP('BadSkill')

    with pytest.raises(ValueError, match='Invalid skill mode'):

        @mcp.skill_tool(mode='sometimes')
        def bad() -> str:
            return 'x'


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

    names = {tool.name for tool in await mcp.list_tools()}
    assert names >= {'bare', 'called', 'named_context'}

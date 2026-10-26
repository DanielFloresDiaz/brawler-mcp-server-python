from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server import META_NAMESPACE, BrawlerMCP
from brawler_mcp_server.tasks.context import ContextTask
from brawler_mcp_server.testkit import call_text, example_server


def test_context_task_rejects_non_str_return() -> None:
    """Context tools must be annotated to return str."""
    mcp = BrawlerMCP('BadContext')

    with pytest.raises(TypeError, match='Context tool'):

        @mcp.context_tool
        def bad() -> int:
            return 1


def test_context_task_rejects_optional_str() -> None:
    """Context tools cannot return ``str | None``."""
    mcp = BrawlerMCP('OptionalContext')

    with pytest.raises(TypeError, match='Context tool'):

        @mcp.context_tool
        def bad() -> str | None:
            return 'x'


def test_context_task_rejects_unannotated_return() -> None:
    """Context tools must declare a return type."""
    mcp = BrawlerMCP('BareContext')

    with pytest.raises(TypeError, match='Context tool'):

        @mcp.context_tool
        def bad():  # type: ignore[no-untyped-def]
            return 'x'


def test_context_task_wrap_rejects_non_str() -> None:
    """ContextTask wraps functions so a non-string result fails at call time."""

    def policies() -> str:
        return 1  # type: ignore[return-value]

    wrapped = ContextTask().wrap(policies)
    with pytest.raises(TypeError, match="Context tool 'policies' must return str"):
        wrapped()


@pytest.mark.asyncio
async def test_context_task_wrap_supports_async_functions() -> None:
    """Async context tools still validate the return type at call time."""

    async def policies() -> str:
        return 'ok'

    assert await ContextTask().wrap(policies)() == 'ok'

    async def bad() -> str:
        return 1  # type: ignore[return-value]

    with pytest.raises(TypeError, match="Context tool 'bad' must return str"):
        await ContextTask().wrap(bad)()


@pytest.mark.asyncio
async def test_context_tool_as_user_message_is_stamped() -> None:
    """``as_user_message=True`` is stored on the context tool meta payload."""
    mcp = BrawlerMCP('UserMessageServer')

    @mcp.context_tool(as_user_message=True)
    def ticket() -> str:
        return 'open'

    tool = next(t for t in await mcp.list_tools() if t.name == 'ticket')
    assert tool.get_meta()[META_NAMESPACE]['as_user_message'] is True


@pytest.mark.asyncio
async def test_call_context_tool_returns_string() -> None:
    """Context tools return their string payload as MCP text."""
    mcp = example_server()
    async with Client(mcp) as client:
        result = await client.call_tool('policies', {})
    assert 'Always cite sources.' in call_text(result)


@pytest.mark.asyncio
async def test_context_call_rejects_non_str_result() -> None:
    """A context tool that returns a non-string fails when called."""
    mcp = BrawlerMCP('RuntimeContext')

    def policies() -> str:
        return 1  # type: ignore[return-value]

    mcp.context_tool(policies)
    async with Client(mcp) as client:
        with pytest.raises(Exception, match='must return str'):
            await client.call_tool('policies', {})

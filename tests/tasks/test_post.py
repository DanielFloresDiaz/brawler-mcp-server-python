from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server import BrawlerMCP
from brawler_mcp_server.tasks.post import PostTask
from brawler_mcp_server.testkit import example_server


def test_post_task_rejects_non_none_return() -> None:
    """Post tools must be annotated to return None."""
    mcp = BrawlerMCP('BadPost')

    with pytest.raises(TypeError, match='Post tool'):

        @mcp.post_tool
        def bad() -> str:
            return 'no'


def test_post_task_rejects_unannotated_return() -> None:
    """Post tools must declare a return type."""
    mcp = BrawlerMCP('BarePost')

    with pytest.raises(TypeError, match='Post tool'):

        @mcp.post_tool
        def bad():  # type: ignore[no-untyped-def]
            return None


def test_post_task_wrap_rejects_value() -> None:
    """PostTask wraps functions so a non-None result fails at call time."""

    def audit() -> None:
        return 'logged'  # type: ignore[return-value]

    wrapped = PostTask().wrap(audit)
    with pytest.raises(TypeError, match="Post tool 'audit' must return None"):
        wrapped()


@pytest.mark.asyncio
async def test_call_post_tool() -> None:
    """Post tools are callable over MCP."""
    mcp = example_server()
    async with Client(mcp) as client:
        await client.call_tool('audit', {'answer': 'ok'})

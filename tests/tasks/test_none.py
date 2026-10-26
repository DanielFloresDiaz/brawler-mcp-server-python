from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server.testkit import call_text, example_server


@pytest.mark.asyncio
async def test_call_none_tool() -> None:
    """None tools are callable by generic MCP clients."""
    mcp = example_server()
    async with Client(mcp) as client:
        ping = await client.call_tool('ping', {})
    assert 'pong' in call_text(ping)

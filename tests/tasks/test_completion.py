from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server.testkit import call_text, example_server


@pytest.mark.asyncio
async def test_call_completion_tool() -> None:
    """Completion tools still behave like ordinary FastMCP tools."""
    mcp = example_server()
    async with Client(mcp) as client:
        result = await client.call_tool('echo', {'text': 'hello'})
    assert 'hello' in call_text(result)

from __future__ import annotations

import json

import pytest
from fastmcp import Client

from tests.conftest import call_text, example_server


@pytest.mark.asyncio
async def test_call_context_tool_returns_string() -> None:
    """Context tools return their string payload as MCP text."""
    mcp = example_server()
    async with Client(mcp) as client:
        result = await client.call_tool('policies', {})
    assert 'Always cite sources.' in call_text(result)


@pytest.mark.asyncio
async def test_call_completion_tool() -> None:
    """Completion tools still behave like ordinary FastMCP tools."""
    mcp = example_server()
    async with Client(mcp) as client:
        result = await client.call_tool('echo', {'text': 'hello'})
    assert 'hello' in call_text(result)


@pytest.mark.asyncio
async def test_call_eval_tool_returns_json_payload() -> None:
    """Eval tools serialize the tuple as is_valid/score/feedback."""
    mcp = example_server()
    async with Client(mcp) as client:
        ok = await client.call_tool('grounded', {'answer': 'cited'})
        empty = await client.call_tool('grounded', {'answer': '  '})

    ok_payload = _json_payload(ok)
    empty_payload = _json_payload(empty)
    assert ok_payload['is_valid'] is True
    assert ok_payload['score'] == 1.0
    assert ok_payload['feedback'] is None
    assert empty_payload['is_valid'] is False
    assert empty_payload['feedback'] == 'Answer is empty.'


@pytest.mark.asyncio
async def test_call_post_and_none_and_skill_tools() -> None:
    """Post, none, and skill tools are callable over MCP."""
    mcp = example_server()
    async with Client(mcp) as client:
        await client.call_tool('audit', {'answer': 'ok'})
        ping = await client.call_tool('ping', {})
        style = await client.call_tool('style', {})
    assert 'pong' in call_text(ping)
    assert 'short sentences' in call_text(style).lower()


def _json_payload(result: object) -> dict:
    structured = getattr(result, 'structured_content', None) or getattr(result, 'structuredContent', None)
    if isinstance(structured, dict) and 'is_valid' in structured:
        return structured
    data = getattr(result, 'data', None)
    if isinstance(data, dict) and 'is_valid' in data:
        return data
    text = call_text(result)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        return parsed
    raise AssertionError(f'Could not parse eval payload from {result!r}')

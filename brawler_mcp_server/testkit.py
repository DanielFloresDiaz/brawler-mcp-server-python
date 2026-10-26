"""Test helpers for this package (import via ``brawler_mcp_server.testkit``, not ``tests.*``)."""

from __future__ import annotations

import json

from brawler_mcp_server import BrawlerMCP


def example_server() -> BrawlerMCP:
    """Build a mixed-task server used by listing and call tests."""
    mcp = BrawlerMCP('TestServer')

    @mcp.context_tool
    def policies() -> str:
        return 'Always cite sources.'

    @mcp.context_tool(as_user_message=True)
    def ticket() -> str:
        return 'Ticket #123 is still open.'

    @mcp.tool
    def echo(text: str) -> str:
        return text

    @mcp.eval_tool
    def grounded(answer: str) -> tuple[bool, float, str | None]:
        if not str(answer).strip():
            return False, 0.0, 'Answer is empty.'
        return True, 1.0, None

    @mcp.post_tool
    def audit(answer: str) -> None:
        return None

    @mcp.none_tool
    def ping() -> str:
        return 'pong'

    return mcp


def call_text(result: object) -> str:
    """Extract concatenated text from a FastMCP call result."""
    content = getattr(result, 'content', None)
    if content:
        texts = [getattr(item, 'text', '') for item in content if getattr(item, 'text', None)]
        if texts:
            return '\n'.join(texts)
    data = getattr(result, 'data', None)
    if data is not None:
        return str(data)
    structured = getattr(result, 'structured_content', None) or getattr(result, 'structuredContent', None)
    if structured is not None:
        return str(structured)
    return str(result)


def json_payload(result: object) -> dict:
    """Parse an eval tool call into ``is_valid`` / ``score`` / ``feedback``."""
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

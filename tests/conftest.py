from __future__ import annotations

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

    @mcp.skill_tool(mode='always-on')
    def style() -> str:
        return '# Style\nUse short sentences.'

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

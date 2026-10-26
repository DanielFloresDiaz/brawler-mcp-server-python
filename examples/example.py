"""Example stdio server used by package tests and Brawler integration tests."""

from __future__ import annotations

from brawler_mcp_server.server import BrawlerMCP

mcp = BrawlerMCP('BrawlerExample')


@mcp.context_tool
def policies() -> str:
    """Company policy injected into the agent system prompt."""
    return 'Always cite sources.'


@mcp.context_tool(as_user_message=True)
def open_ticket() -> str:
    """Ticket reminder injected as a user message."""
    return 'Ticket #123 is still open.'


@mcp.tool
def echo(text: str) -> str:
    """Echo the given text back to the model."""
    return text


@mcp.eval_tool
def grounded(answer: str) -> tuple[bool, float, str | None]:
    """Reject empty answers."""
    if not str(answer).strip():
        return False, 0.0, 'Answer is empty.'
    return True, 1.0, None


@mcp.post_tool
def audit(answer: str) -> None:
    """No-op post tool used to verify post-task listing and calls."""
    return


@mcp.none_tool
def ping() -> str:
    """Generic MCP ping; Brawler agents skip none tools."""
    return 'pong'


def main() -> None:
    """Run the example server over stdio."""
    mcp.run()


if __name__ == '__main__':
    main()

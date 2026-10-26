"""Stdio MCP server used by Brawler's real-env MCPTool tests.

Registers at least one tool per agent task, plus untagged / unsupported tools so
the client can exercise task detection from ``_meta`` and FastMCP tags.
"""

from __future__ import annotations

import json
from typing import TypedDict

from fastmcp import FastMCP

from brawler_mcp_server.server import BrawlerMCP


class AddResult(TypedDict):
    """Structured sum returned by the ``add`` completion tool."""

    sum: int


mcp = BrawlerMCP('BrawlerTaskServer')


@mcp.context_tool
def policies() -> str:
    """Company policy injected into the agent system prompt."""
    return 'Always cite sources.'


@mcp.context_tool(as_user_message=True)
def open_ticket() -> str:
    """Ticket reminder injected as a user message."""
    return 'Ticket #123 is still open.'


@mcp.context_tool
def locale(language: str) -> str:
    """Locale hint that takes a language code."""
    return f'Reply in {language}.'


@mcp.context_tool
def boom() -> str:
    """Context tool that fails so the client can observe a swallowed error."""
    raise RuntimeError('context failed')


@mcp.tool
def echo(text: str) -> str:
    """Echo the given text back to the model."""
    return text


@mcp.tool
def add(a: int, b: int) -> AddResult:
    """Add two integers and return structured output."""
    return {'sum': a + b}


@mcp.tool
def fail(text: str) -> str:
    """Completion tool that raises so run_tool_call can observe a remote error."""
    raise RuntimeError(f'remote failed: {text}')


@mcp.eval_tool
def grounded(answer: str) -> tuple[bool, float, str | None]:
    """Reject empty answers."""
    if not str(answer).strip():
        return False, 0.0, 'Answer is empty.'
    return True, 1.0, None


@mcp.eval_tool
def score_length(answer: str) -> tuple[bool, float, str | None]:
    """Score a non-empty answer by character length."""
    stripped = str(answer).strip()
    if len(stripped) < 3:
        return False, 0.25, 'Answer is too short.'
    return True, 0.9, 'ok'


@mcp.post_tool
def audit(answer: str) -> None:
    """No-op post tool used to verify post-task listing and calls."""
    return


@mcp.post_tool
def record(value: int, query: str) -> None:
    """Post tool with multiple input fields."""
    return


@mcp.none_tool
def ping() -> str:
    """Generic MCP ping; Brawler agents skip none tools."""
    return 'pong'


def legacy_search(q: str) -> str:
    """Untagged FastMCP tool; Brawler treats it as completion."""
    return f'results for {q}'


def style() -> str:
    """Skill-tagged tool; Brawler treats unsupported tasks as none."""
    return 'Prefer short sentences.'


def route(query: str) -> str:
    """Router-tagged tool; Brawler treats unsupported tasks as none."""
    return 'routed'


def train() -> str:
    """Training-tagged tool; Brawler treats unsupported tasks as none."""
    return 'train'


def unknown_task(q: str) -> str:
    """``mcp_server.task`` that is not a Task value defaults to completion."""
    return f'unknown:{q}'


def tagged_eval(answer: str) -> str:
    """Evaluation via FastMCP tags only (no ``mcp_server.task``)."""
    return json.dumps({'is_valid': True, 'score': 1.0, 'feedback': None})


def broken_eval(answer: str) -> str:
    """Evaluation tool that returns non-object text."""
    return 'not-json'


def valid_no_score(answer: str) -> str:
    """Evaluation tool that omits ``score`` so the client can default it."""
    return json.dumps({'is_valid': True, 'feedback': 'fine'})


def _plain_tool(
    fn: object,
    *,
    name: str,
    tags: set[str] | None = None,
    meta: dict[str, object] | None = None,
) -> None:
    """Register a FastMCP tool without BrawlerMCP's task stamp."""
    FastMCP.tool(mcp, name=name, tags=tags, meta=meta)(fn)


_plain_tool(legacy_search, name='legacy_search')
_plain_tool(style, name='style', tags={'skill'})
_plain_tool(route, name='route', tags={'router'})
_plain_tool(train, name='train', tags={'training'})
_plain_tool(unknown_task, name='unknown_task', meta={'mcp_server': {'task': 'not-a-task'}})
_plain_tool(tagged_eval, name='tagged_eval', tags={'evaluation'})
_plain_tool(broken_eval, name='broken_eval', meta={'mcp_server': {'task': 'evaluation'}})
_plain_tool(valid_no_score, name='valid_no_score', meta={'mcp_server': {'task': 'evaluation'}})


def main() -> None:
    """Run the task server over stdio."""
    mcp.run()


if __name__ == '__main__':
    main()

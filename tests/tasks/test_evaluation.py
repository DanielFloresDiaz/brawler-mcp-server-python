from __future__ import annotations

import pytest
from fastmcp import Client

from brawler_mcp_server import BrawlerMCP
from brawler_mcp_server.tasks.evaluation import EvaluationTask, eval_tuple_to_payload
from brawler_mcp_server.testkit import example_server, json_payload


def test_eval_task_rejects_wrong_return() -> None:
    """Eval tools must return tuple[bool, float, str | None]."""
    mcp = BrawlerMCP('BadEval')

    with pytest.raises(TypeError, match='Eval tool'):

        @mcp.eval_tool
        def bad(answer: str) -> str:
            return answer


def test_eval_task_rejects_tuple_without_score() -> None:
    """Eval tools must include the score float in the return tuple."""
    mcp = BrawlerMCP('ShortEval')

    with pytest.raises(TypeError, match='Eval tool'):

        @mcp.eval_tool
        def bad(answer: str) -> tuple[bool, str | None]:
            return True, None


def test_eval_task_rejects_unannotated_return() -> None:
    """Eval tools must declare a return type."""
    mcp = BrawlerMCP('BareEval')

    with pytest.raises(TypeError, match='Eval tool'):

        @mcp.eval_tool
        def bad(answer: str):  # type: ignore[no-untyped-def]
            return True, 1.0, None


def test_eval_task_accepts_tuple_with_str_feedback() -> None:
    """``tuple[bool, float, str]`` is a valid eval return annotation."""
    mcp = BrawlerMCP('StrFeedbackEval')

    @mcp.eval_tool
    def grounded(answer: str) -> tuple[bool, float, str]:
        return True, 1.0, 'ok'

    assert grounded is not None


def test_eval_task_rejects_tuple_with_wrong_item_types() -> None:
    """A 3-tuple whose items are not bool, float, and optional str is rejected."""
    mcp = BrawlerMCP('WrongEvalTypes')

    with pytest.raises(TypeError, match='Eval tool'):

        @mcp.eval_tool
        def bad(answer: str) -> tuple[bool, int, str | None]:
            return True, 1, None


def test_eval_tuple_to_payload_validates_fields() -> None:
    """Eval payloads must be bool, numeric score, and optional str feedback."""
    assert eval_tuple_to_payload({'is_valid': True, 'score': 1.0, 'feedback': None}) == {
        'is_valid': True,
        'score': 1.0,
        'feedback': None,
    }
    assert eval_tuple_to_payload((True, 1, None)) == {'is_valid': True, 'score': 1.0, 'feedback': None}
    with pytest.raises(TypeError, match='tuple\\[bool, float, str \\| None\\]'):
        eval_tuple_to_payload('yes')
    with pytest.raises(TypeError, match='is_valid must be bool'):
        eval_tuple_to_payload((1, 1.0, None))
    with pytest.raises(TypeError, match='score must be float'):
        eval_tuple_to_payload((True, '1.0', None))
    with pytest.raises(TypeError, match='feedback must be str \\| None'):
        eval_tuple_to_payload((True, 1.0, 0))


def test_evaluation_task_wrap_rejects_bad_score() -> None:
    """EvaluationTask wraps functions so a bad runtime tuple fails at call time."""

    def grounded(answer: str) -> tuple[bool, float, str | None]:
        return True, '1.0', None  # type: ignore[return-value]

    wrapped = EvaluationTask().wrap(grounded)
    with pytest.raises(TypeError, match='score must be float'):
        wrapped(answer='x')


@pytest.mark.asyncio
async def test_call_eval_tool_returns_json_payload() -> None:
    """Eval tools serialize the tuple as is_valid/score/feedback."""
    mcp = example_server()
    async with Client(mcp) as client:
        ok = await client.call_tool('grounded', {'answer': 'cited'})
        empty = await client.call_tool('grounded', {'answer': '  '})

    ok_payload = json_payload(ok)
    empty_payload = json_payload(empty)
    assert ok_payload['is_valid'] is True
    assert ok_payload['score'] == 1.0
    assert ok_payload['feedback'] is None
    assert empty_payload['is_valid'] is False
    assert empty_payload['feedback'] == 'Answer is empty.'


@pytest.mark.asyncio
async def test_eval_call_rejects_invalid_tuple() -> None:
    """An eval tool that returns the wrong runtime tuple fails when called."""
    mcp = BrawlerMCP('RuntimeEval')

    def grounded(answer: str) -> tuple[bool, float, str | None]:
        return True, '1.0', None  # type: ignore[return-value]

    mcp.eval_tool(grounded)
    async with Client(mcp) as client:
        with pytest.raises(Exception, match='score must be float'):
            await client.call_tool('grounded', {'answer': 'x'})

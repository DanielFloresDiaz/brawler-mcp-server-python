"""Evaluation task: ``tuple[bool, float, str | None]`` serialized as JSON."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, TypedDict, get_args, get_origin

from brawler_mcp_server.utils import AgentTask, TaskHandler, return_annotation, wrap_checked

EVAL_RETURN = 'tuple[bool, float, str | None]'


class EvalResult(TypedDict):
    """JSON payload returned by evaluation tools."""

    is_valid: bool
    score: float
    feedback: str | None


class EvaluationTask(TaskHandler):
    """Validate and wrap eval tools that return ``tuple[bool, float, str | None]``."""

    task = AgentTask.EVALUATION
    label = 'Eval tool'

    def check(self, fn: Callable[..., Any]) -> None:
        annotation = return_annotation(fn)
        if annotation is inspect.Signature.empty:
            raise TypeError(f'{self.label} {fn.__name__!r} must return {EVAL_RETURN}, got unannotated.')
        if not is_eval_tuple(annotation):
            raise TypeError(f'{self.label} {fn.__name__!r} must return {EVAL_RETURN}, got {annotation}.')

    def wrap(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        wrapped = wrap_checked(fn, eval_tuple_to_payload)
        wrapped.__annotations__ = {**getattr(fn, '__annotations__', {}), 'return': EvalResult}
        return wrapped


def eval_tuple_to_payload(result: Any) -> EvalResult:
    """Validate and convert an eval function result to the wire dict."""
    if isinstance(result, dict) and {'is_valid', 'score', 'feedback'} <= set(result):
        return _eval_payload(result['is_valid'], result['score'], result.get('feedback'))
    if not isinstance(result, tuple) or len(result) != 3:
        raise TypeError(f'Eval tool must return {EVAL_RETURN}, got {type(result).__name__}.')
    return _eval_payload(*result)


def is_eval_tuple(annotation: Any) -> bool:
    """Return True when *annotation* is ``tuple[bool, float, str | None]`` (or str/None feedback)."""
    origin = get_origin(annotation)
    if origin is not tuple:
        return False
    args = get_args(annotation)
    if len(args) != 3:
        return False
    is_valid_t, score_t, feedback_t = args
    if is_valid_t is not bool or score_t is not float:
        return False
    if feedback_t in (str, type(None)):
        return True
    union_args = get_args(feedback_t)
    return set(union_args) == {str, type(None)}


def _eval_payload(is_valid: Any, score: Any, feedback: Any) -> EvalResult:
    if not isinstance(is_valid, bool):
        raise TypeError(f'Eval is_valid must be bool, got {type(is_valid).__name__}.')
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise TypeError(f'Eval score must be float, got {type(score).__name__}.')
    if feedback is not None and not isinstance(feedback, str):
        raise TypeError(f'Eval feedback must be str | None, got {type(feedback).__name__}.')
    return EvalResult(is_valid=is_valid, score=float(score), feedback=feedback)

"""Return-type checks and eval serialization for task decorators."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypedDict, get_args, get_origin, get_type_hints

EvalFunc = Callable[..., tuple[bool, float, str | None] | Awaitable[tuple[bool, float, str | None]]]


class EvalResult(TypedDict):
    """JSON payload returned by evaluation tools."""

    is_valid: bool
    score: float
    feedback: str | None


def require_return_type(fn: Callable[..., Any], expected: type | tuple[type, ...], *, label: str) -> None:
    """Raise TypeError when *fn* is not annotated with *expected*."""
    annotation = _return_annotation(fn)
    if annotation is inspect.Signature.empty:
        raise TypeError(f'{label} {fn.__name__!r} must declare a return type of {expected}.')
    if not _annotation_matches(annotation, expected):
        raise TypeError(f'{label} {fn.__name__!r} must return {expected}, got {annotation}.')


def require_eval_return(fn: Callable[..., Any]) -> None:
    """Raise TypeError unless *fn* returns ``tuple[bool, float, str | None]``."""
    annotation = _return_annotation(fn)
    if annotation is inspect.Signature.empty:
        raise TypeError(f'Eval tool {fn.__name__!r} must return tuple[bool, float, str | None], got unannotated.')
    if not _is_eval_tuple(annotation):
        raise TypeError(f'Eval tool {fn.__name__!r} must return tuple[bool, float, str | None], got {annotation}.')


def wrap_eval_function(fn: EvalFunc) -> Callable[..., EvalResult | Awaitable[EvalResult]]:
    """Convert an eval tuple return value into the JSON wire payload."""
    if inspect.iscoroutinefunction(fn):

        @wraps(fn)
        async def async_wrapped(*args: Any, **kwargs: Any) -> EvalResult:
            result = await fn(*args, **kwargs)
            return eval_tuple_to_payload(result)

        async_wrapped.__annotations__ = {**getattr(fn, '__annotations__', {}), 'return': EvalResult}
        return async_wrapped

    @wraps(fn)
    def synced(*args: Any, **kwargs: Any) -> EvalResult:
        result = fn(*args, **kwargs)
        return eval_tuple_to_payload(result)

    synced.__annotations__ = {**getattr(fn, '__annotations__', {}), 'return': EvalResult}
    return synced


def eval_tuple_to_payload(result: Any) -> EvalResult:
    """Validate and convert an eval function result to the wire dict."""
    if isinstance(result, dict) and {'is_valid', 'score', 'feedback'} <= set(result):
        return EvalResult(
            is_valid=bool(result['is_valid']),
            score=float(result['score']),
            feedback=result.get('feedback'),
        )
    if not isinstance(result, tuple) or len(result) != 3:
        raise TypeError(f'Eval tool must return tuple[bool, float, str | None], got {type(result)!r}.')
    is_valid, score, feedback = result
    if feedback is not None and not isinstance(feedback, str):
        raise TypeError(f'Eval feedback must be str | None, got {type(feedback)!r}.')
    return EvalResult(is_valid=bool(is_valid), score=float(score), feedback=feedback)


def _return_annotation(fn: Callable[..., Any]) -> Any:
    try:
        hints = get_type_hints(fn)
    except (TypeError, NameError, ValueError):
        hints = {}
    if 'return' in hints:
        return hints['return']
    return inspect.signature(fn).return_annotation


def _annotation_matches(annotation: Any, expected: type | tuple[type, ...]) -> bool:
    expected_types = expected if isinstance(expected, tuple) else (expected,)
    if annotation in expected_types:
        return True
    origin = get_origin(annotation)
    if origin in expected_types:
        return True
    return expected_types == (type(None),) and annotation in (None, type(None))


def _is_eval_tuple(annotation: Any) -> bool:
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

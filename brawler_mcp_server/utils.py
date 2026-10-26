"""Shared helpers for task metadata, annotations, and return wrapping."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable, Sequence
from enum import Enum
from functools import wraps
from typing import Any, ClassVar, get_type_hints

META_NAMESPACE = 'mcp_server'
_Check = Callable[[Any], Any]


class AgentTask(str, Enum):
    """Tasks a Brawler agent can consume from an MCP server."""

    CONTEXT = 'context'
    COMPLETION = 'completion'
    EVALUATION = 'evaluation'
    POST_TOOL = 'post_tool'
    NONE = 'none'


AGENT_TASK_VALUES = frozenset(task.value for task in AgentTask)


class TaskHandler:
    """Validates and wraps a tool function for one agent task."""

    task: ClassVar[AgentTask]
    label: ClassVar[str]

    def extra_meta(self) -> dict[str, Any]:
        """Return task-specific ``_meta.mcp_server`` fields."""
        return {}

    def check(self, fn: Callable[..., Any]) -> None:
        """Validate *fn*'s return annotation. Override in subclasses."""

    def wrap(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap *fn* to validate its runtime return value. Override in subclasses."""
        return fn


def require_return_type(fn: Callable[..., Any], expected: type | tuple[type, ...], *, label: str) -> None:
    """Raise TypeError when *fn* is not annotated with *expected*."""
    annotation = return_annotation(fn)
    if annotation is inspect.Signature.empty:
        raise TypeError(f'{label} {fn.__name__!r} must declare a return type of {expected}.')
    if not annotation_matches(annotation, expected):
        raise TypeError(f'{label} {fn.__name__!r} must return {expected}, got {annotation}.')


def wrap_checked(fn: Callable[..., Any], check: _Check) -> Callable[..., Any]:
    """Wrap *fn* so *check* runs on its return value (sync or async)."""
    if inspect.iscoroutinefunction(fn):

        @wraps(fn)
        async def async_wrapped(*args: Any, **kwargs: Any) -> Any:
            return check(await fn(*args, **kwargs))

        return async_wrapped

    @wraps(fn)
    def synced(*args: Any, **kwargs: Any) -> Any:
        return check(fn(*args, **kwargs))

    return synced


def return_annotation(fn: Callable[..., Any]) -> Any:
    """Resolve *fn*'s return annotation, preferring ``get_type_hints``."""
    try:
        hints = get_type_hints(fn)
    except (TypeError, NameError, ValueError):
        hints = {}
    if 'return' in hints:
        return hints['return']
    return inspect.signature(fn).return_annotation


def annotation_matches(annotation: Any, expected: type | tuple[type, ...]) -> bool:
    """Return True when *annotation* is one of *expected* (including ``None``)."""
    expected_types = expected if isinstance(expected, tuple) else (expected,)
    if annotation in expected_types:
        return True
    return expected_types == (type(None),) and annotation in (None, type(None))


def stamp_task_kwargs(
    kwargs: dict[str, Any],
    task: AgentTask | str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy decorator kwargs and stamp task tags plus ``_meta.mcp_server``."""
    value = task.value if isinstance(task, AgentTask) else task
    stamped = dict(kwargs)
    tags = set(stamped.get('tags') or set())
    tags.add(value)
    stamped['tags'] = tags
    meta = dict(stamped.get('meta') or {})
    payload = dict(meta.get(META_NAMESPACE) or {})
    payload['task'] = value
    if extra:
        payload.update(extra)
    meta[META_NAMESPACE] = payload
    stamped['meta'] = meta
    return stamped


def task_from_meta(
    meta: dict[str, Any] | None,
    tags: Iterable[str] | None = None,
) -> AgentTask:
    """Read the agent task from MCP tool meta, then FastMCP tags, else completion."""
    if meta:
        payload = meta.get(META_NAMESPACE)
        if isinstance(payload, dict):
            raw_task = payload.get('task')
            if isinstance(raw_task, str):
                if raw_task in AGENT_TASK_VALUES:
                    return AgentTask(raw_task)
                return AgentTask.NONE
        fastmcp_meta = meta.get('fastmcp')
        if isinstance(fastmcp_meta, dict):
            tag_list = fastmcp_meta.get('tags')
            if isinstance(tag_list, list):
                tagged = _task_from_tags(tag_list)
                if tagged is not None:
                    return tagged
    if tags is not None:
        tagged = _task_from_tags(tags)
        if tagged is not None:
            return tagged
    return AgentTask.COMPLETION


def tools_for_task(tools: Sequence[Any], task: AgentTask | str) -> list[Any]:
    """Filter MCP or FastMCP tool objects whose stamped agent task matches *task*."""
    wanted = AgentTask(task)
    return [tool for tool in tools if tool_task(tool) is wanted]


def tool_task(tool: Any) -> AgentTask:
    """Read the agent task from a FastMCP component or MCP SDK Tool."""
    meta = getattr(tool, 'meta', None)
    get_meta = getattr(tool, 'get_meta', None)
    if callable(get_meta):
        resolved = get_meta()
        if isinstance(resolved, dict):
            meta = resolved
    tags = getattr(tool, 'tags', None)
    return task_from_meta(meta if isinstance(meta, dict) else None, tags)


def _task_from_tags(tags: Iterable[str]) -> AgentTask | None:
    for tag in tags:
        if tag in AGENT_TASK_VALUES:
            return AgentTask(tag)
    return None

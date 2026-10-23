"""Agent task values and the language-agnostic MCP wire contract."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import Enum
from typing import Any

META_NAMESPACE = 'mcp_server'

SkillMode = str  # 'always-on' | 'auto'


class AgentTask(str, Enum):
    """Tasks a Brawler agent can consume from an MCP server."""

    CONTEXT = 'context'
    COMPLETION = 'completion'
    EVALUATION = 'evaluation'
    POST_TOOL = 'post_tool'
    SKILL = 'skill'
    NONE = 'none'


AGENT_TASK_VALUES = frozenset(task.value for task in AgentTask)
SKILL_MODES = frozenset({'always-on', 'auto'})


def task_from_meta(
    meta: dict[str, Any] | None,
    tags: Iterable[str] | None = None,
) -> AgentTask:
    """Read the agent task from MCP tool meta, then FastMCP tags, else completion."""
    if meta:
        payload = meta.get(META_NAMESPACE)
        if isinstance(payload, dict):
            raw_task = payload.get('task')
            if isinstance(raw_task, str) and raw_task in AGENT_TASK_VALUES:
                return AgentTask(raw_task)
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


def mcp_server_payload(meta: dict[str, Any] | None) -> dict[str, Any]:
    """Return the ``mcp_server`` object from tool meta, or an empty dict."""
    if not meta:
        return {}
    payload = meta.get(META_NAMESPACE)
    return payload if isinstance(payload, dict) else {}


def stamp_task_kwargs(
    kwargs: dict[str, Any],
    task: AgentTask,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Copy decorator kwargs and stamp task tags plus ``_meta.mcp_server``."""
    stamped = dict(kwargs)
    tags = set(stamped.get('tags') or set())
    tags.add(task.value)
    stamped['tags'] = tags
    meta = dict(stamped.get('meta') or {})
    payload = dict(meta.get(META_NAMESPACE) or {})
    payload['task'] = task.value
    if extra:
        payload.update(extra)
    meta[META_NAMESPACE] = payload
    stamped['meta'] = meta
    return stamped


def tools_for_task(tools: Sequence[Any], task: AgentTask | str) -> list[Any]:
    """Filter MCP or FastMCP tool objects whose stamped task matches *task*."""
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

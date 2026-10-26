from __future__ import annotations

import pytest

from brawler_mcp_server.utils import (
    AgentTask,
    require_return_type,
    return_annotation,
    stamp_task_kwargs,
    task_from_meta,
    tools_for_task,
)


def test_require_return_type_rejects_unannotated() -> None:
    """Unannotated functions are rejected."""

    def bare():  # type: ignore[no-untyped-def]
        return 'x'

    with pytest.raises(TypeError, match='must declare a return type'):
        require_return_type(bare, str, label='Context tool')


def test_return_annotation_falls_back_when_hints_fail() -> None:
    """Unresolved return annotations fall back to the raw signature."""

    def mystery() -> str:
        return 'x'

    mystery.__annotations__['return'] = 'DoesNotExist'
    assert return_annotation(mystery) == 'DoesNotExist'


def test_stamp_task_kwargs_sets_task_and_tag() -> None:
    """Stamping adds the task tag and ``mcp_server`` payload."""
    stamped = stamp_task_kwargs({'tags': {'extra'}}, AgentTask.CONTEXT, extra={'as_user_message': True})
    assert 'context' in stamped['tags']
    assert 'extra' in stamped['tags']
    assert stamped['meta']['mcp_server'] == {'task': 'context', 'as_user_message': True}


def test_task_from_meta_reads_payload_then_tags() -> None:
    """``mcp_server.task`` wins; FastMCP tags are the fallback; else completion."""
    assert task_from_meta({'mcp_server': {'task': 'skill'}}) is AgentTask.NONE
    assert task_from_meta({'fastmcp': {'tags': ['skill']}}) is AgentTask.COMPLETION
    assert task_from_meta({'fastmcp': {'tags': ['evaluation']}}) is AgentTask.EVALUATION
    assert task_from_meta(None, tags=['evaluation']) is AgentTask.EVALUATION
    assert task_from_meta({}, tags=['skill']) is AgentTask.COMPLETION
    assert task_from_meta(None) is AgentTask.COMPLETION


def test_untagged_tools_are_completion() -> None:
    """A tool without mcp_server meta is treated as completion."""

    class Plain:
        name = 'legacy'
        meta = None
        tags: frozenset[str] = frozenset()

    tool = Plain()
    assert tools_for_task([tool], AgentTask.COMPLETION)[0] is tool

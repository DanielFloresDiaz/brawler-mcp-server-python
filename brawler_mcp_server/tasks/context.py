"""Context task: prompt or user-message injection, return ``str``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from brawler_mcp_server.utils import AgentTask, TaskHandler, require_return_type, wrap_checked


class ContextTask(TaskHandler):
    """Validate and wrap context tools that must return ``str``."""

    task = AgentTask.CONTEXT
    label = 'Context tool'

    def __init__(self, *, as_user_message: bool = False) -> None:
        self.as_user_message = as_user_message

    def extra_meta(self) -> dict[str, Any]:
        return {'as_user_message': self.as_user_message}

    def check(self, fn: Callable[..., Any]) -> None:
        require_return_type(fn, str, label=self.label)

    def wrap(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        name = getattr(fn, '__name__', '<tool>')

        def check(result: Any) -> str:
            if not isinstance(result, str):
                raise TypeError(f'{self.label} {name!r} must return str, got {type(result).__name__}.')
            return result

        return wrap_checked(fn, check)

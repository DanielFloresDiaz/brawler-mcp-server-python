"""Post task: side effects after a result, return ``None``."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from brawler_mcp_server.utils import AgentTask, TaskHandler, require_return_type, wrap_checked


class PostTask(TaskHandler):
    """Validate and wrap post tools that must return ``None``."""

    task = AgentTask.POST_TOOL
    label = 'Post tool'

    def check(self, fn: Callable[..., Any]) -> None:
        require_return_type(fn, type(None), label=self.label)

    def wrap(self, fn: Callable[..., Any]) -> Callable[..., Any]:
        name = getattr(fn, '__name__', '<tool>')

        def check(result: Any) -> None:
            if result is not None:
                raise TypeError(f'{self.label} {name!r} must return None, got {type(result).__name__}.')
            return result

        return wrap_checked(fn, check)

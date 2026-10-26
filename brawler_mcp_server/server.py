"""FastMCP subclass with Brawler agent-task decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, overload

from fastmcp import FastMCP
from fastmcp.tools.function_tool import FunctionTool

from brawler_mcp_server.tasks import (
    CompletionTask,
    ContextTask,
    EvaluationTask,
    NoneTask,
    PostTask,
)
from brawler_mcp_server.utils import AgentTask, TaskHandler, stamp_task_kwargs, tools_for_task

F = TypeVar('F', bound=Callable[..., Any])


class BrawlerMCP(FastMCP):
    """FastMCP server that stamps agent tasks on tools.

    ``@mcp.tool`` is completion. Use ``@context_tool``, ``@eval_tool``,
    ``@post_tool``, and ``@none_tool`` for the other agent tasks.
    FastMCP's ``task=`` keyword on ``tool()`` still means a background MCP task,
    not a Brawler agent task.
    """

    def tool(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        *,
        name: str | None = None,
        tags: set[str] | None = None,
        meta: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Register a completion tool (FastMCP ``@tool`` plus task metadata)."""
        if name is not None:
            kwargs['name'] = name
        kwargs['tags'] = tags
        kwargs['meta'] = meta
        return self._task_tool(name_or_fn, CompletionTask(), **kwargs)

    @overload
    def context_tool(self, name_or_fn: F, /, *, as_user_message: bool = ...) -> F: ...

    @overload
    def context_tool(
        self, name_or_fn: str | None = None, /, *, as_user_message: bool = ..., **kwargs: Any
    ) -> Callable[[F], F]: ...

    def context_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        /,
        *,
        as_user_message: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Register a context tool that must return ``str``."""
        return self._task_tool(name_or_fn, ContextTask(as_user_message=as_user_message), **kwargs)

    @overload
    def eval_tool(self, name_or_fn: F, /) -> F: ...

    @overload
    def eval_tool(self, name_or_fn: str | None = None, /, **kwargs: Any) -> Callable[[F], F]: ...

    def eval_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        /,
        **kwargs: Any,
    ) -> Any:
        """Register an evaluation tool that returns ``tuple[bool, float, str | None]``."""
        return self._task_tool(name_or_fn, EvaluationTask(), **kwargs)

    @overload
    def post_tool(self, name_or_fn: F, /) -> F: ...

    @overload
    def post_tool(self, name_or_fn: str | None = None, /, **kwargs: Any) -> Callable[[F], F]: ...

    def post_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        /,
        **kwargs: Any,
    ) -> Any:
        """Register a post-result side-effect tool that must return ``None``."""
        return self._task_tool(name_or_fn, PostTask(), **kwargs)

    @overload
    def none_tool(self, name_or_fn: F, /) -> F: ...

    @overload
    def none_tool(self, name_or_fn: str | None = None, /, **kwargs: Any) -> Callable[[F], F]: ...

    def none_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        /,
        **kwargs: Any,
    ) -> Any:
        """Register a tool that Brawler agents ignore."""
        return self._task_tool(name_or_fn, NoneTask(), **kwargs)

    async def tools_by_task(self, task: AgentTask | str) -> list[Any]:
        """Return in-process tools whose stamped agent task matches *task*."""
        tools = await self.list_tools()
        return tools_for_task(tools, task)

    def _task_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None,
        handler: TaskHandler,
        **kwargs: Any,
    ) -> Any:
        if isinstance(name_or_fn, str):
            kwargs.setdefault('name', name_or_fn)
            name_or_fn = None
        stamped = stamp_task_kwargs(kwargs, handler.task, extra=handler.extra_meta())

        def apply(fn: Callable[..., Any]) -> FunctionTool | Callable[..., Any]:
            handler.check(fn)
            return super(BrawlerMCP, self).tool(handler.wrap(fn), **stamped)

        if callable(name_or_fn):
            return apply(name_or_fn)
        return apply

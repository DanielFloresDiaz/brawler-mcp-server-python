"""FastMCP subclass with Brawler agent-task decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, overload

from fastmcp import FastMCP
from fastmcp.tools.function_tool import FunctionTool

from brawler_mcp_server.tasks import SKILL_MODES, AgentTask, stamp_task_kwargs, tools_for_task
from brawler_mcp_server.wrapping import require_eval_return, require_return_type, wrap_eval_function

F = TypeVar('F', bound=Callable[..., Any])


class BrawlerMCP(FastMCP):
    """FastMCP server that stamps agent tasks on tools.

    ``@mcp.tool`` is completion. Use ``@context_tool``, ``@eval_tool``,
    ``@post_tool``, ``@skill_tool``, and ``@none_tool`` for the other agent tasks.
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
        stamped = stamp_task_kwargs({'tags': tags, 'meta': meta, **kwargs}, AgentTask.COMPLETION)
        return super().tool(name_or_fn, name=name, **stamped)

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
        stamped = stamp_task_kwargs(kwargs, AgentTask.CONTEXT, extra={'as_user_message': as_user_message})
        return self._task_tool(
            name_or_fn,
            stamped,
            check=lambda fn: require_return_type(fn, str, label='Context tool'),
        )

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
        stamped = stamp_task_kwargs(kwargs, AgentTask.EVALUATION)
        return self._task_tool(
            name_or_fn,
            stamped,
            check=require_eval_return,
            wrap=wrap_eval_function,
        )

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
        stamped = stamp_task_kwargs(kwargs, AgentTask.POST_TOOL)
        return self._task_tool(
            name_or_fn,
            stamped,
            check=lambda fn: require_return_type(fn, type(None), label='Post tool'),
        )

    @overload
    def skill_tool(self, name_or_fn: F, /, *, mode: str = ...) -> F: ...

    @overload
    def skill_tool(self, name_or_fn: str | None = None, /, *, mode: str = ..., **kwargs: Any) -> Callable[[F], F]: ...

    def skill_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None = None,
        /,
        *,
        mode: str = 'always-on',
        **kwargs: Any,
    ) -> Any:
        """Register a skill tool that must return a markdown ``str``."""
        if mode not in SKILL_MODES:
            raise ValueError(f'Invalid skill mode {mode!r}. Allowed modes: {sorted(SKILL_MODES)}.')
        stamped = stamp_task_kwargs(kwargs, AgentTask.SKILL, extra={'mode': mode})
        return self._task_tool(
            name_or_fn,
            stamped,
            check=lambda fn: require_return_type(fn, str, label='Skill tool'),
        )

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
        stamped = stamp_task_kwargs(kwargs, AgentTask.NONE)
        return self._task_tool(name_or_fn, stamped)

    async def tools_by_task(self, task: AgentTask | str) -> list[Any]:
        """Return in-process tools whose stamped agent task matches *task*."""
        tools = await self.list_tools()
        return tools_for_task(tools, task)

    def _task_tool(
        self,
        name_or_fn: str | Callable[..., Any] | None,
        kwargs: dict[str, Any],
        *,
        check: Callable[[Callable[..., Any]], None] | None = None,
        wrap: Callable[[Callable[..., Any]], Callable[..., Any]] | None = None,
    ) -> Any:
        def apply(fn: Callable[..., Any]) -> FunctionTool | Callable[..., Any]:
            if check is not None:
                check(fn)
            registered = wrap(fn) if wrap is not None else fn
            return super(BrawlerMCP, self).tool(registered, **kwargs)

        if name_or_fn is None:
            return apply
        if callable(name_or_fn):
            return apply(name_or_fn)
        kwargs.setdefault('name', name_or_fn)
        return apply

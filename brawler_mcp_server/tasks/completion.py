"""Completion task: model-callable tools, FastMCP default return types."""

from __future__ import annotations

from brawler_mcp_server.utils import AgentTask, TaskHandler


class CompletionTask(TaskHandler):
    """Stamp completion metadata; return types follow FastMCP defaults."""

    task = AgentTask.COMPLETION
    label = 'Completion tool'

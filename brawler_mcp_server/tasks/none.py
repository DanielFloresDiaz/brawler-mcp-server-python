"""None task: generic MCP tools that Brawler agents ignore."""

from __future__ import annotations

from brawler_mcp_server.utils import AgentTask, TaskHandler


class NoneTask(TaskHandler):
    """Stamp none metadata; Brawler agents never call these tools."""

    task = AgentTask.NONE
    label = 'None tool'

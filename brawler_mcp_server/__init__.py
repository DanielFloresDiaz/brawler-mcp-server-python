"""FastMCP wrapper that stamps agent task metadata on MCP tools."""

from brawler_mcp_server.server import BrawlerMCP
from brawler_mcp_server.tasks import META_NAMESPACE, AgentTask, task_from_meta, tools_for_task

__all__ = [
    'META_NAMESPACE',
    'AgentTask',
    'BrawlerMCP',
    'task_from_meta',
    'tools_for_task',
]

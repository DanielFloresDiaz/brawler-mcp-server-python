"""One handler class per agent task."""

from brawler_mcp_server.tasks.completion import CompletionTask
from brawler_mcp_server.tasks.context import ContextTask
from brawler_mcp_server.tasks.evaluation import EvaluationTask
from brawler_mcp_server.tasks.none import NoneTask
from brawler_mcp_server.tasks.post import PostTask
from brawler_mcp_server.utils import AgentTask

__all__ = [
    'AgentTask',
    'CompletionTask',
    'ContextTask',
    'EvaluationTask',
    'NoneTask',
    'PostTask',
]

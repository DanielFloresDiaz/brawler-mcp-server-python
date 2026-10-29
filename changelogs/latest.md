# Changelog

## [0.1.0] - 2026-10-29

Initial release of the Brawler MCP server wrapper for FastMCP 4.

**Core library:**

* Added `BrawlerMCP` with task decorators (`context_tool`, `eval_tool`, `post_tool`, `none_tool`) and completion tools via `@tool`.
* Stamped each tool with `_meta.mcp_server.task` (and optional `as_user_message` for context tools) so clients can filter by agent task.
* Added `tools_for_task` and `tools_by_task` helpers for listing tools by task.

**Examples and packaging:**

* Shipped example MCP servers (`brawler-mcp-example`, `brawler-mcp-task-server`) and documented the wire contract for Brawler agents.

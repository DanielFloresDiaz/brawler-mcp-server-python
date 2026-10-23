# Brawler MCP Server (Python)

FastMCP wrapper that tags tools with **agent tasks** so a client can list and run context, completion, evaluation, post, skill, and none tools from one MCP server.

This is not a fork of [FastMCP](https://github.com/PrefectHQ/fastmcp). It depends on FastMCP 4 and subclasses `FastMCP`. Later language ports (`brawler-mcp-server-typescript`, and so on) should implement the same wire contract.

Brawler agents attach one MCP server as a resource, then fetch tools by task: context tools build the prompt, completion tools are offered to the model, post and eval tools run after a result, skill tools inject or load instructions.

---

## What this adds on top of FastMCP

| FastMCP | This package |
| --- | --- |
| `@mcp.tool` | Same decorator, stamped as **completion** |
| No task model | `@context_tool`, `@eval_tool`, `@post_tool`, `@skill_tool`, `@none_tool` |
| Tags are optional | Every task decorator sets a task tag and `_meta.mcp_server` |
| `tools/list` returns a flat list | Clients filter by `_meta.mcp_server.task` (or call `tools_by_task`) |

Untagged tools from a plain FastMCP server are treated as **completion** by Brawler. Tools from this package always carry an explicit task.

---

## Install

```bash
uv add brawler-mcp-server-python
# or
pip install brawler-mcp-server-python
```

Requires Python 3.10+ and FastMCP 4.1.3+.

---

## Quick start

```python
from brawler_mcp_server import BrawlerMCP

mcp = BrawlerMCP('Docs')


@mcp.context_tool
def policies() -> str:
    """Injected into the agent system prompt."""
    return 'Always cite sources.'


@mcp.context_tool(as_user_message=True)
def ticket() -> str:
    return 'Ticket #123 is still open.'


@mcp.tool
def search(q: str) -> str:
    """Completion tool offered to the model."""
    return f'Results for {q}'


@mcp.eval_tool
def grounded(answer: str) -> tuple[bool, float, str | None]:
    if not answer.strip():
        return False, 0.0, 'Answer is empty.'
    return True, 1.0, None


@mcp.post_tool
def audit(answer: str) -> None:
    return None


@mcp.skill_tool(mode='always-on')
def style() -> str:
    return """---
name: style
description: Prefer short sentences.
---
# Style
Use short sentences.
"""


@mcp.none_tool
def ping() -> str:
    """Visible to generic MCP clients; Brawler agents ignore none tools."""
    return 'pong'


if __name__ == '__main__':
    mcp.run()
```

`mcp.run()` speaks stdio by default. Use FastMCP HTTP transports when you need a remote endpoint.

Example server shipped with this package:

```bash
uv run brawler-mcp-example
```

---

## Wire contract

MCP `tools/list` has no task filter. Identity lives on each tool so any language client can list a subset after listing.

```json
{
  "name": "policies",
  "description": "Injected into the agent system prompt.",
  "_meta": {
    "mcp_server": {
      "task": "context",
      "as_user_message": false
    },
    "fastmcp": {
      "tags": ["context"]
    }
  }
}
```

### `_meta.mcp_server`

| Field | Type | When |
| --- | --- | --- |
| `task` | `context` \| `completion` \| `evaluation` \| `post_tool` \| `skill` \| `none` | Always |
| `as_user_message` | `bool` | Context only. `true` injects the string as a user message instead of the system prompt. |
| `mode` | `always-on` \| `auto` | Skill only. Always-on content is injected with context; auto skills are loaded by name. |

FastMCP also copies the task into `_meta.fastmcp.tags`. Clients may use either field. If both are missing, treat the tool as `completion`.

### Listing only context tools

```python
from fastmcp import Client
from brawler_mcp_server import tools_for_task

async with Client(mcp) as client:
    tools = await client.list_tools()
    context_tools = tools_for_task(tools, 'context')
```

In-process (no MCP round-trip):

```python
context_tools = await mcp.tools_by_task('context')
```

---

## Return types

| Decorator | Python return | On the wire |
| --- | --- | --- |
| `@context_tool` / `@skill_tool` | `str` | Single text content |
| `@eval_tool` | `tuple[bool, float, str \| None]` | JSON `{"is_valid": bool, "score": float, "feedback": str \| null}` |
| `@post_tool` | `None` | Empty / ignored text |
| `@tool` / `@none_tool` | FastMCP default | FastMCP default |

Decorators check the annotation at registration time.

---

## Agent tasks (this package)

Router and training are not included. Those are not function-tool tasks on a Brawler agent.

| Task | Decorator | Agent use |
| --- | --- | --- |
| `context` | `@context_tool` | Prompt / user-message injection |
| `completion` | `@tool` | Model-callable tools |
| `evaluation` | `@eval_tool` | After the final result |
| `post_tool` | `@post_tool` | Side effects after the result, before eval |
| `skill` | `@skill_tool` | Always-on context or auto `load_skill` |
| `none` | `@none_tool` | Not used by Brawler agents |

---

## Using with Brawler

Register the server as an MCP resource on an agent the same way as any other MCP connection (`MCPTool.from_server` / `agent.mcp(...)` / `POST /mcps`). The persisted row stays `entity_type=mcp` with `task=completion` (the connection). Remote tools carry the task in `_meta.mcp_server`.

At run time the agent lists tools, keeps completion tools for the model, and calls context / skill / post / eval tools at the matching pipeline stage.

---

## Development

```bash
uv sync --all-extras --group lint --group dev
make test
make typecheck
```

---

## License

Apache-2.0

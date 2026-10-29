# Brawler MCP Server (Python)

FastMCP wrapper that tags tools with **agent tasks** so a client can list and run context, completion, evaluation, post, and none tools from one MCP server.

This is not a fork of [FastMCP](https://github.com/PrefectHQ/fastmcp). It depends on FastMCP 4 and subclasses `FastMCP`. Later language ports (`brawler-mcp-server-typescript`, and so on) should implement the same wire contract.

Brawler agents attach one MCP server as a resource, then fetch tools by task: context tools build the prompt, completion tools are offered to the model, post and eval tools run after a result. Native Brawler skills stay on the agent; MCP does not offer a skill task.

---

## What this adds on top of FastMCP

| FastMCP | This package |
| --- | --- |
| `@mcp.tool` | Same decorator, stamped as **completion** |
| No task model | `@context_tool`, `@eval_tool`, `@post_tool`, `@none_tool` |
| Tags are optional | Every task decorator sets a task tag and `_meta.mcp_server` |
| `tools/list` returns a flat list | Clients filter by `_meta.mcp_server.task` (or call `tools_by_task`) |

Untagged tools from a plain FastMCP server are treated as **completion** by Brawler. Tools from this package always carry an explicit task. FastMCP tags that are not agent tasks (for example `skill`, `router`, `training`) are ignored when resolving the task; an unknown ``mcp_server.task`` value is treated as **none**.

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


@mcp.none_tool
def ping() -> str:
    """Visible to generic MCP clients; Brawler agents ignore none tools."""
    return 'pong'


if __name__ == '__main__':
    mcp.run()
```

`mcp.run()` speaks stdio by default. Use FastMCP HTTP transports when you need a remote endpoint.

Example server shipped in ``examples/``:

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
| `task` | `context` \| `completion` \| `evaluation` \| `post_tool` \| `none` | Always |
| `as_user_message` | `bool` | Context only. `true` injects the string as a user message instead of the system prompt. |

FastMCP also copies the task into `_meta.fastmcp.tags`. Clients may use either field. If both are missing, treat the tool as `completion`. If `task` is set to an unsupported value, treat the tool as `none`.

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
| `@context_tool` | `str` | Single text content |
| `@eval_tool` | `tuple[bool, float, str \| None]` | JSON `{"is_valid": bool, "score": float, "feedback": str \| null}` |
| `@post_tool` | `None` | Empty / ignored text |
| `@tool` / `@none_tool` | FastMCP default | FastMCP default |

Decorators check the annotation at registration time.

---

## Agent tasks (this package)

Router, training, and skill are not included. Router and training are not function-tool tasks on a Brawler agent. Skills are native Brawler tools, not MCP tasks.

| Task | Decorator | Agent use |
| --- | --- | --- |
| `context` | `@context_tool` | Prompt / user-message injection |
| `completion` | `@tool` | Model-callable tools |
| `evaluation` | `@eval_tool` | After the final result |
| `post_tool` | `@post_tool` | Side effects after the result, before eval |
| `none` | `@none_tool` | Not used by Brawler agents |

---

## Using with Brawler

Register the server as an MCP resource on an agent the same way as any other MCP connection (`MCPClient.from_server` / `agent.mcp(...)` / `POST /mcps`). The persisted row stays `entity_type=mcp` with `task=completion` (the connection). Remote tools carry the task in `_meta.mcp_server`.

At run time the agent lists tools, keeps completion tools for the model, and calls context / post / eval tools at the matching pipeline stage.

---

## Development

```bash
uv sync --all-extras --group lint --group dev
uv run pytest tests/
make test
make typecheck
```

If this repo is checked out as a submodule of brawler, `uv run` still uses this
package's own environment. Do not run these tests with brawler's FastMCP 3 venv.

CI (`.github/workflows/testing.yaml`) runs lint, pyright, and pytest on pull requests to `main`. The release workflow (`.github/workflows/release.yaml`) runs the same tests, builds the package, creates a GitHub release from `changelogs/v<tag>.md`, and publishes to PyPI when a version tag is pushed.

### Releasing

1. Bump `version` in `pyproject.toml`.
2. Add `changelogs/v<tag>.md` and update `changelogs/latest.md` to match (tag includes the `v` prefix, e.g. `v0.1.0`).
3. Merge to `main`, then tag and push: `git tag v0.1.0 && git push origin v0.1.0`.

Before the first PyPI publish, register a **trusted publisher** on [pypi.org](https://pypi.org) for project `brawler-mcp-server-python`: owner `DanielFloresDiaz`, repository `brawler-mcp-server-python`, workflow name `release.yaml`, environment blank. No API token secret is required.

After merging workflow changes, smoke-test locally with `uv build` and inspect `dist/`, then confirm the tag workflow uploads GitHub release assets and the new version appears on PyPI.

---

## License

Apache-2.0

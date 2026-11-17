---
name: development
description: >-
  How to develop brawler-mcp-server-python: package layout, the task decorators
  and the _meta.mcp_server wire contract that brawler reads, the testkit and
  examples, its separate FastMCP 4 environment, and which checks to run. Use
  when changing decorators, tool metadata, helpers, the testkit, or examples.
  Also covers validating every change (lint, typecheck, tests) and the user's
  project rules for this repo.
license: MIT
---

# brawler-mcp-server-python development guide

## Layout

| Path | Role |
|---|---|
| `brawler_mcp_server/server.py` | `BrawlerMCP` (a FastMCP subclass) and the task decorators |
| `brawler_mcp_server/tasks/` | Task definitions and `_meta.mcp_server` stamping |
| `brawler_mcp_server/utils.py` | `tools_for_task`, `tools_by_task` |
| `brawler_mcp_server/testkit.py` | Helpers for testing servers built with this package |
| `examples/` | `example.py`, `task_server.py` (installed as `brawler-mcp-example` / `brawler-mcp-task-server`) |
| `tests/` | pytest |

## Environment

```bash
uv sync --all-extras --group lint --group dev
```

This package has its own venv, even when it is checked out as a brawler submodule. Run `uv run` from this directory.

## Wire contract

Each tool carries `_meta.mcp_server.task` (`context`, `completion`, `evaluation`, `post_tool`, `none`), and context tools can also carry `as_user_message`. Brawler reads these in `brawler/mcp/client/base.py` and `brawler/mcp/task/base.py` to decide when to call a tool. A change to the keys or values is breaking: update both repos, document it in the README "Wire contract" section, and release this package before brawler depends on it.

## Checks

```bash
make pre-commit   # hooks + ruff
make typecheck    # pyright
make test         # pytest (coverage)
```

When decorators, return types, or tasks change, update the README tables and the examples in the same change. Use the `release` skill to publish to PyPI.

## Related skills

- `release`

## Project rules

Rules the user has set for this repository. They override the defaults above. Add an entry whenever the user states one (see "Keeping this skill current"), using the format `- YYYY-MM-DD: <rule>. <reason, if given>`.

_None recorded yet._

## Keeping this skill current

This skill is versioned with the repository, so it must evolve with it. Update it **in the same change**, not as a follow-up, whenever:

- **Something changes:** layout, commands or Make targets, env vars, ports, generated artifacts, CI workflows, cross-repo contracts, or dependency pins. Also when you find a statement here that is wrong or stale.
- **The user sets a rule:** a preference, convention, or prohibition ("never use X", "always do Y", "don't touch Z", a frontend pattern to avoid). Record it under **Project rules** (in this file), with the date (YYYY-MM-DD) and the reason if given. Rules about how code is written go in the `development` skill. Rules about how versions ship go in the `release` skill.
- **You learn something reusable:** a pitfall you hit, a mistake a line here would have prevented, or a non-obvious procedure you worked out. Add it to the section it belongs to.
- **A task repeats:** if it is not covered by `development` or `release`, create a new skill at `.claude/skills/<kebab-name>/SKILL.md` (frontmatter `name` = the folder name, plus a `description` that says what it does and when to use it), and list it under "Related skills" in the `development` skill.

How to edit:

- Check every path, command, and target against the repo before writing it down.
- Keep it short. Edit the existing section instead of appending duplicates, and delete what is no longer true.
- Never record secrets, tokens, personal data, or one-off details of a single task.
- An explicit instruction from the user in the current conversation wins over a recorded rule. If they change a rule, update the entry.
- Tell the user in your final message which skill you changed and why. The skill file is part of this repository (often a git submodule), so include it when they ask you to commit.

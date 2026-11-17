---
name: release
description: >-
  Prepare a brawler-mcp-server-python release: summarize the unreleased delta,
  write the versioned changelog, bump pyproject.toml, check the _meta.mcp_server
  wire contract against brawler's MCP client, reconcile README, and run lint,
  typecheck, tests and build before the PyPI tag. Use when cutting a release,
  bumping the version, writing release notes, checking release readiness, or
  asking what is unreleased.
license: MIT
---

# brawler-mcp-server-python release workflow

A FastMCP 4 wrapper (`BrawlerMCP`, task decorators `@context_tool`, `@tool`, `@eval_tool`, `@post_tool`, `@none_tool`) that stamps each tool with `_meta.mcp_server.task`, so Brawler agents know when to call it. A `v<version>` tag runs `release.yaml`: tests, a version check against `pyproject.toml`, `uv build`, a GitHub release from `changelogs/v<version>.md`, and a **PyPI** publish through a trusted publisher. Brawler consumes it from PyPI (`brawler-mcp-server-python==<ver>` in brawler's dev group).

Run commands from this repo root. It uses its **own** venv. Never run it with brawler's environment.

## 1. Delta

Default range: `main..<release branch>` (this repo works mainly on `main`, so if there is no `develop`, use `<last tag>..main`). If the user says to **omit uncommitted changes**, use only committed history. Read the commits and diffs in `brawler_mcp_server/` (`server.py`, `tasks/`, `utils.py`, `testkit.py`), `examples/`, and `pyproject.toml`, and group them by user-facing area: decorators, metadata contract, helpers (`tools_for_task`, `tools_by_task`), testkit, examples, packaging.

## 2. Version and changelog

- Use three-segment semver. The current version is the highest `changelogs/v*.md`, compared numerically, and it must equal `pyproject.toml` `version`. Use PATCH for fixes. Use MINOR for features, and on `0.x` also for breaking changes to the decorators or to the `_meta.mcp_server` shape.
- Mirror `changelogs/v0.1.0.md` (`# Changelog`, `## [<version>] - YYYY-MM-DD`, a summary paragraph, `**Section:**` headings with `*` bullets). Write `changelogs/v<version>.md` and an exact copy at `latest.md`. Use today's date and end each file with one trailing newline.

### Semantic versioning rules

These rules apply to every version this skill produces. The repo-specific bump guidance above decides which segment moves.

- **Format:** `MAJOR.MINOR.PATCH`, exactly three non-negative integers with no leading zeros (`0.13.0`, never `0.13`, `v0.13`, or `0.013.0`). Add a pre-release only when the user asks: `-rc.1` in npm and Cargo versions, the PEP 440 form (`0.2.0rc1`, `0.0.1b0`) in Python packages.
- **Ordering:** compare segment by segment as integers, never as strings (`0.10.0` > `0.9.0`, `0.2.10` > `0.2.9`). The current version is the highest released one, and the new one must be strictly greater.
- **Bumps:** MAJOR for incompatible changes to the public surface (API, wire or gRPC contract, CLI flags, env vars, config, schema, exported symbols). MINOR for backward-compatible features. PATCH for backward-compatible fixes. Increment exactly one segment and reset the lower ones to `0`.
- **`0.y.z`:** the public surface is not yet stable. Breaking changes bump MINOR. Never move to `1.0.0` or any new MAJOR without an explicit user request.
- **Immutability:** never reuse, decrease, or retag a published version. If a pushed tag is wrong, fix forward with a new PATCH.
- **No-op deltas:** if nothing consumer-visible changed, do not bump. Report that instead.
- **One version everywhere:** the manifest, the lockfile entry, the changelog filename and heading, README badges and mentions, any generated spec (`info.version`), and the git tag (with the `v` prefix where the workflow expects it) carry the same number.

## 3. Release readiness

- [ ] **Wire contract:** if `_meta.mcp_server` keys or task names changed, the brawler side that reads them (`brawler/mcp/client/base.py`, `brawler/mcp/task/base.py`, `brawler/mcp/server/utils.py`) understands the new shape, or the release is marked breaking and the brawler follow-up is listed.
- [ ] **FastMCP range** (`fastmcp>=4.1.1,<5`) is compatible with brawler's own `fastmcp` pin.
- [ ] **README:** What this adds, Install, Quick start, Wire contract (`_meta.mcp_server`, context-only listing), Return types, the Agent tasks table, Using with Brawler, Development and Releasing.
- [ ] **Examples:** `examples/example.py` and `examples/task_server.py` (the `brawler-mcp-example` and `brawler-mcp-task-server` scripts) still run with the new API.
- [ ] `uv lock --check` passes.

Gate:

```bash
uv sync --all-extras --group lint --group dev
make pre-commit
make typecheck
make test
uv build && ls dist/     # inspect the wheel and sdist contents
```

## 4. Deliverable and follow-ups

Report the range and commit count, the grouped summary, the version and date, the files changed, the README updates, and the gate results. After the tag publishes, brawler bumps `brawler-mcp-server-python==<version>` in its dev group, re-locks, and records the new submodule SHA. Do not commit, tag, or push unless asked.

### Pull request title and summary

Always finish the deliverable with a ready-to-paste text for the release pull request (the source branch of the range from section 1 into its target). The user copies it into GitHub, so do not open the PR yourself. Give it as two separate fenced `markdown` blocks, one labelled **PR title** and one labelled **PR summary**, so each copies in one click.

- **PR title:** one line, 70 characters or fewer, in the form `Release v<version>: <the one or two headline changes>`. No trailing period.
- **PR summary:** written for reviewers, from the changelog and the actual diff, not from memory:
  - `## Summary`: two or three sentences on what ships and why it matters.
  - `## Changes`: the changelog bullets, grouped by area, consumer-facing items only.
  - `## Breaking changes / migration`: what downstream repos or operators must do. Omit the section when there is nothing.
  - `## Release checklist`: the version, the files that carry it, and each readiness check marked pass, fixed, or skipped (with the reason). Never mark a check as passed that was not run.
  - `## Follow-ups`: the steps that happen after the merge (tag, downstream pin bumps, submodule SHAs).
- Keep the title and summary consistent with `changelogs/v<version>.md`: same version, same facts. If there is no release (a no-op delta), say so instead and give no PR text.

## Release rules

Release-specific rules the user has set for this repository. They override the steps above. Use the format `- YYYY-MM-DD: <rule>. <reason, if given>`.

_None recorded yet._

## Keeping this skill current

This skill is versioned with the repository, so it must evolve with it. Update it **in the same change**, not as a follow-up, whenever:

- **Something changes:** layout, commands or Make targets, env vars, ports, generated artifacts, CI workflows, cross-repo contracts, or dependency pins. Also when you find a statement here that is wrong or stale.
- **The user sets a rule:** a preference, convention, or prohibition ("never use X", "always do Y", "don't touch Z", a frontend pattern to avoid). Record it under **Release rules** (in this file), with the date (YYYY-MM-DD) and the reason if given. Rules about how code is written go in the `development` skill. Rules about how versions ship go in the `release` skill.
- **You learn something reusable:** a pitfall you hit, a mistake a line here would have prevented, or a non-obvious procedure you worked out. Add it to the section it belongs to.
- **A task repeats:** if it is not covered by `development` or `release`, create a new skill at `.claude/skills/<kebab-name>/SKILL.md` (frontmatter `name` = the folder name, plus a `description` that says what it does and when to use it), and list it under "Related skills" in the `development` skill.

How to edit:

- Check every path, command, and target against the repo before writing it down.
- Keep it short. Edit the existing section instead of appending duplicates, and delete what is no longer true.
- Never record secrets, tokens, personal data, or one-off details of a single task.
- An explicit instruction from the user in the current conversation wins over a recorded rule. If they change a rule, update the entry.
- Tell the user in your final message which skill you changed and why. The skill file is part of this repository (often a git submodule), so include it when they ask you to commit.

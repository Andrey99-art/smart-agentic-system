# Changelog

## ak 0.8.0 — 2026-10-10
- `/ak:feedback`: drafts a redacted feedback issue from the session; the user reviews and submits it. No telemetry, no automatic sending.
- GitHub issue form `.github/ISSUE_TEMPLATE/feedback.yml`.

## ak 0.7.0 — 2026-10-10
Prepared for publication:
- Licensed under Apache-2.0.
- Generic wording: personal preferences moved into one editable "Profile" block in the engineering skill; README gained "Make it yours".
- **Renamed:** review gate opt-out `ANDREY_REVIEW_GATE` → `AK_REVIEW_GATE`.
- Inventory note trimmed of account-specific details.

## ak 0.6.0 — 2026-10-10
Compounding without bloat:
- `test_budgets.py`: size budgets for skills, references, stack guides, agents, templates and scripts, plus description length.
- Agents record memory patterns with a `(seen: N)` count; `/inbox` proposes promoting patterns seen 3 or more times into permanent rules, then prunes them from memory.
- `/ak:handoff` suggests `/ak:retro` when a session had lessons worth keeping.

## ak 0.5.1 — 2026-10-10
- `/ak:learn` checks answers against the user's actual settings and never recommends undoing a deliberate choice. First real use suggested auto-allow, which conflicts with `autoAllowBashIfSandboxed: false`.

## ak 0.5.0 — 2026-10-10
- New commands: `/ak:commit` (explicit staging, conventional message, commit after a yes, never pushes) and `/ak:learn <topic>` (answers verified against the live docs).
- This repo only: `/inbox` project skill for processing retro proposals.

## ak 0.4.0 — 2026-10-10
- Renamed the plugin `andrey-core` → `ak` for short commands: `/ak:start`, `/ak:commit`, `/ak:handoff`, `/ak:retro`, `/ak:learn`. Agents are now `ak:code-reviewer` and `ak:prompt-engineer`; memory folders moved to `~/.claude/agent-memory/ak-*`. Older entries keep the old name.

## andrey-core 0.3.1 — 2026-10-10
- engineering skill: stage files by explicit path; `git add -A` fails inside the Bash sandbox.

## andrey-core 0.3.0 — 2026-10-10
Dynamic stack support replaces the planned stack plugins (architecture §1a):
- Stack guides in `skills/start/references/stacks/` (Django first; uv is the default package manager), read only by `/start`.
- prompt-engineer derives `.claude/rules/` from the repo's actual code; the guide only fills gaps.
- New `format_on_edit` PostToolUse hook: formats edited files from `.claude/format.json`, exact allow-listed formatter commands only.
- Template and init: no `enabledPlugins`; `format.json` only for formatters installed on the machine.

## andrey-core 0.2.0 — 2026-10-10
From the first real project run (inbox `2026-10-10-shop-*`):
- Templates: stack allow-lists use exact commands only (no `*`); `.gitignore` additions gained per-stack blocks that init appends for the detected stack.
- start/init: approval order is agents → rules → CLAUDE.md; a rejected role's references are removed and its paths reassigned.
- code-reviewer runs in the foreground (`background: false`), so review and fixes finish in one turn.
- review gate: reviews only files changed since their last review; at most 3 requests per file per session.

## andrey-core 0.1.0 — 2026-10-10
First version: engineering skill; start, handoff and retro commands; code-reviewer and prompt-engineer agents; guard, secret scan, agent write guard, review gate and session status hooks; Balanced project template.

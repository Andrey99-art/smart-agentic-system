---
name: retro
description: Turn lessons from this session or project into lasting improvements. Project-specific fixes become diffs to CLAUDE.md, rules or agents; general ones become proposals in the andrey-kit inbox. Run at the end of a feature or project.
disable-model-invocation: true
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# Retro

Every repeated mistake is a system gap: a missing instruction, reference, check or hook. Find the gaps this work exposed and propose the smallest fix for each. Never apply a change without the user's yes.

## Facts (collected before you read this)
- Recent commits: !`git log --oneline -30 2>/dev/null; true`
- Project setup: !`ls -d CLAUDE.md STATE.md .claude/agents .claude/rules .claude/agent-memory 2>/dev/null; true`
- andrey-kit inbox: `${CLAUDE_PLUGIN_ROOT}/../../docs/inbox/` (valid only while the plugin loads in place from the andrey-kit repo; see step 3)

## 1. Collect evidence (no repo-wide reading)
Use this conversation, STATE.md, the commits above, and the project agents' memory (`.claude/agent-memory/`). Look for:
- the user's corrections ("no, do it like …"), rejected drafts and repeated questions;
- code-reviewer findings that were real bugs, especially repeated kinds;
- commands that failed for setup reasons, and guard or permission blocks that surprised the user;
- steps that took several tries.

## 2. Turn evidence into lessons (at most 5)
For each lesson: **Evidence** (commit, file:line, or the correction) → **Root cause** (which instruction, reference, check or hook was missing or wrong) → **Fix** (target file and exact text or diff) → **Verify** (the test, eval or check that shows it worked).
Drop a lesson if it would not prevent a repeat, if it restates general advice, or if the target already says it (read the target first).

## 3. Route each lesson
- **Project-specific** (this repo's commands, layout, conventions, agent scopes): show a diff to `CLAUDE.md`, `.claude/rules/*.md` or `.claude/agents/*.md`; apply only after a yes. Keep the budgets: CLAUDE.md ≤ 100 lines, rule ≤ 40, agent ≤ 60.
- **General** (would help every project: the engineering skill, role guide, templates, hooks, agents): write one proposal file to the inbox as `YYYY-MM-DD-<project>-<slug>.md`, using the four fields from step 2 plus `Target: plugins/ak/...`. Writing there is outside the project, so the user is asked. First confirm the inbox is inside the andrey-kit git repo (`git -C <inbox> rev-parse --show-toplevel` succeeds and contains `.claude-plugin/marketplace.json`); if not (e.g. a plugin cache copy, wiped on update), print the proposal for the user to save instead.

## 4. Finish
Three lines: lessons found (project / general) · what was applied or filed · what the user should do next (for inbox proposals: review them in the andrey-kit repo).

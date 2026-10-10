---
name: handoff
description: Save where work stands before leaving. Updates STATE.md (Done, Next, Open, Decisions; at most 60 lines) from this session and git, so the next /ak:start resumes cheaply.
disable-model-invocation: true
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# Handoff

STATE.md is the project's memory between sessions: a fresh Claude must be able to resume from it alone. Build it from this conversation and the facts below; do not re-read the repo.

## Facts (collected before you read this)
- Now: !`date '+%Y-%m-%d %H:%M'`
- STATE.md lines: !`wc -l STATE.md 2>/dev/null; true`
- Recent commits: !`git log --oneline -15 2>/dev/null; true`
- Uncommitted: !`git status --short 2>/dev/null | head -20; true`
- Template (if STATE.md is missing): `${CLAUDE_PLUGIN_ROOT}/templates/project/STATE.md`

## Update STATE.md
Keep the template's sections and set `Updated:` to "Now".
- **Done**: latest first, at most 8, with short commit hashes. Drop the oldest; git keeps history.
- **Next**: 1–3 concrete steps. The first must be startable without this conversation (name files, commands, the open decision).
- **Open**: blockers, unanswered questions, known bugs, and **uncommitted work** (from "Uncommitted").
- **Decisions**: only new ones made this session, each with its reason; at most 8 in total.

Rules: at most 60 lines · facts, not narrative · relative paths · never secrets or credentials · if nothing changed since the last handoff, say so and stop.

## Approve and save
1. Show the change as a diff (or the full file if new) and write it only after the user says yes.
2. If there is uncommitted work, offer one commit with a conventional message (STATE.md plus the work, or STATE.md alone, as the user prefers). Git writes ask anyway; never push.
3. End with one line: `Saved. Next time: /ak:start (or claude --continue within an hour: the cache is still warm).`
4. If this session had confirmed review findings, user corrections, or steps that needed several tries, add one more line: `This session has lessons worth keeping: run /ak:retro.`

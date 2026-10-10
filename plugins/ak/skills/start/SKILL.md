---
name: start
description: Start or continue work in this project. Sets up a new project (questions, prompt-engineer drafts, role agents, Balanced settings) or resumes from STATE.md and proposes the next step.
disable-model-invocation: true
argument-hint: "[init|continue]"
allowed-tools: Read(/${CLAUDE_PLUGIN_ROOT}/**)
---

# Start

The user runs this once at the beginning of a session. You are the only one who talks to the user; agents report to you.

## Project state (collected before you read this)
- Directory: !`pwd`
- STATE.md: !`test -f STATE.md && echo present || echo absent`
- Existing setup: !`ls -d CLAUDE.md .claude/settings.json .claude/agents .claude/rules 2>/dev/null; true`
- Git: !`git status --short --branch 2>/dev/null | head -15; true`

## Plugin paths (reference files are not substituted, so use these)
- Templates: `${CLAUDE_PLUGIN_ROOT}/templates/project/`
- Role guide: `${CLAUDE_SKILL_DIR}/references/roles.md`
- Stack guides: `${CLAUDE_SKILL_DIR}/references/stacks/<stack>.md` (one per known stack)

## Route
- Argument `init`, or STATE.md absent → read `${CLAUDE_SKILL_DIR}/references/init.md` and follow it.
- Argument `continue`, or STATE.md present → read `${CLAUDE_SKILL_DIR}/references/continue.md` and follow it.
- Argument given: `$ARGUMENTS` (empty means decide from STATE.md).

## Rules for both flows
- **Never overwrite.** For a file that exists, show the proposed change as a diff and apply it only after the user says yes. New files are also shown first and written only after a yes.
- **Every agent needs the user's approval** before its file is written. Show each agent's name, purpose and tools; let the user accept, edit or reject each one (use AskUserQuestion for the choice).
- **Ask little.** At most 6 questions in a whole init, fewer when the repo already answers them. Never ask what you can read from files.
- **Delegate drafting** of CLAUDE.md, rules and agents to the `ak:prompt-engineer` agent; one delegation with everything it needs, not several small ones.
- **Stay cheap.** Do not read the whole repo; manifests, the tree (depth 2) and recent git log are enough.
- **Finish with three lines:** what was set up or found · what the user must do now (if anything) · the proposed next step.

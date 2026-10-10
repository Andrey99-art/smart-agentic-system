# 06 — Subagents

Source: live docs, fetched 2026-10-09. [sub-agents](https://code.claude.com/docs/en/sub-agents), [agent-teams](https://code.claude.com/docs/en/agent-teams)

## Facts we use
- ✅ **Precedence:** managed > `--agents` CLI > project `.claude/agents/` > user `~/.claude/agents/` > plugin `agents/`.
  - Identity is the `name` field, which can't contain `:`.
  - Plugin agents are namespaced as `<plugin>:<name>`.
  - [#choose-the-subagent-scope](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope)
- ✅ **Frontmatter.** `name` and `description` are required; unknown fields are silently ignored.
  - We use: `tools`/`disallowedTools`, `model`, `effort`, `maxTurns`, `skills` (preloaded in full), `memory`, `isolation: worktree`, `background`, `omitClaudeMd`.
  - Plugin agents ignore `permissionMode`, `hooks` and `mcpServers`.
  - [#frontmatter-reference](https://code.claude.com/docs/en/sub-agents#frontmatter-reference)
- ✅ **Delegation.**
  - Claude delegates automatically when a task matches an agent's `description`.
  - You can also name the agent explicitly ("use the X agent", `@"X (agent)"`, `claude --agent X`).
  - Agent descriptions share a 15,000-token budget, separate from skills.
  - Subagents can nest up to 3 levels.
  - [#understand-automatic-delegation](https://code.claude.com/docs/en/sub-agents#understand-automatic-delegation)
- ✅ **Context.** A subagent gets its own prompt, the delegation message, **CLAUDE.md**, a git status snapshot and any preloaded `skills`.
  - It does **not** get the chat history, invoked skills or auto memory.
  - It returns only its final report.
  - [#what-loads-at-startup](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup)
- ✅ **Permissions.**
  - Under `acceptEdits`/auto, subagents use the session's mode.
  - Plugin hooks and PreToolUse fire inside subagents.
  - Permission prompts reach you, including from background agents; Esc denies a single call.
- ✅ **Reload.** Edits to `.claude/agents/` are picked up within seconds. But the **first file in a new `agents/` dir needs a restart**.
- ✅ **`memory`.**
  - `project` scope stores notes in `.claude/agent-memory/<name>/`, shareable through git. The first 200 lines of its `MEMORY.md` load.
  - `memory` also grants Read, Write and Edit.
  - It does nothing if auto memory is off.
- ✅ **Cost.** Each fresh subagent has its own cache with a **5-min TTL, even on a subscription**. A fork shares the parent's cache. [prompt-caching#subagents-and-the-cache](https://code.claude.com/docs/en/prompt-caching#subagents-and-the-cache)
- ❓ Without `effort`, the session level probably applies; the docs don't say it outright. Test it with a hook that logs the `effort` input field.
- ✅ **Agent teams** are experimental and off by default (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`). They cost more than subagents.

## Impact on design
- **Role agents** (frontend, backend, devops, ui-ux, …) are project agents in `.claude/agents/`. `start` writes them after you approve. If the folder is new, `start` tells you to restart with `claude --continue`.
- **Global agents** live in `andrey-core`: `prompt-engineer` (read-only) and `code-reviewer` (read-only: `disallowedTools: Edit, Write`). Their safety comes from `tools` lists and plugin hooks.
- **CLAUDE.md is copied into every subagent,** so every line costs once per delegation. `prompt-engineer` must keep it short.
- **Cold-cache cost per spawn.** Fewer, larger delegations beat many small ones. Role agents are proposed only when they'll be reused, and a small site may get 2 agents, not 4.
- **Continuity:** role agents use `memory: project`, so lessons survive between sessions and travel with git.
- 📌 parking_lot: agent teams. Revisit when they leave experimental.

## Commands you'll use
- `claude --continue` restarts after the first agent is created, keeping the conversation.
- `@"code-reviewer (agent)"` calls a specific agent directly.
- `claude --agent <name>` runs a whole session as that agent.

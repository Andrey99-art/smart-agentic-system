# 08 — Memory, CLAUDE.md, rules

Source: live docs, fetched 2026-10-09. [memory](https://code.claude.com/docs/en/memory)

## Facts we use
- ✅ **Locations:**
  - user: `~/.claude/CLAUDE.md`;
  - project: `./CLAUDE.md` or `./.claude/CLAUDE.md`;
  - local: `./CLAUDE.local.md` (gitignored);
  - managed: `/etc/claude-code/CLAUDE.md`.
  - Parent directories load at launch. Subdirectory files load only when a file there is read or edited. [#how-claude-md-files-load](https://code.claude.com/docs/en/memory#how-claude-md-files-load)
- ✅ **Rules.** `.claude/rules/**/*.md` files are found recursively.
  - A rule without `paths` loads at launch, like CLAUDE.md.
  - A rule with `paths` (globs) loads only when a matching file is read or edited.
  - `paths` is the only frontmatter field. User-level rules go in `~/.claude/rules/`.
  - [#path-specific-rules](https://code.claude.com/docs/en/memory#path-specific-rules)
- ✅ **Imports.** `@path` expands at launch, up to 4 hops deep. It saves no context; it only organizes files.
- ✅ **Auto memory.** Claude keeps notes in `~/.claude/projects/<project>/memory/`.
  - They are machine-local and shared across worktrees.
  - `MEMORY.md` loads its first 200 lines or 25KB.
  - Toggle with `/memory` or `autoMemoryEnabled`.
  - Subagents don't receive these notes.
- ✅ **Size.** Keep each CLAUDE.md under 200 lines. Block-level HTML comments are stripped before Claude sees them, so they cost nothing.
- ✅ **After `/compact`,** the root CLAUDE.md is re-read from disk. Instructions given only in chat are lost. [#instructions-seem-lost-after-compact](https://code.claude.com/docs/en/memory#instructions-seem-lost-after-compact)
- ✅ **Debugging.** The `InstructionsLoaded` hook shows which rules loaded.

## Impact on design
- **What goes where in a project:**
  - `CLAUDE.md` holds stack, commands and must-know rules (under 100 lines, since it's copied into every subagent).
  - `.claude/rules/*.md` with `paths` holds per-area conventions.
  - `.claude/agents/` holds the role agents.
  - Agent memory goes in `.claude/agent-memory/`, which is in git.
  - Session handoff goes in a short state file.
  - Personal auto memory stays machine-local and is never the only copy of project knowledge.
- **`prompt-engineer`'s output targets:** project CLAUDE.md, rules files and agent prompts. Its own guidance: short, imperative, no duplication between those layers.
- **Instructions that must survive `/compact`** go in files, never only in chat.

## Commands you'll use
- `/memory` opens CLAUDE.md files and auto memory, and toggles auto memory.
- `/init` drafts a CLAUDE.md from the codebase. `start` may reuse it instead of rebuilding that logic.
- `#` at the start of a message ❓ (older shortcut for saving a memory). Not verified in this pass, so don't rely on it.

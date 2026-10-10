# 01 — Best practices (third-party guide)

Source: ClaudeFast blog post "Claude Code Best Practices: 5 Techniques…", pasted 2026-10-08.
Not official Anthropic docs. The post ends with a product pitch. Only claims checked against the live docs are kept.

## Facts we use
- ⚠️ **Commands → skills.** The guide puts reusable workflows in `.claude/commands/*.md`. The docs say commands were merged into skills. That path still works, but a skill (`<dir>/SKILL.md`) is recommended because it adds supporting files and invocation control. [skills](https://code.claude.com/docs/en/skills)
- ⚠️ **Memory exists.** The guide says there's "no memory between conversations". The docs describe auto memory in `~/.claude/projects/<project>/memory/`. The first 200 lines or 25KB of its `MEMORY.md` index load each session. Toggle with `/memory` or `autoMemoryEnabled`. [memory](https://code.claude.com/docs/en/memory)
- ✅ **Keep CLAUDE.md lean.** The docs recommend under 200 lines per file.
  - `@path` imports work, but they do **not** save context.
  - Real on-demand loading comes from `.claude/rules/*.md` with `paths:` frontmatter, from subdirectory CLAUDE.md files, and from skills.
  - [memory](https://code.claude.com/docs/en/memory)
- ✅ **Skills are lazy.** Only name and description stay in context. The listing budget is 1% of the window, and each description is capped at 1,536 chars.
  - Overflow drops the least-invoked skills first.
  - `disable-model-invocation: true` makes a skill manual-only.
  - Skills support `paths` globs.
  - [skills](https://code.claude.com/docs/en/skills)
- ✅ **Plan, then execute in a fresh context.** The docs recommend Explore → Plan → Implement → Commit. Use plan mode for planning and `/clear` between tasks. For big features, write the spec in one session and implement it in a new one. Skip planning for small, clear changes. [best-practices](https://code.claude.com/docs/en/best-practices)
- ❓ "PRD-first" and "system evolution" are workflow habits, not platform facts. Nothing to verify.

## Impact on design
- No `commands/` dirs anywhere. All workflows are skills, and side-effect ones get `disable-model-invocation: true`.
- Project template: lean CLAUDE.md (<200 lines) plus `.claude/rules/` with `paths:` for per-project conventions. Phase 2 decides the split between stack-plugin skills and rules.
- 📌 parking_lot: a manual `plan`/`execute` skill pair. Only if the bundled plan mode proves insufficient (YAGNI).

## Commands you'll use
- `Shift+Tab` cycles permission modes, including plan mode.
- `/clear` resets the context between planning and implementation.
- `/memory` shows and edits CLAUDE.md files and auto memory.

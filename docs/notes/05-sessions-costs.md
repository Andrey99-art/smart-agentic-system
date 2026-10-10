# 05 — Sessions, caching, effort

Source: live docs, fetched 2026-10-09. [prompt-caching](https://code.claude.com/docs/en/prompt-caching), [sessions](https://code.claude.com/docs/en/sessions), [costs](https://code.claude.com/docs/en/costs), [model-config](https://code.claude.com/docs/en/model-config)

## Facts we use
- ✅ **Cache TTL.** On a subscription, the main conversation gets 1 h within plan usage. Otherwise it's 5 min, and `promptCacheTtl: "1h"` can change that. [#cache-lifetime](https://code.claude.com/docs/en/prompt-caching#cache-lifetime)
- ✅ **What breaks the cache:**
  - switching model, changing effort, turning on fast mode;
  - changes to MCP tools when they aren't deferred;
  - `/compact`;
  - upgrading Claude Code.
  - [#actions-that-invalidate-the-cache](https://code.claude.com/docs/en/prompt-caching#actions-that-invalidate-the-cache)
- ✅ **What doesn't break it:** editing files, switching permission mode, skills, `/rewind`. CLAUDE.md edits apply only after `/clear`, `/compact` or a restart.
- ✅ **Resuming.** `claude --continue` (latest session) and `--resume` (pick one) reuse the cache if you return within the TTL.
  - After about an hour idle with more than 100k tokens, Pro/Max offers "resume from summary". That runs `/compact`, so the full history is reprocessed once.
  - [sessions#resume-from-a-summary](https://code.claude.com/docs/en/sessions#resume-from-a-summary)
- ✅ **Compact vs clear.** `/clear` is free but drops the context. `/compact` is expensive when the cache is cold. `/rename` before `/clear` keeps the old session findable with `/resume`. [costs#reduce-token-usage](https://code.claude.com/docs/en/costs#reduce-token-usage)
- ✅ **Effort.**
  - Set it per session with `/effort low|medium|high|xhigh|max|auto`.
  - The default comes from the `effortLevel` setting (low to xhigh).
  - Frontmatter `effort` on an agent or skill **overrides** your session choice.
  - [model-config#adjust-effort-level](https://code.claude.com/docs/en/model-config#adjust-effort-level)

## Impact on design
- **Returning to a project:**
  - Within an hour, run `claude --continue`; the cache is still warm.
  - After a long break, start fresh with `/start`, which reads a short state file kept in the project. That's cheaper than reprocessing a 100k-token history.
- **State file:** `start` and the agents keep a short handoff file, about 1 page (name decided in Phase 2), updated at task end. That file is the continuity, not the chat history.
- **Your effort choice wins.** Agents and skills **don't set `effort`**, so they inherit yours. Exceptions need a stated reason.
- **Don't change model or effort mid-task;** both break the cache. Pick them at session start.

## Commands you'll use
- `claude --continue` resumes the last session in this folder; the cache is warm if under 1 h.
- `/effort high` sets reasoning depth for this session; agents follow it.
- `/rename <name>` then `/clear` starts fresh but keeps the old session for `/resume`.

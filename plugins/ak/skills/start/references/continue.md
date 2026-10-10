# Continue flow — resume work cheaply

Goal: get from "session opened" to "next step agreed" in as few tokens as possible. STATE.md is the memory; do not re-explore the repo.

## 1. Read the handoff
- Read `STATE.md` in full (it is short by design).
- Changes since the last handoff:
  - `git log --oneline "$(git log -1 --format=%H -- STATE.md)"..HEAD` (if STATE.md was never committed: `git log --oneline -10`);
  - `git status --short`.

## 2. Check that the setup still fits (cheap, read-only)
- Agents named in CLAUDE.md ↔ files in `.claude/agents/`: report any missing or extra ones.
- If a manifest (`pyproject.toml`, `package.json`, `Cargo.toml`, `build.gradle*`) changed since the handoff, CLAUDE.md commands may be stale: say so.
- Uncommitted changes left from the last session: put them at the top of the plan, and ask whether to review, commit or continue them.

## 3. Refresh prompts only when needed
Offer a `ak:prompt-engineer` refresh (never run it unasked) only if:
- the next step needs a role with no agent;
- the stack or commands changed (step 2); or
- the user asks.

The refresh follows init steps 3–4: one delegation, then approval of each changed file as a diff. New agents again need the user's approval and a restart.

## 4. Agree the next step
- The user already chose it in SKILL.md's first question: restate it in one line and give a 3–5 line plan; wait for "ok".
- If steps 1–2 show the choice is already done or blocked, say so in one line and offer the next "Next" item instead.
- Cost hint, once, only if STATE.md "Updated" is less than an hour old: "Next time, `claude --continue` reuses the warm cache and is cheaper than a fresh start."

## 5. Finish
End with the three-line summary from SKILL.md. Do not start coding before the user agrees to the plan.

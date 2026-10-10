# STATE

<!-- At most 60 lines. Written by /ak:handoff and read by /ak:start. Older detail lives in git history. -->
Updated: 2026-10-10 14:42

## Goal
Maintain the `andrey-kit` marketplace and its `ak` plugin; published at github.com/Andrey99-art/smart-agentic-system (GitHub `main` = local `public` branch).

## Done (latest first, at most 8)
- Feedback and releases: `/ak:feedback` + GitHub issue form (ak 0.8.0, c6e9066); `/publish` project command, noreply snapshots via `git commit-tree` (0cbfc55, fix 9fae19a).
- Published: orphan `public` branch with noreply author; private history stays on local `main`.
- Publication prep, ak 0.7.0 (b31022f): Apache-2.0, generic wording + editable Profile block, `AK_REVIEW_GATE`, trimmed inventory.
- ak 0.6.0 (c3b2cb2): size-budget test, agent memory `(seen: N)` → promotion via `/inbox`, handoff suggests retro.
- README (c171d26); CLAUDE.md slimmed to a maintainer guide, original in `docs/build-prompt.md` (c876fa2).
- Plugin renamed `ak`; `/ak:commit`, `/ak:learn`, project `/inbox` (0.4–0.5.1).
- Bash sandbox at user scope (`autoAllowBashIfSandboxed: false`, `.env` unreadable, podman excluded); dynamic stack conventions (Django guide, `format_on_edit`).
- Core installed at user scope and verified in VS Code; 46 tests pass.

## Next
1. Ship pending commits: `git fetch origin && git log --oneline origin/main..public`; then run `/publish` here (main has 6d788f5 not yet on `public`) and `git push origin public:main`.
2. First real project: on a Django repo branch, `/ak:start` → work → `/ak:commit` → `/ak:handoff` → `/ak:retro`; then `/inbox` here.
3. Optional README "Limits" line: git config changes (`git remote add`, `git config`) fail inside the sandbox by design.

## Open (blockers, questions, known bugs)
- `ak:engineering` triggering is unverified (plugin evals need API credits); watch it in real use.
- Optional: set this repo's `user.email` to the noreply address (writes `.git/config`, so it runs outside the sandbox).
- GitHub label `feedback` may need creating.
- "Uncommitted" `??` entries (`.bashrc`, `.mcp.json`, `.claude/hooks`, …) are sandbox placeholders, not real files.
- Android, Tauri and ESP32 guides: just in time, at the first real project in each stack.

## Decisions (why, at most 8)
- Full log: `docs/decisions.md`. This session added:
  - dynamic per-project conventions instead of stack plugins;
  - sandbox without auto-approve;
  - the `ak` rename;
  - learning by distillation within size budgets;
  - Apache-2.0 with noreply public snapshots;
  - opt-in feedback, no telemetry.

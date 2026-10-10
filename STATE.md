# STATE

<!-- At most 60 lines. Written by /ak:handoff and read by /ak:start. Older detail lives in git history. -->
Updated: 2026-10-10 12:00

## Goal
Build Andrey's personal Claude Code system: the `andrey-kit` marketplace with `ak` plus per-stack plugins.

## Done (latest first, at most 8)
- Build complete: README (c171d26); CLAUDE.md slimmed into a 52-line maintainer guide, original kept in docs/build-prompt.md (c876fa2); ak 0.5.1.
- Plugin renamed to `ak` (0.4.0); commands `/ak:commit`, `/ak:learn` and project `/inbox` added (0.5.0).
- Bash sandbox on at user scope: Balanced prompts unchanged, `.env` and keys unreadable from shell, podman excluded; verified headless.
- Dynamic stack support (ak 0.3.0, 959f3b0): Django guide (uv default), format_on_edit hook; other guides just in time.
- Self-hosting: this repo has `.claude/settings.json` (Balanced) and this STATE.md.
- Core rolled out at user scope (8a87542); verified in VS Code (/hooks, /ak:* commands). Synced andrey-engineering turned off via skillOverrides.
- ak 0.2.0: four inbox lessons from the first project applied (9445e65).
- Commands start/handoff/retro verified interactively on a Django fixture; agents code-reviewer and prompt-engineer verified headless.
- Hooks: guard, secret_scan, agent_write_guard, review_gate, session_context; 38 unit tests pass.
- Docs notes 00–08, architecture (approved), decisions log.

## Next
1. Real trial: `/ak:start` on one of Andrey's Django repos, on a branch he creates; then `/ak:retro` there.
2. Android, Tauri and ESP32 guides: just in time, at the first real project in each stack (decision 2026-10-10).

## Open (blockers, questions, known bugs)
- `engineering` skill triggering is unverified (plugin evals need API credits); watch it in real use.

## Decisions (why, at most 8)
- Full log: `docs/decisions.md`. Key: Balanced autonomy; roles derived per project; read-only agents use memory, enforced by agent_write_guard; reviewer reports and the main thread fixes; core rolled out before stacks.

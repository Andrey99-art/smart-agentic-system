# Review gate re-blocks on every fix round when the reviewer runs in the background

Target: plugins/andrey-core/scripts/review_gate.py

## Evidence
Project `shop`, 2026-10-10: the Stop hook blocked 4 times on `.claude/settings.json` and `.gitignore` in one session. Rounds 2 and 3 found real critical holes; round 4 followed a change that only added the reviewer's verbatim suggestions, and the main session had to declare it trivial to stop.
State files in `~/.claude/plugins/data/andrey-core-inline/review-gate/` are still in the old single-hash format (`{"reviewed": "<hash>"}`), so the version running during the session was the old one; that likely explains why the unchanged `.gitignore` was re-listed. The current per-file version fixes that part.

## Root cause
Docstring: "On the follow-up stop (stop_hook_active) it records the post-fix state silently, so fixes are not re-reviewed and the gate never loops." With a background reviewer (Agent runs async), the follow-up stop happens right after the agent is launched, before any fix. The fixes arrive in a later turn (task notification), whose stop has `stop_hook_active` false, so every fix round is a new block. Nothing bounds the number of rounds.

## Fix
- Track blocks per file per `session_id` (hook input) in the state file, e.g. `{"reviewed": {...}, "blocks": {"<session_id>": {"<path>": n}}}`.
- Do not list a file that already caused 3 blocks in this session (silently accept it). Cap 3, not 2: rounds 2–3 here found critical issues.
- Correct the docstring: the `stop_hook_active` save only prevents a loop when the review and fixes finish in the same turn.
- Keep the old-format fallback in `load()`.

## Verify
Unit test: same session_id, four consecutive stops with `stop_hook_active=false`, each with a changed `a.py` → stops 1–3 print a block, stop 4 prints nothing and exits 0. A new session_id blocks again. Run the existing hook tests.

## Outcome (2026-10-10)
Accepted with a simpler root fix: code-reviewer background: false (same-turn review and fixes), plus the per-session cap of 3 as a backstop; tests added. andrey-core 0.2.0.

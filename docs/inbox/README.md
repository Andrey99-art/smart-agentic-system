# Inbox — improvement proposals from projects

`/ak:retro` files general lessons here, one file per lesson: `YYYY-MM-DD-<project>-<slug>.md` with **Evidence → Root cause → Fix → Verify** and a `Target:` path inside `plugins/`.

`/inbox` also proposes promoting agent-memory patterns (`seen: 3` or more, in `~/.claude/agent-memory/ak-*`) into permanent rules. Every change must fit the size budgets in `plugins/ak/tests/test_budgets.py`.

Processing (in this repo, by the maintainer):
1. Read the proposal and check its evidence. Reject it if it is a one-off, or if it is already covered.
2. Apply the fix in a branch. Run the hook tests, `claude plugin validate --strict`, and the evals of any changed skill.
3. Bump the plugin `version`, add a CHANGELOG line, and commit.
4. Move the processed proposal to `docs/inbox/done/` (accepted) or `docs/inbox/rejected/` (with a one-line reason).

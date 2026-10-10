# Skill injection lines can abort a skill silently; nothing checks them

Target: plugins/ak/tests/test_skill_injections.py (new)

## Evidence
- `/ak:start` aborted with no output: its injection line `for f in …; do [ -e "$f" ] …` failed the permission pre-check ("Part of this command (a variable) cannot be checked in advance"). Fixed in 3985278.
- `/ak:retro` first shipped an injection line that read a path outside the project, which risks the same silent abort. It was removed before the skill was used (e750a8b).

## Root cause
The rule ("injection lines: no shell variables, no loops, end with `; true`") exists only as text in CLAUDE.md's gotchas. No test enforces it, so every new skill can repeat the mistake.

## Fix
Add `plugins/ak/tests/test_skill_injections.py`. For every `` !`cmd` `` in `plugins/ak/skills/*/SKILL.md` (and `.claude/skills/*/SKILL.md`), assert:
- after removing the substituted placeholders `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_SKILL_DIR}`, the command contains no `$`;
- it contains no `for ` or `while ` loop;
- it ends with `true` (so a non-zero exit cannot abort the skill).

## Verify
The test passes on the current skills. Planting `` !`ls $f; true` `` in a copy makes it fail. Then run the full suite.

## Outcome (2026-10-10)
Accepted as proposed. The test also flagged three existing lines without a trailing `true` (start: pwd, STATE.md check; handoff: date); they were fixed instead of weakening the rule. 50 tests pass. ak 0.8.1.

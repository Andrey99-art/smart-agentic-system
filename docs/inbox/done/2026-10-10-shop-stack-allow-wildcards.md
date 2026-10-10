# Stack-allow wildcards let "check" commands read secrets and write files

Target: plugins/andrey-core/templates/project/stack-allow.json, plugins/andrey-core/templates/project/settings.json

## Evidence
Project `shop` (Django fixture), init on 2026-10-10. Three code-reviewer rounds on the generated `.claude/settings.json` each reproduced a bypass (ruff 0.14.14, pytest 8.3.5):
- `Bash(ruff check *)`: `ruff check .env` printed `SECRET_KEY=…` (Read deny rules do not cover Bash). `--fix`, `--unsafe-fixes`, `--add-noqa`, `--config 'fix = true'`, `-o <file>` rewrote or overwrote files.
- `Bash(pytest *)`: `--basetemp=<dir>` wiped the directory; `--junitxml=<file>` overwrote a file.
- Even with exact allows (`ruff check`, `pytest -q`), `acceptEdits` lets the agent write `ruff.toml` (`extend-include = [".env"]`, `fix = true`) or `pytest.ini` (`addopts = --basetemp=<dir>`) that the exact command then auto-loads.
Flag-blocklist ask rules were tried first and failed: each review found new flags.

## Root cause
`stack-allow.json` assumes `<tool> check *` is read-only. Wildcards allow any flag, and tool config files are editable without a prompt.

## Fix
1. `stack-allow.json` django list → exact forms only:
   ```json
   "django": [
     "Bash(ruff check)",
     "Bash(ruff check .)",
     "Bash(pytest)",
     "Bash(pytest -q)",
     "Bash(python manage.py check)",
     "Bash(python manage.py makemigrations --check --dry-run)"
   ]
   ```
   Update `_about`: "Exact commands only, no `*`: flags and paths of lint/test tools can write files or print secrets."
2. `settings.json` template `ask` += `Edit(**/ruff.toml)`, `Edit(**/.ruff.toml)`, `Edit(**/pyproject.toml)`, `Edit(**/pytest.ini)`, `Edit(**/setup.cfg)`, `Edit(**/tox.ini)` (or make this per-stack alongside stack-allow).
3. Review the tauri and esp32 lists the same way (`npm run lint *`, `npx tsc --noEmit *`, `cargo check *`, `cargo build *`); not verified in this session.
4. Agent done-checks drafted by prompt-engineer must use exactly the allowed forms (here they did: `ruff check .`, `pytest -q`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`).

## Verify
Generate settings via `/andrey-core:start init` on a Django fixture, then re-run the reproductions above in a sandbox: each must prompt (not auto-run), and editing any listed config file must prompt.

## Outcome (2026-10-10)
Accepted with changes: exact allow-lists for all stacks (fix 1, 3). Rejected fix 2 (config-file ask rules): partial, false assurance; decided 2026-10-10. The real fix is the Phase 6 sandbox, now including filesystem.denyRead for .env. andrey-core 0.2.0.

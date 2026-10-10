# gitignore-additions has no per-stack entries

Target: plugins/andrey-core/templates/project/gitignore-additions, plugins/andrey-core/skills/start/references/init.md (§5)

## Evidence
Project `shop` (Django fixture), 2026-10-10: the code-reviewer flagged that the generated `.gitignore` did not ignore `__pycache__/`, `*.pyc` or `db.sqlite3`. STATE.md assumes local SQLite, which holds sessions and admin password hashes; one `git add -A` would commit it. Running ruff/pytest created `__pycache__` that nothing ignored. (`.pytest_cache`, `.ruff_cache`, `.venv` write their own `*` .gitignore, so they are optional.)

## Root cause
`gitignore-additions` covers only secrets and Claude-local files; init has no stack-specific ignore step.

## Fix
Add stack blocks to the template and have init §5 append the block for the detected stack:
```
# stack: django
__pycache__/
*.py[cod]
db.sqlite3
media/
```
(Equivalent blocks for tauri/esp32, e.g. `target/`, `node_modules/`, `dist/`, to be decided by the maintainer.)
init.md §5, `.gitignore` bullet: "append the missing lines from `Templates/gitignore-additions`: the common block plus the block for the detected stack."

## Verify
Run init on a Django fixture, run `pytest -q` and create `db.sqlite3`, then `git status --porcelain` shows neither.

## Outcome (2026-10-10)
Accepted: per-stack blocks (django, tauri, esp32, android); init appends the detected block. andrey-core 0.2.0.

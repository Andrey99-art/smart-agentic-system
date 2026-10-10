# Stack guide: Django

General knowledge for prompt-engineer. **The repo's own patterns win**: record what the code actually does; use this guide only to know what to look for and to fill gaps. Versions come from the manifests, never from this file.

## Read first
`manage.py` (settings module), the settings file(s) (`INSTALLED_APPS`, `DATABASES`, `TEMPLATES`), `requirements*.txt` or `pyproject.toml`, `pytest.ini` / `[tool.pytest.ini_options]` / `conftest.py`, and one example each of a model, a view, a template and a test.

## Package manager: uv by default (edit this section to prefer another tool)
- **New project, or `uv.lock` present:** use uv.
  - Create: `uv init --app`, then `uv add django`.
  - Add a dependency: `uv add <pkg>`; dev tools: `uv add --dev pytest-django ruff`.
  - Install from the lock: `uv sync`.
  - Run anything: `uv run <cmd>` (e.g. `uv run python manage.py runserver`).
  - Never `pip install` into a uv project.
- **Repo uses something else** (`poetry.lock`, `Pipfile.lock`, or only `requirements*.txt` with pip): follow the repo; `/start` asks the owner once whether to switch to uv, and records the answer in CLAUDE.md.
- Installing packages changes the environment, so `uv add` / `uv sync` always ask (not in the allow-list).

## Conventions to detect (write a rule only for what the repo really has)
- **Layout:** where apps live; settings split (`base/dev/prod`) or a single file; template and static locations.
- **Models:** money as `DecimalField` or integer cents; timestamp fields; `__str__`; `Meta.ordering`; `related_name` style.
- **Views:** function-based, class-based, or DRF ViewSets; URL names and namespaces.
- **Validation:** in forms, serializers or model `clean()`.
- **Templates:** base template and block names; i18n (`{% trans %}`) in use or not.
- **Tests:** pytest-django or `manage.py test`; factories (factory_boy) or fixtures; where tests live.
- **Config:** how env vars are read (`os.environ`, django-environ, python-decouple).

## Gotchas (include only those relevant to the repo)
- A model change needs `makemigrations`; commit the migration with the model change; never edit an applied migration; keep data migrations separate.
- N+1 queries: `select_related` / `prefetch_related` in list views and serializers.
- `QuerySet.update()` and bulk operations skip `save()` and signals.
- `USE_TZ = True`: use `django.utils.timezone.now()`, never naive `datetime.now()`.
- Several dependent writes go in `transaction.atomic()`; races need `select_for_update()`.
- Security: `SECRET_KEY` and credentials from the environment; `DEBUG = False` and `ALLOWED_HOSTS` outside development; CSRF stays on; `|safe` / `mark_safe` only for trusted content; raw SQL only with params; validate uploads (type, size).
- Media files are user data: never commit them; `collectstatic` belongs to deployment.

## Checks (must match the exact forms in `stack-allow.json`)
In a uv project prefix each with `uv run ` (e.g. `uv run pytest -q`); otherwise use them bare.
- `python manage.py check`
- `python manage.py makemigrations --check --dry-run`
- `pytest -q` (or `python manage.py test` when the repo has no pytest; that one asks)
- `ruff check .` (only if ruff is configured or listed)

## Formatter (for `.claude/format.json`)
- `ruff format` if ruff is in the manifests **and** it runs on this machine (`uv run ruff --version` in a uv project, else `ruff --version`): `{"**/*.py": ["uv", "run", "ruff", "format"]}` in a uv project, else `{"**/*.py": ["ruff", "format"]}`.
- Otherwise `black` under the same two conditions; otherwise no formatter.

## Rule files to propose (only for areas the repo has)
| File | `paths` |
|---|---|
| `.claude/rules/models.md` | `**/models.py`, `**/models/*.py`, `**/migrations/*.py` |
| `.claude/rules/views.md` | `**/views.py`, `**/views/*.py`, `**/urls.py`, `**/serializers.py`, `**/forms.py` |
| `.claude/rules/templates.md` | `**/templates/**/*.html`, `**/static/**` |
| `.claude/rules/tests.md` | `**/tests/**`, `**/test_*.py`, `**/conftest.py` |

## Never automate (agents hand these back)
`migrate` against any non-local database, `flush` / `sqlflush`, `createsuperuser` with real credentials, `check --deploy` with production settings, and deploys.

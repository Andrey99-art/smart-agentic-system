# Role guide — deriving project agents

Roles come from **this project's work**, not from a fixed list. The examples at the end are starting points only.

## 1. Derive roles from the work
1. List the work areas the project will need **repeatedly**: by directories, kind of task (UI, API, data, firmware, content, tests, infra) and risk.
2. An area becomes a role only if it has all three:
   - its own owned paths or tools;
   - its own definition of done (different checks);
   - repeated work, not a one-off task.
3. Merge areas that share paths and checks. Default **2–3 roles**; more than 4 needs a stated reason (each delegation is a cold-cache spawn).
4. Name roles by their work, in kebab-case: `api-backend`, `scraper`, `checkout-flow`, `firmware`, `test-writer`, `content-editor`.
5. Not roles: code review (`ak:code-reviewer` exists), prompt writing (`ak:prompt-engineer`), and one-off tasks (the main session does those).

## 2. Required parts of every agent file
- **Frontmatter:**
  - `name` (kebab-case);
  - `description` ≤ 250 chars saying **when to delegate**;
  - explicit `tools` (fewest that work);
  - `memory: project`;
  - **no** `model` or `effort`, so the user's session choice applies.
- **Body:**
  - Mission: 1–2 lines.
  - Owned paths: globs. It edits nothing outside them and hands such work back.
  - Process: the steps specific to this role.
  - Definition of done: exact verification commands taken from the project's manifests, or `TODO(owner)`.
  - Report: ≤ 10 lines back to the main session: what changed, checks run with results, open issues.
  - Boundaries: what it must hand back instead of doing (see §3).

## 3. Safety defaults by kind of work (always include the matching ones)
| Work touches | The agent must |
|---|---|
| Deploys, infra, CI, remote servers | Never deploy, push, or change remote resources. Prepare commands and hand them back. |
| Hardware, firmware, serial | Never flash or open serial ports. Build and check, then hand back the flash command. |
| Databases | Create migrations; never run destructive ones or touch non-local databases. |
| Secrets, credentials, external APIs | No secrets in code (use env). No live calls to paid or production APIs without the user's approval. |
| UI and visual design | Edit templates and styles freely; the rendered result is verified by the user, so say what to look at. |
| Git | Work on the current branch; commits only when the main session asks; never push or rewrite history. |

## 4. Examples (starting points, not a fixed list)
| Example role | Typical owned paths | Done-checks (if the project has them) |
|---|---|---|
| web-frontend | `templates/`, `static/`, `src/` (UI) | lint, type check, build |
| api-backend | app/service code, `tests/` | tests, migrations check |
| devops | `Dockerfile`/`Containerfile`, CI files, deploy scripts | config lint, dry-run builds (podman, rootless, `:Z` volumes) |
| ui-ux | design tokens, components, copy | lint; user checks rendering |
| android-app | `app/src/` | lint (builds run in Android Studio by the user) |
| firmware | `src/`, `.cargo/` | `cargo check`, `cargo clippy`; flashing by the user |
| desktop-app (Tauri) | `src-tauri/`, frontend `src/` | `cargo check`, frontend build |
| test-writer | `tests/` | the tests themselves pass and fail for the right reason |
| data-pipeline / scraper | pipeline or spider modules | sample run on fixture data |

# Code quality — per-language specifics

Read before writing or reviewing substantial code. The general bar is in SKILL.md §2; this file adds what each language needs. Any rule may be relaxed **deliberately, with a comment in the code saying why**.

## The Power-of-10 spirit, applied everywhere
1. Simple control flow: no clever recursion where a loop is clear; no goto-style jumps.
2. Bounded loops: every loop has an obvious upper bound or exit; retry loops have a max attempt count.
3. No unbounded growth: no allocation in hot paths or ISRs (embedded); caches have a size limit.
4. Short functions: ≤ ~60 lines, one responsibility, cognitive complexity ≤ 15.
5. Check assumptions: validate inputs and invariants with real checks (not debug-only asserts).
6. Smallest scope: declare data where it is used; no module-level mutable state without reason.
7. Check every return value and error; never ignore a `Result`, error code or exception.
8. Minimal metaprogramming: macros, decorators and reflection only when they remove real duplication.
9. Restrict indirection: no pointer/reference chains you cannot follow in one read.
10. All warnings on, treated as errors in CI; run the linter before calling a step done.

## Python (incl. Django)
- `assert` is **removed under `python -O`** — never use it for validation or security; raise explicit exceptions.
- No mutable default arguments (`def f(x=[])`); use `None` and create inside.
- Catch specific exceptions; if a broad `except Exception` is needed, log with context and re-raise or return a clear error.
- `subprocess.run([...])` with a list, never `shell=True` with user data; always `check=True` or inspect the return code; set `timeout`.
- Paths with `pathlib`; files with `with` blocks; text files with explicit `encoding`.
- Type hints on public functions; run `ruff check` (and `mypy` when the project uses it).
- Django: ORM or parameterised `raw()`/`cursor.execute(sql, params)`; never f-string SQL. Avoid N+1 queries with `select_related`/`prefetch_related`. Secrets and `SECRET_KEY` from the environment; `DEBUG = False` outside development; keep CSRF on; validate forms/serializers at the boundary.
- pandas/NumPy **view vs copy**: slicing a NumPy array returns a view (writes change the original); chained pandas indexing may write to a copy. Use `.loc[...] = ...` and explicit `.copy()` when you need independence.

## Rust (Tauri, ESP32)
- No `.unwrap()` / `.expect()` in non-test code, unless the invariant is proven and commented (`// invariant: …`). Propagate with `?`; define errors with `thiserror` (libraries) or use `anyhow` (binaries).
- `unsafe` only with a `// SAFETY:` comment stating the invariant that makes it sound.
- `cargo clippy -- -D warnings` and `cargo fmt --check` before a step is done.
- Integer arithmetic that may overflow: use `checked_*`/`saturating_*` where input is external.
- Embedded (`no_std`, esp-hal): no heap unless an allocator is configured on purpose; no panics or blocking in interrupt handlers; bounded busy-waits with timeouts; flashing and serial monitoring are always run by the user (see Profile).
- Tauri: validate every `#[tauri::command]` argument; grant the minimum capabilities/permissions; never expose filesystem or shell APIs broadly to the frontend.

## Kotlin / Jetpack Compose
- No `!!`; model absence with nullable types, `?.`, `?:`, or sealed results.
- Structured concurrency: `viewModelScope`/`lifecycleScope`, never `GlobalScope`; cancel-safe code; `Dispatchers.IO` for blocking work.
- Compose: hoist state, keep composables side-effect free, use `remember`/`rememberSaveable` correctly, stable keys in lazy lists.
- No secrets in `BuildConfig` or resources; no PII in logs.
- `ktlint`/`detekt` when the project has them. Build the way the Profile says (default: Android Studio, no CLI Gradle).

## TypeScript / React
- `strict` mode; no `any` (use `unknown` and narrow); no non-null `!` without a comment.
- No `dangerouslySetInnerHTML` with untrusted data; escape and validate at the boundary.
- `useEffect` with complete dependency arrays; derive state instead of syncing it.
- `eslint` + `tsc --noEmit` before calling a step done.

## C++
- RAII for every resource; no raw `new`/`delete`; prefer `std::unique_ptr`, containers, `std::span`.
- Bounds-checked access in non-hot code (`.at()`); compile with `-Wall -Wextra -Werror`; run sanitizers (`-fsanitize=address,undefined`) in tests.

## SQL
- Parameterised queries only. Name columns (no `SELECT *` in application code).
- Multi-statement changes in a transaction; migrations reversible where possible.
- Check query plans (`EXPLAIN`) for queries on large tables; add indexes deliberately.

## Shell and hook scripts
- bash: `set -euo pipefail`, quote every variable (including `"${CLAUDE_PLUGIN_ROOT}"`), `shellcheck`-clean.
- Or Python 3 stdlib only (hooks run outside any venv). Fail closed in guards: on unexpected input, block with a clear message.

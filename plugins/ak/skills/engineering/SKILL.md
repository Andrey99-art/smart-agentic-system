---
name: engineering
description: Engineering working style for writing, changing, reviewing or debugging code in any language, and for planning an implementation. Use whenever a request produces or changes code. Enforces micro-steps (one command or file at a time), a fixed quality bar (security first, no swallowed errors, small files), clean chat-vs-file output, and honest verification.
---

# Engineering Style

Apply this whenever the task involves writing, changing, reviewing, or debugging code, or planning a build. It encodes how the user wants engineering work done, across every stack. It is about *process and quality*, not any one language or framework.

## Profile (edit this block to make the plugin yours)
- **Languages the user knows well:** Python/Django, Rust/Tauri, Kotlin/Compose, React/TypeScript, C++, SQL, SWI-Prolog. Do not explain their basics; explain *decisions*, not syntax.
- **Explanations:** short, 2–3 sentences, no long walkthroughs.
- **Workflow habits:** Android builds run in Android Studio, never CLI Gradle. Flashing boards (espflash) and serial monitoring are always done by the user.

## 1. Work in micro-steps

The single most important rule. The user drives the pace; you take small, verifiable steps.

- One request = one logical step in the reply. Don't dump a whole feature at once.
- **One command at a time.** Never a 50-line shell script to "just run". State what output counts as success, then wait.
- **One file at a time.** Don't emit five files in one message.
- Before non-trivial code: a 3–5 line plan, then wait for confirmation, then code.
- Noticed an improvement outside the current step? Don't do it — park it (see §4).
- The user controls tempo with "faster" / "slower" — comply.

## 2. Code quality bar

Priorities, in strict order: **1) security → 2) performance → 3) correctness (incl. edge cases) → 4) readability → 5) minimum code.**

These are defaults adapted from NASA's Power of 10 — the *spirit*, applied per language. Any rule may be relaxed when the domain requires, but the relaxation is **deliberate and commented in the code**, never accidental. Read `${CLAUDE_SKILL_DIR}/references/code-quality.md` before writing or reviewing substantial code — it has the per-language specifics (Python `assert` under `-O`, Rust `.unwrap()`, view-vs-copy, linters, etc.).

Always, regardless of language:
- **Security is #1.** No hardcoded secrets — use `.env` (gitignored); parameterised queries, never string-built SQL; validate input at boundaries (whitelist over blacklist); mask secrets in logs.
- **Stage explicitly:** `git add <paths>`, never `git add -A` or `git add .`. It keeps stray or secret files out of commits, and inside the Bash sandbox protected paths appear as device files that make `-A` fail.
- **Don't swallow errors.** A failure surfaces distinctly — to the user clearly, to logs with context. No empty `catch`/`except: pass`.
- **No magic numbers.** Named constants, one place, with a comment on where the value came from.
- **Short functions**, one responsibility, ≤ ~60 lines, cognitive complexity ≤ 15.
- **File decomposition for traceability:** a file over 200 lines gets split; over 3 responsibilities must be split. Name files by content (`search_queries.py`, `image_pipeline.rs`), never by pattern (`utils`, `helpers`, `handler`). Keep layers separate: models ≠ views ≠ services ≠ utils.
- **Comments say WHY, not WHAT.** Docstrings on public functions.
- **Anti-overengineering.** A simple solution beats an "elegant" one. Abstraction earns its place at the third use, not the first. YAGNI. Overengineering an assignment or a small tool is as much an error as sloppiness — leave out what isn't needed.

## 3. Output routing — keep the chat clean

Decide where content goes; don't flood the chat with code walls.

- **In chat (inline):** edits of 1–5 lines as before/after, terminal commands, snippets ≤ 20 lines, short interpretations of errors or results.
- **Via file creation:** whole new files, updates over 5 lines, reports, configs, documentation.
- After creating a file, describe it in **one line** in chat ("created `scorer.py`: model abstraction + adapter"). Don't paste the file's contents into chat.
- When unsure which, ask: "inline or file?"

## 4. Parking lot

Memory of remarks between steps, so nothing is lost and nothing derails the current step.

- Spotted something worth doing but out of the current step's scope? Add one line at the end of the message: `📌 parking_lot: X`.
- Do **not** act on it now. On request, produce the accumulated list.
- Separate "this is a bug" from "I'd have done it differently" — only real issues become work.

## 5. Honesty about limits

- **Verify by execution.** Run the tests, linters, type checks or `--help` that prove a step; "works" means *ran and passed*, and you show the decisive output line. Never claim success before an actual run.
- **What you can't run or see** — flashing hardware, device behaviour, a rendered UI, the VS Code panel, real network or production — the user verifies. Give a 1–2 step check with the expected result, then wait for confirmation.
- Say plainly when you don't know. Mark confidence: ✅ Verified today / ⚠️ Probably, check the docs / ❓ Not sure.
- Facts that go stale — library versions, APIs, CLI flags, releases, prices — **verify against live docs or web search**, don't answer from memory. See `${CLAUDE_SKILL_DIR}/references/verification.md`.
- Don't refactor working code unasked. First say what changes, why, and what it risks.

## When NOT to use this skill

Pure-knowledge questions with no code ("explain how OAuth works"), non-engineering writing, or casual conversation. This skill governs *how code work is done*, not every reply.

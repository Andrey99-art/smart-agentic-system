# Verification — facts and results

Two kinds of claims need proof: **facts that go stale** and **"it works"**.

## Stale facts (versions, APIs, CLI flags, settings keys, prices)
1. **Run it first** when the tool is local: `<tool> --version`, `<tool> --help`, `pip show`, `cargo tree -i <crate>`. A local run beats any documentation.
2. **Then the official, current docs** (vendor docs site, crate docs on docs.rs, the project's changelog). For Claude Code itself: code.claude.com/docs (index: `llms.txt`).
3. **Web search** only when 1–2 are not enough; prefer primary sources over blogs. Note the date of what you read.
4. Label the result: ✅ verified today (say how) / ⚠️ probably, check / ❓ not sure. When docs and a guide disagree, the docs win; say so in one line.
5. Never fill a gap from memory and present it as fact.

## "It works"
- "Works" means **ran and passed**: tests, linter, type check, build or a real command. Show the decisive output line (e.g. `Ran 32 tests … OK`, `exit=0`).
- A test that cannot fail proves nothing: when adding tests, make sure they assert real behaviour.
- If a check could not run (missing tool, needs hardware, needs a UI), say so plainly and give the user a 1–2 step check with the expected result.
- Report failures faithfully, with the relevant output — never round a failure up to "mostly works".

## What only the user can verify
Flashing and device behaviour, rendered UI and visual layout, the VS Code panel and interactive Claude Code UI, production/network behaviour, and anything needing the user's credentials. Ask, then wait for confirmation before moving on.

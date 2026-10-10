# 00 — Inventory (2026-10-08)

Read-only snapshot taken before any plugin work, trimmed for publication to what explains later decisions. ✅ = ran it that day.

## Environment
- ✅ Claude Code `2.1.287`; `python3` 3.14, `git`, `jq` and `podman` present.
- ✅ `shellcheck` missing, so hooks were written in Python 3 stdlib (no bash linting needed).

## Starting point
- An existing personal engineering skill, synced from claude.ai, became the plugin's `engineering` skill. The skill linked to two reference files that did not exist, so they were rebuilt.
- An existing personal Bash guard hook (≈ 90 lines) was migrated into the plugin. Gaps found against the spec:
  - not covered: `git checkout -- .`, podman/docker prune and `volume rm`, `curl | sh`, `chmod -R 777`;
  - no secret scan before commits;
  - ⚠️ **fail-open**: unexpected input raised an exception (exit 1, non-blocking), so the call went through. Confirmed and fixed in the port: guards now exit 2 on any internal error.
- The user settings already had deny rules for destructive Bash and Read denies for secrets; Balanced (`acceptEdits`) was not yet set.

## Early answers that shaped the design
- Android builds run in Android Studio only, so there are no CLI Gradle builds.
- ESP32 flashing (`espflash`) always stays manual.
- The old guard is replaced by the plugin's guard (done in the rollout, after a backup).

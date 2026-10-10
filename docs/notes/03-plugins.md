# 03 — Plugins and marketplaces

Source: live docs, fetched 2026-10-08. Base: https://code.claude.com/docs/en/plugins/

## Facts we use
- ✅ **Manifest.** `.claude-plugin/plugin.json` needs only `name` (kebab-case). We add `version`, `description` and `author.name`.
  - Components live at the plugin root: `skills/`, `agents/`, `hooks/hooks.json`, `.mcp.json`, `bin/`, `settings.json`.
  - A plugin's `settings.json` applies only the keys `agent` and `subagentStatusLine`.
  - [manifest-reference#standard-layout](https://code.claude.com/docs/en/plugins/manifest-reference#standard-layout)
- ✅ **Marketplace.** `.claude-plugin/marketplace.json` needs `name`, `owner.name` and `plugins[]`. Each entry needs `name` and `source`, and `source: "./plugins/x"` must start with `./` with no `..`. [marketplace-reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-entries)
- ⚠️ **Reserved names.** CLAUDE.md lists `claude-`, `anthropic-` and `cc-plugin-`. The docs add the prefix `anthropics-` and the exact names `claude`, `anthropic`, `claude-code` and `claude-mods`. A whole-word `claude` elsewhere in a name only warns. Our `andrey-*` names are clean.
- ✅ **Local dev loop.** Plugins with relative paths in a local-path marketplace **load in place** and are not copied to the cache.
  - Edits apply in the next session or after `/reload-plugins`, with no version bump.
  - Copied plugins update only when `version` changes.
  - [loading#in-place-and-copied-plugins](https://code.claude.com/docs/en/plugins/loading#in-place-and-copied-plugins)
- ✅ **Install.** Run `claude plugin marketplace add <path>`, then `claude plugin install <plugin>@<marketplace>`. Auto-update is off for local marketplaces.
- ✅ **Per-project enable.** Put `"enabledPlugins": {"andrey-django@andrey-kit": true}` in the project's `.claude/settings.json`.
  - Precedence: local > project > user.
  - A relative-path plugin loads from a known marketplace without an install record.
  - [loading](https://code.claude.com/docs/en/plugins/loading#find-where-a-plugin-is-enabled)
- ✅ **Test.** `claude plugin validate <dir> --strict` exits 1 on any warning and also checks marketplaces. For quick trials, `claude --plugin-dir <dir>`.
- ✅ **Plugin agents ignore `permissionMode`, `hooks`, `mcpServers` and `initialPrompt`.**
  - Supported: `tools`, `disallowedTools`, `model`, `effort`, `skills`, `memory`, `maxTurns`, `isolation: worktree`, among others.
  - So agent safety comes from plugin-level hooks plus `tools` allow-lists.
  - [components](https://code.claude.com/docs/en/plugins/components#frontmatter-fields-in-plugin-agents)
- ✅ **Paths.** `${CLAUDE_PLUGIN_ROOT}` changes on every update, so treat it as read-only. `${CLAUDE_PLUGIN_DATA}` (`~/.claude/plugins/data/<id>/`) holds state. Neither is set inside Bash-tool commands.
- ✅ A top-level `bin/` blocks claude.ai/Cowork install. A plugin-root `CLAUDE.md` is not loaded.

## Impact on design
- Add the marketplace once at user scope, keep `andrey-core` enabled at user scope, and enable stack plugins per project in `.claude/settings.json`. This resolves the ⚠️ in CLAUDE.md.
- The dev loop needs no reinstall: edit, then `/reload-plugins`. The version is bumped only for releases (Phase 6).
- Agents get explicit `tools` lists, because `permissionMode` can't be set on plugin agents.
- No `bin/`; scripts live under `hooks/` or `scripts/`.

## Commands you'll use
- `claude plugin marketplace add ~/dev/agentic-system` registers the local marketplace once.
- `claude plugin validate plugins/andrey-core --strict` checks a plugin before committing.
- `/reload-plugins` picks up hook and agent edits in a running session.

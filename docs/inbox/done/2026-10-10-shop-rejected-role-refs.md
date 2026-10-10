# Rejecting a role leaves dangling references in accepted drafts

Target: plugins/andrey-core/skills/start/references/init.md (§4)

## Evidence
Project `shop`, init on 2026-10-10. Approval order was CLAUDE.md → agents. The user accepted CLAUDE.md and shop-backend, then rejected test-writer. The accepted files still named test-writer (CLAUDE.md "Agents", shop-backend "Excluded: tests … (test-writer)", web-frontend "hand back for test-writer"), so tests had no owner. Resolving it took an extra diff and question round (the user then kept test-writer).

## Root cause
§4 approves CLAUDE.md first and says nothing about cross-references when a role is rejected. Role drafts reference each other's owned paths by design.

## Fix
Replace the first lines of §4:
```
## 4. Approve each file
For every draft, in this order: each agent → rules → CLAUDE.md (CLAUDE.md lists the agents, so it comes last).
- If a role is rejected, remove its references from the remaining drafts and reassign its owned paths (usually to the closest remaining role); show those edits in the diffs that follow.
```

## Verify
Eval: run `/andrey-core:start init` on a fixture, reject one proposed role; afterwards `grep -r <rejected-role> CLAUDE.md .claude/` returns nothing and every owned path in the rejected draft appears in another agent's "Owned paths".

## Outcome (2026-10-10)
Accepted as proposed. andrey-core 0.2.0.

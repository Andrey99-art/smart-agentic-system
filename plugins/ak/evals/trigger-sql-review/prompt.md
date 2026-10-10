---
name: trigger-sql-review
tags: [trigger]
runs: 2
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Skill]
---

Review this migration before I run it on production:

```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL;
UPDATE users SET email_verified = false;
```

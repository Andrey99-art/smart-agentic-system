---
name: trigger-python-function
tags: [trigger]
runs: 2
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Skill]
---

Write a Python function that reads a CSV file and returns the rows whose `date` column is not a valid ISO-8601 date.

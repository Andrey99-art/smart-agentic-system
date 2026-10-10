---
name: trigger-rust-unwrap
tags: [trigger]
runs: 2
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Skill]
---

Refactor this so it stops panicking:

```rust
fn load(p: &str) -> Config {
    let s = std::fs::read_to_string(p).unwrap();
    toml::from_str(&s).unwrap()
}
```

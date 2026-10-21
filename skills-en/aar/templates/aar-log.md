# Review journal (aar skill)

One line per review, all projects. The line is written at step 8 of the `aar` skill, once and at
the very end of the review. The file is not loaded into context: steps 1, 5 and 6 grep it.

Line format:

```
YYYY-MM-DD | <project> | symptom in 5-7 words | found by: user|me | category | method: <name or "none"> | angle: <checks map code or "none"> | rung | link to the fix file
```

Example:

```
2026-01-15 | shop-api | "tests pass" without running e2e | found by: user | knew, but did not check | method: proof replaced by plausibility | angle: E | 1 | .claude/settings.json (hook e2e_before_done.py)
```

## Entries


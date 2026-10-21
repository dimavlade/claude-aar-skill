# Project checks map (aar skill, step 6)

A direction is the kind of question a check asks the project or Claude's conclusion. The direction
code is written in the `angle` field of the review journal. The "does not catch" column is the main
one: at step 6 of the review it is the one that most often answers "no".

Fill it in only with checks that the project actually has and runs. A direction that does not exist
is written as a row marked "**No check**", not skipped. A new row is added together with an
executable check and one real run of it.

## Directions

| Code | Direction | Where it runs | What it catches | What it does not catch |
|---|---|---|---|---|
| `U` | Unit tests | `<tests folder>`, `<command>` | | |
| `E` | End-to-end tests | | | |
| `R` | After deployment | | | |
| `D` | Data conclusions (analytics, database, ad accounts) | | | |
| `F` | Form of the response to the user | | | |
| `T` | Interface and documentation texts | | | |
| `I` | Claude's tooling (scripts, permissions, environment) | | | |

## When a direction is required

| What is affected | Required directions |
|---|---|
| Any code edit | `U E` - `<full run command>`, before the commit |
| Deployment | `R` |
| A data conclusion for the user | `D` |
| A reply to a request for a result | `F` |
| Text on screen or in documentation | `T` |

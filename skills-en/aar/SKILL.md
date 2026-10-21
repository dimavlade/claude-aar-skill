---
name: aar
description: >
  After-action review of a mistake in work I have already reported as done: what was missing at
  the moment of the work, whether it is a class or a one-off, which of my working assumptions
  produced it, and at which rung (a new kind of check, automation, a step in a skill, a rule,
  memory) it gets fixed so it does not recur. If the user found the mistake rather than me, the
  project's checks setup is reviewed as well. Use after a mistake is found in work already
  reported as done: a false claim ("tested", "works", "does not exist"), a wrong conclusion, a
  broken edit, a missed case, a defect in code, text or docs I delivered. Also when I write "I
  was wrong", "correction", "actually", "ошибся", "снимаю" about my own earlier answer. Not for
  new tasks or changed requirements.
---

# /aar - review after delivered work

The skill runs when a mistake turns up in something I have already delivered. The usual reaction
is to fix it quietly and apologize. The fix closes the specific case and changes nothing about the
reason it happened: two weeks later the same class of mistake arrives from a different file.

The protocol exists so that every mistake the user finds costs them only **once**.

The goal is not "perfect the first time" - that is unattainable. The goals are measurable, and
there are two:

1. **The same class of mistake does not happen twice.**
2. **A direction nobody was checking is checked after the review.**

Almost every "per-case" fix lacks the second goal: a test for this input, an item in the
instructions. Such a fix closes the class but does not answer where the class came from. And it
almost always comes from one thing: **an entire direction of checks in the project has never been
run even once**, and the mistake simply happened to be the first to come out of it.

Reply to the user in their language. The skill's terms below are in English; in the journal and
the report they go translated into the user's language.

## The three files the review rests on

| File | Default location | Purpose |
|---|---|---|
| **Journal** | `~/.claude/aar-log.md` - one for all projects | One line per review. Needed by steps 1, 5 and 6: to see a repeat, to prove a working method, to see a weak direction |
| **Project checks map** | `.claude/aar/checks-map.md` at the project root | Which kinds of checks the project has, what each one catches and does not catch, when each one is required. Needed by step 6 |
| **Run ledger** | `.claude/aar/runs/YYYY-MM-DD-<topic>.md` in the project | The course of this review, one line per step. Protects against context compaction in the middle of the review |

If the `CLAUDE_CONFIG_DIR` variable is set, the journal lives in that folder rather than in
`~/.claude`. If the project's or the user's `CLAUDE.md` names a different path for the journal or
the map, use that one.

**First run.** No journal - create it from `templates/aar-log.md` in this skill's folder. No checks
map - at step 6 create it from `templates/checks-map.md`: find out which checks the project actually
has (test folders, scripts in `package.json`, `Makefile`, `pyproject.toml`, CI in
`.github/workflows`, hooks in `.claude/settings.json`), and fill in rows with those only. Fill in
the "does not catch" column honestly: it is the most important one. A direction that does not exist
is written as a row marked "**No check**", not skipped.

The journal lives outside repositories and is not committed. The map and the ledgers are part of
the project; they are committed together with the fix if the project commits `.claude/`.

## Three levels of review

The review answers "why" three times, and these are three DIFFERENT questions. They must not be
merged: each has its own fix, and a fix at one level does not close another.

| Level | Question | Example | Fixed by |
|---|---|---|---|
| Case | What broke? | The test harness moved the user's cursor | An edit |
| Check | Why wasn't it caught? | There was no check of harnesses for side effects | A test, a hook, a direction in the checks map |
| **Working method** | **Why did I do it that way at all?** | **Someone else's call is taken by its name; how it works is not read** | **Turning the method into a machine action** |

**A meta-error is the third level: a defect in the working method, not in knowing a fact and not
in having a check.** "There was no check" is still tied to the subject - the cursor, the harness,
the framework. A real meta-error contains no subject at all.

Three signs to recognize it by:

1. **The wording does not name a domain.** "`mouseMove` in the test framework moves the real
   cursor" is a fact. "There was no cursor test" is a check. "A call's name is taken for its
   mechanics" is a method; neither the framework nor the cursor appears in that phrase.
2. **It has already repeated in unrelated domains.** The same method produces the conclusion "the
   process is not running" from a filter that could not have matched; a window capture that
   bypasses the compositor; choosing a tool by its field description instead of a trial call.
   Different domains, one method.
3. **A rule may have already existed - and failed to fire because of where its scope ended.** The
   rule "ask the tool itself" existed, but was read as "about other people's APIs" and was not
   carried over to my own framework. A meta-error often looks not like ignorance of a rule but like
   a silently narrowed scope of that rule.

What does NOT fix a meta-error: a test for this input (the test closed the cursor case, and a week
later the method fires in analytics) and a "be more careful" rule (pays rent in every request,
never fires).

## Two modes

**Mode 1, review** - steps 1-4 and 7-8. Always runs.

**Mode 2, meta** - the same steps plus step 5 "Working method", step 6 "Check direction" and rung
0 in the ladder. It is switched on by one sign:

> **The user found the mistake, not me.**

The sign is not about politeness or tone. It is about how the work is set up:

- the defect was found by me, by a test, by a reviewing agent - the checks system worked. Late and
  clumsily, but it **searched** and **found**. Fixed within mode 1;
- the defect was found by the user - so **nobody was looking** for it. Not a single test, direction
  or gate was pointed that way. This is a fact not about my attentiveness but about the checks map:
  there is a blank spot in it, and the user found it before we did.

So in mode 2 the question "why did I make a mistake" is secondary. The main question is: **why did
the mistake reach a person without meeting a single check on the way.**

"Found by the user" counts regardless of what they used - the program, reading my code, reading my
own report. And regardless of whether they called it a mistake or asked a neutral question.

## When to run

**The trigger is not a user complaint but a defect in what I have already delivered.** As soon as
it turns out that something delivered is wrong, the review starts on its own, without a reminder
and without being asked. Who found the mistake - the user, me during a check, or another agent -
**does not matter for starting the review**: the price is paid by whoever received the wrong
result.

For the **mode**, the same circumstance decides everything: the user found it - mode 2. One
circumstance, two different conclusions; they must not be confused.

What is delivered is **both words and work**. A false statement ("checked", "no effect", "this does
not exist") is only one of the two kinds. The second is **a defect in code, interface text,
documentation or a test that I wrote** and handed over as finished. For the user the difference
between "I said something untrue" and "I wrote it badly" is zero. This protocol has already failed
to fire because the trigger was narrowed to statements alone: I did not count an interface string
with a wrong verb as a "statement", and the review did not start.

The trigger is easiest to catch in my own text. If I write "clarification", "correction",
"actually", "I was wrong", "I made a mistake", "I withdraw the recommendation" about my own earlier
statement - the review has already started, and the next step is not "moving on" but step 1. This
trigger is enforced by the `Stop` hook `aar_trigger_gate.py` from the skill package, if it is
installed: a response that corrects my own delivered work without an `aar` call in the same turn is
sent back once.

**A neutral question is also a trigger.** "Is this your run?", "are you sure?", "where did you get
that?" do not look like complaints, but a wrong answer to them is the same delivered wrong work.
Judge by my own answer, not by the tone of the question.

Run it even for a small mistake: the classification at step 4 will itself filter out what does not
need recording, and that is cheaper than guessing in advance which mistake matters.

Do not run:

- when the user sets a new task or changes requirements - that is not a mistake but a
  clarification;
- when the mistake **did not reach the user**: I found and fixed it inside my own work, and no false
  statement went out. The key here is "did not reach", not "found it myself";
- when I warned about a risk, the user made a decision, and the risk materialized - the decision
  was theirs, there is nothing to review.

## Order

The review happens **after** the cause of the mistake is understood and **before** the final
report. First I fix what was found in the project's usual way (edit, tests, commit; a wrong
conclusion - by correcting the report or the plan file), then I review myself. The other way round
does not work: while the cause is not found, the review turns into guesses about guesses.

**The course of the review is kept in the run ledger** (`templates/run-ledger.md`) - one line for
each of steps 1-8, with a verdict and evidence, written right after the step. The journal line at
step 8 is a summary, not a record of the course: it is written once and at the very end, so it
does not protect against context compaction in the middle of the review. This applies especially
to steps 5 and 6: the named assumption, the direction code, the answer of the "when required" table
and the result of the journal cross-check are finished findings that vanish if not written down.

## Step 1. Has this happened before

First thing - the journal. Grep it for keywords of the symptom. If the user has other review
journals (an archive, another project's journal, a path named in `CLAUDE.md`), grep them too: my
working methods are common to all projects, and a class reviewed there counts as already reviewed.
If the earlier fix is a hook or a rule of another project, check whether it is in effect in this
one (`.claude/settings.json`, the project's `CLAUDE.md`). If it is not - that is the reason for the
repeat.

If something similar has already been reviewed - that is the main result of the review, more
important than the mistake itself. It means the fix adopted back then did not work, and **that fix**
is what needs fixing, rather than writing a second identical rule next to it. The typical cause:
rung 4 (memory) was chosen where rung 1 (automation) was needed.

## Step 2. Facts, without interpretation

Three lines:

1. **What I delivered** - the statement or the edit, verbatim.
2. **What turned out to be true** - what refuted it.
3. **Where exactly** - file and line, message, report.

At this point these are three lines of facts, not a story of how it happened.

## Step 3. What was missing

Exactly one category out of eight. Not "a bit of everything" - the choice of category determines
the rung at step 7, and a smeared answer produces a useless fix.

The first five are about me: I could have done otherwise with what was at hand.

| Category | Sign |
|---|---|
| **Did not know a fact** | The information was in the repository or in the history; I did not read it |
| **Knew, but did not check** | A check was available (test, screenshot, grep, database query) and was not done |
| **No step in the instructions** | I acted according to a skill or a plan, and it does not require such a check |
| **Guessed a fork silently** | There were two readings; I chose one, did not ask and did not state the assumption |
| **Drift** | I knew the rule and followed it earlier in this same session, then stopped |

The last three are about how the work is set up: nothing that catches this mistake was at hand.

| Category | Sign |
|---|---|
| **No such kind of check** | No direction in the checks map asks the project or the conclusion such a question. There was nothing to check with |
| **The check is not required to run** | The direction is in the map, but the "when required" table does not require it for this edit. Whether it ran depended on whether I remembered |
| **No tool** | The direction is described but can only be executed by hand (for example, by eye in a browser), so in practice it is not done |

**Selection rule in mode 2: if both a personal and an organizational category fit, take the
organizational one.** The reason is arithmetic: fixes for personal categories lead to rungs 3-4,
where everything rests on my memory, and mistakes of the same kind come again. An organizational
category leads to rungs 0-2, where nothing rests on anything.

Separately, check for the trap: **confidence without grounds.** If, when delivering the work, I
wrote "checked", "works", "everything is covered", and the basis was reasoning rather than command
output - that is a separate and more serious mistake than the defect itself. Mark it explicitly.

## Step 4. Class or one-off

The question is put like this: **can you describe a condition under which this mistake will repeat
in another file?**

- The condition can be stated - it is a class, move on.
- It cannot - it is a one-off. Fix it and **record nothing.** A record about a one-off is pure harm:
  it pays rent in every request and catches nothing.

The condition must be stated in a checkable form. "Be more careful with settings" is not a
condition. "Any setting that is written to the database but not read back when applied" is a
condition.

**In mode 2 the conclusion "one-off" requires separate grounds.** A mistake that reached the user
went through the whole chain of checks and caught on nothing - that in itself points to a hole in
the chain, not to bad luck. Before closing a case as a one-off, go through steps 5 and 6: often the
condition is stated not in terms of code ("the same setting in another file") but in terms of a
direction ("nobody checks settings by reading them back at all").

## Step 5. Working method

**Mode 2 only.** In mode 1 the step is skipped.

Here we answer not "what was missing to catch it" (that is step 6) but **which of my working
assumptions produced the mistake**. Two questions in a row.

1. **Name the assumption in one phrase without mentioning the domain.** Not "did not know that
   `mouseMove` moves the cursor" but "the mechanics of someone else's call are taken from its
   name". If the phrase cannot be written without words from the subject domain - it is still a
   case, not a method, and the step closes with the conclusion "method not named".
2. **Prove the repeat.** Grep the journal (and the user's other journals) by the method field
   (`grep -i "method:" ~/.claude/aar-log.md`) and name at least one earlier case **from a different
   domain**. The link to the earlier entry is the proof; without it the method is not declared.

**A limiter without which the concept blurs: a method is declared only with a proven repeat across
different domains.** One mistake is still a case. A review where every miss is raised to the level
of a working method fills the journal with abstractions that catch nothing.

Known methods that have already cost delivered work that turned out unusable. The list grows
through this step: a new method is added as a line in the journal, and once it is proven by a
repeat - to this table as well.

| Method | What it looks like | Typical cases |
|---|---|---|
| Mechanics taken from the name | Someone else's call is used without reading how it works or making a trial call | a test framework function moves the real cursor; the `CommandLine` field, empty without permissions; a window capture that bypasses the compositor |
| Proof replaced by plausibility | "You can see it from the code", "logic suggests" instead of command output | "checked" in a review without running anything |
| Scope of the conclusion widened silently | Measured on a part, concluded about the whole | "no violations left" based on 4 rows out of 29 |
| The client's instruction replaced by a recommendation | The user named a form, a sample or a place, and a spec, an agent or convenience suggested something else - and the other thing was chosen without asking | my own form of an element instead of the sample; a separate branch instead of the working one; a limit from a template instead of the one named |
| The detector's other end not checked | "Not found" accepted without checking that the detector can find anything at all | a filter that cannot match; measuring an event that never arrives |
| A quantity measured by a proxy | The check takes an available quantity instead of the one the result depends on | topic coverage measured by a palette detector; a record's age relative to build time instead of publication time |
| The work's result stays in the conversation, not in a file | An agreement, a finding or a decision exists only in the chat; after context compaction, the work proceeds from a file that does not have them | reconciliation findings did not make it into the plan; a decision about a new kind of work did not make it into the skill |
| My own earlier text taken as an observation | A statement from my own plan, memory or report is retold as fact without a fresh check | a number from memory instead of a fresh query; an event's composition taken from my own month-old plan |

Fixing a method is rung 1 in the ladder, not 3 or 4: the method is turned into a machine action (a
registry, a hook, a mandatory evidence line in the ledger) or into a checkable condition. Writing
"from now on, read the primary source" and stopping there means fixing nothing.

## Step 6. Check direction

**Mode 2 only.** In mode 1 the step is skipped.

A direction is the kind of question a check asks the project or my conclusion. The map of
directions lives in a project file (see "The three files"); each direction has a short code, which
is written in the journal's `angle` field. The map consists of two tables:

- **directions** - code, name, where it runs, what it catches, **what it does not catch**;
- **when required** - which edit requires which directions.

Example map rows for an ordinary web project (your project has its own):

| Code | Direction | Where it runs | What it catches | What it does not catch |
|---|---|---|---|---|
| `U` | Unit tests | `tests/unit`, `npm test` | Function logic on stub data | Page appearance, the real database, the network |
| `E` | End-to-end browser tests | `tests/e2e`, Playwright | JavaScript errors, broken forms, phone width | Analytics events, emails, payment |
| `R` | After deployment | CI step after deploy | Response code of key pages | Everything except the response code |
| `D` | Data conclusions | a hook or a conclusion checklist | "No", "does not exist", "always" without a source; a metric's cause without a calculation | A wrong conclusion phrased differently; a wrong calculation |
| `F` | Response form | `Stop` hook | A result replaced by a report about the work | An incomplete result |
| `A` | Analytics events | **No check** | - | Everything: an event disappearing before it reaches production is caught by nothing |

Directions `D` (data conclusions) and `F` (response form) exist in almost any project where I write
conclusions and reports, not only code: a noticeable share of the mistakes the user finds lives in
them. Check whether they are set up.

First determine which direction the mistake belongs to. Then the questions in order; each one
needs an answer before the next.

1. **Which direction of the map would have caught this mistake?** Name the code or honestly say
   "there is no such direction". Not "roughly similar to `E`" - a direction either asks this
   question or it does not. The "does not catch" column is the main one here.
2. **If the direction exists - did the "when required" table require it** for what I was editing?
3. **If it did - why was the check not run?**
4. **If it was run - did it find this defect, and where did the finding go?** The question seems
   redundant ("if it found it, it was caught"), and that is exactly why nobody asks it. What was
   found lives in the check output or in a report, and becomes work only if it is filed separately.

Five outcomes, each with its own fix. One must not be substituted for another.

| Outcome | What it means | Where to fix |
|---|---|---|
| **No direction** | The project has no such kind of check at all | Rung 0: a new map row and an executable check |
| **Direction exists, the table did not require it** | The check exists but is not tied to this type of edit | A new row (or a new code in a row) of the "when required" table |
| **The check was required but not run** | A gate defect, not a knowledge defect | Gates: deployment refused without a fresh check, a mandatory ledger line, a hook in `.claude/settings.json` |
| **The check ran, the defect was FOUND, the finding was not filed** | The check worked, and the defect still reached a person. The hole is not in the check but in its OUTPUT | Gates at the check's output: the summary names the finding, the finding goes into the plan with a status |
| **The check ran, the defect was FOUND, the finding was FILED with a status** | The finding is visible, and the defect still got through, because a filed finding STOPS nothing. Sign: the finding is "open", and deployment is technically possible | Rung 1: turn the finding into a machine refusal - a test, a hook, a deployment refusal. An agreement to "check earlier" does not do this |

The third outcome is the most frequent temptation to write everything off as inattention. The
personal category "did not check" is not enough here: the question is not "why did I forget" but
**why skipping a mandatory check went through silently and the work got delivered**.

The fourth outcome is recognized by one sign: **a written finding about the defect exists and is
older than the failure itself.** Then what is reviewed is not the check but the finding's path
out - both "is the finding named in the check's summary" and "does it have a status".

Hence the step's general rule: **before declaring "nobody looked for this", grep the traces of
earlier checks for the subject of the defect**: plans and ledgers in `.claude/`, test and CI
reports, background job reports. If the finding is there, the conclusion "the direction was not
checked" is wrong, and a narrow fix will go to the wrong place.

**Aggregate cross-check, in the same step.** Before closing the direction, grep the journal not by
symptom (that is step 1) but by direction and project:
`grep -i "| <project> |.*angle: D" ~/.claude/aar-log.md`. Two or three entries along one axis are
no longer a coincidence but a profile: the direction is weak as a whole, and a narrow fix in it
will not hold again. Such a finding belongs in the report as a separate line.

## Step 7. Ladder of fixes

You may step down to a lower rung only after **proving** that the higher one does not fit. State in
the report why.

0. **A new kind of check.** Not a test for this case but a class of questions nobody asks the
   project. Sign - the outcome "no direction" at step 6. It is set up as a row in the map (**what it
   catches - what it does not catch - where it runs**), a row in the "when required" table and an
   executable check connected to the project's common check run. If the project has a check of the
   checks themselves (mutations), add a breakage there too that proves the new check catches it.
   The rung is expensive and therefore rare, but it is the only one that catches not this mistake
   but all future mistakes of the same direction. The first candidates are map rows marked "No
   check".
1. **Automation.** A test, a linter, a CI or deployment refusal, a hook in `.claude/settings.json`.
   A mistake of this class physically cannot get through anymore; nothing needs to be remembered.
   The best outcome, and more cases reduce to it than it seems at first glance.
2. **A step in a skill.** This skill, a review skill, the order in a plan file. Suitable when the
   check cannot be automated but can be described as a mandatory action within a known type of
   task.
3. **A rule in the project's `CLAUDE.md`.** Only for what is tied neither to a task type nor to a
   machine check. Expensive: it hangs in every request.
4. **A line in memory** (Claude Code auto memory). Only a fact that cannot be derived from the
   code, the tests and the git history. Before writing - find an existing entry on the topic in the
   memory index and **update it** rather than create a second one.
5. **Nothing.** A deliberate choice if the mistake is rare and any fix costs more than the mistake
   does. That is allowed too, but it must be said out loud, not left unsaid.

Rungs 3 and 4 pay rent in tokens in every request. So the question at these rungs is not "is it
useful to write this down" but **"is it worth hanging in every request until the end of the
project"**.

**Rung 0 is not replaced by rung 1, and vice versa.** A test closes a case; a map row with an
executable check opens a direction. If step 6 gave "no direction" and the fix was a single test for
the same input - the direction remains unclosed, and the same mistake will come from a neighboring
file where nobody wrote a test. The reverse holds as well: a map row without an executable check
that has never been run is an entry in a reference book, not a check. The normal outcome of a
meta-review is usually **two** fixes: rung 0 (the direction) plus rung 1 (this case).

A limiter to keep the map from bloating: **a new direction is set up only when the repeat
condition from step 4 is stated as a direction, not as a case.** "Setting X is not read back" is a
case, rung 1. "No setting is checked by reading it back" is a direction, rung 0.

## Step 8. Write to the journal

One line in the journal:

```
YYYY-MM-DD | <project> | symptom in 5-7 words | found by: user|me | category from step 3 | method: <name from step 5 or "none"> | angle: <checks map code or "none"> | rung from step 7 | link to the fix file
```

The `method` field is needed by step 5: a repeated habit can only be proven by grepping this
field, because by symptom identical methods from different domains never match. The `found by`
and `angle` fields are needed for the aggregate cross-check at step 6: `found by` separates what
the checks caught from what they missed entirely; `angle` lets you grep the journal by direction
rather than by symptom.

The journal is not loaded into context and pays no rent. It is needed for step 1 (to see a
repeat), step 5 (to prove a method) and step 6 (to see a direction's profile).

## Report to the user

Briefly. No preambles and no apologies - they are not information. Six points in mode 1, nine in
mode 2. If the user asked for a result in this turn, the result comes first, then the review
report.

1. **What was wrong** - one phrase.
2. **What was missing** - the category from step 3.
3. **Class or one-off** - and the repeat condition, if it is a class.
4. **Rung** - and why not higher.
5. **What exactly was done** - file, test, rule. With a link.
6. **What proves it is now caught** - the output of a failing and then a passing test, the result
   of a check run, the hook firing on the original text.

Mode 2 only, three extra points:

7. **Working method** - the named assumption and a link to an earlier case from a different domain.
   If the repeat is not proven - say so, and say that the method is not declared.
8. **Direction** - the map code or "no direction", and which of the step 6 outcomes it is.
9. **What changed in how the work is set up** - a new map row, a new row in the "when required"
   table, new gates. If nothing - say directly that there was no macro fix and why.

Point 6 is mandatory for rungs 0 and 1. A rule added without checking that it fires is a second
instance of the same mistake, "said checked without checking". For a new direction, the proof is
one real run of its check, not its description.

## What not to do

- **No self-flagellation.** The process is reviewed, not me. Apologies, self-assessments and lists
  of past misses are not part of the report and take up space needed for facts.
- **Do not write to memory what a test fixes.** This is the main way to spoil memory: it bloats,
  and mistakes keep getting through.
- **Do not invent a rule broader than the finding.** One mistake gives one narrow checkable rule.
  Broad rules like "always be more careful" never fire and still pay rent.
- **Do not consider the review finished without a change.** A review that produced not a line of
  code, not a line of a rule, not a deliberate "rung 5, we do nothing" is a conversation, not an
  improvement.
- **Do not explain "the user found it" by bad luck.** "A rare scenario", "nobody would have
  noticed", "a coincidence" - that is abandoning step 6. The mistake passed the whole chain of
  checks unnoticed; the question is about the chain, not about probability.
- **Do not pass off a narrow test as a closed direction.** The most common way to fail a
  meta-review: the outcome is "no direction", and the report has one new test and the word
  "covered".
- **Do not set up a direction to tick a box.** A map row without the "does not catch" column and
  without an executable check that has caught its own breakage at least once is garbage that is
  later read as a checked direction. Better an honest "the direction is recognized as weak, not set
  up, for such-and-such reason".
- **Do not declare a method without a proven repeat.** One mistake in one domain is a case.
- **Do not fix a method with words.** "From now on, read the primary source" is rung 4 without a
  single firing. A method is either turned into a machine action or remains unfixed.
- **Do not stretch a meta-review into a revision of the whole process.** One mistake gives one
  direction. A revision of the whole map and all gates at once is a new task, and it is set up
  separately, with the user's consent.

---
name: delegated-research
description: >-
  Investigate a question against high-trust primary sources and capture the findings as a
  Markdown file in the repo. Use when the user wants a topic researched, docs or API facts
  gathered, or reading legwork delegated to a background agent. NOT for decisions the user
  must make, one-call lookups, or any code changes.
slug: delegated-research
version: 1.1.0
displayName: delegated-research
---

# Delegated Research

Spin up a **background agent** to do the research, so you keep working while it reads.

Its job:

1. Investigate the question against **primary sources** — official docs, source code, specs, first-party APIs — not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

## Invocation

Ask for it directly, e.g.:

    /delegated-research What rate limits does the GitHub REST API apply to our token class?

Optional: name the output path. Default = wherever the repo keeps research notes
(look for `docs/`, `notes/`, `research/`); if no convention exists, pick a sensible
location and state where the file landed.

## Example

Prompt: `What rate limits does the GitHub REST API apply to our token class?`
Result: a background agent reads the developer docs (primary pages, not blog posts),
writes `research/github-rest-rate-limits.md`, and footnotes every claim to the doc page
and section it came from — while you keep working on your own task.

## Failure exits

- **Primary sources unreachable** (no network, 4xx/5xx, auth wall): report which sources
  failed and stop. Do not silently substitute secondary write-ups; ask whether
  secondary sources are acceptable.
- **Question too vague to research**: return 2–3 candidate interpretations of the
  question and what each would require; do not pick one and guess.
- **No repo convention for notes**: write to a default location, say where, and note
  that the convention is assumed, not discovered.

## NOT for

- Decisions the user must make — this gathers facts; it does not choose between options.
- Quick lookups answerable in one tool call — just look it up; delegation overhead
  isn't worth it.
- Any code or config changes — scope is one read-only investigation plus the single
  findings file.

## Misuse → fix

| Wrong | Fix |
|---|---|
| Findings cite a secondary write-up | Re-run that claim against the primary source that owns it |
| Agent edited code while "researching" | Revert the edits; scope is read-only plus the notes file |
| Unreachable sources quietly replaced with blogs | Stop and ask; substitution needs the user's yes |

---
name: to-tickets
description: >-
  Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring
  its blocking edges, published to the configured tracker — edges as text in one file per ticket
  locally, or native blocking links on a real tracker. ACs written as machine-verifiable predicates
  (AI-ready, not prose — directly verifiable post-implementation). Use when the user wants to turn a
  plan or PRD into agent-ready tickets, split work with explicit blockers, or publish a tracer-bullet
  breakdown to a local issues folder or issue tracker.
---

**Wide refactors are the exception to vertical slicing.**

- **Blocked by**: which other tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this ticket makes work Ask the user: - Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct — does each ticket only depend on tickets that genuinely gate it?
- Should any tickets be merged or split further? Iterate until the user approves the breakdown. ### 5. Publish the tickets to the configured tracker Publish the approved tickets. **How** depends on the tracker `/setup-matt-pocock-skills` configured — the tickets are the same either way, only the shape of the blocking edges changes: - **Local files** → write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Each file's "Blocked by" lists the numbers/titles it depends on. Use the per-ticket file template below — one ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per ticket in dependency order (blockers first) so each ticket's blocking edges can reference real identifiers. Use the platform's native blocking / sub-issue relationship where it has one; otherwise set each ticket's "Blocked by" to the blocking issues. Apply the `ready-for-agent` triage label unless instructed otherwise — the tickets are agent-grabbable by construction. Work the **frontier**: any ticket whose blockers are all done. For a purely linear chain that means top to bottom. Do NOT close or modify any parent issue. <local-ticket-template> # <NN> — <Ticket title> **What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list. **Blocked by:** the numbers/titles of the tickets that gate this one, or "None — can start immediately". **Status:** ready-for-agent - [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2 </local-ticket-template> <issue-template> ## Parent A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section). ## What to build The end-to-end behaviour this ticket makes work, from the user's perspective — not layer-by-layer implementation. ## Acceptance criteria - [ ] Criterion 1
- [ ] Criterion 2 ## Blocked by - A reference to each blocking ticket, or "None — can start immediately". </issue-template> In either form, avoid specific file paths or code snippets — they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.


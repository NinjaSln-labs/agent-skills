---
name: event-storming
description: >-
  EventStorming facilitation knowledge and reference across Big Picture,
  Process Modeling, and Design-Level formats. Use when: 'run EventStorming',
  'model a domain', 'discover bounded contexts', 'Big Picture session', 'map
  domain events', 'find aggregates', 'DDD workshop', 'bounded context
  heuristics'. Actions: --big-picture / --process / --design-level (format
  guidance), --patterns (facilitation patterns/anti-patterns), --glossary,
  --notation, --remote. No args: interactive discovery — checks Miro for
  boards (if available), asks goal, recommends format. NOT for: actually
  running an agentic multi-persona workshop simulation or executing a
  domain-discovery session with deliverables — facilitation reference and
  guidance only; no skill name implied (any client's own tooling applies).
slug: event-storming
version: 1.1.0
displayName: event-storming
---

# Event Storming

## Variables

Arguments: `$ARGUMENTS`

## Argument Parsing

Parse `$ARGUMENTS` for:

- **Format filter** (optional):
  - `--big-picture`: Big Picture EventStorming workshop guidance
  - `--process`: Process Modeling format and building blocks
  - `--design-level`: Design-Level EventStorming and software modeling
  - `--patterns`: Facilitation patterns and anti-patterns catalog
  - `--glossary`: Terms, definitions, and notation reference
  - `--notation`: Color scheme and sticky note types quick reference
  - `--remote`: Remote/digital workshop adaptations and tool guidance
- **Free-form query**: any other text is treated as a topic to search across all reference docs

If no filter is specified, run the **Interactive Discovery** flow below.

To *run* an agentic AI-driven workshop (multi-persona simulation) rather than read facilitation guidance: that is outside this skill's scope — this skill provides facilitation reference and guidance only. If the user's client happens to have its own simulation tooling, point them there; otherwise guide a human-facilitated session with the reference docs below.

---

## Interactive Discovery (no args)

When invoked with no arguments, help the user figure out what they need. Don't dump information — ask questions.

### Step 1: Check for existing boards

**Miro availability gate:** this step needs a Miro MCP server. If Miro tools are unavailable in the session (no `miro_list_boards` tool), skip board discovery entirely and go straight to Step 2 — do not error. Reference-only guidance (every `--<format>` action) works with no Miro at all.

When Miro IS available, query it for recent boards: `miro_list_boards`. Look for boards with EventStorming-related names (containing "Big Picture", "Process Model", "Design-Level", "EventStorming", or domain-specific names from prior sessions). Sort by last modified.

If recent boards exist, present them:
> "I found these EventStorming boards:
>
> - [Board Name] (last modified [date]) — [item count] items
> - [Board Name] (last modified [date]) — [item count] items
>
> Would you like to:
>
> 1. Continue working with one of these boards
> 2. Start a new EventStorming session
> 3. Just learn about EventStorming (reference mode)"

If the user picks an existing board, read it via `miro_list_board_items` (full pagination) to understand what's there — what format was used, what phase it's in, what building blocks are present. Then suggest next steps:

- If it's a Big Picture with no PM/DL follow-up → suggest facilitating a Process Modeling pass next (`--process`, see `@./reference/process-modeling.md`) or a Value Exploration on the winning problem
- If it's a Big Picture with PM done → suggest a Design-Level session (`--design-level`, see `@./reference/design-level.md`, which covers CRC-card style modeling of aggregates)
- If it has value stickies → suggest contrasting/diverging perspectives
- If it looks incomplete → suggest resuming where it left off

### Step 2: If starting fresh, identify the goal

Use AskUserQuestion:
> "What are you trying to accomplish? This determines which EventStorming format to use:
>
> 1. **Explore a whole business/domain** — discover what we don't know, find the biggest problems, identify bounded contexts (Big Picture)
> 2. **Design a specific process** — model how a particular workflow should work end-to-end (Process Modeling)
> 3. **Design software** — discover aggregates, commands, and events for implementation (Design-Level)
> 4. **Improve an existing process** — retrospective on what's broken and where to fix it (Retrospective)
> 5. **Understand value delivery** — where value is created and destroyed, for whom (Value Exploration)
> 6. **Onboard someone** — teach how the business works through guided discovery (Induction)
> 7. **Optimize user experience** — follow the customer journey, find friction, design for flawless execution (UX-Driven)
> 8. **I'm not sure** — let's figure it out together"

### Step 3: Scope the domain

Based on their choice, ask:
> "What domain or problem space are we exploring?
>
> Examples: e-commerce, conference organization, healthcare scheduling, insurance claims, logistics..."

Then do 3+ web-research searches for domain context before proceeding — use the Perplexity MCP tools if present, otherwise the built-in `WebSearch`/`WebFetch`. If no web-research surface is available, ask the user for the domain context instead of guessing.

### Step 4: Recommend and execute

Based on goal + domain, recommend the specific format and confirm:
> "Based on [goal], I recommend starting with [format]. This will involve [brief description].
>
> To read the facilitation guidance, run this skill with the `--[format]` action (e.g. `--big-picture`, see `@./reference/big-picture-workshop.md`; the Reference Documents section maps every format to its file). Actually running the session as an agentic multi-persona simulation is outside this skill's scope — facilitation reference and guidance only."

If the user said "I'm not sure" in Step 2, ask clarifying questions:

- "Is this a new project or an existing system?"
- "Are you trying to understand the problem or design a solution?"
- "How many people/perspectives need to be represented?"

Then recommend based on Brandolini's transition funnel: almost always start with Big Picture.

---

## Overview

EventStorming is a flexible workshop format for collaborative exploration of complex business domains. It uses simple notation (colored sticky notes on an unlimited modeling surface) to rapidly build a shared understanding of a business process.

**Three main formats, increasing in precision:**

1. **Big Picture** — Explore the entire business domain with all stakeholders. Discover bounded contexts, hotspots, and key business events. The broadest format.
2. **Process Modeling** — Zoom into a specific business process. Model the flow with events, commands, policies, read models, and external systems. A cooperative game.
3. **Design-Level** — Zoom into software design. Discover aggregates, define command/event contracts, and bridge to implementation. The most precise format.

**Core principle:** EventStorming is not about the stickies — it is about the conversations the stickies trigger. The real value is shared understanding, not the artifact.

### Source authority hierarchy

Brandolini's book (*Introducing EventStorming*, Leanpub) is the **canonical source** for all methodology content. When research returns step orderings, procedures, or workflow modifications from secondary sources (Bourgau, MrPicky, practitioners):

1. **Always cross-check against Brandolini** before adopting into the skill
2. Secondary sources are **enrichments** tagged `[BOURGAU]` or `[SUPPLEMENTED]`, never replacements for canonical content
3. **When sources conflict, Brandolini wins**
4. **When Brandolini is silent** (e.g., Design-Level at ~10% written), secondary sources fill the gap with clear attribution

This matters because secondary authors publish their *interpretations* of how to facilitate Brandolini's method — often good interpretations, but not Brandolini's prescribed sequence.

---

## Notation Quick Reference

| Color | Element | Description |
|-------|---------|-------------|
| **Orange** | Domain Event | Something that happened (past tense). The fundamental building block |
| **Blue** | Command / Action | An intention or decision that triggers an event |
| **Lilac/Purple** | Policy | Reactive logic — "whenever X happens, do Y". Connects events to commands |
| **Yellow (small)** | Actor / Person | A human role that issues commands |
| **Yellow (large)** | Read Model | Information a person needs to make a decision |
| **Pink/Red** | External System | A system outside the current domain boundary |
| **Magenta/Hot Pink** | Hot Spot | A problem, question, conflict, or unresolved issue |
| **Green** | Opportunity | Value, revenue, or positive outcome |
| **Pale Yellow** | Aggregate | A consistency boundary (Design-Level only) |

For complete notation details: see `@./reference/notation-and-building-blocks.md`

---

## Reference Documents

Load these based on what the user needs:

**For running a Big Picture workshop**: `@./reference/big-picture-workshop.md`

- Room setup, invitations, phases, facilitation, aftermath, variations, remote mode

**For process-level modeling**: `@./reference/process-modeling.md`

- Building blocks in detail, game strategies, cooperative game structure

**For Design-Level software modeling**: `@./reference/design-level.md`

- Aggregates, domain events, commands, bridging to code, user stories

**For facilitation patterns and anti-patterns**: `@./reference/patterns-and-anti-patterns.md`

- Named patterns catalog, anti-patterns catalog, red zone tips

**For remote / digital workshop adaptations**: `@./reference/remote-eventstorming.md`

- Brandolini's remote guidance, format-specific adaptations, tool landscape, remote vs in-person decision matrix

**For complete notation, glossary, and tools**: `@./reference/glossary-and-tools.md`

- Full glossary of terms, physical tools (stickies, markers, surfaces), digital tools

---

## Applying EventStorming to Your Codebase

EventStorming output (sticky notes on a wall) bridges to code via DDD tactical patterns. Each
sticky-note color maps to a concrete code element in a DDD codebase — commands, domain events,
aggregates, read models, policies. See `reference/design-level.md` ("Relationship to Your
Architecture") for the sticky-color-to-tactical-pattern mapping and how to translate it to the
building blocks your own stack uses.

EventStorming directly informs bounded context discovery, domain event design, aggregate
boundaries, command/query separation, policy identification, and hot-spot tracking — see
`reference/design-level.md` for the concrete code mapping.

When using this skill for domain modeling, read the consuming project's own architecture and
language conventions (its `CLAUDE.md` / `.claude/rules` or equivalent) and map the tactical
patterns onto that stack's building blocks rather than assuming a particular framework.

## Export options

When the user wants shareable artifacts from EventStorming output, and the `document-skills` plugin
(or equivalent document tooling) is available in the session, hand off to it:

- **Board results slides** — `document-skills:pptx` for Big Picture results, Process Model swimlanes
- **Workshop guide** — `document-skills:docx` for participant materials and facilitation notes
- **Stakeholder report** — `document-skills:pdf` for comprehensive modeling report

If no document tooling is present, emit the artifact as markdown instead.

---

## Worked Example (shortest path)

**Precondition:** none required — every action is pure guidance, no MCP tools needed.

**User says:** "run EventStorming" (no args) → Interactive Discovery fires:

1. Miro tools absent → board check skipped silently (Step 2 directly).
2. Asks goal (Step 2) → user picks "Explore a whole business/domain".
3. Asks domain (Step 3) → "e-commerce order fulfillment".
4. Recommends (Step 4): Big Picture, and points to `@./reference/big-picture-workshop.md`.

**Output excerpt (what the guidance looks like):**

> **Big Picture — Phase 2: Event Brainstorming.** Give everyone orange stickies. Each person writes domain events — things that *happened*, past tense ("Order Placed", "Payment Received"). Throw them on the timeline unordered; sorting comes later. Horizontal duplicates are expected — dedupe verbally, not by confiscating stickies.

**User says:** "--design-level" → returns the Design-Level guidance directly (aggregates, command/event contracts, CRC-card modeling) from `@./reference/design-level.md`; no questions asked.

---

## Failure Exits (observable)

| Situation | Observable exit |
|-----------|-----------------|
| Miro tools unavailable | Skip Step 1 entirely (already the documented gate) — say "Miro not connected, skipping board check" at most once, then go to Step 2. Never error or retry. |
| No web-research surface (Perplexity MCP absent, WebSearch/WebFetch unavailable or blocked) | Stop researching, tell the user, and ask them to describe the domain in 2-3 sentences instead of guessing. Do not invent domain facts. |
| Unknown `--flag` (e.g. `--miro-export`) | Say: "`--miro-export` is not a supported action" + list the seven valid actions in one line, then ask whether to run Interactive Discovery. Never silently treat it as a free-form query if it starts with `--`. |
| `@./reference/<file>.md` missing from the package | Name the missing file and stop with guidance drawn from the Notation Quick Reference + Overview only; do not fabricate the reference content. |
| Free-form query matches nothing in the references | Say what was searched and what wasn't found, then offer the closest format action by goal (Step 2 taxonomy). |
| User asks to *run* the workshop as an agent simulation | Refuse per scope (Argument Parsing note) and offer the human-facilitated path: pick format action + reference doc. |

## Network-boundary note (offline / restricted-network users)

The only steps that may touch the network are the domain-research searches in Interactive Discovery Step 3, and they already degrade locally (ask the user instead). Every `--<action>` reference lookup and the notation quick reference are fully offline. Miro is optional end-to-end; its absence changes nothing in the main path.

## 中文速览（Quick Start · Chinese）

- **无参数调用** → 互动发现：先问目标（8 选 1）→ 问领域 → 推荐格式（几乎总是先 Big Picture）。
- **带动作调用** → 直接返回对应指南：`--big-picture`（全景工作坊）、`--process`（流程建模）、`--design-level`（软件设计/聚合）、`--patterns`（引导模式与反模式）、`--glossary`（术语）、`--notation`（便利贴配色速查）、`--remote`（远程/数字化工作坊）。
- **没有 Miro / 没有外网** → 主路径不受影响：Miro 缺席跳过看板检查；外网不可达改为向用户提问收集领域背景。
- **本技能只给引导方法与参考资料**，不替你执行多人模拟工作坊。

## FAQ (wrong → fix)

| Wrong move | Fix |
|------------|-----|
| "It asked me for Miro and errored" | It shouldn't — no Miro tools in the session means board discovery is skipped by design. If you saw an error, re-run; the gate is "skip, don't error". |
| "I typed a topic and got generic content" | Free-form text searches the reference docs. For targeted guidance use a format action (`--big-picture` / `--process` / `--design-level`). |
| "I wanted the AI to role-play the workshop" | Out of scope by design. Take the `--<format>` guidance and facilitate with your team (or your client's own simulation tooling). |
| "Which format should I start with?" | Almost always Big Picture (transition funnel). Use `--process` only for one specific workflow, `--design-level` only once the domain language exists. |
| "The reference file reference is dead / file missing" | Report it as a package defect; meanwhile use the Notation Quick Reference table above. |

## NOT For / Anti-Patterns (observable)

- NOT for actually running a multi-persona agentic workshop simulation with deliverables — this skill returns facilitation guidance only; the refusal is observable (it hands you a reference doc + a facilitation plan, not a simulated session transcript).
- NOT for choosing aggregates by reading code first — Design-Level starts from events/commands discovered in a session, not from the current database schema.
- Anti-pattern: skipping Big Picture and jumping straight to Design-Level for a domain nobody has explored (Brandolini's funnel: start broad).
- Anti-pattern: treating stickies as the deliverable — if the output is a photo of a wall and no shared decisions/hot-spots, the session failed regardless of how neat the wall looks.
- Anti-pattern: deduplicating events silently on a shared board — duplicates are signal; resolve them out loud.

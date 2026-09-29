---
name: product-marketing
description: >-
  Creates and updates `.agents/product-marketing.md` — shared product, audience, and
  positioning context that other marketing skills reference so users avoid repeating
  foundational information. Use when the user wants to create or update their product
  marketing context document, or mentions 'product context,' 'marketing context,' 'set up
  context,' 'positioning,' 'who is my target audience,' 'describe my product,' 'ICP,'
  'ideal customer profile.' Use at the start of any new project before other marketing
  skills.
slug: product-marketing
version: 1.1.0
displayName: product-marketing
---

# Product Marketing Context

You help users create and maintain a product marketing context document. This captures foundational positioning and messaging information that other marketing skills reference, so users don't repeat themselves.

The document is stored at `.agents/product-marketing.md`.

## Workflow

### Step 1: Check for Existing Context

First, check if `.agents/product-marketing.md` already exists. Also check `.claude/product-marketing.md` and the legacy filename `product-marketing-context.md` (in either `.agents/` or `.claude/`) for older setups — if found anywhere other than `.agents/product-marketing.md`, offer to move it to the canonical location.

**If it exists:**
- Read it and summarize what's captured — note its current **Document version** and the last few **Changelog** entries so the user sees where the doc stands and what's changed recently
- Ask which sections they want to update
- Only gather info for those sections
- On any substantive save, bump the version and add a changelog entry (see Step 4). This doc is the shared context every other marketing skill reads, so a dated paper trail of *what changed and why* is worth keeping.

**If it doesn't exist, offer two options:**

1. **Auto-draft from codebase** (recommended): You'll study the repo—README, landing pages, marketing copy, package.json, etc.—and draft a V1 of the context document. The user then reviews, corrects, and fills gaps. This is faster than starting from scratch.

2. **Start from scratch**: Walk through each section conversationally, gathering info one section at a time.

Most users prefer option 1. After presenting the draft, ask: "What needs correcting? What's missing?"

### Step 2: Gather Information

**If auto-drafting:**
1. Read the codebase: README, landing pages, marketing copy, about pages, meta descriptions, package.json, any existing docs
2. Draft all sections based on what you find
3. Present the draft and ask what needs correcting or is missing
4. Iterate until the user is satisfied

**If starting from scratch:**
Walk through each section below conversationally, one at a time. Don't dump all questions at once.

For each section:
1. Briefly explain what you're capturing
2. Ask relevant questions
3. Confirm accuracy
4. Move to the next

Push for verbatim customer language — exact phrases are more valuable than polished descriptions because they reflect how customers actually think and speak, which makes copy more resonant.

---

## Sections to Capture

### 1. Product Overview
- One-line description
- What it does (2-3 sentences)
- Product category (what "shelf" you sit on—how customers search for you)
- Product type (SaaS, marketplace, e-commerce, service, etc.)
- Business model and pricing

### 2. Target Audience
- Target company type (industry, size, stage)
- Target decision-makers (roles, departments)
- Primary use case (the main problem you solve)
- Jobs to be done (2-3 things customers "hire" you for)
- Specific use cases or scenarios

### 3. Personas (B2B only)
If multiple stakeholders are involved in buying, capture for each:
- User, Champion, Decision Maker, Financial Buyer, Technical Influencer
- What each cares about, their challenge, and the value you promise them

### 4. Problems & Pain Points
- Core challenge customers face before finding you
- Why current solutions fall short
- What it costs them (time, money, opportunities)
- Emotional tension (stress, fear, doubt)

### 5. Competitive Landscape
- **Direct competitors**: Same solution, same problem (e.g., Calendly vs SavvyCal)
- **Secondary competitors**: Different solution, same problem (e.g., Calendly vs Superhuman scheduling)
- **Indirect competitors**: Conflicting approach (e.g., Calendly vs personal assistant)
- How each falls short for customers

### 6. Differentiation
- Key differentiators (capabilities alternatives lack)
- How you solve it differently
- Why that's better (benefits)
- Why customers choose you over alternatives

### 7. Objections & Anti-Personas
- Top 3 objections heard in sales and how to address them
- Who is NOT a good fit (anti-persona)

### 8. Switching Dynamics
The JTBD Four Forces:
- **Push**: What frustrations drive them away from current solution
- **Pull**: What attracts them to you
- **Habit**: What keeps them stuck with current approach
- **Anxiety**: What worries them about switching

### 9. Customer Language
- How customers describe the problem (verbatim)
- How they describe your solution (verbatim)
- Words/phrases to use
- Words/phrases to avoid
- Glossary of product-specific terms

### 10. Brand Voice
- Tone (professional, casual, playful, etc.)
- Communication style (direct, conversational, technical)
- Brand personality (3-5 adjectives)

### 11. Proof Points
- Key metrics or results to cite
- Notable customers/logos
- Testimonial snippets
- Main value themes and supporting evidence

### 12. Goals
- Primary business goal
- Key conversion action (what you want people to do)
- Current metrics (if known)

---

## Step 3: Create the Document

After gathering information, create `.agents/product-marketing.md` with this structure:

```markdown
# Product Marketing Context

**Document version:** v1
**Last updated:** [date]

## Product Overview
**One-liner:**
**What it does:**
**Product category:**
**Product type:**
**Business model:**

## Target Audience
**Target companies:**
**Decision-makers:**
**Primary use case:**
**Jobs to be done:**
-
**Use cases:**
-

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| | | | |

## Problems & Pain Points
**Core problem:**
**Why alternatives fall short:**
-
**What it costs them:**
**Emotional tension:**

## Competitive Landscape
**Direct:** [Competitor] — falls short because...
**Secondary:** [Approach] — falls short because...
**Indirect:** [Alternative] — falls short because...

## Differentiation
**Key differentiators:**
-
**How we do it differently:**
**Why that's better:**
**Why customers choose us:**

## Objections
| Objection | Response |
|-----------|----------|
| | |

**Anti-persona:**

## Switching Dynamics
**Push:**
**Pull:**
**Habit:**
**Anxiety:**

## Customer Language
**How they describe the problem:**
- "[verbatim]"
**How they describe us:**
- "[verbatim]"
**Words to use:**
**Words to avoid:**
**Glossary:**
| Term | Meaning |
|------|---------|
| | |

## Brand Voice
**Tone:**
**Style:**
**Personality:**

## Proof Points
**Metrics:**
**Customers:**
**Testimonials:**
> "[quote]" — [who]
**Value themes:**
| Theme | Proof |
|-------|-------|
| | |

## Goals
**Business goal:**
**Conversion action:**
**Current metrics:**

## Changelog
*Newest first. One line per revision: what changed and why.*
- v1 ([date]) — Initial context.
```

---

## Step 4: Confirm, Version, and Save

- Show the completed document
- Ask if anything needs adjustment
- **Set the version and changelog** — this is the paper trail for a doc every other skill reads:
  - **New document:** set `Document version: v1` and a single Changelog entry — `- v1 ([today]) — Initial context.`
  - **Updating an existing document:** increment the version (v2 → v3 …), update `Last updated` to today, and **prepend a new Changelog entry** at the top of the list (newest first) summarizing *what changed and why* in one line. Never rewrite or reorder past entries.
  - A good entry names the sections touched and the reason, not "updated the doc." Examples:
    - `- v3 (2026-07-16) — Repositioned from "email tool" to "deliverability platform"; added RevOps to the ICP.`
    - `- v2 (2026-06-02) — Rewrote value prop and objections after 5 customer interviews; added competitor Acme.`
  - Use today's date in ISO form (YYYY-MM-DD) for the entry and `Last updated`.
  - **Pure typo-only fix:** don't bump the version or add a changelog entry — just save the correction. Every other change bumps the version and gets an entry. When the change is a real repositioning, say so plainly — downstream skills will now generate against the new context.
- Save to `.agents/product-marketing.md`
- Tell them: "Other marketing skills will now use this context automatically. The Changelog at the bottom tracks every revision — check it to see how your positioning has evolved. Run `/product-marketing` anytime to update it."

---

## Tips

- **Be specific**: Ask "What's the #1 frustration that brings them to you?" not "What problem do they solve?"
- **Capture exact words**: Customer language beats polished descriptions
- **Ask for examples**: "Can you give me an example?" unlocks better answers
- **Validate as you go**: Summarize each section and confirm before moving on
- **Skip what doesn't apply**: Not every product needs all sections (e.g., Personas for B2C)

---

## Inputs and Outputs

**Input:** none required to start — the skill gathers everything by reading the repo and asking. Optional inputs that speed it up: an existing `.agents/product-marketing.md`, a README, landing-page copy, or customer quotes the user pastes in.

**Output:** exactly one file, `.agents/product-marketing.md`, in the structure of Step 3, with `Document version`, `Last updated` (ISO date), and a `Changelog` section. No other files are created or modified.

---

## Worked Example (shortest path)

**Precondition:** a repo with a README, no `.agents/product-marketing.md` yet.

**User says:** "Set up my product marketing context."

**What happens:**
1. No existing context found → offers auto-draft (option 1) and the user accepts.
2. Reads README / landing copy / package.json, drafts all 12 sections.
3. Asks: "What needs correcting? What's missing?" — user fixes the one-liner and ICP.
4. Saves and reports the excerpt below.

**Output excerpt (what the saved file looks like):**

```markdown
# Product Marketing Context

**Document version:** v1
**Last updated:** 2026-09-29

## Product Overview
**One-liner:** SavvyCal is scheduling that respects both sides of the meeting.
**Product category:** scheduling software
**Business model:** SaaS, per-seat monthly subscription
...
## Changelog
- v1 (2026-09-29) — Initial context.
```

**Update example — user says:** "We pivoted from an email tool to a deliverability platform; update the context." → Only ICP, Differentiation, Competitive Landscape are re-gathered, version bumps to v3, one changelog line is prepended; untouched sections stay as-is.

---

## Failure Exits (observable, do these — not just "note a degradation")

| Situation | Observable exit |
|-----------|-----------------|
| No repo / empty directory, and user can't answer section questions | Say: "No codebase and no answers provided — I can only produce a skeleton." Save the skeleton with every section left as `**TBD**`, version it `v1`, and list the TBD sections back to the user. Do **not** invent product facts. |
| `.agents/` cannot be written (permission error on save) | Report the exact path and the error message, then offer: save to `.claude/product-marketing.md` instead, or have the user fix permissions (`mkdir -p .agents` / adjust write access) and retry. Do not silently drop the save. |
| A legacy copy exists (`product-marketing-context.md` or `.claude/product-marketing.md`) and differs from `.agents/product-marketing.md` | Show both versions and ask which is canonical before merging; never overwrite without an explicit choice. |
| Repo scan finds no marketing signals (no README, no copy) | Say which sources were checked and came up empty, then switch to conversational gathering instead of fabricating positions. |
| User contradicts a previously saved section | Treat the user as authoritative: update the section, bump the version, and record the contradiction in the changelog line (e.g. "ICP corrected — prior draft was inferred from README, user says otherwise"). |

---

## NOT For

- Writing the actual marketing copy (pages, emails, ads) — that is `marketing-copywriting` and related skills, which **read** this document.
- One-off competitive research or market sizing with no intent to maintain positioning context.
- Internal/non-product docs (engineering design docs, user manuals).

## Common Mistakes → Fixes

| Wrong approach | Observable symptom | Fix |
|----------------|--------------------|-----|
| Dumping all 12 sections of questions at once | One giant question list the user can't answer | Walk section by section (Step 2); ask, confirm, move on. |
| Polishing the customer's words into marketing speak | Changelog/quotes contain paraphrases, no verbatim quotes | Keep `"exact words"` in quotes; polish downstream copy instead. |
| Editing the file by hand later without version/changelog | `Document version` unchanged after real content changes | Every substantive save bumps version + prepends one changelog line (typo-only fixes excepted). |
| Rewriting/reordering old changelog entries | History no longer shows how positioning evolved | Only prepend; never touch past entries. |
| Letting the model invent competitors, metrics, or testimonials | Proof Points contains numbers the user never gave | Ask for the fact or mark `**TBD**`; never fabricate. |
| Filling every section for a tiny B2C product | Personas table full of invented stakeholders | Skip sections that don't apply and say so. |

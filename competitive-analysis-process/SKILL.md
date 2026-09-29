---
name: competitive-analysis-process
description: >-
  Orchestrate a complete competitive analysis end to end: market landscape, product-level
  comparison, ability to fulfill customer needs, business and financial baseline, relative
  positioning, and competitors' strategic direction — closing with the artifacts owners
  consume: battle cards, an executive comparison matrix, positioning counter-moves, a
  threat assessment. Use when a decision needs the whole competitive picture — market
  entry, a roadmap bet, a positioning refresh, deal defense — or when the real question is
  which steps to run and what to skip. NOT for: a one-off competitor snapshot, a single
  field-action card, scheduled monitoring of an existing snapshot, or market sizing alone
  — boundaries by task, no skill name implied.
slug: competitive-analysis-process
version: 1.1.1
displayName: competitive-analysis-process
---

# Competitive Analysis Process

## Purpose

Orchestrate rigorous, repeatable competitive analysis across **six analytical steps**, producing four
actionable output types (battle cards, comparison matrices, positioning counter-moves, threat
assessments). This is the umbrella: each step names its purpose, its frameworks, and the skill that
does the work — the way a discovery pipeline orchestrates its discovery skills. Run all six for a
strategy cycle; run one when a specific question walks in the door. The steps build on each other, but
the sequence bends to the decision.

## Input

**Works best with:** the market or competitor set in scope, and **the decision this analysis
supports** — a roadmap bet, a positioning refresh, a market entry, deal defense. The decision
determines which steps get depth and which get a pass.
**Also useful:** any existing intelligence — a prior landscape scan, snapshots, battle cards, or
`company-intel` output — so steps consume rather than repeat it.

Input supplied inline with the invocation — text after the skill name, a pasted context dump, or an
appended `ARGUMENTS:` line — counts as answers already given. Use it; don't re-ask.

**Arriving empty-handed? That works too.** The workflow opens by asking what decision is on the table
and what you already know, then recommends which steps to run and in what order.

**Example invocation:** `Run the competitive analysis process on the mid-market payroll space —
decision: whether we defend down-market or push up. We have last quarter's landscape scan.`

## Key Concepts

- **Six steps, four outputs.** The steps are analytical lenses; the outputs (battle cards, comparison
  matrices, positioning moves, threat assessments) are what sales, execs, and roadmap owners actually
  consume. A step that doesn't feed an output is a detour.
- **Steps delegate; this skill orchestrates.** Each step below names the skill that does the work.
  This file holds the sequence, the frameworks, and the decision points — not the research mechanics.
- **Evidence discipline throughout.** Every step honors the
  [`autonomous-investigation`](../autonomous-investigation/SKILL.md) protocol
  (Fact/Inference/Assumption labels, real URLs, confidence stacking), drawing signals from the
  channels in [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md).
- **Named frameworks, cited.** Each step stands on published strategy work — Porter's Five Forces,
  the Kano model, Jobs-to-be-Done, the Business Model Canvas, Ries & Trout positioning, Hamel &
  Prahalad strategic intent. The frameworks are defined where used; agents shouldn't assume prior
  knowledge.
- **Present ≠ future.** Steps 1-5 read where competitors *are*; Step 6 reads where they're *going* —
  and it's the step most teams skip, which is why they're perpetually surprised.

## Application

**Step 0 — Scope.** Confirm the decision, the competitor set (or run
[`market-landscape-scan`](../market-landscape-scan/SKILL.md) to find it), and which steps matter.
Offer the six steps as a numbered menu; recommend a subset when the decision doesn't need all six.

### Step 1: Overview of the Competitive Landscape

*Who's in the game, where, and how they operate — market saturation, fragmentation, disruptive entrants.*

- **Frameworks:** Porter's Five Forces (industry structure); strategic group mapping (clustering
  competitors by GTM model, innovation pattern, or regional depth); market fragmentation indexing.
- **Run:** [`market-landscape-scan`](../market-landscape-scan/SKILL.md) — segments, player map,
  dynamics, whitespace with the dead-zone test.
- **Decision point:** which 2-4 players deserve depth? Everything downstream narrows to them.

### Step 2: Comparisons at the Product Level

*Beyond feature lists: value delivery, architecture, interoperability, lifecycle maturity.*

- **Frameworks:** Kano model (which features delight vs. merely satisfy); Geoffrey Moore's Whole
  Product model (core product vs. the ring of services and integrations deals actually hinge on);
  JTBD-based capability maps (compare by customer job, not by feature name).
- **Run:** [`competitive-research-snapshot`](../competitive-research-snapshot/SKILL.md) on the
  selected players — its comparison matrix is this step's artifact.
- **Watch for:** feature parity theater. A capability map by job-to-be-done exposes what a feature
  checklist hides: two "identical" features serving different jobs badly.

### Step 3: Ability to Fulfill Customer Needs

*How well they serve real customers — outcomes, support quality, ecosystem benefits — not tech specs.*

- **Frameworks:** Outcome-Driven Innovation (score against customer-defined outcomes); Value
  Proposition Canvas (their promise vs. the jobs/pains/gains that matter).
- **Run:** [`voice-of-customer-miner`](../voice-of-customer-miner/SKILL.md) across the sources your
  buyer reads — need themes, quoted verbatims, competitor weak points, and switching triggers, each
  with a source-bias note.
- **Watch for:** vendor-authored "reviews" and case studies. Independent complaint clusters are the
  signal; curated success stories are marketing.

### Step 4: Compilation of Business Information

*The financial, organizational, and market baseline: structure, revenue streams, growth levers, channels.*

- **Frameworks:** Business Model Canvas (how the whole machine fits together); revenue stream
  breakdown; sales channel profiling (direct vs. OEM vs. VAR vs. platform).
- **Run:** [`company-intel`](../company-intel/SKILL.md) per deep-dive competitor — its eleven-section
  output (financials, offers, org signals) is this step's artifact; FININT sources per
  `intelligence-collection-disciplines` do the heavy lifting.
- **Watch for:** press-release accounting. Filings and earnings calls outrank announcements —
  companies lie less where lying is a felony.

### Step 5: Perception and Relative Positioning

*How buyers perceive you versus them — in promise, emotion, and mental association, not capability.*

- **Frameworks:** Ries & Trout positioning theory (the battle is for the buyer's mind); perceptual
  mapping (price vs. value-perception plots; find the uncontested space); Blue Ocean strategy canvas.
- **Run:** contrast their *stated* positioning (Step 2 snapshots) against *customer language* (Step 3
  review mining); draft or revise with [`positioning-statement`](../positioning-statement/SKILL.md).
- **Watch for:** the promise-delivery gap — where a competitor's marketing writes checks their reviews
  say they don't cash. That gap is a positioning counter-move waiting to be claimed.

### Step 6: Competitors' Strategic Direction

*Where they're going, not where they are — the step that lets you preempt instead of react.*

- **Frameworks:** Hamel & Prahalad's strategic intent (read the ambition behind the moves); the
  Innovation Ambition Matrix (core/adjacent/transformational mix of their bets).
- **Run:** the forward-looking disciplines in
  [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md) — TECHINT
  (patent clusters, trademark filings, preprints), HUMINT (hiring surges, leadership moves), FININT
  (earnings language, M&A themes), MASINT (supply chain, facility buildout) — fused via the
  confidence-stacking rule. [`competitive-intel-watch`](../competitive-intel-watch/SKILL.md) keeps
  this step running on a cadence after the initial pass.
- **Watch for:** single-signal panic. One patent is exploration; a cluster plus a hiring surge plus a
  subdomain cert is a committed bet. Stack before you brief.

### Step 7: Produce the Outputs

Close by building what the audience consumes — offer as a numbered menu:

1. **Battle cards** for the field — [`battle-card-builder`](../battle-card-builder/SKILL.md)
2. **Executive comparison matrix** — from Step 2's snapshot
3. **Positioning counter-moves** — from Step 5's gap analysis
4. **Threat assessment brief** — Step 6's fused signals, with confidence levels and recommended responses

Then set the maintenance cadence: [`competitive-intel-watch`](../competitive-intel-watch/SKILL.md) on
the schedule the artifact mapping in `intelligence-collection-disciplines` prescribes (weekly SIGINT
layer for cards, quarterly deep passes for direction).

A copy/paste engagement tracker for all seven steps lives in [`template.md`](template.md).

## Examples

**Scoping to the decision (fictional):** the decision is deal defense against one rival in enterprise
deals. The right subset is Steps 2, 3, and 5 on that one competitor, straight into a battle card —
Steps 1, 4, and 6 add days, not win-rate. The orchestrator's value is *permission to skip*: "Based on
your decision, I recommend Steps 2→3→5 only. Run the full six?
1. Yes, deal defense scope (2, 3, 5 → battle card)
2. Add Step 6 — they've been acquiring lately and I want the direction read
3. Full six-step pass
4. Something else"

**Step 6 catching what Steps 1-5 missed:** the present-state read shows a competitor stable and
mid-pack. The direction pass finds a patent cluster in a new classification, four platform-engineer
postings, and an earnings call where the CFO declined to break out R&D — three disciplines, one story:
a platform pivot in progress. The threat assessment brief re-ranks them from "monitor" to "act," a
quarter before their announcement would have forced a reactive scramble.

See [`examples/sample.md`](examples/sample.md) for a complete worked engagement (fictional
FSM-software market) showing the orchestration decisions — scoping menu, recorded skips, and
step-to-step compounding — with links into the delegated skills' own worked artifacts.
[`examples/sample-industrial.md`](examples/sample-industrial.md) shows the umbrella bending —
steps merged, one run out of order, cadence slowed — with each call's reasoning stated.

## Common Pitfalls

- **Running all six on autopilot.** The steps are a menu, not a mandate. Scope to the decision or the
  analysis ships after the decision got made without it.
- **Skipping Step 6.** Present-state analysis ages the moment it ships; direction analysis is what
  buys you a quarter of lead time. Teams that skip it are perpetually surprised on launch day.
- **Framework name-dropping.** Citing Five Forces without rating the forces, or Kano without
  classifying a single feature. A framework earns its mention by producing a judgment.
- **Analysis without outputs.** Six beautiful steps and no battle card, no matrix, no brief. Step 7
  isn't optional — research is only done when it names the artifact it changes.
- **One-time heroics.** A grand annual analysis that's stale by month three. The process ends by
  installing the watch cadence, or it didn't end — it just stopped.

## Failure Exits & Edge Cases

- **A delegated skill is not installed/unavailable** (e.g., `company-intel` missing from the mount):
  say so in one line and either run the step's frameworks inline as a reduced pass (label the output
  "inline reduced pass — not the delegated skill's full artifact") or record the step as skipped in the
  engagement tracker. Never silently substitute a lighter output for the named artifact.
- **No decision given:** ask once ("what does this analysis change — market entry, roadmap bet,
  positioning, deal defense?"); if unanswered, run Steps 1-2 as the default spine and mark Steps 3-6 as
  "pending decision" in the tracker instead of running all six on autopilot.
- **No existing intelligence in session:** Step 0 recommends starting from
  [`market-landscape-scan`](../market-landscape-scan/SKILL.md) to find the competitor set — scoping a
  six-step analysis on a guessed competitor list is the failure this exit prevents.
- **Time-boxed request ("need something by tomorrow"):** offer the deal-defense subset explicitly
  (Steps 2, 3, 5 → battle card, per the scoping example) rather than a thin version of all six.

### FAQ / Wrong way → fix

| Wrong | Fix |
|---|---|
| "Just run the whole process" on every request | Scope to the decision; recorded skips are the orchestrator's output, not laziness |
| Treating this skill as the analyzer | It orchestrates — each step names the skill that does the work; don't inline full research here |
| Citing Five Forces / Kano without producing ratings | A framework earns its mention by producing a judgment; otherwise drop the name |
| Ending at Step 5 because the brief shipped | Without Step 7's artifacts and the watch cadence, the analysis didn't end — it stopped |
| Dependency skill missing → quietly writing shallower prose instead | One-line disclosure + reduced-pass label or recorded skip (see failure exits) |

## 中文速览（Quick Guide）

**这个技能做什么**：端到端编排完整的竞争分析——六个分析步骤（市场格局/产品级对比/需求满足度/经营基线/感知定位/战略方向）各自委托给对应技能执行，本件管顺序、框架与取舍，最终收敛到四类可消费产出：战卡、高管对比矩阵、定位反制、威胁评估简报。

**何时用**：一个决策需要整幅竞争图景时（市场进入、路线图押注、定位刷新、交易防守），或真问题是"该跑哪几步、跳过哪几步"；单次快照或单张战卡不必动用本件。

**核心步骤**：
1. 定范围：确认决策与竞品集，按决策推荐六步的子集而非全跑；
2. 逐步执行并记录跳过项——每步引用的框架要产出判断，不空点名；
3. 不要跳过第 6 步（竞品战略方向）：多源信号堆叠置信度后再下结论；
4. 第 7 步必须落产出物（战卡/矩阵/反制/简报），并安装 watch 节律保持新鲜。

**国内可达性边界**：各步依赖被委托技能的外网源访问（官网、评测站、财报与专利库等）；某步的证据源不可达或付费墙挡住时，按正文出口降级为"inline reduced pass"并在产出中标注置信度，或在该步记录为跳过；可改用公开中文渠道（公开新闻、上市/挂牌公司公开披露、竞品中文官网）补证据并保留 Fact/Inference/Assumption 标签纪律。

## References

- [`market-landscape-scan`](../market-landscape-scan/SKILL.md) (Workflow) — Step 1
- [`competitive-research-snapshot`](../competitive-research-snapshot/SKILL.md) (Workflow) — Step 2
- [`voice-of-customer-miner`](../voice-of-customer-miner/SKILL.md) (Workflow) — Step 3
- [`company-intel`](../company-intel/SKILL.md) (Workflow) — Step 4
- [`positioning-statement`](../positioning-statement/SKILL.md) (Component) — Step 5
- [`competitive-intel-watch`](../competitive-intel-watch/SKILL.md) (Workflow) — Step 6 cadence + maintenance
- [`battle-card-builder`](../battle-card-builder/SKILL.md) (Workflow) — Step 7 output
- [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md) (Component) — signal channels throughout
- [`autonomous-investigation`](../autonomous-investigation/SKILL.md) (Workflow) — evidence discipline throughout
- External frameworks: Porter, *How Competitive Forces Shape Strategy* (HBR, 1979); Kano, attractive
  quality theory; Moore, *Crossing the Chasm* (Whole Product); Ulwick, Outcome-Driven Innovation;
  Osterwalder & Pigneur, *Business Model Generation*; Ries & Trout, *Positioning*; Hamel & Prahalad,
  *Competing for the Future* (HBR, 1994); Nagji & Tuff, *Managing Your Innovation Portfolio* (HBR, 2012)
- Adapted from Dean Peters' Competitive Analysis Playbook (Productside).

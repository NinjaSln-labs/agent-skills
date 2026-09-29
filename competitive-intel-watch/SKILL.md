---
name: competitive-intel-watch
description: >-
  Competitive Intel Watch: scheduled delta monitoring against a prior competitive
  snapshot. Use when tracking competitors on a cadence: material shifts only, cited
  evidence, battle-card update flags, runs unattended.
slug: competitive-intel-watch
version: 1.1.1
displayName: competitive-intel-watch
---

# Competitive Intel Watch

## Purpose

Monitor a competitive landscape for **material shifts** since the last run. Diff the world against the
previous snapshot; report only what changed, with evidence; flag which downstream artifacts need
updating. This is the skill that turns competitive research from a document into a cadence — the
weekly SIGINT sweep and monthly OSINT digest from the fusion cadence live here. A watch reports
*change*, not *state*: regenerating the same report weekly is theater, and "no material shifts this
cycle" is a valid, useful result.

## Input

**Works best with:** the previous Competitive Research Snapshot (pasted or attached) — the baseline
this run diffs against — and the competitor list (defaults to those in the snapshot).
**Also useful:** anything specific you're watching for this cycle, and a materiality bar adjustment if
the default needs tightening or loosening.

Input supplied inline with the invocation — text after the skill name, a pasted context dump, or an
appended `ARGUMENTS:` line — counts as answers already given. Use it against the question budget;
don't re-ask.

**Arriving empty-handed? That works too.** With no prior snapshot, the skill falls back to **baseline
mode**: it produces a first snapshot using the `competitive-research-snapshot` structure and stops —
the delta value starts on run two.

**Example invocation:** `Competitive intel watch — prior snapshot pasted below; this cycle I'm
specifically watching for pricing moves. [snapshot]`

## Key Concepts

- **Governing protocol:** honors the [`autonomous-investigation`](../autonomous-investigation/SKILL.md)
  contract — question budget of 2 (this skill's tightest), search-plan gate, Fact/Inference/Assumption
  labels, Just Enough Mode, stable schema, 4-option Final Step.
- **Discipline mix:** SIGINT first (site diffs, pricing pages, job posts — the freshest layer), with
  OSINT and HUMINT signals monthly and FININT on the quarterly pass — the fusion cadence in
  [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md) is this
  skill's operating rhythm.
- **The materiality bar.** Report a change only if a sales rep, pricing owner, or roadmap owner would
  plausibly act on it: pricing/packaging changes, launches and deprecations, positioning shifts,
  leadership moves, funding or M&A, major customer wins/losses, credible roadmap signals. Below the
  bar: cosmetic site changes, routine content marketing, minor releases. *Why it matters:* a watch
  that cries wolf gets ignored by cycle three — the bar is what keeps the audience.
- **Delta discipline.** Read the prior snapshot fully before searching; diff against it, never
  regenerate it. The empty changelog is a first-class outcome.
- **Update flags close the loop.** Research is only done when it names the artifact it changes — each
  material shift maps to the battle card, positioning, pricing, or roadmap sections now stale.
- **Do-not-invent list:** competitors, features, pricing, market share, customer wins, roadmap items,
  product claims. Every claimed change carries a URL *and a date*.
- **When NOT to use:** no baseline exists and you want the full treatment → run
  [`competitive-research-snapshot`](../competitive-research-snapshot/SKILL.md) first; the scope itself
  changed (new segment, pivot) → re-snapshot from scratch rather than diffing a stale scope.

## Application

1. **Determine mode.** Prior snapshot provided → delta mode. None → baseline mode: produce a
   snapshot per the `competitive-research-snapshot` schema and stop.
2. **Credit inline context**, then ask only the unanswered questions (max 2):
   1. Do you have the previous snapshot, or should I create a baseline?
   2. Anything specific you're watching for this cycle?
   If unanswered, proceed: baseline mode if no snapshot, default materiality bar otherwise.
3. **Read the prior snapshot fully before searching.** The diff target is the document, not your
   memory of the market.
4. **Show the 3-bullet search plan** — what you'll check per competitor, source types (company sites,
   pricing pages, release notes, press, investor materials, credible news, review sites, job
   postings), how facts will be separated from inference. Continue unless revised.
5. **Sweep and filter through the materiality bar.** When nothing clears it, say so plainly.
6. **Emit the schema below exactly** — runs must be diffable.

### Output schema (do not reorder)

~~~markdown
# Competitive Watch Report

## 1. Run Header
**Scope (from prior snapshot):** | **Prior snapshot date:** | **This run date:** | **Competitors checked:**

## 2. Changelog (Material Shifts Only)
For each material shift:
### [Competitor] — [4 to 8 word change summary]
- **What changed:** [1-2 bullets, labeled Fact/Inference]
- **Evidence:** [URL, date]
- **So what:** [why it clears the materiality bar]
- **Confidence:** [high / medium / low]

If nothing cleared the bar: "No material shifts this cycle." List
anything on the watchlist for next run.

## 3. Update Flags
| Downstream artifact | Sections needing update | Driven by |
|---|---|---|
| Battle card | | |
| Positioning statement | | |
| Pricing/packaging analysis | | |
| Roadmap assumptions | | |
Only rows with real updates; omit the rest.

## 4. Watchlist for Next Run
- [Signals below the bar but trending]
- [Open questions this run could not resolve]

### Assumptions to Validate
- [Assumption 1] / [Assumption 2] / [Assumption 3]
~~~

A copy/paste fill-in version of this schema, with quality checks, lives in [`template.md`](template.md).

### Final Step (offer exactly 4 options)

1. Update the battle card sections flagged above ([`battle-card-builder`](../battle-card-builder/SKILL.md))
2. Deep-dive the most significant change
3. Produce the refreshed full snapshot (new baseline)
4. Adjust the materiality bar or competitor list for next run

Accept `1`, `2`, `3`, `4`, `1 and 2`, `Verbose Mode`, or a custom path. On a scheduled, unattended
run, file the report and stop — the options wait for a human.

## Examples

**A changelog entry that clears the bar (fictional):**

> ### Ledgerline — mid-tier plan removed from pricing page
> - **What changed:** the $49 "Team" tier no longer appears; feature list redistributed upward —
>   **Fact** ([pricing page vs. archived version, Jul 2 vs. Jun 1](https://example.com/archive))
> - **Evidence:** URL + archive diff, dated
> - **So what:** entry price effectively doubled; our "cheaper to start" talking point is now
>   stronger, and their SMB churn may spike — clears the bar for both sales and pricing owners
> - **Confidence:** high

**The empty changelog done right:**

> No material shifts this cycle. Below-the-bar activity logged for trend: [Competitor B] published
> three thought-leadership posts on compliance automation (watchlist: possible positioning shift if
> their product pages follow), and two senior-engineer job posts mention a language we haven't seen
> in their stack before (watchlist: TECHINT corroboration needed before this means anything).

See [`examples/sample.md`](examples/sample.md) for a complete worked run (fictional FSM-software
market) that diffs against the `competitive-research-snapshot` example's baseline — including an
assumption from that baseline getting confirmed by the diff. [`examples/sample-industrial.md`](examples/sample-industrial.md)
shows the quarterly-cadence industrial version, where a top risk gets *demoted* and that's
reported as material.

## Common Pitfalls

- **Regeneration theater.** Producing a fresh full report each run and calling it a watch. The
  reader's question is "what changed?" — answer only that.
- **Materiality inflation.** Reporting blog posts and minor releases to seem productive. Every
  below-bar item reported costs credibility the real alerts will need later.
- **Fear of the empty changelog.** Padding a quiet cycle with noise. "No material change" backed by a
  real sweep is exactly what a healthy watch produces most cycles.
- **Undated evidence.** A change claim without both URL and date can't be verified *or diffed next
  run*. The date is half the evidence.
- **Diffing a stale scope.** The market pivoted, you entered a new segment — and the watch keeps
  diffing the old frame. Re-baseline when the scope changes; say so in the run header.
- **Orphaned intelligence.** A changelog with no update flags. If no artifact needs updating, the
  shift probably didn't clear the bar — flags are how research becomes action.

## Failure Exits & Edge Cases

- **No prior snapshot and none attached:** do not guess a baseline — switch to baseline mode, say so
  in one line ("No prior snapshot found; producing a first snapshot as baseline"), and stop after it.
  Delta reporting starts next run.
- **Malformed or mismatched prior snapshot** (truncated paste, wrong artifact, no dates): name what is
  wrong in one line and ask one targeted question ("This looks like a battle card, not a snapshot —
  paste the snapshot or say `baseline` to start over"). Never silently diff against a mismatched
  document.
- **No network / sources unreachable:** report which checks could not run in the Run Header
  ("Competitors checked: 3 of 5 — pricing pages unreachable"), label affected claims as Assumption,
  and put the missed checks on the watchlist — do not emit a changelog built from memory.
- **Competitor missing from the prior snapshot:** treat as a scope question — add it, mark
  "new competitor, no baseline" in its entry, and put "extend baseline" on the watchlist.

### Wrong way → fix

| Wrong | Fix |
|---|---|
| Diffing from memory because the snapshot is long | Re-read the snapshot; the diff target is the document |
| Inventing "probable" pricing moves to fill a quiet cycle | Empty changelog + watchlist entry |
| Swallowing a truncated input and proceeding | One-line diagnosis + one targeted question (max 2 total) |
| Reporting a below-bar blog post to look productive | Log it on the watchlist only |

## 中文速览（Quick Guide）

**这个技能做什么**：把竞争研究从一次性文档变成节律化监控——拿上一份快照做基线，diff 出"实质性变化"并逐条给带日期的证据，同时点名哪些下游工件（战卡、定价、路线图）因之过期；无实质变化时，空的 changelog 就是正确产出。

**何时用**：需要按周期（周扫/月报/季查）跟踪竞品动向时；没有基线快照就先用 `competitive-research-snapshot` 建基线。

**核心步骤**：
1. 判定模式：有前次快照→delta 模式；无→基线模式出首份快照即停；
2. 追问至多 2 问（有无快照、本轮特别关注什么）；
3. 先完整重读基线快照再搜索——diff 的是文档，不是记忆；
4. 出 3 条搜索计划，逐竞品扫过实质性门槛（定价/发布/定位/融资等）；
5. 按 schema 输出 changelog＋更新标记＋下轮观察名单。

**国内可达性边界**：依赖对竞品官网、定价页、发布说明、招聘页、新闻与投资者材料等外网源的访问；某源不可达时在 Run Header 写明"3/5 竞品已查、定价页不可达"，受影响断言标 Assumption，漏查项放进观察名单——不从记忆编造 changelog；可改用公开中文渠道（竞品中文官网、公开新闻稿）补查并保留同样的 URL+日期纪律。

## References

- [`autonomous-investigation`](../autonomous-investigation/SKILL.md) (Workflow) — the governing protocol
- [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md) (Component) — the fusion cadence this watch runs on
- [`competitive-research-snapshot`](../competitive-research-snapshot/SKILL.md) (Workflow) — produces the baseline this skill diffs against
- [`battle-card-builder`](../battle-card-builder/SKILL.md) (Workflow) — consumes the update flags
- PESTEL analysis (optional companion activity) — the macro-environment sibling of this competitor-level watch
- Adapted from `market-intelligence/competitive-intel-watch-prompt.md` in the
  `https://github.com/deanpeters/product-manager-prompts` repo.


---
name: voice-of-customer-miner
description: >-
  Mine public reviews, app stores, and forums for unmet needs, competitor weaknesses, and
  switching triggers — with quoted evidence. Use when you want customer voice without
  waiting on interviews.
slug: voice-of-customer-miner
version: 1.2.0
displayName: voice-of-customer-miner
---

# Voice-of-Customer Miner

## 中文速览（Quick Guide）

- **做什么**：从评论站、应用商店、Reddit 与从业者论坛等公开渠道挖掘客户原声，提炼未满足需求、竞品弱点与切换触发点。
- **何时用**：想不等访谈周期就拿到客户声音时；对象无公开足迹、需要私有区域自有用户声音、或需要统计置信度时不适用。
- **核心步骤**：①问最多 3 个问题（谁的声音、支撑什么决策、有无主题）并按假设推进；②过 search-plan 闸后做来源清扫；③逐条带 URL 抓原话；④按需求（而非功能）归主题并标注事实/推断/假设与来源偏差；⑤给 4 个下一步选项。
- **国内可达性**：正文指定的公开源以境外站点为主，部分（如 Reddit、应用商店评论）在国内不可直接访问；此时可改用国内可访问的公开社区与评论渠道，并保持同样的「原话 + URL + 偏差标注」纪律。

## Purpose

Mine public customer voice — review sites, app stores, Reddit and practitioner forums, community
boards — for unmet needs, competitor weaknesses, and switching triggers: **search plan → source sweep
→ verbatim capture → need themes → so what → next-step options.** This bridges competitive
intelligence and discovery: it delivers customers' exact words without waiting on an interview cycle.
But public voice skews toward the angry and the vocal, so every theme it surfaces is a *hypothesis to
validate*, never a verdict — the output's last stop is always a real conversation.

## Input

**Works best with:** the product(s) or competitor(s) to mine — yours, a rival's, or a set — and **the
decision this should inform**.
**Also useful:** a theme to focus on (onboarding, pricing, reliability) if you have one; otherwise the
sweep runs open.

Input supplied inline with the invocation — text after the skill name, a pasted context dump, or an
appended `ARGUMENTS:` line — counts as answers already given. Use it against the question budget;
don't re-ask.

**Arriving empty-handed? That works too.** The skill opens with at most 3 questions (whose voice,
what decision, theme or open sweep) and proceeds on labeled assumptions if they go unanswered.

**Example invocation:** `Mine voice-of-customer for [Competitor A] and [Competitor B], focus on
onboarding — informs whether our Q1 bet is a migration tool.`

## Key Concepts

- **Governing protocol:** honors the [`autonomous-investigation`](../autonomous-investigation/SKILL.md)
  contract — question budget of 3, search-plan gate, Fact/Inference/Assumption labels, Just Enough
  Mode, stable schema, 4-option Final Step. Discipline: OSINT's review-and-community layer (see
  [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md)).
- **Theme by need, not by feature.** "Exports are broken" is a feature complaint; "I can't get my
  data where my team works" is the underlying need. Theming by need is the same solution-free
  discipline as JTBD and painstorming — and it's what makes themes portable into discovery.
- **Verbatims are the product.** Short, real, quoted customer language with URLs. Verbatims teach
  persona language: the exact words customers use become interview probes and positioning copy.
  Never fabricate quotes, ratings, review counts, or reviewer roles.
- **Every source has a known skew.** Reviewers skew negative; vendor communities skew loyal; app
  stores over-represent update anger. Note the bias per source — public voice is evidence with a
  known skew, not ground truth.
- **Honest frequency.** *Recurring across sources* ≠ *concentrated in one thread* ≠ *isolated but
  vivid*. Say which; one articulate ranter is not a theme.
- **When NOT to use:** no meaningful public footprint (early-stage, niche enterprise) → run
  [`discovery-interview-prep`](../discovery-interview-prep/SKILL.md) instead; you need *your* users'
  voice on a private area → mine your own tickets and research; statistical confidence required →
  this is qualitative theming.

## Application

1. **Credit inline context**, then ask only the unanswered questions (max 3):
   1. Whose customer voice — yours, a competitor's, or a set?
   2. What decision should this inform?
   3. Any specific theme to focus on, or open sweep?
2. **Show the 3-bullet search plan** — which voice sources you'll sweep, how you'll select
   representative verbatims, how observation will be separated from interpretation. Continue unless
   revised.
3. **Sweep mixed voice sources** — review sites (G2, Capterra, TrustRadius), app stores, Reddit and
   practitioner forums, community boards, social threads — capturing short real quotes with URLs and
   noting each source's bias.
4. **Emit the schema below exactly.**

### Output schema (do not reorder)

~~~markdown
# Voice-of-Customer Snapshot

## 1. Scope
**Products mined:** | **Decision supported:** | **Sources swept:** | **As-of date:**

## 2. Need Themes
For each of the top 3-5 themes:
### Theme: [Underlying need, solution-free, 4 to 8 words]
- **Frequency:** [recurring across sources / concentrated / isolated]
- **Verbatim:** "[short real quote]" — [source, URL]
- **Verbatim:** "[short real quote]" — [source, URL]
- **Who says it:** [role/segment, if evident — labeled]
- **Reading:** [Inference — what this suggests]

## 3. Competitor Weak Points
- **[Competitor]:** [weakness in customers' words; frequency; URL]
- [Max 5, strongest evidence only]

## 4. Switching Triggers
- [What pushes customers off a product; what pulls them; labeled, cited]

## 5. So What?
- **3** opportunity hypotheses (phrased as problems, not features)
- **2** battle-card-ready weaknesses (with evidence quality noted)
- **3** assumptions to validate in real interviews
Each bullet: label, confidence, URL where relevant.
~~~

A copy/paste fill-in version of this schema, with quality checks, lives in [`template.md`](template.md).

### Final Step (offer exactly 4 options)

1. Generate discovery interview questions from the top theme ([`discovery-interview-prep`](../discovery-interview-prep/SKILL.md))
2. Feed the weaknesses into a competitive battle card ([`battle-card-builder`](../battle-card-builder/SKILL.md))
3. Organize the top unmet needs into an opportunity → solution tree, then hand that tree to
   downstream opportunity/solution decomposition
4. Re-run scoped to one theme in Verbose Mode

Accept `1`, `2`, `3`, `4`, `1 and 2`, `Verbose Mode`, or a custom path.

## Examples

**A theme done right (fictional product, illustrative verbatims):**

> ### Theme: getting historical data out at contract end
> - **Frequency:** recurring — 9 reviews across two sites plus a forum thread, past 6 months
> - **Verbatim:** "export took three support tickets and still dropped custom fields" — [G2-style review, URL]
> - **Verbatim:** "we stayed a year longer than we wanted because leaving meant losing our audit trail" — [forum thread, URL]
> - **Who says it:** ops managers at 50-200-person firms — **Inference** (reviewer titles where shown)
> - **Reading:** exit friction is functioning as involuntary retention — **Inference**; a rival with
>   effortless migration turns this from their moat into their churn event.

Notice the theme name contains no feature ("export tool") — it names the need, so discovery can
explore solutions the reviews never imagined.

See [`examples/sample.md`](examples/sample.md) for a complete worked mining run (fictional
FSM-software market) where frequency honesty caps a vivid theme at low confidence and each
source's bias becomes a reading instruction. [`examples/sample-industrial.md`](examples/sample-industrial.md)
shows the thin-voice case — what honest mining looks like when the market barely posts reviews.

## Common Pitfalls

- **Feature-name theming.** Clustering by the feature customers blame instead of the need underneath
  hands your roadmap to the loudest UI complaint.
- **Verbatim laundering.** Paraphrasing a review and quoting it. If it has quote marks, it must be a
  real excerpt at a real URL — this domain's do-not-invent list exists because fabricated customer
  quotes are both tempting and toxic.
- **Rant amplification.** One vivid one-star review presented as a theme. Frequency honesty is the
  discipline: recurring, concentrated, or isolated — say which.
- **Skew blindness.** Reading review sites as a census. The angry and the vocal are over-sampled;
  the satisfied-and-silent majority never posts. Bias notes per source are mandatory.
- **Skipping the validation handoff.** Shipping themes straight into the roadmap. The output's
  "assumptions to validate in real interviews" section is the bridge to discovery — use it.

## When Sources Are Out of Reach (Failure Exits)

- **Review sites unreachable or paywalled (G2, Capterra, app stores):** Say which sources failed and switch to what is reachable — user-provided review exports, support tickets, community archives, or locally accessible sources the user nominates (for Chinese markets: practitioner forums, Zhihu-style Q&A, app store CN listings). Same sweep discipline applies; note each substitute source's skew like any other.
- **Not a single verbatim URL captured:** Stop and say so. Do not emit a theme with zero verbatims — paraphrased "quotes" are verbatim laundering (see Pitfalls). The honest deliverable is "no public voice found; here is what to do instead" → run `discovery-interview-prep`.
- **Thin-voice market:** Follow the `examples/sample-industrial.md` pattern — fewer themes, lower confidence caps, explicit absence-of-evidence notes; never pad frequency claims to look busy.
- **Garbage or contradictory input** (gibberish product names, conflicting decisions): Ask one clarifying question naming the specific contradiction; if it stays unclear, proceed only on labeled Assumptions and mark the whole run's confidence accordingly — do not silently guess.

## FAQ (Wrong → Right)

| Wrong | Right |
|-------|-------|
| Clustering by feature ("export complaints") | Theme by underlying need ("getting data out at contract end") — the name should survive solution changes |
| Paraphrasing a review into a "quote" | Only real excerpts at real URLs get quote marks; everything else is a labeled summary |
| Treating one vivid rant as a theme | Label frequency honestly: recurring across sources / concentrated / isolated |
| Feeding themes straight into the roadmap | Themes are hypotheses; the "assumptions to validate in real interviews" section is the required bridge |
| Trusting the source mix as representative | Every source has a skew (reviewers negative, vendor communities loyal) — bias note per source is mandatory |

## References

- [`autonomous-investigation`](../autonomous-investigation/SKILL.md) (Workflow) — the governing protocol
- [`intelligence-collection-disciplines`](../intelligence-collection-disciplines/SKILL.md) (Component) — OSINT review-mining sources and bias tradecraft
- [`jobs-to-be-done`](../jobs-to-be-done/SKILL.md) (Component) — the solution-free framing themes should land in
- [`discovery-interview-prep`](../discovery-interview-prep/SKILL.md) (Interactive) — where the validation happens
- Opportunity solution tree (external optional reference, not installed here) — structures the opportunity hypotheses
- [`battle-card-builder`](../battle-card-builder/SKILL.md) (Workflow) — consumes the weak points
- Adapted from `market-intelligence/voice-of-customer-miner-prompt.md` in the
  `https://github.com/deanpeters/product-manager-prompts` repo.


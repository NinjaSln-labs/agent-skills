---
name: jobs-to-be-done
description: >-
  Uncover customer jobs, pains, and gains in a structured JTBD format. Use when clarifying
  unmet needs, repositioning a product, or improving discovery and messaging.
slug: jobs-to-be-done
version: 1.1.1
displayName: jobs-to-be-done
---

# Jobs To Be Done

## Purpose
Systematically explore what customers are trying to accomplish (functional, social, emotional jobs), the pains they experience, and the gains they seek. Use this framework to uncover unmet needs, validate product ideas, and ensure your solution addresses real motivations—not just surface-level feature requests.

This is not a survey—it's a structured lens for understanding *why* customers "hire" your product and what would make them "fire" it.

## Input

**Works best with:** The customer segment (or product whose customers) you're analyzing.
**Also useful:** Interview notes, support tickets, or research to mine for jobs, pains, and gains; the situation or trigger you care about.

Anything supplied with the invocation itself — text after the skill name, a pasted context dump, or an appended `ARGUMENTS:` line — counts as answers already given. Use it and skip whatever it covers; don't re-ask.

**Arriving empty-handed? That works too.** The skill asks who the customer is and what progress they're trying to make before structuring the JTBD breakdown.

**Example invocation:** `Run JTBD for freelance designers using our invoicing tool — here are 6 interview summaries.`

## Key Concepts

### The Jobs-to-be-Done Framework
Influenced by Clayton Christensen and the Value Proposition Canvas (Osterwalder), JTBD breaks customer needs into three categories:

**1. Customer Jobs:**
- **Functional jobs:** Tasks customers need to perform (e.g., "send an invoice")
- **Social jobs:** How customers want to be perceived (e.g., "look professional to clients")
- **Emotional jobs:** Emotional states customers seek or avoid (e.g., "feel confident in my work")

**2. Pains:**
- **Challenges:** Obstacles customers face
- **Costliness:** What's too expensive in time, money, or effort
- **Common mistakes:** Errors customers make that could be prevented
- **Unresolved problems:** Gaps in current solutions

**3. Gains:**
- **Expectations:** What would exceed current solutions
- **Savings:** Time, money, or effort reductions that delight
- **Adoption factors:** What increases likelihood of switching
- **Life improvement:** How a solution makes life easier or more enjoyable

### Why This Structure Works
- **Separates job from solution:** "Communicate with my team" (job) ≠ "email" (solution)
- **Reveals underlying motivations:** Functional job may be "track expenses," but emotional job is "feel in control of finances"
- **Surfaces competition you didn't see:** Customers "hire" non-obvious alternatives (pen and paper, spreadsheets, workarounds)
- **Prioritizes by intensity:** Not all pains are equal—focus on the most acute

### Anti-Patterns (What This Is NOT)
- **Not a feature wishlist:** "I want AI, automation, and dashboards" is not a job
- **Not demographics:** "Millennials want mobile-first" is a persona trait, not a job
- **Not generic:** "Be more productive" is too vague—dig into *which* tasks and *why*
- **Not one-dimensional:** Focusing only on functional jobs misses social/emotional motivations

### When to Use This
- Early-stage discovery (before you know the solution)
- Validating product-market fit (does your solution address the right jobs?)
- Prioritizing roadmap (which jobs are most painful/important?)
- Competitive analysis (what are customers "hiring" competitors for?)
- Marketing messaging (speak to jobs, not features)

### When NOT to Use This
- After you've already built the product (too late for discovery)
- For trivial features (don't over-analyze small tweaks)
- As a substitute for quantitative validation (JTBD informs hypotheses; data validates them)

---

## Application

Use `template.md` for the full fill-in structure.

### Step 1: Define the Context
Before exploring JTBD, clarify:
- **Target customer segment:** Who are you studying? (reference [`proto-persona`](../proto-persona/SKILL.md))
- **Situation:** In what context does the job arise? (e.g., "When managing a project deadline...")
- **Current solutions:** What do they use today? (competitors, workarounds, doing nothing)

**If missing context:** Conduct customer interviews, contextual inquiries, or "switch interviews" (why they switched from a previous solution).

---

### Step 2: Explore Customer Jobs
Functional / Social / Emotional jobs — each with the interview ask, fill-in template, examples, and quality checks (full tables: [references/jtbd-methods.md](references/jtbd-methods.md)).

---

### Step 3: Identify Pains
Four pain lenses — Challenges / Costliness / Common Mistakes / Unresolved Problems, each with ask, template, and examples (full tables: [references/jtbd-methods.md](references/jtbd-methods.md)).

---

### Step 4: Uncover Gains
Four gain lenses — Expectations / Savings / Adoption Factors / Life Improvement, each with ask, template, and examples (full tables: [references/jtbd-methods.md](references/jtbd-methods.md)).

---

### Step 5: Prioritize and Validate

- **Rank pains by intensity:** Which pains are acute vs. mild annoyances?
- **Identify must-have vs. nice-to-have gains:** What would drive adoption vs. what's just a bonus?
- **Cross-reference with personas:** Do different personas have different jobs/pains/gains? (reference [`proto-persona`](../proto-persona/SKILL.md))
- **Validate with data:** Survey a broader audience to confirm JTBD insights from interviews

---

## Examples

See `examples/sample.md` for full JTBD examples.

Mini example excerpt:

```markdown
**Functional Jobs:** Coordinate tasks across a distributed team
**Pains - Challenges:** Team members use different tools, creating silos
**Gains - Savings:** Reduce status reporting time from 3 hours to 15 minutes
```

---

## Common Pitfalls

### Pitfall 1: Confusing Jobs with Solutions
**Symptom:** "I need to use Slack" or "I need AI-powered analytics"

**Consequence:** You've anchored on a solution, not the underlying job.

**Fix:** Ask "Why?" 5 times. "I need Slack" → "Why?" → "To communicate with my team" → "Why?" → "To get quick answers" → "Why?" → "To avoid project delays."

---

### Pitfall 2: Generic Jobs
**Symptom:** "Be more productive" or "Save time"

**Consequence:** Too vague to inform product decisions.

**Fix:** Get specific. "Save time" → "Reduce time spent generating monthly reports from 8 hours to 1 hour."

---

### Pitfall 3: Ignoring Social/Emotional Jobs
**Symptom:** Only documenting functional jobs

**Consequence:** You miss powerful motivators. People often buy based on emotional/social needs, not just functional.

**Fix:** Explicitly ask about perception and emotions in interviews. "How would solving this make you feel?" "Who would notice if you solved this?"

---

### Pitfall 4: Fabricating JTBD Without Research
**Symptom:** Filling out the template based on assumptions

**Consequence:** You're guessing. JTBD analysis is only valuable if grounded in real customer insights.

**Fix:** Conduct "switch interviews" (ask why they switched from a previous solution), contextual inquiries, or problem validation interviews.

---

### Pitfall 5: Treating All Pains as Equal
**Symptom:** Listing 20 pains without prioritization

**Consequence:** No clarity on what to solve first.

**Fix:** Rank pains by intensity (acute vs. mild). Ask "If we only solved one pain, which would have the biggest impact?"

---

## Failure Exits & Edge Cases

- **No customer data at all (empty-handed):** ask the two opening questions (who is the customer, what
  progress are they making). If they go unanswered, produce the JTBD skeleton with every entry labeled
  **Assumption** and a top-of-output note "unvalidated — mine interviews/tickets before acting on any
  row." Do not present assumed jobs as findings.
- **Only feature requests in the input** ("add AI, add dashboards"): treat them as raw material, not
  jobs — run each through the Pitfall 1 "Why?" ladder and record the job it points to; say in one line
  that the input was feature-shaped.
- **Interview material contradicts the persona:** report the conflict (which source says what) rather
  than averaging it; conflicting jobs by segment are a prioritization input, not noise.
- **Segment too broad to analyze** ("everyone who needs invoicing"): ask once for a narrower segment or
  trigger situation; if declined, split the output by the segments present in the data and mark the
  split as an assumption.

### Wrong way → fix (quick reference)

| Wrong | Fix |
|---|---|
| Copying verbatims into the jobs section unchanged | Translate each into a verb-driven, solution-agnostic job statement |
| Every pain marked "high intensity" | Rank: pick the one pain whose absence would block the job entirely |
| Emotions invented to fill the template | Leave the row empty or quote a real customer sentence |
| JTBD treated as final validation | It produces hypotheses; quantitative validation comes after (see When NOT to Use) |

## 中文速览（Quick Guide）

**这个技能做什么**：用 JTBD 框架结构化挖掘客户"要完成的事"（功能/社交/情感三类任务）、痛点与期望收益——把功能请求还原成背后的任务，把痛点按强度排序，产出可验证的未满足需求假设，而非问卷报告。

**何时用**：澄清未满足需求、重新定位产品、改进发现访谈与营销话术时；产品定型后复盘或琐碎小功能分析不适用。

**核心步骤**：
1. 定上下文：目标客群、触发情境、现用替代方案（含"换用访谈"）；
2. 分三类探索客户任务（功能/社交/情感），每条用"为什么"追问到解决方案无关层；
3. 四个视角识别痛点（障碍/代价/常见错误/未解决问题），按强度排序；
4. 四个视角挖掘收益（期望/节省/采用因素/生活改善）；
5. 交叉验证人设差异，用更大样本定量验证——JTBD 出假设，数据下结论。

**国内可达性边界**：主流程可离线完成，无境外服务依赖——框架与模板均为仓内本地文件；References 所列书目为出处说明，不参与执行，无需在线获取。

## References

### Related Skills
- [`proto-persona`](../proto-persona/SKILL.md) — Defines who has these jobs/pains/gains
- [`problem-statement`](../problem-statement/SKILL.md) — JTBD informs the "Trying to" and "But" sections
- [`positioning-statement`](../positioning-statement/SKILL.md) — JTBD informs the "that need" statement

### External Frameworks
- Clayton Christensen, *Competing Against Luck* (2016) — Origin of Jobs-to-be-Done theory
- Tony Ulwick, *Outcome-Driven Innovation* (2016) — Quantifying jobs and outcomes
- Alexander Osterwalder, *Value Proposition Canvas* (2014) — Customer jobs/pains/gains framework

### Dean's Work
- [Link to relevant Dean Peters' Substack articles if applicable]

### Provenance
- Adapted from `prompts/jobs-to-be-done.md` in the `https://github.com/deanpeters/product-manager-prompts` repo.

---

**Skill type:** Component
**Suggested filename:** `jobs-to-be-done.md`
**Suggested placement:** `/skills/components/`
**Dependencies:** References [`proto-persona`](../proto-persona/SKILL.md)
**Used by:** [`positioning-statement`](../positioning-statement/SKILL.md), [`problem-statement`](../problem-statement/SKILL.md), epic hypothesis statements

---
name: workshop-facilitation
description: >-
  Facilitate workshop sessions in a one-step, multi-turn flow. Use when an interactive
  skill needs consistent pacing, options, and progress tracking.
slug: workshop-facilitation
version: 1.1.1
displayName: workshop-facilitation
---

# Workshop Facilitation

## Purpose
Provide the canonical facilitation pattern for interactive skills: one step at a time, with clear progress, adaptive recommendations at decision points, and predictable interruption handling.

## Input

**Nothing required** — this skill defines the facilitation protocol other interactive skills follow.
**Also useful:** If invoked standalone, name the session you want facilitated and any context for it; that context carries into the session as answers already given.

Anything supplied with the invocation itself — text after the skill name, a pasted context dump, or an appended `ARGUMENTS:` line — counts as answers already given. Use it and skip whatever it covers; don't re-ask.

**Arriving empty-handed? That works too.** When another skill references this protocol, that skill's Input section governs what to provide.

**Example invocation:** `Facilitate a 45-minute retro on our failed beta product launch using this protocol.`

## Key Concepts
- **One-step-at-a-time:** Ask a single targeted question per turn.
- **Session heads-up + entry mode:** Start by setting expectations and offering `Guided`, `Context dump`, or `Best guess` mode.
- **Progress visibility:** Show user-facing progress labels like `Context Qx/8` and `Scoring Qx/5`.
- **Decision-point recommendations:** Use enumerated options only when a choice is needed, not after every answer.
- **Quick-select response options:** For regular context/scoring questions, provide concise numbered answer options plus `Other (specify)` when useful.
- **Flexible selection parsing:** Accept `#1`, `1`, `1 and 3`, `1,3`, or custom text, then synthesize multi-select choices.
- **Context-aware progression:** Build on previous answers and avoid re-asking resolved questions.
- **Interruption-safe flow:** Answer meta questions directly (for example, "how many left?"), restate status, then resume.
- **Fast path:** If the user requests a single-shot output, skip multi-turn facilitation and deliver a condensed result.

## Application
1. Start with a brief heads-up on estimated time and number of questions.
2. Ask the user to choose an entry mode:
   - `1` Guided mode (one question at a time)
   - `2` Context dump (paste known context; skip redundancies)
   - `3` Best guess mode (infer missing details and label assumptions)
3. Run one question per turn and wait for an answer before continuing.
4. Keep questions plain-language; include a short example response format when helpful.
5. Show progress each turn:
   - `Context Qx/8` during context collection
   - `Scoring Qx/5` during assessment/scoring
6. Ask follow-up clarifications only when they materially improve recommendation quality.
7. For regular context/scoring questions, offer quick-select numbered response options when practical:
   - Keep options concise and mutually exclusive when possible.
   - Include `Other (specify)` if likely answers are open-ended.
   - Accept multi-select responses like `1,3` or `1 and 3`.
8. Provide numbered recommendations only at decision points:
   - after context synthesis,
   - after maturity/profile synthesis,
   - during priority/action-plan selection.
9. Accept numeric or custom choices, synthesize multi-select choices, and continue.
10. If interrupted by a meta question, answer directly, then restate progress and pending question.
11. If the user says stop/pause, halt immediately and wait for explicit resume.
12. End with a clear summary, decisions made, and (if best guess mode was used) an `Assumptions to Validate` list.

## Examples
**Opening:**
"Quick heads-up: this should take about 7-10 minutes and around 10 questions. How do you want to start?
1. Guided mode
2. Context dump
3. Best guess mode"

**User:** "2"

**Facilitator:** "Paste what you already know. I’ll skip answered areas and ask only what’s missing."

**Decision point after synthesis:**
1. **Prioritize Context Design** (Recommended)
2. Prioritize Agent Orchestration
3. Prioritize Team-AI Facilitation

**User:** "1 and 3"

**Facilitator:** "Great. We’ll run Context Design first, with Team-AI Facilitation in parallel."

**Inline input at invocation:** when the user supplies context with the invocation itself, credit it as answers, open at the first unanswered question, and keep progress labels honest (start at `Context Q2/6` if Q1 was covered). Full transcript, including the re-asking anti-pattern: [examples/inline-input-flow.md](examples/inline-input-flow.md).

## Common Pitfalls
- Asking multiple questions in the same turn.
- Offering recommendations after every answer (creates interaction drag).
- Using shorthand labels without plain-language questions.
- Hiding progress, so users don't know how much remains.
- Ignoring the user's chosen option or custom direction.
- Failing to label assumptions when running in best-guess mode.

## Failure & Edge-Case Handling (observable exits)

Each case below has a visible facilitator behavior — never silently improvise:

- **Unparseable answer** (user input matches no option and reads as off-topic, e.g. "banana" or a paste of unrelated logs): restate the pending question, quote what you received, and ask whether it was meant as an answer to this question or context for later. Observable exit: the same question is re-asked with the received text quoted — never skip or guess an option mapping for it.
- **Multi-select ambiguity** (`1 and 3` where options are mutually exclusive): name the conflict in one sentence, ask the user to pick one or confirm combining.
- **Empty / no input at invocation**: fall back to the entry-mode offer (Guided / Context dump / Best guess). Do not stall waiting for input that was never required.
- **Stop / pause**: halt immediately, print `Paused at <label> Qx/N`, and wait for explicit resume. On resume, restate that label and the pending question before continuing.
- **User wants to skip a question**: record it as skipped, show `Context Qx/N (1 skipped)`, and carry it into the `Assumptions to Validate` list if best-guess fills it.
- **Session exceeds the announced question count**: say so before continuing ("this needs 2 more questions than announced — continue?"), never just keep going.

## Boundary / NOT for

- **Single-shot deliverables** (user says "just give me the result") → use the Fast path; multi-turn facilitation is wrong here.
- **Pure execution tasks** with no user decisions (run tests, fix a build) → this protocol adds drag, don't apply it.
- **Not a knowledge source**: this skill defines *how* to facilitate; it contributes no domain questions. If invoked standalone without a session named, ask what to facilitate — that request is the exit for an empty invocation.
- **Backend/automated pipelines**: no human is answering turns; the protocol does not apply.

## FAQ / Wrong Way → Fix

| Wrong way | Fix |
|-----------|-----|
| Re-asking something the user already put in the invocation text | Inline input counts as answers given — skip covered questions and keep progress labels honest (start at `Context Q2/6` if Q1 was covered) |
| Asking 2-3 questions in one turn "to save time" | One targeted question per turn, always |
| Offering numbered recommendations after every answer | Recommendations only at decision points (after synthesis, at priority selection) |
| Interpreting a vague answer as option "1" because it's close enough | Quote the input back, ask the user to confirm or correct — never map silently |
| Continuing the queue after "stop" with "just one more quick one" | Halt immediately; resume only on explicit request |
| Best-guess mode without labeling | Every inferred answer goes into the closing `Assumptions to Validate` list |

## 中文速览（Quick Guide）

- **做什么**：定义交互式技能的引导协议：一次只问一步、显示进度标签、仅在决策点给枚举选项、可被打断且支持单次快速输出。
- **何时用**：需要多轮交互、稳定节奏与进度跟踪的技能或工作坊会话（可独立调用，也常作为其它交互技能的协议底座）。
- **核心步骤**：①开场预告时长与问题数 ②选入口模式（Guided / Context dump / Best guess） ③逐步提问并给编号快捷选项 ④回答元问题后复述进度再继续 ⑤结束给出待验证假设清单。
- **国内可达性**：主流程离线可完成，无境外服务依赖。

## References
- Use as the source of truth for interactive facilitation behavior.
- Apply alongside workshop skills in `skills/*-workshop/SKILL.md` and advisor-style interactive skills.

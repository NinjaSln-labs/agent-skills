---
name: problem-resolution-flow
description: >-
  Problem Resolution Flow: end-to-end evidence-driven pipeline from symptom to shipped
  fix — locate, trace root cause, classify by type, scope, grade severity, draft before
  research, cross-validate externally, decide workaround vs permanent fix, fix with a
  failing test, verify, close the loop with a no-blame lesson. Use when handling any bug,
  UX complaint, or behavior gap, before jumping to fixes. NOT for: root-cause
  investigation alone (use systematic-debugging) or the evidence-first intake
  methodology (use problem-dive).
---

# Problem Resolution Flow

## Core Principle

Every fix must be traceable back to evidence. **Never patch the symptom.** If the same
symptom is fixed three times, stop and question the design.

## The Flow

```
① LOCATE     — evidence first: error message → logs → reproduced behavior → which component
② TRACE      — follow the data/call chain back to the original trigger (root-cause-tracing)
③ CLASSIFY   — problem type: single-point / logic error / interaction UX / design or architecture
④ SCOPE      — line / function / module / project → determines fix depth
⑤ SEVERITY   — grade impact × urgency (grading table) → sets the response path
⑥ DRAFT      — form your own solution before looking outward
⑦ RESEARCH   — external evidence by type (competitor behavior / user logs / official or academic
               docs); key claims cross-validated across 2+ independent channels
⑧ DECIDE     — workaround vs permanent fix (decision rules); a shipped workaround must
               keep a tracked permanent-fix item
⑨ FIX        — TDD: write a failing test first, then the minimum change
⑩ VERIFY     — run the verifier (a check that produces pass/fail); full regression stays green
⑪ CLOSE      — refill tickets / handoff deltas / write a no-blame one-line lesson;
               recurring symptoms become a tracked problem with a known-error note
               (reusable knowledge for the next occurrence)
```

## Severity Grading（行业对齐）

| 级 | 含义 | 响应 |
|----|------|------|
| **P0** | 阻断全部用户 / 数据损坏 / 安全事件 | 立即处理，停止常规工作；先恢复服务再深挖；修复+验证+复盘 |
| **P1** | 主要路径不可用（核心功能挂） | 尽快处理；workaround 恢复优先，永久修复跟进 |
| **P2** | 次要功能受损 / 体验明显劣化 | 常规处理，按计划修复 |
| **P3** | 小瑕疵 / 边缘场景 | 可排队，随版本修复 |

- 影响面判断基于**证据**（日志/复现/用户报告数量），不凭感觉。
- **升级路径**：处理中发现影响面扩大（更多用户/数据风险）→ 升级严重度并告知相关方。
- **Incident vs Problem**（ITIL 语义）：P0/P1 是**事件**——先恢复服务（回滚/flag/降级），根因调查可延后；根因治理是**问题**——恢复不等于结束，问题条目必须继续直到永久修复或裁决。

## Rules

- **No fix without location.** If you cannot say which component and which flow step
  fails, you are not ready to fix.
- **3 strikes = upgrade.** Fixing the same symptom 3+ times means the problem is one
  level up: single-point → module → design. Stop and question the architecture — and
  when you do, look for systemic factors (environment/process/tooling), not a single
  scapegoat "root cause" (complex failures are usually multi-factor).
- **Scope discipline.** Fix at the scope the type demands — no bigger, no smaller.
  A single-point bug gets a line fix, not a refactor.
- **Draft before research.** Think first; research validates or refutes, it does not
  replace thinking.
- **Research is not optional for UX problems.** Interaction/design gaps need competitor
  comparison + user-log evidence, not just code reading.
- **Dual-channel verification.** Key external claims must match across 2+ independent
  search channels; conflicting channels are the most valuable signal — dig.
- **Workaround is a state, not an exit.** A workaround restores service; the permanent
  fix keeps a tracked item (ticket/audit item) until shipped and verified.
- **Ship with a test.** The fix is not done until the failing test passes and the suite
  stays green (verification-before-completion).
- **Recovery over blame.** When service is down, restore first, investigate depth second;
  post-incident, write a no-blame lesson (one line into the handoff/decision log) —
  blame kills the lesson, and the lesson is the product.

## Workaround vs Permanent Fix（决策表）

| 情形 | 决策 |
|------|------|
| P0/P1、根因未明 | 先 workaround 恢复（回滚/feature flag/降级路径），根因调查继续 |
| 根因已知但修复风险高（改动大/影响面广） | workaround + 永久修复排期（跟踪项必建） |
| 根因已知、修复小且可测 | 直接永久修复（TDD） |
| 同一症状第 3 次 workaround | 停止 workaround——升级为设计/系统问题（3 strikes 规则） |

**放行控制**：修复合入前过本技能 VERIFY；发布/放行（灰度、flag 切换、生产变更）是独立决策——变更前确认有回滚预案（改了什么可回退、回退命令是什么）。

## Anti-patterns

- Patching the symptom and declaring done
- Skipping classification and scope ("just fix it")
- Single-channel research conclusions
- Fixing beyond the scope (refactoring while fixing a typo)
- No regression check before closing
- Workaround without a tracked permanent fix
- Restoring service and calling it done (incident closed, problem still open)
- Blame in post-incident write-ups (kills the lesson)
- Deploying a fix with no rollback plan

## Relationship to sibling skills

- `problem-dive` — intake methodology when a problem/UX complaint arrives: evidence first,
  do not start fixing. This skill takes over once the problem is understood and a fix
  path is chosen.
- `systematic-debugging` — code root-cause investigation (observe → hypothesize → test →
  fix) for the code-bug path inside ①-③. Use both: systematic-debugging for root cause,
  this skill for the end-to-end flow.
- `audit-item` — tracked permanent fixes / follow-ups land as audit items so gates can
  enumerate them.

## Methodology Sources（2026-08 调研）

- SRE incident lifecycle（detect→respond→remediate→recover→learn）与 blameless postmortem：Google SRE Book（sre.google/sre-book/postmortem-culture）
- ITIL 4：incident vs problem、major incident 路径（Atlassian ITSM 文档）
- Severity 分级：行业 P0-P3 惯例；IEEE 1044 缺陷严重度/优先级矩阵
- 缺陷成本定律：Boehm（修复成本随阶段指数增长——越早修越便宜）
- 修复质量：修复引入回归缺陷的实证研究（arXiv 2207.01942）
- 根因批判视角：David Woods「root cause is a myth」（复杂系统事故多因素）；Hollnagel ETTO 原则（erikhollnagel.com）——支撑 3 strikes 升级到系统层、拒绝替罪式单一根因

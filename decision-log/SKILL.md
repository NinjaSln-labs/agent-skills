---
name: decision-log
description: >-
  Record or query architecture decision records (ADR) — Nygard template
  (context/decision/consequences) with a proposed/accepted/superseded/rejected status
  state machine, written to docs/decisions/NNN-slug.md plus the index table update and
  HANDOFF reference sync. Use when a semantic ruling or adjudication happens in a stage,
  or on "记录裁定" / "写进决策日志" / "ADR" / querying "决策 X 的现状". NOT for: writing
  handoff docs (use project-handoff) — HANDOFF references ADR numbers, never copies them.
---

# Decision Log（ADR 记录/查询）

## 定位

阶段内任何**语义裁定/拍板/设计裁决** → 当阶段写成 ADR（Nygard 模板），集中进
`docs/decisions/`，让「决策 X 的现状」可查询：status + 历史链（superseded 不删除）。

## 何时使用

- 用户说「记录裁定」「这个决策写进决策日志」「ADR」
- 阶段内发生语义裁定（审计裁定、拍板项、设计裁决）——**当阶段记，不攒批**
- 查询：「决策 X 的现状」「这个决定后来改了吗」

## 触发纪律

每次语义裁定后 3 分钟内完成记录。拿不准是否够格 → 记（轻量；比漏记好——历史链靠它）。

## 流程（记录）

```
- [ ] 1. 编号：docs/decisions/000-decision-log.md 索引最大号 + 1 → NNN
- [ ] 2. 文件名：NNN-slug.md（slug = 决策主题 kebab-case，如 001-rejectstreak-semantics.md）
- [ ] 3. 写 ADR（Nygard 模板 + 状态机，见下）
- [ ] 4. 更新 000-decision-log.md 索引表（# | 标题 | 状态 | 日期）
- [ ] 5. HANDOFF §5 同步：决策日志行已存在则更新（引用编号，不复制内容）
```

## ADR 模板（Nygard）

```markdown
# NNN — {决策标题（含来源节，如 §4.1 C8）}

- Status: proposed | accepted | superseded | rejected
- Date: YYYY-MM-DD（{触发语境，如 S1.1 审计裁定}）
- 相关：{设计节/审计报告引用——路径，不复制}

## Context

问题/冲突背景：字面冲突、可选方案、触发证据（测试失败、审计发现）。

## Decision

- 决定内容（分条）
- 边界（什么不在本决策内）
- 落实方（哪个阶段/技能接线）

## Consequences

- 正面/负面后果
- 后续需要做的（如 S3 接线实现 X）
```

## 状态机

```
proposed ──→ accepted ──→ superseded
    └──────→ rejected
```

- **superseded**：被新决策取代——新 ADR 的「相关」注明「supersedes NNN」；旧 ADR 状态改 superseded，**不删除**（历史链保留）。
- **rejected**：评估后不采纳（proposed 阶段否决）。
- 查询时返回：当前 status + 完整链（NNN → superseded by NNN+1 → …）。

## 防双源

- HANDOFF / 设计文档只引用 ADR 编号（如「001 已定」），不复制 ADR 内容。
- spec（stage-spec）引用 ADR 编号记录 DoD 变更来源。

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `project-handoff` | handoff 引用决策日志（§5 一行），不复制；阶段裁定 → 本技能写 ADR |
| `stage-spec` | DoD 变更需当阶段 ADR 记录——spec 引用编号 |
| `stage-gate` | 门禁检查「决策日志同步」断言 = 索引最新 |

## 完成标准（记录）

- [ ] `docs/decisions/NNN-slug.md` 存在（Nygard 三节 + status/date/相关）
- [ ] `000-decision-log.md` 索引已加行（#/标题/状态/日期）
- [ ] 3 分钟内完成（轻量流程，不追求篇幅）
- [ ] 无敏感信息（凭据不写值）

## 完成标准（查询）

- [ ] 返回决策 status + 历史链（含 superseded 链）
- [ ] 引用来源（设计节/审计/相关 ADR），不搬运全文

## 反模式

- 裁定发生但不记录（等「有空」——历史链断）
- 记录超过 3 分钟（过度润色；ADR 不是论文）
- superseded 后删除旧 ADR（链断）
- HANDOFF 里复制 ADR 内容（双源）
- 编号跳号/覆盖旧文件

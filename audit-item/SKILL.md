---
name: audit-item
description: >-
  Track audit/review findings as numbered issue files (audit-items/NNN-slug.md,
  under the directory the project keeps such findings) with id, severity, source
  audit, status (open/fixed/recorded), fix commit, regression test, and closing
  evidence, plus a summary index README that the stage-completion gate enumerates.
  Use when an audit or review produces findings and the user asks to record them
  (e.g. "log the audit findings"). USER-INVOKED ONLY: it writes tracked files —
  the agent must not auto-invoke it. NOT for: finding the issues (that is the
  review or audit pass itself) — this skill only tracks them.
slug: audit-item
disable-model-invocation: true
version: 1.1.0
displayName: audit-item
---

# Audit Item（审计问题 issue 化跟踪）

## 定位

审计/评审产出的发现 → 编号 issue 文件 + 汇总索引，让每个发现可追踪到关闭，
且**可被 stage-gate 枚举**（门禁「审计状态」断言核对 open 项）。

## 何时使用

- 审计/评审产出发现后：「把审计发现入账」「审计项」
- 覆盖矩阵缺口、code-review 阶段评审、文档审计、领域审计——任何来源的发现

## 目录约定

- 单条：`audit-items/NNN-slug.md`（NNN = 顺序编号，slug = kebab）
- 索引：`audit-items/README.md`（汇总表）
- 目录不存在 → 创建（含 README 骨架）

## 模板（字段必填）

```markdown
# A-NNN {标题}

- id: NNN
- 严重度: high | medium | low
- 来源审计: {报告路径 + 轮次/章节，如 docs/audits/intent-confirmation-impl-audit.md §S2}
- 状态: open | fixed | recorded
- 修复 commit: {hash（fixed 时）}
- 回归测试: {测试文件::用例（fixed 时）}
- 关闭证据: {链接/命令输出尾部（fixed/recorded 时）}

## 发现

{现象 + 证据 + 影响}

## 关闭条件

{可勾选：修复 commit 存在 / 回归测试红→绿 / 证据链接}
```

## 状态流转

```
open ──修复──→ fixed（修复 commit + 回归测试 + 关闭证据，三缺一不算 fixed）
open ──裁决──→ recorded（裁决不修：记录理由，不再要求修复——门禁视为已收）
```

- **fixed**：修复 commit 可查 + 回归测试证明（红→绿或等价证据）+ 关闭证据链接。
- **recorded**：明确裁决不修（如「V2 规模待拍板」）——理由写入关闭证据；与 fixed 同样满足门禁。
- 状态变更时更新 README 索引行（状态 + 关闭证据列）。

## 索引 README

```markdown
# Audit Items 索引

| # | 标题 | 严重度 | 状态 | 来源 | 关闭证据 |
|---|------|--------|------|------|---------|
| 001 | … | medium | fixed | … | commit abc + 测试 |
```

- stage-gate「审计状态」断言 = 枚举本索引 open 行（应为空，或每条有 fixed/recorded 证据）。

## 验收

- [ ] 每条发现一条 issue 文件（字段齐全），索引已加行
- [ ] open 项可被 stage-gate 枚举（README 状态列可过滤）
- [ ] fixed 项含验证证据（commit + 回归测试 + 链接）
- [ ] recorded 项含裁决理由

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `code-review` | 阶段末评审产出发现 → 入账本技能（评审只管发现，跟踪归这里） |
| `coverage-matrix` | 矩阵缺口 → 入账本技能 |
| `stage-gate` | 门禁枚举 open 项核对（消费本技能的索引） |
| 各类 audit | 领域/文档/产品审计发现的落点（来源审计字段指向报告） |

## 反模式

- 发现只写在审计报告里不入账（门禁看不见）
- fixed 无回归测试/无证据链（「修了」不算数）
- recorded 无理由（变成永久 open 的挡箭牌）
- 编号跳号/覆盖旧 issue
- 关闭后删文件（历史审计轨迹保留）

## 显式调用示例

```text
@audit-item
把 docs/audits/intent-confirmation-impl-audit.md §S2 的 3 条发现入账（severity 见报告）
```

- 入账 N 条 → 产出 N 个 issue 文件 + README 索引 N 行；无参数时先问来源审计报告路径，**不猜**。
- 本技能只做入账与跟踪，不自主触发审计；`disable-model-invocation: true` 时仅用户显式调用。

## 最短真实样例（前置 → 调用 → 产出摘录）

前置：一轮文档审计已产出报告 `docs/audits/xxx-audit.md`，其中 §S2 有 1 条 medium 发现。

产出摘录（`audit-items/007-intent-confirm-missing.md`）：

```markdown
# A-007 意图确认缺少驳回分支

- id: 007
- 严重度: medium
- 来源审计: docs/audits/xxx-audit.md §S2
- 状态: open
- 修复 commit:
- 回归测试:
- 关闭证据:

## 发现

意图确认只处理"确认"，驳回时流程静默继续（证据：报告 §S2 截图 2）。

## 关闭条件

- [ ] 修复 commit 存在
- [ ] 回归测试红→绿
- [ ] 关闭证据链接
```

索引 README 对应行：

```markdown
| 007 | 意图确认缺少驳回分支 | medium | open | xxx-audit.md §S2 | — |
```

## 失败出口与校验（可观察）

本技能无自带脚本；每步出口都是**文件与文本层面可核对**的检查，不通过就停在原地并报告，不带病入账：

| 情形 | 可观察出口 |
|------|-----------|
| 来源审计路径不存在 | 停止入账该条；回复「来源审计文件不存在: <路径>」，不创建 issue 文件 |
| 发现无证据（只写"感觉有问题"） | 退回补证据行号/引用后才入账；issue 文件里「发现」节不得为空 |
| NNN 编号与已有文件冲突（`ls audit-items/ | grep ^NNN` 命中） | 取下一个空闲编号，不覆盖旧文件 |
| 状态改为 fixed 但三要素缺一（commit/回归测试/证据） | 保持 open，回复「三缺一不算 fixed，缺：<字段>」——不许中间态 |
| recorded 无裁决理由 | 不改状态；回复「recorded 需把理由写入关闭证据字段」 |
| 目录不存在 | 创建目录 + README 骨架（这是唯一允许的自动动作） |

## 错法 → 改法（FAQ）

| 错法 | 后果 | 改法 |
|------|------|------|
| 发现只留在审计报告里，不入账 | stage-gate 枚举不到，门禁形同虚设 | 每条发现一条 issue 文件 + 索引行 |
| 修完直接标 fixed，没留测试与证据 | 「修了」不算数，回归无从验证 | 三要素齐了才改 fixed（commit + 回归测试 + 关闭证据） |
| 用 recorded 永久挂起不想修的项 | 变成规避门禁的挡箭牌 | recorded 必须写明裁决理由（如「V2 规模待拍板」），无理由不许 recorded |
| 关闭后删 issue 文件 | 历史审计轨迹丢失，复查无据 | 文件只改状态列，永不删除 |
| 编号随手起（复用已关闭的号） | 索引与文件对不上，门禁误判 | 严格递增 NNN；冲突时取下一个空闲号 |
| 手改 README 索引但不同步 issue 文件 | 两处状态不一致，枚举结果不可信 | 状态变更时先改 issue 文件，再同步索引行 |

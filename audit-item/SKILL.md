---
name: audit-item
description: >-
  Track audit/review findings as numbered issue files
  (.scratch/neonforge-v1/audit-items/NNN-slug.md) with id, severity, source audit,
  status (open/fixed/recorded), fix commit, regression test, and closing evidence,
  plus a summary index README that stage-gate enumerates. Use when an audit or review
  produces findings ("把审计发现入账" / "审计项"). NOT for: finding the issues
  (use code-review or the audit itself) — this skill only tracks them.
---

# Audit Item（审计问题 issue 化跟踪）

## 定位

审计/评审产出的发现 → 编号 issue 文件 + 汇总索引，让每个发现可追踪到关闭，
且**可被 stage-gate 枚举**（门禁「审计状态」断言核对 open 项）。

## 何时使用

- 审计/评审产出发现后：「把审计发现入账」「审计项」
- 覆盖矩阵缺口、code-review 阶段评审、文档审计、领域审计——任何来源的发现

## 目录约定

- 单条：`.scratch/neonforge-v1/audit-items/NNN-slug.md`（NNN = 顺序编号，slug = kebab）
- 索引：`.scratch/neonforge-v1/audit-items/README.md`（汇总表）
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

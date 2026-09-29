---
name: coverage-matrix
description: >-
  Generate or maintain the three-way coverage matrix (invariants<->tests /
  events<->tests / DoD<->gate) for staged-delivery projects using this skill
  family's layout: unit tests under tests/unit/, a domain event registry
  (e.g. TIMELINE_EVENT_SPECS in src/domain/timeline.ts), per-stage spec DoD
  files, output at docs/tests/coverage-matrix.md — if your project does not
  follow this layout, this skill does not apply without path adaptation.
  Scans those sources, produces the matrix, and flags gaps (invariant without
  test, event without assertion) into the project's audit-item ledger.
  USER-INVOKED ONLY: it writes a tracked artifact and opens audit items; run
  only on the user's explicit request. Use when at a stage end or after
  adding invariants/events. NOT for: runtime enforcement — the matrix is a
  human-checked artifact, never a test gate.
slug: coverage-matrix
version: 1.1.1
displayName: coverage-matrix
disable-model-invocation: true
compatibility: Requires the staged-delivery (spec-kit) project layout; the concrete paths below are this family's default layout example, probe a new repo before applying
---

# Coverage Matrix（覆盖矩阵生成/维护）

## 定位

三向覆盖矩阵：**不变量 ↔ L1 测试 / 事件 ↔ 测试 / DoD ↔ 门禁**。LLM 半自动——
矩阵由本技能生成初版，人工核对；**不做运行时强制**（与 ddd-qa-chain 的强制门禁分工）。

## 何时使用

- 阶段末：「更新覆盖矩阵」（S2 起为 DoD 常驻断言——见 stage-spec 模板）
- 新增不变量 / 新增事件后

## 输入（扫描源）

> **范围声明**：下表路径/符号是**本项目（neonforge）的默认布局示例**，不是普适事实。
> 接手新仓库时先执行流程步 0 的存在性探测，按仓库实际等价源调整；无法对应则停止并向用户说明。

| 源 | 路径 | 提取什么 |
|----|------|---------|
| L1 测试 | `tests/unit/*.test.ts` | describe/it 名称（用例清单） |
| 事件注册表 | `src/domain/timeline.ts` `TIMELINE_EVENT_SPECS` | 全部事件 id/语义 |
| 不变量 | 设计 §9.5 不变量矩阵 / 领域文档 | 不变量 1-N 及断言 |
| stage-spec DoD | `docs/design/stage-specs/S{N}.md` | DoD 断言清单 |

## 流程

```
- [ ] 0. 布局探测：核对上表默认源是否存在（tests/unit/、事件注册表文件、
       docs/design/stage-specs/、docs/tests/）；布局不同→先映射到仓库实际等价源
       并在矩阵头部记录映射；无法映射→停止，向用户说明本技能仅适用 staged-delivery 布局
- [ ] 1. 扫 L1 测试：读 tests/unit/ 全部 *.test.ts，提取 describe/it 名（含所属文件）
- [ ] 2. 扫事件注册表：读 src/domain/timeline.ts TIMELINE_EVENT_SPECS，提取事件 id 清单
- [ ] 3. 读不变量来源（设计 §9.5）与当前阶段 stage-spec DoD
- [ ] 4. 生成/更新 docs/tests/coverage-matrix.md 三向表（见下）
- [ ] 5. 标缺口：不变量无测试 / 事件无断言 / DoD 无门禁方法
- [ ] 6. 缺口清单（非空时）→ audit-item 入账（open，来源=覆盖矩阵）
- [ ] 7. 自查：抽查 3 条与测试/注册表一致（验收硬项）
```

## 矩阵结构（三向表）

三向缺一不可：不变量↔L1 测试 / 事件↔测试 / DoD↔门禁，判定列无空值
（三张检查点表全样见 [references/checkpoint-tables.md](references/checkpoint-tables.md)）。

## 缺口判定

- 不变量在设计中定义但无任何测试覆盖 → **缺口**
- 事件注册表有事件但测试无断言（不限于 tlog 打点——需语义断言）→ **缺口**
- DoD 断言无法映射到门禁方法 → **spec 缺陷**（回 stage-spec，不算矩阵缺口）
- 缺口一律入 audit-item（open），供 stage-gate 审计状态断言枚举

## 最短真实示例（前置 → 调用 → 产出摘录）

**前置**：仓库按 staged-delivery 布局——`tests/unit/` 有测试、`src/domain/timeline.ts` 有
`TIMELINE_EVENT_SPECS`、`docs/design/stage-specs/S2.md` 有 DoD 节；用户在阶段末发起。

**调用句**（用户对 agent 说）：

```text
「更新覆盖矩阵。」
```

**产出摘录**（`docs/tests/coverage-matrix.md` 应长这样——节选表 1 与表 2 各一行）：

```markdown
# 覆盖矩阵
- 生成日期：2026-09-29 · 数据源版本：测试 46 条 / 事件 12 个

## 表 1：不变量 ↔ L1 测试
| 不变量 | 语义 | 覆盖测试 | 判定 |
|--------|------|---------|------|
| Inv 3 | 会话不可从 active 回 pending | tests/unit/conversationState.test.ts::「拒绝回退」 | ✓ |

## 表 2：事件 ↔ 测试
| 事件 id | 断言测试 | 判定 |
|---------|---------|------|
| session.pending_set | tests/unit/timeline.test.ts::「pending 打点」 | ✓ |
| ticket.transferred | —（无任何语义断言） | ✗ 缺口 → audit-item #21 (open)
```

反例对照：矩阵只有 ✓ 没有判定依据、缺口不入账、无生成日期 → 不合格（见验收硬项）。

## 失败出口与边界处置（可观察）

| 情形 | 可观察出口 |
|------|-----------|
| 布局探测失败（步 0 找不到等价源） | 停止并在回复中说明「本技能仅适用 staged-delivery 布局，差异点：<列出>」；不写半成品矩阵 |
| 事件注册表存在但无 `TIMELINE_EVENT_SPECS` 符号 | 问用户该仓的事件注册表在哪；**不**扫全库猜符号 |
| `tests/unit/` 为空 / 无测试 | 矩阵照常产出（全部行判 ✗ 缺口），头部标注「测试 0 条」；缺清一色入账 |
| stage-spec DoD 文件缺失（S1 期） | 表 3 标「无 DoD 源（S1 前正常）」；不算缺口 |
| `docs/tests/` 目录不存在 | 创建后写入；头部记生成日期 + 数据源版本 |
| audit-item 写入口不可用 | 报错原文呈现给用户并停；缺口先留在矩阵内标 ✗，**不**丢账 |

## 错法 → 改法

| 错法 | 改法 |
|------|------|
| 手写矩阵不扫源 | 必须从测试文件/注册表/DoD 提取——手写必然过期（反模式 1） |
| 只更新表 1 不做事件/DoD 向 | 三向缺一不可，表 2/3 空着等于没跑完 |
| 缺口发现了口头提一句不入账 | 一律 audit-item 入账（open，来源=覆盖矩阵），门禁才能枚举 |
| 把矩阵 ✓ 当测试通过 | 矩阵是静态文档，执行归 `ddd-qa-chain`——覆盖 ≠ 通过 |
| 布局不同的仓库硬套默认路径 | 先按步 0 映射等价源并记录映射；映射不了就停（compatibility 字段同口径） |
| 模型在阶段中自行动刷新矩阵 | USER-INVOKED ONLY（disable-model-invocation）：写 tracked 件 + 开审计项，只在用户显式要求（如「更新覆盖矩阵」）时运行 |

## 验收

- [ ] 矩阵与测试/注册表一致（**抽查 3 条**：随机取测试名反查矩阵、事件反查测试）
- [ ] 缺口清单非空时已输出（矩阵内 + audit-item 入账）
- [ ] 三向表齐全；判定列无空值
- [ ] 矩阵头部有生成日期与数据源版本（测试数/事件数）

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `audit-item` | 缺口 → 审计项（本技能只入账，跟踪归 audit-item） |
| `stage-gate` | 门禁只**检查**矩阵存在与一致；矩阵生成/更新归本技能 |
| `ddd-qa-chain` | 运行时强制门禁（L1-L5 执行）；矩阵是静态文档，不替代执行 |
| `stage-spec` | DoD 引「覆盖矩阵已更新」断言；spec 变更驱动矩阵重扫 |

## 反模式

- 手工拍脑袋写矩阵（不扫测试/注册表——必然过期）
- 矩阵与测试脱节还标 ✓（抽查是硬项）
- 缺口发现后不入账（门禁看不到）
- 把矩阵当门禁执行（覆盖 ≠ 通过——矩阵不跑测试）
- 只做表 1 忽略事件/DoD 向（三向缺一不可）

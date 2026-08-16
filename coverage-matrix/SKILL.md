---
name: coverage-matrix
description: >-
  Generate or maintain the coverage matrix (docs/tests/coverage-matrix.md): scan unit
  test names (describe/it in tests/unit/), the timeline event registry
  (TIMELINE_EVENT_SPECS in src/domain/timeline.ts), and stage-spec DoD assertions, then
  produce the three-way matrix (invariants<->tests / events<->tests / DoD<->gate) and
  flag gaps (invariant without test, event without assertion) into audit items.
  Use when at a stage end ("更新覆盖矩阵") or after adding invariants/events. NOT for: runtime
  enforcement — the matrix is a human-checked artifact, never a test gate.
---

# Coverage Matrix（覆盖矩阵生成/维护）

## 定位

三向覆盖矩阵：**不变量 ↔ L1 测试 / 事件 ↔ 测试 / DoD ↔ 门禁**。LLM 半自动——
矩阵由本技能生成初版，人工核对；**不做运行时强制**（与 ddd-qa-chain 的强制门禁分工）。

## 何时使用

- 阶段末：「更新覆盖矩阵」（S2 起为 DoD 常驻断言——见 stage-spec 模板）
- 新增不变量 / 新增事件后

## 输入（扫描源）

| 源 | 路径 | 提取什么 |
|----|------|---------|
| L1 测试 | `tests/unit/*.test.ts` | describe/it 名称（用例清单） |
| 事件注册表 | `src/domain/timeline.ts` `TIMELINE_EVENT_SPECS` | 全部事件 id/语义 |
| 不变量 | 设计 §9.5 不变量矩阵 / 领域文档 | 不变量 1-N 及断言 |
| stage-spec DoD | `docs/design/stage-specs/S{N}.md` | DoD 断言清单 |

## 流程

```
- [ ] 1. 扫 L1 测试：读 tests/unit/ 全部 *.test.ts，提取 describe/it 名（含所属文件）
- [ ] 2. 扫事件注册表：读 src/domain/timeline.ts TIMELINE_EVENT_SPECS，提取事件 id 清单
- [ ] 3. 读不变量来源（设计 §9.5）与当前阶段 stage-spec DoD
- [ ] 4. 生成/更新 docs/tests/coverage-matrix.md 三向表（见下）
- [ ] 5. 标缺口：不变量无测试 / 事件无断言 / DoD 无门禁方法
- [ ] 6. 缺口清单（非空时）→ audit-item 入账（open，来源=覆盖矩阵）
- [ ] 7. 自查：抽查 3 条与测试/注册表一致（验收硬项）
```

## 矩阵结构（三向表）

### 表 1：不变量 ↔ L1 测试

| 不变量 | 语义 | 覆盖测试（文件::用例） | 判定 |
|--------|------|------------------------|------|
| Inv 1 | … | tests/unit/conversationState.test.ts::「…」 | ✅ / ❌ 缺口 |

### 表 2：事件 ↔ 测试

| 事件 id | 语义 | 断言测试 | 判定 |
|---------|------|----------|------|
| session.pending_set | … | … | ✅ / ❌ 无断言 |

### 表 3：DoD ↔ 门禁

| DoD 断言（spec 原文） | 门禁方法（stage-gate 执行方式） | 判定 |
|----------------------|--------------------------------|------|
| L1 全量绿（新增 ≥15 条） | `npx vitest run` | 断言可执行 ✅ |

## 缺口判定

- 不变量在设计中定义但无任何测试覆盖 → **缺口**
- 事件注册表有事件但测试无断言（不限于 tlog 打点——需语义断言）→ **缺口**
- DoD 断言无法映射到门禁方法 → **spec 缺陷**（回 stage-spec，不算矩阵缺口）
- 缺口一律入 audit-item（open），供 stage-gate 审计状态断言枚举

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
- 矩阵与测试脱节还标 ✅（抽查是硬项）
- 缺口发现后不入账（门禁看不到）
- 把矩阵当门禁执行（覆盖 ≠ 通过——矩阵不跑测试）
- 只做表 1 忽略事件/DoD 向（三向缺一不可）

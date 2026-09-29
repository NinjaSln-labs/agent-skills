---
name: ddd-qa-chain
description: >-
  Run the quality verification chain—5 abstract verification layers (domain logic /
  contract / component interaction / E2E user journeys / visual regression) mapped onto
  the project's own test stack (unit runner, type checker, contract tests, e2e suite,
  visual regression), each with a gate, plus a run-all delivery gate and a DoD quality
  gate (deterministic assertions + probabilistic sample/threshold for model-driven
  behavior). Use when delivering or verifying a feature, before claiming work complete,
  or when asked to run full self-tests / quality checks. NOT for: aggregating DoD across
  a delivery stage, or verifying one completion claim in isolation.
slug: ddd-qa-chain
version: 1.1.1
displayName: ddd-qa-chain
---

# QA Chain（质量链编排）

## 定位

**5 层自动化验证链**，从项目**现有测试基建**映射各层工具与命令——不发明新命令，只编排门禁。
全链通过才可交付；每层结果必须带新鲜命令输出（verification-before-completion）。
层是**概念**，工具/命令是**项目映射**（见「项目映射」节）。

## 何时使用

- 交付前 / 重大改动后 / 用户要求「自测全通再给我」
- 任何「宣称完成」之前；「有 QA 链吗」「跑质量链」触发

## 五层验证链 + 金字塔梯度

L1 单元逻辑 → L2 契约 → L3 组件交互 → L4 端到端 → L5 视觉回归；底层多而快、顶层少而慢，
各层有门禁触发条件（全表见 [references/qa-chain-tables.md](references/qa-chain-tables.md)）。

## 验证与确认（V&V——两个不同的问题）

验证（实现正确）与确认（实现的是要的）缺一不可；全链绿但 AC 未实现 = 确认失败——不交付
（详见 [references/qa-chain-tables.md](references/qa-chain-tables.md)）。

## 项目映射（探测 → 适配）

```
- [ ] 1. 探测测试基建：package.json scripts / CI 配置（GitHub Actions 等）/ 测试目录布局
- [ ] 2. 映射各层：L1 → 单测脚本；L2 → 类型检查 + 契约测试；L3 → 组件测试；L4 → e2e 脚本；L5 → 视觉脚本
- [ ] 3. 探测失败（无 scripts/自定义 runner）→ 问用户或查项目文档；禁止猜命令
- [ ] 4. 记录映射表（输出报告含每层实际命令）——下次复用
```

每层必须能回答：「用什么命令跑、怎么算过」。映射不到的命令层 → 标**未覆盖**（不是假装通过）。
可配置槽位：`tool`（运行器）、`runner`（命令模板）、`workdir`、`env`（如密钥类环境变量——路径不写值）。

## 覆盖率与充分性

- **必跑 ≠ 充分**：层门禁通过后，检查该层是否有度量证明「够了」——语句/分支覆盖率门槛（项目约定，如 L1 ≥80% 分支）；
  关键不变量可选**变异测试**抽查（变异杀死率——防「断言没测到语义」）。
- 无覆盖率约定的项目：标注「未度量」（不算 FAIL，但报告显式列出——防虚假安全感）。
- 测试数据隔离：用例间数据互不污染（内存适配器/每用例重置/工厂数据）——避免「依赖执行顺序才绿」。

## 全链 run-all（交付门禁）

```bash
# 按映射结果拼装：全部层依次执行，任一失败即停（或记录后汇总）
<L1 命令> && <L2 命令> && <L3 命令> && <L4 命令> && <L5 命令>
```

- 未跑全链不宣称完成；任一失败 → 定位根因（systematic-debugging）→ 修复 → 重跑全链
- **flaky 治理**：偶发失败先定性（重跑同命令确认是否 flaky）——flaky 测试本身是缺陷，记入待办，
  不得以「重试通过」为由长期放任
- **门禁通过 = 放行，不是发布**：有 CI 的项目 run-all 应成为必过 status check；生产放行
  （灰度/feature flag）是 CI 之外的发布决策，不在此门禁内

## DoD 质量门禁（功能「Done」判定）

五项判定：功能 AC 全过 / 确定性断言 / 概率性样本阈值 / 质量链全绿 / 定义对齐——
确定性必须断言、概率性要样本/阈值证据（全表见 [references/qa-chain-tables.md](references/qa-chain-tables.md)）。

## 工作流

```
- [ ] 0. 项目映射（首次运行/基建变化时）：探测测试基建 → 各层命令映射表（见「项目映射」）
- [ ] 1. 确认改动范围 → 映射影响层（L1-L5 哪些）
- [ ] 2. 跑受影响层（+ 门禁要求的最小集合）——任一失败：定位根因（systematic-debugging）→ 修复 → 重跑该层
- [ ] 3. 交付前全链 run-all（flaky 定性：偶发失败重跑确认——flaky 是缺陷，记入待办）
- [ ] 4. 确认层：tickets AC 回填 + 定义对齐（product-doc-audit 如需）
- [ ] 5. 报告：每层结果 + 实际命令 + 证据（输出尾部）——未通过/未确认不交付
```

## 最短真实示例（前置 → 调用 → 产出摘录）

**前置**：一个有 `package.json` 的 TS 项目，`scripts` 里有 `test`（Vitest）、`typecheck`（tsc）、`test:e2e`（Playwright）；用户刚改完订单折扣逻辑。

**调用句**（用户对 agent 说）：

```text
「帮我跑一遍质量链，全绿了再交付这个折扣功能。」
```

**产出摘录**（报告应长这样）：

```text
## 质量链报告（功能：订单折扣）
| 层 | 映射命令 | 结果 |
|----|---------|------|
| L1 领域/单元 | npx vitest run tests/unit/discount | 42/42 ✓ |
| L2 契约 | npx tsc --noEmit | 0 errors ✓ |
| L3 交互 | npx playwright test --project=components | 8/8 ✓ |
| L4 端到端 | npx playwright test tests/e2e/checkout | 3/3 ✓ |
| L5 视觉 | —（项目无视觉基线） | 未覆盖（显式标注，不算通过） |
确认层：TICKET-117 AC1-AC4 全部回填 ✓
结论：L5 未覆盖，其余全绿 → 可交付（视觉改动需补 L5）
```

反例对照：只贴「测试都过了」一行、无命令无证据 → 不合格（违反 verification-before-completion）。

## 失败出口与边界处置（可观察）

| 情形 | 可观察出口 |
|------|-----------|
| 探测不到测试基建（无 scripts/无 CI 配置） | 报告写「映射失败：未找到 <层> 的命令」并**停下问用户**；禁止猜命令继续跑 |
| 某层命令非零退出 | 报告该层 ✗ + 附最后 20 行输出 + 指向 systematic-debugging；**不**修复后假装全绿 |
| 命令不存在（`command not found`） | 该层标「命令失效，映射需更新」，重跑项目映射步 1-2；不静默跳过 |
| 无 UI 项目 | L5 直接裁剪并在报告写「L5 裁剪（无 UI）」——写明原因，不是漏跑 |
| 概率性验证（LLM 行为）无约定阈值 | 报告写「未度量：项目未约定样本数/阈值」，列进待办；不编数字 |
| 全链 run-all 中断（超时/环境崩） | 报告停在失败层，标注「全链未跑完」；禁止只报已过层就算完成 |

## 错法 → 改法

| 错法 | 改法 |
|------|------|
| 没探测项目就直接跑 `npm test` | 先跑项目映射步 1-2，命令以映射表为准 |
| L1 绿了就说「交付完成」 | 交付前必须全链 run-all + 确认层 AC 回填 |
| 项目没有某层测试 → 该层写「通过」 | 写「未覆盖」并显式标注；未覆盖 ≠ 通过 |
| E2E 偶发失败 → 重跑两次过了就算绿 | 定性为 flaky，记入待办，报告写明「重跑 N 次后通过」 |
| 概率行为一次跑通即宣称达标 | 给样本/阈值证据（如 5 试跑 ≥4 过），样本数从项目约定取 |
| 失败后自己顺手改业务代码再重跑 | 失败交给 systematic-debugging 定根因；本技能只编排 |

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `verification-before-completion` | 单点验证纪律（证据先于断言）；本技能是其链级编排 |
| `stage-gate` | 阶段级 DoD 聚合（stage-spec 逐条执行）；本技能 = 交付级质量链（功能粒度） |
| `systematic-debugging` | 失败先根因再修（本技能只编排不调试） |
| `coverage-matrix` | 覆盖矩阵维护（不变量/事件 ↔ 测试）；本技能 = 执行门禁 |
| `playwright-best-practices` / `pixel-perfect` / `test-data-generation` 等 | 测试**编写**规范（防 flaky/数据隔离）；本技能 = 编排与门禁 |
| `cicd-pipeline` | CI 管道配置（本技能映射的 run-all 落地为 CI job/status check） |

## 完成标准

- [ ] 受影响层全部跑通（命令输出为证，映射表可见）
- [ ] 交付前全链 run-all 通过
- [ ] 确认层：tickets AC 回填（实现↔定义可追溯）
- [ ] 报告含每层证据 + 未覆盖层/未度量项显式标注
- [ ] flaky 已定性并记入待办（如有）

## 反模式

- 凭记忆猜命令（不探测项目基建）
- 只跑 L1 跳过 L4/L5（「改动小」不是理由）
- 单层通过即宣称交付（无 run-all、无确认层）
- 项目无某层测试时假装通过（应标未覆盖）
- E2E 用例数倒挂（金字塔失衡——应下沉断言）
- 以「重试通过」放任 flaky（flaky 是缺陷不是运气）
- 把本技能当调试工具（失败应该交 systematic-debugging）

## 方法论来源（2026-08 调研）

- 测试金字塔/分层：Martin Fowler（martinfowler.com/bliki/TestPyramid.html）；Parasoft 自动化金字塔
- CI 质量门禁：SonarQube Quality Gates；GitHub Required Status Checks（Microsoft Code-with-Engineering-Playbook）
- Definition of Done：Scrum.org DoD 资源；Microsoft Done/Undone
- V&V / IEEE 829（测试文档与验证/确认区分）、ISO/IEC/IEEE 29119
- 契约测试：Pact consumer-driven contracts（docs.pact.io）
- E2E 取舍与 flaky：Google Testing on the Toilet（「好的 E2E 少而聚焦」）
- 覆盖率/变异测试：语句/分支 vs 变异 adequacy 对比（2023 实证）；A Formal Notion of Program-Based Test Data Adequacy（1982）
- 灰度/放行：feature flag canary 实践（ConfigCat/Statsig）
- DoD 学术：On the benefits and problems related to using Definition of Done（survey study）
- 质量模型：ISO/IEC 25010（非功能维度分类）

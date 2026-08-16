---
name: ddd-qa-chain
description: >-
  Run the quality verification chain—5 abstract verification layers (domain logic /
  contract / component interaction / E2E user journeys / visual regression) mapped onto
  the project's own test stack (unit runner, type checker, contract tests, e2e suite,
  visual regression), each with a gate, plus a run-all delivery gate and a DoD quality
  gate (deterministic assertions + probabilistic sample/threshold for model-driven
  behavior). Use when delivering or verifying a feature, before claiming work complete,
  or when asked to run full self-tests / quality checks. NOT for: stage-level DoD
  aggregation (use stage-gate) or single-shot verification (use
  verification-before-completion).
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

| 层 | 质量维度 | 验证对象 | 典型工具族 | 数量/速度/频次（金字塔） | 门禁触发 |
|----|---------|---------|-----------|------------------------|---------|
| **L1 领域/单元逻辑** | 逻辑 | 纯函数、业务规则、值对象不变量、状态机 | 单测框架（Vitest/Jest/…） | **多**·快·每次提交 | 逻辑变更必跑 |
| **L2 契约** | 功能 | 模块/进程间接口、API/通道完整性、schema | 类型检查器（tsc/…）+ 契约测试（Pact/…） | 中·中·CI 必跑 | 接口/契约变更必跑 |
| **L3 组件交互** | 功能 | 组件/模块交互逻辑、授权/状态机流程 | 组件测试（Playwright/Testing Library/…） | 中·中·CI 必跑 | 交互逻辑变更必跑 |
| **L4 端到端** | 体验 | 真实用户旅程（入口→操作→结果→交付） | E2E 框架（Playwright/Cypress/…）+ 真实依赖 | **少**·慢·合并/交付前 | 任何功能改动必跑 |
| **L5 视觉回归** | 视觉 | 界面渲染像素基线 | 视觉回归（toHaveScreenshot/Chromatic/…） | 少·慢·UI 改动时 | UI 改动必跑 |

**金字塔纪律**：底层多而快、顶层少而慢。若某层用例数量倒挂（E2E 比单测多）→ 失衡信号：
把能下沉的断言沉到底层，顶层只留真正需要真实环境的旅程。层可裁剪：无 UI 项目去 L5，
无 IPC/RPC 的去 L2 契约子项（保留类型检查）。

## 验证与确认（V&V——两个不同的问题）

- **验证（Verification）**：实现是否正确（building it right）——L1-L5 各层断言。
- **确认（Validation）**：实现的是否是要的（building the right thing）——功能 AC 全过 +
  实现可追溯到最初定义（tickets/spec ↔ 文档）。
- 两者缺一不可：全链绿但 AC 没实现 = 验证过、确认失败——不交付。

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

| DoD 项 | 检查 | 对应层 |
|--------|------|--------|
| 功能完成 | 该功能所有 AC 全部通过（predicates/场景断言） | 确认（tickets/规格回填） |
| 确定性验证 | 逻辑/契约/交互等**确定性部分**——断言必过（非概率） | L1-L3 |
| 概率性验证 | **模型驱动行为**（LLM 回复质量/agent 行为）——阈值 + 样本验证（如 5 次试跑 ≥4 通过），防 drift | L4（若适用） |
| 质量链通过 | 受影响层 + 全链 run-all 全绿 | L1-L5 |
| 定义对齐 | 实现可追溯到最初定义（tickets AC ↔ 文档） | 确认 |

**铁律（AI 应用特化）**：确定性部分绝不用「模型应该会」糊弄——必须断言；
概率部分绝不用「一次通过」冒充——要样本/阈值证据（样本数与阈值由项目约定，可参数化）。

## 工作流

```
- [ ] 1. 确认改动范围 → 映射影响层（L1-L5 哪些）
- [ ] 2. 跑受影响层（+ 门禁要求的最小集合）
- [ ] 3. 交付前全链 run-all
- [ ] 4. 确认层：tickets AC 回填 + 定义对齐（product-doc-audit 如需）
- [ ] 5. 报告：每层结果 + 实际命令 + 证据（输出尾部）——未通过/未确认不交付
```

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

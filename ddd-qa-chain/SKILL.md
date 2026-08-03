---
name: ddd-qa-chain
description: >-
  Run the DDD quality assurance test chain—5 automated layers (domain logic / IPC contract /
  component interaction / E2E user journeys / visual regression) that verify a build equals its
  original definition and meets quality bar. Each layer has a tool, command, and gate; a run-all
  command is the delivery gate, plus a DoD quality gate (deterministic assertions + probabilistic
  sample/threshold for AI behavior). Use when delivering or verifying a feature, before claiming
  work complete, or when asked to run full self-tests / quality checks.
---

** 5 层自动化验证，每一层有工具、命令、门禁；全链通过才可交付。

## 何时使用
- 交付前 / 重大改动后 / 用户要求「自测全通再给我」时
- 任何「宣称完成」之前（配合 verification-before-completion：证据先于断言）

## 5 层测试链
| 层 | 质量维度 | 测什么 | 工具 | 命令 | 门禁 |
|----|---------|--------|------|------|------|
| **L1 领域逻辑** | 逻辑 | 聚合/实体/值对象不变量、纯函数（如 applyDiff） | Vitest（`tests/unit/`） | `npx vitest run` | 领域规则/纯逻辑变更必跑 |
| **L2 契约** | 功能 | IPC main↔renderer 类型安全、通道完整性 | electron-best-practices IPC 类型 + 契约单测 | `npx tsc --noEmit`（类型）+ vitest 契约 | IPC 通道变更必跑 |
| **L3 组件交互** | 功能 | 授权/验收/状态机交互逻辑 | Playwright component / Testing Library | playwright component tests | 交互逻辑变更必跑 |
| **L4 体验** | 体验 | 真实用户旅程（发送→工具→授权→执行→交付）——12 场景 | `e2e-suite.mjs`（Playwright + Electron + 真实 API） | `NF_TEST_KEY=... node e2e-suite.mjs` | 任何功能改动必跑 |
| **L5 视觉** | 视觉 | 界面渲染像素回归 | pixel-perfect（`toHaveScreenshot` 基线） | `npx playwright test` | UI 改动必跑 |

## L4 覆盖矩阵（12 场景）
1. 空目录主链路（read 找不到→模型回复）
2. bash 待授权（🔒 卡片不卡处理中）
3. 真实项目 read（内容命中）
4. 多轮对话（连续 3 条——会话隔离）
5. 纯文本（无工具）
6. 快速连发（并发保护）
7. write 授权写入（真实写文件）
8. 授权后续聊（点允许→执行→结果回填→续聊）
9. 空回复异常（提示显示）
10. Key 失效（401 → 更新提示）
11. 超时（流式超时 → 错误提示）
| **L5 视觉** | 视觉 | 界面渲染像素回归 | pixel-perfect（`toHaveScreenshot` 基线） | `npx playwright test` | UI 改动必跑 | ## L4 覆盖矩阵（12 场景） 1. 空目录主链路（read 找不到→模型回复）
12. 上下文保留（工具场景后追问记得） ## 门禁（交付合格） **全链命令（run-all——任何交付前必跑）：** ```bash
cd apps/desktop
npx vitest run # L1 领域逻辑
npx tsc --noEmit # L2 契约（类型）
NF_TEST_KEY=<key> node e2e-suite.mjs # L4 体验（12 场景）
npx playwright test # L5 视觉（基线）
``` **一致性验证（④ 交付=定义）：**
- `product-doc-audit`：文档就绪度 + 可交付判断（不修改被审文档）
- tickets AC 回填：ticket 完成 → 勾 AC → 文档对齐（实现可追溯到定义） **铁律：**
- 未跑全链不宣称完成（verification-before-completion）
- 全链任一失败 → 定位根因（systematic-debugging）→ 修复 → 重跑全链
- DDD 方法：测试是领域行为的验证门禁（非 TDD 驱动设计） ## 工作流 ```
- [ ] 1. 确认改动范围 → 映射影响层（L1-L5 哪些）
- [ ] 2. 跑受影响层（+ 门禁要求的最小集合）
- [ ] 3. 全链 run-all（交付前）
- [ ] 4. 一致性：tickets AC 回填 + product-doc-audit（如需）
- [ ] 5. 报告：每层结果 + 证据（命令输出）——未通过不交付
``` ## 交付合格定义（DoD——质量门禁） **一项功能「Done」须同时满足（借鉴 Acceptance Criteria Patterns + DoD for AI Agents）：** | DoD 项 | 检查 | 对应层 |
|--------|------|--------|
| 功能完成 | 该功能的所有 AC **全部通过**（predicates/场景断言）| tickets 回填 |
| 确定性验证 | 授权/schema/工具执行等**确定性部分**——断言必过（非概率）| L1-L3 |
| 概率性验证（AI 应用）| **模型行为**（回复质量/帮助度/拒绝）——阈值 + 样本验证（如 5 次试跑 ≥4 通过），防 drift/hallucination | L4 |
| 质量链通过 | 受影响的层 + 全链 run-all 全绿 | L1-L5 |
| 定义对齐 | 实现可追溯到最初定义（tickets AC ↔ 文档）| ④ 一致性 | **铁律（AI 应用特化）**：确定性部分绝不用「模型应该会」糊弄——必须断言；概率部分绝不用「一次通过」冒充——要样本/阈值证据。 ## 与相关技能协作 - `verification-before-completion`：证据先于断言（每层结果必须有命令输出佐证）
- `systematic-debugging`：失败先根因再修
- `playwright-best-practices`：L4/L5 测试编写规范（防 flaky/断言/locators）
- `electron-best-practices`：L2 契约 + Electron 工程规范
- `pixel-perfect`：L5 视觉基线维护
- `product-doc-audit`：④ 交付=定义（文档审计/就绪度） ## 完成标准 - [ ] 受影响的层全部跑通（命令输出为证）
- [ ] 交付前全链 run-all 通过
- [ ] tickets AC 回填（实现↔定义可追溯）
- [ ] 报告含每层证据（verification-before-completion）

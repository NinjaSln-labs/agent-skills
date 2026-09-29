---
name: stage-spec
description: >-
  Write or backfill a stage spec for staged delivery (spec-kit): turn a stage row of
  the phased design into a machine-verifiable contract — DoD assertions directly
  executable by a stage-completion gate, a TDD grid (spec assertion -> failing test -> implementation
  -> refactor), deliverables, and explicit non-goals. No prose "done" statements.
  Use when starting a new stage (e.g. "write the S3 spec" / "backfill the stage spec") or after the
  design's stage plan changes. NOT for: generic implementation plans, or
  running the gate once a stage is done.
slug: stage-spec
version: 1.1.0
displayName: stage-spec
---

# Stage Spec（阶段 spec 编写/回填）

## 定位

把设计文档的阶段计划升级为**机器可验证的阶段契约**（spec-kit 模式）：每阶段一份
`docs/design/stage-specs/S{N}.md`，供 `stage-gate` 逐条执行。spec 是**阶段契约**
（DoD/网格/边界），不是任务分解——任务分解交给 `writing-plans`。

## 何时使用

- 阶段开工前：「写 S{N} spec」「回填阶段 spec」「S2 定稿」
- 设计 §6（分阶段实施计划）变更后——受影响阶段的 spec 需同步

## 输入

- 设计文档：`docs/design/intent-confirmation-domain-design.md`（§6 阶段行 + 相关 §3/§4 行为规范 + §8 契约）
- 模板：`docs/design/stage-specs/README.md`（模板 + 维护规则）
- 既有资产：`docs/decisions/`（阶段裁定 ADR——spec 引编号）、`docs/tests/coverage-matrix.md`（S2 起）

## 模板（五节——不得增删）

```
# Stage S{N} Spec（{阶段名}）

> 来源：docs/design/intent-confirmation-domain-design.md §6；开工日期：YYYY-MM-DD

## DoD（机器可验证断言——stage-gate 逐条执行）

## TDD 网格（本阶段新增功能——spec-first + test-first）

## 产出物

## 边界（不做——防蔓延）
```

## DoD 断言写作规则（验收核心）

1. **每条可被 stage-gate 直接执行**——要么是完整命令（`npx vitest run`、双 tsc、playwright），
   要么是可验证行为断言 + 承载它的测试文件路径（`tests/unit/xxx.test.ts` 契约用例清单）。
2. **禁散文式「完成」**——「完成 XX 重构」不行；「XX 对 <输入> 产出 <输出>（契约用例：a/b/c）」行。
3. **命令引用不复制**——DoD 直接引用既有门禁命令，不复制门禁输出（防双源）。
4. **计数给下限**——新增用例断言写「≥N 条」并回指 TDD 网格；L3 回归写预期总数（如 31/31）。
5. **状态类断言显式**——审计状态（上阶段 open 项全 fixed/recorded）、覆盖矩阵（首版已产出/已更新）、
   决策日志同步、push + CI 绿——逐条列，不合并成一句「收尾完成」。
6. **嵌套子断言逐条**——行为验收下多条验证点拆成子 `- [ ]`，stage-gate 逐条执行。

## TDD 网格（spec-first + test-first）

| 功能 | 规范断言（先写——来源 §4/§3.3） | 失败测试（红） | 实现（绿） | 重构 |

- 每个本阶段新增功能一行；规范断言标来源小节（§4/§3.3/§8.x）；
- 失败测试给**具体测试文件名** + 契约用例类型清单；重构列写与旧实现的语义对照/去重。

## 产出物

- 文件/模块/测试清单——可勾选，作为 DoD 断言的落点。
- 与项目交接存储（`.handoff/`）的 actions 槽同步：spec 定稿后让该阶段行**指向本 spec 的路径**
  （`docs/design/stage-specs/S{N}.md`），只引用不复制（防双源）；尚无该行则先登记再指。
  写入口与命令形以 [`project-handoff`](../project-handoff/SKILL.md) 的写槽表为**唯一权威面**——
  本件只定「阶段行要指到 spec」这条契约，不复制它的参数面（那份拷贝会先烂）。

## 边界（不做——防蔓延）

- 每条一行，明确排除项（如「XX 属 S{N+1}」）；边界来自设计 §6 或阶段裁定（裁定 → ADR → spec 引用）。

## 验收

- [ ] 每条 DoD 可被 stage-gate 直接执行（命令或测试文件路径，无散文式表述）
- [ ] 无「完成 XX」类无验证表述；计数断言有下限/预期值
- [ ] 五节齐全；来源/开工日期在头部；TDD 网格覆盖全部新增功能
- [ ] 与 `.handoff/` actions 槽同步（该阶段行带上 spec 路径；写入口见「产出物」节所委托的 project-handoff 写槽表）

## 最短真实示例（前置 → 调用 → 产出摘录）

**前置**：设计文档 `docs/design/intent-confirmation-domain-design.md` 已有 §6 阶段行（含阶段名与范围），
且阶段未开工（spec 先行）。

**调用句**（用户对 agent 说）：

```text
「写 S3 spec。」
```

**产出摘录**（`docs/design/stage-specs/S3.md` 应长这样——五节结构，此处节选 DoD 与边界节）：

```markdown
# Stage S3 Spec（会话事件与追溯）

> 来源：docs/design/intent-confirmation-domain-design.md §6；开工日期：2026-09-29

## DoD（机器可验证断言——stage-gate 逐条执行）
- [ ] `npx vitest run tests/unit/conversationState.test.ts` 全绿（新增 ≥5 条：
      pending→active 迁移 / 重复 pending 拒绝 / …，清单见 TDD 网格）
- [ ] `npx tsc --noEmit` 0 errors（双跑：根目录与 worker 目录）
- [ ] docs/tests/coverage-matrix.md 已更新（S3 事件行全部映射测试）
- [ ] S2 open 审计项全部 fixed/recorded（audit-item 清单）

## TDD 网格（本阶段新增功能——spec-first + test-first）
| 功能 | 规范断言（来源 §4.2） | 失败测试（红） | 实现（绿） | 重构 |

## 产出物
- [ ] src/domain/conversationState.ts（状态机）

## 边界（不做——防蔓延）
- 会话归档属 S4，本阶段不做
- 通知推送不在本设计范围（见 ADR-006）
```

反例对照：DoD 写「完成会话状态重构」这类散文 → gate 无法执行，spec 返工（见写作规则 2）。

## 失败出口与边界处置（可观察）

| 情形 | 可观察出口 |
|------|-----------|
| 设计文档或 §6 阶段行不存在 | 停下向用户要设计文档；**不**凭空发明阶段内容 |
| §6 阶段行只有阶段名、无范围 | 先向用户确认范围再写；spec 头部「来源」节标注「范围经用户 2026-09-29 口头确认」 |
| 模板 README（`docs/design/stage-specs/README.md`）不存在 | 用本件「模板」节内联模板创建目录，并在完成报告注明「模板落位待补 README」 |
| `.handoff/` actions 槽写不进（project-handoff 写槽表对不上） | 报错原文向用户呈现并停；**不**手改 `.handoff/` 结构绕过（写入口唯一权威是 project-handoff） |
| 阶段已开工/已完成（要求回填） | 允许回填，但 spec 头部开工日期如实写实际日期，DoD 只列**已验证**可复跑的断言；禁止追认未跑过的断言 |
| 用户要的是通用实施计划/任务拆解 | 不在范围（description NOT for），指向 `writing-plans` 并停 |

## 错法 → 改法

| 错法 | 改法 |
|------|------|
| DoD 写「完成 XX」散文 | 写成命令或「行为断言 + 测试文件路径」（写作规则 1-2） |
| 把门禁命令的输出复制进 spec | 只引用命令，不复制输出（防双源——规则 3） |
| TDD 网格的功能在 DoD 找不到断言 | 网格每行必须在 DoD 有对应断言，否则补齐 |
| 边界节空着或写「无」了事 | 每阶段至少列一条显式排除项（含「属 S{N+1}」式指引）；真无边界则引 §6 行原文佐证 |
| spec 定稿后不回写 `.handoff/` | 阶段行必须指向 spec 路径（只引用不复制）——验收硬项 |
| 模型改了设计 §6 后不问就自行改 spec | 设计变更后受影响 spec 需同步，但变更本身须用户确认来源后再动笔 |
| 自主开工写 spec（用户没要求） | spec 决定阶段验收口径，仅用户显式触发（「写 S{N} spec」「回填阶段 spec」）时运行 |

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `writing-plans` | stage-spec = 阶段契约（DoD/网格/边界，被 stage-gate 执行）；writing-plans = 通用任务分解（bite-size 步骤 + 代码 + 验证）。先 spec 定稿，再按需 plan 拆任务 |
| `stage-gate` | spec 的消费者——spec 写完即被 gate 执行；DoD 不满足可执行性 = spec 返工 |
| `decision-log` | 阶段裁定（如 DoD 变更）→ ADR；spec 引用 ADR 编号不复制内容 |
| [`project-handoff`](../project-handoff/SKILL.md) | 交接存储的**工具方**：`.handoff/` 结构与写命令参数面全归它定义，本件步骤只按契约要求登记引用；它改形不回流改本件 |

## 完成标准

- [ ] `docs/design/stage-specs/S{N}.md` 已创建/更新（五节齐全）
- [ ] 每条 DoD 断言可执行（命令或测试路径），无散文式「完成」
- [ ] TDD 网格先行——规范断言标来源，失败测试给文件名与用例清单
- [ ] `.handoff/` actions 槽已同步（引用 spec）
- [ ] DoD 变更（如有）已由 ADR 记录

## 反模式

- 写「完成 XX」式散文断言——gate 无法执行
- 复制门禁输出/测试输出进 spec（双源）
- DoD 与 TDD 网格脱节（网格功能无对应 DoD 断言）
- 边界节缺失——蔓延风险无人认领
- spec 定稿后不回写 `.handoff/`（下个 session 不知道契约存在）

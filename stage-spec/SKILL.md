---
name: stage-spec
description: >-
  Write or backfill a stage spec for staged delivery (spec-kit): turn a stage row of
  the phased design into a machine-verifiable contract — DoD assertions directly
  executable by stage-gate, a TDD grid (spec assertion -> failing test -> implementation
  -> refactor), deliverables, and explicit non-goals. No prose "done" statements.
  Use when starting a new stage ("写 S{N} spec" / "回填阶段 spec") or after the
  design's stage plan changes. NOT for: generic implementation plans (use writing-plans)
  or running the gate (use stage-gate).
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
- 与 HANDOFF §3 同步：spec 定稿后 HANDOFF §3 的该阶段行加 spec 引用（防双源——只引用不复制）。

## 边界（不做——防蔓延）

- 每条一行，明确排除项（如「XX 属 S{N+1}」）；边界来自设计 §6 或阶段裁定（裁定 → ADR → spec 引用）。

## 验收

- [ ] 每条 DoD 可被 stage-gate 直接执行（命令或测试文件路径，无散文式表述）
- [ ] 无「完成 XX」类无验证表述；计数断言有下限/预期值
- [ ] 五节齐全；来源/开工日期在头部；TDD 网格覆盖全部新增功能
- [ ] 与 HANDOFF §3 同步（引用 spec 路径）

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `writing-plans` | stage-spec = 阶段契约（DoD/网格/边界，被 stage-gate 执行）；writing-plans = 通用任务分解（bite-size 步骤 + 代码 + 验证）。先 spec 定稿，再按需 plan 拆任务 |
| `stage-gate` | spec 的消费者——spec 写完即被 gate 执行；DoD 不满足可执行性 = spec 返工 |
| `decision-log` | 阶段裁定（如 DoD 变更）→ ADR；spec 引用 ADR 编号不复制内容 |

## 完成标准

- [ ] `docs/design/stage-specs/S{N}.md` 已创建/更新（五节齐全）
- [ ] 每条 DoD 断言可执行（命令或测试路径），无散文式「完成」
- [ ] TDD 网格先行——规范断言标来源，失败测试给文件名与用例清单
- [ ] HANDOFF §3 已同步（引用 spec）
- [ ] DoD 变更（如有）已由 ADR 记录

## 反模式

- 写「完成 XX」式散文断言——gate 无法执行
- 复制门禁输出/测试输出进 spec（双源）
- DoD 与 TDD 网格脱节（网格功能无对应 DoD 断言）
- 边界节缺失——蔓延风险无人认领
- spec 定稿后不通知 HANDOFF（下个 session 不知道契约存在）

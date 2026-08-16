---
name: stage-gate
description: >-
  Run a stage-completion gate for staged delivery (spec-kit): read the stage spec's
  DoD assertions and execute each one — unit tests, dual tsc, interaction tests,
  behavioral acceptance, coverage matrix, open audit items, push state — reporting
  PASS/FAIL per assertion with fresh command evidence. Verifies only, never fixes.
  Use when a stage is claimed complete or on "run the stage gate" / "跑阶段门禁".
  NOT for: single-shot verification (use verification-before-completion) or
  executing a plan (use executing-plans).
---

# Stage Gate（阶段门禁执行）

## 定位

NeonForge 阶段完成检查器——把「声称完成」变成「逐条可验证」（spec-kit/evaluator 模式）。
每个 S 阶段有一份 stage-spec（`docs/design/stage-specs/S{N}.md`）承载机器可验证的 DoD 断言；
本技能逐条执行这些断言，输出 PASS/FAIL + 证据。**只验不修**：FAIL 报告差异，交回开发。

## 何时使用

- 用户/agent 声称某 S 阶段完成（「S2 完成了」「阶段完成」）
- 请求「跑阶段门禁」「stage gate」「过门禁」
- 阶段收口前自查（此时跑出的 FAIL 就是待办清单）

## 输入

- stage-spec：`docs/design/stage-specs/S{N}.md`（DoD 节 = 断言清单）
- 仓库：`apps/desktop`（所有门禁命令的工作目录）
- 关联资产：`docs/tests/coverage-matrix.md`（覆盖矩阵）、`.scratch/neonforge-v1/audit-items/`（审计项）、`docs/decisions/`（决策日志）

## 硬约束（不可妥协）

1. **只验不修**——FAIL 一律报告差异，不修代码/不补测试/不改 spec。
2. **证据先行**——每条断言必须带本次运行的新鲜证据（命令输出尾部/exit code/测试结果）；「上次跑过」「应该没问题」不算。
3. **不编造通过**——命令跑不出来、CI 查不到、人工验收未做 → 判 **未验证**（不算 PASS，不算 FAIL，单独列出）。
4. **全量逐条**——DoD 节每条 `- [ ]` 断言都要执行，不许抽样、不许跳过。

## 流程

```
- [ ] 1. 定位 spec：docs/design/stage-specs/S{N}.md（N 由用户给出或从语境推断）
- [ ] 2. spec 缺失 → 直接报告「无 spec，阶段无法门禁」（这本身就是发现——spec 未写）
- [ ] 3. 读 DoD 节 → 提取全部 `- [ ]` 断言（含嵌套子断言——行为验收下常有）
- [ ] 4. 逐条执行（分类方法见下节），每条记录：断言原文 / 判定 / 证据尾部
- [ ] 5. 汇总 → 写 gate 报告 docs/audits/stage-gate-S{N}-YYYY-MM-DD.md
- [ ] 6. 全绿 → 阶段可收（附基线信息）；有 FAIL/未验证 → 差异清单交回开发
```

## DoD 断言分类与执行方法

| 断言类型 | 判定方法 | 证据形式 |
|---------|---------|---------|
| **L1 全量** | `npx vitest run`（工作目录 apps/desktop） | 输出尾部（tests/files/passed/failed）+ exit code；spec 有「新增用例 ≥N 条」时核对用例数 |
| **L2 契约** | `npx tsc -p tsconfig.json --noEmit` + `npx tsc -p tsconfig.main.json --noEmit` 双跑 | 各 0 error 才 PASS；任一有错 → FAIL（列出错误数/首错位置） |
| **L3 交互** | `npx playwright test --project=interaction` | 通过数/总数；spec 有预期计数（如 31/31）时对照——不足即 FAIL |
| **行为验收** | spec 内给出的命令或测试；嵌套子断言逐条执行（有测试文件 → `npx vitest run <file>` 定向跑） | 每条子断言独立 PASS/FAIL + 对应测试输出 |
| **覆盖矩阵** | `docs/tests/coverage-matrix.md` 存在 + 抽查 3 条与测试/注册表一致 | 抽查结果；spec 要求「首版已产出」时核对存在性 |
| **审计状态** | 读 `.scratch/neonforge-v1/audit-items/README.md` 枚举 open 项 → 每条核对是否 fixed/recorded | open 项清单（应为空或全部有关闭证据） |
| **决策日志** | `docs/decisions/000-decision-log.md` 索引最新（本阶段裁定有 ADR 编号） | 索引表尾部 |
| **push 状态** | `git status` 干净 + `git log @{u}..HEAD` 为空（无未 push commit） | git 输出尾部；CI 远端绿若可查（本地查不到 → 未验证） |

**嵌套断言**：行为验收下的 `- [ ]` 子条目逐条执行，不得合并成一条「行为验收通过」。

## Gate 报告（唯一产出）

`docs/audits/stage-gate-S{N}-YYYY-MM-DD.md`：

```markdown
# Stage Gate S{N} 报告

- 日期 / spec 路径 / 基线 commit（阶段首 commit^，如有）
- 结论：全绿 ✅ | 有 FAIL ❌ | 有未验证 ⚠️

## 断言结果

| # | 断言 | 判定 | 证据（输出尾部） |
|---|------|------|-----------------|
| 1 | L1 全量绿 | PASS | vitest: 344 passed, 0 failed |
| 2 | … | FAIL | tsc: 2 errors (src/…:12) |

## 差异清单（交回开发，不修）

- #N：期望 …；实际 …；证据 …
```

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `verification-before-completion` | 单次验证（一条命令/一个声明）；stage-gate = 阶段级聚合（整份 spec 的 DoD）——先单点后聚合 |
| `executing-plans` | 执行计划（逐任务实现）；stage-gate **只验不执行**——执行完才轮到门禁 |
| `audit-item` | 门禁核对 open 审计项；新发现由 code-review/审计入账后，下次门禁枚举 |
| `coverage-matrix` | 门禁检查矩阵存在与一致；矩阵更新由 coverage-matrix 技能负责 |

## 完成标准

- [ ] 每条 DoD 断言都有执行结果（PASS/FAIL/未验证）+ 新鲜证据
- [ ] FAIL 只报告不修复；差异清单具体到断言与证据
- [ ] gate 报告已落盘 `docs/audits/stage-gate-S{N}-YYYY-MM-DD.md`
- [ ] 未验证项显式列出原因（CI 不可查/人工验收未做）
- [ ] spec 缺失时报告「无法门禁」而非假装跑过

## 反模式

- 声称「全绿」却没跑命令（违反 verification-before-completion）
- FAIL 顺手修掉——门禁变开发，失去中立性
- 用上次的输出/别人的报告当本次证据
- 只跑 L1 跳过行为验收、审计核对、push 状态
- 对不存在的 spec「照常跑」——应报告 spec 缺失
- 把「未验证」标成 PASS

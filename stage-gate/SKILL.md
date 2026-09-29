---
name: stage-gate
description: >-
  Run a stage-completion gate for staged delivery (spec-kit): read the stage spec's
  DoD assertions and execute each one — unit tests, dual tsc, interaction tests,
  behavioral acceptance, coverage matrix, open audit items, push state — reporting
  PASS/FAIL per assertion with fresh command evidence. Verifies only, never fixes.
  Use when a stage is claimed complete or the user asks to run the stage gate.
  NOT for: verifying one completion claim in isolation, or carrying out a written
  plan task by task.
slug: stage-gate
version: 1.1.1
displayName: stage-gate
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

八类断言（L1 全量/L2 契约/L3 交互/行为验收/覆盖矩阵/审计状态/决策日志/push 状态），每条证据须「命令→输出尾部→exit code」三件套（类型×判定方法×证据形式全表见 [references/assertion-evidence.md](references/assertion-evidence.md)）。

**嵌套断言**：行为验收下的 `- [ ]` 子条目逐条执行，不得合并成一条「行为验收通过」。

## Gate 报告（唯一产出）

`docs/audits/stage-gate-S{N}-YYYY-MM-DD.md`：

```markdown
# Stage Gate S{N} 报告

- 日期 / spec 路径 / 基线 commit（阶段首 commit^，如有）
- 结论：全绿 ✓ | 有 FAIL ✗ | 有未验证

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

---

## 如何调用（显式示例）

无参数面——对话式触发。最可靠开口方式：

- 「跑 S2 阶段门禁」/「run the stage gate for S2」
- 「S3 声称完成了，过一遍 DoD」
- 「阶段收口前自查 S1」

未指明 N 时从语境推断（最近 stage-spec、当前分支上的阶段收口讨论）；推不出就问一句「哪个 S 阶段」，**不许**猜一个 N 就开跑。

## 最短真实样例

**前置**：`docs/design/stage-specs/S2.md` 存在且 DoD 节有 `- [ ]` 断言；仓库在 `apps/desktop` 有 `npx vitest` 可跑。

**用户说**：「S2 完成了，跑阶段门禁。」

**执行摘录（证据长什么样）：**

```
断言 1「L1 全量绿」 → PASS
  证据：npx vitest run（apps/desktop）→ Tests  344 passed (344) / exit code 0
断言 2「L2 双跑 0 error」 → PASS
  证据：npx tsc -p tsconfig.json --noEmit → (无输出) exit 0；tsconfig.main.json 同
断言 3「交互测试 31/31」 → FAIL
  证据：npx playwright test --project=interaction → 29 passed, 2 failed / exit 1
差异清单：#3 期望 31/31；实际 29/31；证据：…failed(2) 输出尾部…
结论：有 FAIL ✗ —— 差异清单交回开发，不修。
```

**产出**：`docs/audits/stage-gate-S2-2026-09-29.md`（模板见上节），每行断言都有「命令→输出尾部→exit code」三件套。若你的报告里某条断言没有这三件套，视为门禁没跑完，重跑该条。

## 失败闭集（可观察出口）

| 情形 | 出口 |
|------|------|
| spec 不存在（`docs/design/stage-specs/S{N}.md` 读不到） | 报告「无 spec，阶段无法门禁」＋读失败的确切路径，收笔。这本身是发现：spec 未写。 |
| 工作目录缺失（`apps/desktop` 不存在） | 报告「门禁前置不满足：<路径> 不存在」，列出仓库根实际内容，问用户正确路径；不得换目录硬跑。 |
| 命令不存在（如 `npx vitest` 报 command not found / 无 node_modules） | 报告「L1 无法执行：依赖未安装」，给修复命令提示（如 `npm ci`，以仓库实际包管理器为准），该断言判**未验证**——不算 FAIL，不装依赖装到一半继续。 |
| 命令长时间卡住（超时） | 对每条命令设观察上限（如 10 分钟无输出进展）：终止，记录「超时于 <命令>」，该断言判**未验证**并在报告单列；不自动重试超过一次，重试须换条件（如加 `--reporter=dot`）并在报告注明。 |
| CI 状态查不到（无 gh/无网络/私有仓） | push 状态断言本地部分照验（`git status`/`git log @{u}..HEAD`），CI 部分判**未验证**并写明「本地不可查」——不假称 CI 绿。 |
| spec 内断言引用的文件缺失（如覆盖矩阵路径不存在） | 该断言 FAIL（期望存在，实际缺失），证据=路径读取失败；不跳过。 |

## FAQ / 错法→改法

| 错法 | 改法 |
|------|------|
| 「全绿」但报告里没有命令输出 | 违反证据先行——每条断言补跑命令、贴输出尾部＋exit code，否则不算 PASS。 |
| FAIL 了顺手修掉再跑绿 | 门禁变开发。FAIL 只记录；修是开发的事，修完**重新跑整份门禁**（不是只重跑失败项）。 |
| 只重跑上次失败的那几条 | 门禁聚合的是整份 spec——重跑必须全量逐条，防回归。 |
| 把「未验证」混进 PASS/FAIL | 三态分开列。判未验证的必须写明原因（依赖缺失/超时/CI 不可查/人工验收未做）。 |
| 行为验收的子条目合并报「通过」 | 嵌套 `- [ ]` 逐条执行、逐条给证据；合并报告=门禁未完成。 |
| 对普通用户只甩专业差异清单 | 差异清单每条附「下一步」一句：指向修复责任（哪个文件/哪类测试/哪个流程），但**不替开发修**。 |
| 用上次的报告日期命名本次报告 | 报告文件名必须用**本次**运行日期；复用旧文件=证据污染。 |

## NOT for（边界收紧，每条可观察）

- **不修代码/测试/spec**——可观察：门禁会话结束时仓库工作区无本技能产生的改动（gate 报告文件除外）。
- **不验单条完成声明**——单点验证走 `verification-before-completion`；本技能只吃整份 stage-spec 的 DoD 节。
- **不执行计划任务**——`executing-plans` 的活；门禁在执行完之后才开始。
- **不做新问题入账**——门禁中撞见的新问题只写进报告「差异清单/备注」，由 code-review/审计入 `audit-item`，下次门禁枚举；本技能不创建审计项文件。

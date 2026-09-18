---
name: problem-handling
description: >-
  Problem handling: one evidence-driven pipeline from a reported symptom to a shipped fix —
  evidence-first intake, root-cause tracing (5 Whys plus RCA tools, falsifiable experiments),
  cognitive-bias defenses, dual-channel research, severity grading with a P0/P1 restore-first fast
  path, classify and scope, workaround-vs-permanent-fix decision, TDD fix, verification, and a
  blameless close with known-error capture plus a 3-strikes design escalation. Use when a problem,
  bug, error, UX complaint, or behavior gap is reported, before jumping to a fix. NOT for:
  code-bug root cause alone — use systematic-debugging.
slug: problem-handling
version: 1.0.0
displayName: problem-handling
---

# 问题处理（Problem Handling）

> 单链四阶段：**诊断 A → 分级与决策 B → 修复与验证 C → 收尾 D**。
> 铁律：**每个修复可追溯到证据**（没定位不修）；**同一症状修三次就停下问设计**。
> **诊断阶段不直接修**；进入修复先分级（P0/P1 先恢复服务）。

## 触发时机

用户反馈问题时**立即进入本流程**（不直接动手改）：
- 「体验完毕/体验终止」+ 反馈；「有问题/报错/卡住/失败/异常/不太对」
- 「先看看日志/记录」「分析一下」「怎么回事」「根因是什么」
- 任何 bug / UX 投诉 / 行为偏差——**先诊断、再分级、后修复**

## 核心原则

1. **证据 > 印象**——先看日志/记录/trace 还原现场，不凭印象猜
2. **根因 > 症状**——现象→根因→根因的根因（为什么×N），假设须实测证伪
3. **通用 > 特判**——不兜底/白名单穷举，找通用机制（修环境不修命令、修配置不修单例）
4. **调研 > 直觉**——多源交叉验证（≥2 独立渠道 + 官方文档 + 源码 + 实测）
5. **语境 > 抽象**——方案放当前项目/环境语境检验（多项目并行/宿主隔离/环境统一）
6. **小步 > 大改**——决策清单 → 一个一个来
7. **闭环 > 发散**——改完盘点「还剩下什么没解决」
8. **定位 > 修复**——`No fix without location`：说不清哪个组件哪步失败，就别修
9. **恢复 > 追责**——P0/P1 先恢复服务（回滚/flag/降级），根因调查可延后；复盘**无责**（追责杀死教训）
10. **不修症状**——同一症状修 3 次 → 停止，升级到设计/系统层（含环境/流程/工具的多因素）

## 阶段 A · 诊断（不直接修）

**A1 现场还原（证据先行）**：先读日志/记录还原现场。证据形态按可观测性成熟度取用：结构化日志（`tail <log> | jq`）→ 关联 trace/span（按链读，不只 grep 单点）→ metrics（基线对比）→ 复现路径。**按时间顺序完整读**，找全问题（不只是眼前这一点）。

**A2 根因深挖**：现象→根因→根因的根因，每层问「为什么」；同时问**直接诱因与潜伏条件**（环境/流程/工具层）。可选 RCA 工具按复杂度取用：5 Whys（线性）→ 鱼骨图 Ishikawa（多因素）→ 故障树 FTA（条件组合）→ Kepner-Tregoe IS/IS NOT（划边界）。**实测证伪不猜**：把根因变**可证伪预期**，跑实验（倾向推翻假设的实验，Popper）；二分/最小化（delta debugging）而非穷举。
- A2 是**迭代循环**：假设清单 → 逐条证伪 → 不收敛回 A2（假设被推翻 = 进展）。
- **证据不足分支**：无日志/无法复现 → 显式标 `unverified` + 向用户索取复现路径/环境；拿不到证据就不给根因结论（「无法复现」是有效结论，继续分析=编造）。

**A3 方案求真**：拒绝特判找通用机制；**双渠道尽调**（≥2 互不依赖来源一致才定）；项目语境检验；完整性审视（记录？复用？单源？——解决即沉淀，KCS 视角）。

## 阶段 B · 分级与决策

**B1 严重度分级（先分级！）**

| 级 | 含义 | 响应 |
|----|------|------|
| **P0** | 阻断全部用户 / 数据损坏 / 安全事件 | 立即处理；**先恢复服务再深挖**；修复+验证+复盘 |
| **P1** | 主要路径不可用 | 尽快；workaround 恢复优先，永久修复跟进 |
| **P2** | 次要功能受损 / 体验明显劣化 | 常规，按计划修 |
| **P3** | 小瑕疵 / 边缘场景 | 可排队 |

- 影响面判断基于**证据**（日志/复现/报告量），不凭感觉；影响面扩大 → **升级严重度并告知相关方**。
- **Incident vs Problem（ITIL）**：P0/P1 是**事件**——先恢复（回滚/flag/降级），根因调查可延后；根因治理是**问题**——**恢复 ≠ 结束**，问题条目须继续到永久修复或裁决。

**B2 分类与范围**：类型 = 单点 / 逻辑错 / 交互 UX / 设计架构；范围 = 行 / 函数 / 模块 / 项目 → 决定修复深度（**范围纪律**：单点 bug 就一行修，不顺手重构）。

**B3 先自己想（Draft before research）**：研究用于验证/证伪，不替代思考。UX/交互类问题**必须**调研（同类产品行为 + 用户日志），不能只读代码。

**B4 workaround vs 永久修复（决策表）**

| 情形 | 决策 |
|------|------|
| P0/P1、根因未明 | 先 workaround 恢复（回滚/flag/降级），根因调查继续 |
| 根因已知但修复风险高 | workaround + 永久修复排期（**跟踪项必建**） |
| 根因已知、修复小且可测 | 直接永久修复（TDD） |
| 同一症状第 3 次 workaround | 停止 workaround → 升级为设计/系统问题（3 strikes） |

> **workaround 是状态不是出口**：恢复服务后，永久修复保留跟踪项（ticket/audit item）直到上线验证。

## 阶段 C · 修复与验证

- **C1 TDD**：先写**失败测试**（复现缺陷），再最小改动。
- **C2 最小改动**：按 B2 范围，不加戏。
- **C3 验证**：跑 verifier（产生 pass/fail 的检查）；**全量回归保持绿**（见 `verification-before-completion`）。
- **放行控制**：修复合入前过 C3；**发布/放行是独立决策**——变更前确认**回滚预案**（改了什么可回退、回退命令）。

## 阶段 D · 收尾

- **D1 无责复盘**：一行教训进 handoff/decision-log（追责杀死教训）。
- **D2 known-error 沉淀**：复发症状 → 建跟踪问题 + known-error 备注（下次可复用的知识）。
- **D3 回填**：ticket / handoff delta / `audit-item`（永久修复跟踪项入账，供门禁枚举）。
- **D4 3 strikes 升级**：同症状第 3 次 → 上移一层（单点→模块→设计）。
- **D5 持续盘点**：「还剩下什么没解决」——按严重度列表，用户选下一步。

## 认知偏差防御（贯穿 A2–A3）

| 偏差 | 防御 |
|------|------|
| 确认偏差 | 每个根因假设列**可证伪预期** + 至少一条 non-confirmatory 证据；主动找反例 |
| 锚定 | A1 完整顺序读后再下结论；IS/IS NOT 划边界防过早锚定 |
| 可得性 | 候选原因按**证据强度**排序，不按「刚见过」排序 |

## 输出形式

| 阶段 | 产出 |
|------|------|
| A | 分析汇报（现象/证据/根因/方案对比 + 反例清单）——**不修**，等确认 |
| B | 分级 + 决策清单（编号 + 现象/根因/候选方案 + 推荐优先级） |
| C | 失败测试 → 最小修复 → verifier/回归结果 |
| D | 未解决问题盘点表（已解决 ✓ / 未解决 按严重度）+ 一行无责教训 |

## 反模式

- 收到反馈直接动手改（跳过诊断）
- 只看局部不完整读记录（漏问题）；停在表面症状
- 用特判/白名单穷举；单源调研当结论；假设只找支持证据
- 方案不检验项目语境；一次改一堆
- 没定位就修；改超范围；无回归检查就收尾
- workaround 无跟踪项；恢复服务就当结束（event closed, problem open）
- 发布无回滚预案；复盘追责；复发不沉淀 known-error

## 与相邻技能边界

| 技能 | 边界 |
|------|------|
| `problem-handling`（本技能） | 端到端：诊断 → 分级 → 处置 → 收尾 |
| `systematic-debugging` | **代码缺陷**路径的根因调查协议（复现→假设→验证）——本技能 A2 在代码路径内调用它 |
| `verification-before-completion` | C3 验证协议——完成前验证 |
| `audit-item` | D3 永久修复/跟进项入账（被 stage-gate 枚举）|
| `decision-log` | D1 无责教训/语义裁定留痕 |

## 完成标准

- [ ] 已定位（组件 + 失败环节）且根因有证据（不是猜测）
- [ ] 严重度已分级；P0/P1 走了恢复优先路径
- [ ] workaround（若有）有跟踪项；永久修复上线并验证
- [ ] 修复带失败测试；全量回归绿
- [ ] 收尾：无责教训一行 + 回填（ticket/handoff/audit-item）+ 剩余问题盘点

## 方法论来源（2026-08 调研）

- 证据驱动调试：Zeller delta debugging（二分最小失败输入，TSE 2002）；Why Programs Fail（假设→预测→实验）
- RCA 工具谱系：丰田 5 Whys、Ishikawa 鱼骨图、FTA、Kepner-Tregoe IS/IS NOT
- 事故调查：James Reason Swiss Cheese；HFACS 人因分层；David Woods「root cause is a myth」；Hollnagel ETTO
- SRE/ITIL：Google SRE blameless postmortem（detect→respond→remediate→recover→learn）；ITIL 4 incident vs problem
- 严重度：行业 P0-P3 惯例；IEEE 1044 缺陷严重度/优先级矩阵；Boehm 缺陷成本定律
- 可观测性：OpenTelemetry（logs/metrics/traces 统一与 span 关联）；Honeycomb high-cardinality 调试
- 认知偏差：软件工程 confirmation bias/anchoring/availability 实证（arXiv 2508.11278）
- 修复质量：修复引入回归缺陷实证（arXiv 2207.01942）
- 知识沉淀：KCS（Knowledge-Centered Service）Solve/Evolve——解决即沉淀

---
name: skill-eval
description: >-
  Behaviorally evaluate a skill in two modes: pass-rate (define 3-5 representative tasks,
  run each N>=3 times with and without the skill loaded in fresh agents, compare pass
  rates) and trigger rate (build ~20 queries — 8-10 should-trigger plus 8-10 near-miss —
  run each 3 times, score per-query trigger rate). Both report a table plus concrete
  improvement items that feed back into the skill's SKILL.md. Use when a skill changes, at
  quarterly evaluation, when accepting a new skill, or when description triggering looks
  unreliable. Because it writes back into other skills' SKILL.md it is USER-INVOKED ONLY:
  the agent must not auto-invoke it — the user runs it explicitly. NOT for: static
  description-vs-body compliance review of a SKILL.md.
slug: skill-eval
version: 1.1.0
displayName: skill-eval
disable-model-invocation: true
---

# Skill Eval（高频 skill 动态评估：行为 pass-rate ＋ 触发率）

## 定位

高频 process skill 的**动态评估**，两模式互补：① **行为 pass-rate**（有/无 skill 各跑 N 次 → 对比 → 失败案例反哺正文）；② **触发率 trigger rate**（描述在该触发时是否触发、不该触发时是否误触发）。与 `skill-description-audit`（静态描述合规）互补。

## 何时使用

- skill 变更后（行为是否真变好）
- 季度评估（基线节奏）
- 新 skill 验收（交付后先建基线）
- 描述触发不可靠时（应触发不触发／误触发）

## 输入

- 目标 skill（首批：code-review / project-handoff / writing-plans / stage-gate）
- 评估记录目录：`.scratch/neonforge-v1/skill-eval/<skill>-<YYYY-MM-DD>/`

## 流程

```
- [ ] 1. 定义代表任务：3-5 个（见下节）
- [ ] 2. 无 skill 基线：每任务跑 N 次（N≥3，fresh agent、无对话种子）
- [ ] 3. 有 skill 组：同任务同 prompt 跑 N 次（fresh agent + 加载目标 skill 指令）
- [ ] 4. 逐次判定 pass/fail（按任务 AC，机器可验证优先——文件存在/输出匹配/命令结果）
- [ ] 5. 汇总 pass-rate 对比表（任务 | 无 skill | 有 skill | Δ）
- [ ] 6. 失败案例分析：成功/失败样例各取代表，定位 skill 改进点
- [ ] 7. 产出报告 + 改进项写回 skill SKILL.md（或作为下轮验收项）
- [ ] 8. 结果入 SKILLS-MAP 或该 skill README（基线表）
```

## 代表任务定义（3-5 个）

每个任务 = 一段**独立 prompt** + 可判定的 AC：

| 要求 | 说明 |
|------|------|
| 覆盖核心能力 | 任务必须命中 skill 的标志性能力（如 stage-gate 的「跑 S{N} 门禁」） |
| 有代表性失败模式 | 选任务时预判「无 skill 会怎么错」（漏验证/散文断言/只验不修） |
| AC 机器可验证 | 优先：文件存在且含 X / 命令输出匹配 / 断言数正确；次选：结构化报告字段齐全 |
| 现实规模 | 用真实仓库的最小场景（同仓库 fixture），不用玩具示例 |

## 运行纪律

- **fresh agent**：每组每次都是新会话（无对话种子）——防记忆污染；有 skill 组只多加载目标 skill 指令，其余提示词逐字一致。
- **同 prompt 逐字一致**：两组差异仅「是否加载 skill」。
- **判定者独立于执行者**：pass/fail 由 AC 判定，不看「agent 自报成功」（verification-before-completion）。
- 记录：每次运行的任务 prompt、AC、产物路径、判定——落盘评估目录，报告可复核。

## 报告（pass-rate 对比表）

```markdown
# Skill Eval: {skill}（{date}）

| 任务 | 无 skill (N) | 有 skill (N) | Δ | 结论 |
|------|-------------|-------------|---|------|
| 任务 1 | 1/3 | 3/3 | +2 | skill 有效 |
| 任务 2 | 2/3 | 2/3 | 0 | 无效/无差异——改进点：… |

## 失败案例分析（反哺）

- 有 skill 仍失败 ×2 → 改进项：{具体到 SKILL.md 哪节缺什么}

## 改进项（低分 skill 必出）

1. …（具体、可验收）
```

## 动态触发实测（trigger-eval）

评估「描述在该触发时触发、不该触发时不触发」。方法（agentskills.io《Optimizing skill descriptions》）：

- [ ] 1. **查询集 ~20 条**：8–10 条**应触发**（点名该 skill 能力的真实请求）＋ 8–10 条**近似不应触发**（话题相邻但属别的技能／无技能）。
- [ ] 2. 每条跑 **3 次**（fresh agent，仅带该技能描述面），**trigger rate** ＝ 触发次数/3，阈值 **0.5**。
- [ ] 3. 按 **60/40** 切 **train / validation**；只据 train 改 description，在 validation 上复测（防过拟合）。
- [ ] 4. 迭代约 **5 轮**：改 description（补 WHEN／加反触发）→ 重跑 → 直到 validation 上应触发组全过、不应触发组全不触发。
- [ ] 5. 落盘 `.scratch/<项目>/skill-eval/<skill>-trigger-<YYYY-MM-DD>/`（查询集＋逐次结果）；报告附 trigger rate 表。

判读：应触发组漏触发 → WHEN 过窄／触发词缺；不应触发组误触发 → WHEN 过宽／缺反触发。静态面另有跨技能混淆闸 `scripts/trigger-confusion-test.py`（T1/T2/T3）——它不替代本节的按查询集实测。

## 验收

- [ ] 每任务有/无 skill 各 N≥3 次（总计 ≥6 次/任务），记录落盘
- [ ] 输出 pass-rate 对比表（含 Δ 与结论）
- [ ] 低分 skill（有 skill 无显著提升或仍失败）得到具体改进项
- [ ] 触发实测（如做）：查询集 ~20（含 8–10 近似反例）、每查 3 跑、trigger rate 表＋validation 复测
- [ ] 改进项已反馈（写回 SKILL.md 或列入下轮验收）
- [ ] 基线结果入 SKILLS-MAP / skill README

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| `skill-description-audit` | 静态描述合规（description↔正文）；skill-eval = 动态（pass-rate ＋ trigger rate）——先合规后行为 |
| `verification-before-completion` | 判定纪律来源（AC 证据判定，不信自报） |
| `delegated-research` | 不适用——评估是受控实验，不是调研 |

## 反模式

- N<3 或两组条件不一致（结论无统计意义）
- 用同一会话跑两组（skill 指令泄漏到基线组）
- 判定凭「感觉」不按 AC（自报成功当 pass）
- 只报对比不反哺（评估完 skill 没变好）
- 任务不覆盖标志性能力（评估了但没评估到点子上）
- 触发查询集全是正例（无近似反例）——测不出误触发
- 用 train 集自评（读了 validation 再改 description＝过拟合）

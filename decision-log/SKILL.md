---
name: decision-log
description: >-
  记录或检索架构决策记录（ADR）——Nygard 模板（背景/决策/后果），带
  proposed/accepted/superseded/rejected 状态机，写入 docs/decisions/NNN-slug.md 并更新索引表；
  若项目保有交接存储，则在其中留一条引用行。当阶段内发生语义裁定或用户说
  「记录裁定」「写进决策日志」「ADR」或要查「决策 X 的现状」时使用。不适用于：
  撰写会话交接本身——交接存储只引用 ADR 编号、绝不复制正文。
slug: decision-log
version: 1.1.0
displayName: decision-log
---

# Decision Log（ADR 记录/查询）

## 定位

阶段内任何**语义裁定/拍板/设计裁决** → 当阶段写成 ADR（Nygard 模板），集中进
`docs/decisions/`，让「决策 X 的现状」可查询：status + 历史链（superseded 不删除）。

## 何时使用

- 用户说「记录裁定」「这个决策写进决策日志」「ADR」
- 阶段内发生语义裁定（审计裁定、拍板项、设计裁决）——**当阶段记，不攒批**
- 查询：「决策 X 的现状」「这个决定后来改了吗」

## 触发纪律

每次语义裁定后 3 分钟内完成记录。拿不准是否够格 → 记（轻量；比漏记好——历史链靠它）。

## 最短真实样例

**前置：** 阶段内刚发生一条裁定（如「S1.1 审计裁定：C8 按 A 案落地」）；`docs/decisions/` 已存在。
**调用：** `记录裁定：审计项 C8 裁定走 A 案，理由是测试面覆盖不足，来源 §4.1 审计报告`
**产出摘录：**

```markdown
# 004 — C8 按 A 案落地（来源：§4.1 审计报告）

- Status: accepted
- Date: 2026-09-29

## Decision
- C8 采用 A 案；B 案（逐条改写）不采用——测试面覆盖不足
```

**完成判据：** `docs/decisions/004-*.md` 存在且含 status/date/相关；`docs/decisions/000-decision-log.md` 索引已加一行（#004）。

## 失败闭集

- **`docs/decisions/` 不存在**：本项目未建决策目录 → 只报告「无 `docs/decisions/`，未写入」并停；**不自主建目录**（建/迁存储须用户显式调用）。
- **索引缺失（`000-decision-log.md` 不在）**：先补索引表头再写 ADR，并在产出里注明「索引为本次新建」。
- **项目根/路径不明确**：问一句「项目根在哪」；不猜路径乱写。
- **拿不准是否够格记 ADR**：记（轻量）；宁多勿漏——历史链靠连续。

## 错法 → 改法

| 错法 | 后果 | 改法 |
|---|---|---|
| 裁定发生了但不记录（「等有空」） | 历史链断，查询返回空 | 当阶段记，3 分钟内 |
| 把 ADR 全文复制进 `.handoff/`（手改真源） | 双源漂移 | 存储只引用 ADR 编号，不复制内容 |
| 被 superseded 后删除旧 ADR | 链断，无法追溯 | 旧文件保留，状态改 superseded |
| 编号跳号或覆盖旧文件 | 引用悬空 | 索引最大号 +1，只追加 |
| 未发生裁定也自主记一条 | 噪音淹没真裁定 | 仅语义裁定发生时（或用户点名）记 |

**「语义裁定」通俗版：** 凡「两种做法都行、最终拍了板」的时刻——审计项怎么处置、边界怎么划、A 案还是 B 案——就是语义裁定；纯事实陈述（「测试失败了」）不算。

## 流程（记录）

```
- [ ] 1. 编号：docs/decisions/000-decision-log.md 索引最大号 + 1 → NNN
- [ ] 2. 文件名：NNN-slug.md（slug = 决策主题 kebab-case，如 001-rejectstreak-semantics.md）
- [ ] 3. 写 ADR（Nygard 模板 + 状态机，见下）
- [ ] 4. 更新 000-decision-log.md 索引表（# | 标题 | 状态 | 日期）
- [ ] 5. 交接存储同步（**条件步**）：项目**已有** `.handoff/` 存储时，为这条 ADR 登记**一条编号引用**（不复制内容）——
      条目标题镜像 ADR 序号（`NNN — {标题}`）便于两侧对照，正文写 ADR 位置 `docs/decisions/NNN-slug.md`；
      决策条目**不收独立引用字段**（把路径写进标题/正文即可），改判**另开一条**、取代关系由存储侧承载。
      写入口与命令形见 [`project-handoff`](../project-handoff/SKILL.md) 的写槽表（唯一权威面，本件不复制其参数面）。
      **无该存储 → 跳过本步**（只留 ADR 与索引），**不自主建存储**：建/迁由该件定义、须用户显式调用
```

## ADR 模板（Nygard）

```markdown
# NNN — {决策标题（含来源节，如 §4.1 C8）}

- Status: proposed | accepted | superseded | rejected
- Date: YYYY-MM-DD（{触发语境，如 S1.1 审计裁定}）
- 相关：{设计节/审计报告引用——路径，不复制}

## Context

问题/冲突背景：字面冲突、可选方案、触发证据（测试失败、审计发现）。

## Decision

- 决定内容（分条）
- 边界（什么不在本决策内）
- 落实方（哪个阶段/技能接线）

## Consequences

- 正面/负面后果
- 后续需要做的（如 S3 接线实现 X）
```

## 状态机

```
proposed ──→ accepted ──→ superseded
    └──────→ rejected
```

- **superseded**：被新决策取代——新 ADR 的「相关」注明「supersedes NNN」；旧 ADR 状态改 superseded，**不删除**（历史链保留）。
- **rejected**：评估后不采纳（proposed 阶段否决）。
- 查询时返回：当前 status + 完整链（NNN → superseded by NNN+1 → …）。

## 防双源

- `.handoff/`（项目工作存储）与设计文档只引用 ADR 编号（如「001 已定」），不复制 ADR 内容。
- spec（stage-spec）引用 ADR 编号记录 DoD 变更来源。

## 边界（分工）

| 相邻技能 | 分工 |
|---------|------|
| [`project-handoff`](../project-handoff/SKILL.md) | **交接存储的工具方**：本件只定「引一条编号引用、不复制内容」这条契约，`.handoff/` 结构与写命令参数面归它定义；阶段裁定 → 本技能写 ADR |
| `stage-spec` | DoD 变更需当阶段 ADR 记录——spec 引用编号 |
| `stage-gate` | 门禁检查「决策日志同步」断言 = 索引最新 |

## 完成标准（记录）

- [ ] `docs/decisions/NNN-slug.md` 存在（Nygard 三节 + status/date/相关）
- [ ] `000-decision-log.md` 索引已加行（#/标题/状态/日期）
- [ ] 3 分钟内完成（轻量流程，不追求篇幅）
- [ ] 无敏感信息（凭据不写值）

## 完成标准（查询）

- [ ] 返回决策 status + 历史链（含 superseded 链）
- [ ] 引用来源（设计节/审计/相关 ADR），不搬运全文

## 反模式

- 裁定发生但不记录（等「有空」——历史链断）
- 记录超过 3 分钟（过度润色；ADR 不是论文）
- superseded 后删除旧 ADR（链断）
- 往 `.handoff/` 复制 ADR 内容（双源）
- 项目无 `.handoff/` 就为登记引用而自建存储（建/迁须用户显式调用；本件**不建存储**——有存储时它照常经该件写入条目）
- 编号跳号/覆盖旧文件

---
name: ddd-subdomains
description: "Identify business capabilities and classify subdomains (Core/Supporting/Generic), producing core-domain declarations, ownership recommendations, and bounded-context boundary candidates. Use when partitioning core/supporting/generic subdomains, or re-partitioning when god-context or circular-dependency signals suggest a subdomain misfire."
risk: safe
source: self
tags: "[ddd, strategic, subdomains]"
date_added: "2026-05-08"
slug: ddd-subdomains
version: 1.1.0
displayName: ddd-subdomains
---

# DDD Subdomains

> English version: [English](SKILL.en.md)

## 使用时机

- 已完成领域发现（事件流与命令/事件候选已就绪），需要将领域切分为子域。
- 需要明确"什么是核心竞争力、什么可以外购/复用"的战略决策。
- `ddd-context-map` 报告"上帝上下文"或子域误分时，作为回溯目标重新执行。

## 输入要求

- **必需**：事件流、命令/事件候选、边界线索（来自 `ddd-discover`）。
- **可选**：当前系统能力清单或模块清单、业务差异化假设、竞争优势描述（来自 `ddd-scope`）。

**输入缺失时的可观察出口**：若必需工件缺失或事件流为空，**不要**自行臆测分类。输出一段缺失声明：写明"缺少 <工件名>，来自 `ddd-discover`"，并列出为补齐需要跑的入口（无事件流 → 先跑 `ddd-discover`；价值主张不清 → 先跑 `ddd-scope`），然后停下等待。收到补齐材料后从头重跑流程。

**NOT for（不适用，转交对应技能）**：

- 还没做领域发现、没有事件流 → `ddd-discover` 先行。
- 业务价值主张本身模糊 → `ddd-scope` 先行。
- 已确定子域、要做上下文划分 → `ddd-contexts`；本技能产出的是子域到上下文的**候选**，不定稿上下文。
- 本技能只做战略层切分，不做战术建模（聚合/实体/不变量 → `ddd-aggregates`）。

## 流程

1. **提取能力集**：从事件流中抽取业务能力（Capability），去重合并同义能力。
2. **属性标注**：为每个能力标注业务价值、复杂度、变更频率、外部依赖程度。
3. **分类**：按 DDD 子域类型分类——Core（核心差异化）、Supporting（必要但非差异化）、Generic（通用可复用）。
4. **核心域声明**：形成核心域声明文档——为什么它是核心、衡量指标、长期演进方向。
5. **所有权建议**：建议团队归属，对齐语言边界与一致性边界；标注跨团队协作点。
6. **输出边界候选**：为 `ddd-contexts` 提供子域到上下文的初步映射建议。

## 输出

| 工件       | 结构要求                                                                   |
| :--------- | :------------------------------------------------------------------------- |
| 能力清单   | 表格：能力、说明、关联事件、上下游依赖                                     |
| 子域分类表 | 表格：能力/能力组、子域类型（Core/Supporting/Generic）、分类理由、建议投入 |
| 核心域声明 | 1 页以内：价值、边界、衡量指标、风险、演进方向                             |
| 所有权建议 | 表格：能力/子域、建议团队、依赖方、协作方式                                |
| 边界候选   | 列表：子域到上下文的初步映射建议                                           |

## 校验清单

- [ ] 每个能力有分类理由，业务方与技术方均可接受
- [ ] 核心域声明包含可衡量的业务指标
- [ ] 至少识别 3 个跨团队协作点并给出协作建议
- [ ] Core 子域数量 ≤ 总子域的 1/3（核心域不应过多）
- [ ] 边界候选可被 `ddd-contexts` 直接消费

## 回溯触发

- 无法区分 Core 与 Supporting（所有能力看起来同等重要） → 回溯至 `ddd-scope`，业务价值主张需重新澄清。
- 被 `ddd-context-map` 触发回溯：循环依赖或"上帝上下文"暗示子域划分有误。

## 示例

### 调用示例

```text
@ddd-subdomains
基于以下事件流和边界线索，帮我识别子域并分类：
[粘贴 ddd-discover 的事件流表与边界线索]
请输出能力清单、子域分类表、核心域声明与所有权建议。
```

### 最短真实示例（前置 → 调用 → 产出摘录）

前置：`ddd-discover` 已产出事件流（下单、支付、库存扣减、对账、通知推送等事件）与边界线索。

调用：

```text
@ddd-subdomains
事件流：OrderPlaced / PaymentCaptured / StockReserved / StatementReconciled / NotificationSent …
边界线索：对账有独立合规截止日；通知走第三方网关。
```

产出摘录（应长这样）：

```text
| 能力/能力组     | 子域类型  | 分类理由                     | 建议投入 |
| 订单履约        | Core      | 差异化流程，变更频率高       | 自建团队 |
| 对账/结算       | Supporting| 必要但非差异化，规则相对稳定 | 1-2 人   |
| 通知推送        | Generic   | 通用能力，可直接外购         | 复用     |
核心域声明（摘录）：订单履约是核心，衡量指标 = 履约时长与差错率 …
边界候选：订单履约 → OrderContext（供 ddd-contexts 定稿）。
```

## 常见错法 → 改法

| 错法 | 改法 |
| :--- | :--- |
| 没有事件流就按组织架构图直接切子域 | 停在缺失声明，先走 `ddd-discover`；组织架构不是分类依据 |
| 把一半以上子域标成 Core | 核心域 ≤ 总子域的 1/3；超限说明价值主张没收敛，回溯 `ddd-scope` |
| 所有能力"看起来都重要"，强行平均分 | 触发回溯：无法区分 Core/Supporting → `ddd-scope` 重新澄清价值主张 |
| 把边界候选直接当上下文定稿 | 候选只是输入；上下文划分由 `ddd-contexts` 定稿 |
| 按技术分层（前端/后端/DB）当子域 | 子域按业务能力切分，与分层无关 |
| 用户没要求就自动跑子域划分 | 本技能仅在用户点名或上游技能（`ddd-context-map`）回溯触发时执行，不自主触发 |
| 输出分类却不写理由 | 每条分类必须带理由，且校验清单要求业务方与技术方均可接受；写不出理由就回溯 |

---
name: project-handoff
description: >-
  Generate/update a project engineering handoff document (HANDOFF.md) — reference-style delta structure:
  metadata / snapshot / next steps / immediate ops (commands + pitfalls) / reference index / maintenance
  rules. Records only delta not already in docs or commit log; one-line entries (details in commit
  messages); never copies (anti-dual-source); desensitized. Maintenance rules: update timing, one-line
  deltas, rolling archive to HANDOFF-ARCHIVE.md, backfill. Use when handing off across sessions/tools,
  generating or updating HANDOFF.md, or capturing project delta state. NOT for: resuming prior work —
  that belongs to project-intake.
---

# 项目交接文档（Project Handoff）

## 角色

你是交接文档作者。为项目生成/更新**工程交接文档**（HANDOFF.md），让接收方（另一 agent/工具/新 session）无需重读全部文档即可继续工作。**只记 delta，引用不复制。**

## 何时使用

- 工具切换（如 Deep Code → Cursor）、跨 session 交接、委托其他 agent 继续工程；
- 项目到重大里程碑（ticket 完成、阶段切换）需要记录进度；
- 用户要求「交接」「handoff」「生成交接文档」时（「继续之前的工作」属接收方语境，由 project-intake 承担）。

## 硬约束（不可妥协）

1. **防双源（核心）**——既有文档（README/docs/specs/plans）**与 commit message** 已有的内容，**一律引用路径/commit hash，禁止复制**；本文件只记「文档集与 commit 都没有的 delta」（决策背景/用户原话/坑/待办）。
2. **delta 优先**——只写接收方不知道的：进度到哪、下一步做什么、验证什么、本会话踩的坑、即时命令、权威入口在哪。
3. **脱敏**——不得含 API Key/密码/PII；引用密钥存储位置时用路径不写值。
4. **位置**——项目根 `HANDOFF.md`（或其他约定位置）；若已存在，更新而非重写（只动易变节）。

## 结构（6 节）

```
1. 交接元信息     日期/交接方/接收方/原因/项目一句话/文档入口链 + 接收方建议动作（git init → .gitignore（node_modules/dist）→ 首次提交 / 先读哪些 artifacts / 用哪个技能维护 / 凭据索取）
2. 当前状态快照  各域状态表（文档/tickets/资产）+ 版本控制状态（git 与否/branch/未提交变更）+ 构建环境状态（依赖/构建产物就绪与否）+ 最近完成（增量一行式 `- [hash] 一句话标题`——详情在 commit message，git log 是详情权威；明示占位/未完成边界）
3. 下一步与验证点 立即待办（引用 tickets AC）+ 外部依赖来源（凭据/配置从哪获取）+ 随后路线 + 风险提醒
4. 即时操作      启动/构建/验证命令 + 已知坑（本会话发现，不回填 docs/ 的）
5. 引用索引      主题 → 权威文档路径表（架构/产品/指标/tickets/审计/上线）
6. 维护规则      更新时机 / 防双源约定（含 commit message 不复制 + §2 一行式规范）/ 滚动归档约定（跨交接周期旧 delta 移 HANDOFF-ARCHIVE.md，§2 只含当前周期）/ 回填约定（ticket 完成 → 回填 ticket + 同步快照）/ 脱敏
```

## 工作流

```
- [ ] 1. 定位索引（README/文档清单）+ 已有 HANDOFF（存在则更新）
- [ ] 2. 收集状态：各域进度（文档完结/ tickets 状态/资产）
- [ ] 3. 识别 delta：对比文档集，找出「文档没有的」（进度/坑/即时命令/验证点）
- [ ] 4. 生成/更新：按 6 节结构；引用索引节指向既有文档路径
- [ ] 5. 脱敏检查：无 Key/密码/PII
- [ ] 6. 引用检查：每处知识确认「引用而非复制」——复制了则改引用
- [ ] 7. 交付：告知位置 + 接收方下一步起点
```

## 反模式

- **复制文档内容**（架构/约定/映射等 docs/ 已有的）→ 造成双源，文档改交接不同步
- **复述 commit message**（§2 最近完成写成长段落重复 commit 详情）→ 造成双源，commit 一改交接就过期；最近完成一律一行式 `- [hash] 一句话标题`，详情写进 commit message（git log 是详情权威）
- 把稳定知识（架构）与易变状态（进度）混写——分层：稳定进引用索引，易变进快照
- 节数堆砌（把「当前验证清单」「路线图」当固定节）——具体状态属快照/下一步，结构保持通用 6 节
- 写 API Key/密码/PII
- 只生成不维护（更新时只动 §2-§4 易变节）
- **版本控制坐标缺失**（未记 git 状态/branch/commit）→ 接收方无历史可查（marcusglee11 原则：commit hash 优先）
- **进度声明含糊**（占位/未实现未明示）→ 接收方误判「已完成」，基于占位继续开发
- **外部依赖来源不明**（API Key/凭据/配置不指来源）→ 接收方瞎找或卡住；应明确「向用户索取/配置文件位置」
- **快照过期未同步**（ticket 完成后 §2 未更新）→ 接收方按旧进度决策；回填约定须含「回填 ticket + 同步快照」

## 完成标准

- [ ] 项目根存在 `HANDOFF.md`
- [ ] 6 节结构齐全；只记 delta，无文档/commit message 内容复制（引用索引节全覆盖）
- [ ] §2 最近完成一行式 `- [hash] 一句话标题`（详情在 commit message）；跨周期旧 delta 已滚动归档（HANDOFF-ARCHIVE.md）
- [ ] 快照/下一步/即时操作准确反映当前状态
- [ ] 版本控制状态已记（git 与否/branch/未提交变更）
- [ ] 构建环境状态已记（依赖/构建产物就绪与否）
- [ ] 占位/未完成边界明示（防接收方误判）
- [ ] 外部依赖来源明确（凭据/配置从哪获取）
- [ ] 快照与 tickets 同步（回填约定含「ticket 完成 → 更新 §2」）
- [ ] 无敏感信息
- [ ] 接收方起点明确（下一步 + 命令 + 建议动作）

## 方法论来源（2026-08 调研 + 实践）

- mattpocock handoff skill：引用 artifacts 不重复、脱敏、suggested skills——「引用不复制」原则来源
- Agent Handoff（marcusglee11）：省 token 优先坐标引用
- YAKStack /handoff：纯文本简报五节（Who/What/Confirmed/In progress/Next）——简洁叙事启发
- NeonForge HANDOFF.md 实践（2026-08-02）：9 节 → 6 节重构——「delta+引用」批判性修正的产物（初版复制了 docs/ 内容被否，重构为引用型）
- **AI 评审反哺（2026-08-02）**：专家评审 HANDOFF.md 发现 4 项 → 技能化：版本控制坐标（§2+反模式）、接收方建议动作（§1，mattpocock suggested skills）、占位/未完成边界明示（§2+反模式）、外部依赖来源（§3+反模式，凭据索取）

---
name: project-intake
description: >-
  Take over a project as the receiving side — read HANDOFF.md and restore context by its 6
  sections (metadata/snapshot/next steps/immediate ops/reference index/maintenance rules;
  snapshot deltas are one-liners — fetch details via git log or the HANDOFF-ARCHIVE.md
  history), execute suggested receiver actions (git init → .gitignore → first commit / read
  tickets / request credentials). Use when receiving a handoff, onboarding onto an existing
  repo, or resuming from HANDOFF.md.
---

# 项目对接（Project Intake）

## 角色

你是交接**接收方**。接手另一 agent/工具/新 session 交接的项目：**先读 HANDOFF.md 恢复上下文，再按其中指引继续工作**。与 `project-handoff`（交接方）对称——交接方写 delta，接收方读 delta。

## 何时使用

- 接手另一 agent/工具交接的项目（如 Cursor 接手 Deep Code 的工程）；
- 新 session 开始，需要快速恢复项目上下文；
- 用户说「继续之前的工作」「接着做」「接管项目」「按 HANDOFF 推进」。

## 硬约束（不可妥协）

1. **先读后动**——接手第一步是定位并读取 HANDOFF.md（或交接文档），**禁止不读直接开工**（会重复探索、漏掉 delta）。
2. **防双源**——HANDOFF 已有的内容**引用不复制**；你的新文档/笔记不得复制 HANDOFF 内容（只记你新增的 delta）。
3. **脱敏**——不得写入/传播 API Key/密码/PII；凭据从用户处索取（或引用存储位置，不写值）。
4. **先确认再动手**——环境就绪检查通过后才进入业务验证；改动前先按 HANDOFF 快照核对当前状态。

## 工作流（7 步）

```
- [ ] 1. 定位 HANDOFF.md（项目根；不存在则先读 README/docs 重建上下文，并提示交接方先生成）
- [ ] 2. 读 6 节：元信息（谁/为什么/建议动作）/ 快照（进度到哪——§2 最近完成是一行式 `- [hash] 一句话标题`，详情不足时 `git log` 查 commit；更早历史在 `HANDOFF-ARCHIVE.md`）/ 下一步（做什么/验证什么）/
        即时操作（命令+坑）/ 引用索引（权威位置）/ 维护规则（回填约定）
- [ ] 3. 复述上下文：向用户确认「当前状态 + 下一步」，核对无误再继续
- [ ] 4. 执行接收方建议动作（HANDOFF §1）：git init → .gitignore → 首次提交 / 读 tickets / 向用户索取凭据
- [ ] 5. 环境就绪检查（HANDOFF §3 首项）：构建通过 + 应用可启动（依赖已装则跳过重装）
- [ ] 6. 执行下一步验证点（对照 ticket AC 逐条跑）
- [ ] 7. 回填闭环：ticket 完成 → 勾选 AC + 标注文档引用兑现 → 同步更新 HANDOFF §2 快照 → 新坑追加 §4
```

## 反模式

- **不读 HANDOFF 直接开工**——重复探索、漏 delta、误判进度
- **复制 HANDOFF 内容**到你的笔记/新文档——造成双源
- **环境未就绪就业务验证**——把环境问题误判为业务缺陷
- **完成后不回填**（ticket/快照）——HANDOFF 过期，下一位接收方误读
- **凭据瞎猜**（从代码/配置搜索 Key）——应向用户索取或引用存储位置
- **改动前不看快照**——基于过期状态做决策

## 完成标准

- [ ] 已读 HANDOFF 6 节并复述上下文（状态 + 下一步）得到确认（§2 一行式 delta 详情不足时查 `git log` / `HANDOFF-ARCHIVE.md` 回溯）
- [ ] 建议动作已执行（git/.gitignore/读 tickets/凭据来源明确）
- [ ] 环境就绪检查通过（构建 + 启动）
- [ ] 验证点完成（对照 ticket AC）
- [ ] 回填完成（ticket AC 勾选 + HANDOFF §2 快照同步 + 新坑入 §4）
- [ ] 未复制 HANDOFF 内容；无敏感信息写入

## 方法论来源（2026-08）

- project-handoff（对称技能）：交接方 6 节结构 → 接收方按同构 6 节恢复上下文；维护规则（回填/防双源/脱敏）双向共用
- mattpocock handoff：交接文档作为下一 session 的起始上下文——接收方视角即「读文档 → 继续」
- NeonForge HANDOFF.md 实践（2026-08-02）：Deep Code → Cursor 交接——接收方需建议动作（git init/.gitignore/读 tickets/Key 索取）与环境就绪检查（4 轮 AI 评审发现的接收方需求）

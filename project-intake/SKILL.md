---
name: project-intake
description: >-
  Take over a project as the receiving side — read HANDOFF.md and restore context by its five
  sections (metadata / snapshot / next steps / immediate ops / reference index; snapshot deltas
  are one-liners — fetch details via git log or HANDOFF-ARCHIVE/ (cycles.md / done.md / pits.md)).
  Execute suggested receiver actions (git init → .gitignore → first commit / read tickets / request
  credentials). Environment re-verification is gated by the env fingerprint: run the bundled
  handoff-lint script `fp check` first — an unchanged fingerprint means skip re-verification, a
  changed one means re-verify only the changed dimensions. Use when receiving a handoff, onboarding
  onto an existing repo, or resuming from HANDOFF.md.
slug: project-intake
version: 1.2.0
displayName: project-intake
---

# 项目对接（Project Intake）

## 角色

你是交接**接收方**。接手另一 agent/工具/新 session 交接的项目：**先读 HANDOFF.md 恢复上下文，再按其中指引继续工作**。与 `project-handoff`（交接方）对称——交接方写 delta，接收方读 delta。

## 何时使用

- 接手另一 agent/工具交接的项目；
- 新 session 开始，需要快速恢复项目上下文；
- 用户说「继续之前的工作」「接着做」「接管项目」「按 HANDOFF 推进」。

## 硬约束（不可妥协）

1. **先读后动**——第一步定位并读取 HANDOFF.md，禁止不读直接开工。
2. **防双源**——HANDOFF 已有的引用不复制；你的新笔记只记新增 delta。
3. **脱敏**——不写 API Key/密码/PII；凭据从用户处索取或引用存储位置。
4. **先确认再动手**——环境就绪后才进入业务验证；改动前按 §2 快照核对当前状态。
5. **环境复验最小化**——用环境指纹决定复验范围：**一致 → 跳过；不一致 → 只复验变化维度**（见下）。
6. **单一进度源**——开工只读 `HANDOFF.md`；`.agents/session.md` 已退役（原 `core-rules` §4，2026-09-17），不要再找它、也不要新建它。

## 工作流（7 步）

```
- [ ] 1. 定位 HANDOFF.md（项目根；不存在则先读 README/AGENTS 重建上下文，并提示交接方先生成）
- [ ] 2. 读 5 节：元信息（谁/为什么/建议动作）/ 快照（域状态表；详情不足时 git log；过期周期见 HANDOFF-ARCHIVE/cycles.md，已修坑见 pits.md）/
        下一步（未完成项/验证什么）/ 即时操作（命令 + 未修坑）/ 引用索引
- [ ] 3. 复述上下文：向用户确认「当前状态 + 下一步」，核对无误再继续
- [ ] 4. 执行接收方建议动作（§1）：git init → .gitignore → 首次提交 / 读 tickets / 索取凭据
- [ ] 5. 环境就绪检查 —— 先跑指纹门控（见下）：一致则跳过复验，不一致只复验变化维度
- [ ] 6. 执行下一步验证点（对照 ticket AC 逐条跑）
- [ ] 7. 回填闭环：ticket 完成 → 勾选 AC → 同步 §2 快照 → 新未修坑追加 §4 → 确认已修/裁决不修当次迁 HANDOFF-ARCHIVE/（坑→pits.md，待办→done.md）
```

## 环境复验门控（指纹）

交接方已在 `.handoff/fp.sha` 写入环境指纹（输入清单 `.handoff/fp.txt`；见 project-handoff）。

- 先跑（`handoff-lint` 为 project-handoff 附带脚本；Windows 用 `.ps1` 版）：

```bash
scripts/handoff-lint.sh fp check        # Linux/WSL/Git Bash
# scripts/handoff-lint.ps1 fp check     # Windows PowerShell
```

- **一致** → 打印「环境未变，跳过复验」：**不再重跑**依赖安装/基线测试/服务体检，直接进第 6 步。
- **不一致** → 脚本输出**变化的具体项**：**只复验那一维**（如仅 node 版本变 → 重装依赖；仅配置变 → 重启服务），不全量重来。
- 无 `.handoff/fp.sha`（旧交接）→ 走一次全量环境就绪检查，并提示交接方补指纹。

## 超预算处理

若 `HANDOFF.md` 超过 ~1K tokens（`scripts/handoff-lint.sh check HANDOFF.md`）→ **先提示按 project-handoff 规范压缩/归档再继续**，别在膨胀文档上工作。

## 反模式

- 不读 HANDOFF 直接开工——重复探索、漏 delta、误判进度
- 复制 HANDOFF 内容到笔记/新文档——造成双源
- **无视环境指纹就全量复验**——同机同环境白跑（或反：指纹已变却跳过复验）
- 环境未就绪就业务验证——把环境问题误判为业务缺陷
- 完成后不回填（ticket/快照）——HANDOFF 过期
- 确认已修却不归档——与 project-handoff 对称：坑→`pits.md`，待办→`done.md`
- 凭据瞎猜（从代码/配置搜索 Key）——应向用户索取或引用存储位置
- 在超 1K tokens 的膨胀 HANDOFF 上继续工作

## 完成标准

- [ ] 已读 HANDOFF 5 节并复述上下文（状态 + 下一步）得到确认（§2 详情不足查 `git log`；已修坑查 `pits.md`）
- [ ] 建议动作已执行（git/.gitignore/读 tickets/凭据来源明确）
- [ ] **环境复验按指纹门控执行**：一致则已跳过；不一致则只复验了变化维度
- [ ] 验证点完成（对照 ticket AC）
- [ ] 回填完成（AC 勾选 + §2 同步 + 新未修坑入 §4 + 确认已修已迁归档）
- [ ] 未复制 HANDOFF 内容；无敏感信息写入

## 方法论来源（2026-08）

- project-handoff（对称技能）：交接方 5 节结构 → 接收方按同构恢复上下文；维护规则双向共用
- mattpocock handoff：交接文档作为下一 session 的起始上下文
- NeonForge HANDOFF.md 实践（2026-08-02）：接收方需建议动作与环境就绪检查
- **2026-09-17 瘦身改版**：环境指纹门控——同机同环境接手跳过复验，环境变化只复验变化维度；超 1K tokens 先压缩

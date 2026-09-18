---
name: project-handoff
description: >-
  Generate/update a project engineering handoff document (HANDOFF.md) — reference-style delta
  structure with a hard budget of ~1K tokens across exactly five sections: metadata / snapshot /
  next steps / immediate ops / reference index. Records only delta not already in docs or commit
  log; the snapshot holds a domain status table only (commit history stays in git log — no
  "recently done" list); one-line entries; never copies (anti-dual-source); desensitized. Rolling
  archive HANDOFF-ARCHIVE/ (cycles.md / done.md / pits.md) is mandatory and confirmed-fixed
  pitfalls/todos must be moved there, not kept live. Environment re-verification is minimized with
  a non-resident env fingerprint (.handoff/fp.sha, via the bundled handoff-lint
  script) so an unchanged environment skips re-verification; project-intake reads it. Use when
  handing off across sessions/tools, generating or updating HANDOFF.md, capturing project delta
  state, or after stage rulings. NOT for: resuming prior work — that belongs to project-intake.
slug: project-handoff
version: 1.2.0
displayName: project-handoff
---

# 项目交接文档（Project Handoff）

## 角色

你是交接文档作者。为项目生成/更新**工程交接文档**（HANDOFF.md），让接收方（另一 agent/工具/新 session）无需重读全部文档即可继续工作。**只记 delta，引用不复制，硬上限 ~1K tokens。**

## 何时使用

- 工具切换、跨 session 交接、委托其他 agent 继续工程；
- 项目到里程碑（ticket 完成、阶段切换）需要记录进度；
- 用户要求「交接」「handoff」「生成交接文档」时（「继续之前的工作」属接收方语境，由 project-intake 承担）。

## 硬约束（不可妥协）

1. **体积上限 ~1K tokens**——估算 `CJK字数 + 非CJK字符数/4`（代理：字节数 / 3，≈3KB 混合文本）。**超预算不交付**：先归档、压缩，再交接。
2. **防双源**——既有文档（README/docs/specs）与 commit message 已有的一律引用，禁止复制；本文件只记「文档集与 commit 都没有的 delta」。
3. **脱敏**——不得含 API Key/密码/PII；引用密钥只写存储路径不写值。
4. **结构刚性**——固定 **5 节**，禁 emoji、禁自造节（非 `## N.` 的标题即不合规）。
5. **位置**——项目根 `HANDOFF.md`（或约定位置）；已存在则更新，只动易变节。
6. **会话进度已收敛**——不再维护 `.agents/session.md`（原 `core-rules` §4 已退役，2026-09-17）；会话级进度、断点、待决策一律进本文件 §2/§3/§4，不另立进度文件。

## 结构（5 节 + token 上限）

| 节 | 上限 | 内容 |
|----|------|------|
| §1 交接元信息 | ≤120 | 日期 / 交接方 / 接收方 / 原因 / 项目一句话 / 文档入口链 / 接收方建议动作（≤3 条）。**不留历次交接历史**（→ cycles.md）|
| §2 当前状态快照 | ≤400 | **仅域状态表**（域 \| 状态）+ 版本控制/构建环境各一行。**禁 commit 列表 / 「最近完成」**（git log 是详情权威）|
| §3 下一步与验证点 | ≤200 | 未完成项 + 验证命令 + 外部依赖来源（凭据从哪取）|
| §4 即时操作 | ≤180 | 启动/验证命令（`AGENTS.md` 已有则引用）+ 未修/仍会踩的坑（≤5 条，每条一行）|
| §5 引用索引 | ≤100 | 主题 → 权威路径，≤6 行（不放可归 AGENTS.md/README 的内容）|

**无 §6**——维护规则属本技能正文，不在每份交接文件里重复。

## 环境指纹（最小化接手复验）

目标：**同机同环境接手 → 跳过环境复验；环境变了 → 只复验变化的那一维**（不再无脑重跑全套）。

- 输入清单 `<project>/.handoff/fp.txt`（每项目定制，一行一项）：
  - `file:<相对路径>`——纳入文件内容哈希（依赖锁、运行配置等）
  - `cmd:<命令>`——纳入命令输出哈希（版本探测等，如 `cmd:node --version`）
- 写指纹：`scripts/handoff-lint.sh fp write`（Windows：`scripts/handoff-lint.ps1 fp write`）→ 生成 `.handoff/fp.sha`。
- `.handoff/fp.sha` **不占 HANDOFF 预算**（非常驻 sidecar）；只存每项 8 位短哈希，**不存值** → 密钥文件内容不外泄。
- 与 HANDOFF 正交：HANDOFF 记状态，指纹记环境；接收方用 `fp check` 决定是否复验（见 project-intake）。

## 工作流

```
- [ ] 1. 定位现有 HANDOFF + AGENTS.md/README（作为引用源，避免重复）
- [ ] 2. 收集状态：各域进度（**不采 commit 列表**）
- [ ] 3. 归档迁移（硬触发，见下）：旧「最近完成」→ cycles.md；已修坑 → pits.md；§3 [x] → done.md
- [ ] 4. 按 5 节生成/更新（已存在则只动易变节）
- [ ] 5. 脱敏 + 引用检查（每处知识确认「引用而非复制」）
- [ ] 6. lint：`scripts/handoff-lint.sh check HANDOFF.md`——超预算即回压缩，不通过不交付
- [ ] 7. 环境指纹：`scripts/handoff-lint.sh fp write` 写入 .handoff/fp.sha
- [ ] 8. 交付：告知位置 + 接收方下一步起点
```

## 归档（硬触发）

- **触发条件**：HANDOFF >1K tokens、§2 域条目 >8、§4 坑 >5 → 立即归档，留言精简+指针（保留编号锚点，不删号不重排）。
- 三件套 **HANDOFF-ARCHIVE/{cycles,done,pits}.md 必备**（缺则先建）：`cycles.md`（跨周期完成）/ `done.md`（已完成待办）/ `pits.md`（已修坑）。
- 确认已修（或裁决不修）→ **当次迁走**，不留正文。

## 反模式

- 超 1K tokens 仍在交付（正文只胀不瘦）
- §2 混入 commit 列表 / 「最近完成」段落（与 git log 双源）
- §1 累积历次「前次接手确认」全文（历史未归档）
- 复制文档/commit 内容（双源）
- 加 §6 维护规则或自造节、用 emoji 排版
- 缺 HANDOFF-ARCHIVE 三件套；已修坑/已完成待办留在正文
- 写 API Key/密码/PII；引用密钥写值
- 交接不写环境指纹（逼接收方无脑全量复验）

## 完成标准

- [ ] `HANDOFF.md` 存在且 **≤1K tokens**（`handoff-lint.sh check` 通过）
- [ ] 5 节齐全；**无 §6、无自造节、无 emoji**
- [ ] §1 无历次交接历史；§2 无 commit 列表
- [ ] `HANDOFF-ARCHIVE/{cycles,done,pits}.md` 存在；已修/已完成项已迁走
- [ ] 已写环境指纹 `.handoff/fp.sha`
- [ ] 无敏感信息；接收方起点明确

## 附带脚本

| 脚本 | 平台 | 说明 |
|------|------|------|
| `scripts/handoff-lint.sh` | Linux / macOS / WSL / Git Bash | `check`（预算+结构）/ `fp write\|check`（环境指纹）|
| `scripts/handoff-lint.ps1` | Windows PowerShell 5.1+ | 同契约（纯 ASCII，兼容 PS5.1 的 GBK 读稿）|

零 python/node 依赖（仅系统自带 `wc/awk/sed/sha256sum` 或 PowerShell 内建）。

## 方法论来源（2026-08 调研 + 实践）

- mattpocock handoff skill：引用 artifacts 不重复、脱敏、suggested skills——「引用不复制」原则来源
- Agent Handoff（marcusglee11）：省 token 优先坐标引用
- YAKStack /handoff：纯文本简报五节（Who/What/Confirmed/In progress/Next）——简洁叙事启发
- NeonForge HANDOFF.md 实践（2026-08-02）：9 节 → 6 节重构——「delta+引用」批判性修正的产物
- **AI 评审反哺（2026-08-02）**：版本控制坐标、接收方建议动作、占位/未完成边界明示、外部依赖来源
- **2026-09-17 瘦身改版**：26 个实际 HANDOFF.md 盘点（4KB–70KB，仅 3 个达标）→ ~1K token 硬预算 + 删 §6 + §2 去 commit 列表 + §1 去历史 + 归档硬触发 + 环境指纹最小化复验

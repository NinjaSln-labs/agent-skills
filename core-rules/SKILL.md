---
name: core-rules
description: >-
  Global rules applicable to all projects/sessions across AI coding tools (Deep Code /
  Cursor, etc.). Four bottom lines: credential safety (no plaintext secrets),
  permission confirmation (confirm before write ops), long-task feedback (progress update
  within 60s), session progress (maintained in .agents/session.md). Use when handling
  passwords/credentials, write operations, long-running tasks, session records, or at any
  project start/end.
---

# 全局规则（Global Rules）

以下 4 条规则适用于所有项目。

## 1. 禁止明文密码

密码、API Key、Token、Secret 等敏感凭证，**禁止以明文形式出现**在代码、配置、日志、对话输出中。

- 代码从项目 `config/secrets.json` 读取凭证
- 示例/模板中用占位符（`your-key-here`）
- 对话中不暴露真实密钥

## 2. 权限确认

涉及写操作（文件修改、Git、脚本执行、网络请求、远程命令等），**必须先说明并获确认**。

- **只读除外**：纯查询、拉日志、列清单、生成计划可先做
- **确认内容**：范围 + 动作深度 + 影响与回滚
- 禁止因口语简称（如"清一下"）默认全量或默认破坏性步骤

## 3. 长任务反馈

预估超过 60 秒的任务，执行中必须持续反馈进度。

- **禁止**盲 sleep / 固定倒计时当主要等待手段
- 优先用完成信号（`exit_code`、progress JSON），再短轮询
- 连续 60s 内至少一条进度；无变化也报「仍在运行」
- 失败：自检 → 定位 → 汇报 → **等用户决策**（除非已授权自动重试）
- 需要稳定轮询时用 `task-loop-progress` Skill

## 4. 会话进度

每个项目独立维护自己的 `session.md`，放在 `<project>/.agents/session.md`。

工作区根目录的 `.agents/session.md` 仅存跨项目信息（子项目清单、全局待定方向），不存放任何单个项目的进度。

### 分层
- `<project>/.agents/session.md`：该项目活跃事项 + 待定方向 + 关键上下文（引用 `docs/` 路径即可，不重复记录）
- `docs/`：EVOLUTION、ROADMAP 等（项目自建，非强制）

### 格式
```
### <事项名>
- 状态：进行中 / 等待 / 阻塞
- 下一步：1-3 条可执行动作
- 断点：路径、命令、ID 等硬事实
- 待决策：要用户拍板的问题（无则写"无"）

## 待定方向
- [ ] 方向 — 优先级：高/中/低 — 来源：何时提出
```
完成即删，不留历史。

### 收工
更新**当前项目**的 `session.md`，缺则先补。不空收工。

### 开工
读**当前项目**的 `session.md` → 复述：状态、下一步、断点、待决策 → **停住等指令**。

修改用 Edit 逐项增删，禁止全文 Write 覆盖。

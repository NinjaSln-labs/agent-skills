---
name: task-loop-progress
description: >-
  Scaffolds config + adapter for the generic long-task progress loop
  (task_loop_scaffold.py / task_loop_poll.py / task_loop_start.sh). Supports local files,
  remote SSH fetch scripts, stdout JSON, and terminal output matching. Requires successful
  poll validation before start; on AGENT_LOOP_TICK, Agent must post chat_line to Chat.
  Use when the user asks for task loop、进度 loop、AGENT_LOOP_TICK、config+adapter 模板、
  长任务轮询、或为某任务接入 loop 监控、或给定自定义轮询命令（custom）。
---

# 长任务进度 Loop · Config + Adapter 生成

为任意长任务生成 `configs/task_loop/<task_id>.json` 与可选 `scripts/task_loop_adapters/<task_id>_adapter.py`，接入通用 loop。

**参考实现仓库**（⚠️ 2026-08 已迁移/打包——原路径失效；脚本按 [templates/](templates/) 模板自建即可）：

| 路径 | 说明 |
|------|------|
| `scripts/task_loop_poll.py` | 按 config 轮询 |
| `scripts/task_loop_start.sh` / `task_loop_stop.sh` | 启停 loop |
| `scripts/task_loop_scaffold.py` | 一键生成 config + adapter |
| `configs/task_loop/` | 任务配置 |
| `reports/task_loops/<task_id>/live.md` | Agent 每 tick 读取 |

其他仓库：复制上述 `scripts/task_loop_*` 与 `configs/task_loop/_template.json`，或在本仓库生成后拷贝。

## 何时使用

- 用户要为**新长任务**加 60s（或可配）进度 loop
- 进度在**本机文件 / 远程 SSH / 自定义 shell / 终端输出**之一或组合
- 需要 **config + adapter 模板** 或让 Agent 自动生成

## 工作流（按序）

### 1. 采集（AskQuestion 或对话确认）

| 项 | 说明 |
|----|------|
| `task_id` | 小写+下划线，如 `ecs_disk_collect` |
| `title` | 中文显示名 |
| `progress_source` | 见 [reference.md](reference.md) 四种模式 |
| `interval_sec` | 默认 `60` |
| `tick_env` | 可选，如 `AGENT_LOOP_TICK_ECS_DISK`；缺省为 `AGENT_LOOP_TICK_<TASK_ID>` |
| 远程/路径 | 主机、日志、progress JSON 等（写入 poll_command / fetch 脚本，**不**写进 loop 核心） |

### 2. 选模式 → 生成文件

**优先**：在参考仓库执行

```bash
python2 scripts/task_loop_scaffold.py \
  --task-id <task_id> \
  --title "<title>" \
  --mode <local_json|local_log|remote_fetch|stdout_json|custom> \
  [--fetch-script scripts/<name>.sh] \
  [--progress-file /path/to/progress.json] \
  [--log-file /path/to/exec.log] \
  [--terminal-pattern 'substring in terminal cmd'] \
  [--tick-env AGENT_LOOP_TICK_XXX]
```

**或**手动：复制 [templates/](templates/) 下模板，按 [reference.md](reference.md) 填空。

生成后必须有：

- `configs/task_loop/<task_id>.json`
- 若 `poll_adapter` 非空：`scripts/task_loop_adapters/<task_id>_adapter.py`（`chmod +x` 非必须，python2 调用）

### 3. 校验

```bash
python2 scripts/task_loop_poll.py --task <task_id>
```

成功应写出 `reports/task_loops/<task_id>/live.json` 且 `chat_line` 非空。失败则修 `poll_command` / adapter，**不要**启动 loop。

### 4. 启动 loop（长任务开始前）

**Agent 必须用 Shell 工具启动**（`block_until_ms: 0`）并配置 `notify_on_output` pattern=`^<tick_env>`。禁止仅写 log、禁止后台 subagent 代跑却不回 Chat。

```bash
./scripts/task_loop_start.sh <task_id>
```

记录输出的 `tick_env=`。另开 Shell 跑长任务时 pattern 含 `HEARTBEAT`。

### 5. Agent 收到 tick 时

1. 读 `reports/task_loops/<task_id>/live.md`（或 `live.json` 的 `chat_line`）
2. **在 Chat 发一行** `chat_line`（不得只读不发）
3. `status=done` 或任务已结束 → `./scripts/task_loop_stop.sh <task_id>`

遵守 `long-running-progress` 规则：≤60s 须有 Chat 反馈。

## 标准 Adapter 输出（契约）

`poll_adapter` 从 **stdin** 读 `poll_command` 的 stdout（常为 JSON），向 **stdout** 打印一行 JSON：

```json
{
  "status": "running|done|idle|error",
  "finished": false,
  "chat_line": "给用户的一行摘要",
  "metrics": {},
  "log_tail": ["最近日志行"]
}
```

- `poll_command` 已输出含 `chat_line` 的完整 JSON 时，可省略 adapter
- Python 2.7 兼容（`from __future__ import print_function`）；路径含中文时用 `u8()` 见模板

## 模式速查

| mode | poll_command 典型 | adapter |
|------|-------------------|---------|
| `stdout_json` | 命令直接 echo/print 标准 JSON | 无 |
| `local_json` | `cat reports/foo/progress.json` | 有，解析 offset/total |
| `local_log` | `tail -20 /path/log` | 有，从日志 regex 提取 |
| `remote_fetch` | `bash scripts/<task>_fetch.sh` | 有，解析 fetch 包装 JSON |
| `custom` | 用户给定 shell | 按需 |

详见 [reference.md](reference.md) 与 [templates/](templates/)。

## 示例任务

| task_id | 参考 |
|---------|------|
| `cm_drop_stage_a` | `configs/task_loop/cm_drop_stage_a.json` + `cm_drop_adapter.py` |

## 禁止

- 在 config / skill / 日志中写明文密码；SSH 用 `credentials-and-access` + fetch 脚本内解析
- 为每个任务复制 `task_loop_poll.py`；只加 config + adapter（及可选 fetch.sh）
- 未 `task_loop_poll.py --task` 成功就 `task_loop_start.sh`

## 汇报模板

```markdown
已为 **<title>** 创建 task loop：
- config: `configs/task_loop/<task_id>.json`
- adapter: `scripts/task_loop_adapters/<task_id>_adapter.py`（或无）
- tick: `<tick_env>`
- 校验: `chat_line` = …

启动: `./scripts/task_loop_start.sh <task_id>`
```

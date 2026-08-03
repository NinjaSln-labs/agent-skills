---
name: task-loop-progress
description: >-
  Scaffold config + adapter for the generic long-task progress loop (generate task_loop_scaffold.py /
  task_loop_poll.py / task_loop_start.sh from templates/). Config-driven: the adapter extracts
  numeric/percentage/stage three-type progress via progress_extract — zero code changes per task; a
  poll that emits the standard contract directly can omit the adapter. Supports local files, remote SSH
  fetch scripts, stdout JSON, and terminal output matching. Requires successful poll validation before
  start; on AGENT_LOOP_TICK, Agent must post chat_line to Chat. Use when the user asks for a task loop,
  progress loop, AGENT_LOOP_TICK, config+adapter templates, long-task polling, hooking up loop
  monitoring, or provides a custom poll command.
---

# 长任务进度 Loop · Config + Adapter 生成

为任意长任务生成 `configs/task_loop/<task_id>.json` 与可选 `scripts/task_loop_adapters/<task_id>_adapter.py`，接入通用 loop。

**参考实现**：⚠️ 2026-08 原参考实现已迁移/打包（路径失效）；脚本按 [templates/](templates/) 模板自建即可。

**本仓库交付**：

| 路径 | 说明 |
|------|------|
| `templates/adapter.template.py` | poll adapter 模板（Python 3，兼容 2.7）|
| `templates/config.template.json` | task config 模板 |
| `templates/fetch.template.sh` | 远程 fetch 脚本模板 |
| `reference.md` | 模式/契约/示例参考 |

**运行时布局**（按模板生成到参考仓库/项目；原参考实现已迁移/打包，路径失效——见上）：

| 路径 | 说明 |
|------|------|
| `scripts/task_loop_poll.py` | 按 config 轮询（由 adapter.template.py + config 派生）|
| `scripts/task_loop_start.sh` / `task_loop_stop.sh` | 启停 loop |
| `scripts/task_loop_scaffold.py` | 一键生成 config + adapter |
| `configs/task_loop/` | 任务配置 |
| `reports/task_loops/<task_id>/live.md` | Agent 每 tick 读取 |

其他仓库：复制 `templates/` 到目标仓库，按 `reference.md` 生成上述运行时文件。

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

**优先**：若参考仓库已有 `scripts/task_loop_scaffold.py`，直接执行；否则按 [templates/](templates/) 手动生成（主路径）：

```bash
# 1) 复制模板到目标仓库
cp templates/config.template.json   configs/task_loop/<task_id>.json   # 按 reference.md 填空
cp templates/adapter.template.py    scripts/task_loop_adapters/<task_id>_adapter.py  # 按 mode 改解析逻辑
# 2) （可选）remote_fetch 模式：复制 templates/fetch.template.sh 为 scripts/<task_id>_fetch.sh 并填主机/命令
# 3) （可选）参考仓库有 scaffold 时可用：
#    python3 scripts/task_loop_scaffold.py \
#      --task-id <task_id> \
#      --title "<title>" \
#      --mode <local_json|local_log|remote_fetch|stdout_json|custom> \
#      [--fetch-script scripts/<name>.sh] \
#      [--progress-file /path/to/progress.json] \
#      [--log-file /path/to/exec.log] \
#      [--terminal-pattern 'substring in terminal cmd'] \
#      [--tick-env AGENT_LOOP_TICK_XXX]
```

**或**手动：复制 [templates/](templates/) 下模板，按 [reference.md](reference.md) 填空。

生成后必须有：

- `configs/task_loop/<task_id>.json`
- 若 `poll_adapter` 非空：`scripts/task_loop_adapters/<task_id>_adapter.py`（`chmod +x` 非必须，python3 调用）

### 3. 校验

参考仓库有 `scripts/task_loop_poll.py` 时：

```bash
python3 scripts/task_loop_poll.py --task <task_id>
```

无 poll 脚本时：按 [reference.md](reference.md) 契约手工验证——向 adapter 喂 `poll_command` 的 stdout，确认输出 `chat_line` 非空且 `status` 合法。失败则修 `poll_command` / adapter，**不要**启动 loop。

### 4. 启动 loop（长任务开始前）

**Agent 必须用 Shell 工具启动**（`block_until_ms: 0`）并配置 `notify_on_output` pattern=`^<tick_env>`。禁止仅写 log、禁止后台 subagent 代跑却不回 Chat。

```bash
./scripts/task_loop_start.sh <task_id>   # 参考仓库脚本；本仓库需先按模板生成
```

记录输出的 `tick_env=`。另开 Shell 跑长任务时 pattern 含 `HEARTBEAT`。

### 5. Agent 收到 tick 时

1. 读 `reports/task_loops/<task_id>/live.md`（或 `live.json` 的 `chat_line`）
2. **在 Chat 发一行** `chat_line`（不得只读不发）
3. `status=done` 或任务已结束 → `./scripts/task_loop_stop.sh <task_id>`

遵守 `long-running-progress` 规则：≤60s 须有 Chat 反馈。

## 标准契约（adapter 输出 / poll 直出）

adapter 输出与 poll 直出共用同一标准 JSON；`poll_command` 已输出此契约时可**省略 adapter**：

```json
{
  "status": "running|done|idle|error",
  "finished": false,
  "chat_line": "给用户的一行摘要",
  "progress": { "offset": 5, "total": 10 },
  "metrics": {},
  "log_tail": ["最近日志行"]
}
```

- `progress` 三型任选：`{offset,total}`（数值）/ `{pct}`（百分比 0-100）/ `{stage,stage_total}`（阶段）
- `chat_line` / `status` 可选（缺省由 consumer 按 progress/finished 推导）
- adapter 为通用解释器：读 `progress_extract` 提取（config 驱动，**每任务零代码改动**）；输入已是标准契约则原样透传
- Python 3（`from __future__ import print_function` 保留双兼容）；路径含中文时用 `u8()` 见模板

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
- 为每个任务复制轮询核心（`task_loop_poll.py` 或 adapter 模板）；只加 config + adapter（及可选 fetch.sh）
- 校验（poll 契约验证）未成功就启动 loop

## 汇报模板

```markdown
已为 **<title>** 创建 task loop：
- config: `configs/task_loop/<task_id>.json`
- adapter: `scripts/task_loop_adapters/<task_id>_adapter.py`（或无）
- tick: `<tick_env>`
- 校验: `chat_line` = …

启动: `./scripts/task_loop_start.sh <task_id>`
```

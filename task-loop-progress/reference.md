# Task Loop · Config / Adapter 参考

## Config 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 与文件名 `<task_id>.json` 一致 |
| `title` | 是 | 显示名 |
| `interval_sec` | 否 | 默认 60 |
| `tick_env` | 否 | 自定义 `AGENT_LOOP_TICK_*`；缺省由 id 推导 |
| `poll_command` | 是 | 本机 shell，cwd=仓库根 |
| `poll_adapter` | 否 | `python3 scripts/task_loop_adapters/xxx.py`（无 adapter 时 poll 直接输出标准契约，见模式 A）|
| `progress_extract` | 否 | adapter 提取规则（见下）；缺省 = 兼容旧行为（认 `prog.offset` + 文本 `offset=`）|
| `poll_env` | 否 | poll 时注入的环境变量 |
| `poll_env_quiet` | 否 | loop 周期 poll（`--quiet`）额外 env |
| `terminal_watch` | 否 | 见下 |
| `status_when` | 否 | `done_field` / `done_value` / `running_if_terminal_match` |
| `agent_prompt` | 否 | tick 时给 Agent 的指令 |

### progress_extract（adapter 提取规则）

三型进度任选一，`source=auto` 先试 JSON 再试文本正则：

```json
{
  "source": "auto",
  "offset_field": "progress.offset",
  "total_field": "progress.total",
  "pct_field": "pct",
  "stage_field": "progress.stage",
  "stage_total_field": "progress.stage_total",
  "regex": ""
}
```

- 数值型：`offset_field` / `total_field`（点路径取嵌套，如 `progress.offset`）
- 百分比型：`pct_field`（0-100）
- 阶段型：`stage_field` / `stage_total_field`
- 文本型：`regex` 含数字捕获组（首个=当前，次个=总数）

### terminal_watch

```json
{
  "pattern": "终端 tail 里出现的命令片段",
  "progress_regex": "round (\\d+)/(\\d+).*offset=(\\d+)",
  "done_marker": "exit_code:"
}
```

匹配到 `pattern` 且无 `done_marker` → `status` 倾向 `running`，`chat_line` 追加 local terminal 提示。

---

## 标准契约（adapter 输出 / poll 直出）

adapter 输出与「poll 直出」（模式 A）共用同一标准 JSON：

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
- poll 直出时 `chat_line` 可选（缺省由 consumer 按 progress 拼）；`status` 可选（缺省由 `finished`/进度推导）
- adapter 对已是标准契约的输入**原样透传**（仅补缺省字段）——见 `templates/adapter.template.py`

---

## 模式 A：`stdout_json`（无 adapter，推荐直出）

`poll_command` 直接输出标准契约 JSON：

```json
{
  "poll_command": "python3 scripts/my_task_status.py --json",
  "poll_adapter": ""
}
```

`my_task_status.py` 打印标准契约 JSON（含 `progress`，可选 `chat_line`/`status`）即可——无需 adapter。

---

## 模式 B：`local_json`

进度在本机 JSON 文件：

```json
{
  "poll_command": "cat reports/my_task/progress.json",
  "poll_adapter": "python3 scripts/task_loop_adapters/my_task_adapter.py"
}
```

adapter 用 `progress_extract` 提取（config 驱动）：`offset_field: "offset"`、`total_field: "total"` 等——**adapter 代码零改动**，只配 config。缺省（无 `progress_extract`）兼容旧逻辑：认 `prog.offset`。

---

## 模式 C：`local_log`

仅日志文件，用 regex 抽进度：

```json
{
  "poll_command": "tail -30 /tmp/my_task.log",
  "poll_adapter": "python3 scripts/task_loop_adapters/my_task_adapter.py",
  "progress_extract": { "source": "text", "regex": "processed (\\d+)/(\\d+)" }
}
```

adapter 按 `progress_extract.regex` 抽数字组（首个=当前，次个=总数）；无法解析时 `status=idle`，`chat_line` 为最后一行。

---

## 模式 D：`remote_fetch`（推荐远程）

**不要把 SSH 细节写进 config**；单独 fetch 脚本：

`scripts/my_task_fetch.sh`：

```bash
#!/bin/bash
set -e
# 从 credentials-and-access 读凭据；展示给用户时密码用 ***
# 海外：读 doc/基础设施/服务器信息/海外连接.md 再连
ssh ... root@<host> 'cat /remote/path/progress.json; echo "---LOG---"; tail -3 /remote/path/exec.log'
```

包装为单行 JSON 给 adapter（与 `cm_drop_fetch_remote.sh` 同思路）：

```json
{"ts":"...","prog":"{...}","log":"...","datadir":"..."}
```

Config：

```json
{
  "poll_command": "bash scripts/my_task_fetch.sh",
  "poll_adapter": "python3 scripts/task_loop_adapters/my_task_adapter.py",
  "poll_env_quiet": {"MY_TASK_SKIP_HEAVY": "1"}
}
```

---

## 模式 E：`custom`

用户给定 `poll_command` + adapter；Agent 根据实际 stdout 形状编写 adapter。

---

## tick_env 命名

| task_id | 默认 tick_env | 自定义 |
|---------|---------------|--------|
| `cm_drop_stage_a` | `AGENT_LOOP_TICK_CM_DROP_STAGE_A` | 配置 `"tick_env": "AGENT_LOOP_TICK_CM_DROP"` |

`task_loop_start.sh` 启动时打印实际 `tick_env=`，以此配置 `notify_on_output`。

---

## 并行多任务

每个 `task_id` 独立：

- `reports/task_loops/<task_id>/`
- `reports/task_loops/.<task_id>.pid`
- 各自 `AGENT_LOOP_TICK_*`

`./scripts/task_loop_list.sh` 查看状态。

---

## 故障排查

| 现象 | 处理 |
|------|------|
| `poll_command failed` | 单独运行 poll_command；查 SSH/路径 |
| `poll_adapter failed` | `echo '<sample>' \| python3 ..._adapter.py <config_path>`（config_path 为 configs/task_loop/<task_id>.json，读 progress_extract）|
| UnicodeDecodeError | adapter/poll 用 `io.open(..., encoding='utf-8')`；路径 `u8()` |
| Chat 无进度 | 确认 loop 在跑、`notify_on_output` pattern 匹配 `tick_env` |
| status 一直 idle | 检查 `terminal_watch.pattern` 或 progress 里 `finished` |

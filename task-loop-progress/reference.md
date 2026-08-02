# Task Loop · Config / Adapter 参考

## Config 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 与文件名 `<task_id>.json` 一致 |
| `title` | 是 | 显示名 |
| `interval_sec` | 否 | 默认 60 |
| `tick_env` | 否 | 自定义 `AGENT_LOOP_TICK_*`；缺省由 id 推导 |
| `poll_command` | 是 | 本机 shell，cwd=仓库根 |
| `poll_adapter` | 否 | `python2 scripts/task_loop_adapters/xxx.py` |
| `poll_env` | 否 | poll 时注入的环境变量 |
| `poll_env_quiet` | 否 | loop 周期 poll（`--quiet`）额外 env |
| `terminal_watch` | 否 | 见下 |
| `status_when` | 否 | `done_field` / `done_value` / `running_if_terminal_match` |
| `agent_prompt` | 否 | tick 时给 Agent 的指令 |

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

## 模式 A：`stdout_json`（无 adapter）

`poll_command` 直接输出标准 JSON：

```json
{
  "poll_command": "python2 scripts/my_task_status.py --json",
  "poll_adapter": ""
}
```

`my_task_status.py` 打印契约 JSON 即可。

---

## 模式 B：`local_json`

进度在本机 JSON 文件：

```json
{
  "poll_command": "cat reports/my_task/progress.json",
  "poll_adapter": "python2 scripts/task_loop_adapters/my_task_adapter.py"
}
```

Adapter 模板逻辑：

```python
prog = json.loads(sys.stdin.read() or '{}')
offset = int(prog.get('offset', 0))
total = int(prog.get('total', 1))
finished = bool(prog.get('finished'))
chat_line = 'offset=%d/%d (%.1f%%)' % (offset, total, 100.0 * offset / total)
```

---

## 模式 C：`local_log`

仅日志文件，用 regex 抽进度：

```json
{
  "poll_command": "tail -30 /tmp/my_task.log",
  "poll_adapter": "python2 scripts/task_loop_adapters/my_task_adapter.py"
}
```

Adapter：`re.search(r'processed (\d+)/(\d+)', raw)` → 拼 `chat_line`；无法解析时 `status=idle`，`chat_line` 为最后一行。

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
  "poll_adapter": "python2 scripts/task_loop_adapters/my_task_adapter.py",
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
| `poll_adapter failed` | `echo '<sample>' \| python2 ..._adapter.py` |
| UnicodeDecodeError | adapter/poll 用 `io.open(..., encoding='utf-8')`；路径 `u8()` |
| Chat 无进度 | 确认 loop 在跑、`notify_on_output` pattern 匹配 `tick_env` |
| status 一直 idle | 检查 `terminal_watch.pattern` 或 progress 里 `finished` |

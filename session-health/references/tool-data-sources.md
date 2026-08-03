# 工具数据源适配表（session-health 引用）

> **用途**：session-health 按当前工具（Deep Code / Cursor / 其他）读取会话健康度信号时查此表执行。
> **稳定性**：CLI/存储结构随工具版本变化 → `refreshInterval: 180 天`。
> **置信度**：`高`=本机实测验证；`中`=结构稳定但字段可能随版本漂移；`低`=推测（待核实）。
> **扩展**：新工具接入流程见 `tool-adapter-template.md`——探测后按模板生成适配节追加至此。

- lastUpdated: 2026-08-03
- refreshInterval: 180 天
- 下一刷新期限: 2027-01-30

---

## 0. 工具探测（先确认当前工具）

```bash
# 各工具会话存储目录按最近写入排序，取最新的即当前工具
ls -td ~/.deepcode/projects/*/ 2>/dev/null | head -1 && echo "^ Deep Code"
ls -td ~/.cursor/projects/*/   2>/dev/null | head -1 && echo "^ Cursor"
```

仍不确定 → 问用户。

---

## 1. Deep Code 适配（置信度：高——2026-08-03 本机验证）

### 会话目录定位

路径 → 目录名：`/` 替换为 `-`（如 `/path/to/project` → `-path-to-project`）：

```bash
ls -td ~/.deepcode/projects/*/ 2>/dev/null | head -3
```

### 消息数 + 压缩比例（会话文件为 JSONL）

```bash
cd ~/.deepcode/projects/<project-code>
LATEST=$(ls -t *.jsonl | head -1)
TOTAL=$(wc -l < "$LATEST")
COMPACTED=$(jq -r 'select(.compacted == true) | "x"' "$LATEST" 2>/dev/null | wc -l)
echo "会话 $LATEST：$TOTAL 条，compacted $COMPACTED（$(( COMPACTED * 100 / TOTAL ))%）"
```

### 上下文占用快照（sessions-index.json——注意结构为 `.entries[]`）

> ⚠️ 旧版文档误用 `.[0] | {title, activeTokens, tokens}`——该结构已失效（顶层是 `{entries, originalPath, version}`；字段为 `activeTokens`/`usage`/`usagePerModel`，无 `title`/`tokens`）。

```bash
jq -c '.entries[] | {id, activeTokens, createTime, updateTime, status, summary}' \
  ~/.deepcode/projects/<project-code>/sessions-index.json | tail -3
```

（取 `activeTokens` 作每轮输入上界；字段名变化时用 `jq '.entries[0] | keys'` 探查，不硬编码。）

### 模型（查窗口表用）

```bash
jq -c '.entries[] | {id, usagePerModel}' ~/.deepcode/projects/<project-code>/sessions-index.json | tail -2
```

模型名 → 查 `references/model-contexts.md`；未收录 → 问用户/网络核实。

### 会话恢复能力

- `/resume`：列出历史会话继续
- `project-intake`：新会话输入「<项目名> 接手」恢复上下文
- HANDOFF.md / 项目文档

---

## 2. Cursor 适配（置信度：中——2026-08-03 本机验证，结构随版本漂移风险更高）

### 会话目录定位

路径 → 目录名：`/` 替换为 `-`（如 `/path/to/project` → `path-to-project`）：

```bash
ls -td ~/.cursor/projects/*/ 2>/dev/null | head -3
```

### 消息数（agent-transcripts JSONL——仅 Agent 模式会话有转录；普通 Chat 模式无本地转录）

```bash
# 每会话一个目录 <uuid>/<uuid>.jsonl；取最新会话的消息数
LATEST=$(ls -td ~/.cursor/projects/<project-code>/agent-transcripts/*/ 2>/dev/null | head -1)
F="$LATEST$(basename "$LATEST").jsonl"
echo "会话 $(basename "$LATEST")：$(wc -l < "$F") 行（user/assistant 消息 + turn_ended 事件）"
```

### 上下文占用（**无 token 快照**——走估算降级 + 标注）

本地文件不含 token/上下文占用数据。降级做法：

1. 消息数（上面命令）→ 估算占用 = 消息数 × 单条估算（0.5–2K token/条，按内容密度取）÷ 窗口（查 `references/model-contexts.md`）→ 只给量级（低/中/高）。
2. 涉及切换决策 → 请用户看 Cursor UI 上下文占用条确认。
3. 报告标注口径：「估算值，请以 UI 为准」。

### 活跃度 + 模型（ai-code-tracking.db——只读 SQLite）

```bash
DB=~/.cursor/ai-tracking/ai-code-tracking.db
sqlite3 -header "$DB" \
  "SELECT model, count(*) cnt, datetime(MAX(createdAt)/1000,'unixepoch','localtime') last \
   FROM ai_code_hashes GROUP BY model ORDER BY cnt DESC LIMIT 5;" 2>/dev/null
```

- `model` 常为 `default`（= 用户配置的默认模型，需向用户确认实际模型后才能查窗口表）
- `ai_code_hashes` 的 `createdAt`/`conversationId` 可看会话活跃度；`scored_commits` 有 commit 级 AI 占比（可佐证工作性质）

### 会话恢复能力

- Cursor 历史面板（左侧 History）找回旧会话
- 项目 `.cursor/rules/*.mdc` 或 `.cursorrules`（全局 `~/.cursor/rules/`）
- 无命令式 resume——恢复成本按「历史面板 + rules + git」评估

### Cursor 侧信号可用性小结

| 信号 | 可用性 | 来源 |
|------|--------|------|
| 消息数 | ✅（仅 Agent 模式）| agent-transcripts/*.jsonl |
| 压缩/概要化比例 | ❌ 无标记 | 不可量化 |
| 上下文占用 | ❌ 无快照 → 估算降级 | 消息数 × 单条均值 / UI 占用条 |
| 模型 | ⚠️ 多记 `default` | ai-code-tracking.db（需用户确认）|
| 活跃度/时间跨度 | ✅ | ai_code_hashes.createdAt / 转录 mtime |
| 会话恢复能力 | ⚠️ 弱（无命令式 resume）| 历史面板 + rules + git |

---

## 3. 信号可用性汇总（两工具对比）

| 信号 | Deep Code | Cursor |
|------|-----------|--------|
| 消息数 | ✅ JSONL 行数 | ✅ agent-transcripts（仅 Agent 模式；Chat 模式不可得）|
| 压缩比例 | ✅ `compacted` 标记 | ❌ 无 → 跳过维度并标注 |
| 上下文占用 | ✅ `activeTokens` 快照（≤上界）| ❌ 无 → 估算降级 + UI 确认 |
| 经济（每轮输入费）| ✅ 可算（≤快照上界）| ❌ 无法量化 → 标注 |
| 模型 | ✅ `usagePerModel` | ⚠️ `ai_code_hashes.model`（常为 default，需确认）|
| 活跃度/时间跨度 | ✅ `createTime`/`updateTime` | ✅ `ai_code_hashes.createdAt` / 转录 mtime |
| 恢复能力 | ✅ `/resume` + project-intake | ⚠️ 历史面板 + rules + git |
| 模型窗口（分母）| 查 `references/model-contexts.md`（共用）| 同左 |

---

## 刷新记录

| 日期 | 动作 | 变更 |
|------|------|------|
| 2026-08-03 | 初建 + 重写 | 修正 Deep Code `sessions-index` 命令（`.entries[]`）；新增 Cursor 适配（agent-transcripts / ai-code-tracking 实测）|

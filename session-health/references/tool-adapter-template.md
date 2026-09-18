# 新工具适配模板（tool adapter template）

> **用途**：在 Deep Code / Cursor 之外的工具（或版本变更后）使用 session-health 时，按此模板**只读探测**该工具的数据布局，生成适配节追加到 `references/tool-data-sources.md`。生成后 SKILL.md **无需改动**——方法论与工具无关。
>
> **原则**：只读探测；不臆造字段；信号缺失就降级标注（见 SKILL.md「信号缺失降级规则」）。

---

## 接入流程（5 步）

```
1. 探测会话存储目录     → 找到工具把「项目 → 会话数据」存在哪
2. 识别会话文件格式     → JSONL / SQLite / 其他（决定用 jq 还是 sqlite3）
3. 探测可用信号字段     → 消息数 / 压缩标记 / token 占用 / 模型 / 时间戳，逐项确认有或无
4. 探测恢复机制         → resume 命令？历史面板？规则文件？(决定切换成本的可恢复性)
5. 填写适配节           → 按下方骨架生成，追加到 tool-data-sources.md + 更新信号可用性汇总表
```

每步都要验证（跑命令看真实输出），禁止凭文档/猜测填。

---

## 探测命令模板（通用占位——按实际工具替换路径）

```bash
# ① 找会话存储目录（常见候选：~/.<tool>/projects、~/Library/Application Support/<tool>/、~/.config/<tool>/）
ls -td ~/.<tool>/projects/*/ 2>/dev/null | head -3

# ② 识别格式：目录里有什么文件？
ls -la <session-dir>/ | head -20

# ③ 若为 JSONL：看每条记录的结构
head -2 <session-dir>/*.jsonl | jq -c 'keys'      # 有无 compacted / role / message / tokens？
jq -r 'select(.compacted == true) | "x"' *.jsonl | wc -l   # 有无压缩标记

# ③ 若为 SQLite：列出表 + 字段，找 token/占用/模型相关列
sqlite3 <db> ".tables"
sqlite3 <db> "PRAGMA table_info(<表>);"

# ④ 恢复机制：搜配置/文档中的 resume / history / rules 关键字
grep -ri "resume\|history" ~/.<tool>/ 2>/dev/null | head -5
ls <project>/.cursorrules <project>/.<tool>/rules ~/.<tool>/rules 2>/dev/null
```

> 注意探测时**只读**：`ls`/`jq`/`sqlite3` 查询均可；不要 `cp`/`mv`/`sqlite3 <db> "UPDATE..."`。

---

## 适配节模板骨架（复制后填写）

````markdown
## N. <工具名> 适配（置信度：<高/中/低>——<日期> <实测/推测>）

### 会话目录定位

路径 → 目录名：<规则说明>：

```bash
<命令>
```

### 消息数

```bash
<命令>
```

### 上下文占用（<有快照 / 无→估算降级>）

<有快照则给读取命令 + 字段；无则写明「无 token 快照——走 SKILL.md 估算降级 + UI 确认」>

### 压缩/概要化比例（<有标记 / 无→跳过维度>）

<有则给命令；无则写「不可量化」>

### 模型（查窗口表用）

```bash
<命令>
```

<模型名 → references/model-contexts.md；default 等别名需向用户确认>

### 会话恢复能力

- <resume 命令 / 历史面板 / 规则文件 / 其他>

### 信号可用性小结

| 信号 | 可用性 | 来源 |
|------|--------|------|
| 消息数 | ✅/❌/⚠️ | <来源> |
| 压缩比例 | ✅/❌ | <来源 / 不可量化> |
| 上下文占用 | ✅/❌ | <来源 / 估算降级> |
| 模型 | ✅/⚠️ | <来源> |
| 活跃度/时间跨度 | ✅/❌ | <来源> |
| 会话恢复能力 | ✅/⚠️ | <来源> |
````

---

## 生成后校验清单

- [ ] 所有命令都在本机**实际跑过**，输出与文档一致（防臆造）
- [ ] 会话目录定位规则明确（路径 → 目录名转换规则写清楚）
- [ ] 信号逐项确认：有 → 给命令；无 → 写「不可量化/估算降级」，不默认健康
- [ ] 模型字段若为别名（如 `default`）→ 已注明「需用户确认」
- [ ] 恢复能力如实填写（无命令式 resume 就写历史面板/rules，不夸大）
- [ ] 适配节含 `lastUpdated` + `refreshInterval` + 置信度，并更新 `tool-data-sources.md` 头部与「信号可用性汇总」
- [ ] SKILL.md 未改动（方法论层无工具依赖）

---

## 参考案例：Cursor 适配节生成记录（2026-08-03）

本机按上述流程探测 Cursor 得到的结论（详见 `tool-data-sources.md` 第 2 节）：

1. 存储目录：`~/.cursor/projects/<project>/`（`/` → `-` 命名）
2. 会话格式：`agent-transcripts/<uuid>/<uuid>.jsonl`（JSONL，`{role, message}` + `{type: turn_ended}`）
3. 信号探测结果：
   - 消息数 ✅（仅 Agent 模式有转录；Chat 模式无本地文件）
   - 压缩标记 ❌（无 `compacted` 类字段）
   - token/占用 ❌（无快照字段）→ 估算降级
   - 模型 ⚠️（`ai-code-tracking.db` 的 `ai_code_hashes.model` 多为 `default`，需用户确认实际模型）
   - 活跃度 ✅（`ai_code_hashes.createdAt` / 转录 mtime）
   - 恢复 ⚠️（历史面板 + `.cursor/rules`，无命令式 resume）
4. 按骨架生成适配节，置信度标「中」（结构可能随版本漂移）。

> 该流程同样适用于其他工具（Windsurf / Codex / Claude Code 等）——照步骤探测即可。

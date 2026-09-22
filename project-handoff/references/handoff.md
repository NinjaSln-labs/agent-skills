# 交接相位（handoff）

前提：已读 `SKILL.md`。**先过门禁** `handoff check` 再动。

## 步骤

1. **确保存储就绪**：
   - 有**旧模型**（`HANDOFF.md` / `HANDOFF-ARCHIVE/` / `.handoff/fp.*`）→ **请求迁移**（仅显式调用）；同意后先走 `references/migrate.md`（**迁移先于交接**）。
   - **全无存储** → `references/init.md`（**仅显式调用**）。
   - 已有 `.handoff/` → `python3 <技能>/scripts/handoff.py check`。
   - **写入类命令不建库**（`add`/`close`/`set`/`edit`/`rm`/`unconfirmed`/`next`）：无 `.handoff/index` 时非零退出并指路 init / migrate。旧行为会 mkdir 槽目录＋写 index，造出**缺 9 槽的非法半库**、还把 `init`（index 已存在即拒）堵死——建库只发生在显式相位（`import`/`scope add` 的登记先行不受影响）。
   - **并确保项目约定**：`AGENTS.md` 含「未决项只写 `.handoff/`」一节（**无则新建**，机械锚幂等）——防持续偏移。
2. **写 9 槽**（下表＝本技能的**写槽表**，他件引用命令形时指的就是它；**条目与单文件槽均只经 CLI**）：
   | 槽 | 怎么写 |
   |---|---|
   | actions | `handoff add action --domain <域> --summary "…" [--topic …] [--src …] [--status blocked --blockedBy …]` |
   | pitfalls | `handoff add pitfall --domain <域> --summary "…" [--topic …]` |
   | commands | `handoff add command --purpose <用途> --summary "…"` |
   | decisions | `handoff add decision --title "…" --body "…" [--domain … --topic … --supersedes …]` |
   | 切不动的源 | `handoff unconfirmed add --ref <路径#锚> --summary "…"` |
   | 候选结案 | `handoff unconfirmed resolve <id> --as action\|pitfall\|decision [--summary "…" --domain …]`（转正＝**另分新 id**，原候选随内部 `close` 归档）或 `--dismiss`（只作废、不入槽）；`--no-refill` 语义同 `close` |
   | 完成项 | `handoff close <id> --outcome "…"`（关掉的是当前 `next` → **自动补位**；`--no-refill` 关）|
   | next（下一步唯一一条） | `handoff next <id>`；`--auto` 按补位策略落盘；`--clear` 清空 |
   | status / summary / exit | `handoff set <status\|summary\|exit> --file <f>`（缺省读 stdin）|
   | scope | `handoff scope add/remove/prune`（登记表，勿直写）|
   | 纠错：改字段 | `handoff edit <id> [--summary/--detail/--topic/--status/--blockedBy/--domain/--purpose/--src]`（`--outcome` 仅 closed 行；**按该条目型校验**，型不符直接报错不静默丢；`id`/`created`/`closed` 不可改；决策文档不支持 edit，改判另开一条 `--supersedes`）|
   | 纠错：删条目 | `handoff rm <id>`（→ `.handoff/trash/` + 记作废防复用 + 引用守卫；`next`/`blockedBy`/`supersedes` 引用时拒绝）|
3. **重建索引 + 门禁**：`handoff index && handoff check`——**不过不得交付**。
4. **出覆盖声明**：`读到 / 写入（新增 / 关闭 id）/ 未能确认`。

## 硬约束

- **日期由脚本盖**（`add`/`close` 不接受日期参数，防编造）；**id 由脚本分配**（永不复用）。
- **不生成第二副本**（无摘要视图）；`handoff view --save` 存盘属**用户所有、非契约**。
- **旧模型先请求迁移**（仅显式调用）；不在旧模型上直接交接、不擅自迁移。
- `check` 不过 → **相位不得前进**。

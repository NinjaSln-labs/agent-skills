# 接手相位（resume）

前提：已读 `SKILL.md`。

## 步骤

1. **判定存储态**（看 `.handoff/index` / 槽，**不是**看目录是否存在）：
   - 有 `.handoff/index` → `python3 <技能>/scripts/handoff.py check` 过 → 继续。
   - 无，但存在**旧模型**（`HANDOFF.md` / `HANDOFF-ARCHIVE/` / `.handoff/fp.*`）→ **告知用户并请求迁移**（迁移**仅显式调用**，不自主跑）；同意后走 `references/migrate.md`，再回本步。
   - 全无 → 报「尚无工作存储」，**询问**是否新建；同意则 `references/init.md`。
   - **并确保约定**：`AGENTS.md` 缺「未决项只写 `.handoff/`」→ 补 / 新建（防持续偏移）。
2. **读（渐进披露，尽量少）**：
   - `handoff view` 一趟**认识整体**（所有槽 + `next` + `unconfirmed` + 计数）。
   - 需要钻取时，**只读相关槽文件**（如 `actions/<域>.jsonl`），不读全。
   - **只读 live 槽**；`closed/` 仅在追溯时**显式**读。
3. **验环境（探测式）**：命令从项目入口读（README / Makefile / package.json…）。探测不到**不假设**。
   - **门控**：有体检 / 门控命令 → **单独一批先跑、拿结论**，再发其它命令；**禁与核验命令同批**（TOCTOU）。
   - **本技能不提供门控工具**；门控依赖的脚本 / 工具**不存在 → 不执行**，记「无门控」。
   - **禁止副作用 fallback**（部署 / 写盘 / 联网 / `|| make deploy` 之类）——一律降级为**如实报告**。
4. **机检确认（read-back，必须）**：
   ```sh
   python3 <技能>/scripts/handoff.py confirm --seed <N>              # 脚本出题（记下 N）
   python3 <技能>/scripts/handoff.py confirm --seed <N> --answers -  # 接方作答（JSON，须同 N）
   ```
   题面每次调用重新随机抽——两次不同 `--seed` ＝ 题已换、答案全错位。抽查题按视图呈现形
   （`[id] topic summary` 整行）判分，照 `handoff view` 文本抄即可。
   **不 PASS ＝ 交接未完成**——重读所错之槽再答。
5. **出覆盖声明**：`读到 / 写入 / 未能确认`（含 `handoff check` 报的 `unconfirmed` open 计数）。
6. **定「下一步」并做工作**：`next` 已指定 → 从之。`next` 为空且 open actions 多条 → CLI 的**自动补位**只在 `close` 关掉当前 next 时触发，接手相位**不替你排序**：给排序建议并**请用户确认本轮做哪条**（建议不落盘；用户认了才 `handoff next <id>`）。想看策略会选谁：`handoff next --auto`（直接落盘）——不满意随时 `handoff next <id>` 覆盖。

## 硬约束

- **先读后动**：读 `view` / 槽文件之前，不执行项目动作。
- 探测不到先问，**不猜**。
- **门控单独成批**；无工具不执行、不跑副作用 fallback。
- **`confirm` 不 PASS → 视为未接手**（不得声称「已接手」）。
- 发现旧模型 → **请求迁移**（仅显式调用）；用户同意前**不擅自迁移**、也不在旧模型上直接接手。

# 初始化相位（init · 新项目 / 尚无存储）

前提：已读 `SKILL.md`。**仅用于既无 `.handoff/` 也无旧模型的项目**；有旧模型（`HANDOFF.md` / `HANDOFF-ARCHIVE/` / `.handoff/fp.*`）→ 走 `references/migrate.md`。

## 性质

**register-first**：本模型把「未决项」**定义**为 `.handoff/` 里登记的条目——**账本不是镜子**。未登记的不算未决项（最多进 `unconfirmed` 候选）。故新项目的「完备」**构造性成立**（不存在「外部未决项」）。**init 的意义＝把这个约定钉在第一天**，防止项目日后长成开放世界（即未来的迁移工程）。

## 步骤

0. **前提**：本相位由用户显式调用；`add` 等写入命令在**无存储时直接非零退出**（不顺手建库），故新项目的第一个动作必须是下面这条 `init`。

1. **建骨架（脚本，勿手搓）**：
   ```sh
   python3 <技能目录>/scripts/handoff.py init
   ```
   → 建 `.handoff/` 全部 9 槽 + `index`。
2. **构建源登记表（`scope`）**：
   ```sh
   python3 <技能目录>/scripts/handoff.py scope scan     # 机械候选（标记命中 / 旧 HANDOFF 引用 / 未登记）
   python3 <技能目录>/scripts/handoff.py scope add <path|glob>   # 逐条登记
   ```
   → 给候选清单 → **请用户确认 / 补充** → 逐条 `scope add`。
   - **契约**：**只有登记的源被读**；未登记 → **不是未决源**（定义使然）。`check` 校每条登记**可解析**（路径存在 / glob 有命中）。
   - **`scope scan` 仅提议**：漏扫**不影响契约成立**；每轮把「未登记但命中标记」的候选记入覆盖声明「**未能确认**」。
3. **钉约定（register-first）**：确保 `AGENTS.md` 含该节：
   ```
   ## 工作存储
   - 未决项只写 `.handoff/`（登记真源：`actions/` 等；其余处的待办文本仅为候选）。
   ```
   - **幂等用机械锚**：已存在 `## 工作存储` 标题、或提及 `.handoff/` 的行 → **跳过**（勿重复、勿覆盖）。
   - 无 `AGENTS.md` → **新建**并写入该节。
4. **门禁**：`python3 <技能目录>/scripts/handoff.py check`（不过不得交接）。
5. **出覆盖声明**：`读到 / 写入 / 未能确认`。

## 硬约束

- **只经 `handoff` CLI 写条目**（单一写入口）；勿手改 `.handoff/` 内的条目文件。
- **register-first**：不做「项目级完备」承诺——只保证「登记的都在」＋「候选显式」。
- `scope` 声明**先于**任何登记；未声明处不进契约。
- 约定落点 `AGENTS.md`；写入**追加、不覆盖**。
- 只建 `.handoff/`，不建别的；不假设 git / 语言 / 布局。
- **`python3` 缺失** → **询问用户安装**，或降级为最小 `sh` 操作（仅 `add/close/check`）。

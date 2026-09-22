---
name: project-handoff
description: >-
  Maintain a project's handoff store (.handoff/, plain text): a multi-dimensional
  project handoff — status, summary, actions, pitfalls, decisions, commands, scope, exit,
  plus a machine-checked read-back — with a next-step pointer, driven by a script-enforced
  `handoff` CLI (single write path, coverage statement). Use when handing off between
  sessions or tools, or resuming or continuing prior work on a project. Initializing a
  new project's store or migrating an old HANDOFF.md model is done only when the user
  explicitly asks. NOT for: ephemeral scratch notes, or work outside a project.
version: 4.0.0
slug: project-handoff
displayName: project-handoff
---

# 项目交接（Project Handoff · v3 存储模型）

## 角色

维护项目**交接存储** `.handoff/`（纯文本）：**9 槽** ＝ 一份「让接收方（agent / LLM）接得上」的**多维交接件**（**不止未决项**）。条目**只经** `scripts/handoff.py` CLI 写（**单一写入口** + **机检门禁**）。

- **维度闭合**：9 槽固定；槽外信息 → `unconfirmed`（未能确认），**不即兴开槽**。
- **只记不可推导项**：可读的用指针，读不到的才记——交接的意义＝**免重读仓库**。
- **P1 不删 / P2 可重建 / P3 不静默**（见下）。

## 何时读哪个相位

| 意图 | 读 |
|---|---|
| 接手 / 继续之前的工作 / 新 session 进入已有项目 | `references/resume.md` |
| 交接 / 收尾 / 跨会话·跨工具移交 | `references/handoff.md` |
| 新项目 / 尚无工作存储 | `references/init.md`（**仅显式调用**，非自主命中）|
| **发现旧模型**（`HANDOFF.md` / `HANDOFF-ARCHIVE/` / `.handoff/fp.*`）| **先** `references/migrate.md`（一次性，**仅显式调用**）|

## 存储（`.handoff/`，纯文本，不假设 git）

```
index   status   summary   scope   exit   next          # 导航 + 单文件槽 + 指针
actions/<域>.jsonl    pitfalls/<域>.jsonl    commands/<用途>.jsonl
decisions/<id>.md     unconfirmed.jsonl      closed/
prev/<slot>                                     # 单文件槽覆写前快照（自动，回读用）
```

- **9 槽**：S1 `status` · S2 `summary` · S3 `actions` · S4 `pitfalls` · S5 `confirm`（运行时，不入盘）· S6 `decisions` · S7 `commands` · S8 `scope` · S9 `exit`；基础设施：`index`（脚本生成）/ `next`（「下一步唯一一条」指针）/ `unconfirmed`（未能确认账本）/ `closed`（归档）/ `log`（使用快照）。
- **条目（JSONL，键序固定）**：`{"id","created","summary",[status,blockedBy],topic?,src?,detail?}`；归档行加 `closed`/`outcome`。
- `id` = `<type><6 位>`；`type↔槽`：`t`→actions / `p`→pitfalls / `c`→commands / `d`→decisions / `u`→unconfirmed / `q`→closed（历史）。**全槽唯一、永不复用、脚本分配**。
- **决策**：`decisions/<id>.md` = frontmatter(`id/created/status/domain/topic`) + ADR 正文。
- **`index` 由脚本重建**；**永不手写**。

## CLI（`scripts/handoff.py`，python3）

`init` · `index` · `check` · `log` · `add` · `set` · `edit` · `rm` · `close` · `next` · `unconfirmed` · `scope` · `confirm` · `filter` · `view` · `export` · `import`。

- **`check` ＝ 相位门禁**：9 槽齐 / `index` ↔ 文件计数一致 / id 全局唯一 / 日期规则（`created ≤ closed ≤ today`、禁未来日）/ `next` 有效；**不过即非零退出，相位不得前进**。
- **`add` / `close` ＝ 唯一写入口**；**日期脚本盖、id 脚本分配**（LLM 无从编造）。**`add` 参数面按型分列**：`handoff add action|pitfall|command|decision --…`，每型只收本型字段——旧 `add --slot <槽>` 的**并集面**会静默丢弃本型不消费的键，现**硬报错并印新形**；`edit` 亦按条目型校验可改面（不符即报错）。
- **`next` 自动补位**：`close`（含 `unconfirmed resolve` 的内部关闭）关掉的**正是当前 `next`** → 按策略补下一条（`--no-refill` 关；`handoff next --auto` 人工触发同一策略；`next <id>` 随时覆盖补位结果）。策略**确定性可复算**：候选池＝live `actions`（排除 `status=blocked`）；排序键 `(有效档, created↑, id↑)`；基础档 `[高]`0 / `[中]`·无前缀1 / `[低]`2（前缀亦认全角 `【高】` 与 `high`/`med`/`mid`/`medium`/`low`，大小写不敏感）；**时间维**＝超期每满 30 天升一档（下限 0，故陈年 `[低]` 会越过新鲜 `[高]`）。补位/留空均**打印依据**（P3 不静默）。空池或全 blocked：`close` 留空并说明，`next --auto` **拒绝且不写指针**。
- **S7 `commands` 先薄**：只收 `AGENTS` / `README` 里**没有**的非显然命令 ＋ 环境例外（可推导的**不重复记**）→ **常空正常**。每次门禁落一条 `log` 快照（`handoff log --stats`），供日后据数据决定是否保留该槽。
- **`set <status|summary|exit>`**：单文件槽写入口（`add` 只覆盖条目槽 + `decisions`）；**单文件槽唯一写路径**。**整槽覆写、无追加语义**——想改一行也必须先读回全量再写。两道守卫：空内容拒写（`--allow-empty` 才放行）；旧内容 >200 字符且新内容 <60% 亦拒写（`--force` 才放行，防「把整槽覆写当局部编辑」清空槽位）。**快照先于全部守卫**：只要旧槽非空，无论这次写被放行、被骤降守卫拒、还是被空内容守卫拒，旧内容都已落到 `.handoff/prev/<slot>` 可回读。
- **纠错入口**：`edit <id>`（改安全字段；`id`/`created`/`closed` 不可改）与 `rm <id>`（→ `.handoff/trash/` + 记 `void` 防 id 复用 + 引用守卫）——错误**不经手搓**，免 `export→改→import --force` 全量重写。
- **`confirm` ＝ 机检 read-back**：脚本出题、脚本判卷；**不 `PASS` ＝ 交接未完成**。题面**每次调用重新随机抽**——「先出题、后作答」必须两次带**同一 `--seed`**，否则题已换而答案错位。抽查题按**视图行文本**判分（`[id] topic summary`，非 open 条目含末尾 `  (status)`），照 `handoff view` 行原样抄（去掉行首 `- `）即可，勿只抄 summary。
- **`view`**：全局视图（认识整体），默认 stdout；`--save` 存盘（默认 `<项目根>/handoff-view.md`），属**用户所有、非权威、不 `check`**。
- 无 `python3` → **询问用户安装**，或降级最小 `sh`。

## 不变量（任一相位必须守）

- **P1 不删**：只追加；`closed` 永不重写；移除仅在关闭序内原子完成。
- **P2 可重建**：`index` 由脚本重建；**不生成、不落盘第二副本**。
- **P3 不静默**：每次运行输出「**读到 / 写入 / 未能确认**」；`confirm` 为**双向确认**。

## 硬约束

- 不假设 git / 语言 / 工具 / 布局；需用则**先探测**。
- **未决语义唯一落点 `.handoff/`**（白名单硬契约）；其余处的待办文本是**候选**，非未决项。
- **维度闭合**：9 槽固定，槽外→`unconfirmed`。
- **源登记表闭合**：**只有 `scope` 登记的源被读**；未登记 → **非未决源**（定义使然）。`check` 校每条登记**可解析**（路径存在 / glob 有命中）；`scope scan` **仅提议**（机械候选），漏扫不影响契约成立。
- **迁移先于交接**：有旧模型时，**告知用户并请求迁移**（`init`/`migrate` **仅显式调用**）；同意后先走 `migrate`（它建存储），勿先建空存储、勿在旧模型上直接交接。
- **项目约定**：任何**建立或使用存储**的相位（`init`/`migrate`/交接）都要确保 `AGENTS.md` 含「未决项只写 `.handoff/`」一节（**无则新建**）——防持续偏移。
- 崩溃最坏产生重复（按 id 去重，closed 胜）——**绝不丢**。

## 反模式

- 手改 `.handoff/` 条目（绕过 CLI → 门禁兜不住）。
- 手填日期 / 自选 id。
- 把未决写在 `.handoff/` 之外（→ 走 `unconfirmed`，**不假装覆盖**）。
- 手写第二份「视图 / 摘要」当交接件（→ 双源必漂）。

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
version: 4.3.1
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

`init` · `index` · `check` · `selftest` · `log` · `add` · `set` · `edit` · `rm` · `close` · `next` · `unconfirmed` · `scope` · `confirm` · `filter` · `view` · `export` · `import`。

- **`check` ＝ 相位门禁**：9 槽齐 / `index` ↔ 文件计数一致 / id 全局唯一 / 日期规则（`created ≤ closed ≤ today`、禁未来日）/ `next` 有效；**不过即非零退出，相位不得前进**。
- **`add` / `close` ＝ 唯一写入口**；**日期脚本盖、id 脚本分配**（LLM 无从编造）。**`add` 参数面按型分列**：`handoff add action|pitfall|command|decision --…`，每型只收本型字段——旧 `add --slot <槽>` 的**并集面**会静默丢弃本型不消费的键，现**硬报错并印新形**；`edit` 亦按条目型校验可改面（不符即报错）。
- **`next` 自动补位**：`close`（含 `unconfirmed resolve` 的内部关闭）关掉的**正是当前 `next`** → 按策略补下一条（`--no-refill` 关；`handoff next --auto` 人工触发同一策略；`next <id>` 随时覆盖补位结果）。策略**确定性可复算**：候选池＝live `actions`（**仅 `status=open`／缺省入池**；blocked＝等待中、其余值非法均排除）；排序键 `(有效档, created↑, id↑)`；基础档 `[高]`0 / `[中]`·无前缀1 / `[低]`2（前缀亦认全角 `【高】` 与 `high`/`med`/`mid`/`medium`/`low`，大小写不敏感）；**时间维**＝超期每满 30 天升一档（下限 0，故陈年 `[低]` 会越过新鲜 `[高]`）。补位/留空均**打印依据**（P3 不静默）。空池或全 blocked：`close` 留空并说明，`next --auto` **拒绝且不写指针**。
- **S7 `commands` 先薄**：只收 `AGENTS` / `README` 里**没有**的非显然命令 ＋ 环境例外（可推导的**不重复记**）→ **常空正常**。每次门禁落一条 `log` 快照（`handoff log --stats`），供日后据数据决定是否保留该槽。
- **`set <status|summary|exit>`**：单文件槽写入口（`add` 只覆盖条目槽 + `decisions`）；**单文件槽唯一写路径**。**整槽覆写、无追加语义**——想改一行也必须先读回全量再写。两道守卫：空内容拒写（`--allow-empty` 才放行）；旧内容 >200 字符且新内容 <60% 亦拒写（`--force` 才放行，防「把整槽覆写当局部编辑」清空槽位）。**快照先于全部守卫**：只要旧槽非空，无论这次写被放行、被骤降守卫拒、还是被空内容守卫拒，旧内容都已落到 `.handoff/prev/<slot>` 可回读。
- **纠错入口**：`edit <id>`（改安全字段；`id`/`created`/`closed` 不可改）与 `rm <id>`（→ `.handoff/trash/` + 记 `void` 防 id 复用 + 引用守卫）——错误**不经手搓**，免 `export→改→import --force` 全量重写。
- **`status` 值域按型闭集**（`add`/`edit` 同一守卫，t000138）：`action`/`command`＝`open`|`blocked`；`pitfall`＝`open`|`fixed`|`blocked`；缺省（不传或清空）＝`open`。**`closed` 不是可写值**——关闭唯一入口＝`close --outcome`（edit/add 传 `closed` 或表外值即硬报错）；`check` 对 live 行同闭集硬判；补位池**仅 open 入池**（blocked＝等待中、其余＝非法值，均不补位）。`selftest` ＝ 闭集守卫的双向夹具自证（临时 store 内真 CLI 跑通 9 断言）。
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

## 最短真实样例（初始化 → 交接一轮）

前置：项目根目录、`python3` 可用、已获用户显式授权建存储。

```bash
python3 scripts/handoff.py init                 # 建 .handoff/，自动生成 index
python3 scripts/handoff.py add action --summary "[高] 修复登录重定向循环" --domain auth --src src/auth/login.ts:42
python3 scripts/handoff.py add pitfall --summary "测试库必须先 seed，否则 check 全红" --domain test
printf '已完成认证重构；测试待补\n' | python3 scripts/handoff.py set status --file -
python3 scripts/handoff.py check                # 门禁：非零退出 = 不得收尾
python3 scripts/handoff.py confirm --seed 1     # 出题（两次须同 --seed）
python3 scripts/handoff.py confirm --seed 1 --answers "<按 view 行原样逐行>"   # 判卷，PASS 才算交接完成
```

产出（摘录）：`handoff check` 打印 `handoff check: OK` 并落一条 `log` 快照；`confirm` 判卷通过打 `PASS`——**不 PASS ＝ 交接未完成**。接收方恢复上下文只读 `references/resume.md` 相位（`view` + `next` 即可接上）。

## 失败出口

- **`check` 非零退出**：按输出行修——列出的即不满足的判据（槽缺失 / index 计数不一致 / id 冲突 / 日期违规 / `next` 无效）。修法只经 CLI：缺条目 `add`，多出条目 `rm`/`close`，**不手改文件**。修完重跑，`OK` 为唯一通过判据。
- **`set` 被拒（空内容 / 骤降守卫）**：输出已说明是哪道守卫。确属要写空 → `--allow-empty`；确属大幅精简 → `--force`。两守卫之前的旧内容都已快照到 `.handoff/prev/<slot>`，可回读核对后再定。
- **`add` 报「参数面不符」**：你用的是旧 `add --slot <槽>` 并集形——按报错打印的新形重输（`add action|pitfall|command|decision --…`，每型只收本型字段）。
- **`add`/`edit` 报「status 非法」**：值域按型闭集（`action`/`command`＝`open|blocked`，`pitfall`＝`open|fixed|blocked`）；要关闭条目走 `close --outcome`，不要把 `closed` 当状态写。
- **`confirm` 不 PASS**：答案按 `handoff view` 行文本原样抄（去行首 `- `，含末尾 `(status)`）；若两次调用 `--seed` 不同，题已换，重取题再答。
- **无 `python3`**：询问用户安装；不可安装时降级最小 `sh` 约定（写入口纪律照守，门禁缺失须在交接里明示）。

## FAQ

**常见问题从哪查？** 本文「硬约束 / 反模式 / 失败出口」三节覆盖高频误用；相位细节读 `references/` 对应文件（见「何时读哪个相位」表）。

**为什么不能直接编辑 `.handoff/` 里的文件？** 单一写入口是门禁的前提：日期、id、index 全由脚本管理，手改会绕过校验且 `check` 兜不住（见反模式）。

**commands 槽老是空的，坏了吗？** 不是——S7 只收 AGENTS/README 里没有的非显然命令，常空正常（见「S7 `commands` 先薄」）。

**MFA/多工具协作也一样吗？** 是——不假设 git/语言/工具；跨工具交接同一存储，`confirm` 的双向 read-back 就是给跨工具场景设计的。

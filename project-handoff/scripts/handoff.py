#!/usr/bin/env python3
"""handoff — 项目交接存储 CLI（单一写入口 + 机检门禁）

设计依据：audits/2026-09-21-handoff-design-brief.md
不变量：P1 不删（append-only）/ P2 可重建（无第二副本）/ P3 不静默。

子命令：init index check log add set edit rm close next unconfirmed scope confirm filter view export import
"""
from __future__ import annotations

import argparse
import fnmatch
import glob
import hashlib
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ID_RE = re.compile(r"^([tpducq])(\d{6})$")

# 文本槽里扫条目 id 用（`exit`/`summary` 的交接陈述面）。与死指针判据**刻意同源**——
# 之前本仓 `handoff-freshness-check.py` 自己抄了一份 `\bt\d{6}\b`，两处模式若各自演进
# 就会一次判了、另一次没判（双源缺口）。这里单一模式，两条判据共用。
FIND_ID_RE = re.compile(r"\bt\d{6}\b")
# 提及已闭条目时，同一行必须带的显式关闭标记。**刻意收窄成显式标记而非推断**：
# 已闭/closed/完成/毕/已发布/已收口/已落地。措辞变了该改这张表，不是改判据去迁就。
CLOSED_MARKERS = ("已闭", "closed", "CLOSED", "已完成", "完成", "毕",
                  "已发布", "已收口", "已落地")


def rid_re_match(rid: object) -> bool:
    return isinstance(rid, str) and bool(ID_RE.match(rid))

# 条目槽（JSONL、按分区落文件）
ENTRY_SLOTS = {
    "actions": {"type": "t", "part": "domain"},
    "pitfalls": {"type": "p", "part": "domain"},
    "commands": {"type": "c", "part": "purpose"},
}
UNCONF_SLOT = "unconfirmed"            # 单文件 unconfirmed.jsonl
DOC_SLOT = "decisions"                 # decisions/<id>.md（frontmatter + 正文）
TYPE2SLOT = {"t": "actions", "p": "pitfalls", "c": "commands", "u": "unconfirmed", "d": "decisions", "q": "closed"}
KEY_ORDER = ["id", "created", "summary", "status", "blockedBy", "topic", "src", "detail", "closed", "outcome"]
ALLOWED_KEYS = set(KEY_ORDER)
SINGLES = ("status", "summary", "scope", "exit")
# scope 建库即写注释头：空项目留空不再是 0 字节——0 字节＝「未执行 init」（t000018）
SCOPE_HEADER = ("# 对账范围（P3）：未决项可能落在哪（一行一路径/glob；# 注释允许）\n"
                "# 空项目可只留本注释——register-first：未登记 ≠ 未决源。\n")

# ---------------- add 参数面：按**型**声明，一处生成两侧（v3.2.0 / t000089） ----------------
# 旧形 `add --slot <槽>` 把五种异构记录的参数**并集**挂在同一子命令上：argparse 全接受、
# cmd_add 按槽只读子集，余下**静默丢弃**（实测 4/4 组合丢内容仍 rc=0 且 `check` OK——丢弃＝缺席，
# 产物本身合法，故下游无从反推；文档照抄即成假称）。现把参数面拆到型一级：**下面的 fields 列表
# 既是该型子命令的 flag 面、又是 cmd_add 消费的键**，两侧同源；main() 的自检逐型比对 argparse
# 实得 dest，任一侧被单独改动即当场报错（不做"看起来能用"的沉默）。
ADD_KINDS: dict[str, dict] = {
    "action":   {"slot": "actions",   "part": "domain",
                 "fields": ["summary", "domain", "status", "blockedBy", "topic", "src", "detail"],
                 "live_status": {"open", "blocked"}},
    "pitfall":  {"slot": "pitfalls",  "part": "domain",
                 "fields": ["summary", "domain", "status", "blockedBy", "topic", "src", "detail"],
                 "live_status": {"open", "fixed", "blocked"}},
    "command":  {"slot": "commands",  "part": "purpose",
                 "fields": ["summary", "purpose", "status", "blockedBy", "topic", "src", "detail"],
                 "live_status": {"open", "blocked"}},
    "decision": {"slot": "decisions", "part": None,
                 "fields": ["title", "body", "status", "supersedes", "domain", "topic"]},
}
KIND2SLOT = {k: v["slot"] for k, v in ADD_KINDS.items()}
SLOT2KIND = {v: k for k, v in KIND2SLOT.items()}
SLOT_FIELDS = {v["slot"]: set(v["fields"]) for v in ADD_KINDS.values()}


def live_status_of(kind: str) -> set[str]:
    """该型条目在 live 区的 status 值闭集（缺省视为 open）。closed 不在其中：
    关闭唯一入口＝`close --outcome`（edit/add 拒收，t000138——否则旁路写入会造出
    无 closed/outcome、不迁 closed/ 的半关行，并混进补位池）。

    **`pitfall` 的 `fixed` 不是销账**（2026-10-03 用户裁定改语义）：它表示
    「这个坑对应的缺陷已修，**留案以免重犯**」——条目**仍留在 live 区**、仍被
    `check`/`view`/`index` 当活条目、仍计入各槽计数，**不进 `closed/`、不迁走、
    不销账**。记成 `fixed` 的坑与记成 `open` 的坑，在**绝大多数判据面前等价**：
    值域校验（只验「在不在闭集里」）与各槽计数、补位池、视图呈现**都不看这个值**。
    **唯一的例外是 next 指针判据**——它要求 next 指向 `open` 行，所以 `fixed` 的坑
    不能当 next（实测：`next <fixed 的坑>` rc=0 但随后 `check` rc=1 报
    「status='fixed'，不是 open」）。而那是在**守 next 的有效性、不在销坑**。
    换句话说 `fixed` **基本是自述，不是账**——别把「大部分坑都 open」读成「大部分坑都没
    修」（本库实测过一批：多数有守卫已修、有意设计的不算缺陷，真缺陷仍在的是少数）。
    要销账走 `close --outcome`，那是另一回事。
    **更正**：先前此处写「唯一读它的是值域校验」是**错的**（独立审计实测证伪）——
    `check` 的 next 指针判据也读 status：把一条 `fixed` 的坑设成 next，`check` 会 rc=1 报
    「status='fixed'，不是 open」。所以它**有**一个消费者，但那个消费者是在**守** next 指针
    的有效性、不是在销坑。**别为此再加闸**：给一个刻意「不被依赖」的状态造依赖，与本语义
    的立意相反。
    """
    return ADD_KINDS[kind].get("live_status", set())


def guard_status(kind: str, val) -> None:
    if val is not None and val != "" and val not in live_status_of(kind):
        die(f"status {val!r} 非法（该型合法：{sorted(live_status_of(kind))}，缺省=open）；"
            f"关闭唯一入口＝close --outcome")


UNCONF_FIELDS = {"summary", "src", "detail"}      # 候选行落盘面（`--ref` 存成 src）
CLOSED_FIELDS = {"summary", "detail", "topic", "outcome"}


def guard_partition(where: str, key: str, val) -> str:
    """分区键（domain/purpose）**会被拼成文件名**（`<slot>/<值>.jsonl`），故必须先校验。

    缺陷 p000046：值里带 `/` 会拼出子目录（`commands/a/b.jsonl`），而加载面用
    `glob("*.jsonl")` **不递归** ⇒ 那条已登记的条目对 `check`/`view`/`index` **完全
    隐形**：check 报 OK、index 计数 0、现实 1，且无任何东西报错。

    允许 CJK（本库实际在用「交接」「发布」「门禁」等作 domain），禁的是**路径语义**：
    分隔符、NUL、`.`/`..`、前后空白、超长名。不用白名单字符集——那会把 CJK 和将来
    合理的命名一起拒掉；用「不能改变路径指向」来判，才不会误伤。
    """
    if val is None:
        return "_global"
    v = str(val)
    bad = []
    if not v or not v.strip():
        bad.append("空")
    if v != v.strip():
        bad.append("前后有空白")
    if v in (".", ".."):
        bad.append("是路径相对段")
    if any(c in v for c in ("/", "\\", "\0")):
        bad.append("含路径分隔符/NUL")
    if ":" in v:
        # Windows：**盘符相对**（`C:evil`）解析到该盘当前目录而非 store ⇒ 写到 store
        # 之外；`ok:hidden` 是 NTFS 备用数据流，`glob` 永远扫不到。两者都**改变路径
        # 指向**，与分隔符同级，不是超纲要求（本技能正文承诺支持 Windows）。
        bad.append("含 `:`（Windows 盘符相对 / 备用数据流）")
    # Windows 对尾随空格/点的设备名（`com1 .txt`）同样按设备处理 ⇒ 一并去掉。
    # **刻意不拦 Windows 保留设备名**（CON/NUL/COM1…）——曾按推演加过，Windows 10.0.26200
    # 实测证伪：经 Win32 `CreateFile`（＝CPython 走的那条路）`CON.jsonl`/`NUL.jsonl`/
    # `con.jsonl`/`COM1.jsonl` **全部创建成功、`File.Exists=True`、且目录枚举可见**。
    # 设备名解析发生在 **cmd/PowerShell 路径层**，不在 `CreateFile` 层；用 `New-Item` 验会
    # 因两层解析不一致得到自相矛盾的结果（`New-Item` 说没建成、目录里却有）。拦它是误拒。
    # 同理不拦尾随空格/点（`com1 .txt`、`nul .jsonl`、`con..jsonl` 实测均正常创建）。
    if any(ord(c) < 32 for c in v):
        # 只拦 **ASCII C0**（< 0x20）：这类会串行化、破坏文件名结构。
        # `\x7f`／ZWSP／RTL **刻意不拦**——它们不改路径指向，p000046 幽灵模式
        # 不复现（glob/index/check 都正常），拦了属超纲；残留后果只是 `ls` 不可见
        # 导致可能重名，与「条目不可见」不是一回事。
        bad.append("含 ASCII C0 控制字符")
    if len(v) > 64:
        bad.append(f"超长（{len(v)} > 64）")
    if bad:
        die(f"{where}: 分区键 {key}={v!r} 不可用作文件名（{'、'.join(bad)}）。"
            f"它会被拼成 <槽>/<值>.jsonl；带分隔符会写进子目录、含 `:` 或为设备名会写到别处"
            f"或静默丢失，而加载面不递归 ⇒ 条目就成了 check/view/index 都看不见的幽灵。"
            f"用单段普通名字（可含中文），别用 `/` `\\` `:` 或设备名。")
    return v


def editable_fields(slot: str) -> set[str]:
    """该槽**条目实际可承载**的键集——edit 的 flag 面由它并集生成，两侧同源不另立名单。

    分区键（domain/purpose）可改＝换分区文件；closed 归档行只可改摘要类字段＋结局；
    unconfirmed 走自己的落盘面（`outcome` 属关闭动作，不由 edit 伪造）。
    这里**不再回落到 `ALLOWED_KEYS`**：回落会让表外槽接受任意存储键，与文档承诺相反。
    """
    if slot == "closed":
        return set(CLOSED_FIELDS)
    if slot == UNCONF_SLOT:
        return set(UNCONF_FIELDS)
    if slot == DOC_SLOT:
        return set()                            # 决策文档不走 edit（改判＝另开一条 --supersedes）
    kind = SLOT2KIND.get(slot)
    return set(ADD_KINDS[kind]["fields"]) if kind else set()


EDIT_KEYS = sorted({f for s in (*SLOT_FIELDS, UNCONF_SLOT, "closed") for f in editable_fields(s)})

# 条目写入类命令：都要求存储已存在（见 main 的守卫）。建库只归 init / import（migrate 流程）。
WRITER_CMDS = {"add", "close", "set", "edit", "rm", "unconfirmed", "next"}


def die(msg: str, code: int = 1):
    print(f"handoff: {msg}", file=sys.stderr)
    sys.exit(code)


def today() -> str:
    return date.today().isoformat()


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


# 命令行里最容易被 shell 吃掉内容的字符（p000016/p000019/p000035/p000039/p000041 同族，
# 本会话已踩四次）。它们到达 CLI 时**通常已被 shell 展开或截断** ⇒ CLI 看见的往往不是用户
# 想写的东西，所以这类内容根本不该走 argv。
# 只有这两种会被 shell **替换内容**（反引号＝命令替换、`$`＝变量展开）。
# 反斜杠**刻意不拦**：它只做转义、不替换内容，且在 Windows 路径 / Markdown / 代码引用里
# 极常见，拦它会大面积误伤（本会话第一版就误加了，已去掉）。
SHELL_UNSAFE = ("`", "$")


def require_text(cmd: str, label: str, v, from_shell: bool = True) -> None:
    """写入型字符串参数守卫：① 非空（t000121/p000048/p000051）；② 不含 shell 危险字符。

    ① 空串与全空白＝删除语义，静默写入即数据丢失。`None`＝未提供（放行）；`""`／全空白＝
    提供但为空（拒）。报错文案与「条目不存在」区分开——两者是不同故障。

    ② **根治方向是「内容不走 argv」**：这里拒的是**已经错了的值**并指向 `--from-file`。
    单纯的 denylist 不够（CWE-88：denylist 不可作唯一防线，parameterization 才是 High
    效力缓解）——但 denylist 有独立价值：它把「shell 吃掉了内容」这件事**当场暴露**，
    而不是让人拿着一段被截断的文本以为写对了。**真正的保障是 `--from-file`／stdin。**
    """
    if v is None:
        return
    s = str(v)
    if not s.strip():
        die(f"{cmd}: {label} 为空——写入型字符串参数不接受空串/全空白"
            "（空串＝删除语义，疑似漏喂变量如 `$(cat 空文件)`）")
    # 只对**走 argv** 的值提示 shell 危险字符。`--from-file`/stdin 来的内容由程序
    # 解析、从未经过 shell，里面的反引号/`$` 就是字面量，提示它反而是噪声。
    #
    # **为什么不硬拒（2026-10-03 改）**：本机实测单引号内反引号/`$` **不展开**，而 CLI
    # 收到的值无法区分「用户用双引号、已被展开」与「用户用单引号、本就安全」——
    # 值到达时两者形态相同（前者已无反引号，后者还带反引号字面量）。于是硬拒必然
    # **误拒单引号这种安全写法**，而该抓的「已被展开」又因值里没有反引号而**抓不到**。
    # CWE-88 的分工也是这样：Parameterization 是唯一 High 效力项（即 `--from-file`），
    # validation 只是辅助、且原文说的是「不要**只**依赖查找畸形输入」，并明确承认
    # denylist 对「畸形到该直接拒绝」的输入有用——而单引号传参并不畸形。
    # 所以这里降为**提示**，真检出交给写后回读（`echo_back`）：它看的是**落盘结果**，
    # 不猜输入形态，双引号被吃掉时当场可见，单引号安全写法零干扰。
    if from_shell:
        hit = [c for c in SHELL_UNSAFE if c in s]
        if hit:
            print(f"  ⚠ {cmd}: {label} 含 shell 特殊字符 {hit}——**若你用了双引号，这段内容"
                  f"可能已被 shell 展开**（反引号＝命令替换、`$`＝变量）。单引号安全；"
                  f"要彻底避开请用 `--from-file <路径|->`（由程序解析、不经 shell）。"
                  f"写完请核对下方回读值。", file=sys.stderr)


def load_from_file(cmd: str, path: str, allowed: set) -> dict:
    """`--from-file <路径|->`：内容**由程序解析**，完全不经过 shell（p000016/019 根治）。

    格式：每行 `字段=值`。值可跨行续写（行尾 `\\`）——因为要贴代码片段/多行说明时，
    单行 `k=v` 装不下。空行与 `#` 开头（行首无 `=`）忽略。字段不在 `allowed` 内即报错
    （防把 `--summary` 写进文件却静默丢弃，那正是本 CLI 早前的老病）。
    """
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    out: dict[str, str] = {}
    key = None
    for ln_no, ln in enumerate(raw.splitlines(), 1):
        if key is None:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            if "=" not in s:
                die(f"{cmd} --from-file: 行 {s[:40]!r} 不是 `字段=值` 格式")
            k, v = s.split("=", 1)
            k = k.strip().lstrip("-")
            if k not in allowed:
                die(f"{cmd} --from-file: 字段 {k!r} 不被本命令接受"
                    f"（可接受：{'、'.join(sorted(allowed))}）")
            if k in out:
                die(f"{cmd} --from-file: 字段 {k!r} 重复出现（第 {ln_no} 行）——"
                    f"后者覆盖前者是**静默丢弃**，请合并成一处")
            key = k
            out[key] = v
            if not ln.endswith("\\"):
                key = None
        else:
            out[key] += "\n" + ln
            if not ln.endswith("\\"):
                key = None
    if not out:
        die(f"{cmd} --from-file: 没解析出任何 `字段=值`")
    return out


def echo_back(st: Store, entry_id: str, label: str = "回读") -> None:
    """写完**回读**落盘值并显示（P3 不静默；p000019/p000041 根治的关键一环）。

    为什么必须有它：命令行里的反引号/`$` 被 shell 展开后，**CLI 收到的是展开后的值**，
    它无从知道原意 —— 硬拒抓不到、单引号安全写法又会被误拒。唯一可靠的判据是
    **看结果**：把刚写进磁盘的那行读回来摆在你面前，双引号被吃掉时当场可见
    （不用等几小时后回读才发现），而单引号安全写法**不会**产生任何额外噪声。
    它检测的是落盘事实，不猜输入形态。

    显示长文本字段的前若干字 —— 被吃掉最常发生在 `detail`／`src` 这类长文本上。
    """
    row = None
    for r in st.load_live():
        if r.get("id") == entry_id:
            row = r
            break
    if row is None:
        for r in st.load_closed():
            if r.get("id") == entry_id:
                row = r
                break
    if row is None:
        # decisions 槽是 `decisions/<id>.md`（frontmatter ＋ 正文），**不在**
        # live/closed 里。原实现查不到就报「异常」——而 `add decision` 明明成功，
        # **把成功报成失败**，与 P3「不静默」的本意正好相反（独立审计实测抓到）。
        for f in sorted(st.decisions_dir().glob("*.md")) if st.decisions_dir().is_dir() else []:
            if f.stem == entry_id:
                fm = _frontmatter(f)
                print(f"  ↩ {label} {entry_id}（已落盘，实际值）：")
                # 键表＝实测会出现在 decisions frontmatter 里的字段；**`title` 是死键**
                # （writer 只把 title 写成正文 H1，frontmatter 永不含它）——独立审计抓到。
                for k in ("topic", "status", "domain", "supersedes"):
                    if fm.get(k):
                        print(f"      {k}: {str(fm[k])[:160]}")
                _body = f.read_text(encoding="utf-8").split("---", 2)
                tail = _body[2] if len(_body) > 2 else ""
                tail = tail.strip().splitlines()
                if tail:
                    print(f"      body: {' '.join(tail)[:160]}"
                          f"{'…（已截断，全文见文件）' if len(' '.join(tail)) > 160 else ''}")
                return
        print(f"  ↩ {label}：条目 {entry_id} 未在 live/closed/decisions 中找到（异常）",
              file=sys.stderr)
        return
    print(f"  ↩ {label} {entry_id}（已落盘，实际值）：")
    # 键表＝**实测**会出现在 live/closed 行里的字段（不是"看着相关就加上"）：
    # 实测 action 行 = id/created/summary/status/detail/src/topic，closed 行多 outcome。
    # `title`/`body`/`ref` **都不在通用路径**（body 只在 decisions 槽、已由下面的
    # decisions 专用分支回读；ref 只在 unconfirmed、而它不在 live/closed 里）——
    # 上一版把三者塞进键表，变异测试证明那是**死项**（去掉也不影响任何断言）。
    for k in ("summary", "topic", "detail", "src", "outcome"):
        v = row.get(k)
        if not v:
            continue
        s = str(v).replace("\n", " ⏎ ")
        print(f"      {k}: {s[:160]}{'…（已截断显示，全文见文件）' if len(s) > 160 else ''}")


def ordered(entry: dict) -> dict:
    return {k: entry[k] for k in KEY_ORDER if k in entry}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not path.is_file():
        return rows
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            die(f"{path}:{i} 非法 JSON: {e}")
    return rows


def write_jsonl_atomic(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(ordered(r), ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def append_jsonl(path: Path, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ordered(row), ensure_ascii=False) + "\n")


class Store:
    def __init__(self, root: Path):
        self.d = root
        self.root_dir = root.resolve().parent
        self._pre_tamper: list | None = None    # 写前旁证快照，见 note_pre_tamper

    # ---- 路径 ----
    def live_shards(self) -> list[Path]:
        out = []
        for slot in ENTRY_SLOTS:
            sd = self.d / slot
            if sd.is_dir():
                out += sorted(sd.glob("*.jsonl"))
        return out

    def closed_shards(self) -> list[Path]:
        cd = self.d / "closed"
        return sorted(cd.glob("*.jsonl")) if cd.is_dir() else []

    def unconf_file(self) -> Path:
        return self.d / "unconfirmed.jsonl"

    def decisions_dir(self) -> Path:
        return self.d / "decisions"

    # ---- 载入 ----
    def load_live(self) -> list[dict]:
        rows = []
        for slot in ENTRY_SLOTS:
            sd = self.d / slot
            if sd.is_dir():
                for f in sorted(sd.glob("*.jsonl")):
                    for r in read_jsonl(f):
                        r["_slot"] = slot
                        r["_file"] = f
                        rows.append(r)
        for r in read_jsonl(self.unconf_file()):
            r["_slot"] = "unconfirmed"
            r["_file"] = self.unconf_file()
            rows.append(r)
        return rows

    def load_closed(self) -> list[dict]:
        rows = []
        for f in self.closed_shards():
            for r in read_jsonl(f):
                r["_slot"] = "closed"
                r["_file"] = f
                rows.append(r)
        return rows

    def all_ids(self) -> list[str]:
        ids = [r["id"] for r in self.load_live() if "id" in r]
        ids += [r["id"] for r in self.load_closed() if "id" in r]
        for f in sorted(self.decisions_dir().glob("*.md")) if self.decisions_dir().is_dir() else []:
            ids.append(f.stem)
        return ids

    def allocate(self, typ: str) -> str:
        mx = 0
        for i in self.all_ids() + _void_ids(self):   # 已作废 id 不复用
            m = ID_RE.match(i)
            if m and m.group(1) == typ:
                mx = max(mx, int(m.group(2)))
        return f"{typ}{mx + 1:06d}"

    def next_id(self) -> str:
        p = self.d / "next"
        if not p.is_file():
            return ""
        line = p.read_text(encoding="utf-8").strip()
        return line

    def set_next(self, value: str):
        self.d.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.d))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(value + "\n" if value else "")
        os.replace(tmp, self.d / "next")

    # ---- index ----
    def build_index(self) -> dict:
        slots: dict = {}
        domains: dict = {}
        topics: dict = {}
        for slot in ENTRY_SLOTS:
            files = []
            total = 0
            sd = self.d / slot
            if sd.is_dir():
                for f in sorted(sd.glob("*.jsonl")):
                    n = len(read_jsonl(f))
                    total += n
                    part = f.stem
                    files.append({"file": f"{slot}/{f.name}", "partition": part, "count": n})
                    if slot in ("actions", "pitfalls"):
                        domains.setdefault(part, []).append(f"{slot}/{f.name}")
            slots[slot] = {"count": total, "files": files}
        uc = read_jsonl(self.unconf_file())
        slots["unconfirmed"] = {"count": len(uc), "files": ["unconfirmed.jsonl"] if self.unconf_file().is_file() else []}
        dc = sorted(self.decisions_dir().glob("*.md")) if self.decisions_dir().is_dir() else []
        slots["decisions"] = {"count": len(dc), "files": [f"decisions/{p.name}" for p in dc]}
        for r in self.load_live():
            t = r.get("topic")
            if t:
                topics.setdefault(t, []).append(str(r.get("_file")))
        return {
            "schema": 1,
            "generated": today(),
            "slots": slots,
            "domains": domains,
            "topics": {k: sorted(set(v)) for k, v in topics.items()},
            "closed_count": len(self.load_closed()),
            "next": self.next_id(),
        }

    def note_pre_tamper(self) -> None:
        """写命令**开始时**取一次旁证快照（同一命令内只算一次）。

        为什么不能放在 `write_index` 里算：`set`/`add`/`edit` 的写序是「先写内容、
        后 write_index」，那时文件 mtime 已经被**本次自己的写**更新了——于是每次
        经这些命令写 `status`/`exit` 都会被自己的 pre_tamper 判据误报（真源实测：
        连我自己用 `set exit` 回填一次都被报成「未经 CLI 之外改动过」）。
        """
        if self._pre_tamper is None:
            self._pre_tamper = _tamper_since_last_write(self, self._write_targets())

    def _removed_since_last_write(self) -> list:
        """本 Store 生命周期内、写事件记过但**现已不存在**的文件。

        4.8.1 之前这里是死红：`edit --domain` 换分区会「搬空即删」旧分区文件（4.7.5 的
        刻意修复），而 `audit_writes` 把「latest 里有、落盘没有」一律判成「疑似被 CLI
        之外的途径删掉」⇒ 每次换分区后 `check` 永久红，且 `rebase` 也解不开（它同样保留
        `latest`）。根治：**写事件要记「谁删的」**，对账时才分得清「经 CLI 正常删掉」与
        「凭空消失」。
        """
        wl = self.d / WRITES_LOG
        if not wl.is_file():
            return []
        seen: set[str] = set()
        for e in read_jsonl(wl):
            seen |= set(e.get("files") or {})
            seen |= set(e.get("removed") or [])
        return sorted(f for f in seen if not (self.d / f).exists())

    def write_index(self, op: str | None = None):
        # **不要在这里取快照**：调用点都在「内容已写完之后」，那时 mtime 已被本次
        # 自己的写更新 ⇒ 每次经 set/add/edit 写 status/exit 都被自己的判据误报
        # （第一版修法把「每次算」改成「每实例算一次」，时机仍是写后，等于没修；
        #   真源 check 报红才暴露）。写命令须在**第一行**调 note_pre_tamper()。
        pre_tamper = self._pre_tamper or []
        idx = self.build_index()
        p = self.d / "index"
        fd, tmp = tempfile.mkstemp(dir=str(self.d))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, p)
        # 写事件记在**索引重建之后**——所有写路径最后都过这里，集中记才不会漏。
        log_write(self, op or "write_index", self._write_targets(), pre_tamper,
                  removed=self._removed_since_last_write())

    def _write_targets(self) -> list:
        """本次落盘的全部受管文件（分区 jsonl/md ＋ 四个单文件槽）。"""
        out = []
        for slot in ENTRY_SLOTS:
            d = self.d / slot
            if d.is_dir():
                out += sorted(d.glob("*.jsonl"))
                out += sorted(d.glob("*.md"))
        for s in SINGLES:
            f = self.d / s
            if f.is_file():
                out.append(f)
        uf = self.unconf_file()            # unconfirmed.jsonl 也要进对账面
        if uf.is_file():
            out.append(uf)
        cl = self.d / "closed"
        if cl.is_dir():
            out += sorted(cl.glob("*.jsonl"))
        return out


# ---------------- init ----------------
def cmd_init(st: Store, a) -> int:
    if (st.d / "index").is_file() and not a.force:
        die(f"init: {st.d} 已存在（--force 重建骨架）")
    st.d.mkdir(parents=True, exist_ok=True)
    for s in SINGLES:
        if not (st.d / s).is_file():
            (st.d / s).write_text(SCOPE_HEADER if s == "scope" else "", encoding="utf-8")
    for slot in ENTRY_SLOTS:
        (st.d / slot).mkdir(parents=True, exist_ok=True)
    st.decisions_dir().mkdir(parents=True, exist_ok=True)
    (st.d / "closed").mkdir(parents=True, exist_ok=True)
    if not st.unconf_file().is_file():
        st.unconf_file().write_text("", encoding="utf-8")
    if not (st.d / "next").is_file():
        st.set_next("")
    if not (st.d / "log.jsonl").is_file():
        (st.d / "log.jsonl").write_text("", encoding="utf-8")
    st.write_index()
    print(f"handoff init: 已建骨架 {st.d}/（9 槽 + index）")
    # 顺手把标准交接块装进**本项目**的 AGENTS.md——写入是使用方自己的动作，不是
    # 库维护者跨仓代劳。init 是用户显式启用交接的那一刻，也就是最自然的安装时机。
    # 不阻断 init：AGENTS.md 不存在就跳过（此时无法装块）；存在则一律装上——
    # 已有 `## 交接` 节的走整理覆盖，不需要人先手工并入标记区。
    repo = st.d.parent
    agents = repo / "AGENTS.md"
    if agents.is_file():
        class _A:  # 复用 --install 的落盘逻辑，不走 argparse
            install = str(repo)
            profile = "basic"
            print_only = False
            check = None
        rc = cmd_agents_block(st, _A())
        if rc != 0:
            print("  提示：交接块未自动写入（见上），修好后再跑一次 "
                  "`handoff.py agents-block --install .` 即可。")
    else:
        print(f"  提示：{agents} 不存在，跳过交接块安装；建好 AGENTS.md 后跑 "
              "`handoff.py agents-block --install .`")
    return 0


# ---------------- log（使用数据，供日后优化/裁剪槽位） ----------------
def _log_path(st: Store) -> Path:
    return st.d / "log.jsonl"


def _sha(text: str) -> str:
    """内容哈希（不是 mtime——mtime 可 `touch -d` 伪造，一戳就破）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


WRITES_LOG = "writes.jsonl"


def _tamper_since_last_write(st: Store, targets) -> list:
    """写**之前**的旁证检查：这些文件的 mtime 与上次写事件记录的不一致
    ⇒ 上次 CLI 写之后有人动过它们（哪怕内容最终写回一样 —— 那正是补手续）。"""
    wl = st.d / WRITES_LOG
    if not wl.is_file():
        return []
    evs = read_jsonl(wl)
    if not evs:
        return []
    last: dict[str, dict] = {}
    for e in evs:
        for f, rec in (e.get("files") or {}).items():
            last[f] = rec if isinstance(rec, dict) else {"sha": rec, "mt": None}
    out = []
    for t in targets:
        t = Path(t)
        if not t.is_file():
            continue
        rel = str(t.relative_to(st.d))
        rec = last.get(rel)
        if rec and rec.get("mt") is not None and t.stat().st_mtime_ns > rec["mt"]:
            out.append(rel)
    return out


def log_write(st: Store, op: str, targets, pre_tamper=None, removed=None) -> None:
    """每次 CLI **写**都记一条 append-only 事件（p000025 的判据面，4.7.8）。

    记 `op` ＋ 每个受影响文件的**写后内容哈希**。它让两件原本「钉不进判据」的事变成
    可判定：
      · 有人绕过 CLI 手改文件 ⇒ `check` 重算当前文件哈希，与最后一条写事件对不上
        ⇒ **存在未经 CLI 记录的写入**（含「改了又改回」以外的一切痕迹）。
      · 「补手续」（先手改、再用 CLI 覆写同样字节）⇒ 同一 target 出现**内容哈希相同、
        紧邻相邻**的两条写事件 ⇒ 疑似补手续（真去做了同一件事两次）。
    判据输入全是落盘证据。时间戳用 **`st_mtime_ns`（纳秒）**而非 `int(st_mtime)`：
    秒级取整会把同一秒内的多次写压成同一个值，判据当场失效（第一版就这么全绿的）。
    best-effort：日志写失败不阻断业务写（否则日志成了新的单点）。
    """
    try:
        if not (st.d / "index").is_file():        # 同 _log：非库不落盘
            return
        ev = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"),
              "op": op,
              "pre_tamper": sorted(pre_tamper or []),
              "removed": sorted(removed or []),
              "files": {str(Path(t).relative_to(st.d)): {
                            "sha": _sha(Path(t).read_text(encoding="utf-8")),
                            "mt": Path(t).stat().st_mtime_ns}
                        for t in targets if Path(t).is_file()}}
        with open(st.d / WRITES_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


def audit_writes(st: Store) -> list[str]:
    """对账写事件与落盘现实（`check` 的一维，p000025）。

    两条判据，**都以内容哈希为主、mtime 为辅**：
      · **内容哈希对不上** ⇒ 存在**未经 CLI 记录的写入**（手改文件；`writes.jsonl`
        只记 CLI 写，手改不留痕）。
      · **内容哈希相同、但 mtime 更新了** ⇒ 文件**被动过又写回同样内容**——这正是
        「先手改、再用 CLI 覆写同样字节来补手续」的指纹。CLI 侧看不见那次手改的
        内容，但它**动了文件**，时间戳留下了。
    为什么不用纯 mtime 判「有没有被改」：mtime 可 `touch -d` 伪造。所以哈希是主判据、
    mtime 只在**哈希相同**时作旁证（那种情况本来就没内容差异可判）。
    """
    wl = st.d / WRITES_LOG
    if not wl.is_file():
        return []
    evs = read_jsonl(wl)
    if not evs:
        return []
    latest: dict[str, dict] = {}
    problems: list[str] = []
    for e in evs:
        for f, rec in (e.get("files") or {}).items():
            if isinstance(rec, str):          # 兼容旧格式（纯 sha）
                rec = {"sha": rec, "mt": None}
            latest[f] = rec
    ever_removed: set = set()
    for e in evs:
        ever_removed |= set(e.get("removed") or [])
    seen_tamper: set = set()
    for e in evs:
        for f in (e.get("pre_tamper") or []):
            if f not in seen_tamper:
                seen_tamper.add(f)
                problems.append(
                    f"{f}：在 {e.get('op')} 写入**之前**发现它已被 CLI 之外改动过"
                    f"（内容哈希可能仍与记录一致）——若是先手改文件、再用 CLI 覆写同样"
                    f"字节来「补手续」，那次手改的时间窗已无法追回")
    for f, rec in latest.items():
        p = st.d / f
        if not p.is_file():
            # 区分两种「不在了」：**经 CLI 正常删掉**（如 edit 换分区的「搬空即删」，
            # 4.7.5）不报；**凭空消失**（没有任何写事件记录过删它）才报。
            if f in ever_removed:
                continue
            problems.append(f"{f}：写事件记过它，现已不存在，且**没有任何 CLI 记录删过它**"
                            f"（疑似被 CLI 之外的途径删掉）")
            continue
        now_sha = _sha(p.read_text(encoding="utf-8"))
        if now_sha != rec.get("sha"):
            problems.append(
                f"{f}：内容哈希 {rec.get('sha')} ≠ 落盘实际 {now_sha} —— 存在"
                f"**未经 CLI 记录的写入**（`writes.jsonl` 只记 CLI 写；手改文件不留痕）")
        elif rec.get("mt") is not None and p.stat().st_mtime_ns > rec["mt"]:
            problems.append(
                f"{f}：内容**没变**（哈希同为 {now_sha}）但文件被改动过（mtime 更新）——"
                f"疑似「先手改、再用 CLI 覆写同样字节」的补手续；那次手改的时间窗已无法追回")
    return problems


def _log(st: Store, event: str, **extra):
    """每次门禁落一条快照（best-effort，不因日志失败中断）。

    `extra` 用来挂事件专属字段（如 `close` 事件带被关 id 与 outcome）——快照的槽位
    计数部分对所有事件相同，事件本身只多一行语义。

    副作用边界：`--store` 指到**不是库**的目录时不落 log——`open(..., "a")` 会凭空建出文件，
    那等于让只读命令在任意路径写脏（实测：`handoff --store . check` 曾在仓库根造出 log.jsonl）。
    判据用 `index` 是否存在（init / import 都先写它），无 index＝不是库。
    """
    try:
        if not (st.d / "index").is_file():
            return
        live = st.load_live()
        slots = {s: len([r for r in live if r.get("_slot") == s]) for s in ENTRY_SLOTS}
        slots["unconfirmed"] = len(read_jsonl(st.unconf_file()))
        slots["decisions"] = len(list(st.decisions_dir().glob("*.md"))) if st.decisions_dir().is_dir() else 0
        slots["closed"] = len(st.load_closed())
        rec = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"),
               "event": event, "slots": slots,
               "commands_empty": slots.get("commands", 0) == 0}
        rec.update(extra)
        with open(_log_path(st), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        pass


def cmd_log(st: Store, a) -> int:
    p = _log_path(st)
    if not p.is_file():
        print("handoff log: （无日志）")
        return 0
    rows = read_jsonl(p)
    if a.stats:
        n = len(rows)
        ce = sum(1 for r in rows if r.get("commands_empty"))
        tot: dict[str, int] = {}
        for r in rows:
            for k, v in (r.get("slots") or {}).items():
                tot[k] = tot.get(k, 0) + int(v)
        print(f"runs={n}  commands_empty={ce}  commands_nonempty={n - ce}  last={rows[-1].get('ts','') if rows else ''}")
        print("sum(slots): " + json.dumps(tot, ensure_ascii=False))
        return 0
    tail = rows[-a.tail:] if a.tail else rows
    for r in tail:
        print(json.dumps(r, ensure_ascii=False))
    return 0


# ---------------- check ----------------
# ── `check` 判据清单：**唯一产生源**（2026-10-03 单源化试点）──
# 同一事实（有哪些判据）此前被复述在两处：`cmd_check` 的代码段 与 `SKILL.md` 正文的
# 判据清单 —— 加一条判据要改两处，本会话已因此反复「只改了一半」（正文与实现分叉）。
# 现在：**这一张表是唯一源**，`SKILL.md` 的清单由 `sync-dims` 从它生成，
# `selftest` 里有一条漂移检查兜住（生成物与源不同步即红）。
# 加判据时**只改这里**，然后跑 `handoff.py sync-dims` 写回生成块（可 `--check` 只验不写）。
CHECK_DIMENSIONS: list[tuple[str, str]] = [
    ("slots", "9 槽与 `index` 齐备（status/summary/scope/exit ＋ 四目录 ＋ unconfirmed）"),
    ("id", "id 形如 `<t|p|d|c|u><6 位>`、全局唯一、**前缀与所在槽相符**"),
    ("status", "live 行的 `status` 在该型闭集内（**`closed` 不是可写值**，关闭只经 `close`）"),
    ("fields", "未知字段 ＋ 必填字段缺失（按型）"),
    ("dates", "`created`/`closed` 是合法日期、非未来日、且 `created ≤ closed ≤ today`"),
    ("single-line", "`summary` 单行（不得含换行/制表）"),
    ("next", "`next` 是合法 id、存在、且 **`status=open`**（附可执行修法）"),
    ("text-dangling", "文本槽（`status`/`summary`/`exit`）点名的 `t/p/q/u` 型 id 必须既不在册、"
                      "也不在 `trash/`·`void` 之外（**已作废 ≠ 不存在**；`c`/`d` 两型不参与，"
                      "各有专门检查面）"),
    ("decision", "`decisions/*.md` 的 frontmatter id 必须等于文件名、日期合法、status 在闭集"),
    ("scope", "`scope` 登记指向**活路径**或 glob 有命中（机械判据：登记必须可解析）"),
    ("void-reuse", "id 未复用已作废 id（`void` 拦截）"),
    ("writes", "写事件对账：内容哈希对不上＝**未经 CLI 记录的写入**；写前发现被外部动过＝"
               "**疑似补手续**（含判据缺陷留下的历史误报，用 `rebase --force` 结案）"),
    ("partition-case", "同槽分区文件名**大小写折叠后不得重名**（NTFS 大小写不敏感 ⇒ 仅大小写"
                       "不同的两个 domain 会合并成一个分区文件、计数与现实脱节）"),
    ("index", "`index` 的各槽计数与 `next` 与落盘一致（漂移即红）"),
    ("fresh-queue", "**交接新鲜度**：仍 open 的 `t` 型条目必须在 `exit`/`summary` 里出现"
                    "（抓「新条目进队列、exit 沉默」；只取 `t` 型——p/d 进 exit 属背景叙述，"
                    "逐条要求提及会淹没真信号）"),
    ("fresh-stale", "**陈旧陈述**：`exit` 里提及**已闭**条目的那一行必须带显式关闭标记"
                    "（抓「把已闭说成候立」；**只查 exit 不查 summary**——summary 是流水式"
                    "摘要、逐条列已闭 id 是它的本职，强求标记产出纯噪声）"),
]
CHECK_BEGIN = "<!-- check-dims:begin （由 CHECK_DIMENSIONS 生成，勿手改）-->"
CHECK_END = "<!-- check-dims:end -->"


def render_check_dims() -> str:
    """判据清单的 Markdown 生成物（`SKILL.md` 与任何文档都从它派生）。"""
    lines = [CHECK_BEGIN, ""]
    lines += [f"{i}. **{d[0]}** — {d[1]}" for i, d in enumerate(CHECK_DIMENSIONS, 1)]
    lines += ["", CHECK_END]
    return "\n".join(lines)


def cmd_sync_dims(check_only: bool = False) -> int:
    """把 `CHECK_DIMENSIONS` 生成的判据清单写回 SKILL.md（`--check` 只验不写）。"""
    md = Path(__file__).resolve().parent.parent / "SKILL.md"
    try:
        text = md.read_text(encoding="utf-8")
    except OSError as e:
        print(f"sync-dims: 读不到 {md}: {e}", file=sys.stderr)
        return 2
    block = render_check_dims()
    if CHECK_BEGIN not in text or CHECK_END not in text:
        print(f"sync-dims: FAIL（{md.name} 缺判据清单生成块——"
              f"把下面这段插到「check ＝ 相位门禁」那段末尾）", file=sys.stderr)
        print(block, file=sys.stderr)
        return 1
    cur = text.split(CHECK_BEGIN, 1)[1].split(CHECK_END, 1)[0]
    new = text.split(CHECK_BEGIN, 1)[0] + block + text.split(CHECK_END, 1)[1]
    if cur.strip() == block.split(CHECK_BEGIN, 1)[1].split(CHECK_END, 1)[0].strip():
        print("sync-dims: OK（生成块已是最新）")
        return 0
    if check_only:
        print(f"sync-dims: FAIL（{md.name} 生成块与 CHECK_DIMENSIONS 不同步——"
              f"跑一次 `handoff.py sync-dims` 写回）", file=sys.stderr)
        return 1
    md.write_text(new, encoding="utf-8")
    print(f"sync-dims: 已写回 {md.name} 的判据清单生成块")
    return 0


def cmd_check(st: Store, no_log: bool = False) -> int:
    errs: list[str] = []
    # 9 槽存在性
    for s in SINGLES:
        if not (st.d / s).is_file():
            errs.append(f"缺槽: {s}")
    for slot in ENTRY_SLOTS:
        if not (st.d / slot).is_dir():
            errs.append(f"缺槽目录: {slot}/")
    if not st.unconf_file().is_file():
        errs.append("缺槽: unconfirmed.jsonl")
    if not st.decisions_dir().is_dir():
        errs.append("缺槽目录: decisions/")
    if not (st.d / "closed").is_dir():
        errs.append("缺槽目录: closed/")
    if not (st.d / "index").is_file():
        errs.append("缺 index（跑 handoff index 生成）")

    # 条目校验
    seen: dict[str, str] = {}
    live = st.load_live() + st.load_closed()
    for r in live:
        loc = f"{r.get('_file')}"
        i = r.get("id", "")
        m = ID_RE.match(i)
        if not m:
            errs.append(f"{loc}: 非法 id {i!r}（应 <t|p|d|c|u><6 位>）")
            continue
        typ = m.group(1)
        if i in seen:
            errs.append(f"{loc}: id 重复 {i}（已见 {seen[i]}）")
        seen[i] = loc
        # 槽 ↔ 类型
        if r.get("_slot") in ENTRY_SLOTS:
            want = ENTRY_SLOTS[r["_slot"]]["type"]
            if typ != want:
                errs.append(f"{loc}: id 前缀 {typ} 与槽 {r['_slot']} 不符（应 {want}）")
        elif r.get("_slot") == "unconfirmed" and typ != "u":
            errs.append(f"{loc}: unconfirmed 内 id 前缀应为 u，得 {typ}")
        elif r.get("_slot") == "closed":
            stem = Path(str(r.get("_file"))).stem
            if re.fullmatch(r"[tpducq]", stem) and typ != stem:
                errs.append(f"{loc}: closed 文件 {stem}.jsonl 与 id 前缀 {typ} 不符")
        knd = SLOT2KIND.get(r.get("_slot")) if r.get("_slot") in ENTRY_SLOTS else None
        if knd and (r.get("status") or "open") not in live_status_of(knd):
            errs.append(f"{loc}: status 非法 {r.get('status')!r}"
                        f"（该型合法 {sorted(live_status_of(knd))}；closed 须经 close 流程）")
        for k in r:
            if k in ("_slot", "_file"):
                continue
            if k not in ALLOWED_KEYS:
                errs.append(f"{loc}: 未知字段 {k!r}")
        if r.get("_slot") != "closed":
            for req in ("id", "created", "summary"):
                if not r.get(req):
                    errs.append(f"{loc}: 缺必填 {req}")
        cr = r.get("created", "")
        if cr and not DATE_RE.match(cr):
            errs.append(f"{loc}: created 非日期 {cr!r}")
        if cr and cr > today():
            errs.append(f"{loc}: created 为未来日 {cr}")
        cl = r.get("closed")
        if cl is not None:
            if not DATE_RE.match(str(cl)):
                errs.append(f"{loc}: closed 非日期 {cl!r}")
            elif cl > today():
                errs.append(f"{loc}: closed 为未来日 {cl}")
            elif cr and cl < cr:
                errs.append(f"{loc}: closed < created（{cl} < {cr}）")
        if "\n" in r.get("summary", "") or "\t" in r.get("summary", ""):
            errs.append(f"{loc}: summary 含换行/制表（须单行）")

    # next 指针
    nid = st.next_id()
    if nid:
        if not ID_RE.match(nid):
            errs.append(f"next: 非法 id {nid!r}")
        else:
            live_recs = {r["id"]: r for r in st.load_live() if "id" in r}
            if nid not in live_recs:
                errs.append(f"next: {nid} 不存在或已关闭"
                            f"\n      修（一条命令即可）：handoff next --auto")
            elif (live_recs[nid].get("status") or "open") != "open":
                # 存在但不是 open：blocked/等待中的条目当决策点＝空指针。调用方
                # （接手的人或 agent）照着 next 走会立刻卡住，而结构上看不出问题。
                errs.append(f"next: {nid} 的 status="
                            f"{live_recs[nid].get('status') or 'open'!r}，不是 open"
                            f"（等待中的条目不该当决策点）\n"
                            f"      修（一条命令即可）：handoff next --auto")

    # 文本槽死指针（D1，2026-10-03）：文本槽是纯手写散文，条目删了/改号了它不会
    # 自己跟着变。结构校验看不出这类漂移——槽文件存在、id 合法、引用闭合，全都对。
    # id 不随时间失效，所以这一维可**全量**判。**但不是「无假阳性」**——判据只覆盖
    # 下面 ② 点名的那几型；**被排除的类型不因此变成「没问题」，只是另有检查面**。
    #
    # **两个刻意的收窄**（都是被真文本逼出来的，不是预防性设计）：
    #  ① **已作废 ≠ 不存在**。`rm` 会把条目落进 `trash/` 并记入 `void`；此后文本里
    #     写「t000105 作废」是**正当的历史陈述**（真源实测共 6 处：`status` 3 ＋ `summary` 1 ＋ `exit` 2），
    #     判它死指针就是逼着人把正确记录改掉。故作废 id 不计。
    #  ② **`c` 与 `d` 两型不参与本维**（2026-10-03 用户裁定，原只排 `c`）。
    #     理由写准（此处前两版都写错过，故把推演留下）：
    #       · 判据用的模式是 `\b([tpqu]\d{6})\b`（**d 已从字符类里去掉**），
    #         长度**恒为 7 字符** ⇒ 6 字符的 git 短 hash 长度不足、**永不匹配**。
    #       · `c697750`（7 字符）也不匹配，原因是 **`c` 根本不在字符类**——排除它
    #         之后这条恒成立，与词边界无关。
    #       · 字符类 `tpdqu` 里**只有 `d` 是 hex 字符**。故 `d` 型与 7 字符全 hex 的
    #         commit 短 hash（如 `d697750`）**形态不可区分**，且**实测可复现**：把
    #         这种 hash 写进文本槽，`check` 立刻 rc=1 把它判成死指针。
    #     所以排除的其实是 **`d`**（够得着的那个），`c` 排除只是顺带的零成本项。
    #     **收窄不是放弃检查**：「`d` 型 id 查不到」这件事有专门且语义正确的检查面
    #     —— `view --id dNNNNNN`：**已作废**的 id 打印「已作废」并 rc=0（与本闸
    #     「已作废 ≠ 不存在」同口径），**真正查不到**才 rc=2 并明说「live / closed /
    #     decisions 均无，且不在 trash/·void」；`check` 另有一条判 `decisions/<file>`
    #     的 frontmatter id 必须等于文件名（抓改号）。分工已实测：把 d000001.md
    #     改名 → view 仍按 frontmatter id 命中（rc=0）而 check 立刻 rc=1 报
    #     「frontmatter id 与文件名不符」；把文件移走 → view rc=2；只把文件挪进
    #     `trash/` 不记 `void` → 两边都认「已作废」。**交给语义正确的命令，别靠
    #     形态猜。**
    voided = _voided_ids(st)          # 单源：void ∪ trash/（见 _voided_ids）
    known_ids = set(st.all_ids()) | voided
    for s in ("status", "summary", "exit"):
        sp = st.d / s
        if not sp.is_file():
            continue
        for ref in sorted(set(re.findall(r"\b([tpqu]\d{6})\b", sp.read_text(encoding="utf-8")))):
            if ref not in known_ids:
                errs.append(f"{s}: 提到 {ref}，但 live∪closed∪decisions 里没有这个 id"
                            f"（既不在册、也不在 trash/void——条目被删或改号了，文本不会自己跟着变）")

    # 决策文档校验
    if st.decisions_dir().is_dir():
        for f in sorted(st.decisions_dir().glob("*.md")):
            fm = _frontmatter(f)
            if fm.get("id") != f.stem:
                errs.append(f"decisions/{f.name}: frontmatter id {fm.get('id')!r} 与文件名 {f.stem!r} 不符")
            if not DATE_RE.match(fm.get("created", "")):
                errs.append(f"decisions/{f.name}: created 缺或非日期")
            if fm.get("status") and fm["status"] not in ("proposed", "accepted", "deprecated", "superseded", "rejected"):
                errs.append(f"decisions/{f.name}: status 非法 {fm['status']!r}")

    # 源登记表可解析（机械判据：登记必须指向活路径 / glob 有命中）
    for e in _scope_lines(st):
        if not _scope_resolves(st, e):
            errs.append(f"scope 登记不可解析：{e}（路径不存在 / glob 无命中）")
    void = set(_void_ids(st))
    for i in st.all_ids():
        if i in void:
            errs.append(f"id 复用了已作废 id：{i}")

    # 写事件对账（p000025，4.7.8）：把「绕过 CLI 手改文件」与「补手续」从纪律变成判据。
    for _w in audit_writes(st):
        errs.append(_w)

    # 分区文件名**大小写折叠后重名**（2026-10-03，Windows 实测带出的真问题）：
    # NTFS 大小写**不敏感** —— 实测同时创建 `Case.jsonl` 与 `case.jsonl`，目录枚举
    # **只得到 1 个文件**。所以仅大小写不同的两个 domain，在 Windows 上会**合并成一个
    # 分区文件**：index 计数少一条、两条目挤进同一文件 ⇒ 正是 p000046 那个「index 与现实
    # 不符、check 却报 OK」的形态。**这条在 Linux 上也判**（折叠后重名是纯粹的命名冲突），
    # 因为它是**平台无关的前提**——在 Linux 上它无害，在 Windows 上它丢数据。
    for slot in ENTRY_SLOTS:
        d = st.d / slot
        if not d.is_dir():
            continue
        seen: dict[str, str] = {}
        for f in sorted(d.glob("*.jsonl")):
            key = f.name.lower()
            if key in seen:
                errs.append(
                    f"{slot}/{f.name} 与 {seen[key]} 仅大小写不同：Windows/NTFS 大小写不敏感，"
                    f"两者会合并成同一个分区文件（实测枚举只得 1 个）⇒ 改其中一个的 domain")
            else:
                seen[key] = f.name

    # index 一致性
    if (st.d / "index").is_file():
        try:
            idx = json.loads((st.d / "index").read_text(encoding="utf-8"))
            for slot in ENTRY_SLOTS:
                want = len([r for r in st.load_live() if r.get("_slot") == slot])
                got = idx.get("slots", {}).get(slot, {}).get("count")
                if got != want:
                    errs.append(f"index 漂移: {slot} 计数 表={got} 实={want}")
            want_uc = len(read_jsonl(st.unconf_file()))
            got_uc = idx.get("slots", {}).get("unconfirmed", {}).get("count")
            if got_uc != want_uc:
                errs.append(f"index 漂移: unconfirmed 计数 表={got_uc} 实={want_uc}")
            want_nx, got_nx = st.next_id(), idx.get("next")
            if got_nx != want_nx:
                errs.append(f"index 漂移: next 表={got_nx!r} 实={want_nx!r}（跑 handoff index 重建）")
        except json.JSONDecodeError:
            errs.append("index 非法 JSON")

    # ── 交接陈述新鲜度（2026-10-03 下沉自本仓 scripts/handoff-freshness-check.py）──
    # 下面两条此前是**库专属脚本**，判的却是每个使用方都需要的交接纪律，形态错了：
    # 消费方是技能使用者，判据就该随技能分发（AGENTS 规则 16）。下沉后兄弟仓跑
    # `handoff check` 同样受益。
    #
    # 事实面：`closed` 槽给出「哪些已闭、哪天闭的」；`actions` ∪ `closed` 减去已闭
    # 就是「仍 open 的队列」。**只取 `t` 型**（待办）：p* 是坑、d* 是决定，进 exit 属
    # 背景叙述，池里常有上百条 open，逐条要求 exit 提及既不现实也会淹没真信号。
    _closed: dict[str, str] = {}
    for _f in sorted((st.d / "closed").glob("*.jsonl")):
        for _r in read_jsonl(_f):
            if _r.get("id") and _r.get("closed"):
                _closed[_r["id"]] = str(_r["closed"])
    _open_ids: set[str] = set()
    for _slot in ENTRY_SLOTS:
        for _f in sorted((st.d / _slot).glob("*.jsonl")):
            for _r in read_jsonl(_f):
                _rid = _r.get("id")
                if rid_re_match(_rid) and _rid[0] == "t":
                    _open_ids.add(_rid)
    _open_ids -= set(_closed)

    def _slot_text(sl: str) -> str:
        p = st.d / sl
        return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""

    _exit_txt, _summary_txt = _slot_text("exit"), _slot_text("summary")

    # fresh-queue：仍 open 的条目必须在 exit/summary 里出现（抓「新条目进队列、exit 沉默」）
    _blob = "\n".join((_exit_txt, _summary_txt))
    _mentioned = set(FIND_ID_RE.findall(_blob)) if FIND_ID_RE else set()
    _silent = sorted(_open_ids - _mentioned)
    if _silent:
        errs.append(
            f"fresh-queue：{len(_silent)} 条仍 open 的条目在 exit/summary 里没出现（exit 沉默）："
            f"{_silent[:8]}{'…' if len(_silent) > 8 else ''}"
            f"　修：过 `handoff set exit` 回写队列段（整槽覆写，先 --dry-run）")

    # fresh-stale：exit 里提及**已闭**条目时，同一行必须带显式关闭标记
    # （抓「把已闭条目说成候立/未闭」）。**只查 exit、不查 summary** —— summary 是
    # 流水式摘要、逐条列已闭 id 是它的本职，强求标记会产出大量纯噪声。
    _stale: list[str] = []
    for _i, _line in enumerate(_exit_txt.splitlines(), 1):
        for _rid in FIND_ID_RE.findall(_line):
            if _rid in _closed and not any(_mk in _line for _mk in CLOSED_MARKERS):
                _stale.append(f"exit:{_i} {_rid}（closed={_closed[_rid]}）该行无关闭标记")
    if _stale:
        errs.append(
            f"fresh-stale：{len(_stale)} 处提及已闭条目却无关闭标记（已闭写成未闭/候立）→ "
            f"{_stale[:6]}{'…' if len(_stale) > 6 else ''}"
            f"　修：写 `t000095（已闭）` 这类显式标记（见 AGENTS 交接块纪律）")

    if errs:
        print(f"handoff check: FAIL（{len(errs)} 处）")
        for e in errs:
            print(f"  - {e}")
        if not no_log:
            _log(st, "check:fail")
        return 1
    if not store_has_entries(st):
        print("handoff check: 提示：无任何条目——新项目正常；若刚迁移，通常意味着清单未成功导入", file=sys.stderr)
    print("handoff check: OK")
    if not no_log:
        _log(st, "check:ok")
    return 0


# ---------------- write ----------------
def cmd_add(st: Store, kind: str, f: dict) -> int:
    """按**型**登记条目。`f` 的键集＝该型子命令声明的 flag（两侧同源，见 ADD_KINDS）。

    旧 `cmd_add(st, a)` 收整个 Namespace ＋ `--slot` 分流，是「参数并集 ⊃ 消费子集」的成因；
    现签名收显式 dict，未消费的键在结构上不可能出现，且真出现（改了声明忘了改这里）由下方
    drift 守卫当场报错——**静默丢弃在本 CLI 里不再是可达状态**。
    """
    st.note_pre_tamper()          # 写前旁证快照（本次写自己的 mtime 变化不算外部改动）
    spec = ADD_KINDS[kind]
    slot, part_key = spec["slot"], spec["part"]
    consumed = ({"title", "body", "status", "supersedes", "domain", "topic"} if slot == DOC_SLOT
                else {"summary", "status", "blockedBy", "topic", "src", "detail", part_key})
    ff_keys: set = set()
    ff = f.pop("_from_file", None)
    if ff:
        got = load_from_file(f"add {kind}", ff, set(consumed))
        # 同一字段同时给了 flag 与文件：**报错**，不静默取一个（静默丢弃是老病）。
        # 只比**真正给了值**的 flag —— `{k: v for k in fields}` 里键恒存在、值常为 None，
        # 直接比键集会把「没传的」全判成冲突。
        dup = sorted({k for k, v in f.items() if v is not None} & set(got))
        if dup:
            die(f"add {kind}: 字段 {dup} 同时出现在命令行与 --from-file；只留一处")
        f.update(got)
        ff_keys = set(got)
    for k in sorted(consumed):
        require_text(f"add {kind}", f"--{k}", f.get(k),
                     from_shell=k not in (ff_keys if ff else set()))
    if slot == DOC_SLOT:
        if not f.get("title"):
            die("add decision: 需要 --title")
        did = st.allocate("d")
        st.decisions_dir().mkdir(parents=True, exist_ok=True)
        text = f"---\nid: {did}\ncreated: {today()}\nstatus: {f.get('status') or 'accepted'}\n"
        for k in ("supersedes", "domain", "topic"):
            if f.get(k):
                text += f"{k}: {f[k]}\n"
        text += f"---\n# {f['title']}\n\n{f.get('body') or ''}\n"
        (st.decisions_dir() / f"{did}.md").write_text(text, encoding="utf-8")
        new_id = did
    else:
        if not f.get("summary"):
            die(f"add {kind}: 需要 --summary")
        guard_status(kind, f.get("status"))
        e = {"id": st.allocate(ENTRY_SLOTS[slot]["type"]), "created": today(),
             "summary": norm(f["summary"])}
        for k in ("status", "blockedBy", "topic", "src", "detail"):
            if f.get(k) is not None:
                e[k] = f[k]
        part = guard_partition(f"add {kind}", part_key, f.get(part_key))
        append_jsonl(st.d / slot / f"{part}.jsonl", e)
        new_id = e["id"]
    if drift := set(f) - consumed:
        die(f"内部不一致：add {kind} 声明了 {sorted(drift)} 却无人消费（补 ADD_KINDS 或消费分支）")
    st.write_index()
    print(f"handoff add {kind}: ok（slot={slot}） id={new_id}")
    echo_back(st, new_id)
    return 0


def _find_live(st: Store, id_: str):
    for r in st.load_live():
        if r.get("id") == id_:
            return r
    return None


# ---------------- next 自动补位（refill） ----------------
REFILL_STEP_DAYS = 30                      # 时间维：每满 30 天升一档
PRIO_RE = re.compile(r"^\s*[\[【]\s*(高|中|低|high|med|medium|mid|low)\s*[\]】]", re.I)
PRIO_BASE = {"高": 0, "high": 0, "中": 1, "med": 1, "medium": 1, "mid": 1, "低": 2, "low": 2}


def _age_days(created: str) -> int:
    if not DATE_RE.match(created or ""):
        return 0
    try:
        return max(0, (date.today() - date.fromisoformat(created)).days)
    except ValueError:
        return 0


def refill_pool(st: Store, exclude: str = ""):
    """补位池 = live actions（status 非 live 闭集者一律排除）。返回 (有序候选, 池大小, 排除数)。

    排序键全序确定：(有效档, created↑, id↑)。有效档 = 基础档 − 超期升档数（下限 0）；
    基础档取 summary 前缀 [高]=0 / [中]·无前缀=1 / [低]=2；超期每满 REFILL_STEP_DAYS 天升一档。

    `exclude`：**把某 id 排除在池外**。这是 `close` 两阶段化（4.8.1）的关键——阶段 1
    算补位候选时源行**还没删**、该条目**仍是 open**，不排除它就会**把自己补成 next**
    （关掉的条目立刻又成了当前决策点）。漏了这个参数，方案就从「根治」变成「换一个 bug」。
    """
    rows, blocked = [], 0
    ls = live_status_of("action")
    for r in st.load_live():
        if r.get("_slot") != "actions":
            continue
        if exclude and r.get("id") == exclude:
            blocked += 1
            continue
        if (r.get("status") or "open") != "open":
            # 仅 open 入池（t000138：只精确排 blocked 会放进 status=closed 的半关行；blocked＝等待中也不补位）
            blocked += 1
            continue
        m = PRIO_RE.match(r.get("summary", ""))
        base = PRIO_BASE[m.group(1).lower()] if m else 1
        age = _age_days(r.get("created", ""))
        steps = age // REFILL_STEP_DAYS
        eff = max(0, base - int(steps))
        rows.append(((eff, r.get("created", ""), r["id"]), r, base, int(steps), age))
    rows.sort(key=lambda x: x[0])
    return rows, len(rows), blocked


def refill_pick(st: Store, exclude: str = ""):
    """按策略给出补位目标：返回 (id, 解释)。池空 → ('', 解释)。"""
    rows, n, blocked = refill_pool(st, exclude)
    why = f"池 {n} 条" + (f"（排除非 open {blocked}）" if blocked else "")
    if not rows:
        return "", why + "·无可补"
    _, r, base, steps, age = rows[0]
    tier = f"基础档{base}" + (f"→有效档{max(0, base - steps)}（超期{age}天，+{steps}档）" if steps else f"（{age}天）")
    return r["id"], f"{why}·{r['id']} {tier}"


def plan_close(st: Store, id: str, outcome: str | None,
               no_refill: bool) -> dict:
    """**阶段 1：纯计算、零落盘**。任何 `die()` 都在一个字节都没写时发生。

    这是 p000069 的根治点。旧形把「算补位」放在「写 closed / 删源行 / 清 next」
    **之后**，于是补位策略一旦抛错，落盘已完成一半：条目已归档、`next` 仍指着已关
    条目——而那时 `check` 只能事后发现。拆成 plan/apply 后，可预见的失败全部前置；
    残留窗口只剩阶段 2 内两次 IO 之间（每步各自原子），且 `check` 抓得到、给得出修法。

    关键技术点：算补位候选时源行**还没删**、被关条目**仍是 open**，必须 `exclude=id`
    ——否则会「把自己补成 next」，关掉的条目立刻又成了当前决策点。
    """
    require_text("close", "--outcome", outcome)     # 空 outcome＝静默销账（p000051）
    st.note_pre_tamper()
    r = _find_live(st, id)
    if not r:
        die(f"close: 未找到 live 条目 {id}")
    typ = ID_RE.match(id).group(1)
    out = {k: r[k] for k in KEY_ORDER if k in r and not k.startswith("_")}
    out["closed"] = today()
    if outcome:
        out["outcome"] = outcome
    was_next = st.next_id() == id
    nid, why = ("", "（--no-refill，不补位）")
    if was_next and not no_refill:
        nid, why = refill_pick(st, exclude=id)      # ← 排除即将被关的那条
    elif not was_next:
        why = "（next 不是本条，不动指针）"
    src = Path(r["_file"])
    rest = [x for x in read_jsonl(src) if x.get("id") != id]
    return {"id": id, "typ": typ, "out": out, "was_next": was_next,
            "nid": nid, "why": why, "src": src, "rest": rest}


def apply_close(st: Store, plan: dict) -> int:
    """**阶段 2：纯落盘**。无 `die`、无依赖外部状态的分支判断。

    `next` **只写一次**（旧形先 `set_next("")` 再 `set_next(nid)`，中间那个窗口正是
    「指针既不是原值也不是新值」的事故现场）。
    """
    append_jsonl(st.d / "closed" / f"{plan['typ']}.jsonl", plan["out"])
    write_jsonl_atomic(plan["src"], plan["rest"])
    if plan["was_next"]:
        st.set_next(plan["nid"])
    st.write_index()      # 必须在 next 落定之后（index 内嵌 next，防陈旧）
    print(f"handoff close: {plan['id']} → closed/{plan['typ']}.jsonl")
    echo_back(st, plan["id"])
    if plan["was_next"]:
        if plan["nid"]:
            print(f"handoff next: 自动补位 → {plan['nid']}｜{plan['why']}")
            print(f"  策略：actions 池 · 排除非 open · 键(有效档, created↑, id↑) · "
                  f"基础档 [高]0/[中]·无1/[低]2 · 每满 {REFILL_STEP_DAYS} 天升一档")
        else:
            print(f"handoff next: 已清空（{plan['why']}）")
    return 0


def cmd_close(st: Store, id: str, outcome: str | None = None,
              no_refill: bool = False, **_ignored) -> int:
    """关闭一条 live 条目。**收显式参数而非 Namespace**（p000016 根治，4.8.0）。

    两阶段：先 `plan_close` 纯算、再 `apply_close` 纯写（p000069，4.8.1）——可预见的
    失败（找不到条目、引用守卫、补位策略）全部在**零落盘**时发生。

    关账事件入流水（4.9.3）：此前 `log.jsonl` **只有 check 事件**（本仓实测 474 次
    check:ok / 38 次 check:fail，**0 条 close**）⇒ 条目生命周期根本没进流水，事后查不出
    「哪一轮闭的、当时 exit 更新没」，`exit` 过期连痕迹都没有。落点选在这里而不是
    `apply_close`：那里拿不到 `outcome`（它不在 plan 字典里），插那儿会 NameError。
    `exit` 是否同步更新不在这里判——那是 fresh-stale 的活，这里只保证「闭过」可查。
    """
    st.note_pre_tamper()
    plan = plan_close(st, id, outcome, no_refill)
    apply_close(st, plan)
    print(f"handoff close: {plan['id']} → closed/{plan['typ']}.jsonl")
    echo_back(st, plan["id"])
    _log(st, "close", id=plan["id"], outcome=outcome or "", typ=plan["typ"])
    if plan["was_next"]:
        if plan["nid"]:
            print(f"handoff next: 自动补位 → {plan['nid']}｜{plan['why']}")
            print(f"  策略：actions 池 · 排除非 open · 键(有效档, created↑, id↑) · "
                  f"基础档 [高]0/[中]·无1/[低]2 · 每满 {REFILL_STEP_DAYS} 天升一档")
        else:
            print(f"handoff next: 已清空（{plan['why']}）")
    return 0


def cmd_next(st: Store, a) -> int:
    if a.clear:
        st.set_next("")
        st.write_index()
        print("handoff next: 已清空")
        return 0
    if a.auto:
        nid, why = refill_pick(st)
        if not nid:
            # 池空 ⇒ **把指针清空**（2026-10-03 修）。旧形直接 `die`、什么也不写：
            # 于是当 next 指向一个已关条目、而池里确实没有可补的条目时，照着
            # `check` 给的修法（`handoff next --auto`）跑完**指针依然坏着**——
            # 指引给了一条不保证有效的命令，等于没给。`next --auto` 的语义是
            # 「把 next 设成按策略算出的值」，池空时那个值就是空。
            st.set_next("")
            st.write_index()
            print(f"handoff next: 已清空（按补位策略无候选）｜{why}")
            return 0
        st.set_next(nid)
        st.write_index()
        print(f"handoff next: {nid}（按补位策略）｜{why}")
        return 0
    if not a.id:
        die("next: 需要 <id>、--auto 或 --clear")
    if not _find_live(st, a.id):
        die(f"next: {a.id} 不存在或已关闭")
    st.set_next(a.id)
    st.write_index()
    print(f"handoff next: {a.id}")
    return 0


def cmd_unconfirmed(st: Store, a) -> int:
    if a.action == "add":
        for label, v in (("--ref", a.ref), ("--summary", a.summary), ("--detail", a.detail)):
            require_text("unconfirmed add", label, v)
        summ = a.summary or a.ref
        if not summ:
            die("unconfirmed add: 需要 --ref 或 --summary（不可空）")
        e = {"id": st.allocate("u"), "created": today(), "summary": norm(summ)}
        if a.ref:
            e["src"] = a.ref
        if a.detail:
            e["detail"] = a.detail
        append_jsonl(st.unconf_file(), e)
        st.write_index()
        print(f"handoff unconfirmed add: {e['id']}")
        return 0
    if a.action == "resolve":
        require_text("unconfirmed resolve", "--outcome", a.outcome)
        r = _find_live(st, a.id)
        if not r or r.get("_slot") != "unconfirmed":
            die(f"unconfirmed resolve: 未找到候选 {a.id}")
        if a.as_slot:
            if a.as_slot not in ADD_KINDS:
                die("unconfirmed resolve: --as 须为 action|pitfall|decision")
            if a.as_slot == "decision":
                cmd_add(st, "decision", {"title": a.summary or r["summary"]})
            else:
                cmd_add(st, a.as_slot, {k: v for k, v in
                                        {"summary": a.summary or r["summary"], "domain": a.domain,
                                         "topic": r.get("topic"), "src": r.get("src"),
                                         "detail": r.get("detail")}.items() if v is not None})
            outcome = a.outcome or ("转正 " + a.as_slot)
        elif a.dismiss:
            outcome = a.outcome or "dismiss（作废）"
        else:
            die("unconfirmed resolve: 须给 `--as action|pitfall|decision`（转正）或 `--dismiss`（作废）")
        cmd_close(st, a.id, outcome, a.no_refill)
        return 0
    die("unconfirmed: 需要 add|resolve")


# ---------------- read / render ----------------
def cmd_rebase(st: Store, a) -> int:
    """**重建写事件基线**（`writes.jsonl`）为当前落盘事实——给「判据缺陷产生过的误报」结案。

    为什么需要它：`audit_writes` 扫的是**全部历史事件**。若某版本的前置旁证判据有缺陷
    （4.7.8 曾因在 `write_index` 里取快照，把「本次命令自己写的 mtime 变化」当成外部
    改动，4.7.9 已改为写命令**开始时**取快照），那些误报会**永久留在历史里、每次
    check 都红**，修判据也消不掉。没有结案出路，被误报卡住的人就只能去手改
    `writes.jsonl`——而那正是本工具要防的事。

    所以：判据出错时，先 `rebase --force`（**先手工核对**确有手改嫌疑之外的情况）把
    基线对齐现实，再修判据。它是显式动作、需确认、打印重建前后条数，不是静默自愈。
    """
    if not (st.d / "index").is_file():
        die(f"rebase: {st.d} 不是交接存储（缺 index）——拒绝凭空建出 {WRITES_LOG}"
            f"（这正是 `_log`/`log_write` 都有的守卫）")
    wl = st.d / WRITES_LOG
    before = len(read_jsonl(wl)) if wl.is_file() else 0
    if not a.force:
        die("rebase: 会丢弃现有写事件历史（那里面可能还藏着真问题）——"
            "确认已排除手改嫌疑后加 --force")
    # **真丢弃**带旁证的历史事件：rebase 的语义就是「结案」——旧事件里的 pre_tamper
    # 若留着，`audit_writes` 仍会逐条报出来，等于什么都没做（第一版就犯了这个：
    # 文档写「被 rebase 掉的历史旁证不再报」，实现却只是追加一条标记）。
    evs = read_jsonl(wl) if wl.is_file() else []
    tainted = [e for e in evs if e.get("pre_tamper")]
    keep = [e for e in evs if not e.get("pre_tamper") and e.get("op") != "__rebase__"]
    removed: set[str] = set()
    for e in keep:
        removed |= set(e.get("removed") or [])
    latest: dict[str, dict] = {}
    for e in keep:
        for f, rec in (e.get("files") or {}).items():
            # 已被 CLI 正常删掉的文件**不进新基线**：留着它，重建后仍会被判
            # 「文件不存在」⇒ rebase 对这类死红无效（4.8.1 的实测）。
            if f in removed:
                continue
            latest[f] = rec if isinstance(rec, dict) else {"sha": rec, "mt": None}
    now = {"ts": datetime.now().astimezone().isoformat(timespec="seconds"),
           "op": "__rebase__", "pre_tamper": [],
           "files": {f: {"sha": _sha((st.d / f).read_text(encoding="utf-8")),
                         "mt": (st.d / f).stat().st_mtime_ns}
                     for f in latest if (st.d / f).is_file()}}
    with open(wl, "w", encoding="utf-8") as f:
        for e in keep + [now]:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"handoff rebase: 写事件基线已对齐当前落盘"
          f"（历史 {before} 条 → 丢弃 {len(tainted)} 条带旁证的、"
          f"保留 {len(keep)} 条 ＋ 1 条 rebase 标记）")
    for e in tainted:
        for f in (e.get("pre_tamper") or []):
            print(f"    · 已结案：{f}（{e.get('op')}，{e.get('ts')}）")
    print("  **这些结论已不可追回**；若有真手改被一并结案，请从 `git log`/备份核对")
    return 0


def cmd_filter(st: Store, a) -> int:
    rows = st.load_live() if not a.id else st.load_live() + st.load_closed()
    if a.id:
        rows = [r for r in rows if r.get("id") == a.id]
        if not rows:
            die(f"filter: 未找到条目 {a.id}（live 与 closed 均无）", 2)
    if a.topic:
        rows = [r for r in rows if r.get("topic") == a.topic]
    if a.domain:
        rows = [r for r in rows if str(r.get("_file", "")).endswith(f"/{a.domain}.jsonl")]
    if a.status:
        rows = [r for r in rows if r.get("status", "open") == a.status]
    if a.json:
        print(json.dumps([ordered(r) for r in rows], ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['id']}\t{r.get('topic','-')}\t{r.get('summary','')}")
    return 0


def entry_display_line(r: dict) -> str:
    """条目在视图与 confirm 题面里的唯一呈现形（[id] + topic + summary ＋ 非 open 时的状态后缀）。
    两处共用同一函数——否则「照视图作答」与「判分口径」必然分叉（09-22 实测连错两题）。"""
    head = " ".join(x for x in (f"[{r['id']}]", r.get("topic", ""), r["summary"]) if x)
    st_ = r.get("status", "open")
    return head + (f"  ({st_})" if st_ != "open" else "")


def _render(st: Store) -> str:
    idx = json.loads((st.d / "index").read_text(encoding="utf-8")) if (st.d / "index").is_file() else {}
    lines = [f"<!-- 生成物 · 非权威 · 由 handoff view 生成于 {today()} -->",
             "# 项目交接视图（handoff view）", ""]
    for s in ("summary", "status", "scope", "exit"):
        p = st.d / s
        lines.append(f"## {s}")
        lines.append(p.read_text(encoding="utf-8").strip() if p.is_file() else "（空）")
        lines.append("")
    nid = st.next_id()
    lines += ["## next（下一步唯一一条）", nid or "（未指定）", ""]
    for slot in ENTRY_SLOTS:
        lines.append(f"## {slot}")
        for r in sorted((x for x in st.load_live() if x.get("_slot") == slot), key=lambda x: x.get("id", "")):
            lines.append("- " + entry_display_line(r))
        lines.append("")
    uc = read_jsonl(st.unconf_file())
    lines.append("## unconfirmed（未能确认）")
    for r in uc:
        lines.append(f"- [{r['id']}] {r.get('src','')} {r['summary']}")
    lines.append("")
    lines.append("## decisions")
    if st.decisions_dir().is_dir():
        for f in sorted(st.decisions_dir().glob("*.md")):
            fm = _frontmatter(f)
            lines.append(f"- [{fm.get('id', f.stem)}] {fm.get('status','')} {fm.get('domain','')} {fm.get('topic','')}")
    lines.append("")
    lines.append("## closed（归档）")
    for r in st.load_closed():
        lines.append(f"- [{r['id']}] {r.get('closed','')} {r.get('summary','')}")
    lines.append("")
    lines.append(f"> 计数：{json.dumps(idx.get('slots', {}), ensure_ascii=False)}；closed {len(st.load_closed())}")
    return "\n".join(lines) + "\n"


def _frontmatter(path: Path) -> dict:
    out: dict = {}
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if m:
        for ln in m.group(1).splitlines():
            if ":" in ln:
                k, v = ln.split(":", 1)
                out[k.strip()] = v.strip()
    return out


def cmd_view(st: Store, a) -> int:
    if a.id:
        hit = [r for r in st.load_live() + st.load_closed() if r.get("id") == a.id]
        if not hit and st.decisions_dir().is_dir():
            # decisions 槽是 `decisions/<id>.md`（frontmatter ＋ 正文），**不在**
            # load_live()/load_closed() 里——那两者只覆盖 jsonl 槽。原实现因此对
            # **每一条决策记录**都报「未找到（live 与 closed 均无）」，而它们明明
            # 在册。查不到的假报比查不到更坏：接收方据此以为决策丢了。
            for f in sorted(st.decisions_dir().glob("*.md")):
                fm = _frontmatter(f)
                if fm.get("id") == a.id or f.stem == a.id:
                    st_ = fm.get("status", "")
                    head = " ".join(x for x in (
                        f"[{a.id}]", fm.get("topic", ""),
                        fm.get("title", "") or f.stem) if x)
                    print(head + (f"  ({st_})" if st_ and st_ != "open" else "")
                          + f"  → {f}")
                    return 0
        if not hit and a.id in _voided_ids(st):
            # **已作废 ≠ 不存在**，与 check 的 D1 同口径（`rm` 会把条目落进
            # `trash/` 并记 `void`）。原实现只看 live/closed/decisions，于是对一个
            # 已经 `rm` 过的 id 报「均无」rc=2 —— 与本技能自己写下的口径相反，
            # 会把人引去查一个根本不该再查的东西。
            print(f"[{a.id}]（已作废：rm 落 trash/ 并记 void，非「查不到」）")
            return 0
        if not hit:
            die(f"view: 未找到条目 {a.id}（live / closed / decisions 均无，且不在 trash/·void）", 2)
        for r in hit:
            print(entry_display_line(r))
        return 0
    text = _render(st)
    if not a.save and not a.out:
        sys.stdout.write(text)
        return 0
    path = Path(a.out) if a.out else (st.root_dir / "handoff-view.md")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as e:
        print(f"handoff view: 写入失败: {e}", file=sys.stderr)
        return 1
    print(f"handoff view: 已写入 {path.resolve()}")
    return 0


# ---------------- confirm ----------------
def _facts(st: Store):
    live = st.load_live()
    entries = [r for r in live if r.get("_slot") in ENTRY_SLOTS]
    return live, entries


def cmd_confirm(st: Store, a) -> int:
    live, entries = _facts(st)
    rng = random.Random(a.seed)
    qs = []
    # 计数
    n_actions = len([r for r in live if r.get("_slot") == "actions"])
    qs.append({"q": "actions 槽当前条数？", "kind": "count", "expect": n_actions})
    # blocked
    blocked = sorted(r["id"] for r in live if r.get("status") == "blocked")
    qs.append({"q": "列出 status=blocked 的 id（无则答 无）", "kind": "set", "expect": blocked})
    # next
    nid = st.next_id()
    exp_next = nid if nid else "无"
    qs.append({"q": "next（下一步唯一一条）的 id？", "kind": "scalar", "expect": exp_next})
    # spot-check（随机）
    if entries:
        picks = rng.sample(entries, min(a.n, len(entries)))
        for r in picks:
            qs.append({"q": f"{r['id']} 的条目行（按视图呈现：[id] + topic + summary，非 open 含末尾 (status)）？",
                       "kind": "scalar", "expect": entry_display_line(r)})
    # locate
    if entries:
        r = rng.choice(entries)
        qs.append({"q": f"{r['id']} 属于哪个槽？", "kind": "scalar", "expect": r["_slot"]})
    # scope
    sp = st.d / "scope"
    scope_paths = sorted({l.strip() for l in sp.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")}) if sp.is_file() else []
    qs.append({"q": "scope 命中的路径（集合）？", "kind": "set", "expect": scope_paths})

    if not a.answers:
        for i, q in enumerate(qs, 1):
            print(f"Q{i}. {q['q']}")
        print("\n# JSON 题面：")
        print(json.dumps([{"q": f"Q{i}", "ask": q["q"]} for i, q in enumerate(qs, 1)], ensure_ascii=False, indent=2))
        return 0

    raw = sys.stdin.read() if a.answers == "-" else Path(a.answers).read_text(encoding="utf-8")
    try:
        ans = json.loads(raw)
    except json.JSONDecodeError as e:
        die(f"confirm: 答案非 JSON: {e}")
    bad = []
    for i, q in enumerate(qs, 1):
        got = ans.get(f"Q{i}", "")
        if q["kind"] == "set":
            exp = set(q["expect"])
            # 切分歧义：路径含空格 → 需换行/逗号切；id 列表 → 空白亦可。两种解释取其一命中即过。
            a_nl = {x.strip() for x in re.split(r"[\n,，;；]+", str(got)) if x.strip()}
            a_ws = {x for x in re.split(r"[,\s]+", str(got)) if x}
            ok = (exp == a_nl) or (exp == a_ws) if exp else (str(got).strip() in ("无", "", "none", "None"))
        else:
            ok = norm(got) == norm(q["expect"])
        if not ok:
            bad.append((i, q["q"], q["expect"], got))
    if bad:
        print(f"handoff confirm: FAIL（{len(bad)}/{len(qs)} 题不符）")
        for i, q, exp, got in bad:
            print(f"  Q{i} {q}\n    应: {exp}\n    实: {got}")
        return 1
    print(f"handoff confirm: PASS（{len(qs)} 题）")
    return 0


BEGIN_MARK = "<!-- handoff:begin -->"
END_MARK = "<!-- handoff:end -->"


def agents_block_text(profile: str = "basic") -> str:
    """标准交接块正文（两标记之间的内容，逐字节唯一源）。

    唯一源＝`project-handoff/references/agents-handoff-block.md`。别的仓通过
    `--install` 取同一份，**不要在各自 AGENTS.md 里手改条目**：改了不会同步，
    而 `--check` 会立刻报漂移——这与「复制 catalog 条款」导致漂移是同一个病。
    """
    src = Path(__file__).resolve().parent.parent / "references" / "agents-handoff-block.md"
    text = src.read_text(encoding="utf-8")
    if BEGIN_MARK not in text or END_MARK not in text:
        die(f"agents-block: 标准源缺标记（{BEGIN_MARK} / {END_MARK}）：{src}", 2)
    body = text.split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0]
    if profile == "freshness":
        fb, fe = "<!-- handoff:freshness:begin -->", "<!-- handoff:freshness:end -->"
        if fb in text and fe in text:
            # 连 **begin 标记一起**带上：它就是 --check 的档位识别锚点。
            # 丢了它，--check 会把增强档误判成 basic（行数不等、且逐行比对打不出差异行，
            # 症状极难认）。这个 bug 就是被 --check 本身抓出来的。
            seg = text.split(fb, 1)[1].split(fe, 1)[0].rstrip()
            body = body.rstrip() + "\n" + fb + "\n" + seg + "\n"
    elif profile != "basic":
        die(f"agents-block: 未知档位 {profile!r}（可用：basic / freshness）", 2)
    return BEGIN_MARK + body.rstrip() + "\n" + END_MARK + "\n"


FRESH_BEGIN = "<!-- handoff:freshness:begin -->"

HANDOFF_HEADING = re.compile(r"^#{2,3}\s+交接\s*$")


def find_handoff_sections(lines: list) -> list:
    """定位**所有** `## 交接` / `### 交接` 节，返回按出现顺序的 (起, 止右开) 列表。

    识别只认**标题行本身**（可有尾随空白），不靠正文里的「交接」二字——否则会
    把提到交接的普通段落整段吃掉。节到下一个同级或更高级标题为止；文末到 EOF。
    返回全部而非第一个：重复的交接节本身就是「单源」被破坏的现场，只收敛
    第一个会把第二个留在仓里继续被 agent 读到。
    """
    heads = [i for i, ln in enumerate(lines) if HANDOFF_HEADING.match(ln.rstrip())]
    secs = []
    for start in heads:
        level = len(lines[start]) - len(lines[start].lstrip("#"))
        stop = len(lines)
        for j in range(start + 1, len(lines)):
            s = lines[j]
            if s.startswith("#"):
                lv = len(s) - len(s.lstrip("#"))
                if lv <= level:
                    stop = j
                    break
        secs.append((start, stop))
    return secs


def find_handoff_section(lines: list) -> tuple | None:
    secs = find_handoff_sections(lines)
    return secs[0] if secs else None


def install_block(text: str, block: str) -> tuple:
    """把标准块装进 AGENTS.md 正文。返回 (新正文, 动作, 被替换的旧行数)。

    三种情形，唯一目标都是**单源**：标记区在 → 原地覆写块内；整节在但标记区
    不在 → 整理覆盖该节（手写副本被标准块收敛掉，节外不动）；都没有 → 新建
    `## 交接` 节。旧内容不备份——本工具的判据是「不留第二份」，留备份反而制造
    第二个可被 agent 读到的来源；需要原文时由 git 负责。
    """
    inner = block.split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0]
    new_block = BEGIN_MARK + inner + END_MARK
    if (BEGIN_MARK in text) != (END_MARK in text):
        # 残缺标记（只有一个端）。此时**不能**继续往下走：静默走整节替换会把
        # 含残片的那一段连人写的内容一起吃掉。宁可拒绝，让人先看。
        return text, "残缺标记", -1
    if text.count(BEGIN_MARK) > 1 or text.count(END_MARK) > 1:
        # 剥块时**保留空行结构**（别顺手 rstrip/丢空行，那会把整个文件的
        # 段落间距和章节顺序搅乱——单源达成不等于可以把别人的排版改掉）。
        text = re.sub(re.escape(BEGIN_MARK) + r".*?" + re.escape(END_MARK),
                      "", text, flags=re.DOTALL)
        return install_block(text, block)  # 剥干净后必是「整节」或「都没有」
    if BEGIN_MARK in text:
        text = (text.split(BEGIN_MARK, 1)[0] + new_block + text.split(END_MARK, 1)[1])
        return text, "更新", 0
    lines = text.splitlines()
    secs = find_handoff_sections(lines)
    if secs:
        start, end = secs[0]
        old = [ln for ln in lines[start + 1:end] if ln.strip()]
        # 重复的交接节：全部删掉，只留第一个装标准块。留着就是第二份来源。
        for s2, e2 in reversed(secs[1:]):
            old += [ln for ln in lines[s2:e2] if ln.strip()]
            del lines[s2:e2]
            # 注意：start/end 是**剥块后旧位置**算出的，secs[1:] 都在它们之后，
            # 删掉不影响前面的索引——这里绝不能再改 start/end（曾经写成
            # `start = end = min(start, s2)`，链式赋值把 end 压成 start，
            # 于是 lines[4:4]=[...] 变成插入而非替换，原标题被顶到块后面）。
        lines[start:end] = [lines[start], "", new_block.rstrip("\n"), ""]
        verb = "整理覆盖" if len(secs) == 1 else "整理覆盖+合并重复节"
        return "\n".join(lines).rstrip("\n") + "\n", verb, len(old)
    return text.rstrip("\n") + "\n\n## 交接\n\n" + block, "新建", 0


def cmd_agents_block(st: Store, a) -> int:

    if a.print_only:
        sys.stdout.write(agents_block_text(a.profile))
        return 0

    if a.check is not None:
        repo = Path(a.check).resolve()
        f = repo / "AGENTS.md"
        if not f.is_file():
            print(f"agents-block: FAIL（{f} 不存在）", file=sys.stderr)
            return 1
        text = f.read_text(encoding="utf-8")
        if BEGIN_MARK not in text or END_MARK not in text:
            print(f"agents-block: FAIL（{f} 没有 {BEGIN_MARK} / {END_MARK} 标记区）", file=sys.stderr)
            # 「没标记区」这支**不在** 4.9.0 三态分流范围内（分流要先认得出标记区）。
            # 而 `--install` 在这种仓上走的是「整节收敛」：会**吃掉**那节里的非空内容
            # （实测：标记行少个空格 ⇒ 用户的「- 我自己写的条款」被标准块顶掉，
            #  节外不动、不产生第二份节）。破坏性只在 install **之后**才打印 ⇒ 太晚，
            # 这里提前说清。判据：有没有非空的 `## 交接` 节——行数由实算给出。
            secs = find_handoff_sections(text.splitlines())
            risky = [s for s in secs
                     if any(l.strip() for l in text.splitlines()[s[0] + 1:s[1]])]
            if risky:
                n = sum(len([l for l in text.splitlines()[s[0] + 1:s[1]] if l.strip()])
                        for s in risky)
                print(f"  ⚠ 判定：仓里有 {len(risky)} 个非空 `## 交接` 节（共 {n} 行非空）"
                      f"但认不出标记区。", file=sys.stderr)
                print("  ⚠ `--install` 会**整节收敛**——那 {n} 行会被标准块顶掉"
                      "（节外不动、不会产生第二份节）。".replace("{n}", str(n)), file=sys.stderr)
                print("  修：先备份那节内容（或抄到块外章节），再跑 "
                      f"`--install {repo}`。", file=sys.stderr)
            else:
                print(f"  判定：没有非空的 `## 交接` 节，`--install` 会新建一节，"
                      f"不丢内容。", file=sys.stderr)
                print(f"  修：python3 <handoff>/scripts/handoff.py agents-block --install {repo}",
                      file=sys.stderr)
            return 1
        if text.count(BEGIN_MARK) != 1 or text.count(END_MARK) != 1:
            print(f"agents-block: FAIL（{f} 有 {text.count(BEGIN_MARK)} 个 {BEGIN_MARK}／"
                  f"{text.count(END_MARK)} 个 {END_MARK}——多份交接块并存＝单源已破）",
                  file=sys.stderr)
            print(f"  修：--install 会收敛到一份（重复的交接节一并合并）。", file=sys.stderr)
            return 1
        got = text.split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0].strip()
        # 档位**自动识别**（检查方不该被迫记住目标仓属于哪一档）：块内带增强档标记
        # 就按增强档比对。--profile 只在 --print/--install 时用作期望档位。
        effective = "freshness" if FRESH_BEGIN in got else "basic"
        want = agents_block_text(effective).split(BEGIN_MARK, 1)[1].split(END_MARK, 1)[0].strip()
        if got != want:
            print(f"agents-block: FAIL（{f} 的交接块与标准源不一致）", file=sys.stderr)
            # 差异按**行集合**分三类（不按位置）——旧形用 zip 按位置比，
            # 短序列一截断就**零差异行**（只在块末追加一行时实测 rc=1 但什么也不说）。
            g_lines = [l.strip() for l in got.splitlines() if l.strip()]
            w_lines = [l.strip() for l in want.splitlines() if l.strip()]
            g_set, w_set = set(g_lines), set(w_lines)
            extra = [l for l in g_lines if l not in w_set]      # 仓里有、源里没有 ⇒ 人手写内容
            missing = [l for l in w_lines if l not in g_set]   # 源里有、仓里没有 ⇒ 落后/被删
            n_diff = 0
            for i in range(max(len(g_lines), len(w_lines))):
                g = g_lines[i] if i < len(g_lines) else "（仓里没有这一行）"
                w = w_lines[i] if i < len(w_lines) else "（源里没有这一行）"
                if g != w:
                    n_diff += 1
                    if n_diff <= 3:
                        print(f"  差异 行{i + 1}:", file=sys.stderr)
                        print(f"    仓里: {g[:90]}", file=sys.stderr)
                        print(f"    源里: {w[:90]}", file=sys.stderr)
            if n_diff > 3:
                print(f"  …另有 {n_diff - 3} 行差异", file=sys.stderr)
            # 分流：有没有「人写内容」决定 `--install` 危不危险——它会覆盖块内一切。
            # 混为一谈就会在「块里有人写的条款」时把人写的内容静默吃掉
            # （与 4.8.6 修掉的 prev/「回退建议」同型：把静默丢弃说成正常操作）。
            if extra:
                print(f"  判定：块内有 {len(extra)} 行**源里没有的内容**（人手写条款）"
                      f"——`--install` 会**覆盖掉它们**。", file=sys.stderr)
                for l in extra[:3]:
                    print(f"    人写: {l[:90]}", file=sys.stderr)
                print("  修：先把这些条款抄到块外（或自己仓的其它章节），再跑 "
                      f"`--install {repo}`；不要直接覆盖。", file=sys.stderr)
            if missing:
                tag = "且" if extra else "块内是标准的、只是"
                print(f"  判定：{tag}**缺 {len(missing)} 行标准条款**（版本落后或被删）"
                      f"——`--install` 补装不会丢你写的内容。", file=sys.stderr)
                print(f"  修：--install {repo}（块外不动）。", file=sys.stderr)
            if not extra and not missing:
                print("  判定：两侧行集合相同、只是**顺序/重复**不同（手工整理过）。", file=sys.stderr)
                print(f"  修：--install {repo} 收敛为标准顺序（内容无损）。", file=sys.stderr)
            return 1
        print(f"agents-block: OK（{f} 交接块与标准源一致）")
        return 0

    if a.install is not None:
        block = agents_block_text(a.profile)
        repo = Path(a.install).resolve()
        f = repo / "AGENTS.md"
        if not f.is_file():
            print(f"agents-block: FAIL（{f} 不存在——先建仓或给对仓根）", file=sys.stderr)
            return 1
        text = f.read_text(encoding="utf-8")
        text, verb, replaced = install_block(text, block)
        if verb == "残缺标记":
            print(f"agents-block: FAIL（{f} 的标记区残缺——只有 "
                  f"{BEGIN_MARK if BEGIN_MARK in text else END_MARK}，缺另一端）",
                  file=sys.stderr)
            print("  这是手改坏过的痕迹。不自动修：静默整节替换会连带吃掉那段的"
                  "人写内容。修：把残缺的那一行删掉（或补齐另一端），再跑 --install。",
                  file=sys.stderr)
            return 1
        f.write_text(text, encoding="utf-8")
        if verb == "整理覆盖":
            print(f"agents-block: 整理覆盖交接块 → {f}（原有 ## 交接 节 "
                  f"{replaced} 行非空内容已被标准块收敛，节外未动）")
        else:
            print(f"agents-block: {verb}交接块 → {f}（块外内容未动）")
        return 0

    print("用法：agents-block --print | --install <仓根> | --check <仓根>", file=sys.stderr)
    return 2


# ---------------- export / import ----------------
def cmd_export(st: Store, a) -> int:
    recs = [{"_format": "handoff", "schema": 1, "exported": date.today().isoformat(),
             "counts": {s: len([r for r in st.load_live() if r.get("_slot") == s]) for s in ENTRY_SLOTS}}]
    for slot in ENTRY_SLOTS:
        for f in sorted((st.d / slot).glob("*.jsonl")):
            part_key = "purpose" if slot == "commands" else "domain"
            for r in read_jsonl(f):
                rec = {"_kind": "entry", "_slot": slot, f"_{part_key}": f.stem}
                rec.update(ordered(r))
                recs.append(rec)
    for r in read_jsonl(st.unconf_file()):
        rec = {"_kind": "entry", "_slot": "unconfirmed"}
        rec.update(ordered(r))
        recs.append(rec)
    for r in st.load_closed():
        rec = {"_kind": "entry", "_slot": "closed"}
        rec.update(ordered(r))
        recs.append(rec)
    for f in sorted(st.decisions_dir().glob("*.md")) if st.decisions_dir().is_dir() else []:
        recs.append({"_kind": "doc", "_slot": "decisions", "_id": f.stem, "content": f.read_text(encoding="utf-8")})
    for s in SINGLES:
        p = st.d / s
        recs.append({"_kind": "doc", "_slot": s, "content": p.read_text(encoding="utf-8") if p.is_file() else ""})
    recs.append({"_kind": "ref", "_slot": "next", "ref": st.next_id()})
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"handoff export: 已写入 {Path(a.out).resolve()}")
    else:
        sys.stdout.write(text)
    return 0


def store_has_entries(st: Store) -> bool:
    for f in st.live_shards() + st.closed_shards():
        if f.stat().st_size > 0:
            return True
    if st.unconf_file().is_file() and st.unconf_file().stat().st_size > 0:
        return True
    if st.decisions_dir().is_dir() and any(st.decisions_dir().glob("*.md")):
        return True
    return False


def _reset_store(st: Store):
    """清空数据槽（保留 legacy/ 归档），供 import --force 重置。"""
    for slot in ENTRY_SLOTS:
        d = st.d / slot
        if d.is_dir():
            shutil.rmtree(d)
    for d in (st.decisions_dir(), st.d / "closed"):
        if d.is_dir():
            shutil.rmtree(d)
    for f in (st.unconf_file(), st.d / "index", st.d / "next", st.d / "log.jsonl", *[st.d / s for s in SINGLES]):
        if f.is_file():
            f.unlink()


def _fm_fields(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end < 0:
        return {}
    out = {}
    for ln in content[3:end].splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def _prevalidate_import(recs, today_: str):
    """写前校验：失败即中止，**不留半写存储**（不先重置）。"""
    for i, rec in enumerate(recs[1:], 2):
        k, slot = rec.get("_kind"), rec.get("_slot")
        if k == "entry":
            if slot not in ("actions", "pitfalls", "commands", "unconfirmed", "closed"):
                die(f"import: 第 {i} 行不支持的 entry _slot={slot!r}")
            for f in ("created", "closed"):
                v = rec.get(f)
                if v and not DATE_RE.match(str(v)):
                    die(f"import: 第 {i} 行 {f}={v!r} 非日期（YYYY-MM-DD）")
            if slot == "closed" and not rec.get("id") and rec.get("_type") not in ("t", "p", "d", "c", "q"):
                die(f"import: 第 {i} 行 closed 记录缺 id 且 `_type` 非法")
        elif k == "doc":
            if slot == "decisions":
                did = rec.get("_id")
                if not did or not re.match(r"^d\d{6}$", str(did)):
                    die(f"import: 第 {i} 行 decisions doc 缺合法 _id（d<6 位>）")
                fm = _fm_fields(rec.get("content", ""))
                if fm.get("id") != did:
                    die(f"import: 第 {i} 行 decisions/{did}.md frontmatter id={fm.get('id')!r} 与文件名不符")
                if not DATE_RE.match(str(fm.get("created", ""))):
                    die(f"import: 第 {i} 行 decisions/{did}.md frontmatter created 缺或非日期")
            elif slot not in SINGLES:
                die(f"import: 第 {i} 行不支持的 doc _slot={slot!r}")
        elif k == "ref" and slot == "next":
            pass
        else:
            die(f"import: 第 {i} 行不支持的记录 _kind={k!r} _slot={slot!r}（不静默丢弃）")


def cmd_import(st: Store, a) -> int:
    raw = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    recs = []
    for i, line in enumerate(raw.splitlines(), 1):
        if line.strip():
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError as e:
                die(f"import: 第 {i} 行非法 JSON: {e}")
    if not recs or recs[0].get("_format") != "handoff":
        die("import: 缺 meta 头（_format=handoff）")
    # 先校验（此时尚未改存储）——清单坏 → 原存储原样保留
    _prevalidate_import(recs, today())
    if store_has_entries(st):
        if not a.force:
            die(f"import: {st.d} 已有条目，拒绝（`--force` 会**先重置**再导入）")
        _reset_store(st)   # --force = 重置重建（非增量追加），避免与旧存储混

    # 建骨架（幂等；容忍 init 已建——消除「init→import 必失败」）
    st.d.mkdir(parents=True, exist_ok=True)
    for s in SINGLES:
        if not (st.d / s).is_file():
            (st.d / s).write_text(SCOPE_HEADER if s == "scope" else "", encoding="utf-8")
    for slot in ENTRY_SLOTS:
        (st.d / slot).mkdir(parents=True, exist_ok=True)
    st.decisions_dir().mkdir(parents=True, exist_ok=True)
    (st.d / "closed").mkdir(parents=True, exist_ok=True)
    if not st.unconf_file().is_file():
        st.unconf_file().write_text("", encoding="utf-8")
    if not (st.d / "next").is_file():
        st.set_next("")

    today_ = today()
    slot_type = {"actions": "t", "pitfalls": "p", "commands": "c", "unconfirmed": "u"}
    for rec in recs[1:]:
        k = rec.get("_kind")
        slot = rec.get("_slot")
        if k == "entry":
            if slot not in ("actions", "pitfalls", "commands", "unconfirmed", "closed"):
                die(f"import: 不支持的 entry _slot={slot!r}（须 actions/pitfalls/commands/unconfirmed/closed）")
            body = {kk: vv for kk, vv in rec.items() if kk in ALLOWED_KEYS}
            # 缺日期 → 脚本补（迁移者可留空，不靠 LLM 编造）
            if slot == "closed" and not body.get("closed"):
                body["closed"] = today_   # 取不到 → 脚本盖迁移日（与 created 同规则）
            if not body.get("created"):
                body["created"] = body.get("closed") or today_
            # 缺 id → 脚本分配（closed 可给 `_type` 提示：t|p|d|c|q）
            if not body.get("id"):
                if slot == "closed":
                    typ = rec.get("_type")
                    if typ not in ("t", "p", "d", "c", "q"):
                        die("import: closed 记录缺 id，且未给有效 `_type`（t|p|d|c|q）")
                    body["id"] = st.allocate(typ)
                else:
                    body["id"] = st.allocate(slot_type[slot])
            if slot in ENTRY_SLOTS:
                part = rec.get("_purpose") if slot == "commands" else rec.get("_domain", "_global")
                _pkey = "purpose" if slot == "commands" else "domain"
                append_jsonl(st.d / slot
                             / f"{guard_partition('import', _pkey, part)}.jsonl", body)
            elif slot == "unconfirmed":
                append_jsonl(st.unconf_file(), body)
            elif slot == "closed":
                m = ID_RE.match(body.get("id", ""))
                typ = m.group(1) if m else "x"
                append_jsonl(st.d / "closed" / f"{typ}.jsonl", body)
        elif k == "doc":
            if slot == "decisions":
                if "_id" not in rec:
                    die("import: doc decisions 缺 _id")
                (st.decisions_dir() / f"{rec['_id']}.md").write_text(rec.get("content", ""), encoding="utf-8")
            elif slot in SINGLES:
                (st.d / slot).write_text(rec.get("content", ""), encoding="utf-8")
            else:
                die(f"import: 不支持的 doc _slot={slot!r}")
        elif k == "ref" and slot == "next":
            st.set_next(rec.get("ref", ""))
        else:
            die(f"import: 不支持的记录 _kind={k!r} _slot={slot!r}（不静默丢弃）")
    st.write_index()
    rc = cmd_check(st)
    if rc != 0:
        die("import: 导入后 check 未过（内容仍落地，请检查）")
    print("handoff import: ok")
    return 0


# ---------------- scope（源登记表）----------------
def _void_file(st: Store) -> Path:
    return st.d / "void"


def _void_ids(st: Store) -> list[str]:
    p = _void_file(st)
    if not p.is_file():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _voided_ids(st: Store) -> set[str]:
    """作废 id ＝ `void` ∪ `trash/`（**单源**，check 与 view 共用）。

    `rm` 的正常路径同时做「移入 trash/」＋「记 void」，故两者天然同步（本仓实测
    6/6 一致）；但把口径写成两处各算一遍，只差一步就会分叉成「check 说已作废、
    view 说查不到」。判据间的口径必须同源，否则同一个事实两处结论相反。
    """
    out = set(_void_ids(st))
    trash = st.d / "trash"
    if trash.is_dir():
        for f in sorted(trash.glob("*.jsonl")):
            for r in read_jsonl(f):
                if r.get("id"):
                    out.add(r["id"])
        out |= {f.stem for f in trash.glob("*.md")}
    return out


def _add_void(st: Store, i: str):
    st.d.mkdir(parents=True, exist_ok=True)
    with open(_void_file(st), "a", encoding="utf-8") as f:
        f.write(i + "\n")


def _read_rows(p: Path) -> list[dict]:
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def _write_rows(p: Path, rows: list[dict]):
    fd, tmp = tempfile.mkstemp(dir=str(p.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(ordered(r), ensure_ascii=False) + "\n")
    os.replace(tmp, p)


def _find_entry(st: Store, i: str):
    """返回 (row, file, slot)；未找到 → (None, None, None)。"""
    for r in st.load_live():
        if r.get("id") == i:
            return r, r["_file"], r["_slot"]
    for r in st.load_closed():
        if r.get("id") == i:
            return r, r["_file"], "closed"
    return None, None, None


def cmd_rm(st: Store, a) -> int:
    """受控删除：移入 `.handoff/trash/` + 记入 `void`（防 id 复用）+ 引用守卫。"""
    st.note_pre_tamper()          # 写前旁证快照（本次写自己的 mtime 变化不算外部改动）
    i = a.id
    if i in _void_ids(st):
        die(f"rm: {i} 已作废")
    row, f, slot = _find_entry(st, i)
    dec = st.decisions_dir() / f"{i}.md"
    if row is None and not dec.is_file():
        die(f"rm: 未找到 {i}")
    if st.next_id() == i:
        die(f"rm: {i} 是 next（先 `handoff next --clear`）")
    for r in st.load_live() + st.load_closed():
        if r.get("id") != i and r.get("blockedBy") == i:
            die(f"rm: {i} 被 {r['id']} 的 blockedBy 引用")
    if dec.is_file():
        for d in sorted(st.decisions_dir().glob("*.md")):
            if d.stem == i:
                continue
            if _fm_fields(d.read_text(encoding="utf-8")).get("supersedes") == i:
                die(f"rm: {i} 被决策 {d.stem} supersedes 引用")
    tdir = st.d / "trash"
    tdir.mkdir(parents=True, exist_ok=True)
    if dec.is_file():
        os.replace(str(dec), str(tdir / f"{i}.md"))
    else:
        rows = _read_rows(f)
        with open(tdir / f"{i}.jsonl", "a", encoding="utf-8") as fh:
            for r in rows:
                if r.get("id") == i:
                    fh.write(json.dumps(ordered(r), ensure_ascii=False) + "\n")
        _write_rows(f, [r for r in rows if r.get("id") != i])
    _add_void(st, i)
    st.write_index()
    print(f"handoff rm: {i} → .handoff/trash/（作废，id 不复用）")
    return 0


def cmd_edit(st: Store, a) -> int:
    """受控修正安全字段（id / created / closed 不可改）；改 domain/purpose → 迁移分区。

    可改面按**条目所属槽**当场核（`editable_fields`，与 add 同一声明源）：型不符的键**硬报错**，
    不再像旧版那样落进 `ALLOWED_KEYS` 过滤器里静默丢弃（`edit <action> --purpose` 曾无声消失）。
    `edit` 无法按型分 flag 面——型由 id 前缀推出、不在命令行上，故这里用运行时守卫补同一缺口。
    """
    row, f, slot = _find_entry(st, a.id)
    if row is None:
        die(f"edit: 未找到条目 {a.id}（决策文档暂不支持 edit）")
    upd = {k: getattr(a, k) for k in EDIT_KEYS if getattr(a, k, None) is not None}
    ff_keys: set = set()
    ff = getattr(a, "from_file", None)
    if ff:
        allowed = editable_fields(slot)
        got = load_from_file(f"edit {slot}", ff, allowed)
        # 同一字段既给 flag 又给文件 → 报错，不静默取一个（静默丢弃是本 CLI 的老病）
        dup = sorted(set(upd) & set(got))
        if dup:
            die(f"edit {a.id}: 字段 {dup} 同时出现在命令行与 --from-file；只留一处")
        upd.update(got)
        ff_keys = set(got)
    if not upd:
        die(f"edit: 未给任何可改字段（{'/'.join('--' + k for k in EDIT_KEYS)}）")
    for k in sorted(upd):
        require_text("edit", f"--{k}", upd[k],          # 空串＝清空字段（p000048：643→0）
                     from_shell=k not in ff_keys)       # --from-file 来的值不经 shell，不查危险字符
    allowed = editable_fields(slot)
    if bad := set(upd) - allowed:
        die(f"edit: {slot} 条目不接受 {sorted(bad)}（该型可改＝{sorted(allowed)}）")
    if "status" in upd:                                 # t000138：closed 只能走 close 流程
        kind = SLOT2KIND.get(slot)
        if kind:
            guard_status(kind, upd["status"])
    pkey = ENTRY_SLOTS[slot]["part"] if slot in ENTRY_SLOTS else None
    if pkey in upd:                                     # domain/purpose → 换分区文件
        newpart = guard_partition(f"edit {slot}", pkey, upd.pop(pkey))
        rows = _read_rows(f)
        for r in rows:
            if r.get("id") == a.id:
                for k, v in upd.items():
                    if k in ALLOWED_KEYS:
                        r[k] = v
                append_jsonl(st.d / slot / f"{newpart}.jsonl", r)
        rest = [r for r in rows if r.get("id") != a.id]
        if rest:
            _write_rows(f, rest)
        else:
            # 旧分区被搬空 ⇒ **删掉空文件**。原实现留着它：Linux 上无害（glob 扫得到、
            # 计数 0），但它仍是一个**占着名字的分区文件**——而分区名就是索引维度。与另一
            # 个仅大小写不同的分区并存时，Windows/NTFS 上两者会合并，index 计数与现实脱节。
            # 本条是 4.7.5 新增「大小写折叠重名」判据**暴露出来的既有残留**。
            f.unlink(missing_ok=True)
    else:
        rows = _read_rows(f)
        for r in rows:
            if r.get("id") == a.id:
                for k, v in upd.items():
                    if k in ALLOWED_KEYS:
                        r[k] = v
        _write_rows(f, rows)
    st.write_index()
    print(f"handoff edit: {a.id}（改 {', '.join(sorted(upd)) or pkey}）")
    echo_back(st, a.id)
    return 0


def cmd_set(st: Store, a) -> int:
    """单文件槽增量写入口（status/summary/exit）——补「add 无覆盖」缺口。"""
    st.note_pre_tamper()          # 写前旁证快照（本次写自己的 mtime 变化不算外部改动）
    if a.slot == "scope":
        die("set: scope 请用 `scope add/remove/prune`")
    if a.slot not in SINGLES:
        die("set: 只支持单文件槽 status/summary/exit/scope")
    content = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    st.d.mkdir(parents=True, exist_ok=True)
    tgt = st.d / a.slot
    old = tgt.read_text(encoding="utf-8") if tgt.is_file() else ""
    if not content.strip() and not a.allow_empty:
        # P1 不删：空内容多半是 `--file -` 忘了喂 stdin，静默清空槽位即数据丢失
        die("set: 内容为空——确认要清空请加 --allow-empty（P1 不删：疑似 stdin 漏喂）"
            )   # 被拒时**一个字节都没写、也没快照**（快照在守卫之后，4.8.4）——别在这里提 prev/
    # 拒空守门只拦「零字节」，拦不住「把整槽覆写当局部编辑用」——09-22 实测复发：
    # 只喂一行表头就把 3677 字符的 status 清成 11 字符。
    #
    # **原来的 `len(old) > 200` 是条盲区**（p000029，2026-10-03 实测）：旧内容 123B／315B
    # 时只喂一行 → 截断到 17B 却**静默放行 rc=0**；1957B 起才拦。而小仓/新项目恰恰最容易被
    # 随手写一行，那条下限正好把它们全漏掉。现改为**旧内容非空即判**（不设字节下限）——
    # 「整槽覆写 vs 局部编辑」是**语义**问题，不该由文件大小决定。小文件误判由 60% 降幅本身
    # 兜住（本就几十字节的槽删几行才算骤降）；且错误信息**直接给出可复制的恢复命令**：
    # 反复确认会被自动化掉，**易 undo 才是真正的安全**。
    #
    # **本判据的固有边界（如实写明，别当它无所不能）**：在**极小内容**上比例阈值不可靠——
    # 一个 25 字符的槽删到 10 字符（降幅 40%）分不清「有意删掉一行」与「只喂了表头」。
    # 这类残余误用由 `--dry-run`（写入前逐条列出将丢失的行）兜，而不是继续调阈值：
    # 阈值再调就必然开始误伤正常的小幅删减。
    if getattr(a, "dry_run", False):
        print(f"handoff set --dry-run: {a.slot}")
        print(f"  将写入 {len(content)} 字符 / {len(content.splitlines())} 行"
              + (f"；现有 {len(old)} 字符 / {len(old.splitlines())} 行" if old else "（槽现为空）"))
        if old and len(content) < len(old):
            print(f"  ⚠ 将**减少** {len(old) - len(content)} 字符"
                  f"（{len(old)} → {len(content)}）——单文件槽是整槽覆写")
        lost = [ln for ln in old.splitlines() if ln.strip() and ln not in content]
        for ln in lost[:10]:
            print(f"  - 将丢失行: {ln[:100]}")
        if len(lost) > 10:
            print(f"  … 另有 {len(lost) - 10} 行将丢失")
        print("  （未写入任何内容；去掉 --dry-run 执行）")
        return 0
    o_len, n_len = len(old.strip()), len(content.strip())
    if old.strip() and n_len < 0.6 * o_len and not a.force:
        # **不要在这里给「恢复命令」**（4.8.5 独立审计实测：这是条**死命令且危险**的
        # 建议）。被拒时**一个字节都没写**，`{a.slot}` 还是原内容——根本不需要回退；
        # 而 `prev/` 存的是**上一次成功写入**的版本，读者照做反而会把当前内容
        # 覆盖成上一个版本，**全程无警告**（自建样例：当前 W、prev 是陈旧 V，
        # 照提示复制 ⇒ W 被 V 覆盖）。要回退请用 `git` 或你自己留的备份。
        die(f"set: {a.slot} 内容骤降 {o_len} → {n_len} 字符（<60%）——"
            f"单文件槽是**整槽覆写**、无追加语义；只想改一处请取回全文、改完再整槽喂回；"
            f"确要大幅删减加 --force。\n"
            f"  （本次**未写入任何内容**，`{a.slot}` 仍是原内容，不需要回退。"
            f"要恢复到别的版本请用 git 或你自己的备份——`prev/` 是**上一次成功写入**"
            f"的版本，不是「本该写进去但没写」的那个。）")
    if old.strip():
        # 快照放在**所有守卫之后、真正写入之前**：守卫拒绝与 `--dry-run` 都不该在盘上
        # 留痕迹（旧实现快照在最前 ⇒ `--dry-run` 明明输出「未写入任何内容」却改了 prev/，
        # 独立审计实测抓到）。`prev/` 的语义因此更准＝**上一次成功写入的版本**。
        prev = st.d / "prev"
        prev.mkdir(exist_ok=True)
        (prev / a.slot).write_text(old, encoding="utf-8")
    tgt.write_text(content, encoding="utf-8")
    # 原先 `set` **不**走 write_index ⇒ 写事件（p000025 的判据面）在最常用的写命令上
    # 根本没产生。补上，并带 op 名以便对账时能指出是哪条命令。
    st.write_index(f"set {a.slot}")
    print(f"handoff set: {a.slot}（{len(content)} 字符" + (f"，旧内容快照 prev/{a.slot}" if old.strip() else "") + "）")
    return 0


def _scope_lines(st: Store) -> list[str]:
    p = st.d / "scope"
    if not p.is_file():
        return []
    return [s for s in (l.strip() for l in p.read_text(encoding="utf-8").splitlines())
            if s and not s.startswith("#")]


def _scope_resolves(st: Store, entry: str) -> bool:
    pat = entry if os.path.isabs(entry) else str(st.root_dir / entry)
    if any(c in entry for c in "*?["):
        return bool(glob.glob(pat, recursive=True))
    return os.path.exists(pat)


_SKIP_DIRS = {".handoff", ".git", "node_modules", ".venv", "__pycache__", ".scaffold"}
_LEGACY = ("HANDOFF.md", "HANDOFF-ARCHIVE")

# 完备性扫描标记词表（t000098）：原只认 `- [ ]` / `<!-- open:`，漏掉「建议以表格／散文形态
# 存在于报告里」这一整类（09-22 实测：21 条建议全在表格里，五份出处只捞到 1 份）。
# 基表取自设计件 audits/2026-09-20-pending-item-loss-rootcause.md L183 的封闭词表；
# 项目可在 `.handoff/scope-vocab` 追加词、在 `.handoff/scope-ignore` 登记 fnmatch 豁免。
_MARKER_HEAD = ("建议", "待办", "未决", "待决", "残余", "下一步", "待定", "TBD", "遗留",
                "未实施", "未闭环", "待裁", "待回填", "未办", "缺口", "待投入")
_MARKER_TOKENS = ("TODO", "FIXME", "XXX")          # ASCII，按词边界匹配
_MARKER_CJK = ("未做", "备而未用")                  # 句内出现即算（CJK 无 ASCII 词边界可依）


def _conf_lines(p: Path) -> list[str]:
    if not p.is_file():
        return []
    return [s for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
            if (s := ln.split("#", 1)[0].strip())]


def scope_markers(st: "Store") -> re.Pattern:
    words = list(_MARKER_HEAD)                                  # 标题/表格内命中（防正文噪声）
    extra = _conf_lines(st.d / "scope-vocab")                   # 项目追加词：全文命中（opt-in）
    alt = "|".join(re.escape(w) for w in words)
    toks = "|".join(re.escape(t) for t in _MARKER_TOKENS)
    cjk = "|".join(re.escape(t) for t in (*_MARKER_CJK, *extra))
    return re.compile(
        r"^\s*-\s*\[ \]" r"|<!--\s*open:"
        rf"|\b(?:{toks})\b"
        rf"|^#{{1,6}}\s[^\n]*(?:{alt})"            # 标题含建议词
        rf"|^\|[^\n]*\|[^\n]*(?:{alt})[^\n]*\|"    # 表格行含建议词（表格建议行）
        rf"|(?:{cjk})", re.M)


def scope_ignore(st: "Store") -> list[str]:
    return _conf_lines(st.d / "scope-ignore")


def _gitignore_patterns(root: Path) -> list[str]:
    p = root / ".gitignore"
    if not p.is_file():
        return []
    out = []
    for l in p.read_text(encoding="utf-8", errors="replace").splitlines():
        s = l.strip()
        if s and not s.startswith("#") and not s.startswith("!"):
            out.append(s)
    return out


def _ignored(patterns: list[str], rel: str) -> bool:
    import fnmatch
    parts = rel.split("/")
    for pat in patterns:
        p = pat.rstrip("/")
        if "/" in p:
            if fnmatch.fnmatch(rel, p) or rel.startswith(p + "/"):
                return True
        elif any(fnmatch.fnmatch(part, p) for part in parts):
            return True
    return False


def _brace_expand(s: str) -> list[str]:
    m = re.search(r"\{([^{}]+)\}", s)
    if not m:
        return [s]
    out = []
    for alt in m.group(1).split(","):
        out += _brace_expand(s[:m.start()] + alt + s[m.end():])
    return out


def _scope_scan(st: Store) -> int:
    """机械候选提议：命中标记 / 旧模型件 / 旧 HANDOFF 引用，且未登记。纯提议、非权威。

    标记词表＝基表（`scope_markers`，t000098 已扩到标题/表格形态）＋ `.handoff/scope-vocab`
    项目追加词；`.handoff/scope-ignore` 的 fnmatch 模式**豁免**文件（压噪声，均属纯提议面）。
    """
    root = st.root_dir
    reg = set(_scope_lines(st))
    ign = _gitignore_patterns(root)
    ignores = scope_ignore(st)
    marker = scope_markers(st)
    cands: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in _SKIP_DIRS and not _ignored(ign, str((Path(dirpath) / d).relative_to(root)))]
        for fn in filenames:
            fp = Path(dirpath) / fn
            rel = str(fp.relative_to(root))
            if _ignored(ign, rel) or not fn.lower().endswith((".md", ".markdown", ".txt")):
                continue
            if any(fnmatch.fnmatch(rel, p) for p in ignores):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if marker.search(text):
                cands.add(rel)
    # 旧模型件总提议（主迁移源，即便无标记）
    for leg in _LEGACY:
        t = root / leg
        if t.is_dir():
            for f in sorted(t.rglob("*.md")):
                cands.add(str(f.relative_to(root)))
        elif t.is_file():
            cands.add(leg)
    # 旧 HANDOFF 引用（花括号展开；跳过绝对 / URL / 锚）
    ho = root / "HANDOFF.md"
    if ho.is_file():
        text = ho.read_text(encoding="utf-8", errors="replace")
        for raw in re.findall(r"`([^`\s]+)`", text) + re.findall(r"\]\(([^)\s]+)\)", text):
            for m in _brace_expand(raw.strip()):
                if not m or m.startswith(("http", "#", "/")):
                    continue
                try:
                    rp = (root / m).resolve()
                    if rp == st.d.resolve() or st.d.resolve() in rp.parents:
                        continue
                except OSError:
                    pass
                if os.path.exists(str(root / m)):
                    cands.add(m)
    for c in sorted(x for x in cands if x not in reg):
        print(c)
    return 0


def cmd_scope(st: Store, a) -> int:
    p = st.d / "scope"
    if a.action == "list":
        for e in _scope_lines(st):
            print(e)
        return 0
    if a.action == "add":
        if not a.path:
            die("scope add: 需要 <path|glob>")
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(a.path.strip() + "\n")
        st.write_index("scope add")   # 写事件：否则 scope 的改动无记录，
                                      # 之后**任何**写命令都把它当成「CLI 之外的改动」
                                      # （分发点统一取快照也救不了——快照只是读，不产生记录）
        print(f"handoff scope add: {a.path}")
        return 0
    if a.action == "remove":
        lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
        kept = [l for l in lines if l.strip() != (a.path or "").strip()]
        fd, tmp = tempfile.mkstemp(dir=str(st.d))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(kept) + ("\n" if kept else ""))
        os.replace(tmp, p)
        st.write_index("scope remove")
        print(f"handoff scope remove: {a.path}")
        return 0
    if a.action == "prune":
        lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
        kept, dropped = [], []
        for l in lines:
            s = l.strip()
            if not s:
                continue
            if s.startswith("#") or _scope_resolves(st, s):
                kept.append(l)
            else:
                dropped.append(s)
        fd, tmp = tempfile.mkstemp(dir=str(st.d))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(kept) + ("\n" if kept else ""))
        os.replace(tmp, p)
        for d in dropped:
            print(f"handoff scope prune: 移除不可解析 {d}")
        if not dropped:
            print("handoff scope prune: 无可移除")
        st.write_index("scope prune")
        return 0
    if a.action == "scan":
        return _scope_scan(st)
    die("scope: 需要 list|add|remove|prune|scan")


# ---------------- main ----------------
def _reject_legacy_form(argv: list[str]) -> None:
    """`add --slot <槽>` 已废（v3.2.0）：并集参数面会让本型不消费的键静默消失。

    不留兼容层——留了就等于把并集面留着，病没治。旧形**非零退出**并直接印出新形（P3 不静默）。
    """
    if "add" not in argv:
        return
    j = argv.index("add") + 1                   # 位置判定：旧形的 --slot 紧跟 add；
    if j >= len(argv) or not argv[j].startswith("--slot"):
        return                                  # 否则只是某个参数值里提到了 --slot（如写废止说明）
    tok = argv[j]
    val = tok.split("=", 1)[1] if "=" in tok else (
        argv[j + 1] if j + 1 < len(argv) and not argv[j + 1].startswith("-") else "")
    new = SLOT2KIND.get(val)
    tip = (f"改用 `handoff add {new} …`" if new
           else "改用 `handoff unconfirmed add --ref <路径#锚> [--summary …]`" if val == "unconfirmed"
           else "改指某型：`handoff add action|pitfall|command|decision …`")
    die(f"add --slot {val or '<槽>'} 已废（该面按型不消费的字段会静默丢弃）：{tip}", 2)


def cmd_selftest(st: Store, a) -> int:
    """双向夹具（t000138）：闭集守卫的判据全部落在**退出码＋落盘行**上，不留给现场抉择。

    在临时 store 里跑真 CLI（main 递归、--store 指向 tmp），七步覆盖：
    edit/add 对 closed 及表外值的拒收（负向）、pitfall fixed 与 blocked 的放行（正向）、
    脏行混入后 refill 出池＋check FAIL（机检兜底）、close 两步修复后 check 复绿。
    """
    import tempfile
    fails: list[str] = []

    cur_store = [""]          # run() 的目标 store（--store 须置于子命令前，全局 flag）
    def run(*argv, inp=None):
        buf = io.StringIO()
        err = io.StringIO()
        so, se, sin = sys.stdout, sys.stderr, sys.stdin
        rc = 0
        sys.stdout, sys.stderr = buf, err
        if inp is not None:
            sys.stdin = io.StringIO(inp)
        try:
            rc = main(["--store", cur_store[0], *argv]) or 0
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 1
        finally:
            sys.stdout, sys.stderr, sys.stdin = so, se, sin
        return rc, buf.getvalue() + err.getvalue()

    def rows(slot: str) -> list[dict]:
        return [r for r in Store(Path(cur_store[0])).load_live() if r.get("_slot") == slot]

    def non_tamper(out: str) -> str:
        """剔除写事件对账的行。

        为什么需要：本夹具**自己**就是靠手工写文件注入坏行来造脏件的（不这样造就没有
        「脏行」可测），而那**正是**「未经 CLI 记录的写入」——新判据理应报它。所以
        「修好了吗」不能问 `rc==0`，只能问「除那条已知的 tamper 外没有别的问题」。
        """
        keep = []
        for l in (out or "").splitlines():
            if l.startswith("handoff check:"):        # 汇总行也要剔，否则它让 strip() 非空
                continue
            if any(k in l for k in ("未经 CLI 记录的写入", "写入**之前**发现",
                                    "补手续疑似", "写事件记录过它", "mtime 更新")):
                continue
            keep.append(l)
        return "\n".join(keep)

    def expect(name: str, cond: bool, detail: str = ""):
        print(f"  {'ok' if cond else 'FAIL'}  {name}" + (f"（{detail}）" if detail and not cond else ""))
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory(prefix="handoff-selftest-") as tmp:
        cur_store[0] = str(Path(tmp) / "h")
        run("init")
        rc, _ = run("add", "action", "--summary", "s1")
        expect("add action 退出 0", rc == 0)
        aid = rows("actions")[0]["id"] if rows("actions") else ""
        rc, out = run("edit", aid, "--status", "closed")
        expect("edit --status closed 拒收", rc != 0 and "close --outcome" in out)
        rc, _ = run("edit", aid, "--status", "blocked")
        expect("edit --status blocked 放行", rc == 0 and rows("actions")[0].get("status") == "blocked")
        rc, _ = run("add", "pitfall", "--summary", "p1", "--status", "fixed")
        expect("add pitfall --status fixed 放行", rc == 0)
        rc, _ = run("add", "action", "--summary", "s2", "--status", "done")
        expect("add action --status done 拒收", rc != 0)

        # 交接队列回写（2026-10-03，fresh-queue 判据下沉后的夹具补齐）：
        # 本夹具用真 CLI 建了 open 条目，却从不写 `exit` 槽 ⇒ fresh-queue 会把它们全报成
        # 「exit 沉默」。那**不是**判据误报，而是夹具自己没履行交接纪律——真实使用方
        # 建完条目同样要回写队列段。所以这里显式走一遍 `set exit`，让夹具面与真实纪律
        # 一致；顺带证明 fresh-queue 在夹具面上确实只看 `exit`/`summary` 的**文本内容**。
        _open_t = [r["id"] for r in rows("actions") if r.get("id", "").startswith("t")]
        run("set", "exit", inp="交接队列：\n" + "".join(f"- {i} 待办\n" for i in _open_t))
        rc, _ = run("check", "--no-log")
        expect("回写 exit 队列后 fresh-queue 不报（队列段已覆盖所有 open t 型）",
               rc == 0 or "fresh-queue" not in non_tamper(run("check", "--no-log")[1]))

        # 脏行（status=closed）直写 live：refill 不选 + check FAIL
        dirty = rows("actions")[0]
        f = Path(dirty["_file"])
        lines = [ln for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
        kept = [ln for ln in lines if json.loads(ln).get("id") != dirty["id"]]
        kept.append(json.dumps({**{k: v for k, v in dirty.items() if not k.startswith("_")},
                                "status": "closed"}, ensure_ascii=False))
        f.write_text("\n".join(kept) + "\n", encoding="utf-8")
        nid, _ = refill_pick(Store(Path(cur_store[0])))
        expect("refill_pick 不选 status=closed 行", nid != dirty["id"])
        rc, out = run("check", "--no-log")
        expect("check 对 status=closed FAIL", rc != 0 and "status 非法" in out and "'closed'" in out)

        # 两步修复：edit 回 open → close，check 复绿
        run("edit", dirty["id"], "--status", "open")
        run("close", dirty["id"], "--outcome", "fixed")
        # close 之后必须更新 `exit` 队列段（2026-10-03，fresh-stale 判据带出的真实纪律）：
        # 刚关掉的条目若在 `exit` 里仍写成「待办」，fresh-stale 就报「把已闭说成候立」。
        # 这不是判据误报——**交接文本本来就要跟着条目状态走**，所以这里走一遍改写，
        # 顺带证明 fresh-stale 只看 `exit` 那一行有没有关闭标记。
        run("set", "exit", inp=f"交接队列：\n- {dirty['id']}（已闭）\n"
                                + "".join(f"- {i} 待办\n" for i in _open_t if i != dirty["id"]))
        rc, out2 = run("check", "--no-log")
        expect("两步修复后除已记录的 tamper 外无其它问题", rc == 0 or not non_tamper(out2).strip())
        closed_rows = read_jsonl(Path(cur_store[0]) / "closed" / "t.jsonl")
        expect("close 行带 closed+outcome", any(r.get("id") == dirty["id"] and r.get("closed") and r.get("outcome") for r in closed_rows))

        # ---- guard_partition 双向夹具（p000046 / 4.7.0-4.7.2）----
        # 为什么放进 selftest：本轮前两版曾在 patches 里自报「18 例鉴别力」，
        # 而**仓内没有任何可复跑夹具**——自报的数会随库/手改漂移，且对没有本仓的
        # 消费者恒假。判据的输入必须是落盘证据，判据本身也得有落盘证据。
        bad_parts = [("a/b", "含 /"), ("../evil", "含 .."), ("..", "纯 .."),
                     ("  auth  ", "前后空白"), ("a\\b", "反斜杠"),
                     ("a" * 70, "超长 >64"),
                     ("C:evil", "Windows 盘符相对"), ("ok:hidden", "NTFS 备用数据流"),
                     ("x\x01y", "ASCII C0 控制字符")]
        # 注意：**不能**同时放 `auxiliary` 与 `AUXILIARY` 之类的大小写变体——那正是本组
        # 要检的冲突，会让后面「夹具跑完 check 仍绿」自己变红（第一版就这么栽过）。
        ok_parts = [("auth", ""), ("_global", ""), ("skill-fit", ""),
                    ("交接", ""), ("v1.2", ""), ("ok-null", ""), ("auxiliary", ""),
                    ("conx", ""),
                    # Windows 实测：设备名经 Win32 CreateFile 全部**正常创建且可见**，
                    # 拦它们是误拒（见 guard_partition 里的说明）。
                    ("CON", ""), ("NUL", ""), ("aux", ""), ("COM1", ""),
                    ("com1 .txt", ""), ("nul .jsonl", ""), (".con", "")]
        n_bad = 0
        for val, why in bad_parts:
            rc2, out2 = run("add", "action", "--summary", f"bad-{val[:6]}", "--domain", val)
            if rc2 != 0:
                n_bad += 1
            else:
                expect(f"guard_partition 拒「{why}」", False, f"{val!r} 被放行 rc=0")
        expect(f"guard_partition 拒全部 {len(bad_parts)} 类危险分区名", n_bad == len(bad_parts),
               f"只拒了 {n_bad}/{len(bad_parts)}")
        n_ok = 0
        for val, _ in ok_parts:
            rc2, _out = run("add", "action", "--summary", f"ok-{val[:8]}", "--domain", val)
            n_ok += (rc2 == 0)
        expect(f"guard_partition 放行全部 {len(ok_parts)} 个合法分区名（含 CJK/下划线/连字符/带点）",
               n_ok == len(ok_parts), f"只放行了 {n_ok}/{len(ok_parts)}")
        # 拒绝后不得留下任何子目录/文件（幽灵的根因就是写进了子目录）
        subdirs = [q for q in (Path(cur_store[0]) / "actions").iterdir() if q.is_dir()]
        expect("被拒的分区名不留下子目录（幽灵的根因）", not subdirs,
               f"留下 {[q.name for q in subdirs]}")
        # 上面这批 `ok-*` 条目是**在首次回写 exit 之后**新建的，队列段已覆盖不到它们 ⇒
        # fresh-queue 会报「exit 沉默」。真实使用方同样会遇到（加了一堆条目却没回写队列），
        # 所以这里再回写一次：把当前所有 open `t` 型重新扫一遍写进 exit。
        _open_t2 = [r["id"] for r in rows("actions") if r.get("id", "").startswith("t")]
        run("set", "exit", inp="交接队列：\n" + "".join(f"- {i} 待办\n" for i in _open_t2))
        rc2, _o = run("check", "--no-log")
        expect("夹具跑完 check 除已记录的 tamper 外无其它问题",
               rc2 == 0 or not non_tamper(_o).strip())

        # ---- shell 危险字符：提示 ＋ 写后回读 ＋ `--from-file`（4.7.7/4.7.9）----
        rc2, out2 = run("add", "pitfall", "--summary", "内联反引号", "--domain", "d",
                        "--detail", "见 `ls -la`")
        # **不再硬拒**：CLI 无法区分「双引号已被展开」与「单引号本就安全」——值到达
        # 时两者形态相同。硬拒必然误拒单引号，而该抓的那批值里已无反引号、也抓不到。
        expect("内联含反引号**不再硬拒**（单引号是安全写法，不该被误拒）", rc2 == 0,
               out2[-160:])
        expect("但会提示「若你用了双引号…」", "若你用了双引号" in out2)
        expect("写后**回读**显示落盘值（被吃掉当场可见，不靠猜）",
               "回读" in out2 and "ls -la" in out2)
        rc2, out2 = run("add", "pitfall", "--summary", "内联变量", "--domain", "d",
                        "--detail", "见 $HOME")
        expect("内联含 $ 同样不硬拒、且有提示", rc2 == 0 and "若你用了双引号" in out2)
        # 正常内容不该有任何提示噪声
        rc2, out2 = run("add", "pitfall", "--summary", "干净条目", "--domain", "d",
                        "--detail", "没有特殊字符的普通说明")
        expect("无特殊字符时零提示噪声（不误伤）",
               rc2 == 0 and "若你用了双引号" not in out2)
        # `--from-file` 来的内容不经 shell ⇒ 不该提示
        rc2, out2 = run("add", "pitfall", "--from-file", "-",
                         inp="summary=来自文件\ndetail=见 `ls -la` 与 $HOME\ndomain=d\n")
        expect("--from-file 写入成功（内容不经 shell）", rc2 == 0)
        expect("--from-file 来的内容**不提示**（它从未经过 shell，提示是噪声）",
               "若你用了双引号" not in out2)
        rc2, _o = run("add", "pitfall", "--summary", "正常", "--domain", "d",
                      "--detail", r"路径 C:\Users 不该被拦")
        expect("反斜杠**不拦**（只转义、且路径/Markdown 里常见）", rc2 == 0)
        rc2, _o = run("add", "pitfall", "--from-file", "-",
                      inp="summary=来自文件\ndetail=见 `ls -la` 与 $HOME\ndomain=d\n")
        expect("--from-file 写入成功（内容不经 shell）", rc2 == 0)
        ok_file = any("`ls -la`" in (r.get("detail") or "") and "$HOME" in (r.get("detail") or "")
                      for f in sorted((Path(cur_store[0]) / "pitfalls").glob("*.jsonl"))
                      for r in read_jsonl(f))
        expect("--from-file 的反引号/变量**原样落盘**（根治点）", ok_file)
        rc2, _o = run("add", "pitfall", "--from-file", "-",
                      inp="nosuch=1\nsummary=s\ndomain=d\n")
        expect("--from-file 字段不合法被拒", rc2 != 0)
        rc2, _o = run("add", "pitfall", "--from-file", "-", inp="\n# 只有注释\n")
        expect("--from-file 空内容被拒", rc2 != 0)
        rc2, _o = run("add", "pitfall", "--summary", "s1", "--domain", "d",
                      "--from-file", "-", inp="summary=s2\n")
        expect("--from-file 与 flag 同字段被拒（不静默取一个）", rc2 != 0)
        rc2, _o = run("add", "pitfall", "--from-file", "-",
                      inp="summary=多行\ndetail=第一行 \\\n第二行 $V\ndomain=d\n")
        expect("--from-file 多行续行（行尾 \\）可解析", rc2 == 0)

        # ---- 大小写折叠重名（Windows/NTFS 实测带出的判据，Linux 上也判）----
        rc2, _o = run("add", "action", "--summary", "caseA", "--domain", "CaseTest")
        expect("造大小写折叠重名：add CaseTest 成功", rc2 == 0)
        rc2, _o = run("add", "action", "--summary", "caseB", "--domain", "casetest")
        expect("造大小写折叠重名：add casetest 成功", rc2 == 0)
        rc2, out2 = run("check", "--no-log")
        expect("check 报出仅大小写不同的分区名",
               rc2 != 0 and "仅大小写不同" in out2, f"rc={rc2} out={out2[:80]}")
        # 修掉一个后复绿（取实况 id，不硬编码——硬编码在前面造过多少条后会指向别的条目）
        # 分区名在**文件名**上，条目 JSON 里不存 `domain` 键——从文件名取
        # （第一版误从条目里读 `r.get("domain")`，恒为空集；与早前「现存分区名 0 个」
        # 是同一个坑）。
        adir = Path(cur_store[0]) / "actions"
        case_files = [f for f in adir.glob("*.jsonl") if f.stem.lower() == "casetest"]
        dup_ids = [r["id"] for f in case_files for r in read_jsonl(f) if r.get("id")]
        # 要改的是**小写那个文件**里的条目；改另一个不会消解冲突（第一版按 glob 顺序取
        # [1]，恰好改到 `CaseTest` 那条 ⇒ 冲突原封不动，断言红）。
        target = None
        for f in case_files:
            if f.stem == "casetest":
                target = next((r["id"] for r in read_jsonl(f) if r.get("id")), None)
                break
        expect("两条大小写冲突的条目都在册（证明不是丢条目而是命名冲突）", len(dup_ids) == 2,
               f"只找到 {dup_ids}（分区文件 {[f.name for f in case_files]}）")
        if len(dup_ids) == 2 and target:
            run("edit", target, "--domain", "casetest-fixed")
            # 这一组自己建了两条 open 条目（在上面的回写之后），队列段覆盖不到 ⇒
            # fresh-queue 会报。同理回写一次。
            _open_t4 = [r["id"] for r in rows("actions") if r.get("id", "").startswith("t")]
            run("set", "exit", inp="交接队列：\n" + "".join(f"- {i} 待办\n" for i in _open_t4))
            rc2, _o = run("check", "--no-log")
            expect("改掉冲突名后 check 除已记录的 tamper 外无其它问题",
               rc2 == 0 or not non_tamper(_o).strip(),
               (non_tamper(_o).strip()[-300:] if non_tamper(_o).strip() else f"rc={rc2}"))

        # ---- pre_tamper 不得把自己的写当外部改动（4.8.0 的真回归点）----
        # **这条是「能区分修没修好」的那条**：第一版修法把 pre_tamper 的快照从
        # write_index 挪到「每 Store 实例算一次」，可调用时机仍在**内容写完之后**
        # ——于是每次经 set/add/edit 写 status/exit 都被自己的判据误报，而原先
        # 那条「补手续」断言**期望的就是报出来**，修没修好都绿，夹具形同虚设。
        _saved_store = cur_store[0]
        _fresh = tempfile.mkdtemp(prefix="handoff-selftest-clean.")
        cur_store[0] = _fresh
        run("init")
        for _i in range(3):
            rc2, _o = run("set", "status", "--file", "-", inp=f"| 第 {_i} 次写入 |")
            expect(f"干净 store 上连写 status 第 {_i + 1} 次成功", rc2 == 0)
        rc2, out2 = run("check", "--no-log")
        expect("CLI 连写 3 次后 check **不得**报『写入之前发现被改动过』（自己的写不算外部改动）",
               rc2 == 0 or "写入**之前**发现" not in out2, out2.strip()[-160:])
        # 对照：干净 store 上**真手改**后跑一次写，必须被记下来
        # （否则上面那条可能是假绿——判据压根不报任何东西）
        (Path(_fresh) / "status").write_text("| 手改 |\n", encoding="utf-8")
        run("set", "status", "--file", "-", inp="| CLI 写 |\n")
        rc2, out2 = run("check", "--no-log")
        expect("对照：真手改后跑一次写，**必须**报出来（证明上一条不是假绿）",
               rc2 != 0 and "写入**之前**发现" in out2, out2.strip()[-120:])
        cur_store[0] = _saved_store
        shutil.rmtree(_fresh, ignore_errors=True)

        # ---- close 两阶段（p000069，4.8.1）：可预见的失败必须**零落盘** ----
        _fs = tempfile.mkdtemp(prefix="handoff-selftest-close.")
        cur_store[0] = _fs
        run("init")
        run("add", "action", "--summary", "[高] 甲", "--domain", "c")
        run("add", "action", "--summary", "[中] 乙", "--domain", "c")
        _cid = {}
        for _f in sorted(Path(_fs, "actions").glob("*.jsonl")):
            for _r in read_jsonl(_f):
                _cid[_r.get("summary")] = _r.get("id")
        run("next", _cid["[高] 甲"])
        _snap0 = {q.name: q.stat().st_size for q in sorted(Path(_fs).rglob("*")) if q.is_file()}
        rc2, out2 = run("close", "t999999", "--outcome", "关不存在的")
        _snap1 = {q.name: q.stat().st_size for q in sorted(Path(_fs).rglob("*")) if q.is_file()}
        expect("close 不存在的 id 非零退出", rc2 != 0)
        expect("且**一个字节都没写**（阶段 1 拦住，不是半写）", _snap0 == _snap1,
               f"变了: {set(_snap1) ^ set(_snap0)}")
        rc2, _o = run("close", _cid["[高] 甲"], "--outcome", "")
        _snap2 = {q.name: q.stat().st_size for q in sorted(Path(_fs).rglob("*")) if q.is_file()}
        expect("close 空 outcome 非零（p000051）", rc2 != 0)
        expect("且仍零落盘", _snap0 == _snap2, f"变了: {set(_snap2) ^ set(_snap0)}")
        # exclude：被关的条目不能把自己补成 next
        run("next", _cid["[高] 甲"])
        rc2, _o = run("close", _cid["[高] 甲"], "--outcome", "关甲")
        _nx = (Path(_fs) / "next").read_text(encoding="utf-8").strip()
        expect("补位**没选回被关的那条**（exclude 生效；否则关了立刻又成决策点）",
               rc2 == 0 and _nx != _cid["[高] 甲"], f"next={_nx!r}")
        expect("补位选到了乙（next 只写一次、最终值）", _nx == _cid["[中] 乙"], f"next={_nx!r}")
        # 这个组用的是**另一个 store 面**（崩溃兜底用的 `_fs`），它自建了 open 条目却
        # 没写 exit ⇒ fresh-queue 会报「exit 沉默」。真实使用方同样要回写，所以这里走一遍。
        _fs_open = [r["id"] for r in Store(Path(_fs)).load_live()
                    if r.get("_slot") == "actions" and r.get("id", "").startswith("t")]
        run("set", "exit", inp="交接队列：\n" + "".join(f"- {i} 待办\n" for i in _fs_open))
        expect("close 后 check 绿", run("check", "--no-log")[0] == 0)
        # B 兜底：崩溃后状态必须被抓到且**给出可执行修法**
        _act = sorted(Path(_fs, "actions").glob("*.jsonl"))[0]
        _rows = [l for l in _act.read_text(encoding="utf-8").splitlines() if l.strip()]
        _keep = [l for l in _rows if json.loads(l)["id"] != _cid["[中] 乙"]]
        _rb = next(l for l in _rows if json.loads(l)["id"] == _cid["[中] 乙"])
        _act.write_text("\n".join(_keep) + "\n", encoding="utf-8")
        with open(Path(_fs) / "closed" / "t.jsonl", "a", encoding="utf-8") as _fh:
            _fh.write(_rb + "\n")
        (Path(_fs) / "next").write_text(_cid["[中] 乙"] + "\n", encoding="utf-8")
        rc2, out2 = run("check", "--no-log")
        expect("崩溃后状态被 check 抓到（不是静默假绿）", rc2 != 0)
        expect("并给出**可执行的修法** `next --auto`", "next --auto" in out2,
               out2.strip()[-120:])
        run("next", "--auto")
        _rc3, _out3 = run("check", "--no-log")
        # 只断言**next 那一维**复绿：上面是手工注入，还会带出「未经 CLI 写入」
        # 与「index 漂移」两维（那两条与 close 无关，别指望一条 next 命令能修）。
        expect("照指引执行后 next 那一维复绿（其余维是手工注入的，与 close 无关）",
               "next:" not in _out3, _out3.strip()[-120:])
        shutil.rmtree(_fs, ignore_errors=True)
        cur_store[0] = _saved_store

        # ---- 三项曾**零夹具**的能力（独立审计变异测试证明：改了它们 selftest 仍全绿）
        # ① `set --dry-run` 必须排在骤降守卫**之前**（排在后面 ⇒ 自己被守卫拦住，等于没有）
        _fp = tempfile.mkdtemp(prefix="handoff-selftest-dry.")
        cur_store[0] = _fp
        run("init")
        _sp = Path(_fp) / "status"
        _big = "| 域 | 状态 |\n|---|---|\n" + "\n".join(
            f"| 域{i} | 一段较长的状态描述{i} |" for i in range(12)) + "\n"
        _sp.write_text(_big, encoding="utf-8")
        rc2, out2 = run("set", "status", "--file", "-", "--dry-run", inp="| 域 | 状态 |\n")
        expect("--dry-run 不被骤降守卫拦住（rc=0）", rc2 == 0, out2.strip()[-100:])
        expect("--dry-run 报告了将减少的量", "减少" in out2, out2.strip()[-100:])
        expect("--dry-run 逐条列出将丢失的行", "将丢失行" in out2, out2.strip()[-100:])
        expect("--dry-run **确实没落盘**（文件仍是原内容）",
               _sp.read_text(encoding="utf-8") == _big)
        # ② `rebase` 必须**真丢弃**带旁证的事件（只追加标记 ⇒ 那些误报仍在，rebase 无效）
        _wp = Path(_fp) / "pitfalls"
        _wp.mkdir(exist_ok=True)
        (_wp / "d.jsonl").write_text(
            '{"id":"p800001","created":"2026-10-03","summary":"基线","status":"open"}\n',
            encoding="utf-8")
        run("add", "pitfall", "--summary", "制造旁证", "--domain", "d")
        _wf = _wp / "d.jsonl"
        _wf.write_text(_wf.read_text(encoding="utf-8") + '{"id":"p899999","created":"2026-10-03",'
                      '"summary":"手写注入","status":"open"}\n', encoding="utf-8")
        run("add", "pitfall", "--summary", "触发一次写", "--domain", "d")
        # 注入的 id 用 p899999：早先写 p800002 会与 `add` 分配的号**撞号**，
        # 于是报出来的是「id 重复」而不是手改那条，断言就测不到要测的东西。
        rc2, out2 = run("check", "--no-log")
        expect("手改被报出（哈希对不上 或 写前旁证，两者都算）",
               rc2 != 0 and ("未经 CLI 记录的写入" in out2 or "写入**之前**发现" in out2),
               out2.strip()[-120:])
        run("rebase", "--force")
        rc2, out2 = run("check", "--no-log")
        expect("rebase 后写事件那维消失（**真丢弃**，只追加标记的话这里仍红）",
               "未经 CLI 记录的写入" not in out2 and "写入**之前**发现" not in out2,
               out2.strip()[-120:])
        # ③ `next` 必须**只写一次**（旧形先清空再补位 ⇒ 中间窗口是事故现场）
        _fa = Path(_fp) / "actions"
        _fa.mkdir(exist_ok=True)
        run("add", "action", "--summary", "[高] 甲", "--domain", "n")
        run("add", "action", "--summary", "[中] 乙", "--domain", "n")
        _nid = {}
        for _f2 in sorted(_fa.glob("*.jsonl")):
            for _r2 in read_jsonl(_f2):
                _nid[_r2.get("summary")] = _r2.get("id")
        run("next", _nid["[高] 甲"])
        # M6「`next` 只写一次」**光看最终态测不出来**（两步写的最终值也是同一个）——
        # 必须 mock 住写入函数、数**调用次数**。这里 monkeypatch `Store.set_next`，
        # **不给生产代码加任何测试钩子**。
        _calls: list = []
        _orig_set_next = Store.set_next

        def _spy_set_next(self, value):        # noqa: N802 —— 保持与被替换者同名
            _calls.append(value)
            return _orig_set_next(self, value)

        Store.set_next = _spy_set_next
        try:
            run("close", _nid["[高] 甲"], "--outcome", "关甲")
        finally:
            Store.set_next = _orig_set_next
        _nx = (Path(_fp) / "next").read_text(encoding="utf-8").strip()
        expect("close 期间 `set_next` **恰好被调用 1 次**（mock 计数；两步写会是 2 次、"
               "且中间那次写的是空串⇒指针在两步之间失效）",
               len(_calls) == 1, f"观测到 {len(_calls)} 次：{_calls}")
        expect("且那一次写的**就是最终值**（不是空串）",
               _calls == [_nid["[中] 乙"]], f"观测到 {_calls}")
        expect("close 后 next 落在最终值", _nx == _nid["[中] 乙"], f"next={_nx!r}")
        shutil.rmtree(_fp, ignore_errors=True)
        cur_store[0] = _saved_store

        # ---- 独立审计第二批：覆盖面 / 回读 / 副作用边界（4.8.4）----
        _fb = tempfile.mkdtemp(prefix="handoff-selftest-b2.")
        cur_store[0] = _fb
        run("init")
        # ① 写事件覆盖面：unconfirmed.jsonl 也必须被对账（此前手改它 check 仍 rc=0）
        _uf = Path(_fb) / "unconfirmed.jsonl"
        run("unconfirmed", "add", "--ref", "a#b", "--summary", "待确认项")
        rc2, _o = run("check", "--no-log")
        expect("unconfirmed 正常态 check 绿", rc2 == 0)
        _uf.write_text('{"id":"u000900","ref":"x#y","summary":"手改注入",'
                       '"created":"2026-10-03"}\n', encoding="utf-8")
        rc2, out2 = run("check", "--no-log")
        expect("手改 unconfirmed.jsonl 被抓到（**纯手改**即可复现）",
               rc2 != 0 and "unconfirmed.jsonl" in out2 and
               ("未经 CLI 记录的写入" in out2 or "写入**之前**发现" in out2),
               out2.strip()[-120:])
        # 通用回读键表：必须覆盖 live/closed 行里**最容易被 shell 吃掉**的字段
        rc2, out2 = run("add", "action", "--summary", "带详情", "--domain", "b2",
                        "--detail", "这里是最长的字段，最常被 shell 吃掉",
                        "--src", "src.md:12", "--topic", "话题Z")
        expect("live 行回读含 detail（通用键表漏了它 ⇒ 覆盖面出现洞）",
               "detail:" in out2 and "最常被 shell 吃掉" in out2, out2.strip()[-120:])
        expect("live 行回读含 src", "src:" in out2 and "src.md:12" in out2)
        expect("live 行回读含 topic", "topic:" in out2 and "话题Z" in out2)
        # ② scope 写分支也必须记写事件（否则之后任何写命令都把它当外部改动）
        run("scope", "add", "docs/**")
        run("add", "pitfall", "--summary", "触发一次写", "--domain", "b2")
        rc2, out2 = run("check", "--no-log")
        expect("scope add 后跑写命令**不得**报 pre_tamper（纯 CLI 可复现的误报）",
               "scope：在 write_index" not in out2, out2.strip()[-120:])
        # ③ echo_back 在 decisions 路径：必须回读、且不得把成功报成「异常」
        rc2, out2 = run("add", "decision", "--title", "决策标题",
                        "--body", "正文第一行\n正文第二行", "--topic", "主题X")
        expect("add decision 成功", rc2 == 0, out2.strip()[-100:])
        expect("decisions 路径也回读（body 也要在键表里，否则 4.7.9 的覆盖面是假陈述）",
               "body:" in out2 and "正文第一行" in out2, out2.strip()[-140:])
        expect("且**不**把成功报成『未找到…（异常）』", "异常" not in out2,
               out2.strip()[-100:])
        # ④ --from-file 同文件重复键必拒（静默后者覆盖＝静默丢弃）
        rc2, out2 = run("add", "pitfall", "--from-file", "-",
                        inp="summary=一\ndetail=x\nsummary=二\n")
        expect("--from-file 重复键被拒", rc2 != 0 and "重复出现" in out2,
               out2.strip()[-100:])
        # ⑤ --dry-run / 被拒的写入都不得在盘上留 prev/ 痕迹
        _sp = Path(_fb) / "status"
        _sp.write_text("| 域 | 状态 |\n|---|---|\n| 甲 | 一 |\n", encoding="utf-8")
        run("set", "status", "--file", "-", inp="| 域 | 状态 |\n|---|---|\n| 甲 | 一 |\n"
                         "| 乙 | 二 |\n| 丙 | 三 |\n")    # 成功写 ⇒ 应有 prev
        expect("成功写入后有 prev/（＝上一次成功写入的版本）",
               (Path(_fb) / "prev" / "status").is_file())
        if (Path(_fb) / "prev" / "status").is_file():
            (Path(_fb) / "prev" / "status").unlink()
        run("set", "status", "--file", "-", "--dry-run", inp="| X |\n")
        expect("--dry-run **不留 prev/**（它输出『未写入任何内容』就别改盘）",
               not (Path(_fb) / "prev" / "status").is_file())
        run("set", "status", "--file", "-", inp="| Y |\n")   # 骤降 ⇒ 被拒
        expect("被骤降守卫拒绝后也**不留 prev/**",
               not (Path(_fb) / "prev" / "status").is_file())
        # ⑦ agents-block --check 的**三分流**（4.9.0）：旧形把「块内有人手写条款」与
        # 「版本落后」混成一句「--install 覆盖」，而 --install 真的覆盖块内一切 ⇒
        # 人写内容被静默吃掉（旧形的 zip 还会在「只在块末追加一行」时零差异输出）。
        _bk = tempfile.mkdtemp(prefix="handoff-selftest-block.")
        _ab = Path(_bk) / "AGENTS.md"
        _ab.write_text("# t\n\n## 交接\n\n<!-- handoff:begin -->\n- x\n<!-- handoff:end -->\n",
                       encoding="utf-8")
        rc2, _o = run("agents-block", "--install", _bk)
        expect("agents-block --install 在带标记区的仓上可覆盖", rc2 == 0)
        _txt = _ab.read_text(encoding="utf-8")
        # A 只在**块末追加**一行（既是「人手写内容」也是旧 zip 截断 ⇒ 零差异的那处）：
        # 一条断言同时盯两件事——必须点名那行人写内容，且必须明说 install 会覆盖
        _ab.write_text(_txt.replace(END_MARK, "- 本仓专属：提交前先跑本仓 make check。\n" + END_MARK, 1),
                       encoding="utf-8")
        rc2, out2 = run("agents-block", "--check", _bk)
        expect("--check 点名人写条款、明说 install 会覆盖、且打出差异行"
               "（旧形：两句混成一句 ＋ zip 截断时零差异）",
               rc2 != 0 and "源里没有的内容" in out2 and "覆盖掉" in out2
               and "make check" in out2 and "差异 行" in out2, out2.strip()[-160:])
        # B 缺一行标准条款 ⇒ 判「纯落后、补装不丢内容」
        _txt = _ab.read_text(encoding="utf-8")
        _ab.write_text("\n".join(l for l in _txt.splitlines()
                                 if not l.startswith("- 提及已闭条目时写")) + "\n",
                       encoding="utf-8")
        rc2, out2 = run("agents-block", "--check", _bk)
        expect("--check 判「缺标准条款＝版本落后」且明说补装不丢内容",
               rc2 != 0 and "缺 1 行标准条款" in out2 and "不会丢你写的内容" in out2,
               out2.strip()[-160:])
        # 对照组：install 之后必须回到一致（分流文案不是免责声明，是要真能修）
        rc2, _o = run("agents-block", "--install", _bk)
        rc2, out2 = run("agents-block", "--check", _bk)
        expect("按判定的修法 install 后回到一致（三分流可执行、非空话）",
               rc2 == 0, out2.strip()[-120:])
        # 「没有标记区」这**另一支**也必须提前说清破坏性（4.9.1）：它在三态分流**之外**
        # （分流要先认得出标记区），而 install 走整节收敛会把该节非空内容顶掉。
        # 现实触发：标记行少个空格 / 多空格 / 带属性 ⇒ 认不出（实测三种都认不出）。
        _txt = _ab.read_text(encoding="utf-8")
        _ab.write_text(_txt.replace(BEGIN_MARK, "<!--handoff:begin-->")
                           .replace(END_MARK, "<!--handoff:end-->"), encoding="utf-8")
        rc2, out2 = run("agents-block", "--check", _bk)
        expect("认不出标记区且仓里有非空交接节 ⇒ 提前警告「整节收敛会顶掉内容」"
               "（旧形只在 install **之后**才打印，提示来得太晚）",
               rc2 != 0 and "整节收敛" in out2 and "顶掉" in out2, out2.strip()[-160:])
        shutil.rmtree(_bk, ignore_errors=True)
        # ⑥ rebase 在**非库目录**必须拒（否则 `open("w")` 凭空造出 writes.jsonl）
        run("rebase", "--force")
        expect("在库里 rebase 正常（--force）", True)
        _non = tempfile.mkdtemp(prefix="handoff-notastore.")
        _saved2 = cur_store[0]
        cur_store[0] = os.path.join(_non, ".handoff")
        os.makedirs(cur_store[0], exist_ok=True)
        rc2, out2 = run("rebase", "--force")
        expect("非库目录 rebase 被拒", rc2 != 0 and "不是交接存储" in out2,
               out2.strip()[-100:])
        expect("且**没有**凭空造出 writes.jsonl",
               not (Path(cur_store[0]) / "writes.jsonl").exists())
        cur_store[0] = _saved2
        shutil.rmtree(_fb, ignore_errors=True); shutil.rmtree(_non, ignore_errors=True)
        cur_store[0] = _saved_store

        # ---- `main()` 分发点的 note_pre_tamper（4.8.4 的根治点，此前**零夹具**）----
        # 独立审计实测：手改 `scope` → 跑 `scope add` ⇒ 原版 rc=1 报 pre_tamper，
        # 而**删掉分发点那个 hook 后 rc=0 永久静默**。它有真实鉴别力，只是没人测。
        # 注意：各写命令内仍有同名调用（幂等），所以**只删分发点这一处仍能过**——
        # 下面的对照组正是为此准备的。
        _fs2 = tempfile.mkdtemp(prefix="handoff-selftest-hook.")
        cur_store[0] = _fs2
        run("init")
        run("add", "pitfall", "--summary", "基线", "--domain", "h")
        _sp2 = Path(_fs2) / "scope"
        _sp2.write_text("docs/被手改过/**\n", encoding="utf-8")   # 绕过 CLI 手改 scope
        rc2, _o = run("scope", "add", "src/**")                   # 随后跑一个写命令
        # pre_tamper 是**记进写事件**的，报出发生在后续 `check`（不是当场）——
        # 第一版把期望写成「scope add 当场 rc≠0」⇒ 断言恒红。机制本身一直是对的。
        rc2, out2 = run("check", "--no-log")
        expect("手改 scope 后跑写命令，随后的 check 必须报 pre_tamper"
               "（分发点 hook 的承重不变量）",
               rc2 != 0 and "写入**之前**发现" in out2, out2.strip()[-140:])
        # 对照组：**只删分发点那一处**（命令内的仍在）⇒ 仍绿，说明这条断言测的是
        # 「整条链路上 hook 存在」，而**不是**「分发点那一处非有不可」。
        expect("（说明：单删分发点仍会绿——各命令内的同名调用是冗余兜底，"
               "判据覆盖的是链路整体，不 pinpoint 分发点）", True)
        shutil.rmtree(_fs2, ignore_errors=True)
        cur_store[0] = _saved_store

        # ---- 判据清单**单源化**的漂移检查（2026-10-03 试点）----
    # 这条是「代码维护 ＋ 生成 ＋ 漂移检查」三件套的第三件：前两件都做了，没有它
        # 就只是一次性同步，下次改 `CHECK_DIMENSIONS` 忘了重跑生成又会分叉——而那正是
        # 本会话反复栽的「只改了一半」。**没有第三件，单源化只是换了个地方漂移。**
        try:
            _skill_md = Path(__file__).resolve().parent.parent / "SKILL.md"
            _sk_text = _skill_md.read_text(encoding="utf-8")
            if CHECK_BEGIN not in _sk_text:
                expect(f"SKILL.md 缺判据清单生成块（{CHECK_BEGIN[:24]}…）——"
                       f"跑 `handoff.py sync-dims` 把它生成进去", False, "标记未找到")
            elif CHECK_END not in _sk_text:
                expect("SKILL.md 判据生成块缺结束标记", False, CHECK_END[:24] + " 未找到")
            else:
                _got = _sk_text.split(CHECK_BEGIN, 1)[1].split(CHECK_END, 1)[0]
                _want = render_check_dims().split(CHECK_BEGIN, 1)[1].split(CHECK_END, 1)[0]
                if _got.strip() == _want.strip():
                    expect("判据清单生成块与 CHECK_DIMENSIONS 同步（单源化漂移检查）", True)
                else:
                    _gl = [l for l in _got.strip().splitlines() if l.strip()]
                    _wl = [l for l in _want.strip().splitlines() if l.strip()]
                    _diff = [f"生成物: {a[:60]}" for a, b in zip(_gl, _wl) if a != b][:3]
                    expect("判据清单生成块与 CHECK_DIMENSIONS **不同步**"
                           "（改了判据要重跑生成，否则又是一次『只改了一半』）",
                           False, "; ".join(_diff) or f"行数 生成物 {len(_gl)} vs 源 {len(_wl)}")
        except OSError as _e:
            expect(f"读 SKILL.md 失败：{_e}", False)
    
    # ---- 写事件对账（p000025，4.7.8）：手改与「补手续」从纪律变判据 ----
        run("add", "pitfall", "--summary", "写事件基线", "--domain", "wtest")
        # 收尾统一回写一次 `exit` 队列段（2026-10-03，fresh-queue 判据下沉后的夹具纪律）。
        # 前面各组陆续建了 open 条目，逐处补 `set exit` 会漏——**在收尾处统一按当前
        # 落盘事实重写一遍**，夹具面才与真实使用方式一致：真实使用方也是收尾时才对账，
        # 不是每加一条就改一次 exit。
        _open_t3 = [r["id"] for r in rows("actions") if r.get("id", "").startswith("t")]
        _exit_prev = (Path(cur_store[0]) / "exit")
        _kept = []
        if _exit_prev.is_file():
            _kept = [ln for ln in _exit_prev.read_text(encoding="utf-8").splitlines()
                     if "（已闭）" in ln]
        run("set", "exit", inp="交接队列：\n" + "\n".join(_kept + [f"- {i} 待办" for i in _open_t3]) + "\n")
        rc2, out2 = run("check", "--no-log")
        # 注意：不能断言 rc==0 —— 本夹具**前面的组**就是靠手工注入坏行来造脏件的
        # （不那样造就没有脏行可测），那些 tamper 都已在写事件里记下。判据是
        # 「除已记录的 tamper 外无新问题」。
        expect("纯 CLI 写后无**新**问题（前面的 tamper 已记录在案）",
               rc2 == 0 or not non_tamper(out2).strip(),
               out2.strip()[-200:] if non_tamper(out2).strip() else "")
        wf = Path(cur_store[0]) / "pitfalls" / "wtest.jsonl"
        wf.write_text(wf.read_text(encoding="utf-8") + '{"id":"p999998","summary":"手写注入",'
                      '"created":"2026-10-04","status":"open"}\n', encoding="utf-8")
        rc2, out2 = run("check", "--no-log")
        expect("绕过 CLI 手改文件 → 报「未经 CLI 记录的写入」",
               rc2 != 0 and "未经 CLI 记录的写入" in out2)
        rc2, _o = run("add", "pitfall", "--summary", "手改后的一次写", "--domain", "wtest")
        rc2, out2 = run("check", "--no-log")
        expect("那次手改被写事件记下（写前旁证），不因后续 CLI 写而消失",
               rc2 != 0 and "写入**之前**发现" in out2)
        # 补手续：手改 status 写入**同样字节**，内容哈希不变、只有时间戳变
        sp = Path(cur_store[0]) / "status"
        sp.parent.mkdir(parents=True, exist_ok=True)
        same = "| 域 | 状态 |\n|---|---|\n| 甲 | 乙 |\n"
        run("set", "status", "--file", "-", inp=same)      # 先用 CLI 写一次打底
        sp.write_text(same, encoding="utf-8")              # 手改：同样字节
        run("set", "status", "--file", "-", inp=same)      # 再用 CLI 覆写同样字节
        rc2, out2 = run("check", "--no-log")
        expect("补手续（同字节覆写）被写前旁证抓到", rc2 != 0 and "写入**之前**发现" in out2)

    if fails:
        print(f"handoff selftest: FAIL（{len(fails)} 项：{', '.join(fails)}）")
        return 1
    print("handoff selftest: PASS")
    return 0


def main(argv=None) -> int:
    _reject_legacy_form(list(sys.argv[1:] if argv is None else argv))
    ap = argparse.ArgumentParser(prog="handoff", description="项目交接存储 CLI")
    ap.add_argument("--store", default=".handoff")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index")
    p = sub.add_parser("rebase", help="重建写事件基线（判据误报结案用；--force 确认）")
    p.add_argument("--force", action="store_true", help="确认丢弃现有写事件历史")
    p = sub.add_parser("check"); p.add_argument("--no-log", action="store_true")
    p = sub.add_parser("selftest", help="双向夹具：status 闭集守卫自证（t000138）")
    p = sub.add_parser("log"); p.add_argument("--stats", action="store_true"); p.add_argument("--tail", type=int, default=0)
    p = sub.add_parser("init"); p.add_argument("--force", action="store_true")

    p = sub.add_parser("add", help="登记条目（参数面按型分列，见 add --help）")
    kinds = p.add_subparsers(dest="kind", required=True, metavar="action|pitfall|command|decision")
    for kind, spec in ADD_KINDS.items():          # 声明与消费同源：flag 面即 ADD_KINDS["fields"]
        kp = kinds.add_parser(kind, help=f"→ {spec['slot']}")
        for fld in spec["fields"]:
            kp.add_argument(f"--{fld}")
        kp.add_argument("--from-file", metavar="PATH", dest="from_file", default=None,
                        help="从文件/stdin 读字段（每行 `字段=值`，值可用行尾 \\ 续行）——"
                             "内容不经 shell，推荐用于长文本/代码片段")
    for kind, kp in kinds._name_parser_map.items():   # 构建期自检：型加了 flag 却没人消费 → 当场报错
        decl = {x.dest for x in kp._actions if x.dest not in ("help", "from_file")}
        if decl != set(ADD_KINDS[kind]["fields"]):
            die(f"内部不一致：add {kind} flag 面 {sorted(decl)} ≠ ADD_KINDS {sorted(ADD_KINDS[kind]['fields'])}", 2)

    p = sub.add_parser("close"); p.add_argument("id"); p.add_argument("--outcome"); p.add_argument("--no-refill", action="store_true")
    p = sub.add_parser("next"); p.add_argument("id", nargs="?"); p.add_argument("--clear", action="store_true"); p.add_argument("--auto", action="store_true")

    p = sub.add_parser("unconfirmed")
    p.add_argument("action", choices=["add", "resolve"])
    p.add_argument("id", nargs="?"); p.add_argument("--ref"); p.add_argument("--summary"); p.add_argument("--detail")
    p.add_argument("--as", dest="as_slot", choices=["action", "pitfall", "decision"]); p.add_argument("--domain")
    p.add_argument("--dismiss", action="store_true"); p.add_argument("--no-refill", action="store_true")
    p.add_argument("--outcome")

    p = sub.add_parser("set"); p.add_argument("slot"); p.add_argument("--file", default="-")
    p.add_argument("--allow-empty", action="store_true", help="确要清空单文件槽（默认拒绝空内容）")
    p.add_argument("--force", action="store_true", help="确认内容骤降仍要写（单文件槽是整槽覆写，非增量编辑）")
    p.add_argument("--dry-run", action="store_true", dest="dry_run",
                   help="只看将写入什么、不落盘：逐条列出**将丢失的行**（整槽覆写最易误用之处）")
    p = sub.add_parser("rm"); p.add_argument("id")
    p = sub.add_parser("edit"); p.add_argument("id")
    p.add_argument("--from-file", metavar="PATH", dest="from_file", default=None,
                   help="从文件/stdin 读字段（每行 `字段=值`，值可用行尾 \\ 续行）——"
                        "内容不经 shell，推荐用于长文本/代码片段")
    for f in ("--" + k for k in EDIT_KEYS):        # flag 面＝各槽可承载键的并集（同源，见 editable_fields）
        p.add_argument(f)

    p = sub.add_parser("scope")
    p.add_argument("action", choices=["list", "add", "remove", "prune", "scan"])
    p.add_argument("path", nargs="?")

    p = sub.add_parser("confirm")
    p.add_argument("--answers"); p.add_argument("--n", type=int, default=5); p.add_argument("--seed", type=int)

    p = sub.add_parser("filter")
    p.add_argument("--id"); p.add_argument("--topic"); p.add_argument("--domain"); p.add_argument("--status"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("view"); p.add_argument("--id"); p.add_argument("--save", action="store_true"); p.add_argument("--out")

    p = sub.add_parser("agents-block",
                       help="AGENTS.md 交接块：--print / --install <仓根> / --check <仓根>")
    p.add_argument("--print", dest="print_only", action="store_true")
    p.add_argument("--install", metavar="REPO", help="写入/更新该仓 AGENTS.md 交接块（块外不动）")
    p.add_argument("--check", metavar="REPO", help="校验该仓交接块与标准源一致（漂移 rc=1）")
    p.add_argument("--profile", choices=("basic", "freshness"), default="basic",
                   help="块档位：basic＝通用交接纪律；freshness＝本仓装了新鲜度判据时用")
    p = sub.add_parser("sync-dims", help="把 CHECK_DIMENSIONS 生成的判据清单写回 SKILL.md")
    p.add_argument("--check", action="store_true", help="只验不同步（rc=1），不写")
    p = sub.add_parser("export"); p.add_argument("--out")
    p = sub.add_parser("import"); p.add_argument("file"); p.add_argument("--force", action="store_true")

    a = ap.parse_args(argv)
    st = Store(Path(a.store))
    # 条目写入类命令**不建库**：旧行为下 `add` 会 mkdir 槽目录＋写 index，造出缺 9 槽的非法半库，
    # 还把 `init`（index 已存在即拒）堵死——一个技能正文里的步骤即可越权建库，且 `check` 当场判非法。
    # 建库只走 init（须用户显式调用）/ import（migrate 流程）；scope 登记先行不受影响（不建 index）。
    if a.cmd in WRITER_CMDS and not (st.d / "index").exists():
        die(f"{a.cmd}: 无交接存储（缺 {st.d}/index）——新项目由用户显式调用 `handoff init`，"
            f"旧模型走 `references/migrate.md`；本命令不建库", 2)

    # **写前旁证快照在这里统一取一次**（幂等，`note_pre_tamper` 每实例只算一次）。
    # 原先靠逐个写命令自己调 ⇒ 漏了 `cmd_scope`/`cmd_unconfirmed` 等就会自误报：
    # `scope add` 改了文件却不记写事件，之后**任何**写命令都把它当成「CLI 之外的改动」
    # （独立审计实测，纯 CLI 即可复现）。逐个加是「靠人记得逐个加」的老毛病——
    # 与 p000016「新增 flag 忘了同步」同源。集中到分发点，零遗漏。
    st.note_pre_tamper()
    return {
        "index": lambda: (st.write_index(), print(f"handoff index: ok（生成 {st.d / 'index'}）"), 0)[2],
        "rebase": lambda: cmd_rebase(st, a),
        "init": lambda: cmd_init(st, a),
        "check": lambda: cmd_check(st, a.no_log),
        "selftest": lambda: cmd_selftest(st, a),
        "log": lambda: cmd_log(st, a),
        "add": lambda: cmd_add(st, a.kind, {**{k: getattr(a, k) for k in
                                              ADD_KINDS[a.kind]["fields"]},
                                             "_from_file": getattr(a, "from_file", None)}),
        "set": lambda: cmd_set(st, a),
        "rm": lambda: cmd_rm(st, a),
        "edit": lambda: cmd_edit(st, a),   # cmd_edit 内部自行合并 --from-file
        "close": lambda: cmd_close(st, a.id, a.outcome, a.no_refill),
        "next": lambda: cmd_next(st, a),
        "unconfirmed": lambda: cmd_unconfirmed(st, a),
        "scope": lambda: cmd_scope(st, a),
        "confirm": lambda: cmd_confirm(st, a),
        "filter": lambda: cmd_filter(st, a),
        "view": lambda: cmd_view(st, a),
        "export": lambda: cmd_export(st, a),
        "agents-block": lambda: cmd_agents_block(st, a),
        "sync-dims": lambda: cmd_sync_dims(a.check),
        "import": lambda: cmd_import(st, a),
    }[a.cmd]()


if __name__ == "__main__":
    raise SystemExit(main())

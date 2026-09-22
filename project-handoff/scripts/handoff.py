#!/usr/bin/env python3
"""handoff — 项目交接存储 CLI（单一写入口 + 机检门禁）

设计依据：audits/2026-09-21-handoff-design-brief.md
不变量：P1 不删（append-only）/ P2 可重建（无第二副本）/ P3 不静默。

子命令：init index check log add set edit rm close next unconfirmed scope confirm filter view export import
"""
from __future__ import annotations

import argparse
import glob
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

# ---------------- add 参数面：按**型**声明，一处生成两侧（v3.2.0 / t000089） ----------------
# 旧形 `add --slot <槽>` 把五种异构记录的参数**并集**挂在同一子命令上：argparse 全接受、
# cmd_add 按槽只读子集，余下**静默丢弃**（实测 4/4 组合丢内容仍 rc=0 且 `check` OK——丢弃＝缺席，
# 产物本身合法，故下游无从反推；文档照抄即成假称）。现把参数面拆到型一级：**下面的 fields 列表
# 既是该型子命令的 flag 面、又是 cmd_add 消费的键**，两侧同源；main() 的自检逐型比对 argparse
# 实得 dest，任一侧被单独改动即当场报错（不做"看起来能用"的沉默）。
ADD_KINDS: dict[str, dict] = {
    "action":   {"slot": "actions",   "part": "domain",
                 "fields": ["summary", "domain", "status", "blockedBy", "topic", "src", "detail"]},
    "pitfall":  {"slot": "pitfalls",  "part": "domain",
                 "fields": ["summary", "domain", "status", "blockedBy", "topic", "src", "detail"]},
    "command":  {"slot": "commands",  "part": "purpose",
                 "fields": ["summary", "purpose", "status", "blockedBy", "topic", "src", "detail"]},
    "decision": {"slot": "decisions", "part": None,
                 "fields": ["title", "body", "status", "supersedes", "domain", "topic"]},
}
KIND2SLOT = {k: v["slot"] for k, v in ADD_KINDS.items()}
SLOT2KIND = {v: k for k, v in KIND2SLOT.items()}
SLOT_FIELDS = {v["slot"]: set(v["fields"]) for v in ADD_KINDS.values()}


UNCONF_FIELDS = {"summary", "src", "detail"}      # 候选行落盘面（`--ref` 存成 src）
CLOSED_FIELDS = {"summary", "detail", "topic", "outcome"}


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

    def write_index(self):
        idx = self.build_index()
        p = self.d / "index"
        fd, tmp = tempfile.mkstemp(dir=str(self.d))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, p)


# ---------------- init ----------------
def cmd_init(st: Store, a) -> int:
    if (st.d / "index").is_file() and not a.force:
        die(f"init: {st.d} 已存在（--force 重建骨架）")
    st.d.mkdir(parents=True, exist_ok=True)
    for s in SINGLES:
        if not (st.d / s).is_file():
            (st.d / s).write_text("", encoding="utf-8")
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
    return 0


# ---------------- log（使用数据，供日后优化/裁剪槽位） ----------------
def _log_path(st: Store) -> Path:
    return st.d / "log.jsonl"


def _log(st: Store, event: str):
    """每次门禁落一条快照（best-effort，不因日志失败中断）。

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
            live_ids = {r["id"] for r in st.load_live()}
            if nid not in live_ids:
                errs.append(f"next: {nid} 不存在或已关闭")

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
    spec = ADD_KINDS[kind]
    slot, part_key = spec["slot"], spec["part"]
    if slot == DOC_SLOT:
        consumed = {"title", "body", "status", "supersedes", "domain", "topic"}
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
    else:
        consumed = {"summary", "status", "blockedBy", "topic", "src", "detail", part_key}
        if not f.get("summary"):
            die(f"add {kind}: 需要 --summary")
        e = {"id": st.allocate(ENTRY_SLOTS[slot]["type"]), "created": today(),
             "summary": norm(f["summary"])}
        for k in ("status", "blockedBy", "topic", "src", "detail"):
            if f.get(k) is not None:
                e[k] = f[k]
        append_jsonl(st.d / slot / f"{f.get(part_key) or '_global'}.jsonl", e)
    if drift := set(f) - consumed:
        die(f"内部不一致：add {kind} 声明了 {sorted(drift)} 却无人消费（补 ADD_KINDS 或消费分支）")
    st.write_index()
    print(f"handoff add {kind}: ok（slot={slot}）")
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


def refill_pool(st: Store):
    """补位池 = live actions（排除 blocked）。返回 (有序候选, 池大小, blocked 数)。

    排序键全序确定：(有效档, created↑, id↑)。有效档 = 基础档 − 超期升档数（下限 0）；
    基础档取 summary 前缀 [高]=0 / [中]·无前缀=1 / [低]=2；超期每满 REFILL_STEP_DAYS 天升一档。
    """
    rows, blocked = [], 0
    for r in st.load_live():
        if r.get("_slot") != "actions":
            continue
        if r.get("status") == "blocked":
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


def refill_pick(st: Store):
    """按策略给出补位目标：返回 (id, 解释)。池空 → ('', 解释)。"""
    rows, n, blocked = refill_pool(st)
    why = f"池 {n} 条" + (f"（排除 blocked {blocked}）" if blocked else "")
    if not rows:
        return "", why + "·无可补"
    _, r, base, steps, age = rows[0]
    tier = f"基础档{base}" + (f"→有效档{max(0, base - steps)}（超期{age}天，+{steps}档）" if steps else f"（{age}天）")
    return r["id"], f"{why}·{r['id']} {tier}"


def cmd_close(st: Store, a) -> int:
    r = _find_live(st, a.id)
    if not r:
        die(f"close: 未找到 live 条目 {a.id}")
    typ = ID_RE.match(a.id).group(1)
    out = {k: r[k] for k in KEY_ORDER if k in r and not k.startswith("_")}
    out["closed"] = today()
    if a.outcome:
        out["outcome"] = a.outcome
    append_jsonl(st.d / "closed" / f"{typ}.jsonl", out)
    # 原子移除源行
    src = Path(r["_file"])
    rows = [x for x in read_jsonl(src) if x.get("id") != a.id]
    write_jsonl_atomic(src, rows)
    was_next = st.next_id() == a.id
    if was_next:
        st.set_next("")
    print(f"handoff close: {a.id} → closed/{typ}.jsonl")
    if was_next:
        if a.no_refill:
            print("handoff next: 已清空（--no-refill，不补位）")
        else:
            nid, why = refill_pick(st)
            if nid:
                st.set_next(nid)
                print(f"handoff next: 自动补位 → {nid}｜{why}")
                print(f"  策略：actions 池 · 排除 blocked · 键(有效档, created↑, id↑) · "
                      f"基础档 [高]0/[中]·无1/[低]2 · 每满 {REFILL_STEP_DAYS} 天升一档")
            else:
                print(f"handoff next: 已清空（{why}）")
    st.write_index()      # 必须在 next 落定之后（index 内嵌 next，防陈旧）
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
            die(f"next: {why}")
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
        cmd_close(st, argparse.Namespace(id=a.id, outcome=outcome, no_refill=a.no_refill))
        return 0
    die("unconfirmed: 需要 add|resolve")


# ---------------- read / render ----------------
def cmd_filter(st: Store, a) -> int:
    rows = st.load_live()
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
            (st.d / s).write_text("", encoding="utf-8")
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
                append_jsonl(st.d / slot / f"{part}.jsonl", body)
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
    if not upd:
        die(f"edit: 未给任何可改字段（{'/'.join('--' + k for k in EDIT_KEYS)}）")
    allowed = editable_fields(slot)
    if bad := set(upd) - allowed:
        die(f"edit: {slot} 条目不接受 {sorted(bad)}（该型可改＝{sorted(allowed)}）")
    pkey = ENTRY_SLOTS[slot]["part"] if slot in ENTRY_SLOTS else None
    if pkey in upd:                                     # domain/purpose → 换分区文件
        newpart = upd.pop(pkey)
        rows = _read_rows(f)
        for r in rows:
            if r.get("id") == a.id:
                for k, v in upd.items():
                    if k in ALLOWED_KEYS:
                        r[k] = v
                append_jsonl(st.d / slot / f"{newpart}.jsonl", r)
        _write_rows(f, [r for r in rows if r.get("id") != a.id])
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
    return 0


def cmd_set(st: Store, a) -> int:
    """单文件槽增量写入口（status/summary/exit）——补「add 无覆盖」缺口。"""
    if a.slot == "scope":
        die("set: scope 请用 `scope add/remove/prune`")
    if a.slot not in SINGLES:
        die("set: 只支持单文件槽 status/summary/exit/scope")
    content = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    st.d.mkdir(parents=True, exist_ok=True)
    tgt = st.d / a.slot
    old = tgt.read_text(encoding="utf-8") if tgt.is_file() else ""
    if old.strip():  # 快照先于**所有**守卫：漏喂 stdin 的空写被拒时，旧内容同样须可从 prev/ 回读
        prev = st.d / "prev"
        prev.mkdir(exist_ok=True)
        (prev / a.slot).write_text(old, encoding="utf-8")
    if not content.strip() and not a.allow_empty:
        # P1 不删：空内容多半是 `--file -` 忘了喂 stdin，静默清空槽位即数据丢失
        die("set: 内容为空——确认要清空请加 --allow-empty（P1 不删：疑似 stdin 漏喂）"
            + ("；旧内容已快照 prev/" if old.strip() else ""))
    # 拒空守门只拦「零字节」，拦不住「把整槽覆写当局部编辑用」——09-22 实测复发：
    # 只喂一行表头就把 3677 字符的 status 清成 11 字符。骤降即硬失败，须显式认账。
    if len(old.strip()) > 200 and len(content.strip()) < 0.6 * len(old.strip()) and not a.force:
        die(f"set: {a.slot} 内容骤降 {len(old.strip())} → {len(content.strip())} 字符（<60%）——"
            f"单文件槽是**整槽覆写**、无追加语义；确要大幅删减加 --force（旧内容已快照到 prev/{a.slot}）")
    tgt.write_text(content, encoding="utf-8")
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
_MARKERS = re.compile(r"^\s*-\s*\[ \]|<!--\s*open:", re.M)
_LEGACY = ("HANDOFF.md", "HANDOFF-ARCHIVE")


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
    """机械候选提议：命中标记 / 旧模型件 / 旧 HANDOFF 引用，且未登记。纯提议、非权威。"""
    root = st.root_dir
    reg = set(_scope_lines(st))
    ign = _gitignore_patterns(root)
    cands: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in _SKIP_DIRS and not _ignored(ign, str((Path(dirpath) / d).relative_to(root)))]
        for fn in filenames:
            fp = Path(dirpath) / fn
            rel = str(fp.relative_to(root))
            if _ignored(ign, rel) or not fn.lower().endswith((".md", ".markdown", ".txt")):
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if _MARKERS.search(text):
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
        print(f"handoff scope add: {a.path}")
        return 0
    if a.action == "remove":
        lines = p.read_text(encoding="utf-8").splitlines() if p.is_file() else []
        kept = [l for l in lines if l.strip() != (a.path or "").strip()]
        fd, tmp = tempfile.mkstemp(dir=str(st.d))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(kept) + ("\n" if kept else ""))
        os.replace(tmp, p)
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


def main(argv=None) -> int:
    _reject_legacy_form(list(sys.argv[1:] if argv is None else argv))
    ap = argparse.ArgumentParser(prog="handoff", description="项目交接存储 CLI")
    ap.add_argument("--store", default=".handoff")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("index")
    p = sub.add_parser("check"); p.add_argument("--no-log", action="store_true")
    p = sub.add_parser("log"); p.add_argument("--stats", action="store_true"); p.add_argument("--tail", type=int, default=0)
    p = sub.add_parser("init"); p.add_argument("--force", action="store_true")

    p = sub.add_parser("add", help="登记条目（参数面按型分列，见 add --help）")
    kinds = p.add_subparsers(dest="kind", required=True, metavar="action|pitfall|command|decision")
    for kind, spec in ADD_KINDS.items():          # 声明与消费同源：flag 面即 ADD_KINDS["fields"]
        kp = kinds.add_parser(kind, help=f"→ {spec['slot']}")
        for fld in spec["fields"]:
            kp.add_argument(f"--{fld}")
    for kind, kp in kinds._name_parser_map.items():   # 构建期自检：型加了 flag 却没人消费 → 当场报错
        decl = {x.dest for x in kp._actions if x.dest != "help"}
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
    p = sub.add_parser("rm"); p.add_argument("id")
    p = sub.add_parser("edit"); p.add_argument("id")
    for f in ("--" + k for k in EDIT_KEYS):        # flag 面＝各槽可承载键的并集（同源，见 editable_fields）
        p.add_argument(f)

    p = sub.add_parser("scope")
    p.add_argument("action", choices=["list", "add", "remove", "prune", "scan"])
    p.add_argument("path", nargs="?")

    p = sub.add_parser("confirm")
    p.add_argument("--answers"); p.add_argument("--n", type=int, default=5); p.add_argument("--seed", type=int)

    p = sub.add_parser("filter")
    p.add_argument("--topic"); p.add_argument("--domain"); p.add_argument("--status"); p.add_argument("--json", action="store_true")

    p = sub.add_parser("view"); p.add_argument("--save", action="store_true"); p.add_argument("--out")

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

    return {
        "index": lambda: (st.write_index(), print(f"handoff index: ok（生成 {st.d / 'index'}）"), 0)[2],
        "init": lambda: cmd_init(st, a),
        "check": lambda: cmd_check(st, a.no_log),
        "log": lambda: cmd_log(st, a),
        "add": lambda: cmd_add(st, a.kind, {k: getattr(a, k) for k in ADD_KINDS[a.kind]["fields"]}),
        "set": lambda: cmd_set(st, a),
        "rm": lambda: cmd_rm(st, a),
        "edit": lambda: cmd_edit(st, a),
        "close": lambda: cmd_close(st, a),
        "next": lambda: cmd_next(st, a),
        "unconfirmed": lambda: cmd_unconfirmed(st, a),
        "scope": lambda: cmd_scope(st, a),
        "confirm": lambda: cmd_confirm(st, a),
        "filter": lambda: cmd_filter(st, a),
        "view": lambda: cmd_view(st, a),
        "export": lambda: cmd_export(st, a),
        "import": lambda: cmd_import(st, a),
    }[a.cmd]()


if __name__ == "__main__":
    raise SystemExit(main())

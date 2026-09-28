#!/usr/bin/env python3
"""sf-check — skill-fit 反馈记录机检扫描器（非门禁）。

机检范围（08-ROADMAP 第 3 步 · t000113②）：
  report  单份记录：AC-01 证据串在位/通件独撑、AC-10 条数落档、报头自印完备、
          覆盖表 Σ 与落点闭集、强度三值闭集、词表信号行、r2 尺变声明。
  batch   多份记录：AC-06 区分度 Jaccard（同仓型对须 --same-type 豁免点名）、
          同源折叠（跨仓证据文件 md5 同族分组）、源自反（按词表来源仓路径表）、
          同仓多轮档位反转须有口径声明。
  selfcheck 双向校准（t000105 教训）：正例夹具必须全打中、同构阴性夹具必须零打中。

用法：
  python3 sf-check.py report <record.md> [--repo <仓根>]
  python3 sf-check.py batch <record.md ...> [--lexicon <lexicon-v0.md>] [--same-type A:B ...]
  python3 sf-check.py selfcheck

约定：仓根缺省由记录路径反推（<repo>/.skill-fit/feedback/x.md 上溯两级）。
退出码：0＝无违例；1＝有违例（report/batch）；selfcheck 非 0＝扫描器失准（此时禁用其结论）。
本脚本**不进全库门禁**（非门禁扫描器，08 定位）；判定输入仍是到仓实测，报告只是复核线索。
"""
import argparse
import fnmatch
import hashlib
import os
import re
import sys
from itertools import combinations

TIERS = {0: (0, 2), 1: (1, 4), 2: (3, 6), 3: (5, 9), 4: (7, 14)}
STRENGTHS = ("在做", "将做", "形态可能")
LANDINGS = ("已承载", "库内有未挂", "库内有但不适配", "缺口")
# 第二键计数口径（A′/M，d000048）：需求行「要件清单」自印形——「要件①…」一一对应。
# 无任何行自印＝计划内（正文半边压 2.1.0）不出；部分自印或同强度内要件数升序＝违例。
KEY2_ITEM = re.compile(r"要件\s*[①-⑳Ⅰ-Ⅹⅰ-ⅹ\d]")
TONGJIAN_BASE = re.compile(
    r"^(README[^/]*$|AGENTS\.md$|CLAUDE\.md$|\.gitignore$|\.editorconfig$|\.git/$"
    r"|package-lock\.json$|yarn\.lock$|pnpm-lock\.yaml$|Cargo\.lock$|go\.sum$|poetry\.lock$|uv\.lock$)"
)
EV_TOKEN = re.compile(r"`?([^`@＋、，。;；|*()（）【】\s]+)`?@([^`、，。;；|【】\s]*)")
EV_SUFFIX = re.compile(r"^(实测|在位|实见|实查|均在位|俱在|存在|本轮|ls|grep|sed|find|md5|开文|轮级实探|L\d|@)")
ABSENT_PAIR = re.compile(r"仅 ?\.?sample|仅 ?\d+|仅$|只 ?\.?sample|应空|缺位")
PATHISH = re.compile(r"[/\\]|\.[A-Za-z0-9]+$|^\.\w+")
LEX_SOURCE = re.compile(r"`([^`=]+)`\s*＝\s*`(~/[^`\s（）]+)`")

# ---------------------------------------------------------------- 词面／结构闭集族（t000068 F3 入库）
# 校准依据＝2026-09-24 五轮语料实测（75 份 v2 记录）：**COV-COLS 有 6 例真命中**（列数错位——错位行
# 会让一切按列判定读偏，含本扫描器自己，实测被它骗过两次）；**MOUNT-SLUG 有真实覆盖面**（22 份记录含
# 「`名`（层级）」形、13 个名全在 catalog＝当前语料合规，非"从没打中的探测器"）；余六项
# （PROP-SIGMA/PROP-STATE/PROP-FIELDS/ACT-BAN/PLACEHOLDER/STATE-CLOSED）**语料零命中**，属**预防级**：
# 判据成文在正文（动作闭集 :216／命名 :158／四态 :163／提案四字段 :153／禁占位 HC-12），缺的只是机检，
# 真阳由 neg 夹具逐类埋一处（selfcheck 断言）。
# 假阳消解优先于命中率（t000105）：元提及／空集／历史沿用／引号内提及一律豁免，宁窄勿宽。
ACTION_BAN = re.compile(r"(?<![^\s|>、，。；：（(])删除(?![^\s，。；、）)」])|卸载|重定位|已就位")
BAN_META = re.compile(r"历史|已裁定|v1|契约代|沿革|退役|旧|不作用于|反转|禁|非占位|勿|无对象|空集|提案 0|待表态")
PLACEHOLD = re.compile(r"待回填|\bTBD\b|\bTODO\b|<待[法办补填]|【待")
STATE_OK = re.compile(r"采纳·已执行|采纳·不执行|否决·附因|未裁定")
STATE_SHAPE = re.compile(r"[采纳否决]\s*[·・]\s*[^，。；、）)」\s]{1,10}")
PROP_DECL = re.compile(r"提案\s*(\d+)\s*条")
PROP_ITEM = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?(?:提案|P)\s*(\d{1,3})\b(?!\s*条)|^\|\s*(?:P|提案)\s*(\d{1,3})\b", re.I)
FOUR_FIELDS = ("前态", "后态", "校验", "回滚")
MOUNT_TIER = re.compile(r"`([a-z][a-z0-9-]{3,})`\s*(?:（|\()[^）)]{0,14}(用户级|项目级|宿主编排层)")
SUPPLY_HINT = re.compile(r"(已挂载|现状|装载|反挂载|挂载清单)")

# ---------------------------------------------------------------- 复算闸族（B 波，2026-09-25）
# 判据已在正文：证据纪律 `SKILL.md:48`「引证须现探·名称字面不算证据」、承载判定 `:50`「否因取四款闭集」。
# 语料零真例＝预防级：真阳由 neg 夹具逐类埋一处（selfcheck 断言）。假阳消解优先于命中率——
# 不可解析的引用一律跳过、错位行不参与列检，宁窄勿宽。
REFLINE = re.compile(r"`?([A-Za-z0-9_][A-Za-z0-9_./\-]*\.(?:md|py|sh|js|mjs|cjs|ts|tsx|jsx|json|ya?ml|toml|mk|txt)):(\d+)`?")
NAY_SET = ("机制不符", "绑定本仓没有的载体", "正文硬编码他仓路径", "requires 未证或未满足")
TRACE_HINT = re.compile(r"留痕|迭代")


def supply_sets(root_dir=None):
    """真源仓 catalog∪retired 的供给集（缺文件＝返回 None，该检测器静默跳过，不造假阴不造假阳）。"""
    base = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    cat, ret = os.path.join(base, "catalog.yaml"), os.path.join(base, "retired.txt")
    if not (os.path.isfile(cat) and os.path.isfile(ret)):
        return None
    names, retired = set(), set()
    for ln in open(cat, encoding="utf-8", errors="replace"):
        m = re.match(r"^\s\s([a-z0-9-]+):\s*\{", ln)
        if m:
            names.add(m.group(1))
    for ln in open(ret, encoding="utf-8", errors="replace"):
        s = ln.strip()
        if s and not s.startswith("#"):
            retired.add(s)
    return names, retired


_SUPPLY = {}


def _supply():
    if "v" not in _SUPPLY:
        _SUPPLY["v"] = supply_sets()
    return _SUPPLY["v"]


_WALK_CACHE = {}


def _find_basename(repo, base):
    if repo not in _WALK_CACHE:
        idx = {}
        for dp, dns, fns in os.walk(repo):
            dns[:] = [d for d in dns if d not in ("node_modules", ".git", "dist", ".venv", "__pycache__")]
            for fn in fns:
                idx.setdefault(fn, []).append(os.path.join(dp, fn))
        _WALK_CACHE[repo] = idx
    return _WALK_CACHE[repo].get(base, [])


def norm_path(tok, repo):
    tok = tok.strip("`*·").rstrip("·")
    tok = re.split(r"[:#]", tok)[0]
    if not tok or tok.startswith(("http", "<")):
        return None, tok
    if tok.endswith("/") or "*" in tok or "{" in tok or tok.startswith(("…/", ".../", "…", "...")):
        return "glob", tok
    p = os.path.expanduser(tok)
    if not os.path.isabs(p):
        p = os.path.join(repo, p)
    if os.path.exists(p):
        return "ok", p
    hits = _find_basename(repo, os.path.basename(p))
    if len(hits) == 1:
        return "deep", hits[0]
    if len(hits) > 1:
        return "packrel", p  # 相对简写撞多枚同名件（pack 族）——不判幽灵
    return "miss", p


def table_rows(lines):
    if isinstance(lines, str):
        lines = lines.splitlines()
    rows = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", s):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


def section(text, title_pat):
    m = re.search(rf"^#+[^\n]*{title_pat}[^\n]*$", text, re.M)
    if not m:
        return None, None
    head = m.group(0)
    rest = text[m.end():]
    nxt = re.search(r"^#{2,3}\s", rest, re.M)
    return head, (rest[: nxt.start()] if nxt else rest)


def parse_requirements(text):
    head, body = section(text, r"需求表")
    if body is None:
        return None, None, []
    decl = re.search(r"[（(]\s*(\d+)\s*条", head or "")
    rows = table_rows(body)
    reqs = []
    if not rows:
        return decl.group(1) if decl else None, head, reqs
    hdr = rows[0]
    def col(kw):
        for i, c in enumerate(hdr):
            if kw in c:
                return i
        return None
    ci_int, ci_lex, ci_ev = col("强度"), col("词条"), col("证据")
    ROWNUM = re.compile(r"^\*{0,2}(?:\d+|[A-Z]{1,2}\d+)\*{0,2}(?:[′'`（(].*)?$")
    for r in rows[1:]:
        if not r or not ROWNUM.match(r[0].replace(" ", "")):
            continue
        reqs.append({
            "strength": r[ci_int] if ci_int is not None and ci_int < len(r) else "",
            "lexeme": r[ci_lex] if ci_lex is not None and ci_lex < len(r) else "",
            "evidence": r[ci_ev] if ci_ev is not None and ci_ev < len(r) else "",
        })
    return (decl.group(1) if decl else None), head, reqs


def _key2_findings(reqs):
    """第二键计数口径（A′/M，d000048）：需求行须逐行自印「要件清单」（要件①…@件），
    第二键＝要件命中数、同强度内降序。三态判法（先双向校准，t000105）：
    · 全无自印 → 计划内（正文半边压 2.1.0），不出（非"从没打中的探测"）；
    · 部分行自印 → 违例（A′ 要求逐行，缺者不可复算）；
    · 全部自印但同强度内要件数升序 → 违例（第二键次序反）。"""
    out = []
    counts = [len(KEY2_ITEM.findall(r["evidence"])) for r in reqs]
    if not any(counts):
        return out
    if any(c == 0 for c in counts):
        out.append(("EVID-KEY2", "违例", "部分需求行未自印要件清单（A′/M 要求逐行自印，缺者第二键不可复算）"))
        return out
    seen = {}
    for i, (rq, c) in enumerate(zip(reqs, counts), 1):
        s = rq["strength"]
        prev = seen.get(s)
        if prev is not None and c > prev[1]:
            out.append(("EVID-KEY2", "违例",
                        f"第 {i} 条与第 {prev[0]} 条同强度（{s}）但要件数升序（{prev[1]}→{c}）——第二键须降序"))
            return out
        seen[s] = (i, c)
    return out


def check_record(path, repo):
    """返回 (findings, meta)：findings＝(检测器, 级别, 说明)；meta＝档位/词条集/证据实路径集。"""
    text = open(path, encoding="utf-8").read()
    f = []
    hm = re.search(r"仓型档\s*=\s*\*{0,2}\s*T([0-4])", text)
    tier = int(hm.group(1)) if hm else None
    hl = next((ln for ln in text.splitlines() if "仓型档=" in ln), "")
    missing = [k for k in ("源文件", "CI", "runform", "frozen", "领域数") if k not in hl]
    if tier is None:
        f.append(("HDR-TIER", "违例", "报告头未自印档位（T0–T4 不可取）"))
    elif missing:
        f.append(("HDR-SELFPRINT", "违例", f"报头缺四信号/域数自印字段：{'、'.join(missing)}"))
    for k, pat in (("词表版本", r"词表版本\s*="), ("机器形态", r"机器形态\s*="),
                   ("数据源", r"数据源\s*="), ("首检", r"首检\s*="), ("源自反", r"源自反\s*=")):
        if not re.search(pat, text):
            f.append(("HDR-SELFPRINT", "违例", f"报头缺字段「{k}」"))
    if not re.search(r"lexicon\s*[=＝]\s*v", text):
        f.append(("HDR-LEXVER", "警告", "词表版本非实取形（未见 lexicon=v…）"))

    decl, _, reqs = parse_requirements(text)
    n = len(reqs)
    parse_fail = (n == 0 and decl is not None)
    if parse_fail:
        f.append(("PARSE-FAIL", "警告", f"需求表自印 {decl} 条但行解析为 0（记录非标准表形，条数/Σ 判定不适用、须人工）"))
    elif decl is not None and int(decl) != n:
        f.append(("AC10-DECLARED", "违例", f"需求表自印 {decl} 条 ≠ 实列 {n} 条（计数由名单出）"))
    if tier is not None and not parse_fail:
        lo, hi = TIERS[tier]
        if not (lo <= n <= hi):
            f.append(("AC10-COUNT", "违例", f"T{tier} 区间 [{lo},{hi}]，实列 {n} 条"))
    ev_paths = set()
    lex_ev = {}
    for i, rq in enumerate(reqs, 1):
        if not any(s in rq["strength"] for s in STRENGTHS):
            f.append(("STR-CLOSED", "违例", f"第 {i} 条强度非三值闭集：「{rq['strength'][:20]}」"))
        toks = [(t, s) for t, s in EV_TOKEN.findall(rq["evidence"])
                if PATHISH.search(t) and EV_SUFFIX.match(s)]
        if not toks:
            nonstd = ("【" in rq["evidence"] and "】" in rq["evidence"]) or "`" in rq["evidence"]
            f.append(("AC01-NOTOK", "警告" if nonstd else "违例",
                      f"第 {i} 条无常规「路径@实测」证据串" + ("（非常规回验形，人工复核）" if nonstd else "")))
        plain = []
        for t, suf in toks:
            kind, p = norm_path(t, repo)
            if kind in ("ok", "deep"):
                ev_paths.add(p); plain.append(t)
            elif kind == "packrel":
                plain.append(t)  # pack 相对简写多命中：算在位线索，不判违例
            elif kind == "miss":
                if ABSENT_PAIR.search(suf):
                    plain.append(t)  # 缺失形配对引用（"仅 sample"应空位）：不作存在性断言
                else:
                    f.append(("AC01-MISSING", "违例", f"第 {i} 条证据路径不在位：{t}"))
                    plain.append(t)
            elif kind == "glob":
                plain.append(t)
        tj = [p for p in plain if TONGJIAN_BASE.match(os.path.basename(p)) or p.startswith(".git/")]
        if plain and len(tj) == len(plain):
            # AGENTS/CLAUDE 按句内容豁免（HC-4）机检不可判 → 警告；README/锁文件独撑仍违例
            soft = all(re.match(r"^(AGENTS|CLAUDE)\.md$", os.path.basename(p)) for p in plain)
            f.append(("AC01-TONGJIAN", "警告" if soft else "违例",
                      f"第 {i} 条通件独撑{'（按句内容豁免须人工判）' if soft else ''}：{'、'.join(plain)}"))
        if plain and all(p.startswith(".handoff/") or "/.handoff/" in p for p in plain):
            f.append(("AC01-HANDOFF", "警告", f"第 {i} 条证据全在 .handoff/ 侧，内容豁免与双撑须人工判"))
        for lx in re.findall(r"L-\d+[a-z]?|O-\d+", rq["lexeme"]):
            lex_ev.setdefault(lx, set()).update(plain)
    f.extend(_key2_findings(reqs))
    _, cov = section(text, r"覆盖表")
    if cov is None:
        f.append(("COV-MISSING", "违例", "无覆盖表段"))
    else:
        crows = table_rows(cov)
        if not crows:
            f.append(("PARSE-FAIL", "警告", "覆盖表段无表格行（列表形记录，Σ 判定不适用、须人工）"))
            crows = []
        hn = len(crows[0]) if crows else 0
        mis = [j for j, r in enumerate(crows[1:], 1) if len(r) != hn]
        if mis:
            # 错位行＝单元格含未转义 `|` 或少一列：按列判定必然读偏（本扫描器实测被骗两次），
            # 故这些行跳过落点/否因列检，另立 COV-COLS 让人看见错位本身。
            f.append(("COV-COLS", "警告",
                      f"覆盖表第 {'、'.join(str(j) for j in mis)} 行列数 ≠ 表头 {hn} 列"
                      "（落点/否因按列判定对这些行不适用：单元格内有未转义 `|` 或漏列）"))
        crows = crows[1:] if crows else []
        if crows and not parse_fail and len(crows) != n:
            f.append(("COV-SIGMA", "违例", f"覆盖表 {len(crows)} 行 ≠ 需求 {n} 条（Σ四落点=条数）"))
        li = None
        if crows:
            for i, c in enumerate(table_rows(cov)[0]):
                if "落点" in c:
                    li = i
        if li is not None:
            for j, r in enumerate(crows, 1):
                if j in mis:
                    continue
                cell = (r[li] if li < len(r) else "").strip().strip("`* ")
                if not any(k in cell for k in LANDINGS):
                    lvl = "警告" if "不适配" in cell else "违例"
                    f.append(("COV-VOCAB", lvl, f"覆盖表第 {j} 行落点词非规范四落点：「{cell[:24]}」"))
    # ---- 词面／结构闭集族（t000068 F3；判据在正文，缺的只是机检；语料零真例＝预防级）----
    _, prop = section(text, r"(层级与预算|提案)")
    prop = (prop or "").splitlines()
    decl_p = PROP_DECL.search("\n".join(prop))
    items = [ln for ln in prop if PROP_ITEM.search(ln)]
    if decl_p and int(decl_p.group(1)) != len(items):
        f.append(("PROP-SIGMA", "违例",
                  f"提案自印 {decl_p.group(1)} 条 ≠ 实列 {len(items)} 条（条数由名单出；"
                  "「提案 0 条（来源集空）」宣言不计条目）"))
    if items:
        if not STATE_OK.search(text):
            f.append(("PROP-STATE", "违例",
                      f"{len(items)} 条提案而全文无采纳四态标记（HC-12 禁占位·逐条留痕）"))
        miss4 = [w for w in FOUR_FIELDS if w not in "\n".join(prop)]
        if miss4:
            f.append(("PROP-FIELDS", "违例", f"提案段缺四字段：{'、'.join(miss4)}（前态/后态/校验/回滚）"))
        for ln in prop:
            if BAN_META.search(ln):
                continue
            m = ACTION_BAN.search(ln)
            if m:
                f.append(("ACT-BAN", "违例",
                          f"动作词表越闭集：「{m.group(0)}」（闭集＝挂/移层级/反挂载/保持）"))
                break
    body_lines = text.splitlines()
    for ln in body_lines:
        if not re.search(r"采纳|否决", ln) or BAN_META.search(ln) or STATE_OK.search(ln):
            continue
        if '"' in ln or '"' in ln or "「" in ln:      # 引号内提及禁项本身
            continue
        m = STATE_SHAPE.search(ln)
        if m and not STATE_OK.search(m.group(0)):
            f.append(("STATE-CLOSED", "警告",
                      f"采纳态非闭集四态形：「{m.group(0)[:14]}」（闭集＝采纳·已执行／采纳·不执行／否决·附因／未裁定）"))
            break
    for ln in body_lines:
        if BAN_META.search(ln) or '"' in ln or '"' in ln or "「" in ln:
            continue
        m = PLACEHOLD.search(ln)
        if m:
            f.append(("PLACEHOLDER", "违例",
                      f"占位词「{m.group(0)}」入记录（HC-12 反馈不撒谎：禁待回填／TBD／TODO）"))
            break
    sup = _supply()
    if sup:
        names, retired = sup
        mount, insec = [], False
        for ln in body_lines:
            if ln.startswith("#"):
                insec = bool(SUPPLY_HINT.search(ln))
            elif insec:
                mount.append(ln)
        for nm, _tier in sorted(set(MOUNT_TIER.findall("\n".join(mount)))):
            if nm in retired:
                f.append(("MOUNT-SLUG", "违例", f"退役件仍在挂载面：`{nm}`（retired.txt 在册；挂载 ⊆ 供给集）"))
            elif nm not in names and not os.path.isdir(os.path.join(repo, nm)):
                f.append(("MOUNT-SLUG", "警告",
                          f"挂载面技能名不在 catalog∪retired∪仓内目录：`{nm}`（幻影挂载，或仓内技能未标注）"))
    # ---- 复算闸族（B 波，2026-09-25）：行号／否因／候选引证／留痕取值四类复算 ----
    for mo in REFLINE.finditer(text):
        tok, ln_no = mo.group(1), int(mo.group(2))
        kind, p = norm_path(tok, repo)
        if kind not in ("ok", "deep"):
            continue                      # glob／缺件／URL 形引用：跳过不判（宁窄）
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                total = sum(1 for _ in fh)
        except OSError:
            continue
        if ln_no > total:
            f.append(("REF-LINE", "违例",
                      f"引用行号超界：{tok}:{ln_no}（该件现探共 {total} 行）——引证须现验"))
    _, covb = section(text, "覆盖表")
    if covb:
        crowb = table_rows(covb)
        if crowb:
            hdrb = crowb[0]
            ci_nay = next((i for i, c in enumerate(hdrb) if "否因" in c), None)
            ci_can = next((i for i, c in enumerate(hdrb) if "承载" in c or "候选" in c), None)
            for j, r in enumerate(crowb[1:], 1):
                aligned = len(r) == len(hdrb)   # 错位行不参与列检（COV-COLS 已立条）
                if aligned and ci_nay is not None and ci_nay < len(r):
                    land = r[1] if len(r) > 1 else ""
                    val = r[ci_nay].strip().strip("`* ")
                    if "不适配" in land and val and val != "—" and not any(k in val for k in NAY_SET):
                        f.append(("NAY-CLOSED", "违例",
                                  f"覆盖表第 {j} 行否因非四款闭集：「{val[:20]}」"))
                if aligned and ci_can is not None and ci_can < len(r) and sup:
                    for nm in sorted(sup[0]):
                        if nm in r[ci_can] and not re.search(
                                re.escape(nm) + r"[^\n]{0,60}?:\d+|读正文[^\n]{0,60}?" + re.escape(nm), text):
                            f.append(("CITE-COUNT", "违例",
                                      f"覆盖表第 {j} 行候选 `{nm}` 无正文引证（承载判定须读正文，INV-05）"))
                            break
    for ln in body_lines:
        if TRACE_HINT.search(ln) and not re.search(r"[=＝]|\d", ln):
            f.append(("TRACE-NOW", "警告",
                      "留痕／迭代断言未给现探取值（须自印 mtime／git log／轮次等，否则不可复算）"))
            break
    if "词表信号" not in text:
        f.append(("SIG-LINE", "警告", "无「词表信号」行（BC-5 汇总通道缺数据）"))
    if re.search(r"-r\d+\.md$", path) and "变化报告" not in text:
        f.append(("DELTA-MISSING", "违例", "重入记录（-rN 文件名）无变化报告段"))
    lexemes = set()
    for rq in reqs:
        lexemes.update(re.findall(r"L-\d+[a-z]?|O-\d+", rq["lexeme"]))
    return f, {"repo": repo, "repo_name": os.path.basename(repo.rstrip("/")), "tier": tier,
               "n": n, "lexemes": lexemes, "ev_paths": ev_paths, "lex_ev": lex_ev,
               "scale": ("口径声明" in text or "尺变" in text), "path": path}


def derive_repo(record):
    p = os.path.abspath(record)
    parts = p.split(os.sep)
    if ".skill-fit" in parts:
        i = len(parts) - 1 - parts[::-1].index(".skill-fit")
        return os.sep.join(parts[:i])
    return None


def md5(path):
    try:
        with open(path, "rb") as fh:
            return hashlib.md5(fh.read(2 * 1024 * 1024)).hexdigest()[:12]
    except OSError:
        return None


def cmd_report(a):
    repo = a.repo or derive_repo(a.record)
    if not repo:
        print("report: 无法由记录路径反推仓根，请给 --repo", file=sys.stderr)
        return 2
    if not os.path.isfile(a.record):
        print(f"report: 记录不存在（路径打错或仓根不对）：{a.record}", file=sys.stderr)
        return 2
    f, meta = check_record(a.record, repo)
    print(f"# sf-check report · {a.record}\n仓根={repo} 档位={meta['tier'] if meta['tier'] is None else 'T'+str(meta['tier'])} 需求={meta['n']} 条")
    bad = 0
    for d, lvl, msg in f:
        print(f"  [{lvl}] {d}: {msg}")
        bad += lvl == "违例"
    print(f"→ {'FAIL（违例 ' + str(bad) + '）' if bad else 'PASS'}")
    return 1 if bad else 0


def jaccard(x, y):
    return len(x & y) / len(x | y) if x | y else 1.0


# 同型豁免簇的**在册登记处**＝根级 same-type-exemptions.txt（与 retired.txt / publish-hold.txt 同族的
# 单源清单）。此前豁免只活在终局评审散文里、机检靠命令行现传，人工口径与机器口径对不上账。
EXEMPT_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "..", "..", "same-type-exemptions.txt"))


def load_exempt_clusters(path=None):
    p = path or EXEMPT_FILE
    out = []
    if not os.path.isfile(p):
        return out
    for ln in open(p, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip() or ln.startswith("#"):
            continue
        cols = ln.split("\t")
        if len(cols) >= 2:
            out.append((cols[0], cols[1].split()))
    return out


def cluster_of(name, clusters):
    for cname, pats in clusters:
        if any(fnmatch.fnmatch(name, p) for p in pats):
            return cname
    return None


def exemption_basis(a, b, adhoc, clusters):
    """返回豁免依据（簇名或"点名"），无豁免返回 None。"""
    if frozenset({a, b}) in {frozenset(s.split(":")) for s in adhoc}:
        return "命令行点名"
    ca, cb = cluster_of(a, clusters), cluster_of(b, clusters)
    return f"簇 {ca}" if ca and ca == cb else None


def _shared_source_paths(metas):
    """跨仓字节同族（同 md5）的**在仓证据路径**集合——C2 同源折算的分母输入（d000048）。"""
    fam = {}
    for m in metas:
        for p in (m.get("ev_paths") or set()):
            h = md5(p)
            if h:
                fam.setdefault(h, set()).add(m["repo_name"])
    shared = set()
    for m in metas:
        for p in (m.get("ev_paths") or set()):
            h = md5(p)
            if h and len(fam.get(h, set())) >= 2:
                shared.add(p)
    return shared


def _folded_lexemes(x, y, shared_src):
    """某共享词条若其证据在**两仓都**只落在跨仓字节同族件上，则折算掉（C2，d000048）。"""
    lx_ev, ly_ev = x.get("lex_ev") or {}, y.get("lex_ev") or {}
    drop = set()
    for lx in x["lexemes"] & y["lexemes"]:
        px, py = lx_ev.get(lx, set()), ly_ev.get(lx, set())
        if px and py and px <= shared_src and py <= shared_src:
            drop.add(lx)
    return drop


def ac06_findings(metas, exempt=(), clusters=None, shared_src=None):
    """判别力闸（t000103 收口；C2 同源折算前置＝d000048）：06 出口判定把"区分度破"列为 **[高] 类违例**，故此处按违例计。
    三条：① Jaccard>0.6 的仓对——豁免依据＝命令行点名或**在册簇**（根级 same-type-exemptions.txt，
    人工点名的唯一可复算登记处）；两仓**档位不同**时豁免降为警告（跨档豁免是否有效候用户裁）；
    ② ≥3 仓且档位不全同却得出同一词条集合＝常数簇（v1 病灶形，**无需阈值**即可判）；
    ③ 自印 distinct 与实算不符即违例（「条数只能由名单得出」的区分度版）。
    **最小集合规模（d000042）**：min(|A|,|B|) < 3 的仓对不参与 ①——1～2 条需求的薄切片仓（T0/T1）
    重合是算术必然（一对各 1 词条即 Jaccard=1.00），无信息量且会长期占违例位；仍计入 ②③ 与 distinct。
    **C2 折算前置（d000048）**：判阈**之前**先做同源折算——重叠词条若其证据在两仓**都**只由跨仓字节同族件
    （同 md5）支撑，则不进分母；折算动作留痕（`AC-06-FOLDED` 信息行）。折算后仍 >0.6 才判豁免/违例。
    局限如实记：机检只能核到**档位**，06 所述"同语言＋同构建链＋同测试栈"三同靠登记者自证理由。"""
    out = []
    clusters = clusters if clusters is not None else load_exempt_clusters()
    if shared_src is None:
        shared_src = _shared_source_paths(metas)
    sets = {frozenset(m["lexemes"]) for m in metas if m["lexemes"]}
    tiers = {m["tier"] for m in metas if m["tier"] is not None}
    for x, y in combinations(metas, 2):
        if x["repo_name"] == y["repo_name"]:
            continue          # 同仓多轮属尺变面（DELTA-SCALE），不参与跨仓区分度比对
        if x["lexemes"] and y["lexemes"] and min(len(x["lexemes"]), len(y["lexemes"])) >= 3:
            raw = jaccard(x["lexemes"], y["lexemes"])
            fold = _folded_lexemes(x, y, shared_src)
            fx, fy = x["lexemes"] - fold, y["lexemes"] - fold
            jv = jaccard(fx, fy) if (fx | fy) else 0.0   # 折算后尽空＝无独立重合，非 1.0
            if raw > 0.6 and jv <= 0.6:
                out.append(("信息", f"AC-06-FOLDED: {x['repo_name']}×{y['repo_name']} 折算前 Jaccard={raw:.2f}、"
                                    f"折算去 {len(fold)} 条同源词条后={jv:.2f}≤0.6（C2 同源折算前置，d000048）"))
                continue
            if jv > 0.6:
                basis = exemption_basis(x["repo_name"], y["repo_name"], exempt, clusters)
                same_tier = x["tier"] is not None and x["tier"] == y["tier"]
                if basis:
                    # Q1 裁（d000042）：同型按 06「三同」口径**可跨档**——豁免有效，但跨档必须留痕，
                    # 因为档位不同说明两仓的规模/形态确有差异，重合理由要在登记处站得住。
                    if same_tier:
                        out.append(("信息", f"AC-06: {x['repo_name']}×{y['repo_name']} Jaccard={jv:.2f} 豁免有效（{basis}）"))
                    else:
                        out.append(("信息", f"AC-06-XDIR: {x['repo_name']}(T{x['tier']})×{y['repo_name']}(T{y['tier']}) "
                                          f"Jaccard={jv:.2f} 豁免有效（{basis}·**跨档豁免**，三同理由须在登记处可查）"))
                else:
                    hint = (f"，同档可入簇登记或点名 --same-type {x['repo_name']}:{y['repo_name']}"
                            if same_tier else "（跨档对无豁免通道）")
                    out.append(("违例", f"AC-06: {x['repo_name']}×{y['repo_name']} Jaccard={jv:.2f}>0.6 区分度破{hint}"))
    if len(metas) >= 3 and len(tiers) >= 2 and len(sets) == 1:
        out.append(("违例", f"AC-06-CONSTANT: {len(metas)} 仓跨档 {sorted(tiers)} 却 distinct(词条集合)=1"
                          "——判别力不成立（多档同批得同一集合＝v1 常数清单复发）"))
    return out, len(sets), sorted(tiers)


def cmd_batch(a):
    metas, allf = [], []
    for rec in a.records:
        repo = derive_repo(rec)
        if not repo:
            print(f"batch: 跳过（无法反推仓根）{rec}", file=sys.stderr)
            continue
        f, m = check_record(rec, repo)
        metas.append(m)
        allf.extend((m["repo_name"], d, lvl, msg) for d, lvl, msg in f)
    bad = sum(1 for *_, lvl, _ in allf if lvl == "违例")
    for rn, d, lvl, msg in allf:
        print(f"  [{lvl}] {rn} · {d}: {msg}")
    # 区分度只算**每仓一份**（同日多轮以最大 -rN 为准＝r2 为准惯例）；否则同仓多轮会冒充跨仓样本
    def _round(m):
        r = re.search(r"-r(\d+)\.md$", m["path"])
        return int(r.group(1)) if r else 0
    latest = {}
    for m in metas:
        cur = latest.get(m["repo_name"])
        if cur is None or _round(m) >= _round(cur):
            latest[m["repo_name"]] = m
    reps = list(latest.values())
    ac, d_real, tiers = ac06_findings(reps, a.same_type or [], load_exempt_clusters())
    for lvl, msg in ac:
        print(f"  [{lvl}] {msg}")
        bad += lvl == "违例"
    for m in reps:
        txt = open(m["path"], encoding="utf-8", errors="replace").read()
        dm = re.search(r"distinct[^0-9\n]{0,12}(\d+)", txt)
        if dm and int(dm.group(1)) != d_real:
            print(f"  [违例] AC06-DECLARED: {m['repo_name']} 自印 distinct={dm.group(1)} ≠ 实算 {d_real}"
                  "（批末由汇总者统一回填，不得各仓自估）")
            bad += 1
    print(f"  [信息] 区分度对表：仓数={len(reps)}（多轮取最大 -rN）· distinct(实算)={d_real} · 档位集={tiers}")
    # 同源折叠（跨仓字节同族）
    fam = {}
    for m in metas:
        for p in m["ev_paths"]:
            h = md5(p)
            if h:
                fam.setdefault(h, {})[m["repo_name"]] = fam.setdefault(h, {}).get(m["repo_name"], 0) + 1
    for h, repos in sorted(fam.items()):
        if len(repos) >= 2:
            print(f"  [信息] FOLD: md5 {h} 同现 {len(repos)} 仓 {sorted(repos)}（转正线折算候选）")
    # 源自反
    if a.lexicon:
        lx = open(a.lexicon, encoding="utf-8").read()
        srcs = {os.path.normpath(os.path.expanduser(p)) for _, p in LEX_SOURCE.findall(lx)}
        for m in metas:
            hit = os.path.normpath(m["repo"]) in srcs
            txt = open(m["path"], encoding="utf-8").read()
            if hit and re.search(r"源自反\s*=\s*\*{0,2}无", txt):
                print(f"  [违例] SRC-SELF: {m['repo_name']}＝词表来源仓，但报头写「源自反=无」")
                bad += 1
    # 同仓多轮尺变归口
    by = {}
    for m in metas:
        by.setdefault(m["repo_name"], []).append(m)
    for rn, ms in by.items():
        if len(ms) > 1 and len({m["tier"] for m in ms}) > 1:
            for m in ms[1:]:
                if not m["scale"]:
                    print(f"  [违例] DELTA-SCALE: {rn} 跨轮档位反转但 {os.path.basename(m['path'])} 无口径声明行")
                    bad += 1
    # 复现力披露（C3，d000048）：同仓跨轮词条集合 Jaccard——作 AC-06/AC-09-A1 的分母健康度；
    # 提示「≥2 轮同判」是否成立，升为硬闸前须补「同执行者重入」对照（现两轮多为不同执行者）。
    for rn, ms in sorted(by.items()):
        if len(ms) >= 2:
            worst = min(jaccard(ms[i]["lexemes"], ms[j]["lexemes"])
                        for i in range(len(ms)) for j in range(i + 1, len(ms)))
            if worst < 0.9:
                print(f"  [信息] RECON-REPRO: {rn} 跨轮集合 Jaccard（最低）={worst:.2f}（{len(ms)} 轮）"
                      "——C3 分母健康度披露，单轮 AC-06 结论可被下轮推翻；≥2 轮同判闸待「同执行者重入」对照（d000048）")
    print(f"→ batch：{len(metas)} 份 · 违例 {bad}")
    return 1 if bad else 0


# ---------------- selfcheck：双向校准 ----------------
def _fixture_expect():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "fixtures")
    return base


def run_selfcheck(_a):
    base = _fixture_expect()
    expect = {"pos": {"record": "record.md", "违例": 0},
              "neg": {"record": "record-r2.md", "违例": 18}}
    # neg＝阳性夹具（每类违例各埋一处）；pos＝同构阴性（一律不得打中）。
    # 18 处＝八类老检测器 + t000068 本波七类（COV-COLS/PROP-SIGMA/PROP-STATE/PROP-FIELDS/
    # ACT-BAN/PLACEHOLDER/MOUNT-SLUG/STATE-CLOSED，其中 COV-COLS 有语料真例、余为预防级）
    # + t000107 M（EVID-KEY2 第二键计数口径）+ B 波四类复算闸（REF-LINE/NAY-CLOSED/
    # CITE-COUNT/TRACE-NOW，2026-09-25）。
    det_expect = {"AC01-MISSING": 1, "AC01-TONGJIAN": 1, "AC10-COUNT": 1, "STR-CLOSED": 1,
                  "COV-SIGMA": 1, "COV-VOCAB": 1, "HDR-SELFPRINT": 1, "DELTA-MISSING": 1,
                  "COV-COLS": 1, "PROP-SIGMA": 1, "PROP-STATE": 1, "PROP-FIELDS": 1,
                  "ACT-BAN": 1, "PLACEHOLDER": 1, "MOUNT-SLUG": 1, "STATE-CLOSED": 1,
                  "EVID-KEY2": 1, "REF-LINE": 1, "NAY-CLOSED": 1, "CITE-COUNT": 1, "TRACE-NOW": 1}
    fails = []
    for name in ("pos", "neg"):
        f, m = check_record(os.path.join(base, name, expect[name]["record"]), os.path.join(base, name, "repo"))
        cnt = sum(1 for _, l, _ in f if l == "违例")
        warns = sum(1 for _, l, _ in f if l == "警告")
        if cnt != expect[name]["违例"]:
            fails.append(f"{name}: 违例数 {cnt} ≠ 期望 {expect[name]['违例']}")
        if name == "pos" and warns:
            fails.append(f"pos: 阴性夹具出现警告 {warns} 条（同构不得打中）")
        got = {}
        for d, l, _ in f:
            got[d] = got.get(d, 0) + 1
        for d, c in det_expect.items():
            if name == "neg" and got.get(d, 0) < c:
                fails.append(f"neg: 正例打中失败 {d}（期望≥{c}，实得 {got.get(d, 0)}）")
            if name == "pos" and got.get(d, 0):
                fails.append(f"pos: 检测器 {d} 误打中阴性夹具")
    if fails:
        print("selfcheck FAIL——扫描器失准，其 report/batch 结论禁用：")
        for x in fails:
            print("  -", x)
        return 2
    # ---- 判别力闸自检（ac06_findings）：四例三向——常数必抓、同型豁免必须不抓、低重合必须不抓、
    # 跨档假豁免必须抓。缺任一侧＝只测了阈值的一半（t000105）。
    def _mk(n, tier, lex, lex_ev=None):
        return {"repo_name": n, "tier": tier, "lexemes": set(lex), "lex_ev": lex_ev or {}}
    same = {"L-01", "L-02", "L-03", "L-04"}
    probes = [
        ("常数簇（三仓跨档同集合）",
         [_mk("a", 1, same), _mk("b", 2, same), _mk("c", 3, same)], [], {"AC-06-CONSTANT", "AC-06"}),
        ("同档点名豁免（必须不抓）",
         [_mk("x", 2, same), _mk("y", 2, same)], ["x:y"], set()),
        ("低重合（必须不抓）",
         [_mk("p", 1, {"L-01"}), _mk("q", 2, {"L-09"})], [], set()),
        ("跨档簇内豁免（d000042：可豁免，但只出信息、不得静默消失）",
         [_mk("m", 1, same), _mk("n", 3, same)], ["m:n"], set()),
        ("小集合平凡重合（min<3 必须不参与比对）",
         [_mk("s", 0, {"L-01", "L-02"}), _mk("t", 0, {"L-01", "L-02"})], [], set()),
    ]
    pfails = []
    for name, ms, ex, want in probes:
        got = {msg.split(":")[0] for lvl, msg in ac06_findings(ms, ex, [])[0] if lvl != "信息"}
        if got != want:
            pfails.append(f"{name}：期望 {sorted(want)}，实得 {sorted(got)}")
    xdim = [msg for lvl, msg in ac06_findings([_mk("m", 1, same), _mk("n", 3, same)], ["m:n"], [])[0]
            if msg.startswith("AC-06-XDIR")]
    if not xdim:
        pfails.append("跨档豁免未留痕（AC-06-XDIR 信息行缺失＝豁免静默化）")
    # C2 同源折算前置（d000048）：折算后降阈须只留痕、不得判违例（折算前 >0.6、折算后 ≤0.6）
    fold_src = {"/shared/p", "/shared/q"}
    fms = [_mk("foldA", 2, same, {l: {"/shared/p"} for l in same}),
           _mk("foldB", 2, same, {l: {"/shared/q"} for l in same})]
    fres = ac06_findings(fms, [], [], shared_src=fold_src)[0]
    if any(lvl != "信息" for lvl, _ in fres) or not any(m.startswith("AC-06-FOLDED") for _, m in fres):
        pfails.append("同源折算前置（C2）：折算后降阈应只留 AC-06-FOLDED 信息、不得判违例")
    if pfails:
        print("selfcheck FAIL——判别力闸失准（其 AC-06 结论禁用）：")
        for x in pfails:
            print("  -", x)
        return 2
    print(f"selfcheck PASS：neg {len(det_expect)} 类检测器全打中（违例 {expect['neg']['违例']} 处）、"
          f"同构 pos 夹具零打中 ＋ 判别力闸 {len(probes) + 1} 例合期望（含跨档豁免留痕、C2 同源折算前置两例）。")
    return 0


def cmd_serves(a):
    """批跑补录：从各记录「覆盖表·已承载」行聚合 技能→词条 候选表（加速器，非裁决）。"""
    pairs = {}
    known = set()
    if a.catalog:
        for ln in open(a.catalog, encoding="utf-8"):
            m = re.match(r"^\s\s([a-z0-9-]+):\s*\{", ln)
            if m:
                known.add(m.group(1))
    for rec in a.records:
        repo = derive_repo(rec)
        if not repo:
            continue
        text = open(rec, encoding="utf-8").read()
        _, rbody = section(text, r"需求表")
        _, cbody = section(text, r"覆盖表")
        if not rbody or not cbody:
            continue
        lexemes = [re.findall(r"L-\d+[a-z]?|O-\d+", " | ".join(r)) for r in table_rows(rbody)[1:]]
        crows = table_rows(cbody)
        hdr = crows[0] if crows else []
        ci = next((i for i, c in enumerate(hdr) if "承载" in c or "候选" in c), 2)
        li = next((i for i, c in enumerate(hdr) if "落点" in c), 1)
        known_re = re.compile(r"(?<![a-z0-9-])(" + "|".join(map(re.escape, sorted(known))) + r")(?![a-z0-9-])") if known else None
        for k, r in enumerate(crows[1:]):
            row = " | ".join(r)
            if len(r) <= max(ci, li) or "已承载" not in r[li]:
                continue
            names = set(re.findall(r"`([a-z0-9-]+)`", row))
            if known_re:
                names |= set(known_re.findall(row))
                names = {n for n in names if n in known}
            lx = set(re.findall(r"L-\d+[a-z]?|O-\d+", row))
            if not lx:
                lx = set(lexemes[k]) if k < len(lexemes) else set()
            for n in names:
                for l in lx or ["(词条列缺)"]:
                    pairs.setdefault((n, l), set()).add(os.path.basename(repo))
    out = ["# serves 补录草案（批导数 · 2026-09-23 批＋复跑记录聚合）",
           "",
           "> 生成：`sf-check.py serves`（记录见各仓 .skill-fit/feedback/2026-09-23*）。**加速器非裁决**——入 catalog 前须按 INV-05 读正文复核；孤证对（仅 1 仓）不满足转正线。",
           "",
           "| 技能 | 词条 | 观察仓数 | 仓 |", "|---|---|---|---|"]
    for (n, l), repos in sorted(pairs.items(), key=lambda x: (-len(x[1]), x[0])):
        out.append(f"| {n} | {l} | {len(repos)} | {'、'.join(sorted(repos))} |")
    txt = "\n".join(out) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(txt)
        print(f"serves：{len(pairs)} 对 → {a.out}")
    else:
        print(txt)
    return 0


def main():
    ap = argparse.ArgumentParser(prog="sf-check", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="单份记录机检")
    r.add_argument("record")
    r.add_argument("--repo")
    r.set_defaults(fn=cmd_report)
    b = sub.add_parser("batch", help="批跑复核：区分度/同源折叠/源自反/尺变归口")
    b.add_argument("records", nargs="+")
    b.add_argument("--lexicon", help="词表文件（来源仓路径表所在）")
    b.add_argument("--same-type", action="append", metavar="A:B",
                    help="临时点名豁免对（常规豁免请登记根级 same-type-exemptions.txt）")
    b.set_defaults(fn=cmd_batch)
    s = sub.add_parser("selfcheck", help="双向校准（夹具回归）")
    s.set_defaults(fn=run_selfcheck)
    v = sub.add_parser("serves", help="批导数：覆盖表已承载行聚合成 serves 补录草案")
    v.add_argument("records", nargs="+")
    v.add_argument("--catalog", help="catalog.yaml（技能名白名单）")
    v.add_argument("--out", help="写出的草案文件路径")
    v.set_defaults(fn=cmd_serves)
    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()

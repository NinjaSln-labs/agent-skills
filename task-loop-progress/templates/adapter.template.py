#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{{TASK_ID}}：通用 task_loop poll adapter（config 驱动 + 标准契约透传）。

用法：
    echo '<poll_output>' | python3 scripts/task_loop_adapters/{{TASK_ID}}_adapter.py [config_path]

- 无参数：读环境变量 TASK_LOOP_CONFIG；都无 → 默认提取规则（兼容旧行为）。
- config_path：`configs/task_loop/<task_id>.json` 的 `progress_extract` 规则。

行为（按序）：
1. 透传：poll 输出已是标准契约 JSON（含 status / chat_line / progress）→ 原样输出，仅补缺省字段。
2. 提取：按 `progress_extract` 从 JSON 字段路径或文本正则提取进度（支持三型）。
3. 输出：标准契约 JSON（status / chat_line / metrics / log_tail）。

进度三型（`progress_extract` 任选其一）：
- 数值型：offset_field + total_field（默认 progress.offset / progress.total）
- 百分比型：pct_field（默认 pct，0-100）
- 阶段型：stage_field + stage_total_field（默认 progress.stage / progress.stage_total）
"""
from __future__ import print_function
import json
import os
import re
import sys


def read_config(path=None):
    """读取 config；无 path 时尝试环境变量 TASK_LOOP_CONFIG；都无 → 空 dict。"""
    if not path:
        path = os.environ.get("TASK_LOOP_CONFIG", "")
    if path and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg if isinstance(cfg, dict) else {}
        except Exception:
            pass
    return {}


def get_path(obj, dotted):
    """按点路径取嵌套字段，如 'progress.offset'；缺失返回 None。"""
    cur = obj
    for part in (dotted or "").split("."):
        if part and isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def extract(rule, data, raw):
    """按规则提取进度，返回 (offset, total, pct, stage, stage_total)。"""
    source = rule.get("source", "auto")
    # JSON 字段路径提取（auto：offset/pct/stage 任一存在即走 JSON）
    if source in ("auto", "json"):
        off = get_path(data, rule.get("offset_field", "progress.offset"))
        pct = get_path(data, rule.get("pct_field", "pct"))
        stage = get_path(data, rule.get("stage_field", "progress.stage"))
        if off is not None or pct is not None or stage is not None or source == "json":
            return (
                off,
                get_path(data, rule.get("total_field", "progress.total")),
                pct,
                stage,
                get_path(data, rule.get("stage_total_field", "progress.stage_total")),
            )
    # 文本正则提取（数字组：首个=当前，次个=总数）
    if source in ("auto", "text") and rule.get("regex"):
        m = re.search(rule["regex"], raw)
        if m:
            g = [x for x in m.groups() if x and x.isdigit()]
            if g:
                off = int(g[0])
                total = int(g[1]) if len(g) >= 2 else 1
                return (off, total, None, None, None)
    return (None, None, None, None, None)


def main():
    cfg = read_config(sys.argv[1] if len(sys.argv) > 1 else None)
    rule = cfg.get("progress_extract", {}) if isinstance(cfg, dict) else {}

    raw = sys.stdin.read()
    data = {}
    try:
        data = json.loads(raw.strip() or "{}")
    except ValueError:
        data = {"__raw__": raw}

    # 1) 透传：poll 已输出标准契约（status / chat_line / progress 任一存在）
    if isinstance(data, dict) and (data.get("status") or data.get("chat_line") or data.get("progress")):
        out = dict(data)
        out.setdefault("status", "done" if data.get("finished") else "running")
        if not out.get("chat_line"):
            prog = out.get("progress") or {}
            out["chat_line"] = "offset=%s/%s" % (prog.get("offset", "?"), prog.get("total", "?"))
        out.setdefault("log_tail", [])
        print(json.dumps(out, ensure_ascii=False))
        return

    # 2) 提取（config 规则；缺省回退旧行为：prog 嵌套 + offset= 文本）
    off = total = pct = stage = stage_total = None
    if rule:
        off, total, pct, stage, stage_total = extract(rule, data, raw)
    else:
        prog = data.get("prog") if isinstance(data, dict) else None
        if isinstance(prog, dict):
            off = prog.get("offset")
            total = prog.get("total", 1)
            pct = prog.get("pct")
            stage = prog.get("stage")
            stage_total = prog.get("stage_total")
        else:
            m = re.search(r"offset=(\d+)", raw)
            if m:
                off = int(m.group(1))
                total = 1

    # 3) 构造标准契约输出
    metrics = {}
    if off is not None:
        off = int(off)
        total = int(total) if total is not None else 1
        pct = round(100.0 * off / total, 2) if total else 0.0
        metrics = {"offset": off, "total": total, "pct": pct}
        chat = "offset=%d/%d (%.2f%%)" % (off, total, pct)
    elif pct is not None:
        metrics["pct"] = float(pct)
        chat = "进度 %.1f%%" % float(pct)
    elif stage is not None:
        metrics["stage"] = str(stage)
        metrics["stage_total"] = str(stage_total or "?")
        chat = "阶段 %s/%s" % (stage, stage_total or "?")
    else:
        metrics = {"offset": 0, "total": 0, "pct": 0.0}
        chat = "暂无进度"

    log_tail = [ln for ln in raw.splitlines() if ln.strip()][-5:]
    running = bool(off or pct or stage)
    out = {
        "status": "done" if data.get("finished") else ("running" if running else "idle"),
        "finished": bool(data.get("finished")),
        "chat_line": chat,
        "metrics": metrics,
        "log_tail": log_tail,
    }
    if isinstance(data, dict) and data.get("ts"):
        out["polled_at"] = data["ts"]
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()

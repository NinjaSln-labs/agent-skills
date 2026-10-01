#!/usr/bin/env python3
"""sf-gate — skill-fit E4 确认门（挂／移／反挂载 · 2.2.0）。

五步：提案 → 确认 → 应用 → 校验 → 回滚。权限档恒 ask-user（Q-05 白名单空＝全问）。
动作闭集：mount／move／unmount。INV-07：只动挂载点，永不碰真源。

用法：
  python3 sf-gate.py draft  --root <仓> --skill <名> --action mount|move|unmount --tier project|user|host \\
                            --source <真源绝对路径> [--from-tier <原层级>] [--risk 低|中|高]
  python3 sf-gate.py confirm --root <仓> --id <P…> --token yes-this-one|no-and-why|later|all-in-this-class [--why …]
  python3 sf-gate.py apply   --root <仓> --id <P…>
  python3 sf-gate.py verify  --root <仓> --id <P…>
  python3 sf-gate.py rollback --root <仓> --id <P…>
  python3 sf-gate.py status  --root <仓> --id <P…>
  python3 sf-gate.py selfcheck
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ACTIONS = ("mount", "move", "unmount")
TIERS = ("project", "user", "host")
TOKENS = ("yes-this-one", "no-and-why", "later", "all-in-this-class")
RISKS = ("低", "中", "高")

def die(msg: str, code: int = 2) -> None:
    print(f"sf-gate: {msg}", file=sys.stderr)
    raise SystemExit(code)


def tier_dir(root: Path, tier: str, host_root: str | None) -> Path:
    if tier == "project":
        return root / ".agents" / "skills"
    if tier == "user":
        return Path(os.path.expanduser("~/.agents/skills"))
    if tier == "host":
        if not host_root:
            die("host 层级须 --host-root（本波不默认真源宿主编排位，防误伤）")
        return Path(host_root).expanduser().resolve()
    die(f"未知层级: {tier}")


def proposals_dir(root: Path) -> Path:
    d = root / ".skill-fit" / "proposals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_path(root: Path) -> Path:
    d = root / ".skill-fit"
    d.mkdir(parents=True, exist_ok=True)
    return d / "applied.jsonl"


def load_prop(root: Path, pid: str) -> dict:
    p = proposals_dir(root) / f"{pid}.json"
    if not p.is_file():
        die(f"提案不存在: {pid}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_prop(root: Path, prop: dict) -> None:
    p = proposals_dir(root) / f"{prop['id']}.json"
    p.write_text(json.dumps(prop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_log(root: Path, event: dict) -> None:
    event = dict(event)
    event["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with log_path(root).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def resolve_link(path: Path) -> str | None:
    if not path.exists() and not path.is_symlink():
        return None
    try:
        return str(path.resolve())
    except OSError:
        return None


def snapshot(path: Path) -> dict:
    """前态：不存在 / 链接目标 / 非链接占位。"""
    if path.is_symlink():
        return {"kind": "symlink", "target": os.readlink(path), "resolved": resolve_link(path)}
    if path.exists():
        return {"kind": "other", "resolved": str(path.resolve())}
    return {"kind": "absent"}


def check_symlink_to(path: Path, source: Path) -> str | None:
    """返回错误串，None＝通过。"""
    if not path.is_symlink():
        return f"非符号链接 {path}"
    got = Path(resolve_link(path) or "")
    want = source.resolve()
    if got != want:
        return f"解析到 {got}，期望 {want}"
    return None


def cmd_draft(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    action = args.action
    if action not in ACTIONS:
        die(f"动作须为 {ACTIONS}")
    if args.tier not in TIERS:
        die(f"层级须为 {TIERS}")
    if args.risk not in RISKS:
        die(f"风险档须为 {RISKS}")
    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        die(f"真源不存在或非目录: {source}")
    skill = args.skill
    if skill != source.name:
        die(f"技能名 {skill!r} 与真源目录名 {source.name!r} 不一致（防错挂）")
    if action == "move" and not args.from_tier:
        die("move 须 --from-tier")
    if action in ("mount", "unmount") and args.from_tier:
        die(f"{action} 不要 --from-tier")

    host = args.host_root
    dest_parent = tier_dir(root, args.tier, host)
    dest = dest_parent / skill
    prev = snapshot(dest)
    if action == "mount" and prev["kind"] != "absent":
        die(f"挂前置失败：目标已存在 {dest} → {prev}")
    from_snap = None
    if action == "move":
        src_link = tier_dir(root, args.from_tier, host) / skill
        from_snap = snapshot(src_link)
        if from_snap["kind"] != "symlink":
            die(f"移层级前置失败：原层级无链接 {src_link} → {from_snap}")
        if Path(from_snap["resolved"] or "") != source:
            die(f"移层级前置失败：原链接解析 {from_snap['resolved']} ≠ 真源 {source}")
        if prev["kind"] != "absent":
            die(f"移层级前置失败：目标层已存在 {dest}")
    if action == "unmount":
        if prev["kind"] != "symlink":
            die(f"反挂载前置失败：目标非符号链接 {dest} → {prev}")
        if Path(prev["resolved"] or "") != source:
            die(f"反挂载前置失败：链接解析 {prev['resolved']} ≠ 真源 {source}")
        # 真源必须仍在位（INV-07：卸的是挂载点，不是目录）
        if not source.is_dir():
            die(f"反挂载前置失败：真源已不在 {source}")
    n = len(list(proposals_dir(root).glob("P*.json"))) + 1
    pid = f"P{n:04d}"
    prop = {
        "id": pid,
        "state": "proposed",
        "action": action,
        "skill": skill,
        "tier": args.tier,
        "from_tier": args.from_tier,
        "source": str(source),
        "dest": str(dest),
        "prev": prev,
        "from_prev": from_snap,
        "risk": args.risk,
        "permission": "ask-user",
        "host_root": host,
        "confirm": None,
        "verify": None,
    }
    save_prop(root, prop)
    append_log(root, {"event": "drafted", "id": pid, "action": action, "skill": skill, "tier": args.tier})
    print(json.dumps({"id": pid, "state": "proposed", "dest": str(dest), "prev": prev}, ensure_ascii=False))


def cmd_confirm(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    prop = load_prop(root, args.id)
    if prop["state"] not in ("proposed", "deferred"):
        die(f"状态 {prop['state']} 不可确认")
    tok = args.token
    if tok not in TOKENS:
        die(f"口令闭集：{TOKENS}")
    if tok == "all-in-this-class":
        die("all-in-this-class 须同类同风险批确认；单条 CLI 请用 yes-this-one（INV-08）")
    if tok == "no-and-why" and not (args.why or "").strip():
        die("no-and-why 须 --why")
    if tok == "yes-this-one":
        prop["state"] = "confirmed"
    elif tok == "no-and-why":
        prop["state"] = "declined"
    else:  # later
        prop["state"] = "deferred"
    prop["confirm"] = {"token": tok, "why": args.why}
    save_prop(root, prop)
    append_log(root, {"event": "confirm", "id": prop["id"], "token": tok, "state": prop["state"]})
    print(json.dumps({"id": prop["id"], "state": prop["state"]}, ensure_ascii=False))


def _link(dest: Path, source: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        die(f"应用失败：目标已存在 {dest}", 1)
    os.symlink(str(source), str(dest))


def _unlink_only(path: Path, expected_source: Path | None = None) -> None:
    """只删符号链接；若 expected_source 给定则校验解析一致。永不 rm 真源。"""
    if not path.is_symlink():
        if path.exists():
            die(f"拒删非链接（INV-07）: {path}", 1)
        return
    if expected_source is not None:
        got = Path(resolve_link(path) or "")
        if got != expected_source.resolve():
            die(f"回滚拒：链接解析 {got} ≠ 记录真源 {expected_source}", 1)
    path.unlink()


def cmd_apply(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    prop = load_prop(root, args.id)
    if prop["state"] != "confirmed":
        die(f"未确认不可应用（state={prop['state']}；INV-08）")
    source = Path(prop["source"])
    dest = Path(prop["dest"])
    host = prop.get("host_root")
    prop["state"] = "applying"
    save_prop(root, prop)
    try:
        if prop["action"] == "mount":
            if snapshot(dest)["kind"] != "absent":
                die(f"应用失败：目标已存在 {dest}", 1)
            _link(dest, source)
        elif prop["action"] == "move":
            src_link = tier_dir(root, prop["from_tier"], host) / prop["skill"]
            if snapshot(src_link)["kind"] != "symlink":
                die(f"应用失败：原链接消失 {src_link}", 1)
            _link(dest, source)
            _unlink_only(src_link, source)
        elif prop["action"] == "unmount":
            if not source.is_dir():
                die(f"应用失败：真源已不在（INV-07 拒继续）{source}", 1)
            _unlink_only(dest, source)
        else:
            die(f"拒动作 {prop['action']}")
    except SystemExit:
        prop["state"] = "confirmed"  # 回退可重试
        save_prop(root, prop)
        raise
    prop["state"] = "applied"
    save_prop(root, prop)
    append_log(root, {"event": "applied", "id": prop["id"], "dest": str(dest), "prev": prop["prev"]})
    print(json.dumps({"id": prop["id"], "state": "applied", "dest": str(dest)}, ensure_ascii=False))

def cmd_verify(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    prop = load_prop(root, args.id)
    if prop["state"] not in ("applied", "verified", "verification_failed"):
        die(f"状态 {prop['state']} 不可校验")
    source = Path(prop["source"])
    dest = Path(prop["dest"])
    host = prop.get("host_root")
    detail: list[str] = []
    err: str | None = None
    if prop["action"] == "unmount":
        snap = snapshot(dest)
        if snap["kind"] != "absent":
            err = f"挂载点仍在 {dest} → {snap}"
            detail.append(err)
        else:
            detail.append("挂载点已清")
        if not source.is_dir():
            err = err or f"真源消失（INV-07 违）{source}"
            detail.append(err)
        else:
            detail.append(f"真源仍在 {source.resolve()}")
    else:
        err = check_symlink_to(dest, source)
        if err:
            detail.append(err)
        else:
            detail.append(f"dest→{source.resolve()}")
        if prop["action"] == "move":
            old = tier_dir(root, prop["from_tier"], host) / prop["skill"]
            if old.exists() or old.is_symlink():
                detail.append(f"原层级残留 {old}")
                err = err or detail[-1]
            else:
                detail.append("原层级已清")
    ok = err is None
    prop["state"] = "verified" if ok else "verification_failed"
    prop["verify"] = {"ok": ok, "detail": detail}
    save_prop(root, prop)
    append_log(root, {"event": "verify", "id": prop["id"], "ok": ok, "detail": detail})
    if not ok:
        die(f"校验失败 → 须 rollback：{'; '.join(detail)}", 1)
    print(json.dumps({"id": prop["id"], "state": prop["state"], "detail": detail}, ensure_ascii=False))


def cmd_rollback(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    prop = load_prop(root, args.id)
    if prop["state"] not in ("applied", "verified", "verification_failed"):
        die(f"状态 {prop['state']} 不可回滚")
    source = Path(prop["source"])
    dest = Path(prop["dest"])
    host = prop.get("host_root")
    if prop["action"] == "mount":
        _unlink_only(dest, source)
        if snapshot(dest)["kind"] != "absent":
            die("回滚后目标仍在", 1)
    elif prop["action"] == "move":
        # 恢复原层级链接，移除新层级
        _unlink_only(dest, source)
        old_parent = tier_dir(root, prop["from_tier"], host)
        old = old_parent / prop["skill"]
        if snapshot(old)["kind"] != "absent":
            die(f"回滚失败：原位已被占用 {old}", 1)
        _link(old, source)
        err = check_symlink_to(old, source)
        if err:
            die(f"回滚后校验失败：{err}", 1)
    elif prop["action"] == "unmount":
        # 恢复挂载点；真源须仍在
        if not source.is_dir():
            die(f"回滚失败：真源已不在 {source}", 1)
        if snapshot(dest)["kind"] != "absent":
            die(f"回滚失败：目标位已被占用 {dest}", 1)
        _link(dest, source)
        err = check_symlink_to(dest, source)
        if err:
            die(f"回滚后校验失败：{err}", 1)
    else:
        die(f"拒动作 {prop['action']}")
    prop["state"] = "rolled_back"
    save_prop(root, prop)
    append_log(root, {"event": "rolled_back", "id": prop["id"], "action": prop["action"]})
    print(json.dumps({"id": prop["id"], "state": "rolled_back"}, ensure_ascii=False))


def cmd_status(args: argparse.Namespace) -> None:
    root = Path(args.root).resolve()
    prop = load_prop(root, args.id)
    print(json.dumps(prop, ensure_ascii=False, indent=2))


def cmd_selfcheck(_: argparse.Namespace) -> None:
    """临时目录：挂→校验→回滚；挂→移层级→校验→回滚；挂→反挂载→校验→回滚；拒未确认 apply。"""
    with tempfile.TemporaryDirectory(prefix="sf-gate-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        skill = root / "demo-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("# demo\n", encoding="utf-8")
        host = Path(tmp) / "host-skills"
        host.mkdir()
        NS = argparse.Namespace

        # --- mount + rollback ---
        cmd_draft(NS(
            root=str(root), skill="demo-skill", action="mount", tier="project",
            source=str(skill), from_tier=None, risk="低", host_root=None,
        ))
        cmd_confirm(NS(root=str(root), id="P0001", token="yes-this-one", why=None))
        cmd_apply(NS(root=str(root), id="P0001"))
        cmd_verify(NS(root=str(root), id="P0001"))
        link = root / ".agents" / "skills" / "demo-skill"
        assert link.is_symlink() and link.resolve() == skill.resolve()
        cmd_rollback(NS(root=str(root), id="P0001"))
        assert not link.exists() and not link.is_symlink()
        assert skill.is_dir()

        # --- mount then move project→host + rollback move ---
        cmd_draft(NS(
            root=str(root), skill="demo-skill", action="mount", tier="project",
            source=str(skill), from_tier=None, risk="低", host_root=str(host),
        ))
        cmd_confirm(NS(root=str(root), id="P0002", token="yes-this-one", why=None))
        cmd_apply(NS(root=str(root), id="P0002"))
        cmd_verify(NS(root=str(root), id="P0002"))

        cmd_draft(NS(
            root=str(root), skill="demo-skill", action="move", tier="host",
            source=str(skill), from_tier="project", risk="中", host_root=str(host),
        ))
        cmd_confirm(NS(root=str(root), id="P0003", token="yes-this-one", why=None))
        cmd_apply(NS(root=str(root), id="P0003"))
        cmd_verify(NS(root=str(root), id="P0003"))
        assert not (root / ".agents" / "skills" / "demo-skill").exists()
        assert (host / "demo-skill").resolve() == skill.resolve()
        cmd_rollback(NS(root=str(root), id="P0003"))
        assert (root / ".agents" / "skills" / "demo-skill").resolve() == skill.resolve()
        assert not (host / "demo-skill").exists()
        # 清项目级挂（P0002 仍 verified，回滚卸链）
        cmd_rollback(NS(root=str(root), id="P0002"))
        assert skill.is_dir()

        cmd_draft(NS(
            root=str(root), skill="demo-skill", action="mount", tier="project",
            source=str(skill), from_tier=None, risk="低", host_root=None,
        ))
        try:
            cmd_apply(NS(root=str(root), id="P0004"))
            raise AssertionError("应拒未确认 apply")
        except SystemExit as e:
            assert e.code in (1, 2)
        try:
            cmd_confirm(NS(root=str(root), id="P0004", token="no-and-why", why=None))
            raise AssertionError("应拒空 why")
        except SystemExit:
            pass

        # --- mount → unmount → verify → rollback unmount（真源仍在）---
        cmd_draft(NS(
            root=str(root), skill="demo-skill", action="mount", tier="project",
            source=str(skill), from_tier=None, risk="低", host_root=None,
        ))
        cmd_confirm(NS(root=str(root), id="P0005", token="yes-this-one", why=None))
        cmd_apply(NS(root=str(root), id="P0005"))
        cmd_verify(NS(root=str(root), id="P0005"))
        cmd_draft(NS(
            root=str(root), skill="demo-skill", action="unmount", tier="project",
            source=str(skill), from_tier=None, risk="中", host_root=None,
        ))
        cmd_confirm(NS(root=str(root), id="P0006", token="yes-this-one", why=None))
        cmd_apply(NS(root=str(root), id="P0006"))
        cmd_verify(NS(root=str(root), id="P0006"))
        assert not link.exists() and not link.is_symlink()
        assert skill.is_dir()
        cmd_rollback(NS(root=str(root), id="P0006"))
        assert link.is_symlink() and link.resolve() == skill.resolve()
        cmd_rollback(NS(root=str(root), id="P0005"))
        assert skill.is_dir() and not link.exists()

    print("sf-gate selfcheck PASS")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sf-gate")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("draft")
    d.add_argument("--root", required=True)
    d.add_argument("--skill", required=True)
    d.add_argument("--action", required=True, choices=ACTIONS)
    d.add_argument("--tier", required=True, choices=TIERS)
    d.add_argument("--source", required=True)
    d.add_argument("--from-tier", default=None, choices=TIERS)
    d.add_argument("--risk", default="低", choices=RISKS)
    d.add_argument("--host-root", default=None)
    d.set_defaults(func=cmd_draft)

    c = sub.add_parser("confirm")
    c.add_argument("--root", required=True)
    c.add_argument("--id", required=True)
    c.add_argument("--token", required=True, choices=TOKENS)
    c.add_argument("--why", default=None)
    c.set_defaults(func=cmd_confirm)

    for name, fn in (
        ("apply", cmd_apply),
        ("verify", cmd_verify),
        ("rollback", cmd_rollback),
        ("status", cmd_status),
    ):
        x = sub.add_parser(name)
        x.add_argument("--root", required=True)
        x.add_argument("--id", required=True)
        x.set_defaults(func=fn)

    s = sub.add_parser("selfcheck")
    s.set_defaults(func=cmd_selfcheck)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

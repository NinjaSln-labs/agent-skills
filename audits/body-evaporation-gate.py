#!/usr/bin/env python3
"""正文蒸发门禁 — 供 sync-release.sh 调用（2026-08-03 stub 事故防护）。

Usage:
  body-evaporation-gate.py <root> <release_repo> <mode> [allowlist] [ratio] [old_min]

mode: pre-rsync | post-rsync
Exit 0 = OK, 1 = FAIL (prints STUBS/UNCLOSED/DROPS lines on stdout).
"""
from __future__ import annotations

import os
import subprocess
import sys


def body_len(path: str) -> int:
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return -1
    if not text.startswith("---"):
        return len(text.strip())
    lines = text.splitlines()
    close = None
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            close = i
            break
    if close is None:
        return -2  # unclosed frontmatter
    return len("\n".join(lines[close + 1 :]).strip())


def skill_dirs(base: str):
    for name in sorted(os.listdir(base)):
        d = os.path.join(base, name)
        if not os.path.isdir(d) or name in ("audits", ".git"):
            continue
        skill = os.path.join(d, "SKILL.md")
        if os.path.isfile(skill):
            yield name, skill


def main() -> int:
    if len(sys.argv) < 4:
        print(
            "Usage: body-evaporation-gate.py <root> <release_repo> <mode> "
            "[allowlist] [ratio] [old_min]",
            file=sys.stderr,
        )
        return 2
    root = sys.argv[1]
    rel = sys.argv[2]
    mode = sys.argv[3]
    allow = set((sys.argv[4] if len(sys.argv) > 4 else "grill-me").split())
    ratio = float(sys.argv[5] if len(sys.argv) > 5 else "0.20")
    old_min = int(sys.argv[6] if len(sys.argv) > 6 else "500")

    stubs, unclosed, drops = [], [], []
    for name, skill in skill_dirs(root):
        bl = body_len(skill)
        if bl == -2:
            unclosed.append(name)
            continue
        if bl == 0 and name not in allow:
            stubs.append(name)
        elif 0 < bl < 50 and name not in allow:
            stubs.append(f"{name}(body={bl})")

    if mode == "post-rsync" and os.path.isdir(os.path.join(rel, ".git")):
        for name, skill in skill_dirs(root):
            if name in allow:
                continue
            new_sz = os.path.getsize(skill)
            path = f"{name}/SKILL.md"
            r = subprocess.run(
                ["git", "cat-file", "-s", f"HEAD:{path}"],
                cwd=rel,
                capture_output=True,
                text=True,
            )
            if r.returncode != 0:
                continue
            try:
                old_sz = int(r.stdout.strip())
            except ValueError:
                continue
            if old_sz >= old_min and new_sz < old_sz * ratio:
                drops.append(f"{name}: {old_sz}B → {new_sz}B (<{int(ratio * 100)}%)")

    if stubs or unclosed or drops:
        print("FAIL")
        if unclosed:
            print("UNCLOSED " + " ".join(unclosed))
        if stubs:
            print("STUBS " + " ".join(stubs))
        if drops:
            print("DROPS " + " | ".join(drops))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""perf-check — read-only development machine performance check (v1.0: memory / CPU / WSL2).

Judgement skeleton: Brendan Gregg's USE method (Utilization / Saturation / Errors) per resource.
Every finding carries a basis tag: "consensus" (authoritative threshold) or "heuristic"
(experience line — WARN only, never conclusive alone). Zero dependency: reads /proc, /sys,
/etc and (on WSL) the Windows-side .wslconfig; external tools are never required.

Read-only by design; tuning suggestions are commands for the user to run, never executed.
Exit codes: 0 = no FAIL, 1 = at least one FAIL, 2 = usage error.
"""
import argparse
import json
import os
import re
import time
import sys

LEVELS = ("PASS", "INFO", "WARN", "FAIL", "SKIP")


# ---------------------------------------------------------------- pure helpers (selftest targets)

def is_wsl(proc_version: str, env: dict, run_wsl_exists=None) -> bool:
    """WSL_DISTRO_NAME authoritative; kernel string only with /run/WSL confirmation
    (docker containers on a WSL2 host see the host kernel string)."""
    if env.get("WSL_DISTRO_NAME"):
        return True
    if "microsoft" not in (proc_version or "").lower():
        return False
    if run_wsl_exists is None:
        run_wsl_exists = os.path.exists("/run/WSL")
    return bool(run_wsl_exists)


def parse_cpu_stat(text: str):
    """First 'cpu' line -> total and idle jiffies (idle + iowait)."""
    for line in (text or "").splitlines():
        if line.startswith("cpu "):
            vals = [int(x) for x in line.split()[1:]]
            idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
            return sum(vals), idle
    return None, None


def cpu_util(s1, s2):
    """Two (total, idle) samples -> utilization percent, or None on degenerate input."""
    if not s1 or not s2 or s1[0] is None or s2[0] is None:
        return None
    dt = s2[0] - s1[0]
    di = s2[1] - s1[1]
    if dt <= 0:
        return None
    return round(100.0 * (dt - di) / dt, 1)


def parse_meminfo(text: str) -> dict:
    """/proc/meminfo -> {key: kB} (Int values only)."""
    out = {}
    for line in (text or "").splitlines():
        m = re.match(r"^(\w+):\s+(\d+)\s*kB", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def mem_avail_level(avail_kb, total_kb):
    """Pinned: <5% of total = FAIL, <10% = WARN, else PASS (available is the right gauge,
    not free). Degenerate total -> PASS."""
    if not total_kb or total_kb <= 0 or avail_kb is None:
        return "PASS"
    frac = avail_kb / total_kb
    if frac < 0.05:
        return "FAIL"
    if frac < 0.10:
        return "WARN"
    return "PASS"


def parse_vmstat(text: str) -> dict:
    """/proc/vmstat -> {key: int} (pswpin/pswpout are pages, not kb)."""
    out = {}
    for line in (text or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and re.match(r"^\d+$", parts[1]):
            out[parts[0]] = int(parts[1])
    return out


def swap_rates_kb_s(v1, v2, page_bytes=4096, interval_s=1.0):
    """Two vmstat samples -> (swap-in KB/s, swap-out KB/s). None keys -> (0.0, 0.0)."""
    if interval_s <= 0:
        return (0.0, 0.0)
    pin = (v2.get("pswpin", 0) - v1.get("pswpin", 0)) * page_bytes / 1024 / interval_s
    pout = (v2.get("pswpout", 0) - v1.get("pswpout", 0)) * page_bytes / 1024 / interval_s
    return (max(pin, 0.0), max(pout, 0.0))


def swap_level(pin_kb_s, pout_kb_s):
    """Pinned (heuristic): both directions >200 KB/s = FAIL (thrash); >100 = WARN;
    one-directional paging is healthy (does not fire)."""
    if pin_kb_s > 200 and pout_kb_s > 200:
        return "FAIL"
    if pin_kb_s > 100 or pout_kb_s > 100:
        return "WARN"
    return "PASS"


def load_level(load1, cores):
    """Pinned (consensus): load/cores >1.0 = WARN (saturated), >0.7 = INFO (watch)."""
    if not cores or load1 is None:
        return "INFO"
    r = load1 / cores
    if r > 1.0:
        return "WARN"
    if r > 0.7:
        return "INFO"
    return "PASS"


def parse_cpu_max(text: str):
    """/sys/fs/cgroup/cpu.max: "max 100000" -> None (unlimited); "200000 100000" -> 2.0 cores."""
    parts = (text or "").split()
    if len(parts) == 2 and parts[0] != "max" and parts[1].isdigit() and int(parts[1]) > 0:
        return round(int(parts[0]) / int(parts[1]), 2)
    return None


SIZE_RE = re.compile(r"^(\d+)\s*(KB|MB|GB|TB)$", re.IGNORECASE)


def parse_size_gb(value: str):
    """.wslconfig values like "8GB" / "512MB" -> float GB, or None."""
    m = SIZE_RE.match((value or "").strip())
    if not m:
        return None
    n = float(m.group(1))
    unit = m.group(2).upper()
    return n / (1024 if unit == "MB" else 1) if unit in ("MB", "GB") else n * 1024 if unit == "TB" else None


def parse_wslconfig(text: str) -> dict:
    """.wslconfig -> {"wsl2": {...}, "experimental": {...}}; keeps raw strings; skips comments."""
    conf, cur = {}, None
    for raw in (text or "").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        m = re.match(r"^\[(.+)\]$", line)
        if m:
            cur = m.group(1).strip()
            conf[cur] = {}
            continue
        if cur and "=" in line:
            k, _, v = line.partition("=")
            conf[cur][k.strip()] = v.strip()
    return conf


def wslconfig_findings(conf: dict):
    """Advice over parsed .wslconfig (raw values only; no invented defaults)."""
    out = []
    w2 = conf.get("wsl2", {})
    exp = conf.get("experimental", {})
    amr = exp.get("autoMemoryReclaim", "").strip().lower()
    if amr == "disabled":
        out.append(("wsconf.amr-disabled", "INFO",
                    "autoMemoryReclaim=disabled: idle WSL page cache is not returned to Windows "
                    "(vmmem stays large)",
                    "Suggest: set [experimental] autoMemoryReclaim=dropCache in .wslconfig — "
                    "but note known reports of conflicts with Docker inside WSL; your call."))
    if amr == "gradual":
        out.append(("wsconf.amr-gradual", "INFO",
                    "autoMemoryReclaim=gradual: continuous reclaim enabled",
                    "Known user reports of UI hiccups; dropCache is batch instead. Only change if symptomatic."))
    return out


# ---------------------------------------------------------------- runtime probes

def read_text(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def fnd(fid, level, title, evidence, hint, basis):
    return {"id": fid, "level": level, "title": title, "evidence": evidence,
            "hint": hint, "basis": basis}


def effective_cores(env, timeout):
    """CPU count as the VM actually sees it: cgroup cpu.max quota wins over os.cpu_count()."""
    cores = os.cpu_count() or 1
    cm = read_text("/sys/fs/cgroup/cpu.max")
    limited = parse_cpu_max(cm)
    src = "os.cpu_count"
    if limited is not None:
        cores = max(int(limited), 1)
        src = "cgroup cpu.max"
    return cores, limited, src


def probe_cpu(env, timeout, sample_s):
    out = []
    cores, limited, src = effective_cores(env, timeout)
    ev = [f"cores={cores} (from {src})"]
    if limited is not None:
        out.append(fnd("cpu.cgroup-limit", "INFO",
                       f"CPU limited by cgroup to {limited} cores", ev, None, "n/a"))
    t1 = read_text("/proc/stat")
    s1 = parse_cpu_stat(t1)
    time.sleep(sample_s)
    s2 = parse_cpu_stat(read_text("/proc/stat"))
    util = cpu_util(s1, s2)
    if util is None:
        out.append(fnd("cpu.util", "SKIP", "CPU utilization not sampleable (no /proc/stat)",
                       ev, None, "n/a"))
    else:
        ev.append(f"utilization={util}% over {sample_s}s sample")
        level = "WARN" if util > 85 else "PASS"
        out.append(fnd("cpu.util", level, f"CPU utilization {util}%", ev,
                       "Sustained >85% with load high: close heavy jobs or add cores "
                       "(.wslconfig processors= on WSL)." if level == "WARN" else None,
                       "heuristic"))
    try:
        l1, _, l15 = os.getloadavg()
        lvl = load_level(l1, cores)
        out.append(fnd("cpu.load", lvl if lvl != "INFO" else "INFO",
                       f"load1={l1:.2f} load15={l15:.2f} over {cores} cores → {lvl}",
                       [f"ratio(load1/cores)={l1 / cores:.2f}"],
                       ("Linux load includes D-state (IO) tasks: load high + CPU% low ≈ storage "
                        "bottleneck, cross-check disk/IO before blaming CPU.") if lvl == "WARN" else None,
                       "consensus"))
    except OSError:
        pass
    return out


def probe_memory(env, timeout, sample_s):
    out = []
    mi = parse_meminfo(read_text("/proc/meminfo"))
    total = mi.get("MemTotal")
    avail = mi.get("MemAvailable")
    if not total:
        out.append(fnd("mem.info", "SKIP", "MemTotal unavailable (no /proc/meminfo)",
                       [], None, "n/a"))
        return out
    if avail is not None:
        lvl = mem_avail_level(avail, total)
        pct = 100.0 * avail / total
        out.append(fnd("mem.available", lvl,
                       f"MemAvailable {avail // 1024}MB / {total // 1024}MB ({pct:.0f}%) → {lvl}",
                       ["gauge: MemAvailable (not MemFree) — free is mostly page cache"],
                       ("Close memory-heavy jobs; on WSL also raise .wslconfig memory= (Windows-side "
                        "edit + wsl --shutdown, user action).") if lvl in ("WARN", "FAIL") else None,
                       "heuristic"))
    v1 = parse_vmstat(read_text("/proc/vmstat"))
    time.sleep(sample_s)
    v2 = parse_vmstat(read_text("/proc/vmstat"))
    pin, pout = swap_rates_kb_s(v1, v2, page_bytes=4096, interval_s=sample_s)
    lvl = swap_level(pin, pout)
    stotal = mi.get("SwapTotal", 0)
    out.append(fnd("mem.swap-rate", lvl,
                   f"swap in/out {pin:.0f}/{pout:.0f} KB/s → {lvl}"
                   + (f" (swap total {stotal // 1024}MB)" if stotal else " (no swap configured)"),
                   ["gauge: pswpin/pswpout rate (not pgpgin/out — that includes file cache)"],
                   ("Sustained bidirectional swapping = memory pressure. Reduce working set or add "
                    "memory (.wslconfig memory= on WSL).") if lvl in ("WARN", "FAIL") else None,
                   "heuristic"))
    # cgroup ceiling (WSL2 / containers): the real ceiling is often below MemTotal
    cmax = read_text("/sys/fs/cgroup/memory.max").strip()
    if cmax and cmax != "max":
        try:
            maxb = int(cmax)
            ccur = int(read_text("/sys/fs/cgroup/memory.current").strip() or 0)
            out.append(fnd("mem.cgroup-ceiling", "INFO",
                           f"cgroup memory limit {maxb // 1024 // 1024}MB "
                           f"(current {ccur * 100 // maxb}% of ceiling)",
                           ["cgroup v2 memory.max/memory.current"],
                           None, "n/a"))
        except ValueError:
            pass
    return out


def probe_wsl2(timeout):
    out = []
    pv = read_text("/proc/version")
    if not is_wsl(pv, dict(os.environ)):
        out.append(fnd("wsl2.not-wsl", "SKIP", "Not WSL — WSL2 tuning section skipped",
                       [], None, "n/a"))
        return out
    out.append(fnd("wsl2.detected", "INFO",
                   f"WSL detected (distro={os.environ.get('WSL_DISTRO_NAME', '?')})",
                   [], None, "n/a"))
    # Windows-side .wslconfig (read-only)
    cfg_text, cfg_path = "", None
    for root in ("/mnt/c/Users",):
        try:
            for user in sorted(os.listdir(root)):
                p = os.path.join(root, user, ".wslconfig")
                if os.path.isfile(p):
                    cfg_path, cfg_text = p, read_text(p)
                    break
        except OSError:
            pass
        if cfg_path:
            break
    if not cfg_path:
        out.append(fnd("wsl2.no-wslconfig", "INFO",
                       ".wslconfig not found — defaults in effect "
                       "(memory=min(50% host RAM, 8GB), swap=25% of memory)",
                       ["source: Microsoft WSL docs, learn.microsoft.com/windows/wsl/wsl-config"],
                       "Set memory=/processors= in %UserProfile%\\.wslconfig to bound the VM "
                       "(apply via `wsl --shutdown` from Windows — user action).", "consensus"))
    else:
        conf = parse_wslconfig(cfg_text)
        w2 = conf.get("wsl2", {})
        shown = {k: w2[k] for k in ("memory", "processors", "swap") if k in w2}
        out.append(fnd("wsl2.wslconfig", "INFO",
                       f".wslconfig found ({cfg_path})" + (f": {shown}" if shown else " (no wsl2 memory/processors/swap overrides)"),
                       [f"sections={sorted(conf.keys())}"], None, "consensus"))
        for fid, level, title, hint in wslconfig_findings(conf):
            out.append(fnd(fid, level, title, [], hint, "heuristic"))
    return out


# ---------------------------------------------------------------- selftest

def selftest():
    """Dual-direction fixtures: true positives fire, legal decoys stay silent (p000023)."""
    ok = []

    # is_wsl (same contract as env-check)
    ok.append(is_wsl("Linux 5.15 gcc", {}) is False)
    ok.append(is_wsl("microsoft-standard-WSL2", {}, run_wsl_exists=True) is True)
    ok.append(is_wsl("", {"WSL_DISTRO_NAME": "Ubuntu"}) is True)
    ok.append(is_wsl("microsoft-standard-WSL2", {}, run_wsl_exists=False) is False)  # container decoy

    # cpu sampling
    s1 = parse_cpu_stat("cpu  100 0 100 800 0 0 0 0 0 0\n")
    s2 = parse_cpu_stat("cpu  150 0 150 1200 0 0 0 0 0 0\n")
    ok.append(cpu_util(s1, s2) == 20.0)                      # 200 busy of 1000 = 20%
    ok.append(cpu_util(None, s2) is None)                    # decoy: missing sample
    ok.append(cpu_util(s1, s1) is None)                      # decoy: zero delta
    ok.append(cpu_util((None, None), (None, None)) is None)  # regression: macOS has no /proc/stat

    # meminfo
    mi = parse_meminfo("MemTotal: 8000000 kB\nMemAvailable: 1000000 kB\nSwapTotal: 2000000 kB\nHugePages_Total: 0\n")
    ok.append(mi.get("MemTotal") == 8000000 and "HugePages_Total" not in mi)
    ok.append(mem_avail_level(1200000, 8000000) == "PASS")   # 15% decoy
    ok.append(mem_avail_level(700000, 8000000) == "WARN")    # 8.75%
    ok.append(mem_avail_level(300000, 8000000) == "FAIL")    # 3.75%
    ok.append(mem_avail_level(4000000, 8000000) == "PASS")   # decoy: healthy
    ok.append(mem_avail_level(100, 0) == "PASS")             # degenerate

    # vmstat swap rate
    v1 = parse_vmstat("pswpin 100\npswpout 200\npgpgin 999999\n")
    v2 = parse_vmstat("pswpin 200\npswpout 400\npgpgin 999999\n")
    pin, pout = swap_rates_kb_s(v1, v2, 4096, 1.0)
    ok.append(pin == 400.0 and pout == 800.0)          # 100/200 pages * 4KB over 1s
    ok.append(swap_level(pin, pout) == "FAIL")               # both >200
    ok.append(swap_level(300, 20) == "WARN")                 # one-way out — heavy but not thrash
    ok.append(swap_level(50, 50) == "PASS")                  # decoy: quiet
    ok.append(swap_rates_kb_s(v1, v2, 4096, 0.0) == (0.0, 0.0))  # degenerate interval

    # load
    ok.append(load_level(8.0, 4) == "WARN" and load_level(2.9, 4) == "INFO"
              and load_level(1.0, 4) == "PASS" and load_level(None, None) == "INFO")

    # cgroup cpu.max
    ok.append(parse_cpu_max("max 100000\n") is None)         # decoy: unlimited
    ok.append(parse_cpu_max("200000 100000\n") == 2.0)       # 2 cores quota

    # .wslconfig
    conf = parse_wslconfig("[wsl2]\nmemory=8GB # cap\nprocessors=4\n[experimental]\nautoMemoryReclaim=gradual\n")
    ok.append(conf["wsl2"]["memory"] == "8GB" and conf["wsl2"]["processors"] == "4")
    ok.append(parse_size_gb("8GB") == 8.0 and parse_size_gb("512MB") == 0.5
              and parse_size_gb("1TB") == 1024.0 and parse_size_gb("bogus") is None)
    fired = {f[0] for f in wslconfig_findings(conf)}
    ok.append("wsconf.amr-gradual" in fired and "wsconf.amr-disabled" not in fired)
    conf2 = parse_wslconfig("[wsl2]\nswap=0\n")
    ok.append(wslconfig_findings(conf2) == [])               # decoy: no AMR keys

    bad = [i for i, v in enumerate(ok) if not v]
    print(f"perf-check selftest: {len(ok) - len(bad)}/{len(ok)} assertions pass")
    if bad:
        print(f"  FAILED assertions: {bad}")
        return 1
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="perf-check", description="Read-only machine performance check")
    ap.add_argument("--sample", type=float, default=2.0,
                    help="sampling window seconds for CPU/swap deltas (default 2.0)")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON report")
    ap.add_argument("--selftest", action="store_true", help="run fixture assertions and exit")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.sample <= 0 or args.sample > 60:
        print("perf-check: --sample must be in (0, 60]", file=sys.stderr)
        return 2

    env = dict(os.environ)
    findings = []
    findings.extend(probe_memory(env, args.sample, args.sample))
    findings.extend(probe_cpu(env, args.sample, args.sample))
    findings.extend(probe_wsl2(args.sample))

    for f in findings:
        f.setdefault("evidence", [])
        f.setdefault("hint", None)
        f.setdefault("basis", "n/a")
        if f.get("level") not in LEVELS:
            f["level"] = "INFO"
    has_fail = any(f["level"] == "FAIL" for f in findings)
    report = {
        "schema": "perf-check/1",
        "platform": {"wsl": is_wsl(read_text("/proc/version"), env),
                     "wsl_distro": env.get("WSL_DISTRO_NAME")},
        "exit_meaning": "0 = no FAIL, 1 = FAIL present",
        "basis_legend": "consensus = authoritative threshold; heuristic = experience line, WARN only",
        "findings": findings,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        counts = {}
        for f in findings:
            counts[f["level"]] = counts.get(f["level"], 0) + 1
        print(f"perf-check: {sum(counts.values())} findings — " +
              " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        for f in findings:
            tag = f"[{f['level']}]" + ("" if f["basis"] in ("n/a",) else f"[{f['basis']}]")
            print(f"  {tag} {f['title']}")
            for e in f["evidence"]:
                print(f"        {e}")
            if f.get("hint"):
                print(f"        suggest: {f['hint']}")
    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())

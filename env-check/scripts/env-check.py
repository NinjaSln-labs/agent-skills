#!/usr/bin/env python3
"""env-check — read-only development environment health check (MVP: toolchain / env vars / WSL interop).

Read-only by design: every probe is a read (which/--version, env parse, socket connect, file read).
No repair is ever executed; findings carry fix commands for the user to run themselves.

Exit codes: 0 = no FAIL findings (WARN allowed), 1 = at least one FAIL, 2 = usage error.
"""
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys

DEFAULT_TOOLS = ("node", "npm", "python3", "pip3", "git")

LEVELS = ("PASS", "INFO", "WARN", "FAIL", "SKIP")
LEVEL_RANK = {"PASS": 0, "INFO": 1, "SKIP": 1, "WARN": 2, "FAIL": 3}


# ---------------------------------------------------------------- pure helpers (selftest targets)

def is_wsl(proc_version: str, env: dict, run_wsl_exists=None) -> bool:
    """WSL detection: WSL_DISTRO_NAME env is authoritative; kernel string as fallback but
    confirmed by /run/WSL existence — docker containers on a WSL2 host see the host kernel
    string (microsoft) in /proc/version yet have no interop, so kernel string alone lies."""
    if env.get("WSL_DISTRO_NAME"):
        return True
    if "microsoft" not in (proc_version or "").lower():
        return False
    if run_wsl_exists is None:
        run_wsl_exists = os.path.exists("/run/WSL")
    return bool(run_wsl_exists)


def proxy_endpoint(value: str):
    """Extract (host, port) from proxy values: http://host:port, host:port, socks5://host:port.
    None if unparseable or no port (portless targets are not probed)."""
    if not value:
        return None
    v = value.strip()
    v = re.sub(r"^[a-z0-9+]+://", "", v.lower())
    v = v.split("/")[0]
    if v.startswith("["):  # IPv6 literal [::1]:8080
        m = re.match(r"^\[(.+)\]:(\d+)$", v)
        return (m.group(1), int(m.group(2))) if m else None
    if ":" not in v:
        return None
    host, _, port = v.rpartition(":")
    if not host or not port.isdigit():
        return None
    return (host, int(port))


def path_findings(entries):
    """Pure part of PATH hygiene: duplicates (later occurrence flagged) and empty entries.
    Existence checks are runtime (needs the filesystem). Returns list of (index, kind, entry)."""
    out = []
    seen = set()
    for i, e in enumerate(entries):
        if e == "":
            out.append((i, "empty", e))
            continue
        if e in seen:
            out.append((i, "dup", e))
            continue
        seen.add(e)
    return out


def shadowed(tool, hits):
    """A tool is shadowed when `which -a` resolves to more than one distinct path."""
    distinct = list(dict.fromkeys(hits))
    return (tool, distinct) if len(distinct) > 1 else None


def parse_wsl_conf(text: str) -> dict:
    """Minimal INI parse of /etc/wsl.conf → {section: {key: value}}."""
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


def wsl_conf_findings(conf: dict):
    """Judgements over parsed wsl.conf. PASS/WARN per key; absence of a key = PASS (default is fine)."""
    out = []
    interop = conf.get("interop", {})
    if interop.get("enabled", "").lower() == "false":
        out.append(("wsl.interop-disabled", "WARN",
                    "/etc/wsl.conf disables Windows interop (interop.enabled=false)",
                    "Windows executables will not resolve inside WSL. Re-enable if you need them."))
    if conf.get("automount", {}).get("enabled", "").lower() == "false":
        out.append(("wsl.automount-disabled", "WARN",
                    "/etc/wsl.conf disables automount (automount.enabled=false)",
                    "/mnt/c will not exist. Re-enable if you expect Windows files."))
    return out


def autocrlf_level(value: str):
    """core.autocrlf=true on WSL/macOS/Linux → WARN (CRLF churn with Linux-side tooling)."""
    v = (value or "").strip().lower()
    if v == "true":
        return ("git.autocrlf", "WARN",
                "git core.autocrlf=true on a Unix-side checkout",
                "Causes CRLF churn in mixed OS repos. Suggest: git config --global core.autocrlf input")
    return None


# ---------------------------------------------------------------- runtime probes

def run_cmd(argv, timeout=10):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except FileNotFoundError:
        return None, ""
    except subprocess.TimeoutExpired:
        return None, "timeout"


def probe_tool(name, timeout):
    f = {"id": f"tool.{name}", "level": None, "title": "", "evidence": [], "hint": None}
    path = shutil.which(name)
    if not path:
        f.update(level="WARN", title=f"{name}: not found on PATH",
                 hint=f"Install {name} or expose it on PATH (version-manager shims often miss non-login shells).")
        return f
    f["evidence"].append(f"which {name} -> {path}")
    rc, out = run_cmd([name, "--version"], timeout=timeout)
    if rc == 0:
        first = (out or "").strip().splitlines()[0] if out.strip() else ""
        f["evidence"].append(f"{name} --version -> {first}")
        f["title"] = f"{name}: {first}"
        f["level"] = "PASS"
    else:
        f["update"] = None
        f.update(level="WARN", title=f"{name}: on PATH but --version failed (rc={rc})",
                 hint="Binary exists but does not run — possibly broken install or wrong arch.")
    rc2, out2 = run_cmd(["which", "-a", name], timeout=timeout)
    if rc2 == 0:
        hits = [os.path.realpath(l.strip()) for l in out2.splitlines() if l.strip()]
        sh = shadowed(name, hits)
        if sh:
            f["level"] = "WARN"
            f["evidence"].append("which -a: " + " | ".join(sh[1]))
            f["hint"] = (f"{name} resolves to {len(sh[1])} locations; the first wins. "
                         f"Check version-manager vs system install ordering in PATH.")
    return f


def probe_env_vars(timeout):
    out = []
    # PATH hygiene
    entries = os.environ.get("PATH", "").split(os.pathsep)
    for i, kind, e in path_findings(entries):
        out.append({"id": f"env.path.{kind}.{i}", "level": "WARN",
                    "title": f"PATH entry #{i + 1} is {'empty' if kind == 'empty' else 'a duplicate'}: '{e}'",
                    "evidence": [f"PATH[{i}] = {e!r}"],
                    "hint": "Clean PATH in your shell profile; duplicates slow lookup and empty entries mean cwd."})
    for i, e in enumerate(entries):
        if e and not os.path.isdir(e):
            out.append({"id": f"env.path.missing.{i}", "level": "WARN",
                        "title": f"PATH entry does not exist: {e}",
                        "evidence": [f"PATH[{i}] = {e!r}"],
                        "hint": "Stale entry — remove it from your shell profile."})
    # proxy reachability
    for var in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        val = os.environ.get(var) or os.environ.get(var.lower())
        if not val:
            continue
        ep = proxy_endpoint(val)
        if not ep:
            out.append({"id": f"env.{var}.unparseable", "level": "INFO",
                        "title": f"{var}={val} (no port — not probed)", "evidence": [f"{var}={val}"],
                        "hint": None})
            continue
        host, port = ep
        try:
            s = socket.create_connection((host, port), timeout=timeout)
            s.close()
            out.append({"id": f"env.{var}.ok", "level": "PASS",
                        "title": f"{var} -> {host}:{port} reachable", "evidence": [f"{var}={val}"],
                        "hint": None})
        except OSError as exc:
            out.append({"id": f"env.{var}.dead", "level": "FAIL",
                        "title": f"{var} -> {host}:{port} unreachable ({exc.__class__.__name__})",
                        "evidence": [f"{var}={val}", f"connect error: {exc}"],
                        "hint": "Installs/downloads will fail. Fix: unset the var or point it at a live proxy."})
    lang = os.environ.get("LANG")
    if not lang or lang == "C":
        out.append({"id": "env.lang", "level": "WARN", "title": f"LANG={lang!r} (unset or POSIX)",
                    "evidence": [f"LANG={lang!r}"],
                    "hint": "UTF-8 tooling may misbehave. Suggest: export LANG=en_US.UTF-8 (or your locale)."})
    return out


def probe_wsl(timeout, proc_version=None, env=None, run_wsl_exists=None):
    """env/proc_version/run_wsl_exists injectable for branch-level selftest (real runs use live values)."""
    out = []
    if proc_version is None:
        proc_version = _read_proc_version()
    if env is None:
        env = dict(os.environ)
    if not is_wsl(proc_version, env, run_wsl_exists):
        out.append({"id": "wsl.not-wsl", "level": "SKIP", "title": "Not WSL — interop section skipped",
                    "evidence": [], "hint": None})
        return out, False
    out.append({"id": "wsl.detected", "level": "INFO",
                "title": f"WSL detected (distro={env.get('WSL_DISTRO_NAME', '?')})",
                "evidence": [proc_version.strip()], "hint": None})
    # Windows PATH injection
    win_entries = [e for e in os.environ.get("PATH", "").split(os.pathsep)
                   if e.startswith("/mnt/c") or e.startswith("/mnt/d") or e.startswith("/mnt/")]
    if win_entries:
        out.append({"id": "wsl.win-path", "level": "WARN",
                    "title": f"{len(win_entries)} Windows PATH entries injected into WSL PATH",
                    "evidence": win_entries[:5] + (["…"] if len(win_entries) > 5 else []),
                    "hint": ("Windows binaries can shadow Linux ones. Fix: in /etc/wsl.conf set "
                             "[interop] appendWindowsPath=false, then `wsl --shutdown` from Windows.")})
    # /etc/wsl.conf
    try:
        conf = parse_wsl_conf(open("/etc/wsl.conf", encoding="utf-8", errors="replace").read())
        for fid, level, title, hint in wsl_conf_findings(conf):
            out.append({"id": fid, "level": level, "title": title,
                        "evidence": ["see /etc/wsl.conf"], "hint": hint})
        if not any(f["id"].startswith("wsl.") and f["level"] != "SKIP" for f in out[-3:]):
            out.append({"id": "wsl.conf-ok", "level": "PASS",
                        "title": "/etc/wsl.conf present, no disabling flags", "evidence": [], "hint": None})
    except OSError:
        out.append({"id": "wsl.no-conf", "level": "PASS",
                    "title": "/etc/wsl.conf absent (defaults apply)", "evidence": [], "hint": None})
    # git autocrlf
    if shutil.which("git"):
        rc, outp = run_cmd(["git", "config", "--global", "core.autocrlf"], timeout=timeout)
        if rc == 0 and outp.strip():
            f = autocrlf_level(outp.strip())
            if f:
                out.append({"id": f[0], "level": f[1], "title": f[2], "evidence": [f"core.autocrlf={outp.strip()}"],
                            "hint": f[3]})
    return out, True


# ---------------------------------------------------------------- selftest

def selftest():
    """Dual-direction: true positives must fire, legal decoys must not (p000023)."""
    ok = []

    # is_wsl: true positives + decoys (incl. docker-on-WSL2 container: kernel string but no /run/WSL)
    ok.append(is_wsl("Linux version 5.15 (gcc)", {}) is False)                      # decoy: plain kernel
    ok.append(is_wsl("Linux version 5.15 microsoft-standard-WSL2", {},
                     run_wsl_exists=True) is True)                                  # true: kernel + /run/WSL
    ok.append(is_wsl("", {"WSL_DISTRO_NAME": "Ubuntu"}) is True)                    # true: env authoritative
    ok.append(is_wsl("Linux version 5.15 microsoft-standard-WSL2", {},
                     run_wsl_exists=False) is False)                                # decoy: container on WSL host

    # proxy_endpoint: true positives + decoys
    ok.append(proxy_endpoint("http://127.0.0.1:7890") == ("127.0.0.1", 7890))
    ok.append(proxy_endpoint("socks5://[::1]:1080") == ("::1", 1080))
    ok.append(proxy_endpoint("host.example:8080") == ("host.example", 8080))
    ok.append(proxy_endpoint("http://no-port-host") is None)                        # decoy: portless
    ok.append(proxy_endpoint("") is None)

    # path_findings
    pf = path_findings(["/a", "", "/b", "/a"])
    ok.append((1, "empty", "") in pf and (3, "dup", "/a") in pf)
    ok.append(path_findings(["/a", "/b"]) == [])                                    # decoy: clean

    # shadowed
    ok.append(shadowed("node", ["/usr/bin/node", "/mnt/c/x/node.exe"]) ==
              ("node", ["/usr/bin/node", "/mnt/c/x/node.exe"]))
    ok.append(shadowed("node", ["/usr/bin/node"]) is None)                          # decoy: single
    ok.append(shadowed("node", ["/usr/bin/node", "/usr/bin/node"]) is None)         # decoy: same path twice

    # wsl.conf
    conf = parse_wsl_conf("[interop]\nenabled=false # off\n[automount]\nenabled = true")
    ok.append(conf == {"interop": {"enabled": "false"}, "automount": {"enabled": "true"}})
    fires = {f[0] for f in wsl_conf_findings(conf)}
    ok.append("wsl.interop-disabled" in fires and "wsl.automount-disabled" not in fires)  # one fires, decoy not
    ok.append(wsl_conf_findings({}) == [])                                          # decoy: defaults

    # autocrlf
    ok.append(autocrlf_level("true")[1] == "WARN")
    ok.append(autocrlf_level("input") is None)                                      # decoy
    ok.append(autocrlf_level("") is None)                                           # decoy

    # non-WSL branch: SKIP emitted, /etc/wsl.conf never consulted (this host HAS one — proves the branch)
    skip_findings, on_wsl = probe_wsl(5, proc_version="Linux version 6.1.0-generic (gcc)", env={})
    ok.append(on_wsl is False)
    ok.append(any(f["id"] == "wsl.not-wsl" and f["level"] == "SKIP" for f in skip_findings)
              and len(skip_findings) == 1)

    # WSL branch (platform-independent: inject the /proc/version content — macOS has no /proc/version)
    wsl_findings, on_wsl2 = probe_wsl(5, proc_version="Linux version 5.15.0-microsoft-standard-WSL2",
                                      env={}, run_wsl_exists=True)
    ok.append(on_wsl2 is True and any(f["id"] == "wsl.detected" for f in wsl_findings))

    bad = [i for i, v in enumerate(ok) if not v]
    print(f"env-check selftest: {len(ok) - len(bad)}/{len(ok)} assertions pass")
    if bad:
        print(f"  FAILED assertions: {bad}")
        return 1
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(prog="env-check", description="Read-only dev environment health check")
    ap.add_argument("--tools", default=",".join(DEFAULT_TOOLS),
                    help=f"comma-separated tools to probe (default: {','.join(DEFAULT_TOOLS)})")
    ap.add_argument("--timeout", type=int, default=5, help="per-probe timeout seconds (default 5)")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON report")
    ap.add_argument("--selftest", action="store_true", help="run fixture assertions and exit")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    findings = []
    for t in tools:
        findings.append(probe_tool(t, args.timeout))
    findings.extend(probe_env_vars(args.timeout))
    wsl_findings, _ = probe_wsl(args.timeout)
    findings.extend(wsl_findings)

    for f in findings:
        f.setdefault("evidence", [])
        if f.get("level") not in LEVELS:
            f["level"] = "INFO"
    has_fail = any(f["level"] == "FAIL" for f in findings)
    report = {
        "schema": "env-check/1",
        "platform": {"wsl": is_wsl(_read_proc_version(), dict(os.environ)),
                     "wsl_distro": os.environ.get("WSL_DISTRO_NAME"),
                     "kernel": _read_proc_version().strip()},
        "exit_meaning": "0 = no FAIL, 1 = FAIL present",
        "findings": findings,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        counts = {}
        for f in findings:
            counts[f["level"]] = counts.get(f["level"], 0) + 1
        print(f"env-check: {sum(counts.values())} findings — " +
              " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        for f in findings:
            print(f"  [{f['level']}] {f['title']}")
            for e in f["evidence"]:
                print(f"        {e}")
            if f.get("hint"):
                print(f"        fix: {f['hint']}")
    return 1 if has_fail else 0


def _read_proc_version():
    try:
        return open("/proc/version", encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


if __name__ == "__main__":
    sys.exit(main())

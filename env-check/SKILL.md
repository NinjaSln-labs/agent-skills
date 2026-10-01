---
name: env-check
description: >-
  Environment check: read-only health inspection of the local dev environment —
  toolchain presence/version/shadowing, PATH and proxy env vars, disk space and
  inodes, dev-port occupancy (--ports), dependency-tree integrity (node_modules,
  broken venvs), and WSL2/Windows interop (PATH injection, autocrlf, wsl.conf).
  Produces a structured report with fix commands; never executes fixes itself. Use
  when builds fail with "works on my machine" symptoms, commands resolve to wrong
  binaries, a proxy blocks installs, disk/inode space runs out, a dev port is
  occupied, or WSL PATH is polluted. NOT for: system performance tuning, security scanning
  (secrets/dependencies/config), or AI session health.
slug: env-check
version: 1.1.0
displayName: env-check
---
# Env Check

Read-only health inspection of the local development environment. Diagnoses **"can it run"**, never tunes performance, never scans for threats, and **never executes a fix** — every finding carries a fix command for the user to run themselves.

## 中文速览（Quick Guide）

- **做什么**：对开发环境做只读体检（六维：工具链／环境变量／WSL 互操作／磁盘与 inode／端口占用（--ports 指定）／依赖完整性），产出 `[级别] 标题＋证据＋修复命令` 的报告与 `--json` 机读版。
- **何时用**：「我这里跑不起来／明明装了却找不到命令」「代理挂着但装不动包」「WSL 里命中了 Windows 侧的二进制」等环境类问题。
- **核心步骤**：跑 `scripts/env-check.py`（自测先过 `--selftest`）→ 逐条读 FAIL/WARN → 把 `fix:` 行的命令**原样给用户确认执行**（本技能永不代执行）→ 需要平台细节查 `references/`。
- **国内可达性边界**：全部检测本地完成、零依赖零网络（代理连通性探测是对用户已配置代理的本机端口探测）；无外链、无下载。

## When to Use

- A build or install fails with environment-flavored symptoms: `command not found` for an installed tool, wrong binary version, proxy timeouts.
- User asks for an environment checkup / "体检" / "为什么我这里跑不起来".
- On WSL: suspicious Windows-side shadowing (`/mnt/c/...` binaries winning), CRLF churn.

NOT for: performance tuning (CPU/memory/disk speed), security scanning of code or dependencies, project config review, AI session health.

## Hard Constraints

1. **Read-only** — probes are `which`/`--version`/env parsing/socket connect to already-configured proxy ports/file reads. Nothing is written, nothing is installed, no service is started.
2. **Never execute fixes** — output fix commands as text. The user runs them. No `--fix` mode exists (deliberately: repair actions are system-state changes).
3. **Evidence, not vibes** — every finding carries machine-collected evidence lines; if a signal can't be read, report it as such (SKIP/INFO), never guess.
4. **Criteria live in the script** — PASS/WARN/FAIL thresholds are pinned in `scripts/env-check.py`, not re-judged ad hoc. Run `--selftest` first if the script was just modified.

## Workflow

1. Run the checker:
   ```
   python3 scripts/env-check.py                # human report
   python3 scripts/env-check.py --json         # machine-readable (schema env-check/1)
   python3 scripts/env-check.py --tools node,deno,go   # extend the probe list
   python3 scripts/env-check.py --timeout 15   # per-probe timeout seconds (default 5)
   python3 scripts/env-check.py --ports 3000,8080      # check dev-port occupancy
   ```
   Exit codes: `0` = no FAIL (WARN allowed), `1` = at least one FAIL, `2` = usage error.
2. Read findings worst-first (FAIL → WARN). For each, relay the `fix:` command to the user and wait for them to run it.
3. For platform-specific detail (what each check reads, where wsl.conf/.wslconfig live, macOS notes), consult `references/checks-linux-wsl.md` or `references/checks-macos.md`.
4. Re-run after fixes to confirm the FAIL cleared.

## Check Matrix

| Dimension | Checks | Level logic |
|---|---|---|
| Toolchain | presence on PATH, `--version` runs, shadowing (distinct realpaths from `which -a`) | missing/broken = WARN (may be intentional); shadowed = WARN |
| Env vars | PATH hygiene (missing / duplicate / empty entries), proxy reachability (socket probe), LANG | dead proxy = **FAIL**; PATH/locale = WARN |
| WSL interop | Windows PATH injection into WSL, `/etc/wsl.conf` disabling flags, `core.autocrlf=true` | injection/autocrlf/disabled-flags = WARN |
| Disk & inodes | free space + inode usage for cwd's filesystem and `/` (deduped) | free <512MB or <1% = **FAIL**; <2GB or <5% = WARN; inodes <1% = **FAIL**, <5% = WARN |
| Ports | occupancy of user-specified ports (`--ports`), owner via lsof/ss when available | in use = WARN (killing is the user's call); none requested = SKIP |
| Dependency integrity | orphan `node_modules`, broken `.bin` symlinks, missing lockfile, broken venvs (pyvenv.cfg home + bin/python3) | orphan/broken venv/broken bins = WARN; no lockfile = INFO |

Platform coverage: the matrix runs on **WSL2/Linux, macOS (tested — see Platform Test Matrix), and plain Linux (container-tested)**; platform-specific reading detail lives in `references/checks-linux-wsl.md` (Linux/WSL) and `references/checks-macos.md`.

Deferred (do not improvise): version-manager conflict resolution beyond shadow reporting; a `--fix` whitelist mode (explicitly declined for now — user ruling: fixes are command suggestions only).

## Output Contract

Human report: one line per finding — `[LEVEL] title` + evidence lines + `fix:` command. JSON: `{"schema": "env-check/1", "platform": {...}, "findings": [{id, level, title, evidence[], hint}]}` — the JSON field is `hint`; the human report renders the same value as the `fix:` line. Levels: PASS / INFO / WARN / FAIL / SKIP. Downgrade, don't fabricate: an unreadable signal becomes INFO/SKIP with the reason.

## Platform Test Matrix (evidence-pinned, rule-12 style)

| Platform | Status | Evidence |
|---|---|---|
| WSL2 / Linux (this host) | **tested 2026-10-01** | normal run exit=0 (PASS=6/WARN=2, live findings); FAIL path exit=1 (`HTTPS_PROXY=http://127.0.0.1:9` → ConnectionRefusedError); non-WSL SKIP branch returns `wsl.not-wsl` without touching `/etc/wsl.conf`; selftest 34/34 (v1.1.0); 1.1 dims (disk/ports/dep-integrity) re-tested live |
| macOS 15.8.1 (x86_64, ssh host `mac`) | **tested 2026-10-01** | selftest 34/34 (v1.1.0); normal run exit=0 with real findings (MacPorts git shadowing `/opt/local/bin/git` vs `/usr/bin/git` = true positive; node/npm absent = WARN; WSL section SKIP); FAIL path exit=1; `--json` valid (schema env-check/1). macOS run exposed a selftest platform assumption (an assertion read live `/proc/version`) — fixed to injected fixture in 1.0.2; second platform assumption (live `/run/WSL` check inside the WSL-branch assertion) fixed likewise in 1.0.3; 1.1 dims re-tested live (disk PASS, port probe, orphan-node_modules fixture) |
| Windows native (no WSL) | **out of design scope, untested** | host has only the Microsoft Store python stub (no real interpreter); probes assume POSIX PATH/`/proc`. Windows coverage = the WSL2 row above (t000016 first-driver scenario) |
| Plain Linux (non-WSL, docker `ubuntu:24.04` container) | **tested 2026-10-01** | selftest 34/34 (v1.1.0); normal run exit=0 (true-positive WARNs re-confirmed); FAIL path exit=1; `wsl=False` in JSON; orphan-node_modules fixture fires. Container test caught a real bug: `/proc/version` shows the WSL2 **host** kernel inside containers → `is_wsl` now requires `/run/WSL` to confirm kernel-string signal (v1.0.3) |

Re-run on new hardware, then update this table with date + findings summary. Absence of a row entry means untested.

## Completion Criteria

- Checker ran with exit code reported; every FAIL/WARN has been relayed to the user **as commands, not executed**.
- No fix was executed by the agent; no file outside the working scratch was written.
- If the user wants a fix applied, they run the command; a follow-up `env-check` run confirms.

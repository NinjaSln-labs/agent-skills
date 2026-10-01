---
name: perf-check
description: >-
  Machine performance check: read-only sampling diagnosis of the dev machine's speed —
  memory pressure (MemAvailable gauge, swap thrash rate), CPU (load vs cores,
  utilization sampling), WSL2 resource tuning (cgroup ceilings, .wslconfig with
  autoMemoryReclaim advice), disk IO await per device, top CPU/memory processes, and
  macOS memory pressure (compressor gauge). Judgements follow the USE method; every
  threshold carries a basis tag (consensus vs heuristic). Read-only, tuning
  suggestions are commands for the user — never executed. Use when the machine feels
  slow, builds stall, memory pressure or swap activity is suspected, a process eats
  CPU/memory, disk latency is suspect, or WSL2 vmmem/VM sizing needs review. NOT for:
  runnability checks (env-check), application load testing, or AI session health.
slug: perf-check
version: 1.1.1
displayName: perf-check
---
# Perf Check

Read-only performance diagnosis of the development machine: **"is it fast"**, where env-check answers "can it run". Judgement skeleton is Brendan Gregg's **USE method** (Utilization / Saturation / Errors per resource). Every threshold is pinned in the script and tagged with its basis: `consensus` (authoritative) or `heuristic` (experience line — WARN only, never conclusive alone). Tuning suggestions are **commands for the user**; nothing is executed, nothing is tuned.

## 中文速览（Quick Guide）

- **做什么**：只读性能体检（1.1 六维：内存压力／CPU／WSL2 资源配置／磁盘 IO await／TOP 进程／macOS 压力判读），每条判据带 basis 标注（consensus＝权威共识／heuristic＝经验线），USE 方法骨架。
- **何时用**：「机器怎么这么卡」「构建越跑越慢」「怀疑内存压力/swap 抖动」「WSL2 的 vmmem 是不是又吃爆了」。
- **核心步骤**：跑 `scripts/perf-check.py`（改过脚本先 `--selftest`）→ 读 WARN/FAIL（先看 basis=heuristic 的提示「需交叉验证」）→ 把 `suggest:` 命令**原样给用户确认执行**（本技能永不代调）→ 平台细节查 `references/`。
- **国内可达性边界**：全部本地采样（/proc、/sys、/mnt/c 只读），零依赖零网络；微软官方阈值与命令仅作文字引用。

## When to Use

- Machine feels slow, builds progressively slower, compile jobs stall.
- Suspected memory pressure / swap thrash; WSL2 vmmem size review or VM sizing.
- NOT for: runnability issues (env-check: dead proxy, missing tools, disk nearly full), application load testing (k6), AI session health (session-health).

## Hard Constraints

1. **Read-only** — samples /proc, /sys, loadavg; reads Windows-side `.wslconfig` via /mnt/c. No writes, no sysctl changes, no process kills, no cache drops (`drop_caches` is a suggestion string only, never run).
2. **Never tune** — output `suggest:` commands as text. The user runs them. No `--fix` mode (repair actions are system-state changes).
3. **Pinned thresholds with basis tags** — PASS/WARN/FAIL logic lives in the script; each finding carries `basis: consensus | heuristic`. Heuristic WARNs say "cross-check" rather than convict.
4. **Gauge discipline** — MemAvailable not MemFree; pswpin/pswpout not pgpgin/out; high buff/cache is healthy, never a finding (it is what free memory is for).

## Workflow

1. Run:
   ```
   python3 scripts/perf-check.py             # human report (2s sampling window)
   python3 scripts/perf-check.py --json      # machine-readable (schema perf-check/1)
   python3 scripts/perf-check.py --sample 5  # longer sampling window (0 < s <= 60)
   ```
   Exit codes: `0` = no FAIL, `1` = at least one FAIL, `2` = usage error.
2. Read findings worst-first. For `basis=heuristic` WARNs, relay the cross-check hint instead of a verdict. Relay `suggest:` commands as text and wait for the user.
3. Platform detail: `references/checks-linux-wsl.md` (Linux/WSL thresholds & sources), `references/checks-macos.md` (macOS deltas).
4. Re-run after changes to compare.

## Check Matrix

| Dimension | Checks | Level logic (pinned in script) |
|---|---|---|
| Memory — available | MemAvailable vs MemTotal | <5% = **FAIL**, <10% = WARN, else PASS (basis: heuristic, gauge per proc_meminfo(5)) |
| Memory — swap thrash | pswpin/pswpout rate over sampling window | both >200 KB/s = **FAIL**, any direction >100 KB/s = WARN (includes the 100–200 both-directions zone), quiet = PASS (basis: heuristic) |
| Memory — cgroup ceiling | cgroup v2 memory.max/memory.current | INFO report (ceiling often < MemTotal on WSL/containers) |
| CPU — load | load1/cores (cgroup cpu.max quota wins as core count) | >1.0 = WARN, >0.7 = INFO (basis: consensus, Brendan Gregg) |
| CPU — utilization | /proc/stat double-sample delta | >85% = WARN (basis: heuristic) |
| WSL2 | .wslconfig reading (memory/processors/swap/autoMemoryReclaim), official defaults cited | INFO + advice; autoMemoryReclaim known-conflict notes are hints, not verdicts |
| Disk IO — await | /proc/diskstats double-sample per physical device (ops-weighted await, top 3) | >50ms = **FAIL**, >10ms = WARN (basis: heuristic; SSD/HDD baselines differ — cross-check) |
| Top processes | ps snapshot, top 3 by CPU and by memory | INFO evidence; WARN only if a process holds >70% of memory (killing is the user's call) |
| macOS memory | vm_stat compressor occupation + Swapins/Swapouts delta (needs sysctl + vm_stat) | compressor >20% of physical pages = WARN; free-low is normal, never a finding (basis: heuristic) |

Deferred (do not improvise): BSD iostat disk gauges for macOS, `--fix` anything. A future minor version owns them.

## Output Contract

Human report: `[LEVEL][basis] title` + evidence lines + `suggest:` command. JSON: `{"schema": "perf-check/1", "platform": {...}, "basis_legend": ..., "findings": [{id, level, title, evidence[], hint, basis}]}`. Levels: PASS / INFO / WARN / FAIL / SKIP. Absent signals degrade to SKIP/INFO with the reason — never fabricated.

## Platform Test Matrix (evidence-pinned, rule-12 style)

| Platform | Status | Evidence |
|---|---|---|
| WSL2 / Linux (this host) | **tested 2026-10-02** | selftest 33/33 (v1.1.0); live run exit=0 with real findings (.wslconfig memory=24GB/processors=12/swap=8GB; autoMemoryReclaim=gradual advice; disk await 0.8ms; process snapshot) |
| macOS 15.8.1 (x86_64, ssh host `mac`) | **tested 2026-10-02** | selftest 33/33; normal run exit=0: macOS memory gauge live (compressor %, swap delta), top-process snapshot live, absent-Linux-gauges SKIP with reasons. v1.0.0 macOS runs exposed three real bugs (order-dependent `import time`, `(None,None)` bypassing cpu_util guard, run_cmd arity) — all fixed with regression fixtures |
| Plain Linux (docker `ubuntu:24.04`) | **tested 2026-10-02** | selftest 33/33; normal run exit=0; `wsl=False` (no host-kernel false positive with /run/WSL confirmation); disk await + process snapshot live; `--json` valid |

Re-run on new hardware, then update this table with date + findings summary. Absence of a row entry means untested.

## Completion Criteria

- Checker ran with exit code reported; every WARN/FAIL relayed to the user **as commands, not executed**.
- No tuning was performed by the agent; nothing outside the working scratch was written.

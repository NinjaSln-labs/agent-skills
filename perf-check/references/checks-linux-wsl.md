# Checks — Linux / WSL2 (thresholds & sources)

The script is the single judge; this page documents what it reads, the pinned thresholds, and the provenance of each number.

## Memory

- Gauge: **MemAvailable** (not MemFree) — free is mostly reclaimable page cache; proc_meminfo(5) man page, Red Hat KB. Threshold: <10% of MemTotal = WARN, <5% = FAIL (heuristic aggregate; large-page systems may read structurally low).
- Swap thrash: double-sample `/proc/vmstat` `pswpin`/`pswpout` (pages; ×4096 → KB), rate over the sampling window. Both directions >200 KB/s = FAIL, >100 = WARN (heuristic). Do **not** use `pgpgin`/`pgpgout` — that includes file cache IO. One-directional paging of idle pages is healthy.
- buff/cache high is **healthy** — it is what free memory is for; never a finding.
- cgroup v2 ceiling: `/sys/fs/cgroup/memory.max` ("max" = unlimited) and `memory.current`; on WSL2/containers the ceiling is the real budget, usually below MemTotal.

## CPU

- Cores: `os.cpu_count()`, overridden by cgroup `/sys/fs/cgroup/cpu.max` quota (`"200000 100000"` = 2.0 cores) — WSL `processors=` lands here.
- Utilization: `/proc/stat` first `cpu` line, two samples, idle = idle+iowait; >85% = WARN (heuristic).
- Load: load1/cores — >1.0 saturated (WARN), >0.7 watch (INFO) — consensus per Brendan Gregg, "Linux Load Averages". **Pitfall**: Linux load includes D-state (uninterruptible IO) tasks; load high + CPU% low ≈ storage bottleneck, cross-check IO before blaming CPU. iowait >10% only triggers investigation and never convicts alone.

## WSL2 tuning

- Official defaults (learn.microsoft.com/windows/wsl/wsl-config): memory = 50% of host RAM (Win11: min(50%, 8GB)), swap = 25% of memory, processors = all logical. Read back via cgroup values; do not assert version specifics from inside.
- `.wslconfig` (Windows side, read-only via /mnt/c/Users/*/): `[wsl2] memory/processors/swap`, `[experimental] autoMemoryReclaim` (default drifted disabled→dropCache across versions; script reports what the file says, no invented defaults).
- autoMemoryReclaim notes: reclaims idle page cache to Windows (vmmem shrink, microsoft/WSL#4166); `gradual` = continuous (user-reported hiccups), `dropCache` = batch; known conflicts with Docker inside WSL (ddev#5356). All advice strings — never applied.
- `wsl --shutdown` applies .wslconfig changes — always a user action from Windows.

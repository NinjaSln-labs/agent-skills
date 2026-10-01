# Checks — macOS

macOS status for perf-check v1.0: **script runs, most gauges SKIP** — Linux thresholds do not transfer, and macOS-specific reading is deferred to 1.1. This page is design documentation, not a test record, until the Platform Test Matrix says otherwise.

## What works portably

- `os.getloadavg()` → load1/5/15 over `os.cpu_count()`; same consensus thresholds (>0.7 watch, >1.0 saturated). macOS load does **not** include D-state tasks the way Linux does — cross-check semantics differ.
- No /proc → CPU utilization sampling and MemAvailable/swap-rate sections SKIP with reasons. Exit code unaffected by SKIP.

## Deferred macOS gauges (do not improvise in 1.0)

- Memory pressure via `vm_stat` (page-size conversion from header line) — but "Pages free low" is **normal** on macOS (cache policy); pressure reading uses compressor occupation + Swapins/Swapouts speed (Apple VM Pages doc).
- Disk latency via `iostat` (BSD); `memory_pressure` CLI is a stress generator, not a gauge — never run it from this skill.
- Total RAM: `sysctl hw.memsize`.

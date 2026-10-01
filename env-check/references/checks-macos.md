# Checks — macOS

macOS is a **supported platform** for env-check (user ruling 2026-10-01), with these deltas from the Linux/WSL page:

## Not applicable

- The entire WSL interop section reports `SKIP` (`wsl.not-wsl`). Exit code is unaffected by SKIP.

## Toolchain

- Same probes as Linux. macOS-specific notes:
  - Homebrew Cask "stubs" in `/usr/local/bin` can shadow real binaries — the shadowing check (realpath-distinct `which -a`) surfaces them.
  - Apple Silicon: a tool present but failing `--version` may be an x86-only binary under Rosetta; the script reports it as WARN ("on PATH but --version failed").

## Env vars

- Same as Linux (PATH hygiene, proxy reachability, LANG). macOS defaults often have no `LANG` in non-interactive shells — the WARN stands, suggest `export LANG=en_US.UTF-8`.

## Platform differences that matter for judgement

- `python3` may be missing entirely on clean macOS (CLT provides it only after Xcode CLT install) — reported as WARN with install hint (`xcode-select --install`), same as any missing tool.
- Proxy settings configured in System Settings are **not** env vars; env-check only sees shell env. If the user says "proxy works in browser but installs fail", check whether the shell env lacks proxy vars entirely (no finding will fire — absence is not probed at baseline scope).

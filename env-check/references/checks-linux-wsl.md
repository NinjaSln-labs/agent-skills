# Checks — Linux / WSL2

Command-level detail behind `scripts/env-check.py` findings. The script is the single judge (levels are pinned in code); this page only documents **what it reads and where**.

## WSL detection

- `WSL_DISTRO_NAME` env var (authoritative when set), else `microsoft` substring in `/proc/version`.

## Toolchain

- `shutil.which <tool>` → resolved path; `<tool> --version` (10 s cap) → version string; `which -a <tool>` → all hits, realpath-normalized, >1 distinct = shadowing WARN.
- Version-manager awareness: nvm-managed node lives under `~/.nvm/versions/node/<v>/bin`; pyenv under `~/.pyenv/shims`. The script reports what resolves — it does not try to reconcile managers.

## Env vars

- PATH split on `:`; per entry: nonexistent dir (WARN), duplicate (WARN), empty string (WARN — means cwd).
- Proxy: `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` (upper or lower). Parsed forms: `http://host:port`, `socks5://host:port`, `host:port`, IPv6 `[::1]:port`. Reachability = TCP connect to host:port (default 5 s). Unparseable/portless = INFO, not probed. **Dead proxy = FAIL** — the only FAIL Baseline scope, since it hard-breaks installs.
- `LANG` unset or `C` → WARN.

## WSL interop (when WSL detected)

- Windows PATH injection: PATH entries starting `/mnt/` → WARN with count and first 5. Root cause is Windows injecting its PATH; fix lives in `/etc/wsl.conf`:
  ```ini
  [interop]
  appendWindowsPath=false
  ```
  Applying it requires `wsl --shutdown` from the Windows side — **user action, always**.
- `/etc/wsl.conf` (INI): WARN on `interop.enabled=false` and `automount.enabled=false`; absent file = PASS (defaults apply). The script (baseline scope) does not read the Windows-side `C:\Users\<user>\.wslconfig` Baseline scope — memory/VM settings belong to performance work (t000003 territory), not runnability.
- `git config --global core.autocrlf` = `true` → WARN (suggest `input`).

---
name: dependency-scan
description: >-
  Dependency scan: detect CVEs and security issues in project
  dependencies, report severity with remediations, and optionally
  auto-fix by updating to patched versions. Also checks dependency
  health: outdated, deprecated, unmaintained, and license issues.
  Use when you need to audit packages for known vulnerabilities, fix
  vulnerable dependencies, or review dependency health across npm,
  pip, cargo, bundler, Go modules, and other ecosystems. NOT for:
  source-code security review, secrets or credential detection, or
  configuration and IaC misconfiguration scanning.
slug: dependency-scan
version: 1.1.1
displayName: dependency-scan
---

# Dependency Scan

Analyze package dependencies for known vulnerabilities.

## Quick Start

```
/dependency-scan                  # Scan all detected package managers
/dependency-scan --npm            # Node.js packages only
/dependency-scan --pip            # Python packages only
/dependency-scan --fix            # Auto-fix where possible
```

## What This Skill Does

1. **Identifies package managers** in your project
2. **Parses dependency manifests** (package.json, requirements.txt, etc.)
3. **Checks vulnerability databases** for known CVEs
4. **Reports severity and remediation** options
5. **Optionally auto-fixes** by updating to patched versions

## Supported Package Managers

| Ecosystem | Files | Tool Used |
|-----------|-------|-----------|
| Node.js | package.json, package-lock.json | npm audit |
| Python | requirements.txt, Pipfile, pyproject.toml | pip-audit, safety |
| Ruby | Gemfile, Gemfile.lock | bundler-audit |
| Go | go.mod, go.sum | govulncheck |
| Rust | Cargo.toml, Cargo.lock | cargo-audit |

## Scan Modes

### Full Scan
```
/dependency-scan
```
Scans all detected package managers, reports all severity levels.

### Specific Ecosystem
```
/dependency-scan --npm
/dependency-scan --pip
/dependency-scan --go
```

### Severity Filter
```
/dependency-scan --severity critical,high
/dependency-scan --severity medium
```

### Auto-Fix Mode
```
/dependency-scan --fix
/dependency-scan --fix --dry-run    # Preview changes
```

Attempts to update vulnerable packages to patched versions.

## Output Format

### Summary View

```
DEPENDENCY SCAN RESULTS
=======================

Scanned: package.json, requirements.txt
Packages analyzed: 127 (78 npm, 49 pip)

VULNERABILITIES BY SEVERITY
  Critical: 2
  High: 4
  Medium: 8
  Low: 12

TOP ISSUES

[!] CRITICAL: lodash < 4.17.21
    CVE-2021-23337: Command Injection
    Affected: lodash@4.17.19
    Fix: npm update lodash

[!] CRITICAL: urllib3 < 2.0.6
    CVE-2023-43804: Cookie Leak
    Affected: urllib3@1.26.0
    Fix: pip install urllib3>=2.0.6

[H] HIGH: express < 4.19.2
    CVE-2024-29041: Open Redirect
    Affected: express@4.18.0
    Fix: npm update express
```

### Detailed View
```
/dependency-scan --details
```

```
DETAILED VULNERABILITY REPORT
=============================

CVE-2021-23337
--------------
Package: lodash
Installed: 4.17.19
Patched: 4.17.21
Severity: CRITICAL (CVSS 9.8)

Description:
  Command Injection in lodash template function allows
  arbitrary command execution via crafted template strings.

Attack Vector: Remote, no auth required
Exploitability: Public exploit available

References:
  - https://nvd.nist.gov/vuln/detail/CVE-2021-23337
  - https://github.com/lodash/lodash/issues/5085

Remediation:
  npm update lodash
  # or
  npm install lodash@4.17.21
```

## Vulnerability Sources

### Databases Consulted

Each scanning tool queries its own ecosystem's advisory source
(see Commands Used below for the tools). Databases with direct
command support:

| Database | Coverage |
|----------|----------|
| npm Security Advisories | Node.js specific |
| PyPI Advisory Database | Python specific |
| RustSec Advisory Database | Rust specific |

### CVSS Scoring

| Score | Severity |
|-------|----------|
| 9.0-10.0 | Critical |
| 7.0-8.9 | High |
| 4.0-6.9 | Medium |
| 0.1-3.9 | Low |

## Commands Used

### Node.js (npm)
```bash
npm audit --json
npm audit fix           # Auto-fix
npm audit fix --force   # Breaking changes OK
```

### Python (pip-audit)
```bash
pip-audit
pip-audit --fix
pip-audit -r requirements.txt
```

### Python (safety)
```bash
safety check
safety check -r requirements.txt
```

### Ruby (bundler-audit)
```bash
bundle-audit check
bundle-audit update     # Update advisory DB
```

### Go (govulncheck)
```bash
govulncheck ./...
```

### Rust (cargo-audit)
```bash
cargo audit
cargo audit fix         # Auto-fix
```

## Auto-Fix Behavior

### Safe Fixes
Updates within semver-compatible range:
- Patch versions (1.2.3 → 1.2.4)
- Minor versions if locked to major (^1.2.3 → ^1.3.0)

### Breaking Fixes
May introduce breaking changes:
- Major version updates
- Requires `--force` flag

### Fix Report
```
AUTO-FIX REPORT
===============

Fixed: 8 vulnerabilities
  lodash: 4.17.19 → 4.17.21
  axios: 0.21.0 → 0.21.1
  minimist: 1.2.5 → 1.2.6

Unable to fix: 2 vulnerabilities
  react-scripts: No patch available (major version required)
  webpack-dev-server: Conflicts with other dependencies

Review package.json changes before committing.
```

## Configuration

### Ignore Known Issues

Create `.dependency-scan-ignore`:

```yaml
# Ignore specific CVEs (document reason!)
ignore:
  - id: CVE-2021-23337
    reason: "Not exploitable in our usage, lodash template not used"
    expires: 2024-12-31

  - id: GHSA-xxx-xxx
    reason: "Development dependency only"

# Ignore packages
packages:
  - name: lodash
    versions: ["< 4.17.0"]  # Only old versions
```

### Severity Thresholds

```yaml
# .dependency-scan.yaml
thresholds:
  fail_on: critical         # Fail CI on critical
  warn_on: high            # Warn on high
  ignore_below: low        # Don't report low

fix:
  auto_fix: true
  allow_major: false       # No major version bumps
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Dependency Scan
  run: |
    /dependency-scan --severity critical,high --fail-on-findings

- name: Auto-fix and PR
  if: failure()
  run: |
    /dependency-scan --fix
    git add .
    gh pr create --title "Security: Update vulnerable dependencies"
```

### Pre-Commit
```bash
#!/bin/sh
# Run on package.json changes
if git diff --cached --name-only | grep -q "package.json\|requirements.txt"; then
  /dependency-scan --severity critical,high
fi
```

## Dependency Health

### Beyond CVEs

```
/dependency-scan --health
```

Additional checks:
- **Outdated packages**: Major versions behind
- **Deprecated packages**: No longer maintained
- **License issues**: Incompatible licenses
- **Maintenance**: Last update, open issues

### Health Report

```
DEPENDENCY HEALTH
=================

Outdated (major behind): 5
  react: 17.0.2 → 18.2.0
  typescript: 4.9.5 → 5.3.3

Deprecated: 1
  request: Use got, axios, or node-fetch

Unmaintained (>2 years): 2
  moment: Consider dayjs or date-fns

License Issues: 0
```

## Minimal worked example

Precondition: a Node.js project with `package.json` + `package-lock.json` at the repo root.

User says: **"scan the dependencies for vulnerabilities"**

What happens:

1. Detect `package.json` → ecosystem = npm; no `--npm`/`--pip` flag given, so only detected managers run.
2. Run `npm audit --json`.
3. Report excerpt (summary view):

```
DEPENDENCY SCAN RESULTS
=======================

Scanned: package.json
Packages analyzed: 78

VULNERABILITIES BY SEVERITY
  Critical: 1
  High: 1

TOP ISSUES

[!] CRITICAL: lodash < 4.17.21
    CVE-2021-23337: Command Injection
    Affected: lodash@4.17.19
    Fix: npm update lodash
```

If `--fix` was requested, follow with the AUTO-FIX REPORT (see below) and show the resulting `package.json`/lockfile diff before the user commits anything.

## Failure exits (offline / wrong repo / missing tool)

Every failure below is observable via a command's exit status or message — act on it, don't silently downgrade the report.

| Situation | Observable signal | Exit action |
|-----------|-------------------|-------------|
| No lockfile for npm | `npm audit` exits non-zero with `EUSAGE` ("Either your app has no lockfile...") | Report that npm audit needs `package-lock.json`; offer `npm install` to generate it, then rerun. Scan other detected ecosystems meanwhile. |
| pip-audit / safety not installed | `pip-audit: command not found` (exit 127) | Install: `pipx install pip-audit` (or `pip install pip-audit`), rerun. Never report the ecosystem as "clean" without running the tool. |
| bundler-audit advisory DB stale | `bundle-audit update` exits non-zero / fetch error | Report "advisory DB could not be refreshed — results may miss recent advisories"; still show results from the local DB. |
| No network at all | every advisory-DB fetch / registry call fails (timeouts, DNS errors) | Stop and report "offline: vulnerability databases unreachable". Do not fabricate a clean result; ask the user to rerun with network or a mirror. |
| Manifest exists but not a real project (wrong repo / stray file) | manifest parses but the manager's tool errors on resolution, or the path is outside the repo root | Ask the user which directory is the project root; never guess across repos. |
| Go/Rust tool missing | `govulncheck: command not found` / `cargo: command not found` | Name the skipped ecosystem explicitly in the report ("go: skipped, govulncheck not installed") and continue with the rest. |

## FAQ (wrong way → right way)

| Wrong | Right |
|-------|-------|
| Trusting a "0 vulnerabilities" result without checking what was scanned | Verify the `Scanned:` line lists the manifests you expected; a missing manifest means that manager was never scanned |
| Using this skill to review source code for injection/XSS | Out of scope (see NOT for) — use `security-scan` |
| Hunting for leaked API keys in the repo | Use `secrets-scan` |
| Committing `--fix` changes without review | Auto-fix only bumps semver-compatible ranges; review the diff, and use `--force` only for confirmed major upgrades |
| Ignoring a CVE forever via `.dependency-scan-ignore` | Every ignore entry needs a reason and an `expires` date; expired entries resurface |
| Treating "no known CVE" as "dependency is healthy" | Run `--health` for outdated/deprecated/unmaintained/license checks too |

## Completion checklist

- [ ] Each detected package manager either ran its audit tool or is explicitly listed as skipped with the reason (not installed / no lockfile / offline)
- [ ] Output shows severity counts per the format above (or the health report when `--health`)
- [ ] Every Critical/High finding carries: CVE id, affected version, patched version, fix command
- [ ] If `--fix` ran: fix report shown and the manifest/lockfile diff presented for review before any commit
- [ ] If ignores were applied: each has a reason and a future `expires` date

## Related Skills

- `/security-scan` - Full security analysis
- `/secrets-scan` - Credential detection
- `/config-scan` - Configuration security

## 中文速览（Quick Guide）

- **做什么**：调用各生态官方审计工具（npm audit、pip-audit、cargo-audit 等）扫描依赖 CVE 与健康度，按 CVSS 分级给出 CVE 编号、修复版本与命令，`--fix` 可自动升级。
- **何时用**：审计依赖已知漏洞、修复带洞依赖，或检查过期/弃维护/许可证风险时。
- **核心步骤**：①识别包管理器与锁文件 ②跑对应审计工具 ③按严重度过滤汇总 ④逐条给 CVE/修复命令 ⑤ `--fix` 后先出示 diff 供审再提交。
- **国内可达性**：漏洞数据来自 npm/PyPI/RustSec 等官方 advisory 源（多在境外），不可达时把该生态列为 skipped 并注明原因；装包可改用 npmmirror 等镜像源；报告中的 nvd.nist.gov / github.com 详情链接需代理才可打开，仅作参考。

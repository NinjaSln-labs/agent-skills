---
name: security-scan
description: >-
  Security scan: one comprehensive pass over a whole codebase — OWASP Top 10
  detection (access control, crypto, injection, SSRF, logging), hardcoded
  secrets, insecure configuration, with severity ranking and remediation
  guidance. Use when you need a full security review before a release or PR,
  want to triage which security problems matter most, or ask to "scan this
  project for security issues". Detection is pattern-based: no SAST data-flow
  engine or CVE advisory database is bundled, so dependency CVEs and taint
  paths need external tooling. NOT for: a single-category deep dive (secrets
  only, config/Docker/IaC only, dependency CVEs only — use the dedicated
  scanner for that one category) or applying fixes without explicit approval.
  USER-INVOKED ONLY: run only when the user asks for a security scan; never
  auto-trigger from any code-writing task.
slug: security-scan
version: 1.2.0
displayName: security-scan
disable-model-invocation: true
---

# Security Scan

## 中文速览（Quick Guide）

- **做什么**：对整个代码库做一次模式化安全扫描（OWASP Top 10、硬编码凭据、注入、弱加密、错误配置），出带严重度与修复建议的报告。
- **何时用**：发布或 PR 前的全量安全评审、需要给安全问题排优先级；仅由用户显式调用，不随日常写码自动触发。
- **核心步骤**：①发现项目类型与文件 ②静态模式匹配＋逐处 source-to-sink 阅读 ③凭据扫描（值必须掩码） ④读 lockfile/manifest 查陈旧版本 ⑤去重、定级、出报告。
- **国内可达性**：完全离线，不需网络；阿里云、微信、字节系等平台密钥格式在 `references/patterns/secret-formats.md` 中缺失属设计内覆盖缺口，需在 `.security-scan.yaml` 自定义 pattern 补齐。

Comprehensive security vulnerability detection for codebases.

**Invocation**: user-invoked only — run when the user explicitly asks for a security scan; never auto-trigger from ordinary coding tasks. Default output is a report; any file change (see `--fix`) requires the user's explicit approval first.

**Detection basis**: this package ships pattern/regex-based detection and code review guidance only — no SAST data-flow engine, no scripted entropy tool, no bundled CVE advisory database. Where a finding would need such tooling, say so in the report and delegate to external tooling only if the user has it and approves.

## Quick Start

```
/security-scan                    # Full scan of current directory
/security-scan --scope src/       # Scan specific directory
/security-scan --quick            # Fast scan (critical issues only)
/security-scan --focus injection  # Focus on specific category
```

## What This Skill Does

Analyzes code for security vulnerabilities across multiple categories:

1. **OWASP Top 10** - Industry-standard web vulnerability categories
2. **Secrets Detection** - Hardcoded credentials, API keys, tokens
3. **Injection Flaws** - SQL, XSS, command injection patterns
4. **Cryptographic Issues** - Weak algorithms, insecure implementations
5. **Configuration Problems** - Insecure defaults, misconfigurations

## Scan Modes

### Full Scan (Default)
Comprehensive analysis of all security categories.

```
/security-scan
```

**Checks performed:**
- All OWASP Top 10 categories
- Secrets and credential detection
- Dependency manifest review — versions read from the project's own lockfile/manifest; known-CVE matching needs external advisory tooling and is not claimed here
- Configuration file review

**Duration:** scales with codebase size (minutes on typical repos)

### Quick Scan
Fast check for critical and high-severity issues only.

```
/security-scan --quick
```

**Checks performed:**
- Critical injection patterns
- Exposed secrets
- Known dangerous functions

**Duration:** a fraction of the full scan; scales with codebase size

### Focused Scan
Target specific vulnerability category.

```
/security-scan --focus <category>
```

**Categories:**
- `injection` - SQL, XSS, command injection
- `secrets` - Credentials, API keys, tokens
- `crypto` - Cryptographic weaknesses
- `auth` - Authentication/authorization issues
- `config` - Configuration security

## Output Format

### Severity Levels

| Level | Icon | Meaning | Action Required |
|-------|------|---------|-----------------|
| CRITICAL | `[!]` | Exploitable vulnerability | Immediate fix |
| HIGH | `[H]` | Serious security risk | Fix before deploy |
| MEDIUM | `[M]` | Potential vulnerability | Plan to address |
| LOW | `[L]` | Minor issue or hardening | Consider fixing |
| INFO | `[i]` | Informational finding | Awareness only |

### Finding Format

```
[SEVERITY] CATEGORY: Brief description
  File: path/to/file.ext:line
  Pattern: Rule name / code shape that matched — never the raw credential value
  Risk: Why this is dangerous
  Fix: How to remediate
```

### Credential Masking (mandatory)

Hard constraint (workspace rule: credentials never in plaintext): a real credential value found during a scan must **never** be echoed verbatim into terminal output, the report file, logs, or follow-up context. For any credential hit:

- Show only: provider/type + `file:line` + a masked form — first 4 characters + `...` + last 4 characters (e.g. `AKIA...9f3c`, `sk_l...x20q`) — or a short SHA-256 hash prefix (first 8 hex).
- Applies to `--details`, `--json`, and any report written to disk; JSON fields carry the masked string plus a `hash_prefix`, never the full value.
- Examples in this skill (e.g. `sk_test_fake123`) are fabricated placeholders; do not replace them with real values in test output.

### Summary Report

```
SECURITY SCAN RESULTS
=====================

Scope: src/
Files scanned: 127
Duration: 45 seconds

FINDINGS BY SEVERITY
  Critical: 2
  High: 5
  Medium: 12
  Low: 8

TOP ISSUES
1. [!] SQL Injection in src/api/users.ts:45
2. [!] Hardcoded AWS key in src/config.ts:12
3. [H] XSS vulnerability in src/components/Comment.tsx:89
...

Run `/security-scan --details` for full report.
```

## OWASP Top 10 Coverage

| # | Category | Detection Approach |
|---|----------|-------------------|
| A01 | Broken Access Control | Authorization pattern analysis |
| A02 | Cryptographic Failures | Weak crypto detection |
| A03 | Injection | Static pattern matching (source-to-sink reading, no taint engine) |
| A04 | Insecure Design | Security control gaps |
| A05 | Security Misconfiguration | Config file analysis |
| A06 | Vulnerable Components | Manifest staleness review (no advisory database) |
| A07 | Auth Failures | Auth pattern review |
| A08 | Data Integrity Failures | Deserialization checks |
| A09 | Logging Failures | Audit log analysis |
| A10 | SSRF | Request pattern detection |

See `references/owasp/` for detailed detection rules per category.

## Detection Patterns

### Injection Detection

**SQL Injection:**
```
- String concatenation in queries
- Unsanitized user input in database calls
- Dynamic query construction
```

**Cross-Site Scripting (XSS):**
```
- innerHTML assignments with user data
- document.write() with dynamic content
- Unescaped template interpolation
```

**Command Injection:**
```
- exec(), system(), popen() with user input
- Shell command string construction
- Unsanitized subprocess arguments
```

See `references/patterns/` for language-specific patterns.

### Secrets Detection

Provider-specific token formats and generic regexes are **externalized** to
`references/patterns/secret-formats.md` — a table carrying `lastUpdated`,
`refreshInterval` (60 days; token formats are medium-stability) and a per-row
confidence column, because provider prefixes drift over time and hardcoding
them here would silently rot coverage.

How to use it:
1. Load `references/patterns/secret-formats.md` and apply its high-confidence patterns first, then medium-confidence ones.
2. If a provider you expect is missing from the table, treat that as a coverage gap and state it in the report — do not invent patterns in-scan.
3. Every hit is reported with masked values only (see Credential Masking).

### Cryptographic Weaknesses

**Weak Algorithms:**
```
- MD5 for password hashing
- SHA1 for security purposes
- DES/3DES encryption
- RC4 stream cipher
```

**Implementation Issues:**
```
- Hardcoded encryption keys
- Weak random number generation
- Missing salt in password hashing
- ECB mode encryption
```

## Integration with Other Skills

### With `/secrets-scan`
Focused deep-dive on credential detection:
```
/secrets-scan              # Dedicated secrets analysis
/secrets-scan --entropy    # High-entropy string detection
```

### With `/dependency-scan`
Package vulnerability analysis:
```
/dependency-scan           # Check all dependencies
/dependency-scan --fix     # Auto-fix where possible
```

### With `/config-scan`
Infrastructure and configuration review:
```
/config-scan               # All config files
/config-scan --docker      # Container security
/config-scan --iac         # Infrastructure as Code
```

## Scan Execution Protocol

### Phase 1: Discovery
```
1. Identify project type (languages, frameworks)
2. Locate relevant files (source, config, dependencies)
3. Determine applicable security rules
```

### Phase 2: Static Analysis
```
1. Pattern matching for known vulnerabilities
2. Source-to-sink reading of suspicious call sites (heuristic; no automated data-flow engine ships with this skill)
3. Configuration review
```

### Phase 3: Secrets Scanning
```
1. High-confidence pattern matching (formats from references/patterns/secret-formats.md)
2. Entropy-style heuristics on candidate strings (visual/regex screening; no scripted entropy tool)
3. Git history check (optional)
```

### Phase 4: Dependency Analysis
```
1. Read the project's own lockfile/manifest (package-lock.json, Cargo.lock, go.sum, poetry.lock, ...) for pinned versions — never assume versions from memory
2. Flag stale pins and direct-manifest drift
3. Known-CVE matching requires external advisory tooling: state the limitation in the report; delegate only if the user has such tooling and approves
```

### Phase 5: Reporting
```
1. Deduplicate findings
2. Assign severity scores
3. Generate actionable report (credential values masked per Credential Masking)
4. Provide remediation guidance
```

## Configuration

### Project-Level Config

Create `.security-scan.yaml` in project root:

```yaml
# Scan configuration
scan:
  exclude:
    - "node_modules/**"
    - "vendor/**"
    - "**/*.test.ts"
    - "**/__mocks__/**"

# Severity thresholds
thresholds:
  fail_on: critical    # critical, high, medium, low
  warn_on: medium

# Category toggles
categories:
  injection: true
  secrets: true
  crypto: true
  auth: true
  config: true
  dependencies: true

# Custom patterns
patterns:
  secrets:
    - name: "Internal API Key"
      pattern: "INTERNAL_[A-Z]{3}_KEY_[a-zA-Z0-9]{32}"
      severity: high
```

### Ignore Patterns

Create `.security-scan-ignore` for false positives:

```
# Ignore specific files
src/test/fixtures/mock-credentials.ts

# Ignore specific lines (use inline comment)
# security-scan-ignore: test fixture
const mockApiKey = "sk_test_fake123";
```

## Command Reference

Flags below are conversational conventions the agent interprets — no bundled CLI parser exists in this package.

| Command | Description |
|---------|-------------|
| `/security-scan` | Full security scan |
| `/security-scan --quick` | Critical issues only |
| `/security-scan --scope <path>` | Scan specific path |
| `/security-scan --focus <cat>` | Single category |
| `/security-scan --details` | Verbose output |
| `/security-scan --json` | JSON output (masked credential fields) |
| `/security-scan --fix` | Propose patches; apply only edits the user explicitly approved (report-first by default) |

## Related Skills

- [`secrets-scan`](../secrets-scan/SKILL.md) - Deep secrets detection
- [`dependency-scan`](../dependency-scan/SKILL.md) - Package vulnerability analysis
- [`config-scan`](../config-scan/SKILL.md) - Configuration security review
- [`code-review`](../code-review/SKILL.md) - General code review (includes security)

## References

- `references/owasp/` - OWASP Top 10 detection details
- `references/patterns/` - Language-specific vulnerability patterns
- `references/patterns/secret-formats.md` - Provider credential formats (refresh-managed table: lastUpdated + 60-day interval + confidence)
- `references/remediation/` - Fix guidance by vulnerability type
- `assets/severity-matrix.md` - Severity scoring criteria

---

## Worked Example (shortest path)

**Precondition:** a code directory with source files; no network, no extra tools needed.

**User says:** "Scan this project for security issues" → full scan (default mode).

**Output excerpt (what the report looks like):**

```
SECURITY SCAN RESULTS
=====================
Scope: ./
Files scanned: 127

FINDINGS BY SEVERITY
  Critical: 1   High: 2   Medium: 4

TOP ISSUES
1. [!] injection: SQL string concatenation in src/api/users.ts:45
   Pattern: query built with `+ userId`
   Fix: parameterized query / prepared statement
2. [!] secrets: AWS access key in src/config.ts:12
   Pattern: AKIA...9f3c (masked; hash_prefix 3a1f0b92)
   Fix: revoke key, move to env/secret manager
```

Every finding carries `file:line`, the matched pattern name (never the raw credential), a risk sentence, and a fix. The summary ends with the count per severity — if your run's output has none of these four fields on a finding, treat the run as incomplete and re-scan.

## Failure Exits (observable — each names the check and the way out)

| Situation | Observable exit |
|-----------|-----------------|
| Target path doesn't exist / isn't readable | Report the exact path and the failure ("`--scope src/` — path not found"), list what *was* found at the repo root, and ask whether to scan a corrected path. Never report "0 findings" for an unreadable path. |
| A reference file is missing (e.g. `references/patterns/secret-formats.md`) | Name the missing file in the report and continue with the rules that ARE present, stating coverage is reduced. Do not invent replacement patterns. |
| Empty or binary-only directory | Say "no scannable source files found under <path>" and stop with that statement — not a clean-scan verdict. |
| Unknown flag (e.g. `--deep`) | Reply: "`--deep` is not a supported flag" + list the valid flags from Command Reference. Never silently ignore an unknown flag. |
| A fix is requested | Default is report-first: propose patches and wait for explicit approval per finding; if the user already approved in the request, still show the diff of each edit as it is applied. |
| Credential-looking hit in a test fixture already listed in `.security-scan-ignore` | Count it in the report as INFO ("ignored by .security-scan-ignore: <line>"), not silently dropped. |

## Boundary Conditions (offline / wrong-repo / non-code)

- **Fully offline-capable.** No step of this skill requires network access — detection is pattern-based over local files. If any proposed step (e.g. fetching an advisory list) would need the network, it is out of this skill's main path and requires the user's tooling + approval.
- **Wrong repo type.** If the directory contains no recognizable application code (docs-only repo, dotfiles, infra-only), say so in the first line of the report and run only the categories that apply (config, secrets). Observable: the report names which categories were skipped and why.
- **Domestic-platform coverage.** Token formats for platforms not in `references/patterns/secret-formats.md` (e.g. Aliyun, WeChat, ByteDance ecosystem keys) are coverage gaps by design: report the gap, match their access-key shapes only if present in the table, and recommend adding a custom pattern to `.security-scan.yaml` (Configuration → patterns) — do not improvise regexes mid-scan.

## FAQ (wrong → fix)

| Wrong move | Observable symptom | Fix |
|------------|--------------------|-----|
| Auto-triggering a scan from ordinary coding tasks | A scan starts after unrelated edits without the user asking | Violation of user-invoked-only; stop, and only scan on explicit request. |
| Echoing a found credential verbatim | Full token appears in report/log/JSON | Masked form + hash_prefix only (Credential Masking). Rewrite the report; the full value must not persist anywhere in output. |
| Using this scan as a dependency CVE check | "CVE" findings with no external advisory tool present | Out of scope by design — state the limitation and route to `/dependency-scan` or external tooling. |
| Treating one regex hit as a confirmed taint path | Finding claims "user input reaches sink" with no source-to-sink reading shown | Downgrade wording to "pattern match — data flow not verified"; note no SAST engine ships with this skill. |
| Scanning `node_modules/` / `vendor/` | Thousands of noise findings, runtime blown | Use the default excludes (`.security-scan.yaml` scan.exclude); re-scan scoped to first-party code. |
| Silencing a true positive with `.security-scan-ignore` | Violation gone from report but the code is unchanged | Ignore entries are for false positives/test fixtures only; real findings get fixed or accepted explicitly, never hidden. |
| Applying `--fix` edits without approval | Files changed after a scan the user only asked to report | Report-first default; every applied edit needs explicit per-finding approval. |

## NOT For (each observable)

- Single-category deep dive → observable exit: the reply names the dedicated scanner (`/secrets-scan`, `/config-scan`, `/dependency-scan`) instead of running a partial full scan.
- Applying fixes without explicit approval → observable exit: patches are proposed as diffs and nothing is written until approval.
- Continuous monitoring / runtime intrusion detection → this is a point-in-time static pass; output is one report per run.
- Proving absence of vulnerabilities → a clean report means "no pattern matches", never "secure".

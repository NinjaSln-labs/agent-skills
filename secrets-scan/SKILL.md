---
name: secrets-scan
description: >-
  Secrets scan: detect hardcoded API keys, passwords, tokens, private keys, and
  connection strings in source code, git history, and config files, with
  high-entropy analysis. Findings are reported redacted (type plus file:line, never
  full credential values). Use when hunting leaked credentials in a repo, checking
  whether a secret committed and later removed is still recoverable from history, or
  wiring a pre-commit / CI secret gate. NOT for: dependency CVEs, config or IaC
  misconfiguration review, or whole-codebase security audits. USER-INVOKED ONLY:
  credentials-class skill; remediation such as rotation or history rewriting requires
  explicit user approval.
slug: secrets-scan
version: 1.1.1
displayName: secrets-scan
disable-model-invocation: true
---

# Secrets Scan

Deep detection of hardcoded credentials and sensitive data in source code.

## Quick Start

```
/secrets-scan                    # Scan current directory
/secrets-scan --scope src/       # Scan specific path
/secrets-scan --entropy          # Include high-entropy detection
/secrets-scan --git-history      # Check git commit history
```

## What This Skill Detects

### High-Confidence Patterns

Patterns with very low false positive rates:

| Type | Pattern Example | Provider |
|------|-----------------|----------|
| AWS Access Key | `AKIA...` (20 chars) | AWS |
| AWS Secret Key | 40 char base64 | AWS |
| GitHub Token | `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` | GitHub |
| GitLab Token | `glpat-...` | GitLab |
| Slack Token | `xoxb-`, `xoxp-`, `xoxa-` | Slack |
| Stripe Key | `sk_live_`, `rk_live_` | Stripe |
| Twilio | `SK...` (34 chars) | Twilio |
| SendGrid | `SG.` followed by base64 | SendGrid |
| Private Key | `-----BEGIN (RSA\|EC\|DSA)?PRIVATE KEY-----` | Various |
| Google API Key | `AIza...` (39 chars) | Google |

### Medium-Confidence Patterns

May require context validation:

| Type | Pattern | Notes |
|------|---------|-------|
| Generic API Key | `api[_-]?key.*=.*['"][a-zA-Z0-9]{16,}` | Variable names |
| Generic Secret | `secret.*=.*['"][^'"]+` | Context needed |
| Password | `password.*=.*['"][^'"]+` | May be config |
| Connection String | `://[^:]+:[^@]+@` | DB credentials |
| Bearer Token | `Bearer [a-zA-Z0-9_-]+` | In headers/code |

### High-Entropy Detection

Finds potential secrets via entropy analysis:

```
/secrets-scan --entropy
```

Detects strings with high randomness that may be:
- Base64-encoded secrets
- Hex-encoded tokens
- Custom API key formats

## Detection Patterns

Full verbatim pattern tables for generic provider families — cloud provider keys (AWS/Azure/GCP), version control tokens (GitHub/GitLab/Bitbucket), payment & finance (Stripe/Square/PayPal), communication services (Slack/Twilio/SendGrid), database connection strings, private keys, and JWT — live in [references/secret-patterns-extra.md](references/secret-patterns-extra.md). The domestic provider table (Aliyun/Tencent/DingTalk/WeChat) stays below.

## Scan Options

### Basic Scan
```
/secrets-scan
```
Scans for high-confidence patterns only.

### With Entropy Analysis
```
/secrets-scan --entropy
```
Adds high-entropy string detection (more findings, some false positives).

### Specific Scope
```
/secrets-scan --scope src/api/
/secrets-scan --scope "*.ts"
```

### Git History Scan
```
/secrets-scan --git-history
/secrets-scan --git-history --since "2024-01-01"
```
Scans commit history for secrets that were committed and later removed.

### Exclude Patterns
```
/secrets-scan --exclude "*.test.ts" --exclude "fixtures/"
```

## Output Format

### Redaction Rule (MANDATORY)

Raw matched credential values must NEVER appear in scan output, terminal logs,
saved report files, or chat/issue summaries — leaked credentials are irreversible.
Every finding MUST be reported in this exact shape:

- **Type + `file:line` + masked value** — identifying where the finding is, never what it is verbatim.
- **Masked value form:** first 4 characters + `****` + last 4 characters (e.g. `AKIA****MPLE`).
- **`(redacted)` instead of 4+4** whenever the value is a password, passphrase, short token,
  or any value where 4+4 characters carry a meaningful share of its entropy.
- **Connection strings:** mask the password segment entirely (`postgres://user:****@host/db`);
  never reveal user plus password together unmasked.

This rule admits no convenience exception: reports pasted into issues, chat, or CI logs stay redacted.
The only permitted verbatim credential-shaped text is a documented public example value
(e.g. the AWS example key) inside the false-positive/ignore reference lists below — never in scan results.

### Finding Report

```
SECRETS SCAN RESULTS
====================

High-Confidence Findings: 2
Medium-Confidence Findings: 5
Entropy Findings: 3

[!] CRITICAL: AWS Access Key
    File: src/config/aws.ts:15
    Pattern: AKIA****MPLE
    Action: Rotate immediately, check CloudTrail

[!] CRITICAL: GitHub Token
    File: .env.example:8
    Pattern: ghp_****f42k
    Action: Revoke token, remove from history

[H] HIGH: Database Password
    File: docker-compose.yml:23
    Pattern: password: (redacted)
    Action: Use environment variable

[M] MEDIUM: Possible API Key
    File: src/services/api.ts:44
    Pattern: apiKey = "a1b2****x7Yz"
    Context: May be test value
```

### Summary Statistics

```
Files scanned: 342
Patterns checked: 127
Time elapsed: 2.3s

By Severity:
  Critical: 2
  High: 5
  Medium: 8

By Type:
  Cloud credentials: 2
  API keys: 4
  Passwords: 3
  Private keys: 1
  Other: 5
```

## False Positive Handling

### Common False Positives

1. **Example/placeholder values**
   - `AKIAIOSFODNN7EXAMPLE` (AWS example)
   - `sk_test_...` (Stripe test key)
   - `your-api-key-here`

2. **Test fixtures**
   - Mock credentials in test files
   - Fixture data

3. **Documentation**
   - README examples
   - API documentation

### Ignore File

Create `.secrets-scan-ignore`:

```
# Ignore test fixtures
**/fixtures/**
**/__mocks__/**
*.test.ts
*.spec.js

# Ignore documentation
docs/**
*.md

# Ignore specific false positives
src/constants.ts:EXAMPLE_KEY

# Inline ignore comment
# secrets-scan-ignore: test fixture
```

### Inline Ignore

```javascript
// secrets-scan-ignore: example value
const EXAMPLE_KEY = "AKIAIOSFODNN7EXAMPLE";
```

## Remediation Steps

**Approval gate (MANDATORY):** this skill is user-invoked only. Scanning and
redacted reporting need no approval, but NO remediation action below may be
executed without the user's explicit approval for that specific action —
in particular credential rotation, git history rewriting (`git filter-branch`,
BFG), and hook/CI installation. Propose the action, state its blast radius, wait
for approval.

### When Secrets Are Found

1. **Immediate Actions**
   - Rotate the credential immediately
   - Check access logs for unauthorized use
   - Remove from code/config

2. **Clean Git History**
   ```bash
   # Remove secret from history
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch path/to/file' \
     --prune-empty --tag-name-filter cat -- --all

   # Or use BFG Repo Cleaner
   bfg --replace-text secrets.txt repo.git
   ```

3. **Prevent Future Commits**
   - Add pre-commit hooks
   - Configure secret scanning in CI

### Prevention

```bash
# Install pre-commit hook
npx husky add .husky/pre-commit "npx secrets-scan --staged"
```

## Integration

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Secrets Scan
  run: |
    /secrets-scan --fail-on-findings
    exit $?

# Exit codes:
# 0 = No findings
# 1 = Findings detected
# 2 = Error during scan
```

### Pre-Commit Hook

```bash
#!/bin/sh
# .husky/pre-commit
files=$(git diff --cached --name-only)
/secrets-scan --files "$files"
```

## Domestic & Additional Providers

Extend coverage to platforms common in China-market codebases (same confidence rules as above):

```regex
# Alibaba Cloud (Aliyun)
LTAI[a-zA-Z0-9]{12,30}                     # AccessKey ID

# Tencent Cloud
AKID[a-zA-Z0-9]{30,50}                     # SecretId (pair with SecretKey)

# DingTalk
ding[a-z0-9]{8,40}                         # AppKey/robot token (context needed)

# WeChat / WeCom (context needed — check assignment shape)
(corpid|corpsecret)\s*[:=]\s*['"][A-Za-z0-9_-]{10,}['"]
```

## Minimal Worked Example

**Invocation:**

```
/secrets-scan --scope src/ --entropy
```

**Output excerpt (note the mandatory redaction — masked values only):**

```
SECRETS SCAN RESULTS
====================

High-Confidence Findings: 1

[!] CRITICAL: AWS Access Key
    File: src/config/aws.ts:15
    Pattern: AKIA****MPLE
    Action: Rotate immediately, check CloudTrail

Files scanned: 87
```

**Exit codes (CI/hook wiring):** `0` = no findings; `1` = findings detected (gate fails — that is the report, not a crash); `2` = error during scan (fix the environment, then re-run).

## Failure Exits

No standalone binary ships with this skill — the scan is executed by the agent per this document, so each failure has a visible outcome in the report, never a silent pass:

- **Scope path does not exist / not a repo:** report `Files scanned: 0` with the reason line `scope not found: <path>` and stop — do not report "no findings", which reads as a clean scan. Ask the user for the correct path.
- **`--git-history` outside a git repository:** report `git history scan skipped: not a git repository` and continue with the working-tree scan; the summary notes history was not covered.
- **Binary or unreadable files:** counted in the summary as skipped files; never decode-and-report their contents.
- **Scan interrupted (timeout, user abort):** mark the report `PARTIAL — scan interrupted at <path>`; do not emit a summary that implies full coverage. Re-running the same command is safe (read-only).
- **Exit `2` in a CI/hook run:** environment error (e.g. git missing). Fix the environment; a non-zero from findings (`1`) is the gate working as intended.

## Wrong Way → Fix (FAQ)

| Wrong way | Observable symptom | Fix |
|-----------|--------------------|-----|
| Pasting a full credential into a report, issue, or chat | Verbatim secret visible in output | Violates the Redaction Rule — report type + `file:line` + masked value only. If already exposed, rotate first, then clean the transcript. |
| Rotating or rewriting git history without asking | Remediation executed unprompted | Approval gate: propose the action, state blast radius, wait for explicit user approval. |
| Scanning dependency CVEs or IaC misconfigurations with this skill | Findings categories outside credentials | Out of scope — route to `/dependency-scan` or `/config-scan`. |
| Trusting `.secrets-scan-ignore` to hide a real leak | Ignored finding never appears in reports | Ignore lists are for known false positives (fixtures, docs). If a real credential sits in an ignored path, the scan cannot see it — audit the ignore file when a leak is suspected. |
| Treating `sk_test_` / example keys as leaks | CRITICAL finding on `AKIAIOSFODNN7EXAMPLE` | Apply the documented false-positive list before escalating; document new false positives in `.secrets-scan-ignore` with a reason comment. |

## Related Skills

- `/security-scan` - Full security analysis
- `/config-scan` - Configuration security
- `/dependency-scan` - Package vulnerabilities

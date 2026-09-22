# Secret / Token Format Table (security-scan reference)

> **Purpose**: single source of truth for provider credential detection formats used in SKILL.md "Secrets Detection" / Phase 3. SKILL.md must not inline these formats (prevents dual-source drift).
> **Stability**: medium-stability data (providers occasionally add or change token prefixes) → `refreshInterval: 60 days`.
> **Confidence legend**: `high` = pattern published by the provider itself or by a widely used OSS scanner; `medium` = community-derived heuristic (expect false positives).
> **Refresh procedure**: re-verify each row against provider token docs (or a current gitleaks/gosecrets ruleset) before bumping `lastUpdated`; when a new prefix appears in the wild, add a row immediately rather than waiting for the cadence; widen or retire rows that produce sustained noise.

- lastUpdated: 2026-09-22
- refreshInterval: 60 days
- nextRefreshDue: 2026-11-21

## High-Confidence Patterns (known provider formats)

| Provider / Type | Pattern (regex) | Confidence | Notes |
|-----------------|-----------------|------------|-------|
| AWS Access Key ID | `AKIA[0-9A-Z]{16}` | high | Long-term access key prefix |
| AWS Secret Access Key | `[A-Za-z0-9/+=]{40}` | medium | Context-dependent: only flag near `aws_secret` / SDK config keys |
| GitHub token (classic / OAuth / server / refresh) | `gh[pousr]_[A-Za-z0-9]{36,}` | high | Covers `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` |
| GitHub fine-grained PAT | `github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}` | high | NOT matched by the `gh[pousr]_` row above — added 2026-09-22 after a confirmed silent miss; loose fallback: `github_pat_[A-Za-z0-9_]{20,}` |
| Stripe live secret key | `sk_live_[A-Za-z0-9]{24,}` | high | Also check `rk_live_` restricted keys |
| Private key material | `-----BEGIN (RSA \|EC \|OPENSSH \|PGP )?PRIVATE KEY-----` | high | PEM header |

## Medium-Confidence Patterns (generic heuristics)

| Type | Pattern (regex) | Confidence | Notes |
|------|-----------------|------------|-------|
| Generic API key | `api[_-]?key.*[=:]\s*['"][a-zA-Z0-9]{16,}` | medium | Requires assignment context; expect false positives in fixtures |
| Password in code | `password\s*[=:]\s*['"][^'"]+['"]` | medium | Skip test/mock files via ignore patterns before reporting |
| DB connection string | `(mysql\|postgres\|mongodb)://[^:]+:[^@]+@` | high | Embedded credentials; report location only |

## Usage Rules

1. Apply high-confidence rows first, then medium-confidence rows.
2. Every hit is reported **masked** per SKILL.md "Credential Masking (mandatory)": type + `file:line` + first4...last4 or hash prefix. Never echo the raw value.
3. A provider the project clearly uses but with no row here = coverage gap; state it in the report. Do not invent provider regexes during a scan — fix the table instead (and update `lastUpdated`).
4. The patterns above describe public, provider-documented formats; they are not secrets. Example values anywhere in this skill must stay fabricated placeholders.

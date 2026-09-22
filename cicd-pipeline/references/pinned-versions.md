# Pinned Version / Key Reference Table (cicd-pipeline reference)

> **Purpose**: single source of truth for the volatile version and key
> identifiers referenced by the pipeline templates in SKILL.md. SKILL.md keeps
> placeholders and pointers here instead of inlined values (prevents
> dual-source drift and copy-paste breakage when a value rotates).
> **Authority rule**: for anything the project itself pins
> (`@playwright/test` version, action majors already used in the repo,
> service image tags), the project's own lockfile / package.json / CI config
> wins over every value in this table. Example values here serve only as
> starting points for greenfield templates.
> **Stability tiers** → per-row `refreshInterval`: fast (30 days) /
> medium (60 days) / slow (90–180 days), per skill-description-audit §5.
> **Confidence legend**: `high` = rule or value published by the issuer
> itself; `medium` = last-verified snapshot that can rot — re-check before
> relying on it; never treat a `medium` example as the current release.
> **Refresh procedure**: before bumping `lastUpdated`, re-verify each row
> against the issuer's current official install docs / package registry /
> release pages (Playwright: Docker image repo + npm; k6: its APT install
> instructions; actions: each action's releases page). When a template fails
> for a user because a value moved, fix the row here first — do not re-inline
> values into SKILL.md.

- lastUpdated: 2026-09-22
- nextRefreshDue: 2026-10-22 (driven by the fastest row: Playwright tag, 30 days)

## Table

| Item | Value / Rule | Stability | refreshInterval | Confidence | Notes |
|------|--------------|-----------|-----------------|------------|-------|
| Playwright Docker image tag | **Rule**: `mcr.microsoft.com/playwright:v<version>-jammy` where `<version>` equals the project's `@playwright/test` version **exactly**. Example shape only: `v1.42.0-jammy` (snapshot from the pre-externalization template, not a recommended version) | fast | 30 days | rule: high; example value: medium | Monthly image releases; a tag that does not match the npm package fails at runtime. Always derive from package.json — never copy the example. |
| k6 apt archive GPG key ID | **Rule**: use the key ID shown in k6's current official APT install instructions (repo URL: `https://dl.k6.io/deb`). Last-verified value: `C5AD17C747E3415A3642D57D77C6C491D6AC1D68` | slow | 90 days | medium | Key IDs rotate; a stale ID fails `gpg --recv-keys`. Re-check the issuer's install docs before pinning. |
| `actions/checkout`, `actions/setup-node`, `actions/upload-artifact`, `actions/download-artifact` | Major-channel examples: `@v4` | slow | 180 days | medium | Later majors may exist — check each action's release page, or reuse the majors already used in the target repo. |
| `snyk/actions/node` | Channel example: `@master` | medium | 60 days | medium | For deterministic builds prefer a released tag from the Snyk actions repo over a branch reference. |
| `8398a7/action-slack` | Major-channel example: `@v3` | slow | 180 days | medium | Community action; confirm the current release on its repo before use. |
| Service image tags: `postgres:16`, `redis:7`, `node:20` | Major-tag examples matching the SKILL.md templates | slow | 180 days | medium | Tags do not "expire" but majors age; choose the majors matching the project's actual runtime / database versions. |

## Usage Rules

1. When instantiating a `<placeholder>` in a SKILL.md template, apply the row's
   **Rule** first; use the example value only if the project has no existing pin.
2. Example values are snapshots labeled with `lastUpdated` — state the date and
   confidence when surfacing one, and prefer checking the issuer's current
   release over trusting the snapshot.
3. A broken template caused by a rotated value = this table is stale: re-verify
   the row against the issuer, update the value, bump `lastUpdated` and
   `nextRefreshDue`. Do not "fix" it by hardcoding a new literal into SKILL.md.

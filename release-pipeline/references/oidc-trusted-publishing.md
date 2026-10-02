# OIDC / Trusted Publishing (PyPI, npm)

Downstream detail for `SKILL.md` §"OIDC and trusted publishing". This file backs guard **G4**
(credential form) and part of **G5** (provenance). It defines *what to record*, not *what to
type*: the registry side of this setup is configured by the platform, and the platform's
current documentation is authoritative.

## 1. Two routes, one observable difference

| | Short-lived token route | OIDC / trusted publishing route |
|---|---|---|
| Credential material in the repo or job | A stored secret (file on the runner, or an env var injected by the CI secret store) | No stored secret; the job presents an **identity assertion** and the registry exchanges it, in-ephemeral, for a publish credential scoped to that one job |
| Lifetime | Long-lived until rotated; survives job end | Bound to a single job run |
| If leaked | Valid until someone rotates it, for whatever scope it carries | Bound to one job and one identity; per-platform replay windows exist and change |
| Where the trust decision lives | Your secret store | The registry's trusted-publisher configuration, **keyed to a specific repository + workflow (+ environment where the platform supports it)** |
| G4 verdict | Not a failure if OIDC is genuinely unavailable; becomes MANUAL-OK (§4). **FAIL** only when OIDC was available and a long-lived token was used instead | PASS |

## 2. Least privilege is part of the configuration, not an afterthought

A trusted-publisher entry is not a global on/off switch. It names, at minimum, *which* repository
and *which* workflow may mint the credential — and, where the platform offers it, which environment.
Consequences you must state when recording G4:

- An entry that matches a whole org's default branch is broader than one that names a single
  workflow file and a protected environment.
- A fork pull request must never be able to satisfy the entry; if the platform lets you restrict to a
  protected branch/environment, note that it is configured rather than assumed.
- The binding is a **cross-repository secret**: the registry must trust the CI provider, and the
  workflow must live in the repository the registry was told about. Moving or renaming the workflow
  file can silently break the match.

Exact field names, the option set, and whether environment scoping exists for a given platform:
**verify against that registry's current trusted-publishing documentation before configuring.**
No endpoint path, field name, or permission string is reproduced here on purpose — a stale copied
field name is worse than a blank, because it looks authoritative.

## 3. How to tell which route actually ran

Judge from artifacts of the run, not from the workflow file's intent. Evidence shapes:

| Evidence | Reading |
|---|---|
| Job log shows the platform's OIDC identity step succeeded, and the publish step used the credential it minted | OIDC route |
| Job log shows a masked secret being expanded for the publish step | Long-lived token route — record the **variable or file path**, never the value |
| Registry-side record of the published version shows provenance/attestation metadata naming the CI provider and workflow | OIDC route, corroborated after the fact (feeds G5) |
| Release/platform audit log records a token-authenticated publish event without a matching identity exchange | Long-lived token route; escalate the scope question to the scope owner |

If the log is not retained or the audit log is not readable, the route is **unproven**, not
"probably OIDC". Record it as a confirmation-list item.

## 4. "The organization only offers long-lived tokens"

This is a legitimate state, not a failure. It becomes **MANUAL-OK**, and the record must carry all
five rows below. Blank cells are not acceptable.

| Field | Content |
|---|---|
| Credential location | Path on the runner, or the CI variable name. **Never the value.** |
| Scope it carries | What the credential can do (which org, which packages/projects, which actions) as far as it can be determined without printing it |
| Who owns the scope | Named person or team accountable for rotation and revocation |
| Mitigations | Rotation interval; least-privilege scoping actually applied; whether publish actions are audit-logged; whether the credential is restricted to a protected environment |
| Expiry / review | When this MANUAL-OK is re-examined — a permanent exception is not a record, it is a hole |

The G4 exit in `SKILL.md` is the authority on behaviour: this state proceeds, it does not abort.
Aborting is reserved for "OIDC was available and a long-lived token was used anyway".

## 5. Attribution when this file and a platform disagree

- Cite the document you actually used, by name and the date you read it, in the confirmation record.
- If a fact cannot be verified offline (field names, whether a given platform supports environment
  scoping, verification command shape), write "**confirm against <registry>'s current documentation**"
  and state what the unknown affects — e.g. "unknown whether environment scoping is available here;
  it determines how narrow the trusted-publisher entry can be, hence the G4 least-privilege claim."
- The skill's guard semantics outrank any remembered platform detail. A platform fact never
  downgrades a FAIL to a SKIP.

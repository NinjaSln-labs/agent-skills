# Guardrail checklist (G1–G7) — printable

Printable expansion of the table in `SKILL.md`. The state definitions there are authoritative; this
file only restates them in working form. **No default-continue path exists**: every line ends in
PASS, FAIL, SKIP, MANUAL, or an explicit N/A with a reason.

Command *shapes* are described rather than written out, because the exact invocation changes with
registry, CI provider, and platform. A pasted command is a stale source; the output shape is the
judgement criterion.

## Applicability matrix

| # | Guard | PASS | FAIL | SKIP | MANUAL |
|---|---|---|---|---|---|
| G1 | Single version source | ✔ | ✔ | ✔ | N/A — the check compares three values; a value that cannot be read is SKIP, not a judgement call about scope |
| G2 | Clean worktree | ✔ | ✔ | N/A — a local command always produces output; "no output available" is not a state this guard can reach | N/A — same reason |
| G3 | Artifact ↔ tag | ✔ | ✔ | ✔ | N/A — no scope or ownership judgement here; an unreadable digest is SKIP |
| G4 | Credential form | ✔ | ✔ | N/A — the detection action always yields a result; the only non-PASS/FAIL outcomes are the org's token-only reality and the scope judgement | ✔ |
| G5 | Provenance / attestation | ✔ | **N/A — no FAIL state**; attestation verification is post-hoc, there is no artifact to block at check time | ✔ | N/A — the check has no scope judgement to defer; unproducible attestation is SKIP plus an impact statement |
| G6 | Immutability | ✔ | ✔ | ✔ | N/A — the guard reports digest equality; confirmation of an unjudgeable case is the SKIP entry's signer, not a separate state |
| G7 | Tag ↔ release assets | ✔ | ✔ | N/A for a registry-only target; for a release-publishing target, an unreadable asset list is a SKIP | N/A — set comparison only |

## The seven checks

**G1 — Single version source.** *Intent: the manifest, the git tag, and the registry all say the same
version.* Output shape: three version strings, printed side by side, from (a) the project's one
version source, (b) a tag-description read of the local repo, (c) the version's record at the
registry. PASS: all three equal. FAIL: unequal — print the three actual values and **abort**; never
let the check pick a winner or edit any of them. SKIP: the registry record is unreadable (private
package, not authenticated) → confirmation list, published only after a named person signs.

**G2 — Clean worktree.** *Intent: what ships equals what is committed.* Output shape: an empty
string, or a list of entries each tagged as modified / staged / untracked — untracked files included,
they are the ones that get forgotten. PASS: empty. FAIL: any entry → list all of them and abort.
SKIP and MANUAL are N/A (see matrix).

**G3 — Artifact ↔ tag.** *Intent: the bytes published came from the commit the tag points at.*
Output shape: two identifiers — the digest computed over the built artifact, and the commit the tag
resolves to. PASS: equal. FAIL: unequal → report against the digest, do **not** rebuild and re-push
(you cannot know which side is wrong). SKIP: the target exposes no digest → record that a manual
check is required. Next actor: the release owner.

**G4 — Credential form.** *Intent: publishing used a per-job identity, not a stored long-lived
secret.* Output shape: a verdict derived from the job's identity-exchange step and from the presence
of credential files or secret variables in the job environment — see
[`oidc-trusted-publishing.md`](oidc-trusted-publishing.md) for the evidence table. PASS: OIDC route.
FAIL: OIDC was available and a long-lived token was used anyway → abort, naming the **path or
variable name only**. MANUAL: the org genuinely offers no OIDC path → MANUAL-OK record with all five rows from
[`oidc-trusted-publishing.md`](oidc-trusted-publishing.md): credential location, scope carried,
scope owner, mitigations (rotation / least scope / audit log), and expiry or review date. Never print a value, in
any branch.

**G5 — Provenance / attestation.** *Intent: consumers can verify where the artifact came from.*
Output shape: whether an attestation was produced, and the result of the registry's **currently
documented** verification path. PASS: produced and verified — record it. There is no FAIL: this runs
after the artifact exists, so there is nothing to block. SKIP: not produced or not verifiable → state
the impact (consumers cannot verify origin) and add it to the confirmation list. Next actor: the
release owner decides whether it ships that way; this skill does not decide it.

**G6 — Immutability.** *Intent: a published version never changes meaning.* Output shape: the
digest of the existing artifact for this version at the target. PASS: version absent (first
release), or bytes identical. FAIL: bytes differ → abort and present the retraction options defined
in `version-management`; do not overwrite. SKIP: target unreachable → require human confirmation.
Next actor: the scope owner of that registry, since a differing upload is a security question before
it is a release question.

**G7 — Tag ↔ release assets.** *Intent: what the release page shows is what was built.* Output
shape: two sets — the asset list on the release object, and the artifacts produced by this run.
PASS: sets equal. FAIL: unequal → list missing and extra, abort. N/A: a registry-only target has no
release object, so there is nothing to compare. SKIP: the target does publish a release but its asset
list cannot be read. Applicability comes from the step's target in the plan table, not from a judgement
made mid-run. Next actor: the release owner.

## Closing the run

- Collect every SKIP and MANUAL into the confirmation list: guard, why it could not be
  machine-judged, who signs. Publishing continues only once a person has signed each entry.
- Only G1's two local readings and G2 can be pre-checked — five of the seven guards cannot. A clean
  dry-run says nothing about G3, G4, G5, G6, G7 — say that rather than reporting "dry-run passed".
- Output the **unjudged rate** (steps ending in SKIP or MANUAL, over total plan steps); two consecutive
  releases above one half is a guardrail-failure signal and gets a re-review registered
  (the closing-out obligation is stated in `SKILL.md` § "Closing out a release"; the counting
  detail is in [`multi-repo-release.md`](multi-repo-release.md) §6).

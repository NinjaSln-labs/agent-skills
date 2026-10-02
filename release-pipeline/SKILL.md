---
name: release-pipeline
description: >-
  Release guardrails and multi-target release orchestration for packages and
  repos: OIDC / trusted publishing setup for PyPI and npm, provenance and
  attestation verification, single-version-source consistency, immutability
  checks, idempotent multi-registry release plans, and recovery from
  half-finished releases. Use when you are about to publish a version, wire a
  release workflow, or resume a release that failed partway across several
  registries. NOT for: choosing a version number (SemVer/CalVer choices and
  yank/deprecate semantics), branch and PR sequencing, configuring CI test
  stages, or writing a press release. USER-INVOKED ONLY.
disable-model-invocation: true
slug: release-pipeline
version: 1.0.1
displayName: release-pipeline
---

# Release Pipeline

Guardrails and orchestration for the moment you publish. Version numbers are decided elsewhere
(`version-management`); command sequencing lives in `git-workflow`; CI test wiring is
`cicd-pipeline`. This skill owns one question: **is this release correct, and if it fails halfway,
how do we finish it without breaking anything?**

## 中文速览（Quick Guide）

- **做什么**：发布前的七条守卫（G1–G7）＋ 多 registry 发布的计划清单、幂等键与半发布态续发；不负责选版本号。
- **何时用**：准备发版、配 OIDC/trusted publishing、校验 provenance，或多仓发布失败后要接着发。
- **核心步骤**：①列发布目标并给每步生成 `target:name@version` 幂等键 ②逐条跑 G1–G7，把 FAIL 中止、SKIP 与 MANUAL 记入待确认项 ③由人逐条签字 SKIP/MANUAL ④按清单顺序执行，已达成则跳过而非重做 ⑤收尾输出 unjudged rate（SKIP＋MANUAL 步数占比）。
- **国内可达性**：本技能为本地判据编排，不依赖境外在线服务；但 OIDC、provenance 验证与 registry 查询均需访问对应平台，按目标 registry 当前文档核对可达性与替代路径。

## Hard Rules

1. **One source of truth for the version.** Change it in exactly one place; everything else is derived.
   If the three readings disagree, stop — never let the skill "fix" one of them.
2. **Never print a credential value.** Name the file path or environment variable; print nothing else.
3. **SKIP is not PASS.** If a check cannot produce an output, it goes on the confirmation list and a
   human signs it off. There is no "continue anyway by default" path in this skill.
4. **Idempotency key is `target:name@version`.** `target` is one of `npm`, `pypi`, `github-release`,
   `container`, … Two registries can host the same name and version; the bare `name@version` key
   collides and must not be used.
5. **A version already published is immutable.** Re-shipping different bytes under the same version is
   a defect, not a retry. Retraction semantics belong to `version-management`.
6. **No defaults.** Every branch ends in an action or a named person, never in "proceed".

## The Seven Guardrails

Each guard names how to inspect it, what passing looks like, and what happens otherwise. A guard
may declare a state **N/A** — but only with a reason; an empty cell is not acceptable.
Whether a guard applies to a given step is decided **by that step's target in the release plan table**, never
improvised mid-run; a step whose applicability was decided wrongly is corrected in the plan, not on the fly.

| # | Guard | How to inspect | PASS | FAIL | SKIP | MANUAL |
|---|---|---|---|---|---|---|
| G1 | Single version source | Read the one version source, `git describe --tags`, and the registry record | All three strings are equal | Unequal: print all three actual values, abort; do not auto-edit any of them | Registry unreadable (private package, not logged in) → confirmation list | N/A — the check is a comparison; a human never has to judge the values |
| G2 | Clean worktree | `git status --porcelain` | Empty output | Non-empty: list unstaged and untracked files, abort | N/A — a local command always produces output | N/A — same |
| G3 | Artifact ↔ tag | Artifact digest vs the commit the tag points at | Equal | Unequal: report against the digest, do not rebuild | Registry exposes no digest → SKIP, state that manual check is required | N/A — digests are read and compared, never judged |
| G4 | Credential form | Look for long-lived credential files / env vars | Publishing via OIDC | OIDC was available but a long-lived token was used → abort, name path/var, never the value | N/A — the detection step always yields a result | Scope and ownership judgement; organization-only long-lived tokens → **MANUAL-OK, not a skip and not a failure**: record all five of credential location, scope carried, who owns the scope, mitigations (rotation, least scope, audit log), and expiry/review date — see [`references/oidc-trusted-publishing.md`](references/oidc-trusted-publishing.md) |
| G5 | Provenance / attestation | Was an attestation produced, and does the registry's current documented verification accept it? | Produced and verified → record it | **No FAIL state** — verification is post-hoc | Not produced or not verifiable → SKIP, state the impact (consumers cannot verify origin) and add to the confirmation list | N/A — the verdict is the registry's own verifier, not a human call |
| G6 | Immutability | Compare the digest of the existing artifact for this version | Version does not exist yet (first release), or bytes match the last one | Bytes differ: abort, offer the retraction options defined in `version-management` | Registry unreachable → SKIP, require human confirmation | N/A — a digest comparison has no judgement call in it |
| G7 | Tag ↔ release assets | Release asset list vs the actual artifacts | Sets are equal | Unequal: list missing and extra assets, abort | N/A for a registry-only target (no release object exists to check). For a target that does publish a release, an asset list that cannot be read is a SKIP, not an N/A | N/A — the check compares two sets; a human never judges the assets |

### What can be dry-run

Only **G1's two local readings** and **G2** can be checked before publishing. G3, G5, G6 and G7 are
post-hoc — they are verified *after* the publish lands, not before it. G4 depends on the real
credential environment. A clean dry-run therefore says nothing about five of the seven guards; say so
explicitly rather than reporting "dry-run passed".

### The confirmation list

Everything that lands as SKIP or MANUAL is collected into one list before publishing, each entry
naming: the guard, why it could not be machine-judged, and who signs it. **Publishing continues only
after a person has signed every entry.** This skill does not decide that for you.

A printable per-guard checklist — which states apply to each guard, what each one should produce, and
who to hand an unjudgeable one to — is in
[`references/guardrail-checklist.md`](references/guardrail-checklist.md).

## Multi-target orchestration

Full procedure with worked sequencing: [`references/multi-repo-release.md`](references/multi-repo-release.md).

The shape of a release across several registries:

1. **Write the plan before the first publish.** One row per step, with its idempotency key
   (`target:name@version`), the guard that gates it, and its order.
2. **Publish in dependency order** — library before consumer, platform before channel-specific asset.
3. **Skip by key, never by memory.** A step whose key already exists is skipped only when it exists
   *and* G6 passes for it *and* G7 either passes or does not apply to that target. A registry-only step
   has no release object, so G7 is inapplicable there rather than failed. Existence alone is not a
   reason to skip; neither is a reason to redo.
4. **On failure, resume from the plan.** Re-read the plan, re-run the guards for the remaining steps,
   and continue. Do not restart the sequence from the top — earlier steps already changed the world.
5. **Half-finished releases are a state, not an error to clean up.** Say which targets are published,
   which are not, and what remains safe to do.

## OIDC and trusted publishing

Setup details, the minimum-permission shape, and how to tell an OIDC flow from a token flow:
[`references/oidc-trusted-publishing.md`](references/oidc-trusted-publishing.md).

Registry-side configuration changes over time; treat the platform's current documentation as
authoritative and state which document you relied on when a check disagrees with this skill.

### Closing out a release

Count, **per release plan**, how many steps ended unjudgeable — that is, SKIP or MANUAL — and report:

```
unjudged rate = (steps ending in SKIP + steps ending in MANUAL) / total steps in the plan
```

Counting is per **step**, not per guard: a step is the thing the plan enumerates, and a step can
gauge several guards. MANUAL counts here as well as SKIP — a step a human had to judge is equally
unjudged by machine. **If the rate exceeds one half on two consecutive releases, treat that as a
signal the guards have stopped doing their job** — say so explicitly and register a re-review of the
affected guards. A guard suite that is mostly unjudged is not a passing guard suite.

## Failure exits

| Situation | What this skill does |
|---|---|
| Guards disagree on the version | Prints all three readings and aborts; it never picks a winner |
| Long-lived token found where OIDC is available | Aborts, names the path or variable, prints no value |
| Organization has no OIDC path | Proceeds as MANUAL-OK with the credential, its scope owner, and mitigations recorded |
| Attestation missing | Records SKIP and the consumer-facing impact; adds it to the confirmation list |
| Existing version's bytes differ | Aborts and points at the retraction semantics in `version-management` |
| Worktree is not clean | Aborts and lists unstaged and untracked files; an untracked file counts as unclean |
| Artifact does not match the tagged commit | Reports against the digest and does not rebuild — rebuilding would replace bytes already referenced by the tag |
| Release assets and artifacts disagree | Aborts, listing the missing and the extra assets |
| A later step failed after earlier ones succeeded | Stops, reports published vs pending targets from the plan, does not roll back silently |

## Not for

- **Choosing or bumping a version number** — `version-management` (SemVer vs CalVer, epoch,
  retraction semantics, single-version-source mechanics).
- **Branch, PR and `gh release` command sequencing** — `git-workflow` (its Critical Release Rules
  and pre-release ordering already cover the git-side timing).
- **CI test stages, sharding, service containers** — `cicd-pipeline`.
- **Writing a press release** — `press-release`. Same English word, completely different job: that one
  is marketing copy for humans, this one is guardrails for machines.

## Wrong → Fix

| Mistake | Why it breaks | Fix |
|---|---|---|
| Bumping the version in the manifest and the README separately | Two sources drift; G1 then fails at publish time | Change one source; regenerate the rest |
| Treating a dry-run pass as approval | Five of the seven guards cannot run before the publish lands | Dry-run covers G1(local)/G2 only; say so |
| Re-running the whole sequence after a mid-way failure | Already-published targets get hit again | Resume from the plan by idempotency key |
| Skipping a step because "the version is already there" | Existence is not correctness | Skip only when the key exists, G6 passes, and G7 passes or does not apply to that target |
| Pasting a long-lived token into a log to "show which one" | Leaks the secret | Name the file or variable; never the value |
| Expecting attestation checks to block a publish | They run after the artifact exists | G5 is record-and-confirm, not a gate |

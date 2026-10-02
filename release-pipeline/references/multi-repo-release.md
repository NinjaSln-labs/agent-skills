# Multi-registry release orchestration

Procedure behind `SKILL.md` §"Multi-target orchestration". One release, several registries: the
plan, the idempotency key, ordering, skip rules, and what to do when step 4 of 6 fails.

## 1. Write the plan before the first publish

One row per publish step. The plan is the single source of truth for the whole release; nothing is
remembered from the previous attempt.

| # | target | name | version | idempotency key | gated by | order |
|---|---|---|---|---|---|---|
| 1 | pypi | `<pkg>` | `<v>` | `pypi:<pkg>@<v>` | G1, G2, G4, G5, G6 | 1 |
| 2 | npm | `<pkg>` | `<v>` | `npm:<pkg>@<v>` | G1, G2, G4, G5, G6 | 2 |
| 3 | github-release | `<repo>` | `<v>` | `github-release:<repo>@<v>` | G3, G5, G6, G7 | 3 |
| 4 | container | `<image>` | `<v>` | `container:<image>@<v>` | G3, G5, G6, G7 | 4 |

`target` is drawn from the set of registries/channels this release actually uses — `npm`, `pypi`,
`github-release`, `container`, and so on. Add a column for "owner" if a step is run by a different
person or team; a failed step needs a named next actor, not an orphan row.

## 2. The idempotency key is `target:name@version`

**Why the `target:` prefix is mandatory.** Registry namespaces are independent. A project can
legitimately publish `core@2.4.0` to both PyPI and npm, or ship a container image and an npm package
at the same tag. Keyed on `name@version` alone, the second publish sees the first one's key, reports
"already exists", and skips a step that has never run. The same collision in the other direction
turns a genuine retry into a silent no-op. The prefix makes the key unique per destination, which
is the only scope where "already exists" actually means "this step already succeeded".

Hard rule 4 in `SKILL.md` applies verbatim: the bare `name@version` key collides and must not be used.

## 3. Ordering

- **Dependencies before consumers** — the library before the app or plugin that requires it; a
  consumer released first pins a version that does not resolve yet.
- **Platform artifacts before channel-specific assets** — the image before the manifest or bundle
  that references it, so the channel artifact never points at a missing digest.
- **When the dependency relation cannot be stated**, publish the step with the largest cost of
  failure first. A retracted core package is expensive and needs consent; a re-uploadable asset is
  not. Getting an expensive-but-reversible thing out first, while the cheap steps can still absorb
  its consequences, is the safer order.

Order is a property of the plan, not of the moment: if you reorder, you rewrite the plan, you do
not improvise mid-run.

## 4. Skip condition — do not weaken this

Skipping applies from the **second publish onwards in a run**: before this run's first publish, every
planned step is still pending, so the conditions below cannot be satisfied yet and nothing is skipped.

A step is skipped **only when all of these hold**:

1. its idempotency key already exists at that target, **and**
2. G6 (immutability) passes for that step, **and**
3. G7 passes **or is genuinely inapplicable to that target**.

Point 3 matters: G7 checks a release object's asset list, so for a registry-only step (PyPI, npm) it is
inapplicable rather than failed. Requiring a release-level check on a step that has no release object
would push every ordinary cross-platform publish onto the confirmation list and inflate the unjudged rate
until the re-review signal fires on healthy releases (rule: `SKILL.md` § "Closing out a release"). Applicability is decided by the step's target
in the plan table above — not improvised mid-run.

| Situation | Action |
|---|---|
| Key exists, G6 passes, G7 passes or is inapplicable to this target | SKIP — record the key and the fact that the guards confirmed it |
| Key exists, G6 cannot be judged, or G7 applies to this target but its asset list cannot be read | Not a skip. Not a redo either. It is a confirmation-list item: name the guard, why it is unjudgeable, and who signs. (G7 being *inapplicable* to this target is a different case — see the row above) |
| Key exists, G6 or an applicable G7 **fails** | Abort that step and report against the digest. Bytes differing under a published version is a defect; the retraction options are defined in `version-management`, not here |
| Key does not exist | Run the step |

Two errors this rule exists to prevent, both observed: skipping on "the version is already there"
alone, and treating the same fact as licence to re-push. **SKIP is not PASS** — a skipped step
carries the guards' evidence into the release record, and the skip is counted in the unjudged rate (§6).

## 5. Resuming a half-finished release

A partial release is a state to finish, not an error to clean up. Never restart the sequence from
the top: earlier steps already changed the world, and re-running them is what breaks things.

1. Re-read the plan. If the plan is gone, reconstruct it from the registry records before touching
   anything.
2. Re-run the guards for the **remaining** steps only, in the real credential environment — a
   resumed run inherits no verdict from the previous attempt.
3. Continue from the first unfinished row. Do not revisit completed rows; do not roll back.
4. Finish with a three-state list:

| Target | State | Evidence |
|---|---|---|
| `<target>` | Published | Key exists, G6/G7 pass |
| `<target>` | Not published | Key absent at the target |
| `<target>` | Awaiting human confirmation | Key present but a guard is unjudgeable, or MANUAL-OK recorded under G4 |

Every row lands in exactly one state. "Probably published" is not a state — resolve it against the
target or move it to awaiting confirmation with a named signer.

## 6. Unjudged rate — the guardrail-erosion signal

Cross-platform releases can produce a high unjudged rate, at which point the guards are decoration.
Every release therefore ends with:

```
unjudged rate = (steps ending in SKIP + steps ending in MANUAL) / total steps in the plan
```

- Report the rate alongside the three-state list, per step, with the guard that was skipped.
- **Two consecutive releases with an unjudged rate above one half is a guardrail-failure signal**, not a
  statistic to note. Log a re-review of the guard that is being skipped, naming: which guard, how
  often, and whether the cause is a missing output, an unavailable platform feature, or a check
  nobody wrote.
- The typical causes are a guard with no real output source, or a platform that exposes no digest
  for G3/G6. Both are fixable by giving the guard a real output, not by continuing to accept SKIPs.

The re-review is registered, not silently absorbed into the next release.

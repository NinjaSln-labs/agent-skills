# Provider integration (downstream of `SKILL.md`)

How to wire a second and third provider without discovering the differences the hard way. This file
elaborates the capability matrix and the credential/timeout surfaces in `SKILL.md`; it does not
restate the hard rules and does not add any.

**Nothing here carries a provider value.** Every model name, endpoint, price, context length, and
default timeout is `verify` per Hard Rule 1. Where a value is needed, this file tells you *which
document to read* and *which decision that value changes* — never what the value currently is.

## 1. "openai-compatible" is a protocol family, not a contract

Compatibility means "one request/response shape is broadly accepted". It does not mean "identical
behaviour on every axis". Treat the following as a **known-drift checklist**: each row is a class of
difference that exists, how you find out, and what you do.

| Drift axis | How to discover it | How to handle it |
|---|---|---|
| Streaming chunk framing | Compare a raw streamed transcript from each provider against the canonical one: does the terminal event differ, is there a keep-alive, is a chunk ever empty, is the whole stream one line-delimited stream or an SSE-style one | Consume per provider with a thin adapter that normalises into one internal stream type; keep the raw transcript behind a debug flag for diagnosis |
| Tool-call structure | Compare how a call is expressed: one call per event or many, arguments as a string that must be parsed or as structured data, an identifier needed to match a call to its result | Normalise at the adapter boundary into one internal tool-call shape; assert the adapter's own output shape in a test, never the provider's |
| JSON mode strictness | Ask for a structured answer with an ambiguous schema and see whether the answer is parsed, repaired, or handed back raw; check whether the mode refuses a schema at all | Wrap every "I asked for JSON" response in a parse step that fails loudly on failure; treat unparseable-but-200 as response-shape drift (see `failure-handling.md`), not as success |
| Error body shape | Trigger a rejection deliberately in a non-production environment and look at *where* the information sits: status code, a message string, a structured detail block, a machine-readable code, headers | Build the classifier on the *provider's own* observable, verified per provider; do not parse errors with one global heuristic across providers |
| System-prompt field | Find the canonical, provider-specific, and "none" positions for instructions, and check precedence when more than one is used | Send instructions through one internal field and let the adapter place them; document the precedence you assumed |
| Usage / token reporting | Compare the usage block of a normal call and a streamed call; check whether caching or reasoning portions are reported separately | Meter from the usage block if present, else from your own tokeniser estimate, and **label which of the two you used** — an unlabeled mix makes cost attribution untrustworthy |
| Optional-parameter tolerance | Send a request with an optional parameter the model may not support and observe whether it is ignored, rejected, or silently changes behaviour | Send only parameters the matrix cell for that model is verified to support; treat "ignored" as a failure of that cell's assumption, not as compatibility |
| Empty and near-empty prompts | Send a minimal request; compare treatment of empty input, whitespace, and a single token | Fix a policy at the call site rather than relying on the provider's floor |

Rule: a compatibility difference that has not been observed in your own traffic is not yet a fact.
Add a row when you observe it, with the provider and the date.

## 2. Capability matrix: how to fill a cell

| Cell | Fill with | Read from | `Verified against` should say |
|---|---|---|---|
| Provider / Model | The identifier *as your code addresses it* — a config key, not a literal in the matrix | The provider's current model listing / catalogue | Catalogue page + date |
| Tool calls | `yes` / `no` / `partial (<what is missing>)` / `verify` | The provider's structured-output or function-calling page | Page title + date |
| JSON mode | `schema-constrained` / `parse-only` / `no` / `verify` | Same page, plus the mode's own constraints | Page title + date |
| Streaming | `yes` / `no` / `partial (<what differs>)` / `verify` | Streaming/reference page | Page title + date |
| Context | The **limit you may rely on for this model**, with a link to the limit's own table | The provider's context/pricing table | Table + date |
| Latency tier | Your own measured class (`p50`/`p95` bucket), not the provider's marketing class | Your gateway's own measurements | Measurement window + date |
| Price tier | A bucket relative to your other rows **or** a rate with its unit and date | The provider's current pricing table | Table + date |

Filling rules:

- **Every cell is either a value or `verify`.** "Probably yes" is a defect (`SKILL.md`, matrix rules).
- **`Verified against` names a document, not "the docs".** If you cannot name it, the cell is `verify`.
- **A cell is only about that provider's current documentation.** If the answer came from another
  provider's comparable page, it is `verify` — cross-provider resemblance is exactly the assumption
  that breaks silently.
- **Mark a whole row `unverified` when**: the model was retired or renamed; the page you verified
  against no longer exists or no longer names the model; you have no traffic and no reachable
  documentation; the row was copied from another row. An `unverified` row is a legitimate state; a
  stale row presented as verified is not.
- **Latency and price are your numbers**, not the provider's. Only the source document is theirs.
- Re-verification is triggered by any of: a model change, a price-page change, an observed drift
  incident, a matrix row being used to justify a routing change.

## 3. Credential surface

| Concern | Rule |
|---|---|
| Storage | Keys live in the project's secret store, referenced by name. Never in the matrix, prose, examples, test fixtures, or captured transcripts |
| Scoping | One credential per environment and per scope of use, so a rejected key localises to one caller instead of taking down every path. Scope down to what the call site needs where the provider allows it |
| Rotation | Rotation is exercised at least once; an unrotated key that has been in a transcript is compromised, not merely untidy |
| Reference form | In prose and code, write the *reference*: an environment-variable name or a secret path. Placeholder form: a clearly non-functional token of the shape `<env-var-name>` or `<secret-path:…>` |
| Never acceptable | A key-shaped string, however redacted, when its length or prefix is preserved; a captured request body in a log or fixture; a "temporary" key committed for convenience |
| Diagnostics | When a call is rejected for auth, **name** the credential (`AUTH_SOURCE=<env-var-name>`) and the scope that failed. Print no value, no length, no prefix (Hard Rule 5) |
| Test environments | Test credentials are separate values with reduced scope, never a copy of the production key |

Any sample that *looks* like a real key is a leak even when it is fake, because it trains readers to
paste real ones. Placeholders must be visibly placeholders.

## 4. Where timeouts and budgets are set

| Setting | Owner | Notes |
|---|---|---|
| Per-call timeout | The call site. It is part of that call's contract with its caller | A default timeout copied from a provider's docs is a value in disguise; the value depends on the task, not on the provider |
| Token / output budget per call | The call site | Same rule; a provider's documented maximum is an upper bound, not a budget |
| Per-caller limit | The layer that knows the caller | Cannot be set at the call site — the call site does not know who is calling |
| Spend ceiling | Whatever enforces the budget | The remaining budget at decision time must be observable *before* the call, not reconciled afterwards |
| Transport-level connect/read timeouts | The gateway | Must never be longer than the call site's timeout, or the call site can never enforce its own contract |
| Provider default | Nothing to copy | Verify against the provider's current documentation if you must know it; the value decides nothing in your code — your call site's value decides everything |

Conflict resolution, in order:

1. The **call site's** timeout wins. It is the only layer that knows the caller's latency budget.
2. A gateway-level transport timeout may only be *shorter*; a longer one silently disarms rule 1.
3. When a fallback tier has a different latency profile, the chain's trigger for "too slow" is a
   property of the call site, not of either provider.
4. When a per-caller limit and a per-call timeout both apply, both can fire; each is reported under
   its own class rather than being collapsed into "throttled".

## 5. Adding a provider: the minimum order

1. Verify the matrix row exists, or create it with `verify` cells; do not route before it is filled.
2. Add the adapter; keep it thin — normalise, do not add policy.
3. Probe each drift axis in §1 once in a non-production environment and record what you observed.
4. Add the tier to the chain with a trigger, marked as a candidate if it is not the default
   (`SKILL.md`, fallback rules).
5. Label the call site so usage can be attributed before the first real call, not after the first
   bill.
6. Only then route production traffic — and record the switch, per Hard Rule 3.

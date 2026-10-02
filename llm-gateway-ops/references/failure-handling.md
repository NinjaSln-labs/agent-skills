# Failure handling (downstream of `SKILL.md`)

One page per class of the closed set in `SKILL.md`, plus the three questions that cut across all of
them: is a retry legal, what does a fallback leave behind, and how is a bad response caught.

**Recognition here is positional, not nominal.** Provider field names, status codes, and headers
differ per provider and change on the provider's schedule. So each class below says *which part of
the response to read*, and you map that part to the concrete key by reading the provider's current
documentation. A classifier written against a remembered field name is a defect.

## 1. The seven classes, one by one

| Class | How to recognise it (read this part of the response) | Do | Do **not** do |
|---|---|---|---|
| Rate limited / quota exhausted | The status/transport part indicates throttling, or the response carries a retry-delay hint (header or error body) — the hint may be absent, so absence is not a negative signal | Classify, surface the limit to the caller, and let the owner of the budget decide between waiting, degrading, or failing. Honour the delay hint when present | Do not retry immediately; do not treat a missing delay hint as "retry now"; do not silently switch tiers to escape a limit that applies to the whole account |
| Auth / credential rejected | The response indicates the credential was refused or its scope insufficient; the body usually carries a machine-readable reason and sometimes a hint about the missing scope | Report **which** credential reference and which scope failed, by name only; repair the key/scope out of band | Never retry the same credential (Hard Rule 2 in the closed set: a retry cannot succeed); never print, length, or prefix the value; never retry another credential to "see if that one works" |
| Bad request / parameter rejected | The provider rejected the *request* — the error points at a parameter, a schema, or a value the model cannot accept, not at capacity or the credential | Fix the request; pin the offending request shape in a test; revisit the matrix cell you assumed when choosing parameters | Do not retry unchanged; do not retry with the same body and a shorter timeout; do not strip parameters to make it pass and keep the resulting behaviour silently changed |
| Content filtered | The provider blocked the content, as opposed to rejecting the request shape — the reason says the content (or its policy classification), not the parameters | Report the filter and stop; surface to the caller/human | Do not reword, split, translate, or otherwise smuggle the content past the filter; do not retry through a lower-safety tier without an explicit human ask; do not treat it as a transient failure |
| Server error / unavailable | The provider-side failed: the failure is not attributable to the request shape, the credential, or the content | Retry **only** if this call site is idempotent (Hard Rule 2); otherwise surface | Do not retry a non-idempotent call; do not count it as a client error and start "fixing the request"; do not hide it by falling back without a record |
| Timeout | No response within the call site's timeout — note this is a local observation, the provider may well have completed the work | If idempotent: retry within budget. If not: surface the **partial state** and say the outcome is unknown | Do not assume nothing happened; do not retry a non-idempotent call "because the timeout means it failed"; do not shorten the timeout and treat that as a fix |
| Response-shape drift | The response **arrived and parsed** but a field the caller relies on is missing, differently shaped, or empty where the caller assumes a value | Treat as a hard failure even though the request succeeded; fail the call, name the field/position, do not invent a default | Do not coerce, default, or "be liberal in what you accept" your way through; do not retry hoping for a better draw unless the field's absence is genuinely stochastic *and* you have evidence; do not log a raw body to "see what came back" without checking for user content and credentials in it |

Not in the closed set, and deliberately unrouted here: "the answer was wrong" and "the model is
not good enough" (`SKILL.md`, failure taxonomy).

## 2. Retry and idempotency

Decide the idempotency question **first**; "retry with backoff" is not a policy until it is answered
for *this* call site (Hard Rule 2).

| Call site | Retry legal? | Condition |
|---|---|---|
| Read-only lookup, no write downstream | Yes | Classify, then retry within the call's time/token budget with a backoff |
| Generation whose result is written somewhere | Only with an idempotency key | The key must be generated at the call site, be stable across retries of the same logical call, and be what the write side de-duplicates on |
| Generation whose result is written and where the write side cannot de-duplicate | No | Surface instead of retrying |
| Anything that consumes quota, sends a message, charges a card, or mutates a user-visible state | No, unless idempotent by construction | Treat "we can undo it later" as not idempotent |
| Any auth, bad-request, or content-filter failure | **Never** | Reclassified, not retried; the repeat cannot succeed and the third is noise |

Retry budget belongs to the call site and is counted against the same budget as the original call —
a retry storm is a cost event, not just a latency one. A retry that exhausts the budget and *then*
falls back has spent two providers' worth of quota for one caller request; that is reportable.

## 3. Fallback triggers and the record left behind

Every switch is non-silent (Hard Rule 3). A trigger is a condition, not a mood: "primary unavailable
or over budget" is two triggers with different consequences, and each gets its own chain entry.

| Element of a trigger | Must specify | Otherwise |
|---|---|---|
| Condition | The observable that fired (class from §1 + which budget/limit) | "When primary fails" is not a trigger |
| Direction | Which tiers are eligible next | The chain silently widens |
| Guard | What must *not* trigger a fallback (auth, bad request, content filter) | A request bug becomes a quality downgrade |
| Bound | The whole chain's time and token ceiling | One caller request consumes an unbounded number of tiers |
| Outcome when exhausted | Fail, with the list of tiers tried and why each was skipped | An empty success, which is the worst possible return value |

The record every switched call leaves behind, so the incident can be attributed afterwards:

| Field | Why it is there |
|---|---|
| Which tier actually served, and which was intended | Answers "was this even the path we thought" |
| The class that caused the switch, per skipped tier | Distinguishes an outage from a bad request from a limit |
| Which call-site label and which budget applied | Ties the cost of a degraded answer to the feature that caused it |
| Whether the served tier met the caller's quality requirement | Separates "cheaper, still fine" from "degraded, user-visible" |
| Whether the switch was automatic or a human decision | A silent automatic degradation is the one that hides |

Attribution is only possible if the call-site label is attached at the call site. Attaching it later,
from a dashboard, cannot reconstruct which caller caused which spend.

## 4. Catching response-shape drift at integration time

This class is different from the other six: it is **a request that succeeded and a downstream that
gets corrupted**. Nothing raises, no status code is wrong, no log line says "error" — and the
corruption surfaces far from the call that caused it, as a null, a wrong count, a silently empty
list, or a field that suddenly became a string.

| Prevention point | What to do |
|---|---|
| Adapter boundary | The adapter's output shape is the contract; assert it in a test per provider, against a captured-but-sanitised response |
| Parse step | Any "I asked for JSON/text" response goes through a parse that **fails loudly**; a parse that returns a best guess is a drift generator |
| Required-field check | The call site declares the fields it relies on; a missing or empty one is a hard failure at the call site, not a `None` further down |
| Type narrowing | Never let a field's type be decided by the payload: a value that may be a scalar or a list is a union you must handle, at the boundary |
| Optional-capability paths | A model whose matrix cell says "partial" gets its own path in the code, not a hope that the field arrives |
| Drift canary | Cheap, low-stakes, shape-asserting calls on a schedule; a shape change surfaces as a canary failure rather than as a user-visible corruption |
| Captured fixtures | Keep a sanitised fixture per provider per shape class, and re-run the adapter against it on adapter changes; never keep raw production bodies containing user content |
| Before filling a matrix cell | Say plainly that drift is the cost of routing to a model whose capability was assumed rather than verified |

## 5. What the seven classes must never collapse into

| Anti-pattern | Why it hides | Instead |
|---|---|---|
| One `catch` → retry → fallback | Every class becomes "transient"; request bugs get retried, limits get escaped silently | Name the class first (Hard Rule 4), then consult §2 for the retry verdict |
| Logging the raw response body on failure | Leaks user content and sometimes credentials; violates Hard Rule 5 in spirit and often in letter | Log the class, the position read, and the call-site label; body only behind an explicit, reviewed, sanitised debug path |
| "Provider is down" as a conclusion | Rate limits, auth, and timeouts all look like an outage from the outside and need different actions | Record the class; an outage is one of seven |
| Disabling retries to make an anomaly disappear | Hides a cost or shape problem and loses the signal | Report the call site and the shape of the anomaly (`SKILL.md`, failure exits) |

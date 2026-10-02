---
name: llm-gateway-ops
description: >-
  Operate the standing configuration of an application's model calls:
  multi-provider access over openai-compatible endpoints, capability matrices,
  routing and fallback chains, quota and rate-limit budgets, inference cost
  attribution, and the seven provider-specific failure classes (rate limits, auth,
  bad request, content filtering, server error, timeout, response-shape drift). Use when wiring a second
  provider, choosing a fallback chain, capping spend or throughput, or naming
  which model tier served a request. NOT for: triaging one reported model call
  that failed — root-cause tracing, severity grading, shipping a fix, closing
  it out; prompt design or model evaluation; fine-tuning and training; domain
  modelling; general observability beyond LLM-specific amounts.
  Platform model names, endpoints, prices, and timeouts change often — verify
  against the provider's current documentation. No skill name implied: the
  boundary is the task.
slug: llm-gateway-ops
version: 0.3.3
displayName: llm-gateway-ops
---

# LLM Gateway Operations

Everything about *calling models from an application and keeping those calls predictable*: which
provider, which model, what happens when it fails, what it costs, and who is allowed to spend how
much. This is not a book about models.

> **v0.1.0 is a skeleton on purpose.** The two tables below — the capability matrix and the failure
> taxonomy — are left as **shapes with placeholders**, not filled-in values. Model names, endpoints,
> prices, context limits, and default timeouts change on the provider's schedule; a table filled in
> today is a stale authority source within weeks. Fill a cell only from that provider's current
> documentation, and record which document you used. Until then the cell stays `verify` and this
> skill tells you to go read — rather than handing you a plausible-looking value.

## 中文速览（Quick Guide）

- **做什么**：把应用接到多个模型 provider 上，管路由与降级链、配额限流、推理成本归因，并给每种 provider 特有失败一个可观察出口。
- **何时用**：要接第二个 provider、选主备降级链、控某条调用线的预算/吞吐，或判断某次请求实际由哪一档模型服务。
- **核心步骤**：①查能力矩阵确认目标模型是否支持你要的能力（tool call／JSON mode／流式／上下文）②定降级链并把切换留痕写进代码 ③设配额与超时，重试前先判幂等 ④按调用点归集 token 成本 ⑤失败时按分类走出口，不静默重试。
- **国内可达性**：本技能为本地判据与流程，不依赖境外在线服务；但 provider 端点本身在国内的可达性、速率与价格各不相同，选型时须按目标 provider 当前文档核对，必要时在降级链里把不可达的一档显式列为候选而非默认。

## Hard Rules

1. **Never hardcode a provider value into prose.** Model names, endpoints, prices, context limits, and
   default timeouts are `verify` until read off that provider's current documentation. A remembered
   value is a guess, and a plausible guess is the failure mode this skill exists to prevent.
2. **Judge idempotency before retries.** A read-only lookup may be retried; a call whose result is
   written somewhere must carry an idempotency key or it must not be retried. "Retry with backoff" is
   not a policy until that question is answered for *this* call site.
3. **Fallback is never silent.** Every switch records which tier actually served the request and why
   the higher tier did not. A silent fallback makes production incidents untraceable.
4. **A failure is named before it is handled.** Rate limit, auth, bad request, content filter, server
   error, timeout, and response-shape drift are seven different problems. "Handle exception" is not
   an exit.
5. **Never log a credential.** Name the environment variable or secret path; print no value.
6. **Cost attribution stops at inference.** Training and fine-tuning are out of scope for this skill.

## The Two Tables

Depth for both tables lives in the references: how to fill the matrix and where the
openai-compatible edges actually drift is in
[`references/provider-integration.md`](references/provider-integration.md); the per-class exits,
the idempotency-to-retry table, and how to keep a fallback switch attributable afterwards are in
[`references/failure-handling.md`](references/failure-handling.md).

### Capability matrix (shape — values unverified)

One row per model you actually intend to call. Fill `verify` from current docs; leave it at `verify`
until you have.

| Provider | Model (the identifier your code addresses) | Tool calls | JSON mode | Streaming | Context | Latency tier | Price tier | Verified against |
|---|---|---|---|---|---|---|---|---|
| _verify_ | _verify_ | _verify_ | _verify_ | _verify_ | _verify_ | _verify_ | _verify_ | _which document + date_ |

Rules for this table:

- **Every cell must be filled or explicitly `verify`** — "probably yes" is a defect.
- `Verified against` names the document, not just "the docs". Prices and context limits move.
- Two models that look interchangeable in the table are not interchangeable in production; the
  difference shows up in the failure taxonomy, not in the happy path.

### Failure taxonomy (closed set)

Each row's exit must name **what to read** and **what to do** — and, for at least one row, what
*not* to do.

| Class | How to recognize it | Exit |
|---|---|---|
| Rate limited / quota exhausted | Provider signals throttling; a retry-delay hint is present or absent (its name varies by provider — read the response, not this row) | Do not retry immediately. Surface the limit to the caller; decide with the human owning the budget whether to wait, degrade, or fail. |
| Auth / credential rejected | Provider rejects the key or its scope | Do not retry — a retry with the same key cannot succeed. Report which credential is missing or under-scoped (name only). |
| Bad request / parameter rejected | Provider rejects the request shape | Do not retry unchanged. This is a code bug in the request, not an outage. |
| Content filtered | Provider blocks the content | Do not retry with a reworded prompt unless a human asked for a fallback; report the filter, do not smuggle the content past it. |
| Server error / unavailable | Provider-side failure | Retry only if the call site is idempotent (Hard Rule 2). |
| Timeout | No response within the call's timeout | Retry only if idempotent; otherwise surface partial state rather than assuming nothing happened. |
| Response-shape drift | Response parses but a field the caller relies on is missing or differently shaped | This is the failure that silently corrupts downstream code. Treat as a hard failure even when the request "succeeded". |

**Not in the closed set**: "model quality is bad" and "the answer was wrong". Those are evaluation
concerns, not gateway concerns — this skill does not route them.

## Fallback chains

A chain is an ordered list of tiers with a reason for each. The shape:

| Tier | Role | Chosen when | Cost | Recorded on every call |
|---|---|---|---|---|
| primary | default | — | _verify_ | yes |
| secondary | degraded quality, still usable | primary unavailable or over budget | _verify_ | yes |
| last resort | correctness over quality, or cached answer | both above unavailable | _verify_ | yes |

Rules:

- Every tier needs a **trigger**, not just an order. "Primary times out" and "primary exceeds the
  caller's latency budget" are different triggers with different consequences.
- Tiers that are simply unreachable from your network belong in the chain **as candidates**, marked
  as such — not as defaults that quietly fail.
- If a caller's quality requirement is met by no tier, the chain does not get a last-resort entry
  that produces a worse answer silently; the call fails and says why.

## Quota, rate limits, and cost attribution

| Concern | Where it is decided | What must be observable |
|---|---|---|
| Per-call rate ceiling | the call site, as a timeout plus a token budget | which budget applied to a given call |
| Per-caller limit | the layer that knows the caller | when a limit was hit, and by whom |
| Spend ceiling | whatever enforces the budget | the remaining budget at decision time, not afterwards |
| Cost attribution | the point where usage is metered | usage split by call site; a total alone cannot answer "which feature got expensive" |

**Attribution needs a call-site label.** If usage is metered without one, the numbers cannot be split
later — plan the label at the call site, not at the dashboard.

## Failure exits

This table is **not an eighth failure class** — every row is a situation *made of* the seven above.
If a new row cannot be traced back to one of them, it probably belongs in the taxonomy instead.


| Situation | What to do |
|---|---|
| Provider unreachable from your network | Record the tier as a candidate in the chain; do not make it the default. |
| The chain is exhausted | Fail with the list of tiers already tried and why each was skipped. Never return an empty success. |
| Quota exhausted mid-run | Surface it; do not let one caller consume another's budget silently. |
| Usage looks anomalous (retry storm, context growth) | Report the call site and the shape of the anomaly; do not silently disable retries to make it go away. |
| The capability matrix is stale for a model in use | Treat the affected call as unverified and say so; do not fill the gap from memory. |

## Not for

- **Prompt design and model evaluation** — iterating on what you ask or scoring what comes back.
- **Fine-tuning and training** — explicitly out of scope; this skill ends at inference.
- **Application domain modelling** — `ddd-*` and `architecture-patterns`.
- **General observability infrastructure** — metrics, logs, and tracing belong to the project; this
  skill only owns the LLM-specific amounts (tokens, per-caller limits, fallback tier actually used).

### Boundary with `problem-handling` (settled 2026-10-02 by scenario test, not by guess)

An eight-scenario collision test (audits/2026-10-02-llm-gateway-ops-boundary-test.md) found that
**5 of 8** realistic LLM scenarios match *both* skills' trigger language: `problem-handling`
triggers on 「报错/失败/异常/行为偏差」, and this skill owns the provider-shaped exits. Overlapping
trigger words are unavoidable — the line is therefore **not** "whose trigger fires first".

**The line is: standing state vs. an event.**

| | `problem-handling` | This skill |
|---|---|---|
| Nature of the work | a **reported event** that needs diagnosing, grading, fixing, and closing out | **standing state** of the model-call layer: which provider, which tier served it, what it costs, what the budget allows |
| Entry question | "something broke — what is the root cause?" | "how should this layer behave, and is it behaving that way?" |
| Output | a fix, plus a blameless close with captured known errors | a configured behaviour: routing, budgets, failure exits |
| Time | one incident, start to close | continuous, revised whenever providers change |

**Reading the collision.** A single 401 or one timeout burst is an *event* → `problem-handling`,
which may call this skill's failure taxonomy for the provider-shaped part. "This provider silently
served the cheap tier for a week", "the bill doubled and nobody knows which feature", "we need a
second provider" are *standing state* → this skill, with no incident to diagnose.

Neither skill's `NOT for` names the other: they are not exclusive, and pretending otherwise would
break both. What is exclusive is the question being asked.

## Wrong → Fix

| Mistake | Why it breaks | Fix |
|---|---|---|
| Retrying every failure with backoff | Non-idempotent calls duplicate side effects; auth and bad-request retries never succeed | Judge idempotency first, then classify, then retry only what is retryable |
| Falling back silently | Production looks fine while quality quietly drops | Record the tier that served and the reason for every switch |
| One model for everything | Cheap tasks pay premium prices; hard tasks fail on a model that cannot do tool calls | Route by task, then verify the capability matrix cell before routing to it |
| Metering usage without a call-site label | Cost cannot be split later, so the bill cannot be attributed | Label at the call site, where the caller is still known |
| Filling the matrix from memory | Prices, context limits, and model availability move on the provider's schedule | `verify` until read from the current documentation; name the document and date |
| Logging the provider key to "see which one" | Leaks the credential | Name the variable or secret path; print no value |

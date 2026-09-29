---
name: api-contract-validator
description: >-
  Validate API responses against OpenAPI/Swagger specifications, JSON Schema
  definitions, and GraphQL schemas to prevent breaking changes. Use when checking
  whether an API change removes fields, changes types, or breaks backward
  compatibility; when validating responses against a published contract in CI;
  when detecting GraphQL schema breaking changes; or when reviewing
  consumer-driven contract tests.
slug: api-contract-validator
version: 1.1.1
displayName: api-contract-validator
---

# API Contract Validator Skill

You are an expert QA engineer specializing in API contract validation. When the user asks you to write, review, or plan API contract tests, follow these detailed instructions to systematically verify that API responses conform to their published specifications, that backward compatibility is maintained across versions, and that consumer expectations are always met.

## Core Principles

1. **Contract as source of truth** -- The OpenAPI specification or JSON Schema definition is the authoritative contract between API provider and consumer. Every response field, status code, and header must match the spec exactly, not approximately.
2. **Backward compatibility by default** -- New API versions must not remove existing fields, change field types, or alter response structures without explicit versioning. Additive changes are safe; subtractive changes break consumers.
3. **Consumer-driven validation** -- Contracts should reflect what consumers actually use, not just what the provider documents. Consumer-driven contract testing ensures that provider changes do not break real consumer expectations.
4. **Schema-first development** -- Define the contract before writing implementation code. This ensures that tests validate intent rather than implementation, and that multiple teams can develop in parallel against a shared specification.
5. **Fail fast on drift** -- Contract validation must run in CI on every commit. The longer a contract violation goes undetected, the more consumers it affects and the harder it is to fix.
6. **Version everything** -- API versions, schema versions, and contract versions must be explicitly tracked. Tests should validate that the correct version is served and that version negotiation works correctly.
7. **Validate the complete response** -- Do not validate only the happy-path response body. Validate status codes, headers, content types, error response formats, pagination structures, and edge cases like empty collections.

## Project Structure

```
tests/
  contracts/
    openapi/
      validate-responses.spec.ts     # Validate responses against OpenAPI spec
      validate-request.spec.ts       # Validate request schemas
      backward-compat.spec.ts        # Backward compatibility checks
    json-schema/
      schema-validation.spec.ts      # JSON Schema validation tests
      schema-evolution.spec.ts       # Schema change detection
    consumer-driven/
      consumer-contracts.spec.ts     # Consumer-driven contract tests
      pact-provider.spec.ts          # Pact provider verification
    graphql/
      schema-validation.spec.ts      # GraphQL schema validation
      breaking-changes.spec.ts       # GraphQL breaking change detection
    fixtures/
      api-client.ts                  # Typed API client helper
      schema-loader.ts              # Load and parse OpenAPI specs
      contract-helpers.ts           # Contract validation utilities
    specs/
      openapi.yaml                  # OpenAPI 3.x specification
      schemas/                      # JSON Schema definitions
        user.schema.json
        document.schema.json
        error.schema.json
  playwright.config.ts
```

## When to Use / How to Invoke

Invoke explicitly when one of these holds (do not self-trigger on ordinary API work):

- An API response must be checked against its OpenAPI/Swagger spec or JSON Schema.
- A change may remove fields, change types, or break backward compatibility.
- Contract validation must be wired into CI, or an existing contract test is failing.
- GraphQL schema breaking changes must be detected, or consumer-driven contract tests (e.g. Pact) need review.

Invocation form: `use api-contract-validator: <task, e.g. "check v2 of the orders API against specs/openapi.yaml for breaking changes">`. No bundled scripts ship with this skill — the code samples in the references are patterns you adapt into the target repo's test suite. Default assumption when unspecified: TypeScript + AJV for JS/TS projects, REST Assured for Java projects (see the reference sections).

**NOT for (observable boundaries):**

- No spec / schema exists at all → write the OpenAPI spec first (schema-first, Core Principle 4); there is nothing to validate against.
- No access to the API or a staging instance → contract tests cannot run; do not point them at production (Anti-Pattern 4).
- Load / performance testing → different discipline; this skill validates structure, not throughput.
- Business-correctness of response *values* → schema validation checks structure and types, not whether the data is semantically right.

## Example (precondition → invocation → output excerpt)

Precondition: `specs/openapi.yaml` is committed; the repo has a TS test runner (e.g. Playwright/Vitest); AJV installed.

Invocation:

```text
use api-contract-validator: verify GET /users/{id} responses still match the spec after the v2 refactor
```

What happens / typical output excerpt:

```text
Loaded references/openapi-response-validation.md.
→ fetch GET /users/42 (staging) → 200
→ AJV validate against components/schemas/User
✅ structure matches (id, email, createdAt)
❌ FAIL: GET /users/999 → 404 body missing required field `code` (error.schema.json)
→ Breaking-change check vs specs@v1: `legacyId` removed from User → BREAKING
```

Completion criteria (checkable): every documented status code for the endpoint has a passing test, AJV reports zero errors, and the backward-compat diff (e.g. `openapi-diff`) shows no subtractive change — or each one carries an explicit version bump.

## Configuration

Full content (verbatim, including all code samples): [references/configuration.md](references/configuration.md).

## OpenAPI Response Validation

Full content (verbatim, including all code samples): [references/openapi-response-validation.md](references/openapi-response-validation.md).

## JSON Schema Validation

Full content (verbatim, including all code samples): [references/json-schema-validation.md](references/json-schema-validation.md).

## Backward Compatibility Testing

Full content (verbatim, including all code samples): [references/backward-compatibility-testing.md](references/backward-compatibility-testing.md).

## Java REST Assured Contract Validation

Full content (verbatim, including all code samples): [references/java-rest-assured-contract-validation.md](references/java-rest-assured-contract-validation.md).

## GraphQL Schema Validation

Full content (verbatim, including all code samples): [references/graphql-schema-validation.md](references/graphql-schema-validation.md).

## Content-Type and Error Response Contracts

Full content (verbatim, including all code samples): [references/content-type-and-error-response-contracts.md](references/content-type-and-error-response-contracts.md).

## Best Practices

1. **Validate against the spec, not the implementation** -- Your contract tests should read the OpenAPI spec file and dynamically generate validations. If you hardcode expected fields in tests, you are testing your assumptions, not the contract.

2. **Use JSON Schema validators, not manual field checks** -- Libraries like AJV (TypeScript) and json-schema-validator (Java) provide comprehensive validation including nested objects, format constraints, and pattern matching. Manual checks miss edge cases.

3. **Test every documented status code** -- If your spec documents 200, 400, 404, and 500 responses, write tests that trigger each one and validate the response body against its respective schema.

4. **Run backward compatibility checks in CI** -- Keep the previous version of your spec in the repository and automatically compare it with the current version. Breaking changes should fail the build unless explicitly overridden.

5. **Validate error responses as rigorously as success responses** -- Error responses are part of the contract. Consumers depend on consistent error formats for error handling. An inconsistent error response is a contract violation.

6. **Test with real-world payloads** -- Use production-like data with unicode characters, empty strings, large numbers, deeply nested objects, and null values. Schema validation is only useful if it covers real edge cases.

7. **Version your schemas explicitly** -- Use schema version fields or API version headers. Tests should verify that the correct version is served and that version negotiation works properly.

8. **Validate response headers** -- Content-Type, Cache-Control, rate limit headers, and CORS headers are all part of the API contract. A missing Content-Type header can break consumers that rely on it.

9. **Generate client SDKs from the spec** -- If you can generate a type-safe client from your OpenAPI spec and the generated client works correctly with the API, your contract is accurate. This is the ultimate contract validation.

10. **Test nullable and optional field behavior** -- Verify that nullable fields can actually be null in responses, that optional fields can be omitted, and that required fields are always present regardless of the resource state.

11. **Include contract tests in provider CI and consumer CI** -- Providers run contract tests to verify they haven't broken the spec. Consumers run contract tests to verify their code handles the contract correctly. Both sides must validate.

12. **Document why each contract rule exists** -- When a contract test fails, the developer needs to know whether the test is wrong or the code is wrong. Comments explaining the business reason for each contract rule prevent accidental test removal.

## Anti-Patterns to Avoid

1. **Snapshot-based contract testing** -- Saving an API response as a JSON file and comparing future responses against it is brittle. Any additive change (new field) breaks the test even though it is not a breaking change. Use schema validation instead.

2. **Testing only with valid inputs** -- If you only send valid requests and check valid responses, you miss half the contract. Error responses, validation messages, and edge case behaviors are critical parts of the contract.

3. **Ignoring response headers in contract tests** -- Many developers validate only the response body. Headers like Content-Type, pagination links, rate limit info, and API version are contractual obligations that consumers depend on.

4. **Using production APIs for contract testing** -- Contract tests should run against a local or staging instance. Testing against production introduces flakiness from network issues and risks modifying production data.

5. **Maintaining contracts only in tests** -- If your OpenAPI spec lives only in test code, it is invisible to API consumers. The spec must be a shared artifact published to a spec portal or versioned alongside the codebase.

6. **Treating all field additions as non-breaking** -- While adding new response fields is generally safe, adding new required request fields or changing default values are breaking changes that contract tests must catch.

7. **Skipping contract tests for internal APIs** -- Internal APIs have consumers too. Other teams, microservices, and future developers depend on internal API contracts just as much as external consumers do.

## Debugging Tips

1. **Use Ajv verbose mode for schema failures** -- When a schema validation fails, the default error message may be cryptic. Configure AJV with `verbose: true` to see the actual data that failed validation alongside the expected schema.

2. **Diff specs visually** -- When backward compatibility tests fail, use tools like `openapi-diff` or `swagger-diff` to generate a human-readable diff between the old and new specs. This shows exactly what changed and whether it is breaking.

3. **Log full request and response** -- When a contract test fails unexpectedly, capture and log the complete HTTP request (method, URL, headers, body) and response (status, headers, body). The failure often becomes obvious once you see the raw data.

4. **Check content negotiation** -- If responses fail schema validation, verify that the client is sending the correct Accept header and that the server is returning the expected Content-Type. A mismatch can cause the server to return HTML instead of JSON.

5. **Validate the spec itself** -- Before running contract tests, validate your OpenAPI spec with a linter like `spectral` or `openapi-generator validate`. A malformed spec produces misleading test failures.

6. **Test with minimal and maximal payloads** -- Create test cases with only required fields (minimal) and all possible fields (maximal). This catches issues where optional fields are accidentally required or where extra fields cause parsing errors.

7. **Use test fixtures with known data** -- If contract tests depend on database state, use deterministic seed data. Flaky contract tests are often caused by tests running against non-deterministic data sets.

8. **Separate schema errors from business logic errors** -- When a contract test fails, determine whether the response structure is wrong (schema violation) or the response content is wrong (business logic error). These require different debugging approaches.

9. **Check for schema references that do not resolve** -- OpenAPI specs use `$ref` to reference shared components. If a reference points to a non-existent schema, the validator may silently skip validation, causing false passes.

10. **Verify API version routing** -- If backward compatibility tests pass but consumers report breakage, check that the API correctly routes requests to the appropriate version handler. Version misrouting is a common source of contract violations.

## Failure Exits (observable)

| Symptom (observable) | Way out |
|----------------------|---------|
| `Cannot find module` / `ajv` not installed | Install the validator dependency (`npm i -D ajv`) before running contract tests; the skill ships no runtime |
| Test run: `ENOENT ... openapi.yaml` | Spec path wrong — resolve the spec relative to `specs/` in the project structure; confirm with `ls` before running |
| Spectral/spec lint fails before any test runs | Fix the spec first — a malformed spec produces misleading test failures (Debugging Tip 5) |
| AJV errors look cryptic | Re-run with `verbose: true` (Debugging Tip 1); quote the instance path in the fix |
| Backward-compat test fails on an intentional breaking change | Do not delete the test — bump the API version and update the spec deliberately (Core Principles 2 and 6) |
| Tests pass locally, fail in CI | Check that CI has a staging instance URL and seeded fixtures (Debugging Tip 7); never fall back to production |
| `$ref` silently skipping validation (false pass) | Resolve all refs with a spec bundle/lint step; unresolvable refs are a build failure, not a pass |

## 中文速览（Quick Guide）

- **做什么**：以 OpenAPI / JSON Schema / GraphQL 契约为真源校验 API 响应，拦截删字段、改类型等破坏性变更，并给出向后兼容测试与 CI 接入模式。
- **何时用**：检查 API 变更是否破坏契约、在 CI 校验响应符合已发布契约，或评审消费者驱动契约测试时。
- **核心步骤**：①确保 spec 已入库、AJV 等校验器已装 ②按 schema 校验完整响应（状态码/头/错误格式） ③跑向后兼容测试 ④失败先修 spec 或实现再合入 ⑤接入 CI 每次提交执行。
- **国内可达性**：主流程离线可完成（校验依赖 npm 包 ajv，可走 npmmirror 等镜像安装），无其它境外服务依赖。

## FAQ / Wrong Way → Fix

| Wrong way | Fix |
|-----------|-----|
| Snapshot-testing whole JSON responses as the "contract" | Replace with schema validation — snapshots break on additive changes (Anti-Pattern 1) |
| Pointing contract tests at production "because the data is real" | Run against local/staging only (Anti-Pattern 4) |
| Validating only the 200 response body | Test every documented status code plus headers and error formats (Best Practices 3, 5, 8) |
| Treating a new *required request* field as non-breaking | New required request fields and changed defaults ARE breaking (Anti-Pattern 6) |
| Keeping the OpenAPI spec only inside test code | Publish the spec as a shared artifact alongside the codebase (Anti-Pattern 5) |
| Self-triggering contract validation on any API code change | Invoke for the named trigger scenarios; otherwise ordinary API work needs no contract run |

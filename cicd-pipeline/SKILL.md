---
name: cicd-pipeline
description: >-
  Configure testing in CI/CD pipelines for GitHub Actions, Jenkins, and GitLab CI: shards,
  parallelization, wait-on health checks, and service containers. Use when configuring
  tests in CI/CD pipelines (GitHub Actions, Jenkins, GitLab).
slug: cicd-pipeline
version: 1.2.0
displayName: cicd-pipeline
---

# CI/CD Pipeline Config Skill


## 中文速览（Quick Guide）

- **做什么**：为测试自动化配置 CI/CD 流水线，覆盖 GitHub Actions、Jenkins、GitLab CI 的分片、并行、wait-on 健康检查与服务容器。
- **何时用**：需要在流水线里跑测试（sharding、并行化、服务依赖），或排查流水线慢、不稳定、失败难定位时。
- **核心步骤**：①按 static analysis → unit → build → integration → E2E → performance 排序阶段（fail fast）→ ②配置并行分片与 wait-on 健康检查 → ③保存报告/截图/日志等 artifacts → ④对照 Best Practices 与 Anti-Patterns 复核。
- **国内可达性**：只生成 CI 配置文本；运行期拉取 actions、镜像与依赖的可达性取决于所选平台仓库与镜像源，正文未涉及具体镜像源。
You are an expert DevOps engineer specializing in CI/CD pipeline configuration for test automation. When the user asks you to create, review, or improve CI/CD pipelines for testing, follow these detailed instructions.

## Core Principles

1. **Fast feedback** -- Tests should provide feedback as quickly as possible.
2. **Fail fast** -- Run cheap tests first (lint, unit), expensive tests last (E2E, performance).
3. **Reproducible builds** -- Pipeline results must be deterministic regardless of when or where they run.
4. **Parallel execution** -- Maximize parallelism to minimize total pipeline duration.
5. **Artifact preservation** -- Always save test results, screenshots, and logs for debugging.

## Pipeline Strategy

Test pyramid in CI, stage ordering, and durations: moved to
[references/pipeline-strategy.md](references/pipeline-strategy.md). Rule that stays in
the body: **fail fast** -- order stages cheap-to-expensive (static analysis -> unit ->
build -> integration -> E2E -> performance), and keep stages independent so failures
diagnose to one stage.

## GitHub Actions

### Complete Testing Pipeline

```yaml
name: Test Pipeline
# Remaining pins below (action majors like @v4/@v3, postgres/redis/node tags,
# snyk @master) are channel examples: prefer the versions your project already
# uses; the refresh-managed table (rules + last-verified values + re-check
# procedure) is references/pinned-versions.md.
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '20'
  CI: true

jobs:
  lint-and-typecheck:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: ESLint
        run: npx eslint . --max-warnings=0

      - name: TypeScript Check
        run: npx tsc --noEmit

      - name: Prettier Check
        run: npx prettier --check .

  unit-tests:
    name: Unit Tests
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: [lint-and-typecheck]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Run Unit Tests
        run: npx jest --coverage --ci --reporters=default --reporters=jest-junit
        env:
          JEST_JUNIT_OUTPUT_DIR: ./test-results/unit

      - name: Upload Coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: unit-coverage
          path: coverage/
          retention-days: 7

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: unit-test-results
          path: test-results/unit/

  api-tests:
    name: API Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15
    needs: [unit-tests]
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Run Database Migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://test:test@<db-host>:5432/testdb

      - name: Start Application
        run: npm run start:test &
        env:
          DATABASE_URL: postgresql://test:test@<db-host>:5432/testdb
          REDIS_URL: redis://<redis-host>:6379
          PORT: 3000

      - name: Wait for Application
        run: npx wait-on http://<app-host>:<port>/health --timeout 30000

      - name: Run API Tests
        run: npx playwright test --project=api
        env:
          API_BASE_URL: http://<app-host>:<port>

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: api-test-results
          path: test-results/

  e2e-tests:
    name: E2E Tests (${{ matrix.shard }})
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: [unit-tests]
    strategy:
      fail-fast: false
      matrix:
        shard: [1/4, 2/4, 3/4, 4/4]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps chromium

      - name: Start Application
        run: npm run start:test &

      - name: Wait for Application
        run: npx wait-on http://<app-host>:<port> --timeout 30000

      - name: Run E2E Tests (Shard ${{ matrix.shard }})
        run: npx playwright test --shard=${{ matrix.shard }}

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-results-${{ strategy.job-index }}
          path: |
            test-results/
            playwright-report/

  merge-e2e-reports:
    name: Merge E2E Reports
    runs-on: ubuntu-latest
    if: always()
    needs: [e2e-tests]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - run: npm ci

      - name: Download All Reports
        uses: actions/download-artifact@v4
        with:
          pattern: e2e-results-*
          path: all-results/

      - name: Merge Reports
        run: npx playwright merge-reports --reporter=html all-results/

      - name: Upload Merged Report
        uses: actions/upload-artifact@v4
        with:
          name: e2e-report-merged
          path: playwright-report/
          retention-days: 14

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: [lint-and-typecheck]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - run: npm ci

      - name: npm audit
        run: npm audit --audit-level=high
        continue-on-error: true

      - name: Run Snyk
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  performance-tests:
    name: Performance Tests
    runs-on: ubuntu-latest
    timeout-minutes: 30
    if: github.ref == 'refs/heads/main'
    needs: [api-tests, e2e-tests]
    steps:
      - uses: actions/checkout@v4

      - name: Install k6
        run: |
          # <k6-key-id> = the CURRENT k6 apt archive signing key ID published in
          # k6's official APT install instructions (key IDs rotate; a stale ID
          # fails this step). Last-verified value and re-check procedure:
          # references/pinned-versions.md.
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys <k6-key-id>
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run Load Test
        run: k6 run k6/scripts/load-test.js --out json=k6-results.json
        env:
          BASE_URL: ${{ secrets.STAGING_URL }}

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: k6-results
          path: k6-results.json

  notify:
    name: Notify
    runs-on: ubuntu-latest
    if: always()
    needs: [unit-tests, api-tests, e2e-tests, security-scan]
    steps:
      - name: Slack Notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          fields: repo,message,commit,author,action,ref
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Jenkins Pipeline

The complete declarative Jenkinsfile (checkout/install, parallel static analysis,
unit tests with junit + coverage publishing, E2E with Playwright, Slack notify) is
externalized verbatim in [references/jenkins-pipeline.md](references/jenkins-pipeline.md) --
edit there when adapting; same stage order as the GitHub Actions pipeline above.

## GitLab CI

```yaml
stages:
  - lint
  - test
  - e2e
  - report

variables:
  NODE_VERSION: "20"
  CI: "true"
  # Must equal the @playwright/test version in the project's package.json --
  # the official image requires an exact match (derivation rule + refresh
  # notes: references/pinned-versions.md). Derive per project, not from here.
  PLAYWRIGHT_VERSION: "<match-playwright-package-version>"

.node-cache:
  cache:
    key:
      files:
        - package-lock.json
    paths:
      - node_modules/
    policy: pull

install:
  stage: .pre
  image: node:${NODE_VERSION}
  script:
    - npm ci
  cache:
    key:
      files:
        - package-lock.json
    paths:
      - node_modules/
    policy: push

lint:
  stage: lint
  image: node:${NODE_VERSION}
  extends: .node-cache
  script:
    - npx eslint . --max-warnings=0
    - npx tsc --noEmit

unit-tests:
  stage: test
  image: node:${NODE_VERSION}
  extends: .node-cache
  script:
    - npx jest --coverage --ci
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    when: always
    reports:
      junit: test-results/unit/junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
    paths:
      - coverage/

e2e-tests:
  stage: e2e
  # Tag is derived from PLAYWRIGHT_VERSION above (must match @playwright/test
  # exactly) -- never copy a literal tag from this template.
  image: mcr.microsoft.com/playwright:v${PLAYWRIGHT_VERSION}-jammy
  extends: .node-cache
  parallel: 4
  script:
    - npm run start:test &
    - npx wait-on http://<app-host>:<port> --timeout 30000
    - npx playwright test --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
  artifacts:
    when: always
    paths:
      - playwright-report/
      - test-results/
    expire_in: 7 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

## Test Parallelization Strategies

Shard-based (Playwright `--shard=i/N` via matrix), file-based (Jest workers), and
tag-based (`--grep @tag`) strategies with snippets: moved verbatim to
[references/parallelization-strategies.md](references/parallelization-strategies.md).

## Best Practices

1. **Cache dependencies** -- Cache `node_modules`, `.m2`, pip packages to speed up installs.
2. **Use matrix strategies** -- Run tests across multiple browsers/versions in parallel.
3. **Set timeouts** -- Prevent hung pipelines from consuming resources indefinitely.
4. **Always upload artifacts** -- Use `if: always()` to save results even on failure.
5. **Use service containers** -- Run databases and services as containers alongside tests.
6. **Cancel redundant runs** -- Use concurrency groups to cancel superseded pipeline runs.
7. **Separate concerns** -- Keep test stages independent so failures are easy to diagnose.
8. **Use environment-specific configs** -- Different configs for CI vs local development.
9. **Notify on failure** -- Integrate Slack, email, or Teams notifications.
10. **Monitor pipeline performance** -- Track and reduce pipeline duration over time.

## Anti-Patterns to Avoid

1. **Running all tests serially** -- Parallelize wherever possible.
2. **No artifact preservation** -- Without artifacts, debugging failures requires re-running.
3. **Flaky tests in CI** -- Fix or quarantine flaky tests immediately.
4. **No timeout limits** -- Hung tests can consume runner minutes for hours.
5. **Testing against external services** -- Use mocks or containers for dependencies.
6. **Hardcoded secrets** -- Always use CI/CD secret management.
7. **No caching** -- Installing dependencies from scratch every run wastes minutes.
8. **Ignoring CI-specific config** -- Some tests need different settings in CI (headless, retries).
9. **Single point of failure** -- If one shard fails, still collect results from others.
10. **Not cleaning up** -- Stale containers, files, or processes can affect subsequent runs.

## When to Use This Skill & NOT For

Use it when the user asks to create, review, speed up, or debug **test automation in CI/CD** (GitHub Actions, Jenkins, GitLab CI): sharding, parallelization, service containers, wait-on health checks, artifact/caching setup. NOT for (say so and stop):

- **Wrong repo / no repo**: no `.git` or no CI config and the user only wants local test runs -> local tooling, not this skill.
- **No network / restricted network**: runners that cannot reach npm/ghcr/mcr.microsoft.com need mirror registries and self-hosted runners configured first -- declare that prerequisite, do not hand over templates that will fail on `npm ci` or image pulls.
- **Deploy/infra pipeline authoring** (build-push-deploy, IaC): out of scope -- testing portion only. **Local flaky triage**: use the testing skills (`playwright-best-practices` etc.); this skill only quarantines/parallelizes in CI.

## Minimal Worked Example (prerequisite -> invocation -> output excerpt)

**Prerequisite**: a Node repo with `npm ci`, unit tests (`npx jest`) and an existing GitHub Actions workflow file (`.github/workflows/*.yml`).

**Invocation** (what the user says):

```text
"Our PR pipeline takes 40 minutes. Split the E2E suite across 4 runners
and add Postgres as a service container."
```

**What you produce**: a diff applying the templates above -- `strategy.matrix` shards `1/4..4/4` with `npx playwright test --shard=${{ matrix.shard }}` (E2E section), plus a `services: postgres:` block with `--health-cmd pg_isready` and `DATABASE_URL: postgresql://test:test@<db-host>:5432/testdb` (api-tests job). Net effect in this shape: 40m pipeline -> ~14m (fail-fast order: lint+unit gate before E2E).

**Output excerpt** (run after the change):

```text
unit-tests        ✓ 3m12s
e2e-tests (1/4)   ✓ 6m41s   e2e-tests (2/4)  ✓ 6m55s
e2e-tests (3/4)   ✓ 7m02s   e2e-tests (4/4)  ✓ 6m48s
```

## Troubleshooting (Failure Exits)

Observable CI failure -> what it means -> exit action (each CI run ends red/green; the red run is the observable output, not a reason to improvise):

- `npm ci` fails with `E404`/registry timeout -> dependency or registry unreachable -> pin the registry/mirror in `.npmrc` or runner env; do not switch to `npm install` to mask it.
- Service container never healthy: job hangs then aborts -> health-check options missing or wrong port mapping -> verify `ports: 5432:5432` + `--health-cmd pg_isready` (api-tests job); the fix lands there, not in the test step.
- `wait-on ... timeout` (exit code 1) -> app under test did not start -> the real error is in the `Start Application` step log above it, not in wait-on.
- One shard red, others green (`fail-fast: false`) -> real failure in that shard until proven flaky -> read that shard's uploaded `test-results/` artifact; quarantine only after re-qualifying as flaky. Artifacts missing on failure -> step lacked `if: always()`.

## Wrong -> Fix

| Wrong | Fix |
|---|---|
| Copying `<app-host>`/`<db-host>` placeholders literally into a real workflow | Replace with the DNS names CI provides (`localhost` for service containers on the same runner) |
| Copying example pins (`@v4`, `postgres:16`) into a project using different versions | Read `references/pinned-versions.md` rule + the project's own workflow/lockfile; the project always wins |
| `fail-fast: true` cancelling everything on one shard failure | `fail-fast: false` + merge reports (merge-e2e-reports job) so one flaky shard doesn't hide the others' results |
| Retrying the whole pipeline until green | Diagnose the failed stage from its artifact; retry-to-green hides real failures (anti-pattern #3) |

## Version References

Fast-changing pins are kept out of the templates above and live in one
refresh-managed table:

- `references/pinned-versions.md` — carries `lastUpdated` + `refreshInterval`
  (tiered by data stability: 30/60/180 days) + a per-row confidence column.
  Covers the Playwright Docker image tag rule, the k6 apt signing key ID,
  GitHub Action majors, and service image tags. When filling a `<placeholder>`
  in a template, read the rule from this table first; the project's own
  lockfile/package.json/CI config always wins over the example values there.

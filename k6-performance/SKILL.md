---
name: k6-performance
description: >-
  k6 performance testing: modern load testing with thresholds, scenarios, custom metrics,
  and env-based BASE_URL. Use when load/performance testing with k6 (thresholds,
  scenarios, metrics).
slug: k6-performance
version: 1.2.1
displayName: k6-performance
---

# k6 Performance Testing Skill

## 中文速览（Quick Guide）

- **做什么**：指导编写、审查、调试与解读 k6 负载／性能测试脚本，覆盖测试类型、阈值、场景、自定义指标与基于 `BASE_URL` 的环境配置。
- **何时用**：要写 k6 压测脚本、给已有脚本加阈值或场景、解读百分位与错误率、或选 smoke/load/stress/spike/soak 类型时；不涉及 k6（JMeter 等）、目标不可达、未获运维批准的生产压测、以及 CI 流水线接线（归 `cicd-pipeline`）。
- **核心步骤**：①先确认前置：`BASE_URL`（或默认主机）可达且 `k6 version` 有输出 ②选测试类型并按 Basic Load Test Script 组织脚本（stages、`http_req_duration` 阈值、checks）③按需加 scenarios、认证、数据驱动与自定义 metrics ④`k6 run -e BASE_URL=...` 执行并按结果分析解读百分位与错误率。
- **国内可达性**：正文唯一的外部引用是示例里的 `https://jslib.k6.io/papaparse/...` 远程模块；`k6` 本体、示例数据 CSV 与被测服务都需自备，正文未提供镜像或替代源，出现拉取失败时按 Failure Exits 报原始错误并问用户，不自行编造替代地址。

You are an expert performance engineer specializing in k6 load testing. When the user asks you to write, review, or debug k6 performance tests, follow these detailed instructions.

## When to Use This Skill

Use it when the user asks to: write a k6 load/performance test, add thresholds or scenarios to an existing k6 script, interpret k6 results (percentiles, error rate), or pick a test type (smoke/load/stress/spike/soak). **NOT for** (say so and stop, do not improvise):

- No k6 involved (JMeter/Gatling/Locust) -- this skill only covers k6.
- No reachable target: if `BASE_URL` (or the default host) does not respond, fix that first (see Troubleshooting).
- Production load testing: never without explicit ops approval (anti-pattern #10).
- CI pipeline wiring of k6 jobs: that is the `cicd-pipeline` skill's job.

## Minimal Worked Example (prerequisite -> invocation -> output excerpt)

**Prerequisite**: a running service with a health endpoint, and k6 installed (`k6 version` prints a version).

**Invocation** (what the user says):

```text
"Write a quick load test for my checkout API at https://staging.example.com,
95% of requests must be under 500ms."
```

**What you produce**: a script like the Basic Load Test Script below (stages + `http_req_duration: ['p(95)<500']` threshold + checks), run as:

```bash
k6 run -e BASE_URL=https://staging.example.com scripts/load-test.js
```

**Output excerpt** (end of a passing run):

```text
  ✓ checks..............: 100.0% ✓ 2410 ✗ 0
  ✓ http_req_duration...: p(95)=412ms p(99)=480ms
  █ THRESHOLDS
  ✓ http_req_duration p(95)<500
  ✓ http_req_failed   rate<0.01
EXIT CODE: 0 (all thresholds passed)
```

Exit code semantics: `0` = pass; non-zero (e.g. `99`) = at least one threshold was crossed -- treat a non-zero exit as a failed test, not a crashed tool.

## Troubleshooting (Failure Exits)

Exit code semantics: `0` = pass; non-zero (e.g. `99`) = at least one threshold was crossed -- treat a non-zero exit as a **failed test**, not a crashed tool. Quick map (full table in [references/troubleshooting.md](references/troubleshooting.md)):

- `connection refused` / target unreachable -> fix `BASE_URL` / service health first (`curl BASE_URL/api/health`); do not run load stages.
- Exit `99` with `✗` threshold lines -> a threshold was crossed; report which one and the measured value; never loosen thresholds to force green.
- Script `SyntaxError` -> fix the line, smoke-test (`k6 run --vus 1 --duration 30s`) before real load.
- Checks `✗` while `http_req_failed` = 0% -> fast wrong responses (4xx/5xx); inspect check names + `--http-debug`.

## Wrong -> Fix

Top mistakes (full table in [references/troubleshooting.md](references/troubleshooting.md)):

- Full load run to "check the script works" -> smoke first (1 VU, 1 minute).
- No `sleep()` think time -> add `sleep(1)`-`sleep(4)`.
- Thresholds defined after seeing results -> define before the run.
- Agent self-triggering a load test against an arbitrary URL -> load testing hits real infrastructure; run only on the user's explicit request and target.

## Core Principles

1. **Test realistic scenarios** -- Model tests after actual user behavior patterns.
2. **Define clear thresholds** -- Every test must have pass/fail criteria defined upfront.
3. **Ramp up gradually** -- Never slam the system with full load instantly.
4. **Use checks extensively** -- Validate responses even under load.
5. **Monitor and correlate** -- Combine k6 metrics with server-side monitoring.

## Project Structure

The recommended `k6/` directory layout (scripts/scenarios/utils/data/thresholds/config/results)
is externalized verbatim in [references/project-structure.md](references/project-structure.md) --
any Node/k6 repo can adopt it as-is or map it onto an existing layout.

## Basic Load Test Script

```javascript
import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const loginDuration = new Trend('login_duration');
const requestCount = new Counter('total_requests');

export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],  // 95th percentile < 500ms
    http_req_failed: ['rate<0.01'],                     // Error rate < 1%
    errors: ['rate<0.05'],                              // Custom error rate < 5%
    login_duration: ['p(95)<800'],                      // Login 95th < 800ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://<app-host>:<port>';

export default function () {
  group('Homepage', () => {
    const response = http.get(`${BASE_URL}/`);

    check(response, {
      'homepage status is 200': (r) => r.status === 200,
      'homepage loads in < 2s': (r) => r.timings.duration < 2000,
      'homepage has correct title': (r) => r.body.includes('<title>'),
    });

    errorRate.add(response.status !== 200);
    requestCount.add(1);
  });

  sleep(1);

  group('Login', () => {
    const startTime = Date.now();

    const loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
      email: 'user@example.com',
      password: 'SecurePass123!',
    }), {
      headers: { 'Content-Type': 'application/json' },
    });

    loginDuration.add(Date.now() - startTime);

    check(loginResponse, {
      'login status is 200': (r) => r.status === 200,
      'login returns token': (r) => JSON.parse(r.body).token !== undefined,
    });

    errorRate.add(loginResponse.status !== 200);
    requestCount.add(1);
  });

  sleep(Math.random() * 3 + 1); // Random think time between 1-4 seconds
}
```

## Test Types

Pick by what you need to learn, then copy the matching `options` block verbatim:

| Type | `options` shape | Answers |
|---|---|---|
| Smoke | `vus: 1`, `duration: '1m'` | Does the system work at all under minimal load? |
| Load | ramp 5m -> 100 VUs -> hold 10m -> down | Does it hold the target VUs within thresholds? |
| Stress | step 100 -> 200 -> 300 VUs, 5m each | Where does it break, and how gracefully? |
| Spike | 10 VUs -> 500 VUs for 3m -> recover | Does it survive a sudden 50x jump and recover? |
| Soak | 50 VUs sustained 4h | Does it degrade over time (leaks, drift)? |

Full ready-made scripts: [`references/test-types.md`](references/test-types.md).

## Scenarios (Advanced Configuration)

```javascript
export const options = {
  scenarios: {
    browse_products: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },
        { duration: '5m', target: 50 },
        { duration: '2m', target: 0 },
      ],
      gracefulRampDown: '30s',
      exec: 'browseProducts',
    },
    checkout_flow: {
      executor: 'constant-arrival-rate',
      rate: 10,          // 10 iterations per timeUnit
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 20,
      maxVUs: 50,
      exec: 'checkoutFlow',
    },
    api_health_check: {
      executor: 'constant-vus',
      vus: 5,
      duration: '10m',
      exec: 'healthCheck',
    },
  },
  thresholds: {
    'http_req_duration{scenario:browse_products}': ['p(95)<300'],
    'http_req_duration{scenario:checkout_flow}': ['p(95)<800'],
    'http_req_duration{scenario:api_health_check}': ['p(95)<100'],
  },
};

export function browseProducts() {
  http.get(`${BASE_URL}/api/products`);
  sleep(2);
}

export function checkoutFlow() {
  // Full checkout flow
  const cart = http.post(`${BASE_URL}/api/cart`, JSON.stringify({
    productId: 'prod-001',
    quantity: 1,
  }), { headers: { 'Content-Type': 'application/json' } });

  check(cart, { 'cart created': (r) => r.status === 201 });

  const checkout = http.post(`${BASE_URL}/api/checkout`, JSON.stringify({
    cartId: JSON.parse(cart.body).id,
  }), { headers: { 'Content-Type': 'application/json' } });

  check(checkout, { 'checkout success': (r) => r.status === 200 });
  sleep(1);
}

export function healthCheck() {
  http.get(`${BASE_URL}/api/health`);
  sleep(1);
}
```

## Authentication Patterns

```javascript
import http from 'k6/http';
import { check } from 'k6';

// Setup function runs once before the test
export function setup() {
  const loginResponse = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: 'load-test@example.com',
    password: 'SecurePass123!',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  const body = JSON.parse(loginResponse.body);
  return { token: body.token };
}

export default function (data) {
  const params = {
    headers: {
      Authorization: `Bearer ${data.token}`,
      'Content-Type': 'application/json',
    },
  };

  const response = http.get(`${BASE_URL}/api/users/me`, params);
  check(response, {
    'authenticated request succeeds': (r) => r.status === 200,
  });
}
```

## Data-Driven Testing

### Using CSV Data

```javascript
import { SharedArray } from 'k6/data';
import papaparse from 'https://jslib.k6.io/papaparse/5.1.1/index.js';
import { open } from 'k6';

const csvData = new SharedArray('users', function () {
  return papaparse.parse(open('./data/users.csv'), { header: true }).data;
});

export default function () {
  const user = csvData[Math.floor(Math.random() * csvData.length)];

  const response = http.post(`${BASE_URL}/api/auth/login`, JSON.stringify({
    email: user.email,
    password: user.password,
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'login successful': (r) => r.status === 200,
  });
}
```

### Using JSON Payloads

```javascript
import { SharedArray } from 'k6/data';
import { open } from 'k6';

const products = new SharedArray('products', function () {
  return JSON.parse(open('./data/payloads.json'));
});

export default function () {
  const product = products[__VU % products.length];

  const response = http.post(`${BASE_URL}/api/products`, JSON.stringify(product), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(response, {
    'product created': (r) => r.status === 201,
  });
}
```

## Custom Metrics

```javascript
import { Trend, Rate, Counter, Gauge } from 'k6/metrics';

// Trend -- tracks min, max, avg, percentiles
const apiCallDuration = new Trend('api_call_duration');

// Rate -- tracks percentage of non-zero values
const failureRate = new Rate('failure_rate');

// Counter -- tracks cumulative count
const totalRequests = new Counter('total_requests');

// Gauge -- tracks last value
const activeUsers = new Gauge('active_users');

export default function () {
  const start = Date.now();
  const response = http.get(`${BASE_URL}/api/products`);
  const duration = Date.now() - start;

  apiCallDuration.add(duration);
  failureRate.add(response.status !== 200);
  totalRequests.add(1);
  activeUsers.add(__VU);
}
```

## Best Practices

1. **Always define thresholds** -- Tests without pass/fail criteria are just observations.
2. **Use realistic think times** -- Add `sleep()` between requests to model real users.
3. **Ramp up gradually** -- Start low and increase load to identify breaking points.
4. **Parameterize everything** -- Use environment variables for URLs, credentials, and targets.
5. **Use `group()` for logical sections** -- Groups appear in results and help analysis.
6. **Use `check()` extensively** -- Checks validate correctness under load.
7. **Use `SharedArray` for large datasets** -- It reduces memory usage across VUs.
8. **Tag requests** -- Use tags to filter metrics in analysis.
9. **Run smoke tests first** -- Verify the script works before running at scale.
10. **Save results to file** -- Use `--out json=results.json` for post-analysis.

## Anti-Patterns to Avoid

1. **No thresholds** -- Without thresholds, you cannot determine if a test passed or failed.
2. **No think time** -- Running requests without `sleep()` creates unrealistic load patterns.
3. **Testing from a single location** -- Use distributed execution for realistic geographic spread.
4. **Ignoring ramp-up** -- Instant full load does not match real traffic patterns.
5. **Hardcoded URLs** -- Use environment variables and config files.
6. **Not validating responses** -- A fast 500 error is not a successful request.
7. **Forgetting `setup()`/`teardown()`** -- Use lifecycle hooks for test data management.
8. **Large file uploads in default function** -- Use `open()` outside the default function.
9. **No correlation with server metrics** -- k6 results alone do not tell the full story.
10. **Running performance tests against production without approval** -- Always coordinate with ops teams.

## Running k6 Tests

```bash
# Basic run
k6 run scripts/load-test.js

# With environment variables
k6 run -e BASE_URL=https://staging.example.com scripts/load-test.js

# With output to JSON
k6 run --out json=results/output.json scripts/load-test.js

# With cloud output (k6 Cloud)
k6 cloud scripts/load-test.js

# With InfluxDB output
k6 run --out influxdb=http://<influx-host>:8086/k6 scripts/load-test.js

# Override VUs and duration
k6 run --vus 50 --duration 5m scripts/smoke-test.js
```

## Results Analysis

After a test run, analyze these key metrics:

- **http_req_duration** -- Response time distribution (p50, p90, p95, p99)
- **http_req_failed** -- Percentage of failed requests
- **http_reqs** -- Total request rate (requests per second)
- **vus** -- Number of active virtual users
- **iterations** -- Number of complete test iterations
- **checks** -- Pass/fail ratio of check assertions
- **data_received** / **data_sent** -- Network throughput

Look for these patterns:
- Response time increasing as VUs increase = capacity limit
- Error rate spike at specific VU count = breaking point
- Gradual memory increase during soak test = memory leak
- Response time plateau then sudden spike = thread pool exhaustion

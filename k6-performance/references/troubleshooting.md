# k6 Troubleshooting & Wrong->Fix (long tables)

Pointer source: `SKILL.md` section "Troubleshooting (Failure Exits)". Content below is the
canonical long-form tables; the SKILL.md body keeps only a short summary. Exit code
semantics note: `0` = pass; non-zero (e.g. `99`) = at least one threshold was crossed --
treat a non-zero exit as a failed test, not a crashed tool.

## Troubleshooting (Failure Exits)

| Symptom (observable) | What it means | What to do |
|---|---|---|
| `ERRO[...] couldn't reach the target: dial tcp ... connection refused` | Target host/port wrong or service down | Re-check `BASE_URL` value and that the service is up (`curl BASE_URL/api/health`); do not proceed to load stages |
| Exit code `99`, threshold lines prefixed `✗` | Test ran fine but a threshold was crossed | This is a **failed test**: report which threshold (`p(95)=...` vs the bound), do not loosen thresholds to force green |
| `ERRO[...] SyntaxError ... at file:line` | Script error (typo, bad import) | Fix the script line first; run smoke (`k6 run --vus 1 --duration 30s`) before any real load |
| Checks fail (`✗`) while `http_req_failed` is 0% | Server returned fast but wrong responses (4xx/5xx handled as check failures) | Look at failed check names + `--http-debug` output; a fast 500 is not a passing request |
| Script needs a CSV/JSON file and errors with `open(...): no such file` | Data file path wrong (k6 resolves relative to the script, not cwd) | Fix the path or pass it via `__ENV`; do not inline the whole dataset |
| Durations are microseconds on every request | Requests are being answered by a CDN/cache or hitting the wrong host | Verify with a unique URL/tag and check server-side logs correlate |
| Timeouts under load only | Connection pool / keep-alive or server-side saturation | Correlate with server metrics (anti-pattern #9); lower the ramp and re-run stress stages to find the breaking point |

## Wrong -> Fix

| Wrong | Fix |
|---|---|
| Running the full load test to "check the script works" | Smoke test first (1 VU, 1 minute) -- Best Practice #9 |
| No `sleep()` between requests | Add realistic think time (`sleep(1)` to `sleep(4)`) |
| Hardcoded `https://staging.example.com` in the script | Read `__ENV.BASE_URL` with a sensible default (as in the Basic script) |
| Thresholds added *after* seeing results | Define thresholds before the run; post-hoc limits are just observations |
| `JSON.parse(r.body)` on every response inside `check()` without guarding | Guard: check `r.status === 200` first, then parse; a login page HTML body will crash the parse |
| Treating one failed run as proof of regression | Re-qualify: verify target health, re-run smoke, then load; flaky infra is not a perf regression |
| Letting the agent self-trigger a load test against an arbitrary URL | Load testing hits real infrastructure -- run only on the user's explicit request and target |

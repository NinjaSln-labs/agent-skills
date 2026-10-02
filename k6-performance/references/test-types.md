# k6 Test Types — Ready-Made `options` Blocks

Verbatim from `SKILL.md` § Test Types (progressive disclosure; the body keeps a selection table).

Pick by what you need to learn, then copy the block into your script and adjust the thresholds:

| Type | `options` shape | Answers |
|---|---|---|
| Smoke | `vus: 1`, `duration: '1m'` | Does the system work at all under minimal load? |
| Load | ramp 5m -> 100 VUs -> hold 10m -> down | Does it hold the target VUs within thresholds? |
| Stress | step 100 -> 200 -> 300 VUs, 5m each | Where does it break, and how gracefully? |
| Spike | 10 VUs -> 500 VUs for 3m -> recover | Does it survive a sudden 50x jump and recover? |
| Soak | 50 VUs sustained 4h | Does it degrade over time (leaks, drift)? |

## Smoke Test

```javascript
export const options = {
  vus: 1,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(99)<1500'],
    http_req_failed: ['rate<0.01'],
  },
};

// Quick validation that the system works under minimal load
export default function () {
  const response = http.get(`${BASE_URL}/api/health`);
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
```

## Load Test

```javascript
export const options = {
  stages: [
    { duration: '5m', target: 100 },   // Ramp up
    { duration: '10m', target: 100 },   // Steady state
    { duration: '5m', target: 0 },      // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};
```

## Stress Test

```javascript
export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 100 },
    { duration: '2m', target: 200 },
    { duration: '5m', target: 200 },
    { duration: '2m', target: 300 },
    { duration: '5m', target: 300 },
    { duration: '2m', target: 400 },
    { duration: '5m', target: 400 },
    { duration: '10m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
  },
};
```

## Spike Test

```javascript
export const options = {
  stages: [
    { duration: '1m', target: 10 },     // Normal load
    { duration: '10s', target: 500 },    // Spike!
    { duration: '3m', target: 500 },     // Stay at spike
    { duration: '10s', target: 10 },     // Recovery
    { duration: '3m', target: 10 },      // Observe recovery
    { duration: '1m', target: 0 },       // Ramp down
  ],
};
```

## Soak Test

```javascript
export const options = {
  stages: [
    { duration: '5m', target: 50 },     // Ramp up
    { duration: '4h', target: 50 },     // Sustained load for 4 hours
    { duration: '5m', target: 0 },      // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};
```
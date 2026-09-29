# Test Parallelization Strategies (moved from SKILL.md body — pointer only there)

## Test Parallelization Strategies

### Shard-Based Parallelization (Playwright)

```yaml
# Split tests evenly across N machines
strategy:
  matrix:
    shard: [1/4, 2/4, 3/4, 4/4]

steps:
  - run: npx playwright test --shard=${{ matrix.shard }}
```

### File-Based Parallelization (Jest)

```yaml
# Jest automatically parallelizes by file
steps:
  - run: npx jest --maxWorkers=4 --ci
```

### Tag-Based Parallelization

```yaml
jobs:
  smoke-tests:
    steps:
      - run: npx playwright test --grep @smoke

  regression-tests:
    steps:
      - run: npx playwright test --grep @regression

  visual-tests:
    steps:
      - run: npx playwright test --grep @visual
```

# Pipeline Strategy (moved from SKILL.md body — pointer only there)

## Pipeline Strategy

### Test Pyramid in CI

```
                    /\
                   /  \  E2E Tests (slowest, fewest)
                  /    \  ~5-15 minutes
                 /------\
                /        \  Integration Tests
               /          \  ~3-10 minutes
              /------------\
             /              \  Unit Tests (fastest, most)
            /                \  ~1-5 minutes
           /------------------\
          /                    \  Static Analysis
         /                      \  ~30 seconds - 2 minutes
        /________________________\
```

### Recommended Pipeline Stages

```
1. Checkout & Install    (~1 min)
2. Static Analysis       (~1-2 min) -- lint, type check, format check
3. Unit Tests            (~2-5 min) -- jest, pytest, junit
4. Build                 (~2-5 min) -- compile, bundle
5. Integration Tests     (~3-10 min) -- API tests, database tests
6. E2E Tests             (~5-15 min) -- browser tests, mobile tests
7. Performance Tests     (~5-30 min) -- only on main/release branches
8. Security Scan         (~3-10 min) -- SAST, dependency audit
9. Deploy to Staging     (~2-5 min)
10. Smoke Tests          (~2-3 min)
11. Report & Notify      (~1 min)
```

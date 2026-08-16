# Agent Skills

**[中文](README.md) | English**

> Portable Agent Skills (following the [Agent Skills](https://agentskills.io) open spec, `SKILL.md`), installable on any AI coding agent that supports the spec (Claude Code / Cursor / Deep Code / Copilot CLI, etc.).

**87 skills** covering the full product 0-1 lifecycle (discovery → definition → design → delivery → launch → operations), plus cross-cutting layers for DDD, engineering, QA, security, and UI/UX. Each skill is one directory with a `SKILL.md` (frontmatter `name`/`description` + body), progressive disclosure (body <500 lines; deeper content lives in `references/`).

The full map (skills classified by product-0-1 stage with orchestration paths — including the "stage-gate chain" and "problem-resolution chain") is in [SKILLS-MAP.md](SKILLS-MAP.md).

## Quick Start

```bash
git clone https://github.com/NinjaSln-labs/agent-skills.git
cd agent-skills

# Install a single skill (copy into your agent's skill discovery root)
cp -r <skill-name> ~/.agents/skills/
# Or install all skills
for d in agent-skills/*/; do cp -r "$d" ~/.agents/skills/; done
```

Restart/reload your agent client and the skills will be discovered. User-level directory: `~/.agents/skills/`; project-level: `<project>/.agents/skills/`.

## Skill List

### Engineering Practice (21)

| Skill | Description |
|-------|-------------|
| architecture-patterns | Architecture pattern guide |
| audit-item | Track audit findings as issues (open/fixed/recorded, enumerated by stage gate) |
| cicd-pipeline | CI/CD pipeline test configuration |
| code-review | Code review (incl. stage-end review mode) |
| codebase-design | Codebase design |
| deep-codebase-analysis | Deep codebase analysis |
| electron-best-practices | Electron best practices |
| frontend-design | Frontend design |
| git-workflow | Git branch/commit/PR/merge workflow |
| react-vite-best-practices | React + Vite performance optimization |
| systematic-debugging | Systematic debugging (root cause first) |
| problem-dive | Deep problem dive (evidence first, no direct fixing) |
| problem-resolution-flow | End-to-end problem resolution (locate→grade→research→fix→close) |
| typescript-best-practices | TypeScript best practices |
| verification-before-completion | Verify before claiming done (evidence over assertion) |
| stage-gate | Stage completion gate (runs stage-spec DoD assertions, verifies only) |
| stage-spec | Stage contract authoring (machine-verifiable DoD + TDD grid) |
| writing-plans | Write implementation plans |
| write-spec | Write specs / PRDs |
| executing-plans | Execute implementation plans |
| to-tickets | Break plans/PRDs into executable tickets |

### DDD / Domain-Driven Design (13)

| Skill | Description |
|-------|-------------|
| ddd-aggregates | Aggregate design |
| ddd-context-map | Context mapping |
| ddd-contexts | Bounded contexts |
| ddd-discover | Domain discovery |
| ddd-domain-interactions | Domain interactions |
| ddd-model-review | Domain model review |
| ddd-openspec-bridge | OpenSpec bridge |
| ddd-qa-chain | Quality chain (5 verification layers + DoD gate, project-mapped commands) |
| ddd-scope | Domain scope |
| ddd-subdomains | Subdomain classification |
| ddd-tactical-review | Tactical design review |
| event-storming | Event storming |
| prd-driven-ddd | PRD-driven DDD modeling |

### Product / PM (26)

| Skill | Description |
|-------|-------------|
| autonomous-investigation | Autonomous research |
| battle-card-builder | Competitive battle cards |
| company-intel | Company intelligence |
| competitive-analysis-process | Competitive analysis process |
| competitive-intel-watch | Competitive intel watch |
| competitive-research-snapshot | Competitive research snapshot |
| customer-journey-map | Customer journey mapping |
| discovery-interview-prep | Discovery interview prep |
| grill-me / plan-grilling | Plan/design grilling (stress test before committing) |
| intelligence-collection-disciplines | Intelligence collection disciplines |
| jobs-to-be-done | JTBD framework |
| product-launch | Product launch (ORB + five phases) |
| market-landscape-scan | Market landscape scan |
| positioning-statement / positioning-workshop | Positioning statement / workshop |
| prd-development | PRD development |
| press-release | Press-release PRD |
| problem-statement | Problem statement |
| product-doc-audit | Product doc audit |
| product-marketing | Product marketing context |
| proto-persona | Proto-persona |
| roadmap-planning | Roadmap planning |
| user-research | User research |
| voice-of-customer-miner | Voice-of-customer mining |
| workshop-facilitation | Workshop facilitation |

### Testing / QA (9)

| Skill | Description |
|-------|-------------|
| accessibility-auditor | Accessibility compliance audit |
| api-contract-validator | API contract validation |
| coverage-matrix | Coverage matrix (invariants/events/DoD ↔ test gates) |
| dependency-scan | Dependency vulnerability scan |
| k6-performance | k6 performance testing |
| playwright-best-practices | Playwright best practices |
| pixel-perfect | Visual regression (Playwright) |
| test-data-generation | Test data generation |
| visual-regression-tester | Visual regression testing (Playwright/Chromatic) |

### Security (3)

| Skill | Description |
|-------|-------------|
| config-scan | Config security scan |
| secrets-scan | Secrets leak scan |
| security-scan | Comprehensive security scan (OWASP Top 10) |

### UI/UX & Content (6)

| Skill | Description |
|-------|-------------|
| ui-ux-pro-max | UI/UX design database (84 styles/192 palettes/22 stacks) |
| web-design-guidelines | Web interface guidelines review |
| ui-animation | Motion design decisions (Emil Kowalski philosophy) |
| ui-typography | Typography rules (quotes/spacing/hierarchy) |
| ux-heuristics | Usability heuristic audit (Nielsen 10) |
| marketing-copywriting | Marketing copywriting |

### Agent Session & Personal Efficiency (9)

| Skill | Description |
|-------|-------------|
| project-handoff | Project handoff document |
| project-intake | Project intake / context restore |
| decision-log | Decision log ADR (record/query, state machine) |
| delegated-research | Delegated background research |
| session-health | Session health assessment |
| core-rules | Global rules (secrets/permissions/long-task feedback/session) |
| skill-description-audit | Skill description cross-validation audit |
| skill-eval | Skill behavior evaluation (with/without pass-rate comparison) |
| task-loop-progress | Long-task progress loop |

## Directory Layout

```
<skill-name>/
├── SKILL.md          # Skill definition (frontmatter name/description + body)
├── references/       # Progressive-disclosure reference docs (loaded on demand)
├── scripts/          # Helper scripts
├── templates/        # Templates
├── examples/         # Examples
└── evals/            # Evaluation cases
```

## License

Each skill carries its own `license` field (mostly MIT / CC-BY-SA-4.0); the frontmatter of each `SKILL.md` is authoritative.

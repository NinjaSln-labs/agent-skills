# Agent Skills

[![skills.sh](https://skills.sh/b/NinjaSln-labs/agent-skills)](https://skills.sh/NinjaSln-labs/agent-skills)

**[中文](README.md) | English**

> Portable Agent Skills (following the [Agent Skills](https://agentskills.io) open spec, `SKILL.md`), installable on any AI coding agent that supports the spec (Claude Code / Cursor / Deep Code / Copilot CLI, etc.).

**89 skills** covering the full product 0-1 lifecycle (discovery → definition → design → delivery → launch → operations), plus cross-cutting layers for DDD, engineering, QA, security, and UI/UX. Each skill is one directory with a `SKILL.md` (frontmatter `name`/`description` + body), progressive disclosure (body <500 lines; deeper content lives in `references/`).

The full map (skills classified by product-0-1 stage with orchestration paths — including the "stage-gate chain" and "problem-resolution chain") is in [SKILLS-MAP.md](SKILLS-MAP.md).

## Quick Start

```bash
npx skills add NinjaSln-labs/agent-skills   # one command installs all 89 skills via skills.sh
```

```bash
git clone https://github.com/NinjaSln-labs/agent-skills.git
cd agent-skills

# Install a single skill (copy into your agent's skill discovery root)
cp -r <skill-name> ~/.agents/skills/
# Or install all skills
for d in */; do cp -r "$d" ~/.agents/skills/; done
```

Restart/reload your agent client and the skills will be discovered. User-level directory: `~/.agents/skills/`; project-level: `<project>/.agents/skills/`.

## Skill List

### Engineering Practice (21)

| Skill | Description |
|-------|-------------|
| architecture-patterns | Implement proven backend architecture patterns including Clean Architecture, Hexagonal… |
| audit-item | Track audit/review findings as numbered issue files… |
| cicd-pipeline | Configure testing in CI/CD pipelines for GitHub Actions, Jenkins, and GitLab CI: shards… |
| code-review | Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes —… |
| codebase-design | Shared vocabulary for designing deep modules. |
| deep-codebase-analysis | Deep codebase analysis: read and analyze an entire software project's source to understand… |
| electron-best-practices | Guide AI agents through Electron app development with React including security patterns… |
| frontend-design | Guidance for distinctive, intentional visual design when building new UI or reshaping an… |
| git-workflow | Git workflow skill: branching strategies, Conventional Commits, creating or reviewing PRs… |
| react-vite-best-practices | React and Vite performance optimization guidelines. |
| systematic-debugging | Systematic Debugging: find the root cause before proposing fixes — symptom fixes are failure… |
| problem-handling | Problem handling: one evidence-driven pipeline from a reported symptom to a shipped fix —… |
| typescript-best-practices | Guide AI agents through TypeScript coding best practices including type safety, error handling… |
| version-management | Universal version management for any software artifact, independent of any VCS. |
| verification-before-completion | > Run verification commands and confirm fresh output before claiming work complete—evidence… |
| stage-gate | Run a stage-completion gate for staged delivery (spec-kit): read the stage spec's DoD… |
| stage-spec | Write or backfill a stage spec for staged delivery (spec-kit): turn a stage row of the phased… |
| writing-plans | > Write comprehensive implementation plans from a spec or requirements—break multi-step work… |
| write-spec | Write a feature spec or PRD from a problem statement or feature idea. |
| executing-plans | Executing Plans: execute a written implementation plan — load the plan, review it critically… |
| to-tickets | Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each… |

### DDD / Domain-Driven Design (13)

| Skill | Description |
|-------|-------------|
| ddd-aggregates | Design DDD aggregates and aggregate boundaries from invariants: aggregate roots, entities… |
| ddd-context-map | Map relationships and integration strategies between bounded contexts: pattern selection… |
| ddd-contexts | Design bounded contexts and their ubiquitous language: boundaries, responsibilities, glossary… |
| ddd-discover | Collaborative domain discovery via event storming or domain storytelling, producing event… |
| ddd-domain-interactions | Design collaboration mechanisms between building blocks: domain events, domain services… |
| ddd-model-review | Global model quality assessment: consistency, completeness, coupling analysis, and… |
| ddd-openspec-bridge | Map DDD tactical modeling artifacts into OpenSpec structured specifications for a smooth… |
| ddd-qa-chain | Run the quality verification chain—5 abstract verification layers (domain logic / contract /… |
| ddd-scope | DDD scope: converge vague requirements into executable DDD modeling inputs — problem statement… |
| ddd-subdomains | Identify business capabilities and classify subdomains (Core/Supporting/Generic), producing… |
| ddd-tactical-review | Detects anemic domain models, validates and refactors them into rich domain models, and… |
| event-storming | EventStorming facilitation knowledge and reference across Big Picture, Process Modeling, and… |
| prd-driven-ddd | Transform product design documents (PRDs, flowcharts, prototypes, state machines, rules/AC)… |

### Product / PM (26)

| Skill | Description |
|-------|-------------|
| autonomous-investigation | The protocol behind every investigation skill. |
| battle-card-builder | Research and draft a competitive battle card from public evidence — every claim labeled and… |
| company-intel | Research a company, industry, or competitor set using web search and seven analytical lenses. |
| competitive-analysis-process | Orchestrate a complete competitive analysis across six steps, from landscape to strategic… |
| competitive-intel-watch | Competitive Intel Watch: scheduled delta monitoring against a prior competitive snapshot. |
| competitive-research-snapshot | Research a competitive landscape with cited snapshots, a comparison matrix, and so-what… |
| customer-journey-map | Create a customer journey map across stages, touchpoints, actions, emotions, and metrics. |
| discovery-interview-prep | Plan customer discovery interviews with the right goal, segment, constraints, and method. |
| grill-me | User-invoked entry that runs a /plan-grilling session — a relentless interview to sharpen a… |
| plan-grilling | Grill the user relentlessly about a plan, decision, or idea. |
| intelligence-collection-disciplines | Run competitive research like an intelligence agency: eight collection disciplines (OSINT to… |
| jobs-to-be-done | Uncover customer jobs, pains, and gains in a structured JTBD format. |
| product-launch | Plan a product launch with the ORB framework (owned, rented, borrowed channels) and a… |
| market-landscape-scan | Market Landscape Scan: map a market's segments, players, substitutes, and whitespace with cited… |
| positioning-statement | Create a Geoffrey Moore-style positioning statement. |
| positioning-workshop | Run a positioning workshop that surfaces target customer, unmet need, category, benefits, and… |
| prd-development | PRD development: build a structured Product Requirements Document that connects problem, users… |
| press-release | Write an Amazon-style press release that defines customer value before building. |
| problem-statement | Write a user-centered problem statement with who is blocked, what they are trying to do, why it… |
| product-doc-audit | Product Document Audit: three-layer audit of a product documentation set (0-1 phase docs): 1)… |
| product-marketing | > Creates and updates `.agents/product-marketing.md` — shared product, audience, and… |
| proto-persona | Create a proto-persona from current research, market signals, and team knowledge. |
| roadmap-planning | Plan a strategic roadmap across prioritization, epic definition, stakeholder alignment, and… |
| user-research | Plan, conduct, and synthesize user research. |
| voice-of-customer-miner | Mine public reviews, app stores, and forums for unmet needs, competitor weaknesses, and… |
| workshop-facilitation | Facilitate workshop sessions in a one-step, multi-turn flow. |

### Testing / QA (9)

| Skill | Description |
|-------|-------------|
| accessibility-auditor | Comprehensive WCAG 2.1 AA compliance testing combining automated axe-core scans with manual… |
| api-contract-validator | Validate API responses against OpenAPI/Swagger specifications, JSON Schema definitions, and… |
| coverage-matrix | Generate or maintain the coverage matrix (docs/tests/coverage-matrix.md): scan unit test names… |
| dependency-scan | Dependency scan: detect CVEs and security issues in project dependencies. |
| k6-performance | k6 performance testing: modern load testing with thresholds, scenarios, custom metrics, and… |
| playwright-best-practices | Playwright best practices for E2E, component, API, visual, and accessibility testing… |
| pixel-perfect | Visual regression testing — pixel-by-pixel screenshot comparison against a baseline. |
| test-data-generation | Test data strategies using Faker.js, factories, builders, and database seeding Use when… |
| visual-regression-tester | Visual Regression Tester: screenshot comparison, diff detection, and CI integration using… |

### Security (3)

| Skill | Description |
|-------|-------------|
| config-scan | Config scan: detect security misconfigurations in config files, Docker, and IaC. |
| secrets-scan | Secrets scan: detect API keys, passwords, tokens, and other secrets in code. |
| security-scan | Security scan: scan code for security vulnerabilities including OWASP Top 10, secrets, and… |

### UI/UX & Content (6)

| Skill | Description |
|-------|-------------|
| ui-ux-pro-max | UI/UX Pro Max design intelligence for web and mobile: searchable local database with styles… |
| web-design-guidelines | Review UI code for Web Interface Guidelines compliance (Vercel Labs guidelines via WebFetch or… |
| ui-animation | > Encodes Emil Kowalski's design-engineering philosophy: UI polish, component design, animation… |
| ui-typography | UI Typography: professional typography rules for UI design, web apps, software interfaces, and… |
| ux-heuristics | Evaluate and improve interface usability using heuristic analysis. |
| marketing-copywriting | Marketing copywriting: write, rewrite, or improve marketing copy for any page — homepage… |

### Agent Session & Personal Efficiency (11)

| Skill | Description |
|-------|-------------|
| project-handoff | Generate/update a project engineering handoff document (HANDOFF.md) — reference-style delta… |
| project-intake | Take over a project as the receiving side — read HANDOFF.md and restore context by its five… |
| experiment-handoff | Experiment handoff for mid-project experiments and spikes. |
| decision-log | Record or query architecture decision records (ADR) — Nygard template… |
| delegated-research | Investigate a question against high-trust primary sources and capture the findings as a… |
| session-health | Session Health: assess the current AI coding tool session — context compaction/condensation… (deprecated) |
| core-rules | (deprecated) — no longer maintained. |
| skill-description-audit | Skill Description Audit. |
| skill-eval | Behaviorally evaluate a skill: define 3-5 representative tasks, run each N>=3 times with and… |
| skill-fit | Skill fit: a read-only audit that matches a project against the skill catalog. |
| task-loop-progress | Generate config + adapter for the generic long-task progress loop (scaffold… (deprecated) |

## Deprecated

These names were renamed or merged and are no longer published on their own (old names must not be reused):

| Old name | Status |
|----------|--------|
| `animation` | renamed to `ui-animation` |
| `typography` | renamed to `ui-typography` |
| `grilling` | renamed to `plan-grilling` |
| `launch` | renamed to `product-launch` |
| `copywriting` | renamed to `marketing-copywriting` |
| `research` | renamed to `delegated-research` |
| `sin-rules` | renamed to `core-rules` |
| `problem-dive` | merged into `problem-handling` |
| `problem-resolution-flow` | merged into `problem-handling` |

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

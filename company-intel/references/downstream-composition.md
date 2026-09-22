# Downstream Composition Guide (company-intel)

> Companion to `SKILL.md`, for **other skill authors and agent builders**: the stable output structure and the per-section downstream consumption map.

## Downstream Composition Guide

This section is for other skill authors and agent builders who want to consume company-intel output.

### What This Skill Produces

A structured markdown document with 11 numbered sections (12 for competitor sets). Each section has a stable heading and defined content type:

| Section | Content Type | Downstream Use |
|---------|-------------|----------------|
| 1. What This Entity Is | Entity definition, scale, market position | Context setting for any downstream skill |
| 2. How It Makes Money | Revenue, costs, margins, financial logic | business-health diagnosis, feature investment advice |
| 3. Who It Serves | Buyers, users, segments, stakeholder map | `proto-persona`, `jobs-to-be-done`, `positioning-statement` |
| 4. What It Sells or Delivers | Value propositions, core offers | `positioning-statement`, battlecards |
| 5. Key Product Lines | Product families, platforms, services | Competitive analysis, portfolio mapping |
| 6. Business and Market Pressures | Competitive, regulatory, technology forces | PESTEL analysis, de-risk measurement scan |
| 7. Competitors and Alternatives | Direct, adjacent, substitutes, disruptors | Battlecards, competitive positioning |
| 8. Important Trends and Risks | Macro forces, AI impact, consolidation | PESTEL analysis, de-risk measurement scan |
| 9. Strategic Signals | Patents, hiring, leadership changes | Competitive intelligence, trend analysis |
| 10. What This Means for PM | Org dynamics, discovery maturity, PM challenges | Workshop content, coaching, engagement prep |
| 11. Sources and Confidence | Citations, assumptions, data quality flags | Quality assurance for all downstream use |
| 12. Cross-Company Comparison | Divergence, convergence, gaps, tensions | Battlecards, SWOT, competitive strategy |

### How to Reference This Skill

In your skill's References section:
```markdown
- **[company-intel](../company-intel/SKILL.md)** (Workflow) — Run first to generate structured company/industry research; this skill consumes Sections [X, Y, Z] as input
```

### Passing Output to Downstream Skills

When handing off to a downstream skill, pass the relevant sections explicitly:
- **Battlecard** → Sections 4, 5, 7, 9, 12
- **SWOT** → Sections 2, 6, 7, 8, 9
- **Positioning** → Sections 3, 4, 7
- **PESTEL** → Sections 6, 8, 9
- **TAM/SAM/SOM** → Sections 2, 3, 5
- **Business health** → Sections 2, 5, 8
- **PM briefing** → Sections 1, 5, 9, 10
- **Workshop guide** → Sections 6, 9, 10 (tensions and PM implications)

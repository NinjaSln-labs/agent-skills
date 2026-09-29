---
name: user-research
description: >-
  Plan, conduct, and synthesize user research. Trigger with "user research plan",
  "interview guide", "usability test", "survey design", "research questions", or when the
  user needs help with any aspect of understanding their users through research. NOT for
  usability of code you cannot observe, or research with no user access.
slug: user-research
version: 1.1.0
displayName: user-research
---

# User Research

Help plan, execute, and synthesize user research studies.

## Research Methods

| Method | Best For | Sample Size | Time |
|--------|----------|-------------|------|
| User interviews | Deep understanding of needs and motivations | 5-8 | 2-4 weeks |
| Usability testing | Evaluating a specific design or flow | 5-8 | 1-2 weeks |
| Surveys | Quantifying attitudes and preferences | 100+ | 1-2 weeks |
| Card sorting | Information architecture decisions | 15-30 | 1 week |
| Diary studies | Understanding behavior over time | 10-15 | 2-8 weeks |
| A/B testing | Comparing specific design choices | Statistical significance | 1-4 weeks |

## Interview Guide Structure

1. **Warm-up** (5 min): Build rapport, explain the session
2. **Context** (10 min): Understand their current workflow
3. **Deep dive** (20 min): Explore the specific topic
4. **Reaction** (10 min): Show concepts or prototypes
5. **Wrap-up** (5 min): Anything we missed? Thank them.

## Analysis Framework

- **Affinity mapping**: Group observations into themes
- **Impact/effort matrix**: Prioritize findings
- **Journey mapping**: Visualize the user experience over time
- **Jobs to be done**: Understand what users are hiring your product to do

## Deliverables

- Research plan (objectives, methods, timeline, participants)
- Interview guide (questions, probes, activities)
- Synthesis report (themes, insights, recommendations)
- Highlight reel (key quotes and observations)

## Example

Input: "I need to find out why trial users churn in week 1."
Output: a short plan — method (5-8 interviews), 6 open questions that avoid leading the
witness ("walk me through the first thing you did after signing up"), a recruiting
criterion (signed up in the last 30 days, churned), and a synthesis template ready to fill.

## Edge cases → what to do

- **No access to real users**: say so and stop short of fabricating findings. Offer the
  closest legal substitutes — support-ticket mining, public community threads, review
  mining — and label them as proxies, not user research.
- **Stakeholders want a survey first**: push back with the sample-size reality (100+
  respondents, and you still won't learn *why*); recommend interviews unless the question
  is genuinely quantified ("which of these 2 labels do more people understand?").
- **Findings conflict with stakeholder beliefs**: report the evidence with quotes and
  counts; do not soften it into what the room wants to hear.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Leading questions ("Don't you find it confusing?") | Ask what the user did / expected, not what they feel about your hypothesis |
| Interviewing only happy customers | Recruit churned and struggling users too; add a screening criterion |
| Synthesizing from memory | Do affinity mapping on notes/quotes the same day as the session |
| Survey measuring "why" | Use surveys to quantify *what*; use interviews to explain *why* |

## NOT for

- Pure market sizing or competitive analysis — that is market research, not user research.
- Studies with no user access and no proxy data — say so instead of inventing personas.
- A/B test implementation — design the comparison here; the code change is out of scope.

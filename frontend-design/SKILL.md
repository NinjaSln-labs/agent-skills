---
name: frontend-design
description: >-
  Guidance for distinctive, intentional visual design when building new UI or reshaping an
  existing one. Helps with aesthetic direction, typography, color, motion, and interface copy
  that doesn't read as templated defaults. Use when designing or restyling a web page, landing
  page, dashboard, or app UI; when choosing fonts, palettes, layout, or a signature visual
  element; or when generated design looks generic and needs a stronger point of view. NOT for:
  accessibility/WCAG compliance review, UI code review against style guides, or marketing sales
  copy (boundaries by task; no other skill implied).
slug: frontend-design
version: 1.2.0
displayName: frontend-design
---

# Frontend Design

## 中文速览（Quick Guide）

- **做什么**：指导新建或重塑界面时做出有明确观点的视觉设计，定调色板、字体、版面、动效与文案，避免生成物像模板。
- **何时用**：设计或重做网页、落地页、仪表盘与应用界面，或要挑字体／配色／版面、给界面一个签名式视觉元素时；不用于 WCAG 合规评审、UI 代码评审与营销文案。
- **核心步骤**：①先把题目定死（一个具体主体、受众、页面唯一职责）②按正文列的设计原则定方向：hero、字体配对、结构即信息、动效、复杂度匹配、文案 ③走「头脑风暴→探索→计划→批判→做→再批判」的流程 ④对照正文的默认长相清单与克制／自检要求收尾。
- **国内可达性**：本技能为纯设计方法与写作指导，不抓取外部数据、不依赖境外在线服务。

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Ground it in the subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. If there's any information in your memory about the human's preferences, context about what they're building, or designs you've made before – use that as a hint. The subject's own world, its materials, instruments, artifacts, and vernacular, is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is a thesis. Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the template answer, only use if that's truly the best option.

Typography carries the personality of the page. Pair the display and body faces deliberately, not the same families you would reach for on any other project, and set a clear type scale with intentional weights, widths, and spacing. Make the type treatment itself a memorable part of the design, not a neutral delivery vehicle for the content.

Structure is information. Structural devices, numbering, eyebrows, dividers, labels, should encode something true about the content, not decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence - like a real process or a typed timeline where order carries information the reader needs. Question if choices like numbered markers actually make sense before incorporating them.

Leverage motion deliberately. Think about where and if animation can serve the subject: a page-load sequence, a scroll-triggered reveal, hover micro-interactions, ambient atmosphere. An orchestrated moment usually lands harder than scattered effects; choose what the direction calls for. However, sometimes less is more, and extra animation contributes to the feeling that the design is AI-generated.

Match complexity to the vision. Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

Consider written content carefully. Often a design brief may not contain real content, and it's up to you to come up with copy. Copy can make a design feel as templated as the design itself. See the below section on writing for more guidance.

## Process: brainstorm, explore, plan, critique, build, critique again

For calibration: AI-generated design right now clusters around three looks: (1) a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns. All three are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. Just like a human designer who's hired, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Work in two passes. First, brainstorm a short design plan based on the human's design brief: create a compact token system with color, type, layout, and signature. Color: describe the palette as 4–6 named hex values. Type: the typefaces for 2+ roles (a characterful display face that's used with restraint, a complementary body face, and a utility face for captions or data if needed). Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Signature: the single unique element this page will be remembered by that embodies the brief in an appropriate way.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan exactly and deriving every color and type decision from it.

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and a element-based selector like .cta). This can happen often with paddings/margins between sections.

Try to do a lot of this planning and iteration in your thinking, and only show ideas to the user when you have higher confidence it'll delight them.

## Restraint and self-critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself! Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected. Critique your own work as you build, taking screenshots if your environment supports it – a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory. Human creators have memory and always try to do something new, so if you have a space to quickly jot down notes about what you've tried, it can help you in future passes.

## How to invoke

There is no CLI or bundled script — trigger it with a design ask. Prompts that route here:

- "Design a landing page for <product> — make it distinctive, not templated."
- "This dashboard looks generic; give it a stronger point of view."
- "Pick fonts and a palette for our docs site."

Defaults when you supply nothing else: the skill pins the subject, audience, and the page's single job itself (see "Ground it in the subject"), then produces a plan with a 4–6 color palette, 2+ type roles, one layout concept, and one signature element — and shows the plan before writing code.

## Worked Example

Brief: "Landing page for a tide-pool logging app for marine volunteers."

Ask: "Design the landing page."

Expected plan excerpt (the token system from the Process section):

```
Color:  #0B3C49 deep slate-teal, #EAF4F2 foam, #F2A541 buoy orange, #1B7F79 kelp
Type:   display "Fraunces" (hero thesis only), body "Public Sans"
Layout: full-bleed tide-pool hero with the headline set low-left; the social-proof
        section is a species-log table mirroring the app's own UI
Signature: a tide-chart divider that fills as you scroll, echoing the app's log chart
```

The plan is then critiqued against the three AI-look defaults and revised (with the revision stated) before any code is written.

## Failure exits and boundaries

- Brief names no subject and there is no memory of the human's context: pick one concrete subject and state it — this is documented behavior, not an error; if the human corrects it, restart from the token system with the correction.
- Brief pins a look ("use cream and serif", "copy brand X"): follow it exactly even when it matches one of the three default looks — the brief wins; say so rather than re-briefing.
- No way to run or screenshot code: deliver plan + code and state plainly that screenshot self-critique was skipped — never claim screenshots you did not take.

## NOT for / Anti-patterns (observable)

- NOT for accessibility audits: the quality floor here (focus visible, reduced motion, responsive) is a floor — "is this WCAG compliant?" is a different task.
- NOT for checking existing UI code against a style guide or design tokens — that is a code-review task, not a design one.
- NOT for marketing sales copy: interface copy (buttons, errors, empty states) is in scope; persuasive landing-page sales copy is not.
- Anti-pattern: shipping the first plan — output with no stated revision is a skipped two-pass step.
- Anti-pattern: reaching for cream+serif+terracotta, black+acid-green, or broadsheet hairlines when the brief left those axes free.

## Wrong → Right

| Wrong | Right |
|---|---|
| "Just make it look nice" → designing silently | Pin subject/audience/job, state the choice, then design |
| Five accents and three display faces | 4–6 named colors; one display face used with restraint |
| Animation on every section | One orchestrated moment; cut the rest |
| 01/02/03 numbering on unordered content | Number only real sequences |
| Asking "is this accessible?" | Out of scope — run an accessibility review instead |

## More on writing in design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Bring the same intentionality to copy that you would bring to spacing and color. Before writing anything, ask what the design needs to say, and how it can best be said to help the person navigate the experience.

Write from the end user's side of the screen. Name things by what people control and recognize, never by how the system is built. A person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Being specific is always better than being clever.

Use active voice as default. A control should say exactly what happens when it's used: "Save changes," not "Submit." An action keeps the same name through the whole flow, so the button that says "Publish" produces a toast that says "Published." The vocabulary of an interface is the signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act.

Keep the register conversational and tuned: plain verbs, sentence case, no filler, with tone matched to the brand and the audience. Let each element do exactly one job. A label labels, an example demonstrates, and nothing quietly does double duty.

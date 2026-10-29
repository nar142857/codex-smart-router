---
name: smart-router
description: Delegate all computer and browser UI operation to a GPT-6.1 Terra subagent. Select engineering subagents when independent, bounded work makes delegation worthwhile; keep small or tightly coupled non-UI work with Root.
---

# Smart Router

Root uses the conversation-selected model, including Astra. It may directly perform discovery, implementation, testing, review, and synthesis. Do not override that model choice.

## Decide whether to delegate

For non-UI engineering work, delegate only a concrete deliverable that can be completed independently while Root advances useful work, or an independent review with material value. Consider context transfer, coordination, integration, and duplicated checks as part of the cost. A cheaper model does not by itself prove lower total usage.

Keep small, sequential, or tightly coupled non-UI tasks with Root. UI delegation is mandatory regardless of task size or coordination cost. There is no minimum agent count and no mandatory explorer → worker → tester → reviewer sequence. Respect the host's concurrency limit without treating it as a target. Do not create roles mechanically.

## Choose a role for delegated work

| Role | Model | Appropriate task |
| --- | --- | --- |
| explorer | Luna | Locate files, call chains, dependencies, existing patterns and tests |
| researcher | Luna | Focused official documentation or API research |
| tester | Luna | Relevant tests, typecheck, build, reproduction and verification |
| fast_worker | Luna | Obvious, bounded low-risk edits with an established pattern |
| worker | Terra | Normal feature implementation or coherent multi-file changes |
| browser_operator | gpt-6.1-terra | All computer and browser UI operation, including native apps, navigation, forms, and visual verification |
| expert | Sol | Subtle bugs, algorithms, concurrency, performance or difficult integration |
| reviewer | Sol | Independent review justified by change scope or risk |
| deep_reviewer | Astra | Exceptional high-risk independent review with costly failure modes |

The restriction on additional Astra subagents does not constrain Astra Root. Do not delegate ordinary work away merely because Root is Astra. Model roles express preferences, not measured guarantees of cost or quality.

## Mandatory computer and browser UI delegation

All tasks requiring computer or browser UI operation must be delegated to a browser_operator subagent using gpt-6.1-terra. The subagent executes every UI step, including simple, sequential, or tightly coupled steps; Root must not operate the UI directly, even when Root uses the same model. Keep complex engineering analysis, implementation, and review on the existing routing.

For mixed tasks, Root retains engineering decisions and delegates all UI execution to the Terra subagent with clear steps and acceptance criteria. This includes native applications, screenshots, clicks, typing, scrolling, navigation, and UI verification. Shell commands, code edits, and direct API or connector calls that do not operate a UI remain on the existing engineering route. Prefer available purpose-built tools when suitable. If the role, model, UI tools, or concurrency capacity is unavailable, report the blocker and wait or request user direction; Root must not take over UI execution or silently substitute another model. This mandatory rule takes precedence over the general delegation cost guidance.

## Scope and context

Give each subagent its objective, owned files, constraints, required evidence, and acceptance criteria. Pass only relevant context. Parallelize non-overlapping work; resolve shared contracts before separate workers edit them. Ask for concise conclusions, paths/symbols, validation, and risks rather than full files or transcripts.

Escalate when evidence shows the assigned task exceeds the selected role: unfamiliar interacting contracts may need Terra; subtle root causes or hard architecture may need Sol. An independent Astra review is optional for exceptional risk, not an obligatory final stage.

## Integration and completion

Root reconciles outputs, reviews the actual changes, resolves conflicts, and verifies acceptance criteria. Start with relevant checks and expand only for new changes, failures, or unresolved risks. Do not duplicate completed validation without a reason, and do not accept output merely because a subagent finished.

Follow the global/project token-report rule when routing was actually used. The report switch does not change the mandatory UI delegation rule.

# Project Instructions

## Project context
- Summarize the repository purpose here.
- List primary stack/frameworks here.
- List important architecture boundaries here.

## Commands
- Install: `<command>`
- Dev: `<command>`
- Test: `<command>`
- Lint: `<command>`
- Typecheck: `<command>`
- Build: `<command>`

## Engineering rules
- Follow existing repository patterns before introducing new abstractions.
- Keep changes scoped to the user request.
- Do not change public APIs, database schemas, dependencies, auth/security behavior, or deployment configuration unless required.
- Add/update targeted tests for behavior changes.
- Prefer focused validation first; expand only when risk requires it.

## Multi-agent routing
Use `$smart-router` for every task requiring computer or browser UI operation. For engineering work, use it only when a concrete subtask has enough independent work to justify delegation.

- Root is the model selected for the current Codex conversation and may complete non-UI work directly; computer and browser UI execution is delegated as required below.
- Keep small, sequential, and tightly coupled non-UI work with Root. Do not require a fixed number of agents or an explorer/worker/tester/reviewer sequence.
- For delegated work, prefer Luna for focused discovery, research, validation, or obvious small edits; Terra for normal implementation; Sol for difficult implementation or justified independent review.
- All tasks requiring computer or browser UI operation must be delegated to a browser_operator subagent using gpt-6.1-terra. The subagent executes every UI step, including simple, sequential, or tightly coupled steps; Root must not operate the UI directly, even when Root uses the same model. Keep complex engineering analysis, implementation, and review on the existing routing.
- Use an additional Astra agent only for exceptional high-risk independent review; this does not restrict Astra when it is Root.
- Respect the host concurrency limit as a ceiling, not a target. Root integrates and validates delegated results.

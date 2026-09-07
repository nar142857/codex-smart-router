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
Use `$smart-router` for non-trivial work.
- Luna: exploration/research/tests/obvious low-risk edits.
- Terra: normal implementation.
- Sol: hard debugging, architecture-sensitive logic, algorithms/concurrency/performance, substantial review.
- Astra: root/orchestration; deep review only for very high-risk changes.

Do not use multi-agent delegation for trivial one-file edits unless it clearly reduces context or latency.

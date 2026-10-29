# Smart Multi-Agent Routing

Use `$smart-router` for every task requiring computer or browser UI operation, and when independent, bounded software-engineering subtasks make delegation worthwhile in quality, total time, or total usage. Keep local, sequential, or tightly coupled non-UI work with Root.

- Root uses the model selected in the conversation, including Astra, and may directly analyze, implement, test, review, and summarize any in-scope task; computer and browser UI execution is delegated as required below.
- For non-UI engineering work, delegate only concrete deliverables with enough independent work to justify context transfer, coordination, and integration. There is no minimum agent count or required role sequence; respect the host's concurrency limit without treating it as a target.
- For delegated work, prefer Luna for focused discovery, research, validation, and obvious small edits; Terra for normal implementation; Sol for difficult implementation or justified independent review.
- All tasks requiring computer or browser UI operation must be delegated to a browser_operator subagent using gpt-6.1-terra. The subagent executes every UI step, including simple, sequential, or tightly coupled steps; Root must not operate the UI directly, even when Root uses the same model. Keep complex engineering analysis, implementation, and review on the existing routing.
- Reserve additional Astra subagents for exceptional high-risk independent review. This restriction does not apply to Astra Root.
- Pass only needed context; request conclusions, file/symbol references, validation, and risks. Root integrates results and owns final acceptance.

## Task-completion token report

Only when the current task actually used the `$smart-router` skill to route
work, or spawned a subagent that logged usage, run the installed Smart Router
`scripts/token_report.py` before the final reply and append its Markdown output
unchanged. Do not generate a token report for an ordinary single-agent task
that did neither. The report contains the current root turn's snapshot for
root and every subagent that logged usage. The snapshot necessarily excludes
the final reply's own model call.

Users can disable this per project with `.codex/smart-router.toml`, or globally
with `~/.codex/smart-router.toml`:

```toml
token_usage_report = false
```

The project setting takes priority. If neither file exists, reporting remains enabled.

If a repository contains its own AGENTS.md, obey the more specific project rules as well.

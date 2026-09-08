# Smart Multi-Agent Routing

For software-engineering work, use the `$smart-router` skill whenever decomposition or model routing can materially improve quality or reduce expensive-model usage.

Routing policy:
- Root/orchestrator: use the model selected for the current Codex conversation.
- Keep trivial/local tasks single-agent.
- Luna: exploration, repository search, reading, research, tests, and low-risk bounded tasks.
- Terra: normal implementation; it is also Root when selected in the conversation model picker.
- Escalate only difficult reasoning/implementation to Sol.
- Sol: difficult debugging, algorithms, concurrency, performance, architecture-sensitive work, and important review.
- Astra: exceptional high-risk deep review only.
- Do not use Astra for routine repository exploration, implementation, testing, summarization, or ordinary review.
- Parallelize independent tasks, normally no more than 2–4 subagents.
- Never spawn every role mechanically.
- Subagents return concise conclusions, file/symbol references, validation results, and risks rather than long transcripts.
- Root owns architecture, scope decisions, integration, conflict resolution, and final acceptance.

## Task-completion token report

By default, before the final reply of a task, run the installed Smart Router
`scripts/token_report.py` and append its Markdown output unchanged. It reports
the current root turn's token snapshot for root and every subagent that has
logged usage. The snapshot necessarily excludes the final reply's own model
call.

Users can disable this per project with `.codex/smart-router.toml`, or globally
with `~/.codex/smart-router.toml`:

```toml
token_usage_report = false
```

The project setting takes priority. If neither file exists, reporting remains enabled.

If a repository contains its own AGENTS.md, obey the more specific project rules as well.

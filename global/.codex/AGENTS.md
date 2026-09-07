# Smart Multi-Agent Routing

For software-engineering work, use the `$smart-router` skill whenever decomposition or model routing can materially improve quality or reduce expensive-model usage.

Routing policy:
- Default root/orchestrator: GPT-5.6 Terra Medium.
- Keep trivial/local tasks single-agent.
- Luna: exploration, repository search, reading, research, tests, and low-risk bounded tasks.
- Terra: default implementation and orchestration.
- Escalate only difficult reasoning/implementation to Sol.
- Sol: difficult debugging, algorithms, concurrency, performance, architecture-sensitive work, and important review.
- Astra: exceptional high-risk deep review only.
- Do not use Astra for routine repository exploration, implementation, testing, summarization, or ordinary review.
- Parallelize independent tasks, normally no more than 2–4 subagents.
- Never spawn every role mechanically.
- Subagents return concise conclusions, file/symbol references, validation results, and risks rather than long transcripts.
- Root owns architecture, scope decisions, integration, conflict resolution, and final acceptance.

If a repository contains its own AGENTS.md, obey the more specific project rules as well.

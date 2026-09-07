# Smart Multi-Agent Routing

For software-engineering work, use the `$smart-router` skill whenever decomposition or model routing can materially improve quality or reduce expensive-model usage.

Routing policy:
- Keep trivial/local tasks single-agent.
- Prefer Luna for repository exploration, focused research, tests, and obvious low-risk edits.
- Prefer Terra for normal implementation.
- Escalate only difficult reasoning/implementation to Sol.
- Use Astra primarily as root/orchestrator; use Astra `deep_reviewer` only for very high-risk work.
- Parallelize independent tasks, normally no more than 2–4 subagents.
- Never spawn every role mechanically.
- Subagents return concise conclusions, file/symbol references, validation results, and risks rather than long transcripts.
- Root owns architecture, scope decisions, integration, conflict resolution, and final acceptance.

If a repository contains its own AGENTS.md, obey the more specific project rules as well.

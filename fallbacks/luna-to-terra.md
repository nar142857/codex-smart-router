# Luna subagent compatibility fallback

If your Codex build can run Luna directly but `spawn_agent` rejects Luna, update Codex first.
If the problem remains, temporarily replace Luna with Terra in:
- explorer.toml
- researcher.toml
- tester.toml
- fast_worker.toml
- config.toml `default_subagent_model`

This costs more allowance than Luna but keeps the architecture functional.

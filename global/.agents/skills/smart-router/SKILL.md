---
name: smart-router
description: Route Codex software-engineering work across Astra, Sol, Terra, and Luna subagents to maximize quality per expensive-model token. Use for implementation, debugging, refactoring, repository analysis, testing, research, review, or other coding work that may benefit from task decomposition. Do not force multi-agent delegation for trivial local edits.
---

# Smart Router

Root/orchestrator: the model selected for the current Codex conversation. The skill never overrides that selection. Optimize for correct results while minimizing Plus-plan allowance consumption.

## Core principle

Use the cheapest capable agent for each bounded task:
- `explorer` (Luna): repository search, call/data-flow mapping, dependency/test discovery.
- `researcher` (Luna): focused docs/API/library research.
- `tester` (Luna): tests, lint, typecheck, build, reproduction and verification.
- `fast_worker` (Luna): tiny, obvious, low-risk implementation following an established pattern.
- `worker` (Terra): default implementation and routine multi-file work.
- `expert` (Sol): hard debugging, algorithms, concurrency, performance, subtle integration, architecture-sensitive changes.
- `reviewer` (Sol): independent review for substantial or risky changes.
- `deep_reviewer` (Astra): only for very high-risk or costly-to-fail changes.

The current conversation Root handles small/local tasks directly; do not start a subagent unless delegation materially improves the result. Astra must not be selected for routine repository exploration, ordinary implementation, ordinary testing, summarization, or standard review; reserve it for exceptional high-risk deep review.

## Step 1 — classify by uncertainty + blast radius

### S — trivial/local
Signs: one obvious file/tiny edit, established pattern, low blast radius, no architecture/schema/public-API/security implications.
Action: the current conversation Root handles directly, or `fast_worker` only if delegation clearly saves context. No mandatory explorer/reviewer.

### M — normal engineering
Signs: bounded feature/bug, a few related files, architecture is clear, moderate contained risk.
Action: use Luna (`explorer`/`researcher`) for unknown locations, call chains, reading, or focused research; implementation defaults to Terra `worker`; use Luna `tester` after meaningful changes; reviewer only when justified.

### L — complex/cross-cutting
Signs: multiple subsystems, unclear root cause, significant refactor/integration, public API/schema/compatibility implications, several independent workstreams.
Action: parallel Luna `explorer`/`researcher` only for independent discovery; the current conversation Root decides architecture; Terra `worker` for normal slices; Sol `expert` only for genuinely hard slices; Luna `tester`; finish with Sol `reviewer` only when the risk warrants it.

### XL — high-risk
Signs: auth/authorization/security boundary, payments/billing, destructive migration, irreversible data operation, concurrency correctness, major public API/architecture change, costly production failure.
Action: the current conversation Root owns architecture; Sol `expert` for difficult implementation; Luna `tester`; Sol `reviewer`; Astra `deep_reviewer` only when an independent high-risk pass is worth the allowance.

## Step 2 — parallelism
Parallelize only independent work. Good: backend discovery + frontend discovery; docs research + repo exploration; workers on non-overlapping files. Avoid two workers editing the same contract/file. Do not spawn roles mechanically. Target 2–4 active subagents by default.

## Step 3 — context economy
Subagents return conclusions, exact paths/symbols, validation, and risks — not transcripts, whole files, repeated prompts, or long logs. Root passes only needed context.

## Step 4 — escalation
Luna -> Terra when implementation stops being obvious or several contracts interact.
Terra -> Sol only when the root cause is subtle, algorithms/concurrency/performance matter, architecture tradeoffs appear, or repeated attempts fail.
Sol -> Astra deep review only for exceptional high blast radius, security/auth/payment correctness, destructive migration, expensive/irreversible failure, or a materially useful independent top-tier judgment.

## Step 5 — integration
Root reconciles outputs, resolves conflicts, checks acceptance criteria, ensures one coherent patch, runs/delegates final validation, and reports residual risks. Never accept subagent output merely because it completed.

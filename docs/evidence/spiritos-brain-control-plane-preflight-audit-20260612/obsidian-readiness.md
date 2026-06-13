# Obsidian Readiness

## What Obsidian Currently Is

In this repo/system, Obsidian is currently a read-only Markdown context source. The default local vault is `data/design-vault` if present. It is useful for design/context notes and can return safe excerpts, but it is not yet the trusted Hippocampus.

## Where It Appears

Code:

- `source_proxy/context/obsidian.py`
- `source_proxy/context/source_readiness.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/self_status.py`
- `source_proxy/decision/prompt_packet.py`
- `source_proxy/tasks/long_running.py`

Tests:

- `source_proxy/tests/test_obsidian_context.py`
- `source_proxy/tests/test_context_source_readiness.py`
- `source_proxy/tests/test_self_status.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`

Vault:

- `data/design-vault/README.md`
- `data/design-vault/token-model-v0.1.md`
- `data/design-vault/packs/internal-dashboard-demo-v4/**`
- `data/design-vault/source-cards/**`

## Real Or Planned Integration

Real integration:

- optional vault discovery
- Markdown note scanning
- include/exclude globs
- simple task-term search
- safe excerpt redaction
- read-only diagnostics
- `/v1/context/obsidian/query`
- context-source readiness packet

Planned or unproven integration:

- authoritative memory
- automatic write-back
- freshness-based ranking
- route/model/worker selection influence
- planner decision influence
- evidence-linked note lifecycle

## Working Now

- Querying selected Markdown notes in a configured vault.
- Excluding `.obsidian/**`, `private/**`, `secrets/**`, and `archive/**` by default.
- Redacting email, token, password, secret, and API-key shaped values in excerpts.
- Reporting read-only authority.
- Testing disabled, missing vault, relevance, excludes, redaction, default local vault, and context packet shape.

## Unproven

- Live deployed Obsidian query with Britton's real long-term vault.
- Quality of retrieval on broad/ambiguous tasks.
- Freshness and duplicate handling.
- Whether selected notes improve outcomes.
- Whether notes are used by Source Proxy route/model/planning decisions.
- Write safety and audit.

## Hippocampus Role

Obsidian can serve as the human-readable long-term memory surface for:

- project memory summaries
- prior failure summaries
- successful prompt patterns
- model performance notes
- route decision rationale
- user workflow preferences
- brain-map specs
- long-term plans

It should not be the sole proof store. Evidence docs and durable run records should remain the authoritative proof trail. A database/vector store can hold fast retrieval indexes, embeddings, and run-level facts. Obsidian should hold curated, reviewable summaries and links.

## What Lives Where

Obsidian:

- curated project memory
- summarized lessons
- user preferences
- architectural concepts
- route/model decision notes
- human-readable long-term plans

Evidence docs:

- raw receipts
- command output
- screenshots
- test logs
- NO-GO evidence
- exact run artifacts

Database/vector store:

- run rows
- embeddings
- search index
- freshness metadata
- exact machine-readable provenance

## Read-Only First

Recommended initial mode: read-only memory first.

SpiritOS should not write to Obsidian automatically yet. Write-back should be approval-gated and previewed as a note diff. Britton should approve the note path, source evidence links, summary, and confidence before the system writes to Obsidian.

## Handling Specific Memory Types

- Project memory: curated per-project notes with evidence links.
- Prior failures: summarize exact failure, cause, fix, and proof; link evidence.
- Successful prompts: store prompt pattern, model/route, constraints, outcome, and caveats.
- Model performance notes: store date, model alias, task class, result, and proof.
- Route decisions: store routing rule, rationale, and counterexamples.
- User workflow preferences: high-confidence, date-stamped, approval-reviewed.
- Brain-map specs: keep architecture intent in Obsidian, implementation proof in evidence docs.
- Long-term plans: store approved plan summaries only; draft packets should stay in evidence/planning docs until approved.

## Risks Of Trusting Too Much

- Stale notes can override current repo truth.
- Duplicated notes can produce conflicting context.
- Human-written notes may contain intent, not proof.
- Sensitive text can leak if write/read boundaries weaken.
- Automatic writes can pollute memory with failed assumptions.
- Retrieval can select plausible but wrong context without citations.

## Minimum Promotion Requirements

- Required frontmatter schema.
- Evidence links required for factual memory.
- Freshness/staleness and deprecation flags.
- Conflict detection across Obsidian/evidence/durable runs/blueprints.
- Approval-gated note writes.
- Read logs or query diagnostics.
- Tests proving note selection, redaction, freshness, and route/planner consumption.
- A rule that repo/test/live evidence beats Obsidian when they conflict.

## Recommended Obsidian v0.1 Role

Use Obsidian as a read-only Hippocampus advisory layer: curated context summaries and long-term memory hints, returned with source paths and confidence labels. Do not allow automatic write-back or authoritative route/planner decisions until the guardrails above exist.

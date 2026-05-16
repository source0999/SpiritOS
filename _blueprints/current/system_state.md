---
blueprint_id: system-state
title: SpiritOS Current Architecture Blueprint
project: SpiritOS
component: system
doc_type: current_state
status: active
source_of_truth: true
owner: Britton
code_paths:
  - scout/**
  - source_proxy/**
  - src/**
  - _blueprints/**
related_blueprints:
  - scout-architecture
  - source-proxy-coding-workflow
  - dashboard-state
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-15
---

# SpiritOS Current Architecture Blueprint

## 1. Current Milestone

Scout v0.1 Read-Only Intelligence + Manual Promotion Gate

SpiritOS now has a working local Scout intelligence loop that can observe configured sources, clean source material, summarize it into intelligence packets, check those packets, display them in the dashboard, manually recheck old verdicts, and manually promote selected packets. This does not touch the coding workflow, proxy memory, or approved workspace write path.

## 2. High-Level System Map

Scout intelligence loop:

```text
Sources
-> Scout Pollers
-> Raw Events
-> Extracted Artifacts
-> Intelligence Packets
-> Debugger Verdicts
-> Dashboard Explorer
-> Manual Queue
-> Manual Approval/Rejection
-> Promoted Scout Packet
```

Coding workflow loop:

```text
User Prompt
-> /coding UI
-> Source Proxy
-> Architect
-> Coder
-> Reviewer
-> Approval Gate
-> Approved Execution
-> Post-Apply Verification
```

These loops are still separate. Scout can observe and prepare intelligence inside its own service. The coding workflow still runs through Source Proxy, planning, review, approval, execution, and verification without Scout context being injected into it.

## 3. Frontend Surfaces

- The Dashboard Scout widget shows Scout health, source trust, source summaries, useful packets, saved packets, the review queue, promoted packets, and source cards.
- The widget is read-only by default. Its only write actions are explicit Scout-only manual actions: Queue, Recheck, Approve, and Reject.
- Next route proxies under `src/app/api/scout/` forward dashboard requests to the Scout API. Current proxies cover overview, promotions, queue promotion, finalize promotion, and recheck.
- The `/coding` UI is separate from Scout. Scout packet state does not currently feed Architect, Coder, Reviewer, or Approval Gate.
- Dashboard telemetry is separate from Scout. System telemetry cards should not be treated as Scout intelligence.

## 4. Scout Service Architecture

Scout is a separate FastAPI service run through the Scout Docker Compose profile. It uses SQLite for structured state and JSONL/filesystem artifacts for raw and extracted source material.

The service starts in `scout/src/scout/main.py`, initializes storage, applies migrations, registers recurring jobs, and serves APIs under `/v1/scout`. APScheduler-style jobs handle source polling, artifact extraction, packet synthesis, debugger processing, and pruning.

Configured sources live in `scout/config/sources.yaml`. Current examples are:

- `anthropics/anthropic-sdk-python` GitHub commits
- `fastapi/fastapi` GitHub commits
- Python blog RSS feed

Topic anchors live in `scout/config/topic_anchors.yaml` and currently include topics such as Python, FastAPI, TypeScript, local LLMs, agents, SQLite, Docker, security, embeddings, and developer tools.

Scout tracks:

- Source tracking with ETags, last-modified values, rate limits, polling timestamps, and failure counts.
- Raw event indexes for unique source events.
- Extracted artifacts that convert raw source material into readable markdown or artifact files.
- Intelligence packets synthesized from extracted artifacts.
- Debugger verdicts from deterministic, structural, and LLM-aware checks.
- Source quality and source trust labels.
- A promotion queue that records human review state inside Scout.

## 5. Scout Data Flow

- `raw_event_index` means Scout noticed a unique source event from a configured source.
- `extracted_artifacts` means source material was converted into a readable artifact, usually markdown or a similar cleaned file.
- `packets` means Scout created an intelligence summary with source URI, tags, summary, impact analysis, confidence, graph relations, and provenance.
- `verdicts` means the Scout debugger reviewed a packet and produced a decision such as surface, store, ignore, or promote.
- `source_quality` means Scout has a basic score for source usefulness and reliability.
- `packet_embeddings` currently exists but semantic memory is inactive because embeddings are not stored.
- `promotion_queue` means human review state inside Scout. It is not proxy memory and it does not make Scout content active coding context.

## 6. Manual Recheck Flow

```text
Packet
-> Recheck endpoint
-> Current bounded debugger logic reruns
-> Verdict/status updates
```

Manual recheck does not refetch source data, does not resummarize the packet, does not promote the packet, and does not write to proxy memory.

The current manual recheck path is bounded for dashboard use. It updates Scout verdict/status with current Scout debugger logic while keeping Tier 3 LLM behavior safe for an explicit manual request.

## 7. Manual Promotion Flow

```text
Packet
-> Queue manually
-> Review Queue
-> Approve or Reject manually
-> Overview count updates
-> Explorer promotion state updates
```

Queueing does not require debugger `decision=promote`. A human can queue useful surfaced packets or saved stored packets for manual review.

Approving a queued item sets it to approved inside Scout and increments the Scout overview promoted count. This count means human-approved inside Scout. It does not mean the packet is active coding memory.

Rejecting a queued item stores a rejection reason and does not increment the promoted count. Rejected packets can be queued again later as a new pending review request, leaving the old rejected row in place for audit.

Approving does not write to proxy memory yet. The promotion queue remains contained inside Scout storage.

## 8. Source Proxy / Coding Workflow

The current coding workflow is still Source Proxy owned:

- The `/coding` frontend sends a user task to Source Proxy.
- Source Proxy handles routing, decision shaping, and task planning.
- Architect prepares the plan and target constraints.
- Coder produces proposed diffs.
- Reviewer checks the proposed work.
- Approval Gate blocks workspace writes until the user approves.
- Approved execution uses the Source Proxy long-running task layer.
- Post-apply verification is part of the safety model and remains the path to a trustworthy done state.

Principle: No Scout integration until coding remains stable and every workflow state is honest.

There are Source Proxy files for Scout research preview and signed Scout intake, but the current confirmed system has not activated Scout as coding context or proxy memory. Those pieces should be treated as dormant or future-facing until Option C or a later approved phase explicitly connects them.

## 9. Safety Boundaries

- Scout packets are untrusted context.
- Scout cannot authorize file writes.
- Scout cannot override user targets.
- Scout cannot bypass Approval Gate.
- Scout cannot write proxy memory automatically.
- Promotion is manual and still contained inside Scout.
- `/coding` must remain safe if Scout is offline.
- Source Proxy is the only place that should handle approved workspace writes.
- Coder cannot edit based only on Scout context.
- Scout context must never become an editable target by itself.
- Approved Scout state is not the same thing as approved code execution.

## 10. Current Known States

- Semantic memory is inactive because packet embeddings are not stored.
- Manual recheck works end to end.
- Manual promotion now works end to end for surfaced or stored packets.
- The Dashboard Scout widget is readable, compact, and polished.
- Promoted packet count can be nonzero, but this still does not mean coding integration.
- Old packet verdict wording may exist from previous debugger versions until those packets are rechecked.
- Scout remains pre-integration.
- No automatic promotion exists.
- No proxy memory integration has been activated.
- No `/coding` integration has been activated.

## 11. Option C Proposal: Read-Only Architect Context Preview

Do not implement this in the current docs step.

Option C should mean Source Proxy can ask Scout for approved/promoted packets, and possibly explicitly allowed surfaced packets, that are relevant to a user task. Architect can preview those packets as optional read-only context before any coding work begins.

The UI should show exactly what Scout context would be included. The user should be able to approve or disable Scout context. CoderPacket should record whether Scout context was used.

Scout context remains read-only. Approval Gate remains unchanged. There are no automatic file writes and no automatic memory injection.

## 12. Option C Acceptance Criteria

- Scout context preview is visibly labeled.
- Only approved/promoted or explicitly allowed surfaced packets are eligible.
- User can disable Scout context.
- Architect explains why each packet was included.
- CoderPacket records Scout context usage.
- Approval Gate remains unchanged.
- No Scout packet can become an editable target.
- No proxy memory write occurs unless a future separate approval path exists.
- Tests prove no pending or ignored packets are included.
- Tests prove coding works when Scout is offline.

## 13. Open Questions Before Option C

- Should Option C use only approved/promoted packets, or allow surfaced packets with a separate toggle?
- Should Scout context be global or per-task?
- Should the user approve context before Architect sees it, or after Architect proposes it?
- Should promoted Scout packets eventually write to proxy memory, or stay only in Scout until a later phase?
- What is the max number of Scout packets allowed in a context preview?

## 14. Next Step

Next step requires explicit permission: begin Option C, Read-Only Architect Context Preview.

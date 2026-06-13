# Recommended Next Implementation Plan

Do not implement in this sweep.

## Step 1: Add Integration Truth Receipt Schema

Goal: add a per-prompt schema that records exact subsystem usage.

Likely files:

- `source_proxy/decision/` new or existing receipt helper
- `source_proxy/api/decision.py`
- `source_proxy/tasks/long_running.py`
- artifact evidence report builder

Evidence:

- unit tests
- one dry prompt receipt
- JSON schema sample

Stop condition: receipt validates and shows skipped integrations explicitly.

Needs approval: yes.

## Step 2: Add Context Needed Decision

Goal: deterministic/router decision for context needs.

Options:

- no extra context
- repo context
- Obsidian
- search/web
- Scout
- Cartographer
- verifier
- Mac worker advisory

Evidence:

- tests for each decision bucket
- negative tests for secrets/private context

Stop condition: router can choose no-context and records skip reasons.

Needs approval: yes.

## Step 3: Wire One Low-Risk Context Source

Recommended first live integration: Obsidian or repo/search depending on desired proof prompt.

Why not Gemma/Hermes first: model sidecars can inflate confidence without improving context unless receipts and deterministic authority are already strong.

Evidence:

- source-specific receipt
- transcript showing bounded context included
- final verdict still browser/deterministic grounded

Stop condition: one proof prompt with actual invocation and no hidden fallback.

Needs approval: yes.

## Step 4: Add Cartographer Advisory Recommendation

Goal: Cartographer recommends context/model/verifier, Source Proxy remains gate.

Evidence:

- Cartographer request/response receipt
- override path test
- no write authority proof

Needs approval: yes.

## Step 5: Add Integrated Level Test

Goal: a new level prompt that cannot pass without live context invocation.

Stop condition: GO/NO-GO based on invocation receipt plus behavior, not route status.

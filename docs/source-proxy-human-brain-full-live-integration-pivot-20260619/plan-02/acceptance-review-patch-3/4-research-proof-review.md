# Research Proof Review

## Evidence Reviewed

Patch 3 evidence file reviewed:

- 6-current-research-regression.md

The review prompt referenced 6-research-regression.md. The committed artifact name is 6-current-research-regression.md.

## Findings

The research proof reports:

- status: INTEGRATED_LIVE
- task: task_8e88f3a54bc2
- provider: http://127.0.0.1:8080
- Scout: skipped/disabled
- SearXNG: used
- source_count: 4
- downstream decision: research_sources_available
- downstream changed: true
- untrusted sources marked: true
- consumer: cartographer_current_research_consumer
- consumer event: consumer_3a8289e42ec6494a

A read-only task trace check during this review confirmed the same consumer event for task_8e88f3a54bc2.

The bad-provider proof reports blocked/searxng_unreachable with only the explicit bad provider candidate and zero sources. This supports the no-silent-fallback requirement.

An optional local curl smoke reached the SearXNG endpoint but returned HTML for that simple request rather than JSON. This was not treated as a blocker because the Patch 3 proof and focused tests exercise the JSON path and explicit-provider no-fallback behavior.

## Research Verdict

PASS for Plan 2 Patch 3 research integration.

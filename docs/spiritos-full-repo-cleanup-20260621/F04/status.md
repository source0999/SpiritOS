# F04 Status

**Stage:** F04 - Generic local packet decomposition
**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Verdict:** INTERNAL_GO_PENDING_SECONDARY_REVIEW
**Depends on:** F03

## Frozen artifacts
- `acceptance-contract.json` - frozen before source edits.
- `holdout-manifest.json` - frozen before source edits.
- Hashes recorded in `status.json`.

## Completed increments
- 4.1 - generic local decomposer, sub-packet validator, and unseen task-shape tests.
- 4.2 - additive prompt-packet wiring when F3 dry-run recommends `LOCAL_DECOMPOSITION_RECOMMENDED`.

## Manual findings
- Decomposition is local-only and does not call providers, subprocesses, or network APIs.
- Supported shapes: multi-node resource planning, current-tool comparison, architecture planning, implementation handoff, and research-backed recommendation.
- Sub-packets serialize evidence requirements, validation focus, and F1 failure classifications.
- F3 formatting/decomposition recommendations can attach `local_decomposition` metadata to prompt packets without removing existing packet fields.
- Production code does not contain named A2/A5/A9/Set A/4R/4R7 labels; those labels remain test-only regression examples.

## Caveat
- The broad `source_proxy/tests` timeout from F1-F3 is carried into F10 and is not counted as PASS here.

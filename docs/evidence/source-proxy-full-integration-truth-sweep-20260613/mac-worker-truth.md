# Mac Worker Truth

## Existing Files

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md`

## Current Capabilities

The worker scripts support job types including:

- `repo_context_search`
- `source_proxy_context_discovery`
- `trial_context_assist`
- `scout_research_packet`
- `browser_design_check`
- `run_safe_check`
- `system_status`

Docs record a Mac Mini support node at `10.0.0.147`, advisory boundaries, and a future SearXNG advisory search packet model.

## Source Proxy Usage

No current Source Proxy artifact prompt path invocation was found. Recent Level 3/4 runs did not use Mac worker.

Status: DORMANT for Source Proxy prompt integration; advisory worker code/docs exist.

## Could It Host Browser/Search/Fetch/Context?

Yes, by design it could host advisory repo context, search packets, browser design checks, and safe status checks. But it must remain output-only until explicit approval and receipts exist.

## Missing Wiring

- Source Proxy endpoint/client to create a Mac advisory job.
- Request/response schema with allowed outputs and forbidden actions.
- Timeout and failure handling.
- Receipt fields proving no repo write, no Scout intake write, no Cart mutation, and no Source Proxy mutation.

## Required Receipts

- `mac_worker_requested`
- `mac_worker_host`
- `job_type`
- `allowed_outputs`
- `forbidden_outputs`
- `provider_used`
- `result_count`
- `used_in_model_prompt`
- `writes_performed: false`
- `errors`

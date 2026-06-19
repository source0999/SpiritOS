# Current Tracked-Source Findings

Authoritative current-source anchors inspected during packet creation:

- `src/app/coding/page.tsx` imports `@/components/coding/CodingCockpitShell` and renders `<CodingCockpitShell />`; this confirms the active `/coding` shell is `src/components/coding/CodingCockpitShell.tsx`.
- `src/app/v1/decisions/route/route.ts` forwards `/v1/decisions/route` to Source Proxy only when `SPIRIT_CODING_USE_PROXY=true`, using `sourceProxyFetch("/v1/decisions/route")` and merging repo-first sources.
- `src/app/v1/actions/execute-approved/route.ts` sends approved diffs to Source Proxy long-running tasks at `/v1/tasks/long-running/{taskId}/execute-approved` with `commit_authority:false` and `push_authority:false`.
- `source_proxy/api/decision.py` registers `/v1/decisions` and imports `central_gate_check`, Obsidian context, Cartographer context, Scout research diagnostics, SearXNG diagnostics, model lanes, and repair/verifier machinery.
- `source_proxy/api/long_running_tasks.py` registers `/v1/tasks/long-running`, plan, stream, verify, reject-plan, and execute-approved task routes.
- `source_proxy/approval/external_gate.py` defines `central_gate_check(action, increment_id, run_id)` with gate states and allowed actions, but it is not yet a complete structured policy decision layer.
- `source_proxy/context/obsidian.py` implements read-only Obsidian/local vault retrieval; diagnostics explicitly report `obsidian_read_only: True`.
- `source_proxy/decision/scout_research.py` contains a dedicated Scout research diagnostics path gated by `SOURCE_PROXY_SCOUT_RESEARCH_ENABLED`; it is evidence-only and `can_apply:false`.
- `src/app/v1/coding/research-preview/route.ts` is preview/advisory-only and may return a local roadmap fallback when no research sources are supplied.
- `src/app/v1/coding/cartographer/preview/route.ts` is explicitly control-preview-only and rejects activation, queue worker start, approval token consumption, and live map mutation.
- `src/app/v1/coding/mac-advisory/route.ts` is explicitly `advisory_only:true`, `preview_only:true`, and has no Mac repo write authority.
- `src/app/api/coding/mac-worker/route.ts`, `src/lib/mac-worker/types.ts`, `src/lib/mac-worker/client.ts`, and `scripts/mac-worker/spirit_mac_worker.py` define a real Mac worker contract with job types including `scout_research_packet`, `browser_design_check`, `run_safe_check`, and `system_status`; current integration must prove whether canonical `/coding` consumes it.
- `source_proxy/cartographer/workflow_state.py`, `workflow_runner.py`, and `workflow_event_ledger.py` provide existing workflow/checkpoint/event machinery that Plan 0 must evaluate before any new orchestrator is proposed.
- `source_proxy/decision/model_lanes.py`, `source_proxy/routing/ollama_route.py`, `source_proxy/routing/litellm_router.py`, and `source_proxy/agents/registry.py` are the current model/specialist discovery anchors. Gemma, Hermes, and Qwen must be confirmed through these files and runtime status, not old packets.
- `source_proxy/decision/artifact_repair_loop.py`, `artifact_repair_contract.py`, `verifier_lane.py`, and related tests are current repair/verifier anchors.
- `backend/docker-compose.yml` declares a `spirit-searxng` service; `source_proxy/decision/research.py` and `src/app/api/research/web-search/route.ts` are current SearXNG/research anchors.

Resolved contradictions:

- Active `/coding` is not a dormant design demo route: it currently renders `CodingCockpitShell`.
- Scout does have a dedicated current research diagnostics module; older claims of only generic local-file fallback are historical unless Plan 0 source inspection proves dispatch still falls through for a specific job class.
- Mac has a real worker route and typed contract, but the user-facing `/v1/coding/mac-advisory` route remains advisory-only; real integration is unproven until canonical-route invocation and downstream consumption appear in one trace.
- Obsidian is read-only in current source; future writeback requires explicit Britton approval and implementation.
- Cartographer has substantial machinery, but `/v1/coding/cartographer/preview` is deliberately preview-only; Plan 0 must distinguish reusable machinery from dormant preview surfaces.

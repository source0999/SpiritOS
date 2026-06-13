# Live Path Map

Scope: current Product/artifact Source Proxy prompt path, based on code inspection and Level 3/4 evidence.

| Step | Source files | Runs today | Proof field / evidence | Receives | Emits | External subsystem |
| --- | --- | --- | --- | --- | --- | --- |
| API app registration | `source_proxy/main.py` | YES | app includes decision, cartographer, context, scout intake routers | HTTP request | FastAPI route | none |
| Prompt endpoint | `source_proxy/api/decision.py` | YES | `/v1/decisions/prompt-packet` | task, trial flags, allowed/forbidden files | route payload, coder packet, diagnostics | optional local model path |
| Task spec intake | `source_proxy/decision/task_spec_intake.py`, `source_proxy/api/decision.py` | YES | `task_spec_intake` in prompt-packet response | user task, workspace root | legacy task spec / intake | filesystem inspection |
| Route decision | `source_proxy/decision/router.py` | YES | `route_decision`, `reason_codes`, `recommended_route` | task and flags | route classification | repo-first research only if requested/needed |
| Product/artifact resolver | `source_proxy/decision/human_messy_homepage.py`, `source_proxy/decision/artifact_behavior_contract.py`, evidence runner scripts | YES for artifact batches | receipts show `route_type: product`, `task_shape: disposable_small_file_bundle` | messy artifact prompt | artifact contract, workspace decision | none |
| Disposable/real-repo decision | artifact runner and receipts | YES for Level 3/4 artifacts | receipt `workspace_mode: disposable_workspace` | task shape | workspace root | local filesystem |
| Context packet assembly | `source_proxy/tasks/long_running.py`, `source_proxy/planning/plan.py` | YES for repo coder path; narrow for artifact runner | `context_packet_summary`, `coder_packet`; artifact receipts mostly behavior contract data | task spec, target, repo slices | context slices, summary | Obsidian diagnostics only, not injected |
| Model lane selection | `source_proxy/decision/model_lanes.py`, `source_proxy/tasks/long_running.py` | YES for Qwen/coder alias; preview for sidecars | Level 3/4 `model_id: qwen2.5-coder:7b`, `selected_coder_lane: qwen_local_coder` | model alias config | provider/model truth | Ollama/LiteLLM router |
| Qwen invocation | `source_proxy/tasks/long_running.py`, artifact runner | YES in recent levels | `model_call_count: 1`, `raw_model_transcripts`, `active_model: qwen2.5-coder:7b` | coder prompt | file/action blocks | Ollama local model |
| Action/file-block parsing | `source_proxy/decision/tool_actions.py`, `source_proxy/decision/tool_action_loop.py`, artifact receipts | YES | `parsed_action_count`, `actions_file_blocks_parsed`, `files_applied` | model output | structured write actions | none |
| Workspace write | `source_proxy/decision/tool_action_executor.py`, artifact receipts | YES in disposable roots | receipt `WriteFile`, `workspace_root`, `files_touched` | parsed actions | files in workspace | local filesystem |
| Preview selection | `source_proxy/decision/artifact_preview_resolution.py`, evidence reports | YES | `selected_preview_path`, preview links | workspace files | preview HTML path | browser/open path |
| Browser behavior probe | evidence probe scripts, `artifact_behavior_contract.py` | YES | Level 3/4 browser behavior JSON | preview path, contract | PASS/FAIL observations | local browser automation |
| Repair loop | `source_proxy/decision/artifact_repair_loop.py`, evidence repair summaries | YES for failed artifacts | `repair_status`, `verification_repairs_used`, repair summaries | failure packet and artifact | repaired workspace content | Qwen/local model when attempted |
| Final verdict | `source_proxy/decision/artifact_final_verdict.py`, evidence report builders | YES | `final_verdict`, `overall_verdict`, `report_verdict_mismatch` | behavior result, repair result | strict PASS/FAIL/GO/NO-GO | none |
| Evidence/receipt | artifact runner, receipts, score JSON | YES | `receipt.json`, `score.json`, `route_trace.json`, HTML reports | all run artifacts | evidence folder | local filesystem |
| Mini context pack | evidence folders | YES | `mini-context-pack.md/json/xml` | final evidence | uploadable summary | none |

Key missing live calls in this path: Gemma, Hermes verifier, Cartographer ownership, Obsidian selected notes, Scout/SearXNG/xersearch, Mac worker, Continue/Cursor.

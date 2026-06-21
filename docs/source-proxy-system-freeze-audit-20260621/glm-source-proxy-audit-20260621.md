# GLM Independent Source Proxy Freeze + Audit — 2026-06-21

**Reviewer:** GLM (independent). **Mode:** freeze + read-only audit. **No source mutation, no cleanup, no stage/commit/push.**
**HEAD:** `927055e4` · **Branch:** `master` · **Host:** Spirit (Dell/source-server) · **Repo:** `Z:\` (= `~/SpiritOS`)
**Scope:** Source Proxy / coding lane / Mac worker / research / model lanes / traces / debugging / anti-cheat.
**Companion files:** `glm-source-proxy-freeze-20260621.xml` (AI context), `glm-mobile-download-index.md`, `glm-checksums.sha256`, `glm-freeze-metadata.json`.

> Read this first on Fold 7. Then compare with Codex's view before approving any cleanup. Do **not** approve implementation from this audit alone.

---

## 1. GLM Independent Executive Verdict

**Overall: PARTIALLY_HEALTHY · STRUCTURALLY_STRAINED · ANTI-CHEAT_STRONG · BRAIN-SWITCH_INCOMPLETE.**

- The intended workflow (`messy prompt → route/spec/context → lanes → packet → validator/grader → trace+receipt+consumer → honest verdict`) is **real and wired**, not aspirational. Plan 3 durable execution, FIP0–FIP6 receipts, causal traces, and the 4R hardened grader all exist and run.
- **Anti-cheat is the strongest part.** The old generator-cheated Set A was honestly disqualified; the 4R2 grader, `fake_go_detected`, fabricaton/garble detectors, and "renderer only renders validated fields" rules are in force and self-tested. A2/A5/A9 failed **honestly** (local model could not produce valid structured packets) — that is the system working, not cheating.
- **The biggest weakness is concentration + taxonomy, not trust.** `source_proxy/api/decision.py` is a **7,971-line FIP0–FIP6 megafile** mixing receipts, research, qwen/ollama, hermes verifier, browser + functional verifiers, traces, and route handlers. The three React shells total **37,956 lines**. There is **no centralized failure taxonomy**: `LOCAL_MODEL_INSUFFICIENT`, `MODEL_FORMATTING_FAILURE`, `API_ESCALATION_RECOMMENDED`, `MODEL_CAPABILITY_LIMIT` are **not implemented as distinct reason codes** — only `local_model_unavailable` (env/connection) exists. This blurs exactly the brain-switch question the audit was asked to answer.
- **Blueprint/Cartographer alignment is good on paper and mostly held in code.** Central gate is fail-closed; advisory routes don't mutate; apply requires approval. The drift risk is that several decision.py side-paths call subprocess/urllib directly instead of going through lanes, which creates a parallel execution surface outside Cartographer's view.

**If Britton does one thing next:** freeze here (C0, this audit), then unify the failure taxonomy and split `decision.py` before any new feature work. Details in §14.

---

## 2. Current Source Proxy System Map

```
Messy human prompt (src/app/coding, CodingCommandCenterShell.tsx 10,050 lines)
   │  Next proxy (src/app/v1/**)
   ▼
FastAPI Source Proxy (source_proxy/main.py → 18 routers)
   ├── /v1/decisions/route        advisory route decision + FIP0–FIP6 enrichment (decision.py 7,971 lines)
   ├── /v1/tasks/long-running/*   durable execution + apply path (durable_execution.py, long_running.py)
   ├── /v1/actions/execute-approved  ← only decision-bearing apply (central_gate_check fail-closed)
   ├── /v1/coding/**              mac-advisory, research-preview, runs, self-tests, agent-lab…
   ├── cartographer, chat, codex_adapter, context, diff_verification, healthcheck, scout_intake, tools_manifest, workspace_tools
   ▼
Decision lanes (source_proxy/decision/*.py, 32 modules)
   route_decision → task_spec → context(Obsidian/Cartographer/design) → current_research(SearXNG/Scout)
   → mac_worker → model_lanes(qwen/hermes/gemma/cloud_future) → verifier → repair → recovery → receipt
   ▼
Durable task engine (tasks/durable_execution.py: PLAN3 status enum + transition table + terminal states)
   ▼
Evidence: FIP0 receipt JSON (/home/source/spiritos-evidence/...) + causal trace events + consumer_event_id
   ▼
Hardened grader (4R2) → final_status PASS | NEEDS_FIX | FAIL | BLOCKED_ENV | BLOCKED_HUMAN + fake_go_detected
```

Two parallel UI shells exist: `CodingCommandCenterShell.tsx` (active per `/coding` page) and the older/larger `CodingAgentInterface.tsx` (14,966 lines) + `CodingCockpitShell.tsx` (12,940 lines). See §6.

---

## 3. Main Entry Points

| Entry | Path | Role | Mutates state? |
|---|---|---|---|
| Visual `/coding` | `src/app/coding/page.tsx` → `CodingCommandCenterShell.tsx` | Human prompt surface | No (client) |
| Next proxy `/v1/decisions/route` | `src/app/v1/decisions/route.ts` → `decision.py` | Advisory route + FIP enrichment | No (advisory) |
| Apply path | `src/app/v1/actions/execute-approved/route.ts` → `long_running.execute_approved_long_running_task` | **Only** workspace apply | Yes, after `central_gate_check("apply",…)` |
| FastAPI root | `source_proxy/main.py` | Wires 18 routers, declares write policy | Boot only |
| Durable engine | `tasks/durable_execution.create_plan3_durable_task` + `apply_plan3_policy` | Plan 3 state machine | Yes (task state, gated) |
| Long-running | `tasks/long_running.py` | Task lifecycle, causal trace, apply | Yes (gated) |
| Operator gate | `scripts/gate-{status,approve,start,complete,block}` + `approval/external_gate.central_gate_check` | Human approval | Yes (approval ledger) |

---

## 4. Subsystem Ownership Table

| Subsystem | Canonical files | Entry | Inputs | Outputs | State mutated | Trace fields | Tests | Risk |
|---|---|---|---|---|---|---|---|---|
| Route/intent | `decision/router.py`, `decision/task_spec_intake.py`, `safety/paths.py` | `decide_route` | task text | `RecommendedRoute`, risk tier | none | route_type | yes | low |
| Context lane | `decision/current_research.py`, `context/obsidian.py`, `context/inventory.py` | `_build_fip1_context_lane_packet` | task, repo | context packet | none | obsidian/cartographer status | yes | med (read-only OK) |
| Research lane | `decision/research.py`, `decision/scout_research.py` | `run_local_research_preview` | query | sources | none | search_needed, source_count | partial | med (live network) |
| Mac worker | `decision/mac_integration.py`, `src/lib/mac-worker/*`, `scripts/mac-worker/*` | `run_mac_worker_for_task` | task | advisory result | none | mac_status | partial | med (not always invoked) |
| Model lanes | `decision/model_lanes.py`, `routing/litellm_router.py`, `routing/ollama_route.py` | `model_lane_registry` | task | lane metadata | none | lane_id, provider, model | yes | **high — see §7** |
| Verifier | `verification/{contracts,deterministic,diff}.py`, `decision/verifier_lane.py`, `_fip5_*_verifier` in decision.py | `_fip5_deterministic_verifier` | changed files | verdict | none | verdict, attempts | yes | med |
| Repair/recovery | `decision/artifact_repair_loop.py`, `tasks/long_running.record_post_apply_verification` | artifact repair | failed verify | retest result | task state | repair result | yes | med |
| Durable engine | `tasks/durable_execution.py` | `create_plan3_durable_task` | task spec | status transitions | **task DB** | status, transition | yes | low (well-bounded) |
| Long-running apply | `tasks/long_running.py` | `execute_approved_long_running_task` | approved diff | applied tree | **workspace + causal trace** | task_id, trace_id, run_id, consumer_event_id | yes | high (write path) |
| Cartographer | `cartographer/service.py` + ~80 modules | `build_cartographer_*` | repo state | ownership map, proposals | none (preview/gate) | many | yes | low (advisory) |
| Trace/receipt | `_fip0_receipt_*`, `_fip6_operator_trace_*`, `_append_causal_event` in long_running.py | FIP0 receipt dir | run | receipt JSON | evidence dir | full FIP6 trace | partial | **med — taxonomy gap, §5/§7** |
| Grader | `_stage4r_runner.py` (Set A), `decision/artifact_final_verdict.py` | `grade` | work+evidence | final_status, fake_go_detected | none | final_status, gates | yes | low (strong) |

---

## 5. File Structure / Code Quality Audit

### What is good
- **Clear package split:** `source_proxy/{api,decision,tasks,cartographer,routing,verification,approval,safety,context,planning,sandbox,agent_factory,agents,diagnostics,budget,expenditure,vector,proxy_memory,codex,testing,tests}`. Intent is readable.
- **Durable engine is textbook-clean:** explicit `PLAN3_STATUSES` enum, `PLAN3_TRANSITIONS` table, `PLAN3_TERMINAL_STATUSES`, and a `fake_go_detected` gate that blocks GO. This is the model the rest should follow.
- **Fail-closed apply:** `central_gate_check` on the only write path; advisory routes verified non-mutating (matches Codex plan-00 review).
- **Subprocess calls have timeouts** (`timeout=5/10/+3s`), `subprocess.TimeoutExpired` is caught and classified. Network calls use `urllib.urlopen(..., timeout=…)`.
- **Anti-cheat comments explain intent** (e.g., `# fake_go_detected computed`, `# renderer does not invent recommendations`).

### What is risky (no change made — audit only)

| Pattern | Where | Why risky |
|---|---|---|
| **Megafile** | `api/decision.py` 7,971 lines mixes FIP0 receipts + FIP1 context + FIP2 research + FIP4 qwen + FIP5 browser/functional verifiers + FIP6 trace + route handlers | One change can break 6 lanes; untestable in isolation; parallel truth sources for "what ran" |
| **UI megafiles** | `CodingAgentInterface.tsx` 14,966 · `CodingCockpitShell.tsx` 12,940 · `CodingCommandCenterShell.tsx` 10,050 | Three overlapping shells; type defs, storage keys, business rules, render all in one file |
| **Cartographer level sprawl** | `cartographer/service.py` 5,769 lines, ~80 submodules, `build_cartographer_level_6…14…` dozens of builders | Level numbering is implicit versioning; hard to know which level is "current" |
| **Domain logic in API file** | FIP4/FIP5 verifier harnesses, qwen call loop, browser probe live **inside `api/decision.py`** | Violates API-transport-vs-domain split; can't reuse from CLI/tests without importing the router |
| **26 `except Exception` in decision.py** (8 in long_running.py, 0 in cartographer service.py) | lines 288, 364, 368, 372, 580, 1055, 1906, 1955, …, 7659 | Most record the error, but several are bare `except Exception: pass` (e.g. 7020/7023/7313 plan-save and packet-payload soft paths) → silent fail-soft that can mask a real lane failure |
| **Hardcoded local debug log path** | `_DEBUG_LOG_PATH = "/home/source/SpiritOS/.cursor/debug-9460b9.log"` at top of `decision.py` | Session-specific debug sink baked into prod module; writes silently swallowed on OSError |
| **Dict blobs** | FIP0/FIP1/FIP2/FIP4/FIP5 packets are `dict[str, Any]` with field conventions, not Pydantic models | Stable schemas exist in docs (`canonical-state-and-event-contract.md`, `mvi-contract.json`) but not enforced in code |
| **Parallel execution surface** | `decision.py` calls `subprocess.run`/`urllib.urlopen` directly for browser probe, ollama tags, qwen call, playwright check | Bypasses lane routing; Cartographer can't see these as "lanes invoked" |

### Commenting standard observed
- **Good:** durable_execution.py status/transition tables are documented; anti-cheat invariants are commented with *why*; FIP6 trace fields explained.
- **Bad:** `decision.py` re-states syntax in places; the `_DEBUG_LOG_PATH` magic string is uncommented; FIP0–FIP6 numbering is never explained in one place (must be inferred from `_fip0_receipt_root` … `_fip6_operator_trace`).
- **Public boundaries lack docstrings** on most `_*` helpers; complex contracts (e.g., `validate_decision_packet`) are documented in the Set A runner, not at the function.

---

## 6. Large-File / Responsibility Concentration Audit

| File | Lines | Responsibilities mixed | Why risky | Safe split boundary | Tests needed before refactor | Risk of touching |
|---|---|---|---|---|---|---|
| `src/components/coding/CodingAgentInterface.tsx` | 14,966 | types + storage + history + decision memory + workflow memory + verification rollup + telemetry + render | Largest file in repo; likely legacy shell | types→`*.ts`, storage→hook, render→subcomponents | existing cockpit/command-center tests must stay green; need isolated test for this shell | **high** (unclear if still active) |
| `src/components/coding/CodingCockpitShell.tsx` | 12,940 | shell + state + render | Was active per plan-00; large | same as above | coding-cockpit-shell.test.tsx exists | high |
| `source_proxy/api/decision.py` | 7,971 | **6 lanes (FIP0–FIP6) + 2 verifiers + qwen loop + receipts + traces + route handlers** | The core concentration risk | split by FIP lane: `lanes/{context,research,coder,verifier,trace}.py`; keep `api/decision.py` as router only | test_prompt_packet_context_metadata (3,648), test_coder_agent_repomix_diff (1,645), test_proxy_runner (2,067) | **very high** — touch last |
| `source_proxy/cartographer/service.py` | 5,769 | level_6…level_14 builders + v1 closeout dashboards | Implicit version sprawl | one module per level group; promote "current level" to a constant | test_cartographer_api (12,207) | high |
| `src/components/coding/CodingCommandCenterShell.tsx` | 10,050 | active shell + state + render | Active `/coding` surface | split as above | coding-command-center-shell.test.tsx (4,963) exists | high |
| `source_proxy/tasks/long_running.py` | 6,513 | task lifecycle + apply + git apply + next-router detection + causal trace + post-apply verify + coding-frontend regression trigger | Mixes engine with detection heuristics | `apply/` (git apply, next-router), `trace/` (causal events), `regression/` (frontend gate) | test_long_running_tasks (1,945), test_diff_verification (1,123) | high |
| `source_proxy/testing/runner.py` | 4,078 | self-test runner | OK-to-large if single-purpose | minor | exists | med |

**Safe order:** start with the *non-active* UI shells and durable-engine-adjacent code; **do `decision.py` last** and only after C1 taxonomy + C7 packet decomposition land, because every split needs the new reason codes to be useful.

---

## 7. Debugging and Observability Audit

### Can a debugger follow a run end-to-end? Mostly yes — for what is recorded.

Per-run identity is strong on the apply path:

| Field | Present? | Where |
|---|---|---|
| `task_id` | ✅ | long_running, durable, FIP0 receipt |
| `trace_id` (`trace_<hex>`) | ✅ | `_ensure_causal_trace_id`, causal events |
| `run_id` | ✅ | FIP0 receipt, central_gate_check |
| `event_id` / `parent event` | ✅ | `_new_causal_event_id`, causal events list |
| `consumer_event_id` | ✅ | `_record_long_running_status_observer_consumer`, plan3 consumer evidence |
| `subsystem` / `lane` | ✅ | `integrations[normalized_subsystem]`, lane status |
| `provider` / `model` | ✅ | model_lanes registry, ollama route, qwen attempt summary |
| `attempt number` | ✅ | `_fip4_qwen_max_attempts`, 4R7 lane attempts |
| `timeout` | ✅ | classified via `subprocess.TimeoutExpired`, `asyncio.wait_for` |
| `policy decision` | ✅ | central_gate_check, PLAN3 transitions |
| `verification result` | ✅ | `_fip5_*_verifier`, post-apply verify |
| `repair result` | ✅ | artifact_repair_loop, record_post_apply_verification |
| `final status` | ✅ | grader `final_status` |
| `raw evidence path` | ✅ | `/home/source/spiritos-evidence/...`, RAW constant in runner |

FIP6 operator trace (`_fip6_operator_trace_from_receipt`) projects a sanitized, operator-readable view with run_metadata + context_trace + search_trace + coder/verifier traces. **This is genuinely good observability for an operator.**

### Failure taxonomy support — the real gap

The audit asked to classify 17 failure modes. GLM verdict per mode:

| Failure mode | Status | Evidence |
|---|---|---|
| TECHNICAL_FAILURE | **PARTIAL** | Caught as `except Exception` → recorded; not a distinct code |
| ENVIRONMENT_FAILURE | **PARTIAL** | `blocked_env` PLAN3 status exists; not propagated as reason code on FIP lanes |
| SERVICE_UNAVAILABLE | **PARTIAL** | healthcheck returns 503; not classified inside decision flow |
| BRIDGE_INTEGRATION_FAILURE | **MISSING** | no distinct code for next-mcp-ws / mac-worker bridge failures |
| ROUTING_FAILURE | **PARTIAL** | `route_type` recorded; failure-of-route not a code |
| TOOL_FAILURE | **MISSING** | tool_action_executor failures not distinct from model failures |
| MODEL_CAPABILITY_LIMIT | **MISSING** | **no code** — the A2/A5/A9 root cause is exactly this and it is unclassified |
| MODEL_FORMATTING_FAILURE | **PARTIAL** | 4R7 records `parse_error`/`validation` per lane attempt, but not surfaced as a stable reason code on the receipt |
| LOCAL_MODEL_INSUFFICIENT | **MISSING** | only `local_model_unavailable` exists (connection/env), not "model reachable but output insufficient" |
| API_ESCALATION_RECOMMENDED | **MISSING** | 4R7 *does* escalate lanes and records attempts, but no `*_recommended` verdict is emitted for the operator |
| POLICY_BLOCKED | **SUPPORTED** | `policy_blocked` PLAN3 status, central_gate_check |
| HUMAN_APPROVAL_REQUIRED | **SUPPORTED** | `blocked_human`, approval gate, gate scripts |
| EVIDENCE_MISSING | **PARTIAL** | `fake_go_detected`, missing-field lists in FIP6; not a unified code |
| VALIDATOR_FAILURE | **PARTIAL** | grader records `failed_gates`; not separated from model failure |
| PROMPT_AMBIGUITY | **MISSING** | no detection of ambiguous prompts |
| RESOURCE_PRESSURE | **MISSING** | budget/manager.py + expenditure/logger.py exist but not wired to a pressure reason code |
| UNKNOWN_NEEDS_INVESTIGATION | **PARTIAL** | bare `except Exception` effectively serves this role silently |

**Summary: 4 SUPPORTED/PARTIAL on the policy/human side, 0 distinct codes for the model-capability/escalation side.** This is the single most important observability gap and it directly weakens the brain-switch story (§9, §11).

### Can it answer the four hard questions?

- **Why did the system fail?** Yes, if you read the FIP0 receipt + causal trace by hand. Not yes via a single `reason_code`.
- **Was local AI insufficient?** **Not as a first-class signal.** You must infer it from "lane attempted, parse_error, validation invalid, no API key set." That inference is correct for A2/A5/A9 but is not encoded.
- **Is API escalation justified?** **Not emitted.** 4R7 escalates silently and falls back; the operator sees `NEEDS_FIX` + "live decision packet did not validate," not `API_ESCALATION_RECOMMENDED`.
- **Bridge/tool vs model reasoning failure?** **Not distinguishable.** `local_model_unavailable` covers env/connection; nothing covers "model answered but badly."

---

## 8. Anti-Cheat / False-Positive Audit

This is the area where the repo is strongest and most honestly documented.

| Risk | Status | Evidence |
|---|---|---|
| default PASS | **PROTECTED** | grader derives status; PASS requires all gates clear |
| `fake_go=false` hardcoded | **PROTECTED** | `fake_go_detected` is *computed* (`status=="PASS" and (failed or blocked)`), not a constant; selftest enforces `not fake_go_detected` for PASS (runner line ~1753) |
| canned work products | **PROTECTED** | deterministic renderer runs **only after** packet validation; invalid packet → safe `NEEDS_FIX` fallback text (runner line 2461), never a fake plan |
| static sources as live search | **PROTECTED** | old `_generate_set_a_records.py` with hardcoded SOURCES/PLANS explicitly **disqualified** (`1-prior-generator-disqualified.md`); rerun uses `run_current_research_for_task` |
| route-exists = integration | **PROTECTED** | plan-00 Codex review confirmed advisory vs apply distinction; central_gate_check is the only apply |
| status ping = task proof | **PROTECTED** | behavior verifiers (browser/functional) required when `behavior_required`; open_status PASS alone does not GO if behavior verdict missing (`artifact_final_verdict.py:136`) |
| local repo context = internet | **PROTECTED** | `repo_context_used` is a recorded gate; `research_materially_changed_output` is checked |
| consumer event on canned output | **PROTECTED** | consumer_event_id attached to real lane outputs; invalid-packet path does not synthesize consumer success |
| mock/fixture as live | **PROTECTED** | fixtures marked; `_generate_set_a_records.py` segregated to `set-a/` as failed-fixtures-only |
| advisory/preview as executed | **PROTECTED** | preview endpoints set `file_writes_allowed` for local_route only; apply is a separate approval step (main.py comment) |
| fallback counted as success | **PROTECTED** | headroom/repomix fallback is explicitly "fallback" in verify script; grader does not count fallback as PASS |
| summary contradicting raw | **PARTIAL** | summary is generated from `final_status`; A2/A5/A9 summary notes list real failed gates — consistent |
| validator = code being graded, no independent review | **PARTIAL** | grader/validator/renderer are separate functions in the same runner file; **independence is by function boundary + selftest, not by process**. The 4R7 selftest (`packet_lane_escalation_records_raw_attempts_without_secrets`, `validator_rejects_fabricated_source_url`, etc.) mitigates but is co-located |
| manual JSON flipping | **PROTECTED** | `_generate_set_a_records.py` removed from acceptance; records validated structurally (`validate()`, `validate_stage_acceptance()`) |
| renderer supplying substance | **PROTECTED** | selftest `renderer_does_not_invent_missing_limit_fields` + `renderer_only_renders_validated_packet_fields`; `renderer_supplied_substance: False` recorded |

### Set A lessons (GLM read-back, not re-acceptance)
- **Old Set A:** disqualified — generator/canned evidence with hardcoded SOURCES/PLANS and stamped PASS. ✅ correctly retired.
- **4R real rerun:** uses live research + repo context + mac worker + live model. ✅
- **4R2 hardened grader:** `fake_go_detected`, materiality, prompt-specific gates. ✅
- **4R3/4R4 structured packet:** validator + renderer aligned; renderer formats only validated fields. ✅
- **4R6/4R7 local-model structured-packet failures:** A2/A5/A9 fail because hermes4/gemma could not emit a valid packet; lane escalation attempted; **no API key set** so escalation exhausted locally. ✅ honest.
- **brain-switch/API escalation:** 4R7 *records* lane attempts and unavailable lanes (OPENAI/ANTHROPIC/DEEPSEEK/LITELLM all unset), but **does not emit** `API_ESCALATION_RECOMMENDED`. This is the open thread.

**GLM does NOT claim Set A is accepted.** Stage 4R verdict is `NEEDS_FIX` (7/10 PASS, A2/A5/A9 NEEDS_FIX, 0 blocked). Stage 5 is not approved.

---

## 9. Model Lane / Brain-Switch Audit

### What exists
- `decision/model_lanes.py`: registry of `qwen_local_coder` (primary), `hermes_sidecar_verifier_preview`, `gemma_sidecar_context_preview`, `manual_handoff`, `cloud_future`. Global rules: qwen is primary; sidecars can't edit or declare success; cloud requires Britton approval. ✅ well-thought-out.
- `routing/ollama_route.py`: `local_model_unavailable_from_error` correctly maps connection/refused/model-missing to a reason code.
- 4R7 runner: explicit lane escalation order (`PLAN3_STAGE4R_PACKET_MODEL` → hermes4 → default → preconfigured API lanes if keys exist); records prompt/response hashes, parse status, validation status, validation errors per attempt without secrets. ✅ the *mechanism* is sound.

### What is missing — the brain-switch gap

The system can decide/env:
- ✅ local model unreachable → `local_model_unavailable`
- ❌ local model reached but **formatting** failed (JSON parse) → recorded as `parse_error` per attempt, **not** a stable receipt-level reason code
- ❌ local model reached but **reasoning** insufficient → **no detection at all**
- ❌ local model reached but **structured packet** invalid → recorded as `validation invalid` per attempt, **not** a stable reason code
- ✅ search provider failed → recorded in research packet
- ✅ Mac worker failed → `mac_status` recorded
- ❌ **API escalation justified** → **not emitted**. 4R7 silently exhausts lanes and falls back to the canned `NEEDS_FIX` renderer.

### A2 / A5 / A9 — GLM read-back

| | A2 (browser ext → proxy task) | A5 (local AI workstation plan) | A9 (current local LLM tools) |
|---|---|---|---|
| Stronger packet-gen considered? | Yes — 4R4→4R7 added structured packet + lane escalation | Yes | Yes |
| Trigger appropriate? | **Yes.** Local model produced no valid packet after bounded attempts; escalation to next local lane (hermes4) then API was the right call. | **Borderline.** A5 is a planning/research task; with better decomposition it should be local-capable. | **Borderline.** A9 is a comparison task; should be local-capable with decomposition. |
| Should local have been enough? | Probably not alone — MV3/native-messaging constraints need precise structured facts. | **Yes, likely** — decompose into role-split / cost / privacy / tooling sub-prompts. | **Yes, likely** — decompose into per-tool sub-queries. |
| Decomposition that would help | split safe-MVP slice, payload boundary, native-host registration into separate packet fields | split Dell/Mac/Windows roles, cost, privacy, model-tooling into separate packets | split per-tool comparison + current-limitations + proxy-setup into separate packets |
| Provider/env missing | OPENAI/ANTHROPIC/DEEPSEEK/LITELLM keys all unset | same | same |
| Prevent API overuse | lane order + "API only if creds exist" + Britton approval rule | same | same |

**GLM stance (evaluated, not blindly accepted):**
- **A2 escalation: reasonable.** This is the case where a stronger model genuinely helps with structured technical constraints.
- **A5/A9: should be local-capable after decomposition.** Escalating them to API by default would be overuse. The right fix is C7 (packet decomposition) + C8 (escalation contract), not a standing API lane.
- **The system currently cannot *say* this.** Because there is no `LOCAL_MODEL_INSUFFICIENT` / `API_ESCALATION_RECOMMENDED` code, the operator sees a flat `NEEDS_FIX` and must manually infer the brain-switch recommendation. That is the gap to close.

---

## 10. Blueprint / Cartographer Workflow Alignment

| Principle | Held? | Notes |
|---|---|---|
| Blueprint defines intent/boundaries | ✅ | `_blueprints/{current,components,runbooks,history,sandbox,proposals,_schema}` with frontmatter + write_policy; `current/system_state.md` is canonical |
| Cartographer maps ownership | ✅ | `cartographer/service.py` + level_6 component ownership, level_9 worker registry, level_10 health timeline |
| Source Proxy runs canonical paths | ✅ | apply only via execute-approved + central_gate_check |
| Receipts prove invocation + downstream consumption | ✅ | FIP0 receipt + causal trace + `consumer_event_id` + plan3 consumer evidence |
| Verifier/grader checks work | ✅ | FIP5 verifiers + 4R2 grader + `fake_go_detected` |
| Human approves high-risk transitions | ✅ | gate scripts, `blocked_human`, approval_id validated |
| No casual parallel implementation path | ⚠️ **PARTIAL** | `decision.py` calls subprocess/urllib directly for browser probe, ollama tags, qwen loop — these are *lanes* in behavior but not *lanes* in Cartographer's view. Not a second engine, but a seam that bypasses ownership mapping. |

**Flag:** the `_DEBUG_LOG_PATH` hardcoded sink and the direct network/subprocess calls in `decision.py` are the main Blueprint/Cartographer drift. They don't create a parallel *engine*, but they create parallel *surfaces* Cartographer can't inventory. C2/C4 in the roadmap address this.

---

## 11. Testing and Verification Map

- **Python:** 114 `test_*.py` under `source_proxy/tests/`, including `test_coding_regression_pack.py` (4,225 lines, wired to `npm run test:coding-regression`), `test_prompt_packet_context_metadata.py` (3,648), `test_cartographer_api.py` (12,207), `test_long_running_tasks.py` (1,945), `test_diff_verification.py` (1,123).
- **Frontend:** vitest suites under `src/{app,components,lib}/coding/__tests__/` (26+ files), plus `npm run test:coding-frontend-regression` pinning a specific critical-path file list.
- **Anti-cheat selftests:** 4R2 grader selftest, 4R4 structured-packet selftest, 4R5 roundtrip selftest, 4R6 structured-output-repair selftest, 4R7 model-escalation selftest — all co-located in the Set A runner.
- **Operator checks:** `docs/.../plan-0X/operator-check.sh` per plan; require artifact presence + JSON parse + plan-N-1 carryforward.
- **Gap:** anti-cheat selftests live **inside** the artifact they guard (same runner file). Independence is by function boundary + selftest, not by separate process/repo. Acceptable today; should be split in C6.

---

## 12. Where GLM Disagrees with Likely Codex/System Self-Assessment

| Area | Likely Codex/system claim | What GLM verified | Verdict | Evidence |
|---|---|---|---|---|
| Source Proxy structure | "lanes are cleanly split" | decision.py is a 7,971-line megafile mixing 6 lanes + 2 verifiers + qwen loop | **DISAGREE** (cleanly split at package level; concentrated at file level) | `wc -l`, def list |
| File organization | "durable engine is the model" | durable engine is clean; decision.py/cartographer/service.py/3 UI shells are not | **PARTIAL** | §6 |
| Debuggability | "FIP0–FIP6 + causal trace gives full observability" | True for recorded fields; **false for failure taxonomy** — 0 model-capability/escalation codes | **DISAGREE** | §7 grep for taxonomy |
| Anti-cheat protection | "fake_go computed, renderer bounded, generator disqualified" | All verified | **AGREE** | §8, runner lines |
| Model lane routing | "lane registry + 4R7 escalation covers brain-switch" | Mechanism yes; **verdict/recommendation not emitted** | **PARTIAL** | §9, 4R7 records attempts but no `*_recommended` |
| Set A status | "real rerun, honest NEEDS_FIX" | Confirmed: 7/10 PASS, A2/A5/A9 NEEDS_FIX, 0 blocked, Stage 5 not approved | **AGREE** | summary.md, 7-stage4r-verdict.md |
| Local model capability | "local models are the primary lane" | True in registry; **A5/A9 should be local-capable but aren't yet decomposed** | **PARTIAL** | §9 |
| API escalation need | "escalation is fallback after bounded local failure" | Mechanism matches; **not surfaced as a recommendation** so the operator can't act on it cleanly | **PARTIAL** | §9 |
| Blueprint/Cartographer alignment | "single canonical path, no parallel engine" | True for engines; **partial for surfaces** (direct subprocess/urllib in decision.py) | **PARTIAL** | §10 |
| Dirty-tree safety | "clean tree, no media mutation" | Verified: 0 dirty, 0 staged, 1 untracked 0-byte temp artifact outside scope | **AGREE** | git status, metadata.json |

---

## 13. Known Risks and Blockers

1. **`decision.py` concentration (very high).** Any lane change risks 5 other lanes; the file is the single largest blast radius in the system.
2. **Failure-taxonomy gap (high).** Without distinct codes for `MODEL_CAPABILITY_LIMIT` / `LOCAL_MODEL_INSUFFICIENT` / `API_ESCALATION_RECOMMENDED`, the system literally cannot answer the brain-switch question it was built for. This blocks honest A2/A5/A9 closure.
3. **Three overlapping UI shells (high).** Which is canonical is implicit (plan-00 says CockpitShell; `/coding` page imports CommandCenterShell; CodingAgentInterface is largest and unclear status). Confusion risk for any frontend work.
4. **Anti-cheat selftest co-location (med).** Selftests guard the runner they live in. A future bad edit to the runner could weaken both together. Needs physical separation in C6.
5. **Headroom proxy not running (low, environmental).** Freeze used the documented fallback; not a code risk, but every future context export will be larger than necessary until the proxy is up.
6. **Dict-blob packets vs documented schemas (med).** `mvi-contract.json` / `canonical-state-and-event-contract.md` define shapes; code uses `dict[str, Any]`. Drift between doc and code is silent.
7. **Hardcoded debug log path (low).** `_DEBUG_LOG_PATH` in a prod module is a smell; silent OSError swallow hides telemetry loss.
8. **No `PROMPT_AMBIGUITY` / `RESOURCE_PRESSURE` detection (low-med).** Budget/expenditure modules exist but aren't wired to reason codes.

---

## 14. Recommended Cleanup Plan (staged, do not implement from this audit)

Each stage is **plan-only**. Britton + Codex must review before any code lands. Order is risk-ascending.

### C0 — Source-of-truth freeze + dirty-tree preservation
- **Goal:** this audit + freeze XML are the agreed baseline; no edits until C1 is approved.
- **Files:** the 5 audit outputs only.
- **Why:** every later stage references HEAD `927055e4` as the freeze point.
- **Safe first patch:** none (freeze is the patch).
- **Tests/checks:** checksums + metadata JSON parse (this audit's §validation).
- **Stop:** until Britton opens C1.
- **Rollback:** delete audit dir.
- **Human approval:** Britton confirms freeze before C1.

### C1 — Failure taxonomy + debug receipt unification
- **Goal:** one module (`source_proxy/diagnostics/status_codes.py` or similar) defining all 17 codes; every lane emits a stable `reason_code`; FIP0 receipt carries a top-level `failure_classification`.
- **Files likely:** new `diagnostics/status_codes.py`; edits to `decision.py` emit sites; `tasks/long_running.py`; `tasks/durable_execution.py`; receipt serializers.
- **Why:** closes the §7/§9 gap; unblocks honest A2/A5/A9.
- **Safe first patch:** add the enum + a `classify_failure(error, context)` helper; wire one lane (qwen) end-to-end; leave existing strings as fallback.
- **Tests:** new `test_status_codes.py`; extend test_prompt_packet_context_metadata to assert reason_code present.
- **Stop:** if any existing test goes red for reasons other than the new field.
- **Rollback:** revert the enum module; fallback strings still work.
- **Human approval:** Britton signs off on the 17-code list before wiring.

### C2 — API transport vs domain logic split (decision.py)
- **Goal:** `api/decision.py` becomes a thin router; FIP0–FIP6 logic moves to `decision/lanes/*.py`.
- **Files:** `api/decision.py` (7,971 → target <1,500); new `decision/lanes/{receipts,context,research,coder,verifier,trace}.py`.
- **Why:** §5/§6 concentration risk; enables per-lane testing.
- **Safe first patch:** extract FIP0 receipt read/serialize (pure functions) first; keep behavior identical.
- **Tests:** test_proxy_runner, test_prompt_packet_context_metadata must stay green; add lane-isolation tests.
- **Stop:** if receipt JSON shape changes.
- **Rollback:** move functions back.
- **Human approval:** Britton approves the lane file layout.
- **⚠️ Do this AFTER C1** so splits can carry the new reason codes.

### C3 — Long-running task engine responsibility split
- **Goal:** `tasks/long_running.py` splits into `apply/`, `trace/`, `regression/`.
- **Files:** `tasks/long_running.py` (6,513 → engine ~2,500 + 3 helpers).
- **Why:** mixes engine with git-apply heuristics + next-router detection + frontend-regression triggers.
- **Safe first patch:** extract `_git_apply_*` and next-router helpers to `tasks/apply/`.
- **Tests:** test_long_running_tasks, test_diff_verification.
- **Stop:** if apply behavior changes.
- **Rollback:** re-import.
- **Human approval:** Britton approves the split.

### C4 — Decision/research/model lane split
- **Goal:** direct subprocess/urllib calls in decision.py route through lanes so Cartographer can inventory them.
- **Files:** browser probe, ollama tags, qwen call → `decision/lanes/`.
- **Why:** §10 drift; parallel surfaces outside Cartographer.
- **Safe first patch:** wrap qwen call in a lane function; decision.py calls the lane.
- **Tests:** test_coder_agent_repomix_diff, test_ollama_route.
- **Stop:** if any lane timing changes materially.
- **Rollback:** inline again.
- **Human approval:** Britton.

### C5 — Coding UI shell split
- **Goal:** decide which shell is canonical (retire/feature-flag the others); split the canonical one into types/hooks/components.
- **Files:** `CodingAgentInterface.tsx`, `CodingCockpitShell.tsx`, `CodingCommandCenterShell.tsx`.
- **Why:** §6 three overlapping 10k+ line shells.
- **Safe first patch:** add a feature flag + extract types to `*.ts`; do NOT delete any shell yet.
- **Tests:** coding-*-shell.test.tsx, page.test.tsx.
- **Stop:** if `/coding` route regresses.
- **Rollback:** flip flag.
- **Human approval:** Britton picks the canonical shell.

### C6 — Anti-cheat / false-positive detector hardening
- **Goal:** move 4R2/4R4/4R7 selftests out of the Set A runner into a standalone `verification/anticheat/` package so they guard from outside.
- **Files:** new `source_proxy/verification/anticheat/`; the Set A runner imports from it.
- **Why:** §8/§11 independence-by-process, not just by-function.
- **Safe first patch:** copy (not move) selftests to the new package; run both; assert identical results.
- **Tests:** the selftests themselves, plus a parity test.
- **Stop:** if parity fails.
- **Rollback:** delete new package; runner unchanged.
- **Human approval:** Britton + Codex review.

### C7 — Local-model packet generation decomposition
- **Goal:** decompose A5/A9-style prompts into sub-packets the local model can satisfy; packet prompt templates per task shape.
- **Files:** `decision/prompt_packet.py`, new `decision/packet_templates/`.
- **Why:** §9 — make A5/A9 local-capable before reaching for API.
- **Safe first patch:** add a decomposer for one task shape (comparison); A/B against monolithic.
- **Tests:** new packet-template tests; re-run A5/A9 locally.
- **Stop:** if decomposition makes packets worse.
- **Rollback:** use monolithic.
- **Human approval:** Britton.

### C8 — Provider/API escalation contract
- **Goal:** emit `API_ESCALATION_RECOMMENDED` only after bounded local failure (C1 code + C7 decomposition); record cost/privacy before any API call; Britton-approval gate.
- **Files:** `decision/model_lanes.py`, `routing/litellm_router.py`, new `decision/escalation_contract.py`.
- **Why:** §9 — make the brain-switch explicit and auditable.
- **Safe first patch:** add the contract + a dry-run that prints the recommendation without calling API.
- **Tests:** escalation-contract tests; assert no API call without approval.
- **Stop:** if any unapproved API call attempt.
- **Rollback:** disable contract.
- **Human approval:** Britton (this is the highest-stakes stage).

### C9 — Test + operator-check requalification
- **Goal:** after C1–C8, re-run the full regression + frontend suites + per-plan operator checks; update runbooks.
- **Files:** `source_proxy/tests/`, `src/**/__tests__/`, `docs/.../operator-check.sh`, `_blueprints/runbooks/`.
- **Why:** every prior stage changes surfaces; tests must prove no regression.
- **Safe first patch:** add a top-level `npm run check:all` that runs lint+typecheck+build+both test suites+operator checks.
- **Tests:** the suites themselves.
- **Stop:** if any suite red.
- **Rollback:** per-stage.
- **Human approval:** Britton signs the requalification before any new feature work.

---

## 15. Mobile Download File Index

See `glm-mobile-download-index.md` (next file). Short version:

| File | Open with | Use |
|---|---|---|
| `glm-source-proxy-audit-20260621.md` | Markdown viewer | Read this first on Fold 7 |
| `glm-source-proxy-freeze-20260621.xml` | Text/XML / upload to AI | Compact Source Proxy context for another AI/chat |
| `glm-mobile-download-index.md` | Markdown viewer | File list + hashes + how-to |
| `glm-checksums.sha256` | Text | Verify integrity |
| `glm-freeze-metadata.json` | JSON | Machine-readable freeze identity |

---

**End of GLM audit.** No source was modified. No cleanup was performed. Nothing staged/committed/pushed. Compare against Codex before any C1–C9 work.

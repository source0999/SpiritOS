# GLM Full-Repo Second Audit — 2026-06-21

**Reviewer:** GLM (independent). **Mode:** full-repo freeze + read-only audit against the **supplied** 2026 best-practice benchmark. No source mutation, no cleanup, no stage/commit/push.
**HEAD:** `927055e4` · **Branch:** `master` · **Host:** Spirit (Dell/source-server) · **Repo:** `Z:\` (= `~/SpiritOS`)
**Scope:** full code + architecture docs across SpiritOS — Source Proxy, Coding UI, SpiritFlix, media tooling, Mac worker, Scout, Cartographer/Blueprint, scripts/ops, docs.
**Companion files:** 3 freeze shards (`-shard-00{1,2,3}.xml`), `glm-full-repo-mobile-index.md`, `glm-headroom-repair-log.md`, `glm-full-repo-metadata.json`, `glm-full-repo-checksums.sha256`, `glm-full-repo-freeze-20260621-shard-index.md`.

> Open this first on Fold 7. Then compare against the **prior** source-proxy-min GLM audit and any future Codex audit before approving cleanup. Do **not** approve implementation from this audit alone.

---

## 1. GLM Independent Executive Verdict

**Overall: PARTIALLY_HEALTHY · OS-BRAIN-MODEL-IS-REAL · CONCENTRATED-AND-TAXONOMY-WEAK · ANTI-CHEAT-STRONG · MEDIA-BOUNDARY-CLEAN.**

The full-repo view confirms and widens the prior source-proxy-min findings:

- The **OS-brain ↔ human-brain model is genuinely implemented**, not just documented. `messy prompt → /coding (CodingCommandCenterShell) → /v1/decisions route (advisory) → Source Proxy lanes (route/spec/context/research/mac/model/verifier/repair) → durable engine → receipt+trace+consumer → grader → human approval` is real and wired across Python + TypeScript.
- **SpiritOS is multi-system, not one app.** Beyond Source Proxy there are: Scout (read-only intelligence poller, own FastAPI + Docker), SpiritFlix (Jellyfin-backed media app), a media tooling suite (`scripts/media/`, incl. a **10,829-line `face_organizer.py`**), a converter with an authorization gate, TTS/STT, an Oracle voice session, a Mac worker bridge, and a ytmclone-android app. Each has its own boundary.
- **Media/SpiritFlix boundary is clean and safe.** SpiritFlix/media code lives under `src/app/spiritflix`, `src/lib/spiritflix`, `src/lib/media`, `scripts/media`, `services/jellyfin`, `backend/searxng`. The converter enforces ownership/license authorization before YouTube imports. `face_organizer.py` is **dry-run by default**. Source Proxy does **not** import SpiritFlix. The two dirty + one new SpiritFlix file at this HEAD are Britton's WIP, not this audit's.
- **The same two structural problems from the prior audit are now repo-wide:** (1) **concentration** — `decision.py` 7,971 lines, `face_organizer.py` 10,829 lines, three Coding UI shells (37,956 lines combined), `cartographer/service.py` 5,769 lines; (2) **failure taxonomy gap** — no `MODEL_CAPABILITY_LIMIT` / `LOCAL_MODEL_INSUFFICIENT` / `API_ESCALATION_RECOMMENDED` codes anywhere in the repo, which directly weakens the brain-switch.
- **Anti-cheat remains the strongest subsystem** and is honestly documented (old generator-cheated Set A disqualified; 4R2 grader + `fake_go_detected` computed + renderer-bounded + selftests).
- **Headroom is BLOCKED_ENV** on this host (Cursor holds 8797; Linux venv can't run on Windows git-bash). Documented fallback used; no token savings lost any data.

**If Britton does one thing next:** keep the F0 freeze, then do F1 (failure taxonomy) + F5 (split `decision.py`) before any feature expansion. See §17.

---

## 2. Freeze Identity and Caveats

| Field | Value |
|---|---|
| HEAD | `927055e489eb1dc9a263bf3a80cde53869e274ce` |
| Branch | `master` |
| Dirty paths | 2 (SpiritFlix WIP, not this audit) |
| Staged | 0 |
| Untracked | 4 (1 zero-byte temp, 1 SpiritFlix WIP script, 2 GLM audit dirs) |
| Freeze form | **3 shards** (single full XML was 38 MB / 6,630 files — unusable on mobile) |
| Shard total | 4.20 MB / 1,436 files / tree-sitter compressed |
| Headroom | BLOCKED_ENV (proxy down; Cursor on 8797; Linux venv) |

**Caveat (important):** This is a **shard freeze**, not a literal single-file dump of every byte. Each shard is a clean repomix run scoped to one area; together they cover all code + architecture docs. Binary/media/build/runtime/secrets/evidence-raw were excluded per the task's bloat rules. A reviewer wanting byte-exact full-tree should regenerate with `repomix.config.json` (warned at **321 MB** pre-ignore in `docs/context-export/repomix-headroom-preflight.md`).

| Shard | Bytes | Files | Scope |
|---|---|---|---|
| `-shard-001.xml` | 1,769,609 | 816 | Core OS code: `source_proxy/**` + `src/**` |
| `-shard-002.xml` | 550,807 | 189 | Tooling: `scout/**` + `scripts/**` + root configs |
| `-shard-003.xml` | 1,883,468 | 431 | Architecture docs: `_blueprints/**` + plan `.md` + pivot docs |

---

## 3. Supplied Benchmark Summary

GLM used **only** the supplied 2026 benchmark (A–K). No independent best-practice research was performed. Categories applied:

- **A** modular architecture & responsibility boundaries (thin routers, service/domain split, UI shell split)
- **B** bounded agent-computer interfaces (bounded tools, explicit contracts, no shell chaos)
- **C** structured outputs & schema validation (strict JSON, bounded repair, renderer formats only validated decisions, no manual PASS flip)
- **D** traceability & receipts (task_id/trace_id/run_id/event_id/…/raw_evidence_path)
- **E** debugging & failure taxonomy (19 named failure classes)
- **F** anti-cheat / false-positive detectors (17 detector categories)
- **G** context & memory strategy (bounded packets, Headroom/Repomix, no whole-repo stuffing)
- **H** human-in-the-loop control (approval gates, protected paths, blocked states, rollback)
- **I** local-first, API-after-bounded-failure (A2 may escalate; A5/A9 should be local-capable)
- **J** clean coding & commenting (small modules, thin handlers, typed contracts, intent-comments)
- **K** OS brain ↔ human brain model (intent → structure → lanes → workers → evidence → summary → approval → memory)

---

## 4. Whole-Repo System Map

```
SpiritOS = Next 16 App Router (src/) + Python Source Proxy (source_proxy/) + Scout (scout/) + media tooling (scripts/media) + services

Human surface
  /coding (CodingCommandCenterShell.tsx 10,050L)  ← active
  /chat (Spirit Chat 2,204L)  /oracle (voice session)  /spirit (Ollama chat API)
  /spiritflix (SpiritFlixApp + Player 3,042L)  /media  /converter (auth-gated)
  /dashboard /map /stats /intelligence

Next proxy routes (src/app/v1/**, src/app/api/**)
  /v1/decisions/route      advisory route decision + FIP0–FIP6 enrichment
  /v1/actions/execute-approved   ONLY decision-bearing apply (central_gate_check fail-closed)
  /v1/coding/{runs,self-tests,mac-advisory,research-preview,agent-lab-*,…}
  /v1/tasks/long-running   durable apply path
  /api/spirit  /api/tts  /api/stt  /api/spiritflix/**  /api/coding/mac-worker

Python Source Proxy (source_proxy/, FastAPI, 18 routers)
  api/  decision/ (32 modules)  tasks/  cartographer/ (80+ modules)  routing/
  verification/  approval/  safety/  context/  planning/  sandbox/  agent_factory/
  agents/  diagnostics/  budget/  expenditure/  vector/  proxy_memory/  codex/

Scout (scout/, separate FastAPI, Docker, CPU-only, read-only intel)
  pollers/{github,rss}  sources/  extractors/  api/  debugger/  packets/

Media tooling (scripts/media, dry-run by default)
  face_organizer.py 10,829L  spiritflix_anime_import.py  (+ dual-audio WIP)
  spiritflix_smart_tag*  spiritflix_*_import.py  model_gallery (excluded bloat)

Mac worker bridge (scripts/mac-worker + src/lib/mac-worker) — advisory, approval-bounded
Converter (src/lib/converter) — ownership/license authorization gate before YouTube
Cartographer / Blueprint (_blueprints/ + source_proxy/cartographer/) — ownership maps, advisory
```

### Per-subsystem detail

| Subsystem | Purpose | Main files | Entry | State/storage | External svc | Tests | Belongs in OS-brain? |
|---|---|---|---|---|---|---|---|
| Source Proxy | OS brain: route/spec/lanes/grader | `source_proxy/**` | `main.py` (FastAPI) | sqlite receipts, evidence dir | Ollama, SearXNG, Mac | 114 py tests | **Yes — core** |
| Coding UI | Human brain surface | `src/app/coding`, `src/components/coding` | `/coding` page | Dexie (client), server run store | Source Proxy API | vitest suites | **Yes — human face** |
| SpiritFlix | Personal media app | `src/app/spiritflix`, `src/lib/spiritflix` | `/spiritflix` | Jellyfin DB | Jellyfin | partial | **No — separate product** |
| Media tooling | Offline media organization | `scripts/media/*` | CLI (dry-run) | NFO/crops on --apply | insightface/GPU | schema tests | **No — tooling** |
| Scout | Read-only intel polling | `scout/src/scout/**` | `scout/main.py` | scout/data | GitHub/RSS allowlist | scout tests | **Adjacent — feeds research lane** |
| Mac worker | Mac GPU dispatch bridge | `scripts/mac-worker`, `src/lib/mac-worker` | mjs/py | advisory only | Mac over LAN | contract tests | **Yes — worker brain** |
| Converter | Authorized media import | `src/lib/converter` | `/converter` | job queue | yt-dlp/ffmpeg | service tests | **No — separate product** |
| Cartographer | Ownership mapping/planning | `source_proxy/cartographer` (80+) | service.py | advisory | none | api tests | **Yes — meta-brain** |
| Blueprint | Intent/boundary source-of-truth | `_blueprints/**` | frontmatter | markdown | none | validate-blueprints | **Yes — intent layer** |
| Spirit chat / Oracle / TTS | Conversational + voice | `src/lib/spirit`, `src/lib/oracle`, `src/lib/tts` | `/api/spirit` | chat-db | Ollama/Whisper/Piper | partial | **Yes — human I/O** |

---

## 5. OS Brain ↔ Human Brain Alignment (Benchmark K)

Expected chain: `human messy intent → OS brain structuring → lane/tool/model selection → bounded worker execution → evidence return → honest human summary → human approval → memory/context improvement`.

| Link in chain | Where in repo | Verdict |
|---|---|---|
| Human-facing surfaces | `/coding`, `/chat`, `/oracle`, `/spiritflix`, `/converter` | **STRONG** |
| Machine-facing packets | FIP0–FIP6 receipts, prompt_packet, plan3 durable, mvi-contract.json | **STRONG** |
| Subsystem ownership | `source_proxy/{api,decision,tasks,…}`, scout, mac-worker | **STRONG** (at package level) |
| Plan/execute/verify boundaries | planning/, durable_execution, verification/, grader | **STRONG** |
| Memory/context layer | context/obsidian, proxy_memory, model_lanes, headroom/repomix | **PARTIAL** (exists; not unified) |
| Model lane registry | decision/model_lanes.py | **STRONG** |
| Worker contracts | mac-worker contract.ts/registry.ts, worker_contract.py | **STRONG** |
| Evidence/receipt contracts | FIP0 receipt, causal trace, consumer_event_id | **STRONG** |
| Human authority gates | approval/gate + external_gate, gate-* scripts, blocked_human | **STRONG** |

**OS-brain alignment verdict: STRONG.** The repo genuinely implements the K-model in code structure, not just docs. This is the headline positive of the full-repo view.

---

## 6. AI Coding Loop Readiness (Benchmark A–J loop components)

| Loop component | Verdict | Note |
|---|---|---|
| Messy human goal intake | **READY** | CodingCommandCenterShell + /v1/decisions |
| Intent/spec extraction | **READY** | decision/router, task_spec_intake |
| Repo/context read | **READY** | context/inventory, obsidian, repo_map |
| Context compression/digests | **PARTIAL** | headroom/repomix exist; headroom BLOCKED_ENV here |
| Plan decomposition | **PARTIAL** | planning/architect deterministic; decomposition for A5/A9 weak (§11) |
| Tool/lane selection | **READY** | decision/router, model_lanes |
| Bounded execution | **READY** | durable_execution transitions, bounded tool actions |
| Verification | **READY** | FIP5 browser/functional verifiers, verification/ |
| Repair loop | **READY** | artifact_repair_loop, record_post_apply_verification |
| Trace/receipt | **READY** | FIP0 receipt, causal trace, consumer_event_id |
| Failure taxonomy | **MISSING** | no model-capability/escalation codes (§9) |
| Anti-cheat detector | **STRONG** | §10 |
| Human approval for risky boundaries | **READY** | central_gate_check, blocked_human |
| Artifact/handoff output | **READY** | artifact_handoff_packet, prompt_packet |
| Requalification tests | **READY** | 114 py + 26 ts suites + operator checks |
| Resume/continue support | **PARTIAL** | durable task resume yes; loop-level resume partial |

**Loop state location:** sqlite + evidence dir + Dexie (client) + server run store. **Inspectable:** yes via FIP0/FIP6 endpoints. **Can resume:** task-level yes. **Can explain blocked/fail:** partial — `blocked_human`/`blocked_env` clear; model-failure explanation weak. **Avoids repeating failed retries:** partial — 4R7 records attempts but no "do not retry this lane" memory. **Knows when to escalate to API:** mechanism yes, verdict no (§11). **Knows when to ask human:** yes via policy gates.

---

## 7. Clean Architecture / Module Boundaries Audit (Benchmark A, B, J)

### Backend (FastAPI) — verdict: PARTIAL

| Check | Verdict | Evidence |
|---|---|---|
| Route/API transport thin | **WEAK** | `api/decision.py` is 7,971 lines with FIP0–FIP6 logic + verifiers + qwen loop **inside the router file** |
| Routers delegate to service/domain | **PARTIAL** | some routers delegate (cartographer, healthcheck); decision.py does not |
| Domain logic not in one giant route file | **CONTRADICTORY** | decision.py is exactly this anti-pattern |
| APIRouter/module boundaries used | **STRONG** | 18 routers in main.py |
| Write paths isolated from advisory | **STRONG** | execute-approved + central_gate_check is the only apply; advisory routes verified non-mutating |

### Frontend (Next/React) — verdict: PARTIAL

| Check | Verdict | Evidence |
|---|---|---|
| Page entry files small | **STRONG** | page.tsx files are thin (import + render shell) |
| Route handlers thin | **PARTIAL** | v1 routes mostly delegate; some inline logic |
| Large UI shells split into state/hooks/view | **WEAK** | 3 shells 10k–15k lines each, mixing types+storage+business+render |
| Debug/timeline/receipt widgets separate | **PARTIAL** | tool-runtime-surface, timeline-events, task-story-ledger exist as lib modules |
| API adapters not mixed with rendering | **PARTIAL** | proxy-route-payload, route-availability separated; but shells still call them inline |
| Canonical UI shell clear | **CONTRADICTORY** | plan-00 says CockpitShell active; `/coding` imports CommandCenterShell; CodingAgentInterface (largest) status unclear |

### Bounded agent-computer interfaces (Benchmark B) — verdict: PARTIAL→STRONG

| Check | Verdict | Evidence |
|---|---|---|
| Bounded tool surfaces | **STRONG** | tool_actions, tool_action_executor, workspace_tools, sandbox/bubblewrap |
| Explicit tool contracts | **STRONG** | contracts.py, worker_contract.py, mac-worker contract.ts |
| Repo read APIs | **STRONG** | context/inventory, workspace_tools, repo_map |
| Safe write APIs | **STRONG** | safe_write, safe_task_queue, central_gate_check |
| Test runners / verifier lanes | **STRONG** | testing/runner, verification/, FIP5 verifiers |
| Worker contracts | **STRONG** | mac-worker, multi_worker_branch_workflow |
| Raw evidence paths / deterministic receipts | **STRONG** | evidence dir, FIP0 receipt |
| Generic shell chaos | **PARTIAL** | decision.py direct subprocess/urllib for browser/qwen/ollama bypasses lane registry |
| Hidden side effects | **PARTIAL** | `_DEBUG_LOG_PATH` hardcoded sink in decision.py |

---

## 8. Clean Coding and Commenting Audit (Benchmark J)

### Coding standard

| Check | Verdict | Note |
|---|---|---|
| Small modules with clear ownership | **PARTIAL** | packages small; several God-files |
| Thin API/route handlers | **WEAK** | decision.py |
| Clear service/domain modules | **PARTIAL** | durable_execution is exemplary; decision.py is not |
| Clear model/worker adapters | **STRONG** | routing/litellm_router, ollama_route, mac-worker |
| Typed contracts/schemas for stable data | **PARTIAL** | Pydantic on routes; FIP packets are dict[str, Any] despite mvi-contract.json |
| Minimal global mutable state | **PARTIAL** | coder timing diagnostics globals in long_running.py |
| No duplicated truth calculations | **PARTIAL** | lane status computed in multiple places |
| No hidden import-time side effects | **PARTIAL** | decision.py writes debug log at import-able call sites |
| Timeouts around shell/network | **STRONG** | subprocess timeouts present; `face_organizer.py` has only 1 timeout for 4 subprocess calls (media tooling exception) |
| Descriptive names | **STRONG** | naming is clear and consistent |
| Tests near behavior | **STRONG** | co-located __tests__ + source_proxy/tests |

### Commenting standard — concrete examples

- **Good (intent/invariant/safety):**
  - `source_proxy/tasks/durable_execution.py` — `PLAN3_STATUSES`, `PLAN3_TRANSITIONS`, `PLAN3_TERMINAL_STATUSES` documented with allowed transitions. ✅ matches J "complex state machines should document allowed transitions."
  - `source_proxy/main.py` — `# Human-approved local diffs: execution goes to POST .../execute-approved` explains the write-policy invariant. ✅
  - Set A runner — `# fake_go_detected computed`, `# renderer does not invent recommendations` document anti-cheat intent. ✅ matches J "anti-cheat/debug detectors should document what they protect against."
  - `scripts/media/face_organizer.py` — "This tool is dry-run by default" at top. ✅ safety boundary documented.
  - `scout/SCOPE.md` — explicit Permitted/Prohibited Activities + Kill Switch. ✅ exemplary.

- **Bad (restates syntax / missing invariants):**
  - `source_proxy/api/decision.py` line ~1 — `_DEBUG_LOG_PATH = "/home/source/SpiritOS/.cursor/debug-9460b9.log"` with **no comment** explaining why a session-specific path is baked into a prod module. ❌
  - FIP0–FIP6 numbering is **never explained in one place** — must be inferred from `_fip0_receipt_root` … `_fip6_operator_trace`. ❌ missing public-contract docstring.
  - Several `except Exception: pass` (decision.py lines 7020/7023/7313) with **no comment** on why the soft-fail is safe. ❌ missing safety-boundary comment.

---

## 9. Debugging / Observability / Failure Taxonomy Audit (Benchmark D, E)

### Traceability fields (Benchmark D) — verdict: STRONG on the apply path

| Field | Present? | Note |
|---|---|---|
| task_id, trace_id, run_id, event_id, parent_event_id | ✅ | causal events chain |
| subsystem, tool/lane invoked | ✅ | integrations[normalized_subsystem], lane status |
| worker/node, provider/model | ✅ | mac_status, model_lanes, ollama route |
| attempt number, timeout | ✅ | qwen max attempts, subprocess timeouts classified |
| policy decision, verification result, repair result | ✅ | central_gate, FIP5, repair loop |
| consumer_event_id | ✅ | plan3 consumer evidence |
| final_status, raw_evidence_path, human approval state | ✅ | grader + evidence dir + approval ledger |

A reviewer **can** answer: what was asked/decided/used/acted/changed/verified/failed/consumed/why-final. ✅

### Failure taxonomy (Benchmark E) — verdict: the gap

| Failure class | Verdict |
|---|---|
| TECHNICAL_FAILURE | PARTIAL (caught as except Exception, not a code) |
| ENVIRONMENT_FAILURE | PARTIAL (blocked_env status; not a reason code) |
| SERVICE_UNAVAILABLE | PARTIAL (healthcheck 503; not in flow) |
| BRIDGE_INTEGRATION_FAILURE | MISSING |
| ROUTING_FAILURE | PARTIAL |
| TOOL_FAILURE | MISSING |
| SEARCH_PROVIDER_EMPTY | PARTIAL (research packet records empty) |
| SEARCH_PROVIDER_FAILURE | PARTIAL |
| MODEL_CAPABILITY_LIMIT | **MISSING** ← A2/A5/A9 root cause, unclassified |
| MODEL_FORMATTING_FAILURE | PARTIAL (4R7 parse_error per attempt, not receipt-level) |
| LOCAL_MODEL_INSUFFICIENT | **MISSING** ← only local_model_unavailable (conn/env) exists |
| API_ESCALATION_RECOMMENDED | **MISSING** ← 4R7 escalates silently |
| POLICY_BLOCKED | SUPPORTED |
| HUMAN_APPROVAL_REQUIRED | SUPPORTED |
| EVIDENCE_MISSING | PARTIAL |
| VALIDATOR_FAILURE | PARTIAL |
| PROMPT_AMBIGUITY | MISSING |
| RESOURCE_PRESSURE | MISSING (budget/expenditure exist, unwired) |
| UNKNOWN_NEEDS_INVESTIGATION | PARTIAL (bare except serves this silently) |

**Can a debugger:**
- tell **where** it failed? **Yes** (trace + receipt).
- tell **why** it failed? **Partial** — by reading raw evidence; not via one `reason_code`.
- tell if **local AI was insufficient**? **No, not as a first-class signal.** Must infer from "lane attempted → parse_error → validation invalid → no API key."
- tell when **API escalation is justified**? **No — not emitted.**
- distinguish **tool vs reasoning** failure? **No.**
- distinguish **bridge vs model** failure? **No** (only local_model_unavailable for conn/env).
- prevent **false PASS**? **Yes** (fake_go_detected, §10).

**This taxonomy gap is unchanged from the prior audit and is the #1 blocker for honest A2/A5/A9 closure.**

---

## 10. Anti-Cheat / False-Positive Detector Audit (Benchmark F)

| Detector category | Verdict | Evidence |
|---|---|---|
| default PASS | PROTECTED | grader derives status |
| hardcoded fake_go=false | PROTECTED | fake_go_detected is computed |
| canned work products | PROTECTED | renderer runs only after validation; invalid → safe NEEDS_FIX |
| static sources as live research | PROTECTED | old generator disqualified; rerun uses live research |
| route exists = integration | PROTECTED | plan-00 confirmed advisory vs apply |
| status ping = task proof | PROTECTED | behavior verifiers required |
| local repo context = internet | PROTECTED | repo_context_used gate |
| consumer event on canned output | PROTECTED | consumer_event_id on real lane outputs |
| mock/fixture as live | PROTECTED | fixtures segregated |
| advisory/preview as executed | PROTECTED | preview endpoints non-writing |
| fallback counted as success | PROTECTED | headroom/repomix fallback explicitly "fallback" |
| summary contradicting raw | PARTIAL | summary from final_status; consistent in Set A |
| manual JSON flipping | PROTECTED | records structurally validated |
| renderer supplying substance | PROTECTED | selftest renderer_only_renders_validated_packet_fields |
| validator and runner too coupled | PARTIAL | separate functions, same runner file |
| selftests too close to graded code | PARTIAL | 4R selftests co-located in Set A runner |
| provider unavailable reported as success | PROTECTED | 4R7 records unavailable lanes honestly |

### Set A case study (read-back, not re-acceptance)
- Old generator-cheated Set A: **disqualified** (`1-prior-generator-disqualified.md`). ✅
- 4R real rerun: live research + repo + mac + live model. ✅
- 4R2 hardened grader: fake_go_detected + materiality + prompt gates. ✅
- 4R4 structured packets: validator + renderer aligned. ✅
- 4R6/4R7 local-model packet failures: A2/A5/A9 fail because local models couldn't emit valid packets; lane escalation attempted; no API key set. ✅ honest.
- **Stage 4R verdict: NEEDS_FIX (7/10 PASS, A2/A5/A9 NEEDS_FIX, 0 blocked). Stage 5 NOT approved. GLM does NOT claim Set A accepted.**

**Anti-cheat verdict: STRONG.** Unchanged from prior audit — the strongest subsystem.

---

## 11. Model Lane / Brain-Switch Audit (Benchmark I)

### Can the system decide each case?

| Decision | Verdict |
|---|---|
| local model can handle | PARTIAL (registry says yes; runtime proof only post-hoc) |
| local failed formatting | PARTIAL (parse_error per attempt, not a receipt code) |
| local failed reasoning | MISSING |
| local failed structured output | PARTIAL (validation invalid per attempt, not receipt code) |
| local insufficient | MISSING |
| search provider failed | PARTIAL |
| worker/bridge failed | PARTIAL |
| API escalation recommended | MISSING (4R7 escalates silently) |
| human approval required | SUPPORTED |

### A2 / A5 / A9 evaluation

| | A2 (browser ext) | A5 (workstation plan) | A9 (local LLM tools) |
|---|---|---|---|
| Realized API needed at right point? | Yes — bounded local failure then escalation | Borderline | Borderline |
| Escalation by repeated validator failure or task label? | **Repeated validator failure** (correct) | same | same |
| Should local have handled it? | Probably not alone (precise structured constraints) | **Yes, after decomposition** | **Yes, after decomposition** |
| Decomposition that helps | split safe-MVP/payload/native-host fields | split roles/cost/privacy/tooling | split per-tool comparison |
| Provider/env missing | OPENAI/ANTHROPIC/DEEPSEEK/LITELLM all unset | same | same |
| Prevent API overuse | lane order + "API only if creds" + Britton approval | same | same |

**GLM stance (tested against benchmark I, not blindly accepted):**
- **A2 escalation reasonable.** ✅ aligns with benchmark.
- **A5/A9 should be local-capable after decomposition.** ⚠️ currently they fail because monolithic packet prompts exceed local model structured-output ability — a **formatting/context** failure masquerading as capability. The system **cannot currently say this** because there is no MODEL_FORMATTING_FAILURE / LOCAL_MODEL_INSUFFICIENT distinction.
- **API escalation must be fallback after bounded local failure, not default by task type.** ✅ the 4R7 mechanism matches; ❌ the verdict is not emitted.

---

## 12. Context / Memory / Headroom / Repomix Strategy (Benchmark G)

| Check | Verdict | Note |
|---|---|---|
| Bounded context packets | STRONG | FIP1 context packet, prompt_packet |
| Repo maps | STRONG | repo_map, cartographer repo_map |
| Headroom/Repomix packs | PARTIAL | tooling STRONG; Headroom BLOCKED_ENV on this host |
| Source-specific readbacks | STRONG | context/inventory, obsidian |
| Compressed reasoning digests | PARTIAL | exists in receipts; not unified |
| Resumable run state | PARTIAL | task-level yes; loop-level partial |
| Evidence references | STRONG | raw_evidence_path everywhere |
| Avoid re-reasoning from scratch | PARTIAL | proxy_memory exists; not deeply wired |

**Headroom reality (this host):** Port 8797 is held by **Cursor.exe** (the editor), not Headroom. The Headroom CLI is a **Linux venv** that cannot execute under Windows git-bash. Bounded 12s repair attempt on alt port 8798 failed (`cannot execute: required file not found`). Cursor was NOT killed (unrelated service). Fallback: tight tree-sitter repomix profile. **No data lost; only token savings forgone.** See `glm-headroom-repair-log.md`.

**Full-repo freeze strategy finding:** the default `repomix.config.json` (`include: ["**/*"]`) produced **321 MB** historically (`docs/context-export/repomix-headroom-preflight.md`); current ignore list cuts it but a full pack is still 38 MB. The source-proxy-min profile (1.6 MB) is too narrow for a full audit. GLM's shard approach (3 × <2 MB) is the right middle ground and matches the task's shard provision.

---

## 13. Blueprint / Cartographer Workflow Alignment (Benchmark A/K)

| Principle | Verdict | Note |
|---|---|---|
| Blueprint defines intent/boundaries | STRONG | `_blueprints/` with frontmatter + write_policy; INDEX.md canonical |
| Cartographer maps ownership | STRONG | service.py + 80 modules, level_6 ownership |
| Source Proxy runs canonical paths | STRONG | apply only via execute-approved + gate |
| Receipts prove invocation+consumption | STRONG | FIP0 + causal trace + consumer_event_id |
| Verifier/grader checks work | STRONG | FIP5 + 4R2 grader |
| Human approves high-risk transitions | STRONG | gate scripts, blocked_human |
| No casual parallel implementation paths | PARTIAL | decision.py direct subprocess/urllib bypasses lane inventory; `_DEBUG_LOG_PATH` hardcoded |

**Flags:** the direct network/subprocess calls in `decision.py` (browser probe, ollama tags, qwen loop) are lanes in behavior but not in Cartographer's view — a parallel surface, not a parallel engine. F4/F5 address this.

---

## 14. SpiritFlix / Media Boundary and Safety Audit

| Check | Verdict | Evidence |
|---|---|---|
| SpiritFlix code isolated from Source Proxy | STRONG | Source Proxy has no spiritflix imports |
| Media tooling dry-run by default | STRONG | face_organizer.py "dry-run by default"; --apply required |
| Converter authorization gate | STRONG | YouTube imports require affirmed ownership/license + proofPath |
| Write roots bounded | STRONG | converter writes under /mnt/spirit-8tb/converter/* only |
| No SpiritFlix mutation by this audit | STRONG | 2 dirty + 1 new SpiritFlix files are Britton's WIP, untouched |
| Media galleries excluded from freeze | STRONG | scripts/media/model_gallery excluded (923-file bloat) |

**SpiritFlix/media verdict: STRONG boundary, safe.** The dirtiest-looking thing in the tree (the new `spiritflix_dual_audio_anime_import.py`) is Britton's authorized-anime importer WIP with proper docstring; not a concern. `face_organizer.py` at 10,829 lines is a concentration risk **within media tooling** but is offline/CLI/dry-run, so blast radius is contained — it does not affect the OS-brain loop.

---

## 15. Where This Full-Repo Audit Expands / Disagrees with the Prior source-proxy-min Audit

| Area | Prior (source-proxy-min) finding | This full-repo finding | Change |
|---|---|---|---|
| Scope | Source Proxy only | + SpiritFlix, Scout, media, Mac, converter, spirit chat/oracle | **Widened** |
| OS-brain model | inferred | confirmed repo-wide in code | **Strengthened** |
| Concentration | decision.py + 3 UI shells | + `face_organizer.py` 10,829L, cartographer 80 modules | **Widened** |
| Failure taxonomy | weak (no model codes) | same — confirmed repo-wide absence | **Unchanged** |
| Anti-cheat | strongest part | confirmed; still strongest | **Unchanged** |
| Brain-switch | incomplete | confirmed; A5/A9 = formatting failure misread as capability | **Sharpened** |
| Media boundary | not audited | clean + safe + dry-run | **New (positive)** |
| Headroom | proxy down | BLOCKED_ENV — root cause = Cursor on 8797 + Linux venv | **Root-caused** |
| Scout | not audited | exemplary bounded read-only intel service (SCOPE.md + kill switch) | **New (positive exemplar)** |
| Context strategy | headroom/repomix exist | full pack 321MB→38MB; shards are the right unit | **Sharpened** |

**Net:** the full-repo view **upgrades** the OS-brain assessment (it's real and broad), **confirms** the two structural problems (concentration + taxonomy), and **adds** two positive exemplars (Scout's bounded contract; SpiritFlix's clean boundary) that the Source Proxy itself could learn from.

---

## 16. Top Risks Ranked

1. **Failure-taxonomy gap (high).** No MODEL_CAPABILITY_LIMIT / LOCAL_MODEL_INSUFFICIENT / API_ESCALATION_RECOMMENDED. Blocks honest A2/A5/A9 closure and the brain-switch. Highest leverage to fix.
2. **`decision.py` concentration (very high).** 7,971-line FIP0–FIP6 megafile; largest blast radius in the OS brain.
3. **Three overlapping UI shells (high).** Canonical shell implicit (CommandCenterShell active, CockpitShell per plan-00, AgentInterface largest/unclear).
4. **`face_organizer.py` 10,829 lines (med, contained).** Concentration in media tooling; dry-run so blast radius limited, but unmaintainable.
5. **Anti-cheat selftest co-location (med).** 4R selftests guard the runner they live in; independence by function not process.
6. **Direct subprocess/urllib in decision.py (med).** Parallel surface bypassing Cartographer lane inventory.
7. **Dict-blob packets vs mvi-contract.json schema (med).** Drift silent.
8. **Headroom port collision (low, env).** Cursor on 8797; needs port-consistency fix or Linux-side start.
9. **Hardcoded `_DEBUG_LOG_PATH` (low).** Session-specific path in prod module.
10. **No PROMPT_AMBIGUITY / RESOURCE_PRESSURE detection (low-med).** Budget/expenditure modules unwired.

---

## 17. Cleanup Roadmap (PLAN ONLY — do not implement; review vs Codex first; Britton signs off per stage)

Each stage: goal · why · files · safe first patch · tests · stop · rollback · approval.

### F0 — Preserve full-repo freeze + audit comparison
- **Goal:** this audit + 3 shards are the agreed full-repo baseline.
- **Why:** every later stage references HEAD `927055e4`.
- **Files:** the 7 audit outputs only.
- **Safe first patch:** none (freeze is the patch).
- **Tests:** checksums + metadata parse (this audit).
- **Stop:** until Britton opens F1.
- **Rollback:** delete audit dir.
- **Approval:** Britton confirms freeze.

### F1 — Failure taxonomy + debug receipt unification (Benchmark E)
- **Goal:** one `diagnostics/status_codes.py` with all 19 classes; every lane emits a stable reason_code; FIP0 receipt carries top-level failure_classification.
- **Why:** closes the #1 risk; unblocks A2/A5/A9.
- **Files:** new diagnostics module; decision.py emit sites; long_running.py; durable_execution.py; receipt serializers.
- **Safe first patch:** add enum + classify_failure() helper; wire qwen lane only; keep old strings as fallback.
- **Tests:** new test_status_codes.py; extend test_prompt_packet_context_metadata.
- **Stop:** if existing tests red for non-new-field reasons.
- **Rollback:** revert enum module; fallback strings still work.
- **Approval:** Britton signs the 19-code list.

### F2 — Anti-cheat detector registry + independent selftests (Benchmark F)
- **Goal:** move 4R2/4R4/4R7 selftests to standalone `verification/anticheat/` guarding from outside.
- **Why:** independence by process, not just function.
- **Files:** new verification/anticheat/; Set A runner imports from it.
- **Safe first patch:** copy (not move) selftests; run both; assert identical.
- **Tests:** selftests + parity test.
- **Stop:** if parity fails.
- **Rollback:** delete new package.
- **Approval:** Britton + Codex.

### F3 — Model lane / brain-switch verdict contract (Benchmark I)
- **Goal:** emit LOCAL_MODEL_INSUFFICIENT / API_ESCALATION_RECOMMENDED only after bounded local failure; record cost/privacy before any API call.
- **Files:** model_lanes.py, litellm_router.py, new escalation_contract.py.
- **Why:** make brain-switch explicit + auditable.
- **Safe first patch:** contract + dry-run that prints recommendation without API call.
- **Tests:** escalation-contract tests; assert no unapproved API call.
- **Stop:** if any unapproved API attempt.
- **Rollback:** disable contract.
- **Approval:** Britton (highest-stakes stage).

### F4 — Local-model packet-generation decomposition (Benchmark I)
- **Goal:** decompose A5/A9-style prompts into sub-packets local models can satisfy; per-task-shape templates.
- **Files:** prompt_packet.py, new packet_templates/.
- **Why:** make A5/A9 local-capable before API.
- **Safe first patch:** decomposer for comparison task shape; A/B vs monolithic.
- **Tests:** packet-template tests; re-run A5/A9 locally.
- **Stop:** if decomposition worsens packets.
- **Rollback:** monolithic.
- **Approval:** Britton.

### F5 — Architecture split: API transport vs domain services (Benchmark A, J)
- **Goal:** api/decision.py → thin router; FIP0–FIP6 → decision/lanes/*.py.
- **Why:** §7 concentration risk.
- **Files:** decision.py 7,971→<1,500; new decision/lanes/{receipts,context,research,coder,verifier,trace}.py.
- **Safe first patch:** extract FIP0 receipt serialize (pure) first; behavior identical.
- **Tests:** test_proxy_runner, test_prompt_packet_context_metadata stay green + lane-isolation tests.
- **Stop:** if receipt JSON shape changes.
- **Rollback:** move functions back.
- **Approval:** Britton approves lane layout. **⚠️ after F1.**

### F6 — Long-running task engine split
- **Goal:** long_running.py 6,513 → engine ~2,500 + apply/ + trace/ + regression/.
- **Files:** tasks/long_running.py.
- **Safe first patch:** extract git-apply + next-router helpers to tasks/apply/.
- **Tests:** test_long_running_tasks, test_diff_verification.
- **Stop:** if apply behavior changes.
- **Rollback:** re-import.
- **Approval:** Britton.

### F7 — Coding UI shell split + canonical UI decision (Benchmark A)
- **Goal:** pick canonical shell; feature-flag others; split canonical into types/hooks/components.
- **Files:** CodingAgentInterface.tsx, CodingCockpitShell.tsx, CodingCommandCenterShell.tsx.
- **Safe first patch:** feature flag + extract types to *.ts; do NOT delete any shell.
- **Tests:** coding-*-shell.test.tsx, page.test.tsx.
- **Stop:** if /coding regresses.
- **Rollback:** flip flag.
- **Approval:** Britton picks canonical shell.

### F8 — Context / memory / Headroom strategy cleanup (Benchmark G)
- **Goal:** unify context packets + digests; fix Headroom port collision (Cursor vs 8797) or move Headroom to a free port consistently; document Linux-side start.
- **Files:** context/, proxy_memory/, headroom scripts, repomix configs.
- **Safe first patch:** add HEADROOM_PORT env consistency across headroom-check.sh, headroom-proxy-dev.sh, repomix-llm.mjs; document Cursor collision.
- **Tests:** headroom-check, context verify.
- **Stop:** if context pack shape changes.
- **Rollback:** revert env.
- **Approval:** Britton.

### F9 — Worker / tool contract cleanup (Benchmark B)
- **Goal:** route decision.py direct subprocess/urllib (browser/qwen/ollama) through lane functions Cartographer can inventory.
- **Files:** decision.py → decision/lanes/; mac-worker contract.
- **Safe first patch:** wrap qwen call in lane function; decision.py calls lane.
- **Tests:** test_coder_agent_repomix_diff, test_ollama_route.
- **Stop:** if lane timing changes materially.
- **Rollback:** inline again.
- **Approval:** Britton.

### F10 — Full-loop requalification battery
- **Goal:** after F1–F9, re-run full regression + frontend + operator checks; update runbooks.
- **Files:** tests/, __tests__/, operator-check.sh, _blueprints/runbooks/.
- **Safe first patch:** add npm run check:all (lint+typecheck+build+both suites+operator checks).
- **Tests:** the suites.
- **Stop:** if any suite red.
- **Rollback:** per-stage.
- **Approval:** Britton signs requalification before new features.

---

## 18. Human Review Checklist

- [ ] Open this Markdown on Fold 7 first (§1, §9, §11, §15, §16).
- [ ] Use shard-001 (core OS code) as the primary AI context for a second opinion on Source Proxy + Coding UI.
- [ ] Use shard-002 (tooling) to check Scout + scripts + Mac worker.
- [ ] Use shard-003 (architecture docs) to check Blueprint/Cartographer intent vs code.
- [ ] Compare against the **prior** source-proxy-min GLM audit — does Codex agree the taxonomy gap + decision.py concentration are the top two risks?
- [ ] Compare against any future Codex full-repo audit.
- [ ] Reconcile on: A5/A9 = formatting failure misread as capability? Scout as the bounded-contract exemplar for Source Proxy?
- [ ] **Do NOT approve F1–F10 implementation** until both GLM + Codex reviewed and Britton signs off per-stage.

---

**End of GLM full-repo audit.** No source modified. No cleanup performed. Nothing staged/committed/pushed. Headroom bounded-repair attempted and honestly logged as BLOCKED_ENV. Compare against prior audit + Codex before any F1–F10 work.

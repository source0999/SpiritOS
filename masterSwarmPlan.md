# Master Swarm Plan: Phases 8–13 for SpiritOS Coder Decomposition

> **Revision history**
> - **v2 (current):** Incorporates review feedback. Phase 8.1 gains context-mode switching for agent-internal tasks. Phase 8.3 restructured into three escalating verification tiers. Phase 10.1 adds explicit UX requirement for vague-task fallthrough states. Phase 11.2 now ships a compatibility shim instead of replacing the Coder signature outright; Phase 11.3 deletes the shim after a soak period. Endpoint URLs and ESLint command shape marked with `TODO: confirm` placeholders pending verification against the live dev setup.
> - **v1:** Initial plan.

---

This is the post-Coder-Agent-fix plan. It continues from `masterProxyPlan.md` (Phases 3–7) and addresses the architectural debt diagnosed in the orchestration review: the `propose_coder_agent_implementation_diff` function is doing nine jobs at once, the frontend can still synthesize implementation diffs, and there is no structured handoff between the Architect role and the Coder role.

The strategy is **cheap wins first, structural rewrite second.** Phase 8 ships deterministic verification and workspace hygiene without touching the agent orchestration — these alone remove the two largest concrete failure modes (synthetic-diff incidents and the agent reading its own source) and buy you time to do the bigger rewrite without UI regressions. Phases 9–12 then introduce the `ArchitectPlan` packet and decompose the Coder properly. Phase 13 adds the Reviewer agent on top of the now-stable foundation.

Every increment in this document is sized for a single Codex prompt: roughly 2–4 hours of focused work, one or two files of meaningful change, and a manual smoke test you can run in the `/coding` UI or via `curl` against the running proxy.

---

## Local Development Endpoints

> **TODO: confirm before running any manual checks.** Every `curl` example in this document uses the shell variables `$PROXY_URL` and `$NEXT_URL`. Set these in your shell before running checks. The values below are placeholders based on a prior pass through the orchestration review; verify against your actual `.env.local` / proxy startup logs.
>
> ```bash
> # Placeholder values — verify before use
> export PROXY_URL="https://127.0.0.1:8787"
> export NEXT_URL="https://127.0.0.1:3000"
> # If the proxy uses self-signed TLS in dev, add -k to every curl
> alias spcurl="curl -sk"
> ```
>
> If your proxy is HTTP rather than HTTPS, change to `http://` and drop the `-k` / `-sk` flag. If ports differ, update both vars and re-run.

## Local Linter and Typecheck Commands

> **TODO: confirm ESLint configuration shape.** Phase 8.3 invokes ESLint and TypeScript. The exact command depends on whether your repo uses flat config (`eslint.config.mjs`, ESLint 9+) or legacy config (`.eslintrc.*`).
>
> - **Flat config (most likely for a Next 16 project):** `npx eslint <target>` — ESLint auto-discovers `eslint.config.mjs`. Do not pass `-c` or `--no-eslintrc`; these are legacy-only flags.
> - **Legacy config:** `npx eslint --no-eslintrc -c .eslintrc.json <target>`.
>
> Confirm with `ls eslint.config.* .eslintrc.*` in your repo root and pick the matching command. Phase 8.3's checks reference `$ESLINT_CMD` as a placeholder; substitute the verified command before running.

---

## The Keystone: ArchitectPlan and CoderPacket Schemas

Before any phase work, read this section. Every phase below derives from these schemas. If the schema is wrong, every layer above it inherits the wrong overload — which is exactly how the current Coder got to nine responsibilities.

### `ArchitectPlan` (the full planning artifact, owned by the task)

```python
@dataclass(frozen=True)
class ArchitectPlan:
    plan_id: str                          # uuid4 hex
    task_id: str                          # long_running_task.id
    schema_version: int                   # start at 1; bump on breaking change
    created_at: str                       # iso8601 UTC

    source_task: str                      # raw user task text, audit only

    bundle_snapshot: BundleSnapshot       # see below
    classification: TaskClassification    # see below
    coder_packet: CoderPacket             # see below
    verification_plan: VerificationPlan   # see below
    budget: PlanBudget                    # see below
```

### `BundleSnapshot` (closes the stale-bundle race)

```python
@dataclass(frozen=True)
class BundleSnapshot:
    bundle_path: str                      # absolute path on disk
    bundle_sha256: str                    # hash of the bundle bytes at plan time
    workspace_root: str
    generated_at: str
```

The Coder MUST re-hash the bundle before reading any context slice. If the hash differs from `bundle_snapshot.bundle_sha256`, the Coder refuses with `reason_code = "bundle_snapshot_drift"` and the task returns to the Architect for re-planning. This is non-negotiable; it's how you eliminate "patch does not apply" theatre forever.

### `TaskClassification`

```python
@dataclass(frozen=True)
class TaskClassification:
    task_class: Literal["implement", "refactor", "fix", "style", "explain"]
    visual_change: bool                   # true if user-visible UI changes expected
    designer_required: bool               # marker only until Designer ships
    estimated_complexity: Literal["trivial", "small", "medium", "large"]
```

### `CoderPacket` (the Coder's entire world — it sees nothing else)

```python
@dataclass(frozen=True)
class CoderPacket:
    target_file: TargetFile               # exactly one target
    operation: Literal["edit", "create", "delete"]
    acceptance_criteria: list[AcceptanceCriterion]
    constraints: ContentConstraints
    context_slices: list[ContextSlice]    # pre-selected by Architect
    forbidden_paths: list[str]            # Coder cannot emit these even if mentioned
    style_directives: list[str]           # max 6, free text, e.g. "Tailwind only"


@dataclass(frozen=True)
class TargetFile:
    path: str                             # repo-relative posix
    exists: bool
    sha256_before: str | None             # for optimistic concurrency on edit


@dataclass(frozen=True)
class AcceptanceCriterion:
    id: str                               # short slug, stable
    description: str
    kind: Literal["literal", "behavioral"]
    # literal:    "must contain string X"      → checked deterministically
    # behavioral: "must render H1 with theme"  → checked by Reviewer in Phase 13


@dataclass(frozen=True)
class ContentConstraints:
    must_contain: list[str]               # exact substrings required in output
    must_not_contain: list[str]
    preserve_imports: list[str]           # symbol names that must remain imported
    preserve_exports: list[str]
    max_added_lines: int | None
    max_removed_lines: int | None


@dataclass(frozen=True)
class ContextSlice:
    path: str
    kind: Literal["target", "import", "sibling", "type_definition", "doc"]
    sha256: str                           # of the slice content, not the source file
    content: str                          # the actual text given to the Coder
    line_range: tuple[int, int] | None
```

### `VerificationPlan`

```python
@dataclass(frozen=True)
class VerificationPlan:
    required_checks: list[VerificationCheck]
    designer_review_required: bool
    architect_review_required: bool       # for re-plans after Verifier failure


@dataclass(frozen=True)
class VerificationCheck:
    id: str                               # "lint", "typecheck", "git_apply_check"
    command: list[str]                    # argv form
    blocking: bool                        # if false, surface as warning only
    timeout_seconds: int
```

### `PlanBudget`

```python
@dataclass(frozen=True)
class PlanBudget:
    max_coder_attempts: int               # default 3
    max_total_seconds: int                # default 120
    cloud_escalation_allowed: bool        # honors proxy's existing budget gate
```

### `CoderResponse` (the Coder's ONLY output shape)

```python
@dataclass(frozen=True)
class CoderResponse:
    status: Literal["ok", "blocked"]
    target_path: str                      # must equal packet.target_file.path
    replacement_content: str | None
    reasoning: str                        # ≤ 500 chars, audit log
    blocked_reason: str | None
    blocked_needed_context: str | None
```

The Coder produces this exact shape or fails. It does not generate diffs (the backend does), it does not parse targets (the packet does), it does not decide context (the Architect did), it does not check materiality (the Verifier does). It only chooses content.

---

## Phase 8: Workspace Hygiene and Deterministic Verification

The cheapest, highest-leverage work in the entire plan. Two of these increments don't require any new orchestration to ship value. Do them first.

### Increment 8.1: Exclude Proxy Source from Coder Context (with Mode Switching)

**Action:** Add two constants in `source_proxy/tasks/long_running.py`: `USER_APP_FORBIDDEN_PATHS` (path prefixes excluded when the user is working on app code) and `AGENT_INTERNAL_FORBIDDEN_PATHS` (excluded when the user is working on the agent itself). Specifically:

```python
USER_APP_FORBIDDEN_PATHS = (
    "source_proxy/", "src/components/coding/", "src/lib/coding/",
    "src/lib/spirit/apply-unified-diff.ts", "scripts/",
    "masterProxyPlan.md", "masterSwarmPlan.md", "notes.md",
)
AGENT_INTERNAL_FORBIDDEN_PATHS = (
    # When you're debugging the agent itself, exclude user-app noise instead.
    "src/app/", "src/components/dashboard/", "src/components/chat/",
    "public/", "backend/searxng_data/",
)

def derive_context_mode(target_path: str) -> Literal["user_app", "agent_internal"]:
    normalized = target_path.replace("\\", "/").lower()
    agent_prefixes = ("source_proxy/", "src/components/coding/",
                      "src/lib/coding/", "src/lib/spirit/apply-unified-diff.ts")
    return "agent_internal" if normalized.startswith(agent_prefixes) else "user_app"
```

Update `_rank_repomix_context_path` to accept a `context_mode` parameter and return a hard-negative score (`-10_000`) for any path matching the appropriate forbidden list. Then add the resolved forbidden list as a `forbidden_paths` field on the future `CoderPacket` (stub for now; Phase 9 wires it through). The mode is derived from the explicit target path, so debugging tasks on `source_proxy/decision/router.py` automatically flip into `agent_internal` mode without any user flag.

**Expected Outcome:** App tasks ("Improve `src/components/ThemeStrip.tsx`") get clean app-only context — no agent code leaks in. Agent tasks ("Fix the retry logic in `source_proxy/tasks/long_running.py`") get agent-only context with user-app noise excluded. The agent stops being confused about whether it's editing itself or the app, in both directions.

**Manual Checks:**
1. Run `repomix` against the workspace so a fresh `repomix-output.xml` exists.
2. **App task:** `spcurl $PROXY_URL/v1/decisions/prompt-packet -X POST -H 'Content-Type: application/json' -d '{"task":"Target file: src/components/ThemeStrip.tsx\nAdd a subtle hover state to the active swatch","wants_implementation":true}' | jq '.coder_packet.context_slices[].path'`
3. Expected output for app task: a list containing `src/components/ThemeStrip.tsx` (and siblings), but **zero entries** starting with `source_proxy/`, `src/components/coding/`, or `src/lib/coding/`.
4. **Agent task:** `spcurl $PROXY_URL/v1/decisions/prompt-packet -X POST -H 'Content-Type: application/json' -d '{"task":"Target file: source_proxy/decision/router.py\nFix the route classification for empty tasks","wants_implementation":true}' | jq '.coder_packet.context_slices[].path'`
5. Expected output for agent task: a list containing `source_proxy/decision/router.py` and adjacent proxy modules, but **zero entries** starting with `src/app/` or `src/components/dashboard/`.
6. Confirm the response includes `context_mode: "user_app"` or `context_mode: "agent_internal"` so the frontend can display which mode is active.

**Recommended Debugging:** If `source_proxy/...` paths still appear in user-app `context_slices`, the filter is being applied after slicing rather than before ranking. Check that `_rank_repomix_context_path` is called inside `_build_coder_repomix_context` *before* the `ranked = sorted(...)` step. If only some forbidden paths are filtered, the prefix matching is case-sensitive against a path that has Windows backslashes — normalize with `.replace("\\", "/").lower()` before comparing. If `derive_context_mode` returns the wrong mode, the agent-prefix check is too narrow or too wide; log the normalized target and the resolved mode together. If the filter is too aggressive and excludes the target itself, ensure the explicit-target path is added back to the candidate list with a maximum positive score AFTER the forbidden filter runs, regardless of mode.

**Next Steps:** Lock in the dual-source target parser before any more changes touch the explicit-target path.

---

### Increment 8.2: Backend Owns the Target Path, Frontend Consumes It

**Action:** In `source_proxy/decision/router.py` and the `/v1/decisions/route` endpoint, add a top-level `resolved_target: { path: str, exists: bool, source: "explicit_line" | "inferred" }` field on the `RouteDecision.as_payload()` output. Populate it from the existing `_parse_explicit_target_file_line` so the parser only runs in Python. Then update `src/components/coding/approval-gate-binding.ts` and `CodingAgentInterface.tsx` to **read** `decision.resolved_target.path` instead of calling `parseExplicitTargetFileLine` on the task text. Leave `parseExplicitTargetFileLine` in the frontend codebase but mark it `@deprecated` and add a runtime warning if it's invoked.

**Expected Outcome:** The explicit target path has exactly one parser. Frontend and backend cannot drift. The approval UI can no longer claim "you are editing X" while the backend generated a diff for Y. This eliminates a whole category of silent desync bugs that the current dual regex creates.

**Manual Checks:**
1. Submit a task in `/coding`: `Target file: "src/app/page.tsx"\nAdd a footer link to GitHub`.
2. Open browser devtools, watch the `/v1/decisions/route` response. Confirm `resolved_target.path === "src/app/page.tsx"` and `resolved_target.source === "explicit_line"`.
3. Confirm the approval gate header shows the same path.
4. In the JS console run `await import('@/lib/coding/explicit-task-target').then(m => console.warn(m.parseExplicitTargetFileLine.toString()))`. Confirm the deprecation comment is visible.

**Recommended Debugging:** If the frontend still hits the local parser, search the bundle for `parseExplicitTargetFileLine(` and confirm every call site now reads `decision.resolved_target.path`. If `resolved_target` is missing from the response, the `as_payload()` method on `RouteDecision` is using a stale dict literal — switch it to a dataclass-asdict pattern so new fields auto-propagate. If `exists: false` shows up for a file that obviously exists, the workspace root resolution is wrong; log `os.getcwd()` and `_workspace_root()` together to find the mismatch.

**Next Steps:** With target parsing centralized, the deterministic verification gate is the next quick win.

---

### Increment 8.3: Deterministic Pre-Approval Verification Gate (Tiered)

**Action:** Create `source_proxy/verification/deterministic.py` with a `run_deterministic_checks(diff: str, target_path: str, workspace_root: Path) -> DeterministicVerificationResult` function. It runs checks in **three tiers**, escalating only when needed. Tier 1 always runs; tier 2 runs only when tier 1 passes and TS/JS files changed; tier 3 runs only when changes touch declared types or exported symbols.

**Tier 1 — Always (target: < 2 seconds total):**
- `git apply --check` against the diff
- Per-file syntax parse (use `tree-sitter` or `node --check` for JS/TS, `python -m py_compile` for Python, `ruff check --select E9,F63,F7,F82 <target>` for Python error-only checks)

**Tier 2 — When TS/JS files changed and tier 1 passed (target: < 8 seconds):**
- `$ESLINT_CMD <target>` (see "Local Linter and Typecheck Commands" callout at top — substitute the verified command for your config shape)
- `npx tsc --noEmit --incremental --tsBuildInfoFile /tmp/spirit-tsbuild.json <target>` — file-scoped, uses on-disk incremental cache

**Tier 3 — When the diff touches `export`, `interface`, `type`, or `class` declarations (target: < 30 seconds):**
- `npx tsc --noEmit -p tsconfig.json` — full project typecheck, catches cross-file type breakage that file-scoped tsc misses

Run inside bubblewrap with a per-tier timeout (3s / 10s / 35s). Each check returns a structured result with stdout/stderr capped at 4 KB. Tier-1 failures block immediately; tier-2 failures block; tier-3 failures block but surface a clear "full project typecheck — slow path" hint in the UI. Wire this into the existing `preview_diff_verification` path so deterministic results land in the approval payload as `deterministic_checks: [{tier: 1|2|3, id, status, duration_ms, output}, ...]` before the human ever sees the gate.

**Expected Outcome:** The approval gate catches lint/typecheck/syntax failures before the user sees the diff. Common cases (small implementation diffs that don't touch types) complete in under 10 seconds. Type-graph-affecting changes pay the full-typecheck cost only when they earned it. No LLM is added to the loop. This is the single highest-value change in the plan.

**Manual Checks:**
1. **Tier-1 failure:** Submit a task: `Target file: src/app/page.tsx\nReplace the default export with a function named "Page" that returns <div>{unbalanced</div>`. Expected: red banner "Syntax check failed", tier-1 only, < 2 seconds elapsed.
2. **Tier-2 failure:** Submit: `Target file: src/app/page.tsx\nReplace the default export with a function named "Page" that returns <div>{undefinedVariable}</div>`. Expected: tier 1 passes, tier 2 fails on `typecheck` with the `tsc` error visible. Total elapsed < 12 seconds.
3. **Tier-3 escalation:** Submit a task that modifies an exported type, e.g.: `Target file: src/lib/types.ts\nAdd a "premium" variant to the UserTier type`. Expected: all three tiers run, the deterministic-checks panel shows three entries with a "full project typecheck — slow path" note on tier 3.
4. **Clean pass:** Submit a task that only changes JSX text content. Expected: tiers 1 and 2 pass, tier 3 skipped (no type-affecting changes), green panel.
5. Run `tail -f /tmp/source_proxy.log | grep deterministic` and confirm each tier logs its duration separately.

**Recommended Debugging:** If `git apply --check` fails for a diff that obviously matches the file, `_ensure_fresh_repomix` may have regenerated the bundle but the diff was generated against the old content — check the `bundle_sha256` against the on-disk hash. If `npx` errors with "command not found" inside bubblewrap, the shared-library mounts are incomplete; cross-reference `ldd $(which node)` against the readonly binds in `bubblewrap.py`. If tier-3 runs on every task even when no types changed, the heuristic detecting type-affecting changes is too broad — grep the diff for added lines matching `^\+\s*(export\s+)?(interface|type|class|enum|function\s+\w+\s*<)` only. If tier-2 incremental typecheck is somehow slower than tier-3 full typecheck, the `.tsbuildinfo` cache is being invalidated every run — confirm the path is writable and stable across invocations. If ESLint runs with the wrong config flavor (legacy vs flat), see the "Local Linter and Typecheck Commands" callout at the top and verify `$ESLINT_CMD` matches your repo's `eslint.config.*` shape.

**Next Steps:** Frontend can now stop inventing diffs entirely, since deterministic verification gives strong enough server-side signal.

---

### Increment 8.4: Frontend Synthetic-Diff Kill Switch

**Action:** Behind a feature flag `NEXT_PUBLIC_DISABLE_CLIENT_SYNTHETIC_DIFFS=1`, make `tryClientLocalCoderImplementationDiff` return `null` immediately. When `proposed_diff` is empty, render an explicit "Proxy returned no diff — re-run with cloud escalation?" state in the UI instead of synthesizing one. Default the flag ON in development. Once Phase 12 lands (frontend lockdown), delete the synthetic-diff functions entirely — but in 8.4 you only neutralize them.

**Expected Outcome:** The class of bugs where the frontend mints `--- /dev/null` patches against existing files is fully impossible when the flag is on. You can still flip it off if a regression in Phase 8.3 makes the gate too strict, so the change is reversible.

**Manual Checks:**
1. Set `NEXT_PUBLIC_DISABLE_CLIENT_SYNTHETIC_DIFFS=1` in `.env.local`. Restart Next.
2. Stop the source proxy entirely.
3. Submit a coding task in `/coding`. Expected: an explicit "Proxy unavailable — no implementation diff generated" message, never a populated approval gate.
4. With the proxy running, submit a task that returns `proposed_diff: ""`. Expected: a "Re-run with cloud?" prompt, not a synthetic diff.
5. Search the deployed bundle source for `newFileUnifiedDiff(` — confirm the function still exists in code but is never reached when the flag is on.

**Recommended Debugging:** If a synthetic diff still appears, search every call site of `tryClientLocalCoderImplementationDiff` and `buildDefaultNewPageTsx` — there may be a second code path that constructs `--- /dev/null` directly without going through the wrapped function. If the UI shows a blank approval gate instead of the new "Proxy unavailable" message, the conditional ordering is wrong; the synthetic-diff null-check must run before the "show approval" branch.

**Next Steps:** Phase 8 is complete. You now have a stable foundation with deterministic checks and no client diff invention. Begin Phase 9 to introduce the `ArchitectPlan` artifact.

---

## Phase 9: The ArchitectPlan Schema and Persistence

Phase 9 is plumbing. No new agent behavior, no LLM changes. You're adding a typed, persisted artifact that future phases populate and read.

### Increment 9.1: Dataclass Definitions and Serialization

**Action:** Create `source_proxy/planning/__init__.py` and `source_proxy/planning/plan.py` containing the seven frozen dataclasses defined in the keystone section: `ArchitectPlan`, `BundleSnapshot`, `TaskClassification`, `CoderPacket`, `TargetFile`, `AcceptanceCriterion`, `ContentConstraints`, `ContextSlice`, `VerificationPlan`, `VerificationCheck`, `PlanBudget`. Add `to_dict()` and `from_dict()` methods on `ArchitectPlan` that round-trip through JSON cleanly. Add `PLAN_SCHEMA_VERSION = 1` as a module-level constant. Write unit tests in `source_proxy/tests/test_architect_plan_schema.py` that cover empty plans, full plans, and rejection of unknown schema versions.

**Expected Outcome:** A typed, importable plan object that the rest of the codebase can begin referencing. No behavior change yet — this is purely the type system.

**Manual Checks:**
1. `cd source_proxy && pytest tests/test_architect_plan_schema.py -v`. Expected: 6+ passing tests including `test_roundtrip_full_plan`, `test_rejects_unknown_schema_version`, `test_coder_packet_target_path_normalized`.
2. From a Python REPL: `from source_proxy.planning.plan import ArchitectPlan, PLAN_SCHEMA_VERSION; print(PLAN_SCHEMA_VERSION)`. Expected: `1`.
3. Confirm `mypy source_proxy/planning/` reports zero errors.

**Recommended Debugging:** If round-trip serialization loses fields, you're using `dict(dataclass_instance)` rather than `dataclasses.asdict()` — only the latter recursively handles nested dataclasses. If `from_dict` accepts unknown keys silently, you forgot to validate against the declared field names; use `dataclasses.fields(cls)` to build an allow-list.

**Next Steps:** Persist plans to SQLite so they survive process restarts.

---

### Increment 9.2: SQLite Persistence with Schema Versioning

**Action:** Add an `architect_plan_json: str | None` column to the `long_running_tasks` table via a forward-only migration in `_initialize_store`. Store the JSON-serialized plan there, never as separate columns. Add `load_plan(task_id) -> ArchitectPlan | None` and `save_plan(task_id, plan) -> None` helpers in `source_proxy/planning/plan.py`. On load, check `plan["schema_version"]` against `PLAN_SCHEMA_VERSION` — if older, attempt registered migrators; if newer, raise `PlanSchemaTooNew`.

**Expected Outcome:** Plans persist across process restarts. A task started under one process version can be loaded by a newer process and migrated forward. The schema version is the only thing that ever needs to change to roll out plan-shape updates.

**Manual Checks:**
1. Start the proxy. Create a long-running task: `spcurl $PROXY_URL/v1/tasks/long-running -X POST -H 'Content-Type: application/json' -d '{"description":"Test plan persistence"}' | jq .task.id`. Save the returned id as `$TASK_ID`.
2. From a Python REPL while the proxy is running: `from source_proxy.planning.plan import save_plan, ArchitectPlan; save_plan("$TASK_ID", ArchitectPlan(plan_id="test", task_id="$TASK_ID", schema_version=1, ...))`.
3. Restart the proxy entirely.
4. `from source_proxy.planning.plan import load_plan; print(load_plan("$TASK_ID"))`. Expected: the full plan dataclass instance.
5. `sqlite3 data/long_running_tasks.sqlite3 "PRAGMA table_info(long_running_tasks);"`. Expected: a row showing `architect_plan_json TEXT`.

**Recommended Debugging:** If `load_plan` returns `None` for a task you just saved, the `_save_task` function is overwriting the row with stale field state — make sure plan persistence is written via its own column-targeted `UPDATE` rather than a wholesale row rewrite. If the migration crashes on existing tasks, `ALTER TABLE` may not be wrapped in `IF NOT EXISTS` semantics — wrap migrations in a `try/except OperationalError` that's idempotent.

**Next Steps:** Add an API endpoint so the frontend can see plans.

---

### Increment 9.3: Plan Retrieval API and Read-Only Frontend Panel

**Action:** Add `GET /v1/tasks/long-running/{task_id}/plan` returning the plan JSON or `404`. Stream the plan over the existing SSE channel as a `plan_updated` event whenever `save_plan` is called. In `CodingAgentInterface.tsx` add a collapsible "Architect Plan" panel that renders the plan when present. Render `target_file.path`, `classification.task_class`, `acceptance_criteria` (as a checklist), `verification_plan.required_checks` (as a list with status icons), and `budget`. Read-only — no edit affordances yet.

**Expected Outcome:** The user can see exactly what the system thinks it's going to do, before approving anything. This is the visibility piece that future phases depend on. Even with zero behavior change in the agents, just seeing the plan exposes confusion early.

**Manual Checks:**
1. Submit a task in `/coding`. Open the new "Architect Plan" panel — initially shows "no plan yet" because Phase 10 hasn't shipped.
2. From a Python REPL, manually `save_plan` for the active task with a hand-crafted plan. Watch the SSE event arrive in the browser devtools network tab. Confirm the panel auto-populates without a page refresh.
3. `spcurl $PROXY_URL/v1/tasks/long-running/$TASK_ID/plan | jq`. Expected: the JSON plan.

**Recommended Debugging:** If the SSE event fires but the panel doesn't update, the React reducer for plan state isn't keying off `task_id` — confirm the event handler scopes to the active task. If the API returns 404 for a task that exists, the route handler is hitting `_lookup_task` instead of `load_plan` — those are different lookups against different stores.

**Next Steps:** Phase 9 is complete. Now build the agent that produces these plans.

---

## Phase 10: The Real Architect Agent

The Architect agent's job is to convert a raw task string into a fully-populated `ArchitectPlan`. Increment 10.1 does this deterministically (no LLM) for the common case, which is the fastest path to real value. Increment 10.2 adds the LLM only for the residual hard cases.

### Increment 10.1: Deterministic Architect for Simple Cases

**Action:** In `source_proxy/planning/architect.py`, write `plan_task_deterministically(task: str, workspace_root: Path) -> DeterministicPlanResult`. The return type is a small union: `Plan(plan: ArchitectPlan)`, `FallthroughToLLM(reason: str)`, or `Block(reason: str)`. It returns `Plan` ONLY when: (a) the task contains an explicit `Target file:` line, (b) the target exists, (c) the task does not request a "new feature" or "new component" (heuristic: no occurrence of "create", "scaffold", "new page", "new module", "build from scratch"), and (d) the task is under 500 chars. Otherwise return `FallthroughToLLM` with a structured reason like `"no_explicit_target"`, `"target_missing"`, `"creation_task"`, or `"task_too_long"`. Wire this into `_run_architect_handoff` in `long_running.py`: if `Plan`, persist it and transition the task to `current_agent_role = "coder"`. If `FallthroughToLLM`, set `task.architect_status = "awaiting_llm"` with the reason, persist, and **do not** transition role. The deterministic Architect generates a `CoderPacket` with the target file slice, the immediate-imports slice (parsed via a tiny tree-sitter or simple regex pass over the target's import statements), and a `must_contain` derived from any quoted strings in the task.

**UX requirement:** The frontend Architect Plan panel must render `FallthroughToLLM` states explicitly. When `task.architect_status == "awaiting_llm"`, show a clear "Planning with LLM Architect..." spinner with the structured reason ("This task asks for new file creation — using LLM Architect"). Do not show an empty panel. Do not show "no plan available" with no explanation. The whole point of 10.1 is fast deterministic planning for simple cases; the secondary point is making the fall-through visible so users don't think the system is broken when their "create a new page" task takes longer.

**Expected Outcome:** Roughly 60–70% of your real implementation tasks ("Target file: X. Add Y.") never invoke an LLM Architect at all. They get a deterministic plan in under 50ms with no token cost. The remaining cases visibly fall through to 10.2 with a clear "why" message.

**Manual Checks:**
1. Submit: `Target file: src/components/Footer.tsx\nAdd a "Built with SpiritOS" line at the end`. Open the Architect Plan panel. Expected: a fully-populated plan in under 1 second, with `context_slices` containing `src/components/Footer.tsx`.
2. Submit: `Make the dashboard prettier`. Expected: the panel shows "Planning with LLM Architect — reason: no_explicit_target" and a spinner. **Not** an empty panel.
3. Submit: `Create a new page at src/app/billing/page.tsx that shows current usage`. Expected: panel shows "Planning with LLM Architect — reason: creation_task" and a spinner.
4. Submit: `Target file: src/components/DoesNotExist.tsx\nFix the rendering`. Expected: panel shows "Planning with LLM Architect — reason: target_missing" and a spinner.
5. Confirm the original happy-path plan from check 1 includes an `acceptance_criteria` entry with a literal criterion for "Built with SpiritOS" (since it was quoted in the task).

**Recommended Debugging:** If a deterministic plan is generated but `context_slices` is empty, the import-parsing regex isn't catching the target's imports — print the regex match against the file content and confirm at least the first 10 lines are scanned. If a task that should fall through is producing a plan anyway, the "new feature" detection heuristic is too narrow; widen it to include "build", "implement from scratch", "design", "scaffold". If the UI shows an empty Architect Plan panel instead of the fallthrough message, the panel's empty-state branch is checking `plan == null` rather than `task.architect_status`; switch the check to status-driven rendering.

**Next Steps:** Add the LLM Architect for the residual cases.

---

### Increment 10.2: LLM Architect with Strict JSON Output

**Action:** Add `plan_task_with_llm(task: str, workspace_root: Path, bundle: str) -> ArchitectPlan` in `source_proxy/planning/architect.py`. Use a dedicated `SOURCE_PROXY_ARCHITECT_MODEL_ALIAS` env var (default to the same alias as Coder if unset). Prompt the LLM with: (a) the bundle's file index (paths only, not contents), (b) the task, (c) the JSON schema for `CoderPacket` rendered inline, and (d) hard instructions that the response must be `CoderPacket` JSON only, no prose. Validate the response against the dataclass; on parse failure, retry once with the error appended. The Architect produces ONLY the `coder_packet` and `classification`; the surrounding `ArchitectPlan` wrapper (bundle snapshot, verification plan, budget) is added by the deterministic outer layer that calls into the LLM.

**Expected Outcome:** Vague tasks ("make the dashboard prettier") now produce a structured plan with a concrete target, even when the user didn't specify one. The Architect's only output shape is `CoderPacket` — every other field is owned by the deterministic wrapper. This keeps the LLM's surface area minimal and the failure modes contained.

**Manual Checks:**
1. Submit: `Make the dashboard prettier — focus on spacing and consistency`. Open the Architect Plan panel. Expected: within 5–15 seconds, a plan appears with a concrete `target_file.path` (likely something under `src/app/dashboard/` or a dashboard component), and at least one acceptance criterion describing the spacing change.
2. Submit a malformed task that the LLM might fumble: `do the thing`. Expected: the Architect either produces a plan with `classification.task_class = "explain"` and no target, OR blocks with `reason_code = "task_too_vague_for_plan"`. Either is fine; what's NOT fine is producing a plan with a hallucinated target file.
3. Run `tail -f /tmp/source_proxy.log | grep architect_llm`. Expected: per-task timing and token-count logs.

**Recommended Debugging:** If the LLM returns prose instead of JSON, the system prompt isn't strict enough — add "Your entire response must be a single JSON object. Do not include explanations, markdown fences, or any text before or after the JSON." If the JSON parses but fields are wrong types, the schema isn't included verbatim in the prompt — render the dataclass field list with types into the prompt template. If the Architect picks a target that doesn't exist, the bundle file-index isn't being passed; confirm `bundle` is non-empty in the prompt arguments.

**Next Steps:** Make the Coder enforce the bundle snapshot before reading anything.

---

### Increment 10.3: Bundle Snapshot Enforcement

**Action:** In `propose_coder_agent_implementation_diff` (still in its current form for now — Phase 11 rewrites it), add a precondition check: re-hash the on-disk repomix bundle and compare to `plan.bundle_snapshot.bundle_sha256`. If different, return a structured `bundle_snapshot_drift` block immediately. Surface this in the approval payload as `reason_code = "bundle_snapshot_drift"` with a UI affordance "Bundle changed since plan was created — regenerate plan?" Add a test in `test_coder_agent_repomix_diff.py` that hashes a bundle, mutates it, and asserts the Coder refuses.

**Expected Outcome:** "Patch does not apply" failures caused by stale repomix bundles become impossible. The system fails fast and visibly when the workspace drifts mid-task, with a clear remediation path (regenerate plan).

**Manual Checks:**
1. Submit a task, let the Architect plan run. Note the `bundle_snapshot.bundle_sha256` in the plan panel.
2. While the task is paused before approval, edit any source file (not the target) and save it. Wait 2 seconds for `_ensure_fresh_repomix` to potentially regenerate.
3. Trigger the Coder advance step. Expected: `reason_code = "bundle_snapshot_drift"` and a UI prompt to regenerate the plan.
4. Click "Regenerate plan." Expected: a fresh plan with a new `bundle_sha256`, Coder runs successfully.

**Recommended Debugging:** If snapshot drift isn't detected, the hash is being computed over a different byte range than what was hashed at plan time — log both `len(bundle_bytes)` and `bundle_sha256` at write and read time, they must match exactly. If the snapshot drifts on every run even without file changes, the bundle includes a timestamp or random ordering — pin repomix's output to deterministic ordering and exclude any timestamp headers.

**Next Steps:** Phase 10 is complete. Architects are real and produce strict, persisted, snapshot-bound plans. Time to make the Coder boring.

---

## Phase 11: Coder Decomposition

This is the structural rewrite. After Phase 11, `propose_coder_agent_implementation_diff` is under 80 lines and does one thing: ask the LLM for replacement content given a packet.

### Increment 11.1: Extract Materiality and Validation into a Shared Module

**Action:** Create `source_proxy/verification/contracts.py`. Move into it: `task_requests_subjective_improvement`, `_visual_diff_line_is_non_material`, `_visual_semantic_text`, `validate_replacement_content` (currently in `verification/diff.py`), the subjective-improvement reason code constants, and the visual-improvement constants. Update all import sites. Add unit tests covering each function in isolation. **Do not change behavior** — this is a pure refactor.

**Expected Outcome:** All the materiality/validation logic lives in one place, separate from the Coder. The Coder file shrinks. Future agents (Reviewer in Phase 13) can call the same module without depending on Coder internals.

**Manual Checks:**
1. `pytest source_proxy/tests/ -v`. Expected: full test suite still green. If any test imports moved, fix the import path but don't change assertions.
2. `grep -r "task_requests_subjective_improvement" source_proxy/` — should only appear in `verification/contracts.py` and import sites, never duplicated.
3. Count lines in `tasks/long_running.py` before and after. Expected: roughly 200–300 lines shorter.

**Recommended Debugging:** If a test fails after the move, the function had an implicit dependency on a module-level constant that wasn't moved with it — chase the import chain. If the diff is noisy in code review, you accidentally reformatted something; the rule for 11.1 is move-only, format changes go in a separate commit.

**Next Steps:** Now that gates are extracted, rewrite the Coder to consume only packets.

---

### Increment 11.2: Coder Consumes CoderPacket (with Compatibility Shim)

**Action:** Add a new function `propose_coder_agent_implementation_diff_from_packet(packet: CoderPacket, workspace_root: Path) -> CoderResponse` alongside the existing `propose_coder_agent_implementation_diff(task, workspace_root, ...)`. The new function: (a) renders the prompt from the packet's `context_slices`, `acceptance_criteria`, `constraints`, and `style_directives`; (b) calls the Coder LLM; (c) parses the response into `CoderResponse`; (d) validates `target_path` matches `packet.target_file.path`; (e) returns. Diff generation, materiality checks, and validation are done by the CALLER (the orchestrator in `long_running.py`), using the now-shared `verification/contracts` module from 11.1.

Then convert the **existing** `propose_coder_agent_implementation_diff(task, ...)` into a thin shim — roughly 15 lines — that builds a synthetic `CoderPacket` from the raw task (using the same regex helpers it always used) and delegates to `propose_coder_agent_implementation_diff_from_packet`. Mark the shim `@deprecated` with a comment pointing to 11.3 for removal. **Do not delete** `_parse_coder_explicit_target`, `_build_coder_repomix_context`, `_slice_coder_file_context`, or `_rank_repomix_context_path` yet — the shim still depends on them. They get deleted in 11.3 along with the shim itself.

**Expected Outcome:** Two code paths exist temporarily: packet-based (new, used by post-Phase-10 orchestrator code) and task-based (shim, used by anything that hasn't been migrated). Both produce identical output for the same task. The shim is small and visibly marked for deletion. If you have to stop work mid-phase for any reason, the system still functions on the old path.

**Manual Checks:**
1. `grep "def propose_coder_agent_implementation_diff" source_proxy/tasks/long_running.py` — expected: two function definitions, the original (now a shim) and the new `_from_packet` variant.
2. Run the full pytest suite. Expected: all existing tests still pass — they're hitting the shim, which delegates to the packet path.
3. **Equivalence test:** Write a new test in `test_coder_agent_repomix_diff.py` that builds the same task via both paths (raw task string vs hand-crafted `CoderPacket` with equivalent fields) and asserts the resulting `CoderResponse` is identical. Expected: pass.
4. Submit a normal task end-to-end via the UI. Expected: works exactly as before. Logs should show "coder_path=shim_to_packet" so you can see the shim is engaged.
5. Submit a task with a deliberately wrong-target packet via a direct call to `_from_packet`. Expected: `CoderResponse(status="blocked", blocked_reason="target_path_mismatch", ...)`.

**Recommended Debugging:** If shim output differs from packet output for the same task, the synthetic packet is missing fields the LLM relies on — diff the two generated prompts and find what's missing. If happy-path tasks now fail with "context too sparse," the synthetic packet's `context_slices` are too thin; the shim should reuse the existing `_build_coder_repomix_context` output verbatim until 11.3. If retries are happening externally now and looping, the orchestrator's retry counter isn't decrementing — it's tempting to bring retries back into the Coder; resist this and fix the orchestrator's state machine instead.

**Next Steps:** With both paths proven equivalent, delete the shim and lock the Coder's context boundary completely.

---

### Increment 11.3: Delete the Shim and Lock the Coder Boundary

**Action:** Remove the deprecated `propose_coder_agent_implementation_diff(task, ...)` shim entirely. Rename `propose_coder_agent_implementation_diff_from_packet` back to `propose_coder_agent_implementation_diff` (it's now the only one). Delete `_parse_coder_explicit_target`, `_build_coder_repomix_context`, `_slice_coder_file_context`, `_rank_repomix_context_path` from `tasks/long_running.py` — they belong in the Architect module (10.1) now, and any orchestrator code calling them should be routed through the packet path. Then in the renamed Coder function, remove every read of `repomix-output.xml`, `_extract_repomix_files`, and the workspace filesystem. The Coder may only read `packet.context_slices[*].content`. Add a guard: if `len(packet.context_slices) == 0`, return `blocked` with `reason_code = "coder_packet_missing_context"`. Verify each slice's `sha256` against its content on packet receipt; mismatch means a tampered packet.

**Expected Outcome:** The Coder has zero filesystem access. Its entire universe is the packet. The legacy task-string API no longer exists. This makes the Coder trivially auditable, trivially sandboxable, and immune to "the repomix is stale" bugs (because the bundle hash check happened in Phase 10.3, and the slices are content-addressed).

**Manual Checks:**
1. `grep -E "REPOMIX_BUNDLE_NAMES|_extract_repomix|read_text|read_bytes" source_proxy/tasks/long_running.py` — expected: no matches inside the Coder function. The matches that remain should be in the Architect's planning code or in the diff-generation post-step.
2. `grep "def _parse_coder_explicit_target\|def _build_coder_repomix_context\|def _slice_coder_file_context\|def _rank_repomix_context_path" source_proxy/tasks/long_running.py` — expected: no matches. They should now live in `source_proxy/planning/architect.py`.
3. `grep "propose_coder_agent_implementation_diff_from_packet" source_proxy/` — expected: no matches (the rename completed).
4. Run a normal task end-to-end. Expected: still works.
5. Submit a packet with a tampered `context_slices[0].content` (manually hex-edit a slice via a test fixture). Expected: `blocked` with `reason_code = "context_slice_hash_mismatch"`.
6. Run pytest. Expected: any test that called the old task-string signature has either been migrated to the packet signature or deleted.

**Recommended Debugging:** If the Coder still touches disk, it's likely through a helper imported from another module that itself reads — trace every transitive import. The principle: from the Coder function's stack, `os.open`, `Path.read_text`, and `Path.read_bytes` must never be called. If old tests fail because they used the task-string signature, migrate them to construct a synthetic `CoderPacket` in setup — don't restore the shim. If the rename causes import errors, your IDE missed a reference; `grep -r propose_coder_agent_implementation_diff` and update every site.

**Next Steps:** Phase 11 is complete. The Coder is boring. Frontend lockdown is next.

---

## Phase 12: Frontend Lockdown

The frontend stops being a place where implementation diffs are invented. It only displays what the backend produced.

### Increment 12.1: Delete the Synthetic Diff Pathway

**Action:** Remove `tryClientLocalCoderImplementationDiff`, `buildDefaultNewPageTsx`, `buildDefaultNewModuleTsx`, `buildDefaultNewTsModule`, `newFileUnifiedDiff`, `isClientSyntheticNewFileTargetBlocked`, and `shouldEmitClientLocalCoderDiff` from `CodingAgentInterface.tsx`. Remove the `NEXT_PUBLIC_DISABLE_CLIENT_SYNTHETIC_DIFFS` flag introduced in 8.4 — there's nothing left to disable. Add a single comment block at the top of the file: `// Implementation diffs are produced exclusively by the backend Coder. Never synthesize.`

**Expected Outcome:** It is structurally impossible for a frontend code path to create an implementation diff. The class of bugs that produced `--- /dev/null` patches for real files is fully eliminated.

**Manual Checks:**
1. `wc -l src/components/coding/CodingAgentInterface.tsx` — confirm the file is materially shorter (a few hundred lines removed).
2. Stop the proxy. Submit a task. Expected: "Proxy unavailable" message, no diff at all.
3. `grep -r "newFileUnifiedDiff\|buildDefaultNewPageTsx" src/` — expected: no matches.

**Recommended Debugging:** If anything in the bundle still references the deleted functions, you have a dead import — the TypeScript compiler should catch this; if it doesn't, the build cache is stale (`rm -rf .next && npm run build`).

**Next Steps:** Surface plan rejection reasons so users can act on them.

---

### Increment 12.2: Approval UI Shows Plan + Diff, Rejection Captures Reason

**Action:** Restructure the approval pane to show three stacked sections: (1) Architect Plan summary (target, acceptance criteria, verification checks with status icons), (2) Coder output (the diff, with the deterministic-check results inline), (3) Approve / Reject controls. The reject control opens a small picker with reason codes: `wrong_target`, `wrong_approach`, `missing_constraint`, `style_violation`, `other`. The reason is persisted to the task audit log and, if non-`other`, fed back to the Architect on regenerate.

**Expected Outcome:** Rejection is structured and useful. When you reject because the Architect picked the wrong file, the next Architect pass knows that — instead of repeating the mistake. The approval surface is the user's primary interaction point with the swarm; structured rejection turns it into a real feedback loop.

**Manual Checks:**
1. Submit a task. At the approval gate, click "Reject" → "wrong_target". Confirm a toast appears: "Plan will be regenerated with this feedback."
2. Watch the Architect Plan panel — expected: a new plan appears in 5–15 seconds, with a different target if applicable.
3. Open `data/approved_actions.audit.jsonl` and confirm rejection entries are present with the reason code.
4. Reject the second plan as well, with `wrong_approach`. Expected: the Architect produces a third attempt visibly different in approach.

**Recommended Debugging:** If rejection feedback doesn't reach the Architect, the regenerate path is calling `plan_task_with_llm` without the rejection history — pass it as an additional prompt section labeled "Previous attempts and why they were rejected." If the reason picker doesn't render, the rejection control is wired to the old single-click handler; replace with a dialog component.

**Next Steps:** Make role transitions visible.

---

### Increment 12.3: Visible Role Transitions in the SSE Stream

**Action:** Emit explicit `role_transition` SSE events with payload `{ from: SwarmAgentRole, to: SwarmAgentRole, reason: string }` whenever `current_agent_role` changes on the task. Render these as a horizontal pipeline at the top of `CodingAgentInterface.tsx`: `[architect] → [coder] → [verifier] → [approval]`, with the active stage highlighted and elapsed time per stage.

**Expected Outcome:** You can watch the swarm work in real time. When something goes wrong, you can see at a glance where in the pipeline it stalled. This turns the agent system from a black box into a debuggable pipeline.

**Manual Checks:**
1. Submit a task with the dev tools network tab open. Filter for `text/event-stream`. Expected: see `role_transition` events fire in order.
2. The UI pipeline updates as the events arrive. Each stage shows its elapsed time.
3. Force a Coder failure (e.g. set `SOURCE_PROXY_CODER_MODEL_ALIAS=does-not-exist`). Expected: pipeline highlights the Coder stage in red with the error message.

**Recommended Debugging:** If events fire but the pipeline doesn't update, the SSE client's reducer is keying on a stale task id — pass the active task id through the reducer's dependency array. If the events don't fire at all, the role transitions are happening inside a synchronous block that the SSE writer can't flush mid-execution; add an explicit flush after each role write.

**Next Steps:** Phase 12 is complete. The frontend is honest about what the backend did. Phase 13 adds the Reviewer agent on top.

---

## Phase 13: Reviewer Agent

The Reviewer runs AFTER the Coder, AFTER deterministic checks, BEFORE human approval. It catches style violations, security issues, performance smells — things deterministic tools miss. Reviewer is an LLM call, but its scope is intentionally narrow: it reviews the diff against the `acceptance_criteria` and `style_directives` and emits structured findings.

### Increment 13.1: Reviewer-as-Deterministic-Checks (No LLM Yet)

**Action:** In `source_proxy/planning/reviewer.py`, write `review_diff_deterministically(plan: ArchitectPlan, diff: str) -> ReviewReport`. It runs structured checks against the diff: every `must_contain` constraint is verified (case-sensitive), every `must_not_contain`, `max_added_lines`, `max_removed_lines`, `preserve_imports`, `preserve_exports`. For each acceptance criterion of `kind = "literal"`, it confirms the literal appears in the new content. The output is a `ReviewReport(passed: bool, findings: list[ReviewFinding])`. Wire this into the approval flow after deterministic verification but before the human gate.

**Expected Outcome:** The Reviewer catches "you forgot the import" or "you removed the export" before approval, deterministically. This handles 70%+ of style and contract violations with zero LLM cost.

**Manual Checks:**
1. Submit a task with `must_contain: ["GlassPanel"]` in the constraints (via a hand-crafted plan or via 10.2 producing one). Have the Coder produce a diff that omits `GlassPanel`. Expected: review fails with `finding.id = "missing_must_contain"`, `details = "GlassPanel"`.
2. Submit a task where `preserve_exports: ["default"]` and the Coder removes the default export. Expected: review fails with `finding.id = "exports_violated"`.

**Recommended Debugging:** If `must_contain` matches incorrectly (e.g. matches inside a comment), be explicit about whether the constraint is "in any context" or "in code only" — start with any-context and tighten later. If `preserve_imports` flags a false positive, the import name resolution isn't normalized (`import X from 'y'` vs `import {X} from 'y'`); use a tree-sitter pass instead of regex.

**Next Steps:** Add the LLM Reviewer for the residual style cases.

---

### Increment 13.2: LLM Reviewer for Subjective Quality

**Action:** Add `review_diff_with_llm(plan: ArchitectPlan, diff: str) -> ReviewReport` using a dedicated `SOURCE_PROXY_REVIEWER_MODEL_ALIAS` env var. The LLM is prompted with the diff and the `style_directives`, and must return a JSON `ReviewReport`. It runs ONLY when `plan.classification.task_class in ("implement", "refactor", "style")` and only when deterministic review passed (no point reviewing style on a broken diff). Findings are surfaced in the approval UI as advisory — they don't block approval, they inform it.

**Expected Outcome:** Subtle quality issues get flagged for human attention. Approval is faster because the user knows the safe parts have been pre-checked and only the subjective parts need their eye.

**Manual Checks:**
1. Submit a styling task with `style_directives: ["use Tailwind utility classes, no inline styles"]`. Have the Coder produce a diff with inline styles. Expected: Reviewer flags `style_directive_violation` with a snippet of the offending code.
2. Submit a clean task. Expected: Reviewer returns `passed: true` with zero findings, in ~3–8 seconds.
3. Confirm the approval UI shows reviewer findings as orange (advisory), not red (blocking).

**Recommended Debugging:** If the LLM Reviewer is too pedantic and flags every diff, the prompt is asking for "any improvements" rather than "violations of the listed directives" — tighten the prompt to "Report only findings that violate one of the listed `style_directives`." If it misses obvious violations, the prompt isn't showing the directives alongside the diff in proximity; restructure so directives appear immediately before the diff.

**Next Steps:** Phase 13 is complete. The swarm is now Architect → Coder → Deterministic Verifier → Reviewer → Approval. Designer agent (UI-specific) and Tester agent (autogenerated tests) are natural future additions on the same scaffolding.

---

## Cross-Cutting Concerns Not Tied to a Phase

A few items don't belong in a single increment but should be tracked throughout.

**Hardware budget on the RTX 3060:** Every LLM-bearing increment (10.2, 13.2) needs an explicit timeout and a fallback. If the Architect LLM takes >20 seconds, fall back to deterministic planning (10.1) with a degraded plan. If the Reviewer LLM takes >10 seconds, fall back to deterministic review only (13.1). Never let a slow LLM block the user indefinitely.

**Audit logging:** Every plan, every Coder response, every review report, every rejection lands in `data/approved_actions.audit.jsonl` with the task id, plan id, and timestamps. This is your debugging gold. Treat it as load-bearing: a missing audit entry is a P1 bug.

**Schema evolution:** When `PLAN_SCHEMA_VERSION` bumps, register a migrator in `source_proxy/planning/migrations.py` that takes a v(N) plan dict and returns a v(N+1) plan dict. Never break old plans — migrate them forward.

**Tests for the live path, not just units:** Phase 12.3 makes role transitions visible via SSE. Add at least one end-to-end test that submits a real task, watches the SSE stream, and asserts that all expected role transitions fire in order. This is the test that would have caught the original orchestration mess.

---

## Recommended Order of Operations

If you want to ship value as fast as possible:

1. **Phase 8 in full** (4 increments, ~2 days). This alone makes your workflow noticeably better with zero rewrite risk.
2. **Phase 9.1 and 9.2** (1 day). Plumbing only; nothing depends on it yet but everything will.
3. **Phase 10.1** (half day). Deterministic Architect handles your common case immediately.
4. **Phase 11.1** (half day). Pure refactor, makes everything else easier.
5. **Phase 9.3 + 12.3** (1 day together — both are UI visibility). Now you can SEE what's happening.
6. **Phase 10.2 + 10.3** (1–2 days). LLM Architect with snapshot enforcement.
7. **Phase 11.2** (half day). Coder packet path ships with shim — both paths work, low risk.
8. **Soak time** (1–3 days). Run real tasks. Confirm the equivalence test stays green. The shim is your safety net.
9. **Phase 11.3** (half day). Delete the shim once you're confident. This is the irreversible step — do it only after soak time.
10. **Phase 12.1 + 12.2** (1 day). Frontend lockdown.
11. **Phase 13 when time permits.** Reviewer is gravy on a working pipeline.

After Phase 8.3 alone, the system is materially better. After Phase 10.1, you have a real Architect. Everything past that is polish and structural insurance against the next class of bug.s
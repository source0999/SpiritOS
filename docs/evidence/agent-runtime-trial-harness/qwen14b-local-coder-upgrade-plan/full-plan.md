# Qwen2.5-Coder 14B Local Coder Upgrade Plan

## Purpose

Upgrade the local coding agent from Qwen2.5-Coder 7B to Qwen2.5-Coder 14B without increasing hidden risk, silent overbuilding, or false confidence.

The goal is not to make Qwen 14B “trusted.” The goal is to place Qwen 14B inside a small, enforceable, local-only pipeline where:

* simple static/isolated tasks can be attempted locally
* broad/auth/db/refactor tasks are blocked or narrowed
* model output is structurally constrained before diff display
* repair cannot rewrite logic
* Codex cannot self-approve progress
* every promotion level is earned through evidence

This plan favors fewer moving parts with stronger enforcement.

---

# Current State Diagnosis

The current 7B problem is mostly a protocol and control problem, not just a raw coding problem.

Qwen2.5-Coder 7B was asked to satisfy several things at once:

* understand the user’s messy natural-language task
* obey strict scope boundaries
* produce exact structured multi-file output
* stay inside allowed paths
* avoid scaffold/fallback contamination
* pass parser validation
* produce a usable diff
* fit the trial harness and reversible apply model

That is too much for a small local model to do reliably through a brittle JSON bundle contract.

Qwen2.5-Coder 14B may improve:

* instruction following
* code quality
* multi-file consistency
* repair success
* target retention
* fewer malformed bundles

But 14B will not automatically solve:

* scope creep
* silent overbuilding
* hidden fallback
* bad task classification
* invalid structured output
* visual/browser verification
* Codex continuing past gates
* accidental trust promotion

The system should treat 14B as a better local worker, not as a stronger authority.

---

# Core Design Principles

## 1. Keep the Safety Stack Small

The plan keeps only the layers that directly reduce real failure modes:

| Layer                                 |             Keep? | Reason                                          |
| ------------------------------------- | ----------------: | ----------------------------------------------- |
| Minimal external gate                 |               Yes | Prevents accidental Codex self-continuation     |
| Central gate-checking function        |               Yes | Prevents bypass through new scripts/routes      |
| Phi-4 Mini classifier                 | Yes, but fallible | Useful first-pass router, not trusted authority |
| Deterministic backend guard           |               Yes | Main scope-control mechanism                    |
| Local-friendly XML output format      |               Yes | Reduces brittle JSON failures                   |
| One-shot repair with similarity guard |               Yes | Prevents repair from rewriting logic            |
| Tiered checks                         |   Yes, simplified | Reduces manual fatigue                          |
| Complex supervisor daemon             |                No | Too much bootstrapping risk                     |
| Broad autonomous phase automation     |                No | Too risky for one human + Codex                 |

## 2. Backend Enforcement Beats Model Judgment

Phi and Qwen may classify or generate, but they do not enforce safety.

The backend must enforce:

* allowed paths
* file-count caps
* line-count caps
* forbidden keyword rejection
* provider/model route truth
* parser validation
* repair similarity
* apply eligibility
* preview-before-apply
* local-only proof fields

If a model says “safe” but backend rules say “unsafe,” the result is blocked.

## 3. All Model Calls Must Pass Through One Gate Function

Every current and future model-calling path must call one centralized gate-checking function before any model request is made.

This is non-negotiable.

Examples of paths that must use the centralized gate function:

* Phi classifier calls
* Qwen coder calls
* repair retry calls
* trial runner calls
* comparison/evaluation calls
* apply scripts
* future API routes that generate code
* future worker/background jobs that call models
* future CLI wrappers that call local or cloud models

No script, route, worker, test harness, or “temporary debug path” may implement its own separate gate check. Inline gate checks are not acceptable because they drift and become bypasses.

Required pattern:

```text
centralGateCheck(action, increment_id, run_id)
  → if approved: continue
  → if not approved: exit before model call
```

A future model path that does not use the centralized gate function is a security regression and must block the phase.

## 4. Phi-4 Mini Is a Fallible Classifier, Not a Judge

Phi-4 Mini is useful as a lightweight local pre-router, but small models often produce invalid structured output.

Therefore:

* Phi output is advisory until validated
* invalid Phi output does not call Qwen
* repeated invalid Phi output triggers a deterministic fallback classifier
* deterministic fallback may only allow narrow safe tasks
* unclear results become human review, not endless blocking

## 5. External Control Must Be Bootstrapped Safely

Codex building the thing that controls Codex is dangerous.

So the plan starts with a **human-created minimal gate file**, not a full supervisor system.

The first control mechanism is intentionally simple:

```text
.gate/state.json
.gate/README.md
npm run gate:status
npm run gate:approve -- 2.1
npm run gate:start -- 2.1
npm run gate:complete -- 2.1
npm run gate:block -- "reason"
```

Early phases are human-led. Codex may later improve the gate scripts, but only after the minimal gate already exists and is manually verified.

## 6. Manual Checks Must Be Tiered and Concrete

Not every passive action needs a hard stop. But anything that changes behavior, authority, model routing, parser behavior, repair behavior, or apply behavior does.

This plan uses two working tiers:

| Tier   | Name           | Meaning                                                           |
| ------ | -------------- | ----------------------------------------------------------------- |
| Tier 0 | Batch Check    | Passive inventory/evidence/doc work that can be reviewed together |
| Tier 1 | Hard Stop Gate | Any behavior-changing or authority-changing work                  |

Phase completion is always a hard stop.

## 7. No Silent Escalation

No OpenAI, Anthropic, DeepSeek, Gemini, Codex cloud, stronger local model, scaffold, or backend-generated content may count as local proof.

Escalation is allowed only as an explicitly approved comparison and must be labeled:

```text
local_proof=false
```

## 8. 14B Promotion Requires Metrics

Qwen 14B does not get promoted because it is bigger.

It must clear:

* parse success threshold
* low context dropping
* no severe overbuild behavior
* no hidden fallback
* local-only proof
* preview safety
* controlled apply/reverse proof if apply is authorized

If it fails, the plan forks decisively into one of two paths. No vague third option.

---

# Simplified Execution Architecture

## Local Coding Pipeline

```text
Human approval gate
  ↓
Centralized gate-checking function
  ↓
User request
  ↓
Phi-4 Mini classifier
  ↓
Validated TaskSpec or deterministic fallback
  ↓
Backend guard preflight
  ↓
Qwen2.5-Coder 14B
  ↓
Raw output guard
  ↓
Parser
  ↓
Optional one-shot repair
  ↓
Similarity guard
  ↓
Diff preview
  ↓
Human apply approval
  ↓
Cartographer safe apply / reverse
  ↓
Evidence receipt
```

## Model Roles

| Model             | Role                     | Authority                                     |
| ----------------- | ------------------------ | --------------------------------------------- |
| Phi-4 Mini        | Lightweight classifier   | May classify only                             |
| Qwen2.5-Coder 14B | Local coder              | May generate model-authored file content only |
| Qwen2.5-Coder 7B  | Baseline comparison      | No promotion authority                        |
| Cloud/API models  | Explicit comparison only | Never local proof                             |

---

# Minimal External Gate

## Why This Replaces the Full Supervisor

A full supervisor daemon is overkill and creates bootstrapping risk. The first version should be a dumb external gate that prevents accidental continuation.

The gate does not need to be clever. It only needs to ensure model calls and apply actions cannot run unless the human approved the exact increment.

## Required Gate Files

```text
.gate/state.json
.gate/README.md
scripts/gate-status.*
scripts/gate-approve.*
scripts/gate-start.*
scripts/gate-complete.*
scripts/gate-block.*
```

Implementation can be Node, shell, or Python. Keep it boring.

## Required `state.json` Fields

```json
{
  "status": "WAITING_FOR_HUMAN",
  "approved_increment": null,
  "last_completed_increment": null,
  "approval_token": null,
  "updated_at": null,
  "notes": ""
}
```

## Required States

| State                | Meaning                                  |
| -------------------- | ---------------------------------------- |
| `WAITING_FOR_HUMAN`  | Codex must stop                          |
| `APPROVED_INCREMENT` | One named increment may run              |
| `RUNNING_INCREMENT`  | Current increment is active              |
| `BLOCKED`            | Something failed or needs human decision |

No complex state machine is needed.

## Required Commands

| Command                          | Purpose                                                           |
| -------------------------------- | ----------------------------------------------------------------- |
| `npm run gate:status`            | Show current gate state                                           |
| `npm run gate:approve -- 2.1`    | Human approves one increment                                      |
| `npm run gate:start -- 2.1`      | Codex marks the approved increment as running                     |
| `npm run gate:complete -- 2.1`   | Codex marks increment complete and returns to `WAITING_FOR_HUMAN` |
| `npm run gate:block -- "reason"` | Codex or human blocks execution                                   |

## Central Gate Function Requirement

All model-call and apply paths must call the same central function before doing anything irreversible or model-driven.

Required behavior:

| Check                                                                             | Required Result                           |
| --------------------------------------------------------------------------------- | ----------------------------------------- |
| Gate missing                                                                      | Block                                     |
| Gate malformed                                                                    | Block                                     |
| Gate status not `APPROVED_INCREMENT` or `RUNNING_INCREMENT` for current increment | Block                                     |
| Approved increment does not match requested increment                             | Block                                     |
| Approval token missing or already consumed                                        | Block                                     |
| Action type not allowed for this increment                                        | Block                                     |
| Gate passes                                                                       | Continue and record gate state in receipt |

Any new script, route, worker, or test harness that calls a model without this function must fail review.

---

# Tier 0 vs Tier 1 Rules

## Tier 0: Batch Check

Tier 0 is allowed only when all of these are true:

* no source behavior changes
* no model-call path changes
* no route/default/provider changes
* no parser/repair/backend guard changes
* no apply/reverse behavior changes
* no trust-label/UI-status changes
* no commit, push, reset, stash, clean, or new worktree
* only docs/evidence/runbook files may be written
* any model smoke prompt is non-mutating and explicitly listed in the increment

Tier 0 examples:

| Example                                                                    | Why Tier 0                 |
| -------------------------------------------------------------------------- | -------------------------- |
| Record current git status, model inventory, and route map in evidence docs | Passive evidence only      |
| Run a Qwen 14B smoke prompt and record latency without parser/trial/apply  | Non-mutating runtime proof |
| Update runbook text explaining gate commands                               | Documentation only         |

Tier 0 still ends with the gate returning to `WAITING_FOR_HUMAN`.

## Tier 1: Hard Stop Gate

Tier 1 is required for anything that changes how the system behaves.

Tier 1 includes:

* any source code mutation outside docs/evidence/runbooks
* any centralized gate function change
* any model-call path change
* any provider route change
* any parser/output-format change
* any repair-loop change
* any backend caps/blacklist change
* any TaskSpec/Phi routing change
* any apply/reverse change
* any trial scoring change
* any UI/status label that affects trust or proof
* any script that can call a model
* any script that can apply files

Tier 1 examples:

| Example                                                    | Why Tier 1                                  |
| ---------------------------------------------------------- | ------------------------------------------- |
| Add `centralGateCheck()` to Source Proxy generation routes | Changes model-call authority                |
| Add XML parser support for Qwen output                     | Changes what model output can become a diff |
| Add blacklist rejection before diff display                | Changes backend safety behavior             |

Tier 1 always stops immediately after the increment and requires active human review.

---

# TaskSpec Classification

## Required Task Classes

Keep TaskSpec small.

| Task Class            | Meaning                                                      | Default Route             |
| --------------------- | ------------------------------------------------------------ | ------------------------- |
| `STATIC_SAFE`         | Tiny static/demo/docs-like output, max 2 files               | Local OK                  |
| `ISOLATED_EDIT`       | One isolated component/test/config edit, max 3 files         | Local OK                  |
| `BORDERLINE_REFACTOR` | Crosses more than 3 modules or unclear broad edit            | Human review / scale down |
| `BLOCKED_AUTH_DB`     | Auth, accounts, sessions, database, payments, secrets        | Block                     |
| `BLOCKED_EXTERNAL`    | External service, deployment, hardware, browser-only proof   | Block or human review     |
| `AMBIGUOUS`           | Target or scope unclear                                      | Block until clarified     |
| `ROUTER_INVALID`      | Phi output invalid twice and fallback cannot safely classify | Human review              |

## Required Phi Flags

Phi must return structured output with only these fields:

```json
{
  "task_class": "STATIC_SAFE",
  "requires_auth": false,
  "requires_db": false,
  "requires_external_service": false,
  "is_multi_file_refactor": false,
  "estimated_file_count": 1,
  "target_unclear": false,
  "route": "LOCAL_OK",
  "reason_codes": []
}
```

## Required Routing Rules

| Condition                        | Result                                |
| -------------------------------- | ------------------------------------- |
| `requires_auth=true`             | Block                                 |
| `requires_db=true`               | Block                                 |
| `requires_external_service=true` | Block or human review                 |
| `is_multi_file_refactor=true`    | Borderline; offer scale-down          |
| `estimated_file_count > 3`       | Borderline                            |
| `target_unclear=true`            | Block until clarified                 |
| `route=LOCAL_OK` and class safe  | Qwen may be called                    |
| invalid Phi output once          | Retry Phi once                        |
| invalid Phi output twice         | Use deterministic fallback classifier |
| deterministic fallback uncertain | Block for human                       |

---

# Phi Invalid Output Handling

Phi is expected to be useful but flaky. Invalid output is not a crisis.

## Invalid Output Flow

```text
Phi call #1 invalid
  ↓
Retry once with shorter schema prompt
  ↓
If valid: continue
  ↓
If invalid again: deterministic fallback classifier
  ↓
If fallback confidently returns STATIC_SAFE or ISOLATED_EDIT: continue
  ↓
Otherwise: block for human
```

## Deterministic Fallback Classifier

The fallback classifier is simple regex/rule logic. It is not another LLM.

It may allow only narrow, obvious tasks.

### Fallback May Return `STATIC_SAFE`

Only when all are true:

* request clearly asks for a static/demo/docs-like artifact
* expected output is 1–2 files
* no existing production app files are implied unless explicitly allowed
* no auth/db/external/deployment/server blacklist terms appear
* no broad refactor language appears
* target root is known and safe

Examples:

| Request                                                               | Fallback Result |
| --------------------------------------------------------------------- | --------------- |
| “make a tiny fake product site in the dummy fixture”                  | `STATIC_SAFE`   |
| “add a README note to this test fixture”                              | `STATIC_SAFE`   |
| “create a simple static HTML/CSS mock under the allowed trial folder” | `STATIC_SAFE`   |

### Fallback May Return `ISOLATED_EDIT`

Only when all are true:

* request names one known file, component, test, or config target
* expected change is local to that target
* estimated output is no more than 3 files
* no auth/db/external/deployment/server blacklist terms appear
* no broad refactor language appears
* target exists or is inside an allowed test/fixture root

Examples:

| Request                                            | Fallback Result                    |
| -------------------------------------------------- | ---------------------------------- |
| “change the button copy in `TrialRunnerPanel.tsx`” | `ISOLATED_EDIT` if path is allowed |
| “add one regression test for this parser case”     | `ISOLATED_EDIT`                    |
| “update this config label only”                    | `ISOLATED_EDIT`                    |

### Fallback Must Escalate to Human Review

Fallback must block or escalate when any are true:

* target file/root is unclear
* request says “make it production ready”
* request asks for login, accounts, users, sessions, database, payments, secrets, deployment, or external APIs
* request implies cross-route or cross-module refactor
* request would touch more than 3 files
* request requires browser/visual/hardware confirmation
* request depends on external service response
* fallback confidence is not obvious from deterministic rules

This avoids getting stuck on Phi invalid output while keeping fallback narrow and safe.

---

# Backend Structural Guard

The backend structural guard is the main anti-overbuild layer.

It runs after Qwen raw output but before diff display.

If it fails, no diff is shown.

## Caps

| Task Class            | Max Files | Max Added Lines | Max Modified Existing Files |
| --------------------- | --------: | --------------: | --------------------------: |
| `STATIC_SAFE`         |         2 |             150 | 0 unless explicitly allowed |
| `ISOLATED_EDIT`       |         3 |             300 |                           2 |
| `BORDERLINE_REFACTOR` |         0 |               0 |       0 until human narrows |
| `BLOCKED_AUTH_DB`     |         0 |               0 |                           0 |
| `BLOCKED_EXTERNAL`    |         0 |               0 |                           0 |
| `AMBIGUOUS`           |         0 |               0 |                           0 |
| `ROUTER_INVALID`      |         0 |               0 |                           0 |

## Blacklist

For local-safe tasks, raw output is rejected if it contains terms like:

```text
auth
login
logout
signup
register
account
session
jwt
oauth
password
bcrypt
lucia
nextauth
clerk
database
db
prisma
drizzle
migration
postgres
mysql
sqlite
mongodb
stripe
checkout
payment
billing
express
fastify
server.listen
middleware
.env
secret
api key
private key
deploy
vercel
dockerfile
```

False positives block. Human can reclassify or narrow later.

## Backend Guard Result Fields

Every receipt must include:

```text
task_class
route
file_count
added_line_count
modified_existing_file_count
caps_passed
caps_violation_reason
blacklist_passed
blacklist_matches
blocked_reason
diff_shown
apply_allowed
```

---

# Output Format and Repair

## Preferred Output Format

Use a simple XML-style format:

```xml
<file path="tests/ui-agent-trials/fixtures/dummy-product-site/index.html">
...
</file>
<file path="tests/ui-agent-trials/fixtures/dummy-product-site/styles.css">
...
</file>
```

Why:

* easier than strict JSON
* path is explicit
* parser can be deterministic
* model output remains model-authored
* backend does not invent content

## Repair Rules

One repair attempt is allowed only for formatting errors.

Allowed repair cases:

* missing closing tag
* malformed file tag
* markdown fence wrapper
* accidental prose outside file tags
* escaping issue

Not repairable:

* forbidden path
* blacklisted keyword
* too many files
* too many lines
* auth/db/external service content
* scope expansion
* missing required task target
* provider mismatch
* central gate failure
* local-proof mismatch

## Similarity Guard

Before accepting repaired output:

1. Extract code payload from original malformed output.
2. Extract code payload from repaired output.
3. Strip file markers and whitespace noise.
4. Compare character-count variance and/or Levenshtein similarity.
5. Fail closed if variance exceeds threshold.

Thresholds:

| Task Class      | Max Logic Variance |
| --------------- | -----------------: |
| `STATIC_SAFE`   |                 2% |
| `ISOLATED_EDIT` |                 5% |

If repair changes logic beyond the threshold:

```text
repair_status=failed_similarity_guard
diff_shown=false
apply_allowed=false
```

---

# Performance Fork

The plan has only two failure paths. There is no vague router pivot inside this plan.

## Metric Gate

After the 7B vs 14B comparison, stop and decide.

14B must meet:

| Metric                    |                      Required |
| ------------------------- | ----------------------------: |
| Parse success             | ≥ 85% on approved preview set |
| Severe context dropping   |                0 severe cases |
| Severe scope drift        |                0 severe cases |
| Hidden fallback           |                             0 |
| Backend-generated content |                             0 |
| Apply without approval    |                             0 |
| Gate bypass               |                             0 |

## If 14B Fails

Human must choose one of two concrete paths:

| Path   | Name                    | Meaning                                                                                                                        |
| ------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Path A | Ultra-Lean XML Contract | Keep 14B, but reduce output to one file per call using strict XML tags only. No multi-file output until it proves reliability. |
| Path B | Static Sandbox          | Keep 14B preview-only for static/demo/docs tasks. No apply eligibility. No production promotion.                               |

No third path is allowed in this upgrade plan.

A different model can be researched later in a separate plan.

---

# Phase 1: Human-Led Gate Bootstrap and Baseline Freeze

## Goal

Create the minimum external control mechanism before Codex is allowed to modify the model pipeline. Freeze the current baseline so later “improvements” cannot hide regression or fallback contamination.

## Success Criteria

| Criterion                         | Required Proof                                        |
| --------------------------------- | ----------------------------------------------------- |
| Minimal gate exists               | `.gate/state.json` and gate commands exist            |
| Gate starts closed                | Default state is `WAITING_FOR_HUMAN`                  |
| Central gate function required    | Model-call paths must use one central gate check      |
| Codex cannot self-approve by plan | Human approval command is required between increments |
| 7B baseline preserved             | Existing failure pattern is recorded honestly         |
| No model upgrade yet              | Qwen 14B is not promoted or defaulted                 |

## Increments

### 1.1 Human creates minimal gate files

**Tier:** Tier 1 Hard Stop Gate
**Owner:** Human-led, Codex may only provide commands or docs.

**What changes**

Create the minimal gate directory and scripts:

```text
.gate/state.json
scripts/gate-status
scripts/gate-approve
scripts/gate-start
scripts/gate-complete
scripts/gate-block
```

**Self-checks Codex can run**

* Verify files exist.
* Verify default state is `WAITING_FOR_HUMAN`.
* Verify approval can name exactly one increment.
* Verify completion returns to `WAITING_FOR_HUMAN`.

**Manual check required**

Human confirms they created or reviewed the gate and that Codex cannot proceed without a named approval.

**Gate**

Codex may continue only after human runs approval for Increment 1.2.

---

### 1.2 Baseline evidence batch

**Tier:** Tier 0 Batch Check

**What changes**

Record current state:

* current git status
* current Source Proxy route map
* current `/coding` runner state
* current local model inventory
* current 7B Coder failure evidence
* known scaffold/fallback status
* known dirty-tree caveats

Docs/evidence only.

**Self-checks Codex can run**

* `git status --short`
* local route/status inspection
* model list inspection
* evidence path inventory
* no source mutation except evidence docs

**Manual check required**

Human verifies the baseline describes the real failure: local Qwen was reached, scaffold/fallback did not pass, but output protocol failed.

**Gate**

Continue only after human approval.

---

### 1.3 Central gate function and model-call wrapper

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Create one centralized gate-checking function and require every model-call/apply path to use it.

It must cover:

* Phi calls
* Qwen calls
* repair calls
* trial generation calls
* comparison calls
* apply calls
* future scripts/routes/workers that call models

No duplicate inline gate logic.

**Self-checks Codex can run**

* Attempt model-call script while gate is closed; expect fail.
* Approve a dummy increment; expect only that increment can run.
* Complete increment; verify gate closes again.
* Search for known model-call entry points and confirm they call the centralized function.
* Add a regression test or static check for model-call paths bypassing the central function where practical.

**Manual check required**

Human verifies the gate actually blocks model calls and that future paths are required to use the centralized function.

**Gate**

Continue only after human approval.

---

### 1.4 Tier rules documented

**Tier:** Tier 0 Batch Check

**What changes**

Document the Tier 0 allow-list and Tier 1 hard-stop list in the operator runbook.

**Self-checks Codex can run**

* Docs contain explicit Tier 0 allow-list.
* Docs contain explicit Tier 1 hard-stop list.
* Docs include at least 2–3 examples for each tier.
* Docs state phase completion always stops.

**Manual check required**

Human verifies the tier rules are understandable and not vague.

**Gate**

Phase 1 complete only after human approval.

---

## Phase Completion Gate

Human must verify:

* Gate exists before model pipeline work begins.
* Gate starts closed.
* All model-call/apply paths must use the centralized gate-checking function.
* Gate blocks model calls.
* Baseline is frozen.
* Tier 0 vs Tier 1 is clear enough to use.

---

# Phase 2: Local Model Inventory and Safe 14B/Phi Activation

## Goal

Install or confirm Qwen2.5-Coder 14B and Phi-4 Mini locally without changing production defaults or granting authority.

## Success Criteria

| Criterion              | Required Proof                                              |
| ---------------------- | ----------------------------------------------------------- |
| Qwen 14B available     | Local inventory shows model                                 |
| Phi available          | Local inventory shows model or approved local equivalent    |
| Neither is default yet | Existing route remains unchanged unless explicitly approved |
| Route truth visible    | Requested model and resolved model are shown                |
| Missing model blocks   | No fallback if either model is missing                      |
| Gate enforced          | Smoke probes run only through approved gated paths          |

## Increments

### 2.1 Local model inventory batch

**Tier:** Tier 0 Batch Check unless installation is required; Tier 1 if installation mutates system state

**What changes**

Inventory current local models and confirm whether Qwen 14B and Phi-4 Mini/equivalent are present.

If install is required, stop and ask before install.

**Self-checks Codex can run**

* model list
* disk space check
* current default route check
* no route mutation
* no model deletion

**Manual check required**

Human confirms model inventory and approves any install separately.

**Gate**

Continue only after human approval.

---

### 2.2 Qwen 14B smoke probe

**Tier:** Tier 0 Batch Check

**What changes**

Run a non-mutating local prompt through Qwen 14B.

No trial. No parser. No apply.

**Self-checks Codex can run**

* central gate check passed
* provider is local
* resolved model is Qwen 14B
* response returns
* latency/timeout recorded
* no files changed except evidence

**Manual check required**

Human verifies the machine remains stable and the output is local.

**Gate**

Continue only after human approval.

---

### 2.3 Phi smoke probe with invalid-output test

**Tier:** Tier 0 Batch Check

**What changes**

Run Phi through a simple structured classification prompt and one intentionally tricky prompt.

Record:

* valid structured output rate
* invalid output behavior
* retry behavior if available manually
* proof that Qwen is not called after invalid Phi output

**Self-checks Codex can run**

* central gate check passed
* parse result recorded
* invalid output captured
* no Qwen call after invalid Phi result

**Manual check required**

Human verifies Phi is treated as fallible and does not become a trusted judge.

**Gate**

Continue only after human approval.

---

### 2.4 Route truth surface

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Expose model role and route truth:

```text
router_model
coder_model
requested_model
resolved_model
provider
fallback_used
local_proof
gate_status
```

**Self-checks Codex can run**

* status endpoint or UI shows requested/resolved model
* missing model blocks
* no cloud fallback
* no scaffold fallback
* route truth appears in receipt/status

**Manual check required**

Human verifies the UI/API cannot confuse Phi router with Qwen coder.

**Gate**

Phase 2 complete only after human approval.

---

## Phase Completion Gate

Human must verify:

* Qwen 14B is available but not blindly trusted.
* Phi is available but treated as fallible.
* Missing model routes block.
* Route truth is visible.
* Gate truth is visible.
* No default authority increased.

---

# Phase 3: TaskSpec Router and Deterministic Backend Guard

## Goal

Create the minimum reliable routing and scope-control system: Phi classifies, deterministic fallback handles Phi invalid output, and backend caps/blacklist prevent overbuild before diff preview.

## Success Criteria

| Criterion              | Required Proof                                     |
| ---------------------- | -------------------------------------------------- |
| Phi schema exists      | Structured classification schema is implemented    |
| Invalid Phi handled    | One retry, then deterministic fallback or block    |
| Auth/db blocks         | Auth/database requests never reach Qwen            |
| Refactors borderlined  | >3-module refactors trigger scale-down             |
| Static/isolated passes | Safe small tasks may reach Qwen                    |
| Backend guard enforced | Caps/blacklist reject before diff display          |
| Gate remains central   | Router/coder calls still use central gate function |

## Increments

### 3.1 Minimal TaskSpec schema

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Implement the small TaskSpec schema:

```text
STATIC_SAFE
ISOLATED_EDIT
BORDERLINE_REFACTOR
BLOCKED_AUTH_DB
BLOCKED_EXTERNAL
AMBIGUOUS
ROUTER_INVALID
```

Required flags:

```text
requires_auth
requires_db
requires_external_service
is_multi_file_refactor
estimated_file_count
target_unclear
route
reason_codes
```

**Self-checks Codex can run**

* schema validation tests
* invalid fields rejected
* prose output rejected
* missing required fields rejected

**Manual check required**

Human verifies the schema is small enough to maintain.

**Gate**

Continue only after human approval.

---

### 3.2 Phi router with practical invalid-output fallback

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Implement:

```text
Phi attempt 1
  → if invalid, retry once with shorter prompt
  → if invalid again, deterministic fallback classifier
  → if fallback uncertain, block for human
```

Fallback may only allow:

* obvious static/demo/docs task
* obvious one-file isolated edit

Everything else blocks.

**Self-checks Codex can run**

* valid Phi output routes correctly
* invalid once then valid works
* invalid twice falls back
* fallback allows obvious static-safe fixture task
* fallback allows obvious single-file isolated edit
* fallback blocks auth/db/refactor
* fallback never routes broad ambiguous task to Qwen

**Manual check required**

Human reviews invalid-output cases and confirms the system does not get stuck forever or pass unsafe tasks.

**Gate**

Continue only after human approval.

---

### 3.3 Backend caps

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Add caps by TaskSpec:

```text
STATIC_SAFE: max 2 files, max +150 lines
ISOLATED_EDIT: max 3 files, max +300 lines, max 2 existing files
Everything else: no Qwen or no diff unless narrowed
```

**Self-checks Codex can run**

* output with 3 files for STATIC_SAFE rejects
* output with +151 lines for STATIC_SAFE rejects
* output with 4 files for ISOLATED_EDIT rejects
* rejected output does not show diff
* receipt records cap violation reason

**Manual check required**

Human verifies caps are strict enough to prevent “tiny site becomes app platform.”

**Gate**

Continue only after human approval.

---

### 3.4 Backend blacklist

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Add raw-output keyword rejection for local-safe tasks.

Blacklist categories:

* auth/accounts/session/password
* database/ORM/migration
* payments/billing
* server/backend expansion
* secrets/env/API keys
* deployment/CI/Docker/Vercel

**Self-checks Codex can run**

* each category triggers rejection
* rejection happens before parser/diff
* receipt records matched term/category
* false positives block rather than pass

**Manual check required**

Human verifies blacklisted overbuild never reaches diff preview.

**Gate**

Continue only after human approval.

---

### 3.5 Scale-down options for borderline tasks

**Tier:** Tier 1 Hard Stop Gate

**What changes**

For `BORDERLINE_REFACTOR`, return only predefined options:

```text
one_file_only
one_component_only
static_mock_only
test_only
docs_plan_only
ask_for_target
```

Do not call Qwen until human selects or rewrites the task.

**Self-checks Codex can run**

* 4-module refactor produces scale-down options
* broad “make it production ready” blocks
* auth/db still blocks, not scale-downs silently
* selected scale-down re-enters classification
* scale-down option appears in receipt/status

**Manual check required**

Human verifies scale-down options are useful and not evasive.

**Gate**

Phase 3 complete only after human approval.

---

## Phase Completion Gate

Human must verify:

* Phi invalid output is handled practically.
* Deterministic fallback is narrow but not useless.
* Auth/db blocks before Qwen.
* Backend caps and blacklist reject before diff.
* Borderline tasks are narrowed instead of guessed.
* No Qwen call can bypass the centralized gate.

---

# Phase 4: Local-Friendly Output Contract and Repair Guard

## Goal

Replace brittle JSON bundle dependence with a simpler XML file format and add one repair attempt that cannot rewrite logic.

## Success Criteria

| Criterion                       | Required Proof                                       |
| ------------------------------- | ---------------------------------------------------- |
| XML file format works           | Parser accepts valid file tags                       |
| JSON is not required            | Qwen can use simpler output                          |
| Backend does not invent content | Parsed content comes only from model output          |
| Repair is bounded               | One attempt only                                     |
| Similarity guard works          | Repair cannot rewrite logic                          |
| Unsafe output not repairable    | Caps/blacklist/path violations fail closed           |
| Gate still enforced             | Parser/repair model calls cannot bypass central gate |

## Increments

### 4.1 XML file output parser

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Add parser for:

```xml
<file path="...">
content
</file>
```

Rules:

* no paths outside allowed root
* no duplicate paths
* no empty path
* no protected path
* no backend-created missing content
* no markdown explanation accepted as proof

**Self-checks Codex can run**

* valid one-file parse
* valid two-file parse
* duplicate path reject
* outside path reject
* protected path reject
* malformed tag reject
* parser failure records receipt fields

**Manual check required**

Human reviews raw output and parsed result side-by-side.

**Gate**

Continue only after approval.

---

### 4.2 Qwen output prompt update

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Update Qwen coder prompt:

* smallest sufficient implementation
* obey TaskSpec
* use XML file tags only
* no markdown wrapper
* no unasked features
* no auth/db/payments/deployment unless explicitly allowed, which local-safe tasks never allow

**Self-checks Codex can run**

* prompt snapshot
* no wording encouraging “production-ready” expansion
* no cloud fallback language
* no self-approval language
* output format instruction is unambiguous

**Manual check required**

Human reviews exact prompt wording.

**Gate**

Continue only after approval.

---

### 4.3 One-shot repair loop

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Add one repair attempt only for format errors.

Repair cannot run for:

* central gate failure
* blacklisted output
* cap violations
* forbidden paths
* wrong task class
* provider mismatch
* scope expansion
* local-proof mismatch

**Self-checks Codex can run**

* malformed XML repaired once
* second repair attempt blocked
* unsafe output not repairable
* repair uses same local model unless explicitly approved otherwise
* repair receipt records original parse error and final status

**Manual check required**

Human verifies repair cannot launder unsafe output.

**Gate**

Continue only after approval.

---

### 4.4 Similarity guard

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Compare original malformed payload to repaired payload.

Thresholds:

```text
STATIC_SAFE: max 2% logic variance
ISOLATED_EDIT: max 5% logic variance
```

Fail closed if exceeded.

**Self-checks Codex can run**

* closing-tag-only repair passes
* changed button copy over threshold fails
* added new file fails
* added auth/login term fails
* repaired output with changed logic fails
* receipt records similarity score and threshold

**Manual check required**

Human reviews original vs repaired sample evidence.

**Gate**

Phase 4 complete only after approval.

---

## Phase Completion Gate

Human must verify:

* XML format is simpler than strict JSON.
* Parser is conservative.
* Repair is one-shot.
* Similarity guard blocks logic rewrite.
* Backend still rejects unsafe output before diff.
* Repair cannot bypass the centralized gate.

---

# Phase 5: 7B vs 14B Trial Harness and Performance Fork

## Goal

Evaluate 14B honestly against 7B using the new router, guard, XML format, and repair logic. Decide whether 14B can progress to controlled preview/apply or must be constrained.

## Success Criteria

| Criterion                   | Required Proof                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------- |
| Separate 14B lane exists    | 14B results are not mixed with 7B/cloud                                            |
| Preview-only trial set runs | No apply during evaluation                                                         |
| Metrics recorded            | parse success, repair rate, context dropping, scope drift, caps/blacklist failures |
| Traps included              | auth, db, refactor, wrong-path, ambiguous, no-op                                   |
| Gate is tested              | Evaluation cannot run while gate is closed                                         |
| Performance fork enforced   | If metrics fail, choose Path A or Path B                                           |

## Increments

### 5.1 Trial profile and receipt schema

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Create 14B local trial profile:

```text
gate → Phi/fallback → backend preflight → Qwen 14B → raw guard → parser → repair/similarity → preview
```

Receipt fields:

```text
router_model
coder_model
task_class
route
fallback_classifier_used
caps_passed
blacklist_passed
parse_status
repair_status
similarity_score
context_drop_flag
scope_drift_flag
local_proof
diff_shown
apply_allowed
```

**Self-checks Codex can run**

* receipt populated for pass
* receipt populated for block
* receipt populated for invalid Phi
* receipt populated for repair fail
* apply not allowed during evaluation
* trial cannot run with gate closed

**Manual check required**

Human verifies receipts are auditable.

**Gate**

Continue only after approval.

---

### 5.2 Prompt set approval batch

**Tier:** Tier 0 Batch Check

**What changes**

Prepare small prompt set:

| Prompt Type             | Purpose              |
| ----------------------- | -------------------- |
| tiny static site        | normal safe task     |
| isolated component edit | normal safe edit     |
| test-only task          | local-safe test      |
| docs/config task        | passive-safe task    |
| auth trap               | should block         |
| db trap                 | should block         |
| 4-module refactor       | should borderline    |
| wrong-path trap         | should block         |
| ambiguous target        | should block         |
| no-op honesty           | should say no change |

No model run yet.

**Self-checks Codex can run**

* each prompt has expected route
* no broad benchmark
* no apply mode
* no hidden cloud/provider comparison

**Manual check required**

Human approves prompt set before execution.

**Gate**

Continue only after approval.

---

### 5.3 7B vs 14B preview comparison

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Run approved set in preview-only mode through both 7B and 14B, using the same routing and backend guard.

Record:

* parse success
* repair needed
* similarity failures
* context dropping
* scope drift
* caps/blacklist hits
* wrong files
* blocked tasks handled correctly
* gate status
* local proof status

**Self-checks Codex can run**

* no apply
* no scaffold
* no fallback
* local provider only
* both models identified correctly
* no run starts with gate closed

**Manual check required**

Human reviews comparison summary and samples.

**Gate**

Continue only after approval.

---

### 5.4 Performance fork decision

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Apply metric gate.

14B must meet:

```text
parse_success >= 85%
severe_context_drops = 0
severe_scope_drift = 0
hidden_fallback = 0
backend_generated_content = 0
gate_bypass = 0
```

If it passes, continue.

If it fails, human must choose:

| Path                   | Decision                                                   |
| ---------------------- | ---------------------------------------------------------- |
| Path A: Ultra-Lean XML | one file per call, stricter caps, no multi-file generation |
| Path B: Static Sandbox | preview-only forever for static/demo/docs tasks            |

**Self-checks Codex can run**

* metrics calculated
* fork recommendation generated
* no invented third path
* decision recorded in evidence

**Manual check required**

Human chooses pass, Path A, or Path B.

**Gate**

Phase 5 complete only after human decision.

---

## Phase Completion Gate

Human must verify:

* 14B passed objective metrics or was constrained.
* No vague pivot remains.
* Next phase matches the chosen decision.
* 14B is still not called trusted or production-ready.

---

# Phase 6: Controlled Preview, Apply, and Reverse

## Goal

If allowed by Phase 5, prove that 14B can safely move from preview to one controlled reversible apply for low-risk tasks only.

If Phase 5 selected Path B, this phase becomes documentation-only and no apply is attempted.

## Success Criteria

| Criterion                            | Required Proof                                   |
| ------------------------------------ | ------------------------------------------------ |
| Apply eligibility is narrow          | Only safe TaskSpec classes may apply             |
| Human approval binds to exact output | Apply token tied to run ID/output hash/file list |
| Reverse works                        | Approved change can be cleanly reverted          |
| Unexpected delta blocks              | Any extra file/change fails                      |
| Gate controls apply                  | Apply path cannot run while gate is closed       |
| Path B respected                     | Static Sandbox never applies                     |

## Increments

### 6.1 Apply eligibility contract

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Define apply eligibility:

| Task Class            | Apply Eligibility                    |
| --------------------- | ------------------------------------ |
| `STATIC_SAFE`         | Eligible only after preview approval |
| `ISOLATED_EDIT`       | Eligible only after preview approval |
| `BORDERLINE_REFACTOR` | Not eligible                         |
| `BLOCKED_AUTH_DB`     | Not eligible                         |
| `BLOCKED_EXTERNAL`    | Not eligible                         |
| `AMBIGUOUS`           | Not eligible                         |
| `ROUTER_INVALID`      | Not eligible                         |

If Path B was chosen, all classes are preview-only.

**Self-checks Codex can run**

* ineligible classes cannot apply
* Path B disables apply
* apply requires run-specific approval
* apply path checks centralized gate

**Manual check required**

Human verifies apply eligibility is narrow.

**Gate**

Continue only after approval.

---

### 6.2 Preview approval binding

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Approval for apply must bind to:

```text
run_id
model
output_hash
parsed_file_list
caps_result
blacklist_result
repair_status
similarity_score
gate_token
```

If anything changes, approval is invalid.

**Self-checks Codex can run**

* stale approval rejected
* changed output rejected
* changed file list rejected
* changed model rejected
* reused token rejected
* gate-closed apply rejected

**Manual check required**

Human verifies approval cannot be reused.

**Gate**

Continue only after approval.

---

### 6.3 First reversible apply trial

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Run one approved low-risk fixture task through:

```text
gate
classification
backend guard
Qwen
raw guard
parser
preview
human approval
apply
verify
reverse
```

**Self-checks Codex can run**

* applied files match parsed output
* no unexpected files
* reverse restores fixture state
* receipt includes apply/reverse proof
* final fixture state is clean or expected

**Manual check required**

Human inspects created result and reverse result.

**Gate**

Continue only after approval.

---

### 6.4 Repeatability micro-run

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Run a tiny repeatability set, still low-risk and reversible.

Do not run broad suites.

**Self-checks Codex can run**

* consistency summary
* parse rate
* repair rate
* cap/blacklist blocks
* reverse proof
* gate proof

**Manual check required**

Human decides operating level.

**Gate**

Phase 6 complete only after human selects operating level.

---

## Phase Completion Gate

Human chooses one operating level:

| Level                    | Meaning                                           |
| ------------------------ | ------------------------------------------------- |
| `NO_GO`                  | 14B should not be used                            |
| `PREVIEW_ONLY`           | 14B may produce previews but never apply          |
| `STATIC_SAFE_APPLY_ONLY` | 14B may apply approved static-safe tasks only     |
| `ISOLATED_APPLY_ONLY`    | 14B may apply approved static/isolated tasks only |

No broader autonomy level exists in this plan.

---

# Phase 7: Runbooks, UI Truth, Rollback, and Final Decision

## Goal

Make the final system understandable and operable by one human without relying on memory, vibes, or hidden assumptions.

## Success Criteria

| Criterion                    | Required Proof                                                            |
| ---------------------------- | ------------------------------------------------------------------------- |
| Operator runbook exists      | Human can run gate, preview, approve, apply, reverse, block               |
| Central gate rule documented | All future model-call paths must use the central gate function            |
| Rollback exists              | 14B/Phi route can be disabled safely                                      |
| UI truth visible             | `/coding` shows local proof, model, route, gate, task class, guard status |
| Evidence chain complete      | Baseline through final decision is linked                                 |
| Final decision explicit      | Operating level is named and limited                                      |

## Increments

### 7.1 Operator runbook

**Tier:** Tier 0 Batch Check

**What changes**

Document:

* gate commands
* centralized gate-checking rule
* how to approve next increment
* how to run preview
* how to read TaskSpec
* how to read caps/blacklist result
* how to approve apply
* how to reverse
* how to block
* what each operating level means

**Self-checks Codex can run**

* runbook references real commands
* no destructive commands
* no claim of autonomy
* no claim of production trust
* future model-call paths must use central gate function

**Manual check required**

Human follows the runbook for one preview path.

**Gate**

Continue only after approval.

---

### 7.2 Rollback and disable plan

**Tier:** Tier 0 Batch Check

**What changes**

Document how to:

* disable Qwen 14B route
* disable Phi classifier
* force preview-only
* restore prior local route
* block all local coding
* preserve model files without deleting them

**Self-checks Codex can run**

* rollback docs avoid destructive deletion
* route disable is clear
* preview-only fallback is clear
* gate can force all coding blocked

**Manual check required**

Human verifies rollback is safe.

**Gate**

Continue only after approval.

---

### 7.3 UI/operator truth surface

**Tier:** Tier 1 Hard Stop Gate

**What changes**

Ensure the operator UI/status surface shows:

```text
gate_state
approved_increment
router_model
coder_model
requested_model
resolved_model
task_class
route
fallback_classifier_used
caps_passed
blacklist_passed
blacklist_matches
parse_status
repair_status
similarity_score
local_proof
diff_shown
apply_allowed
operating_level
final_trust_status
```

**Self-checks Codex can run**

* status tests for blocked
* status tests for preview-only
* status tests for apply-eligible
* status tests for non-local comparison
* no ambiguous “passed” label when blocked or preview-only
* gate state displayed for every coding run

**Manual check required**

Human visually verifies the UI/status surface.

**Gate**

Continue only after approval.

---

### 7.4 Evidence index

**Tier:** Tier 0 Batch Check

**What changes**

Create final evidence index linking:

* Phase 1 gate bootstrap
* central gate function proof
* baseline freeze
* model inventory
* Phi invalid-output behavior
* deterministic fallback behavior
* backend caps tests
* blacklist tests
* XML parser tests
* repair similarity tests
* 7B vs 14B comparison
* performance fork decision
* apply/reverse proof if any
* final operating level

**Self-checks Codex can run**

* all evidence files exist
* links/paths are accurate
* no missing claimed proof
* no local-proof claim lacks receipt support

**Manual check required**

Human verifies evidence can be handed to a new chat.

**Gate**

Continue only after approval.

---

### 7.5 Final decision packet

**Tier:** Phase Hard Stop

**What changes**

Produce final decision packet:

```text
final_operating_level
allowed_task_classes
blocked_task_classes
router_model
coder_model
central_gate_function
local_proof_requirements
apply_requirements
rollback_path
known_failure_modes
next_authorized_increment
```

**Self-checks Codex can run**

* decision matches Phase 6 operating level
* no unsupported production-ready claim
* no hidden autonomy claim
* no commit/push claim
* central gate rule included

**Manual check required**

Human accepts or rejects final decision packet.

**Gate**

Plan complete only after human approval.

---

## Phase Completion Gate

Human must verify:

* The system is understandable.
* Centralized gate rule is documented and tested.
* Rollback is possible.
* UI truth is visible.
* Evidence is complete.
* Final operating level is explicit.
* No hidden autonomy was introduced.

---

# Final Operating-Level Definitions

| Level                    | Allowed                                                  | Forbidden                                                     |
| ------------------------ | -------------------------------------------------------- | ------------------------------------------------------------- |
| `NO_GO`                  | None                                                     | All Qwen 14B coding use                                       |
| `PREVIEW_ONLY`           | Generate local previews for approved safe tasks          | Apply, commit, push, broad tasks                              |
| `STATIC_SAFE_APPLY_ONLY` | Approved static/demo/docs fixture apply/reverse          | Existing app refactors, auth/db, external services            |
| `ISOLATED_APPLY_ONLY`    | Approved static and isolated component/test/config edits | Broad refactors, auth/db, external services, unattended apply |

There is no full-autonomy level in this plan.

---

# Required Receipts

Every run must record:

```text
run_id
timestamp
phase_id
increment_id
gate_state_before
gate_state_after
approved_increment
approval_token_id
central_gate_check_passed
router_model
router_status
router_attempt_count
router_invalid_reason
fallback_classifier_used
fallback_classifier_result
coder_model
requested_model
resolved_model
provider
provider_call_made
task_class
route
reason_codes
target_unclear
caps_profile
file_count
added_line_count
modified_existing_file_count
caps_passed
caps_violation_reason
blacklist_passed
blacklist_matches
parse_status
parse_error
repair_attempted
repair_status
repair_similarity_score
repair_similarity_threshold
context_drop_flag
scope_drift_flag
local_proof
scaffold_used
fallback_used
backend_generated_content
diff_shown
apply_allowed
apply_approval_bound
apply_performed
reverse_performed
unexpected_delta_detected
final_trust_status
blocked_reason
human_gate_required
```

Receipt rules:

* Missing receipt fields make the run incomplete.
* `local_proof=true` is allowed only when provider, model, gate, scaffold, fallback, and backend-content fields all support it.
* `diff_shown=true` is forbidden if caps or blacklist failed.
* `apply_allowed=true` is forbidden if diff was not shown and approved.
* `final_trust_status=pass` is forbidden without local proof or explicit non-local comparison labeling.

---

# Required Block Behaviors

| Failure                                 | Required Behavior                                  | Required Receipt Fields                                          |
| --------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------- |
| Gate closed                             | No model call                                      | `central_gate_check_passed=false`, `blocked_reason=gate_closed`  |
| Approved increment mismatch             | No model call                                      | `blocked_reason=increment_mismatch`                              |
| New model path lacks central gate check | Block as implementation failure                    | `blocked_reason=gate_bypass_risk`                                |
| Phi invalid once                        | Retry once                                         | `router_attempt_count=1`, retry recorded                         |
| Phi invalid twice                       | Deterministic fallback                             | `router_status=invalid_twice`, `fallback_classifier_used=true`   |
| Fallback confidently safe               | Continue only for `STATIC_SAFE` or `ISOLATED_EDIT` | `fallback_classifier_result` recorded                            |
| Fallback uncertain                      | Block for human                                    | `blocked_reason=fallback_uncertain`                              |
| Auth/db detected                        | Block before Qwen                                  | `task_class=BLOCKED_AUTH_DB`                                     |
| External service detected               | Block or human review                              | `task_class=BLOCKED_EXTERNAL`                                    |
| Refactor over 3 modules                 | Scale-down options                                 | `task_class=BORDERLINE_REFACTOR`                                 |
| Caps exceeded                           | Reject before diff                                 | `caps_passed=false`, `diff_shown=false`                          |
| Blacklist hit                           | Reject before diff                                 | `blacklist_passed=false`, `blacklist_matches` recorded           |
| Parser failed                           | One repair if eligible                             | `parse_status=failed`, `repair_attempted=true/false`             |
| Unsafe output needs repair              | Do not repair                                      | `repair_attempted=false`, `blocked_reason=unsafe_not_repairable` |
| Repair rewrote logic                    | Block                                              | `repair_status=failed_similarity_guard`                          |
| Provider mismatch                       | Block                                              | `blocked_reason=provider_mismatch`                               |
| Hidden fallback                         | Block and mark proof invalid                       | `fallback_used=true`, `local_proof=false`                        |
| Scaffold/backend content used           | Block as local proof                               | `backend_generated_content=true` or `scaffold_used=true`         |
| Visual proof needed                     | Stop for human visual check                        | `human_gate_required=true`                                       |
| Apply requested without bound approval  | Block                                              | `apply_allowed=false`, `blocked_reason=missing_apply_approval`   |
| Approval token reused/stale             | Block                                              | `blocked_reason=stale_or_reused_approval`                        |
| Unexpected file delta                   | Block and require human review                     | `unexpected_delta_detected=true`                                 |

---

# Prompt Engineering Requirements

## Phi Prompt

Phi must be prompted as:

```text
You are a code compiler gatekeeper. You are not an assistant.
Return only the required structured classification.
Do not explain.
Do not suggest implementation.
Do not call tools.
Do not choose models.
If uncertain, classify as AMBIGUOUS or BORDERLINE_REFACTOR.
Auth/database/external-service requests must not be LOCAL_OK.
```

## Qwen Prompt

Qwen must be prompted as:

```text
You are a local coding worker.
Implement only the smallest explicit request.
Obey the TaskSpec and allowed files.
Do not add auth, accounts, sessions, database, payments, deployment, analytics, external services, or broad refactors.
Use only the required XML file format.
Do not include markdown, prose, or explanations.
If the task cannot be completed inside the allowed scope, return no files.
```

## Repair Prompt

Repair mode must be prompted as:

```text
Fix formatting only.
Do not change code logic.
Do not add files.
Do not remove files.
Do not rename files.
Do not add features.
Do not add dependencies.
Do not change behavior.
The backend will reject repaired output if code changes beyond the similarity threshold.
```

---

# How Codex Must Execute This Plan

## Execution Loop

For every increment:

1. Check gate status through the centralized gate function or approved gate command.
2. Confirm the exact increment is approved.
3. Start only that increment.
4. Do only the work listed for that increment.
5. Run self-checks.
6. Write evidence.
7. Mark increment complete.
8. Gate returns to `WAITING_FOR_HUMAN`.
9. Stop.
10. Wait for human approval.

## Codex Must Stop If

* gate is not approved
* centralized gate function is missing or bypassed
* task target is unclear
* a test fails and the fix requires guessing
* model route is unclear
* provider/model mismatch occurs
* Phi fails and fallback is uncertain
* Qwen output exceeds caps
* blacklist triggers
* repair similarity fails
* browser/visual/hardware verification is needed
* dirty tree contamination appears
* manual check reveals a problem
* applying would require guessing

## Codex Must Never

* approve its own gate
* skip an increment
* merge Tier 1 increments
* add a model-call path without the centralized gate function
* call Qwen before routing
* call Qwen after block
* show diff after caps/blacklist failure
* repair more than once
* accept repair that rewrites logic
* silently switch models
* use cloud fallback
* count cloud output as local proof
* count scaffold/backend content as model output
* apply without exact approval binding
* commit, push, stash, reset, clean, or create worktrees unless separately authorized

---

# Final Target State

The target is a small, survivable local coding system:

```text
Human gate
→ centralized gate-checking function
→ Phi classifier, with invalid-output fallback
→ deterministic backend guard
→ Qwen 14B local coder
→ XML parser
→ one-shot repair with similarity guard
→ preview
→ human approval
→ safe apply/reverse
→ evidence receipt
```

The system succeeds if Qwen 14B can safely handle small local tasks under strict constraints.

The system also succeeds if it honestly proves Qwen 14B should remain preview-only or static-only.

The system fails only if it hides uncertainty, silently escalates, overbuilds, self-approves, bypasses the central gate, or claims trust without evidence.

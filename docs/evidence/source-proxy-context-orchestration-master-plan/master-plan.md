# Source Proxy Context-Orchestrated Coding Agent Readiness Master Plan

Status: master plan only. Do not execute Plan 0 until Britton approves.

## Goal

Bring the SpiritOS coding agent from preview/advisory pieces into a real Source Proxy context-orchestrated coding workflow.

The target is not a route demo. The target is Source Proxy assembling a task-specific coder packet from polished SpiritOS systems, routing it through the real `/coding` hot path, validating strict coder output, and leaving durable evidence that every context source was used, skipped, or blocked.

## Global Execution Law

Every plan follows Britton's pivot workflow:

1. complete one increment
2. test it
3. write evidence
4. move to the next increment only if GO
5. verify the phase before the next phase
6. verify the plan before the next plan
7. stop and ask Britton before starting the next plan

Global forbidden actions until separately approved: runtime behavior changes, coder trials, Coder 50, Coder 100, complex feature work, autonomous Cartographer queue work, background workers, hidden Scout memory writes, hidden apply, hidden commit, hidden push, and 14B default switch.

## Plan 0: Baseline, Model Route, and Workflow Law

Purpose: Freeze current truth and define the execution workflow before patching anything.

Why this plan exists: The repo already contains Source Proxy, `/coding`, Cartographer, Scout/Mac/Search, Design packets, helper agents, Agent Factory, Repomix, and route previews. Plan 0 prevents those pieces from being accepted as integration without current evidence and workflow law.

Prerequisites: Britton approval to execute Plan 0. No runtime changes. No coder trials. No git mutation unless separately approved.

Files likely involved: `docs/evidence/source-proxy-context-orchestration-master-plan/plan-0/`, `source_proxy/`, `src/app/`, `src/components/coding/`, `config/`, `package.json`, `.env.example`, `repomix.config.json`, current git metadata.

Tests/checks: read-only `git status --short --branch`, route/file inventory via `rg --files`, route truth inspection, docs lint/link review if available, no provider/model calls unless Britton explicitly approves.

Evidence files to produce: `plan-0/phase-0.1-baseline.md`, `plan-0/phase-0.2-route-inventory.md`, `plan-0/phase-0.3-model-truth.md`, `plan-0/phase-0.4-workflow-law.md`, `plan-0/plan-0-closeout.md`.

### Phase 0.1: Repo, Branch, and Dirty-Tree Baseline

- Increment 0.1.1: Record repo root, branch, upstream, HEAD, dirty tree, untracked files, and protected existing changes.
- Increment 0.1.2: Classify dirty files as unrelated, relevant, generated, local config, or blocked-to-touch.
- Increment 0.1.3: Record safe verification surface, including Windows share path and Dell host path if needed.

GO/NO-GO criteria: GO if baseline is recorded without mutation and unrelated dirty work is protected. NO-GO if the tree cannot be safely classified.

### Phase 0.2: Source Proxy and `/coding` Route Inventory

- Increment 0.2.1: Inventory Source Proxy backend routes, coding frontend routes, trial widgets, and durable receipt surfaces.
- Increment 0.2.2: Identify preview-only, advisory-only, integrated, and production-ready surfaces.
- Increment 0.2.3: Record where Repomix currently appears and whether it is treated as fallback, fixture, or primary context.

GO/NO-GO criteria: GO if every relevant route is classified without claiming integration. NO-GO if route existence is being used as acceptance.

### Phase 0.3: Current Model and Provider Route Truth

- Increment 0.3.1: Record configured provider aliases and displayed model truth.
- Increment 0.3.2: Confirm or switch the default coder route to `qwen2.5-coder:7b` only if the change is explicitly inside Britton-approved Plan 0 scope.
- Increment 0.3.3: Preserve 14B as comparison-only and document the upgrade criteria.

GO/NO-GO criteria: GO if 7B default truth is documented or an approved change is made with evidence. NO-GO if 14B is defaulted without passing contract tests.

### Phase 0.4: Workflow Definitions and Pivot Law

- Increment 0.4.1: Define preview, advisory, integrated, and production-ready.
- Increment 0.4.2: Write the pivot workflow law into the active evidence set.
- Increment 0.4.3: Define stop gates and exact operator handoff for Plan 1.

GO/NO-GO criteria: GO if definitions and stop gates are explicit. NO-GO if the plan allows jumping ahead.

Phase closeout: Each phase closeout must include evidence file links, checks run, result, and next allowed phase.

Plan closeout: Plan 0 closes only when baseline, route inventory, model truth, and workflow law are complete.

Stop condition: Stop after Plan 0 closeout and ask Britton before Plan 1.

Exact operator handoff for next plan: "Britton, Plan 0 is closed with GO/NO-GO evidence. Do you approve starting Plan 1: Output Contract, Parser, and Repair Discipline?"

## Plan 1: Output Contract, Parser, and Repair Discipline

Purpose: Fix the known malformed output problem before adding more context.

Why this plan exists: Context orchestration is useless if the coder output cannot be parsed safely. The first product requirement is reliable file-block output under messy prompts.

Prerequisites: Plan 0 GO and Britton approval to start Plan 1.

Files likely involved: `source_proxy/`, `source_proxy/tests/`, `tests/ui-agent-trials/fixtures/`, coding prompt fixtures, parser/output-contract docs, evidence under `plan-1/`.

Tests/checks: focused parser tests, malformed-output negative tests, messy Britton-style prompt fixtures, 7B baseline only after parser route is safe, 14B comparison only after parser stability.

Evidence files to produce: `plan-1/phase-1.1-output-contract.md`, `plan-1/phase-1.2-parser-rejection.md`, `plan-1/phase-1.3-repair-discipline.md`, `plan-1/phase-1.4-model-contract-tests.md`, `plan-1/plan-1-closeout.md`.

### Phase 1.1: Strict File-Block Output Contract

- Increment 1.1.1: Define allowed file-block syntax and path rules.
- Increment 1.1.2: Ban markdown fences around coder file blocks.
- Increment 1.1.3: Require non-empty diff/content payloads for every accepted block.

GO/NO-GO criteria: GO if contract is testable and unambiguous. NO-GO if freeform markdown can pass as a patch.

### Phase 1.2: Malformed Block Rejection

- Increment 1.2.1: Reject markdown fence found.
- Increment 1.2.2: Reject unclosed file tag.
- Increment 1.2.3: Reject no file block.
- Increment 1.2.4: Reject malformed file block.
- Increment 1.2.5: Reject empty diff.
- Increment 1.2.6: Reject unsafe path.
- Increment 1.2.7: Reject out-of-scope file.

GO/NO-GO criteria: GO if every diagnostic is covered by a targeted negative test. NO-GO if any malformed output can silently continue.

### Phase 1.3: One-Pass Repair Discipline

- Increment 1.3.1: Define the one allowed formatting repair pass.
- Increment 1.3.2: Prove failed repair remains blocked.
- Increment 1.3.3: Record repair diagnostics in the durable run receipt.

GO/NO-GO criteria: GO if repair is bounded, visible, and cannot become hidden retry autonomy. NO-GO if repeated silent repair loops are possible.

### Phase 1.4: Messy Prompt Model Contract Tests

- Increment 1.4.1: Create messy Britton-style basic prompt fixtures.
- Increment 1.4.2: Run 7B baseline output-contract tests.
- Increment 1.4.3: Run 14B comparison only after parser stability.
- Increment 1.4.4: Record 14B as non-default unless it passes the same contract.

GO/NO-GO criteria: GO if 7B produces valid file blocks for basic messy prompts without markdown fences or malformed tags. NO-GO if 7B fails the basic contract.

Phase closeout: Each phase closeout must include parser diagnostics, fixture names, commands, and result.

Plan closeout: Plan 1 closes only when parser and repair discipline are enforced with evidence.

Stop condition: Stop after Plan 1 closeout and ask Britton before Plan 2.

Exact operator handoff for next plan: "Britton, Plan 1 is closed with output-contract evidence. Do you approve starting Plan 2: Context Source Readiness?"

## Plan 2: Context Source Readiness

Purpose: Polish each context source before integrating it into Source Proxy.

Why this plan exists: Source Proxy should assemble the final coder packet from polished SpiritOS systems. If a subsystem is not ready, it must produce a blocked/skipped reason instead of being silently bypassed.

Prerequisites: Plan 1 GO and Britton approval to start Plan 2.

Files likely involved: Cartographer modules under `source_proxy/cartographer/`, Obsidian/vault config surfaces, Scout/Mac/Search modules, Design packet docs/components, tests for packet adapters, evidence under `plan-2/`.

Tests/checks: packet-shape tests, disabled/missing config tests, safe read-only query tests, metadata/citation tests, no-hidden-write tests.

Evidence files to produce: `plan-2/phase-2.1-cartographer-readiness.md`, `plan-2/phase-2.2-obsidian-readiness.md`, `plan-2/phase-2.3-scout-mac-search-readiness.md`, `plan-2/phase-2.4-design-readiness.md`, `plan-2/plan-2-closeout.md`.

### Phase 2.1: Cartographer Readiness

- Increment 2.1.1: Produce repo map packet shape.
- Increment 2.1.2: Produce component map packet shape.
- Increment 2.1.3: Include dirty-tree status.
- Increment 2.1.4: Include ownership/conflict status.
- Increment 2.1.5: Include architecture/blueprint truth.
- Increment 2.1.6: Define context packet adapter shape for Source Proxy.

GO/NO-GO criteria: GO if Cartographer can produce a real packet or blocked/skipped reason. NO-GO if "map route exists" is the only evidence.

### Phase 2.2: Obsidian Readiness

- Increment 2.2.1: Record vault path/config truth.
- Increment 2.2.2: Add disabled/missing config diagnostics.
- Increment 2.2.3: Prove safe query behavior.
- Increment 2.2.4: Select task-specific notes.
- Increment 2.2.5: Produce safe excerpts.
- Increment 2.2.6: Prove production-ready read-only context behavior.

GO/NO-GO criteria: GO if Obsidian produces task-specific safe context or an explicit unavailable reason. NO-GO if missing config is silent.

### Phase 2.3: Scout/Mac/Search Readiness

- Increment 2.3.1: Produce real search packet or hard blocked reason.
- Increment 2.3.2: Include source/citation metadata.
- Increment 2.3.3: Define Mac advisory boundary.
- Increment 2.3.4: Prove no hidden memory writes.
- Increment 2.3.5: Prove no hidden code writes.

GO/NO-GO criteria: GO if Scout/Search can advise visibly with citations or block honestly. NO-GO if it writes memory/code or omits source status.

### Phase 2.4: Design Readiness

- Increment 2.4.1: Produce design token/context packet.
- Increment 2.4.2: Produce component/style vocabulary.
- Increment 2.4.3: Produce UI critique packet.
- Increment 2.4.4: Define design-to-coder handoff.
- Increment 2.4.5: Add blocked states if the design lane is not ready.

GO/NO-GO criteria: GO if Design can produce an advisory packet or blocked/skipped reason. NO-GO if design claims apply authority or hides readiness gaps.

Phase closeout: Each source phase must show real packet, blocked reason, or skipped reason.

Plan closeout: Plan 2 closes only when all four context sources have explicit readiness states.

Stop condition: Stop after Plan 2 closeout and ask Britton before Plan 3.

Exact operator handoff for next plan: "Britton, Plan 2 is closed with context-source readiness evidence. Do you approve starting Plan 3: Helper/Subagent Readiness?"

## Plan 3: Helper/Subagent Readiness

Purpose: Make helper agents real enough to assist the coder agent.

Why this plan exists: Helper agents can improve review, testing, and task shaping, but only if their authority boundaries and outputs are visible to Source Proxy.

Prerequisites: Plan 2 GO and Britton approval to start Plan 3.

Files likely involved: `source_proxy/agents/`, `source_proxy/agent_factory/`, helper registry modules, task/result schemas, Source Proxy advisory packet adapters, tests, evidence under `plan-3/`.

Tests/checks: registry tests, schema tests, no-mutation tests, conflict reporting tests, Source Proxy-readable packet tests.

Evidence files to produce: `plan-3/phase-3.1-helper-registry.md`, `plan-3/phase-3.2-helper-schemas.md`, `plan-3/phase-3.3-reviewer-tester-outputs.md`, `plan-3/phase-3.4-authority-proof.md`, `plan-3/plan-3-closeout.md`.

### Phase 3.1: Helper/Subagent Role Registry

- Increment 3.1.1: Inventory helper/subagent roles.
- Increment 3.1.2: Define authority boundaries for each role.
- Increment 3.1.3: Mark advisory-only helpers.

GO/NO-GO criteria: GO if every helper role has an explicit authority boundary. NO-GO if any helper can run hidden mutation.

### Phase 3.2: Helper Packet Schemas

- Increment 3.2.1: Define helper task packet schema.
- Increment 3.2.2: Define helper result packet schema.
- Increment 3.2.3: Define Source Proxy-readable advisory packet.

GO/NO-GO criteria: GO if schemas are machine-checkable and visible. NO-GO if helper output is freeform-only.

### Phase 3.3: Reviewer, Tester, and Conflict Output

- Increment 3.3.1: Define reviewer helper output.
- Increment 3.3.2: Define tester helper output.
- Increment 3.3.3: Define conflict/disagreement reporting.

GO/NO-GO criteria: GO if disagreements are visible to Source Proxy and Britton. NO-GO if one helper can silently override another.

### Phase 3.4: No Hidden Mutation Proof

- Increment 3.4.1: Prove no hidden apply.
- Increment 3.4.2: Prove no hidden commit.
- Increment 3.4.3: Prove no hidden push.
- Increment 3.4.4: Prove no hidden background worker continuation.

GO/NO-GO criteria: GO if helper agents advise, critique, test, or hand off without secret mutation. NO-GO if mutation authority leaks.

Phase closeout: Each phase closeout must include role/schema evidence and no-hidden-mutation proof.

Plan closeout: Plan 3 closes only when helper outputs are visible and Source Proxy-readable.

Stop condition: Stop after Plan 3 closeout and ask Britton before Plan 4.

Exact operator handoff for next plan: "Britton, Plan 3 is closed with helper/subagent readiness evidence. Do you approve starting Plan 4: Source Proxy Context Orchestration?"

## Plan 4: Source Proxy Context Orchestration

Purpose: Wire the polished systems into the real `/coding` hot path.

Why this plan exists: The readiness goal is Source Proxy assembling task-specific coder packets. Plan 4 is where the polished context sources become part of the actual coding route, not a side demo.

Prerequisites: Plan 3 GO and Britton approval to start Plan 4.

Files likely involved: Source Proxy prompt/context builder modules, `/coding` frontend components, durable receipt writers, route handlers, source adapter modules, tests, evidence under `plan-4/`.

Tests/checks: context builder unit tests, route integration tests, UI display tests, receipt persistence tests, fallback-only warnings/blocks, coder-packet payload proof without hidden mutation.

Evidence files to produce: `plan-4/phase-4.1-context-builder.md`, `plan-4/phase-4.2-task-and-file-resolution.md`, `plan-4/phase-4.3-source-selection-and-budgeting.md`, `plan-4/phase-4.4-coder-packet-display-and-receipt.md`, `plan-4/phase-4.5-coder-receives-final-packet.md`, `plan-4/plan-4-closeout.md`.

### Phase 4.1: Context Packet Builder

- Increment 4.1.1: Create or repair a context packet builder.
- Increment 4.1.2: Require all source adapters to return used/skipped/blocked.
- Increment 4.1.3: Block or warn if context is fallback-only.

GO/NO-GO criteria: GO if no coder run can bypass the builder. NO-GO if fallback-only context can masquerade as full context.

### Phase 4.2: Task and File Resolution

- Increment 4.2.1: Normalize Britton's messy prompt into a task spec.
- Increment 4.2.2: Resolve target files.
- Increment 4.2.3: Resolve allowed files.
- Increment 4.2.4: Resolve forbidden files.

GO/NO-GO criteria: GO if target/allowed/forbidden files are visible and safe. NO-GO if the model guesses write scope silently.

### Phase 4.3: Source Selection and Budgeting

- Increment 4.3.1: Select context sources by task.
- Increment 4.3.2: Apply budget/context compression.
- Increment 4.3.3: Include Repomix only as fallback/source, not the main context brain.

GO/NO-GO criteria: GO if each selected source has visible status and budget handling. NO-GO if a source is silently skipped.

### Phase 4.4: `/coding` Display and Durable Receipt

- Increment 4.4.1: Display the final packet in `/coding`.
- Increment 4.4.2: Store the packet in durable run receipt.
- Increment 4.4.3: Display model route truth and output contract version.

GO/NO-GO criteria: GO if Britton can inspect the packet and receipt. NO-GO if evidence exists only in transient logs.

### Phase 4.5: Prove Coder Receives Final Packet

- Increment 4.5.1: Prove original prompt, normalized task, intent, file scopes, and all source statuses are in the final compact coder prompt payload.
- Increment 4.5.2: Prove the selected 7B default route receives that payload.
- Increment 4.5.3: Prove no hidden apply/commit/push occurs during packet assembly.

GO/NO-GO criteria: GO if the coder receives the final packet and receipt proves it. NO-GO if `/coding` display and actual model payload diverge.

Phase closeout: Each phase closeout must include packet examples, diagnostics, tests, and no-bypass proof.

Plan closeout: Plan 4 closes only when the real `/coding` hot path uses the Source Proxy context packet builder.

Stop condition: Stop after Plan 4 closeout and ask Britton before Plan 5.

Exact operator handoff for next plan: "Britton, Plan 4 is closed with Source Proxy context-orchestration evidence. Do you approve starting Plan 5: A+ Basic Coding Gauntlet?"

## Plan 5: A+ Basic Coding Gauntlet

Purpose: Prove the whole chain before complex tasks.

Why this plan exists: The system must pass simple messy coding requests through the full context chain before Coder 50, Coder 100, complex work, or autonomy is allowed.

Prerequisites: Plan 4 GO and Britton approval to start Plan 5.

Files likely involved: gauntlet prompt fixtures, Source Proxy coding run receipts, output-contract tests, frontend/backend checks relevant to each prompt, evidence under `plan-5/`.

Tests/checks: three messy Britton-style basic coding prompts, expected-result checks, full Source Proxy context chain, 7B default route truth, output contract pass, diff produced, tests/checks pass, no scaffold/fallback, no hidden mutation.

Evidence files to produce: `plan-5/phase-5.1-gauntlet-definition.md`, `plan-5/phase-5.2-run-1.md`, `plan-5/phase-5.3-run-2.md`, `plan-5/phase-5.4-run-3.md`, `plan-5/phase-5.5-final-a-plus-readiness-report.md`, `plan-5/plan-5-closeout.md`.

### Phase 5.1: Define Basic Gauntlet

- Increment 5.1.1: Define three messy Britton-style basic coding prompts.
- Increment 5.1.2: Define expected result for each prompt.
- Increment 5.1.3: Define grading rubric and A+ threshold.

GO/NO-GO criteria: GO if prompts are basic, bounded, messy, and expected results are checkable. NO-GO if prompts become complex feature tasks.

### Phase 5.2: Gauntlet Run 1

- Increment 5.2.1: Run prompt 1 through the full Source Proxy context chain.
- Increment 5.2.2: Confirm 7B default route, context packet present, output contract passed, diff produced, tests/checks pass, no scaffold/fallback, and no hidden mutation.
- Increment 5.2.3: Grade run 1.

GO/NO-GO criteria: GO if run 1 earns A+. NO-GO if any required proof is missing.

### Phase 5.3: Gauntlet Run 2

- Increment 5.3.1: Run prompt 2 through the full Source Proxy context chain.
- Increment 5.3.2: Confirm 7B default route, context packet present, output contract passed, diff produced, tests/checks pass, no scaffold/fallback, and no hidden mutation.
- Increment 5.3.3: Grade run 2.

GO/NO-GO criteria: GO if run 2 earns A+. NO-GO if any required proof is missing.

### Phase 5.4: Gauntlet Run 3

- Increment 5.4.1: Run prompt 3 through the full Source Proxy context chain.
- Increment 5.4.2: Confirm 7B default route, context packet present, output contract passed, diff produced, tests/checks pass, no scaffold/fallback, and no hidden mutation.
- Increment 5.4.3: Grade run 3.

GO/NO-GO criteria: GO if run 3 earns A+. NO-GO if any required proof is missing.

### Phase 5.5: Final A+ Readiness Report

- Increment 5.5.1: Produce final A+ readiness report.
- Increment 5.5.2: Confirm 3 out of 3 basic messy prompts passed with A+.
- Increment 5.5.3: List remaining blocked upgrades, including Coder 50, Coder 100, complex tasks, autonomy, and 14B default switch.

GO/NO-GO criteria: GO only if 3 out of 3 basic messy prompts pass with A+. NO-GO if any prompt fails or any proof is missing.

Phase closeout: Each run phase must include prompt, expected result, context packet receipt, route truth, output-contract result, diff proof, checks, mutation boundary, and grade.

Plan closeout: Plan 5 closes only when all three basic runs pass A+.

Stop condition: Stop after Plan 5 closeout and ask Britton before any larger task lane.

Exact operator handoff for next plan: "Britton, Plan 5 is closed with final A+ readiness evidence. Do you approve planning the next lane? Coder 50, Coder 100, complex multi-file tasks, autonomy, and 14B default switch remain blocked unless you approve a specific next plan."

## Do Not Start Yet

- Coder 50
- Coder 100
- complex multi-file feature tasks
- autonomous Cartographer queue work
- background workers
- 14B default switch
- hidden Scout memory writes
- hidden apply/commit/push

## Final Master-Plan GO/NO-GO For Review

GO for Britton review of this master plan.

NO-GO for executing Plan 0 until Britton explicitly approves.

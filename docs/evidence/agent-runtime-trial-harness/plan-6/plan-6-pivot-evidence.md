# Plan 6/8: Combined Coding + Design Handoff Trial Evidence

## Scope

Plan 6 proves a preview-only design-to-coder handoff. The design side generates a bounded packet, the packet is validated before coding delivery, and the coding side receives only a bounded proposal prompt. No apply, final CSS polish, production mutation, commit, push, provider call, Cartographer activation, or hidden worker authority is granted.

## Phase 6.1: Handoff Contract

Implemented in `scripts/agent-trials/run-ui-agent-trials.mjs` for `--agent combined`.

Required packet fields:

- `design_packet_id`
- `route`
- `issue`
- `evidence`
- `recommended_files`
- `forbidden_files`
- `risk_level`
- `expected_check`
- `coding_task_prompt`

Validation:

- Blocks before coding prompt delivery if required fields are missing.
- Blocks if recommended or forbidden files are empty.
- Blocks if risk is not `low`, `medium`, or `high`.
- Blocks if the coding task prompt lacks the no-apply/no-final-CSS/no-production-mutation boundary.

GO / NO-GO: GO.

## Phase 6.2: Combined Trial Flow

Flow implemented:

1. Visit `/coding/design-demo` and capture design evidence.
2. Type design request through `/coding` UI.
3. Generate bounded design handoff packet.
4. Validate packet before coding delivery.
5. Type the generated `coding_task_prompt` through `/coding` UI.
6. Record coding side as preview/proposal-only.

Smoke evidence:

- `node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 2` passed 2/2 with 0 hidden mutation failures.
- `docs/evidence/agent-runtime-trial-harness/plan-6/combined-report.json` records `design_packets_generated`, `coding_task_prompts_delivered`, and `go`.

GO / NO-GO: GO.

## Phase 6.3: No Mutation + Rollback Proof

No dummy fixture mutation was used.

Mutation evidence:

- Combined trial result JSON files include `mutation_result`.
- `mutation_result.cleanup` is `not_needed_preview_only`.
- Unexpected files list is empty for passing combined trials.

GO / NO-GO: GO.

## Phase 6.4: Combined Smoke

Checks run:

```bash
node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 5
node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport mobile --limit 3
npx --no-install tsc --noEmit --pretty false
git diff --check
git status --branch --short --untracked-files=normal
```

Evidence:

- Desktop combined smoke passed 5/5 with 100% weighted score and 0 hidden mutation failures.
- Mobile combined smoke passed 3/3 with 100% weighted score and 0 hidden mutation failures.
- Final combined report records `go: true`, `invalid_design_packets: 0`, `hidden_mutation_failures: 0`, `fake_authority_failures: 0`, and `final_css_claim_failures: 0`.

GO / NO-GO: GO.

## Plan 6 Result

GO.

The combined flow exists, design packets are bounded, coding prompts are generated from validated packets, coding output remains preview/proposal-only, and no unsafe file target, hidden mutation, fake authority, or final CSS claim occurred.

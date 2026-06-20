# Stage 3 Policy Gates

Result: `INTEGRATED_LIVE`.

Implementation:
- `evaluate_plan3_policy`
- `apply_plan3_policy`

Covered actions:
- Mac write
- Mac unsafe path
- Obsidian write
- Cartographer git mutation
- source patch
- external web research
- model lane execution
- browser/functional verification
- repair apply
- push
- media/Jellyfin mutation
- Docker/systemd mutation

Fail-closed proof:
- task: `task_6ecf07847f44`
- trace: `trace_6d3256350cd748f2`
- blocked action: `mac_write`
- target: `../unsafe`
- status: `policy_blocked`
- policy_decision: `policy_blocked`
- failure class: `unsafe_path_rejected`
- causal event type: `policy`
- mutation prevented: yes

Raw evidence:
- `/home/source/spiritos-evidence/plan-03/plan3-disposable-proof.json`

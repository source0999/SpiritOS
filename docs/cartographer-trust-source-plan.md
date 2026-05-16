# Cartographer Trust Source Plan

Cartographer trust is earned through repeated read-only checks, explicit approvals, and boring soak snapshots. A passing soak snapshot is evidence, not permission to apply, commit, push, merge, or enable autopilot.

## Snapshot Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
```

## Trust Inputs

- Safety manifest keeps write actions disabled and approval bypasses locked.
- Proposal queue remains deduped with no duplicate pending proposals.
- Drift, commit proposal, and push queue counts stay explainable.
- Audit trail contains rollback hints and explainability fields.
- Git HEAD does not change during soak.
- The only expected mutation is a JSON snapshot under `source_proxy/cartographer/soak-logs/`.

## Reliability Score

The runner starts at 100 and subtracts for unsafe or noisy signals:

- write actions enabled
- bypass flags unlocked
- duplicate proposals
- pending proposal review
- unresolved drift
- dirty working tree

Scores are labels, not authority:

- `boring`: keep observing and proceed to the next manual increment.
- `watch`: continue soak before trusting the workflow.
- `blocked`: fix the reported warnings before proceeding.

## Manual Closeout

Run three snapshots over time:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
sleep 60
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
sleep 60
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
```

Expected:

```text
cartographer-soak-snapshot: pass
mutation boundary: snapshot log only
recommendation: ready for next increment
```

If the reliability grade is `watch`, the expected recommendation is `continue soak`; the report must also print concrete next actions with live proposal, drift, or commit proposal IDs and copy-paste inspection commands. Fix or review those listed items before moving on.

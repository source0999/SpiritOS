# Scout v0.6 Phase 0.4 Dry-Run Receipt Preview Copy Audit

status: implemented/manual-controlled

Status date: 2026-05-20

This document records the Scout v0.6 Phase 0.4 dry-run receipt preview copy audit. The increment clarifies labels in the Scout import receipt preview UI so the operator sees that the displayed receipt is a preview from a dry run. It does not call proxy intake, does not emit actual receipts, does not finalize promotions, does not write proxy memory, does not write coding context, does not register workers, does not schedule writes, does not apply code, does not commit, and does not push.

## Goal

Prevent the dry-run receipt preview from reading like a completed import.

Updated labels:

- `Receipt Preview Event`
- `Imported In Dry Run`
- `Applied In Dry Run`
- `Append-Only Evidence Write`
- `Proxy Memory Write`
- `Coding Context Write`
- `Active Context Write`
- `Rollback Tombstone Preview`

## Safety Boundary

This increment only changes passive UI labels and the matching frontend test. It must not add or trigger:

- proxy intake calls
- append-only intake writes
- actual receipt emission
- promotion finalization
- proxy memory writes
- coding context writes
- active context writes
- hidden background workers
- scheduled writes
- automatic packet promotion
- automatic source approval
- source activation
- discovery execution
- candidate extraction
- apply actions
- commits
- pushes

## Verification

Required checks:

- frontend test proves receipt preview labels include `Preview` and `Dry Run`
- frontend test proves dry-run still does not call promotion finalization
- closeout profile remains read-only and non-mutating
- closeout summary still says `mode: dry_run_only`

## Manual Check

```bash
cd /home/source/SpiritOS && grep -n "Scout v0.6 Phase 0.4 Dry-Run Receipt Preview Copy Audit\|Receipt Preview Event\|Imported In Dry Run\|Applied In Dry Run\|Rollback Tombstone Preview\|Next Permission Gate" docs/scout-v0-6-dry-run-receipt-preview-copy-audit.md src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx && git diff --check && CI=1 npm run test -- HomelabScoutIntelligenceWidget && PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-v0-5-closeout --json | jq '{profile,result,read_only,mutated,closeout_summary,checks,file_change_verdict:{unexpected_status_delta:.file_change_verdict.unexpected_status_delta,head_changed:.file_change_verdict.head_changed}}'
```

Expected outcome:

- doc and UI include receipt-preview dry-run labels
- frontend test passes
- `git diff --check` prints nothing
- closeout returns `result: pass`
- `closeout_summary.mode` is `dry_run_only`
- `mutated` is `false`
- unexpected status delta is empty
- head changed is false

## Rollback

```bash
git restore src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
rm docs/scout-v0-6-dry-run-receipt-preview-copy-audit.md
```

## Next Permission Gate

Operator approval is required before implementing Scout v0.6 Phase 0.5. The recommended next increment is **Scout v0.6 Phase 0.5: Dry-Run Closeout Manual Check Compression**, which should make mobile manual checks shorter without changing Scout behavior.

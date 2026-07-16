# Campaign 1 Evidence Index

Schema: `spiritos-campaign-1-evidence-index/v2`

## Current verdict

- Campaign: `spiritos-campaign-1`; phase: **Campaign 1 complete**; verdict: `GO_CAMPAIGN_1_COMPLETE`; `commit_safe=true`; critical blocker: `none`; Campaign 2 is not started.
- Candidate implementation head: `007bb4ea8288284fb3c5600ae8fbd189b334ed80`; prior closeout-control-plane head: `38a8b5a017f357eef1ece29d8904b849ce8b7990` under the atomic control-plane checkpoint policy.
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.

## Accepted receipts

| Receipt | Result | Claim ceiling |
| --- | --- | --- |
| `campaign-1-baseline/authenticated-browser-proof.json` | pass, redacted baseline | no-reversion browser regression only |
| `campaign-1-evidence/ar001-admin-operator-lifecycle-20260714.md` | AR-001 pass | administrative authority lifecycle |
| `campaign-1-evidence/cartographer-durable-selection-20260714.md` | AR-002 pass | durable selection/consumer boundary |
| `campaign-1-evidence/design-writeback-acknowledgement-20260714.md` | AR-003 pass | Design acknowledgement boundary |
| `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` | authoritative `truth_status=GO`, `commit_safe=true`, all required stages evidence-complete; model diff, approval/apply, managed/direct Chromium, anti-cheat, Undo/reset, clean baseline/rerun | isolated authenticated Prompt 1 lifecycle |
| [campaign-1-test-profiles.md](campaign-1-test-profiles.md) | mandatory matrix accepted: 85/133/193/61/263/3/3 plus validators and build | each named profile only |

Every receipt is redacted by reference. No secret, cookie, approval ID, task ID, raw model output, or media path is repeated in this index.

## Historical evidence — non-current

Earlier partial runtime receipts and narrower profile counts are preserved for provenance only. They neither reduce the authoritative final receipt nor reopen a completed gate.

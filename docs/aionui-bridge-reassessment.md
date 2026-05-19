# AionUi Bridge Reassessment

Status date: 2026-05-18
Status: decision document only

## Purpose

This document decides whether SpiritOS should build an AionUi bridge after Source Proxy and `/coding` matured.

No AionUi integration was built for this reassessment. SpiritOS was not opened in AionUi. No production source code was changed for this reassessment.

## Decision

Do not build an AionUi bridge now.

Keep AionUi as UX/reference research only. Future AionUi experiments must stay in a toy repository unless a later explicit approval gate changes that boundary.

## Evidence Reviewed

- `docs/aionui-reference-study.md`
- `docs/spirit-cowork-gap-report.md`
- current Source Proxy `/coding` operator console state
- provider capability registry from Phase 9

The prior AionUi study used only `/home/source/aionui-toy-repo`. It did not open SpiritOS in AionUi, and it did not grant AionUi SpiritOS authority.

## Why No Bridge

AionUi has useful UX ideas, but its bridge cost is higher than its current value for SpiritOS:

- AionUi is GUI-dependent and awkward for headless Source Proxy operation.
- Its authority model is outside the Source Proxy trust boundary.
- Provider behavior depends heavily on model/tool support.
- `.aionrs/` repo-local state would need explicit ignore and cleanup policy.
- Source Proxy already owns task specs, allowed files, diff preview, verifier/reviewer flow, approval gates, Cartographer logging, commit gating, and push gating.
- `/coding` now provides the operator-console surface where AionUi-like ideas can be borrowed safely.

## Borrow Later

These AionUi ideas may be borrowed into `/coding` later:

- workspace picker
- model/provider selector
- permission mode labels
- visible tool steps
- current workspace label
- provider configuration summary
- history/task sidebar patterns
- clearer tool result visibility

Borrowing UI patterns does not mean integrating AionUi or delegating authority to it.

## Do Not Build

Do not build:

- AionUi bridge
- AionUi-backed provider adapter
- AionUi task scheduler
- AionUi remote-control path into SpiritOS
- AionUi-managed apply, commit, or push controls
- `.aionrs/` workflow inside SpiritOS

## Future Experiment Rules

Any future AionUi experiment must:

- use a toy repo by default
- not open `/home/source/SpiritOS`
- not read SpiritOS secrets, certificates, tokens, or `.env*`
- not create files inside SpiritOS
- not run apply, commit, or push
- document cleanup before installation or launch
- treat output as UX evidence only

If a later explicit experiment needs SpiritOS access, it must define:

- exact workspace path
- files allowed
- files forbidden
- expected generated state
- cleanup command
- approval boundary
- rollback command

## Safety Boundary

This reassessment does not authorize:

- production code changes
- provider-layer implementation
- Cowork Console build
- AionUi bridge
- AionUi dependency
- opening SpiritOS in AionUi
- scheduled provider tasks
- autonomous writes

Source Proxy remains the trust boundary:

- TaskSpec first
- allowed files required
- diff preview required
- verifier/reviewer required
- approval required before apply
- commit requires separate approval
- push requires separate approval

## Recommendation

Keep AionUi as reference material only.

Borrow UX ideas into `/coding` when a real Source Proxy workflow needs them. Do not integrate AionUi, and do not use it as a foundation for SpiritOS.

## Manual Check

```bash
cd /home/source/SpiritOS
sed -n '1,260p' docs/aionui-bridge-reassessment.md
grep -n "Do not build an AionUi bridge now\\|reference material only\\|does not authorize" docs/aionui-bridge-reassessment.md
git diff --check
```

Expected output:

- decision document only
- decision says no AionUi bridge now
- AionUi remains UX/reference only
- no production source code changed by this reassessment
- `git diff --check` has no output

## Rollback

```bash
git restore docs/aionui-bridge-reassessment.md docs/source-proxy-production-hardening-plan.md
```

# SpiritOS Source Proxy Design Apply Lane v0.1

Status: approval-lane contract only, no Source Proxy behavior changes

This document defines how an approved Design Vault pack may later become Source Proxy proposal evidence. It does not implement apply behavior, add routes, modify Source Proxy code, change app UI, change Scout runtime behavior, or change Cartographer authority.

## Purpose

Design packs can help a human and Source Proxy understand a future UI change. They are not write authority. A design pack may become proposal evidence only after a human chooses to use it for a bounded implementation task.

## Core Rule

Design Vault artifacts may inform a proposal. They must not apply changes.

The only app-write lane remains Source Proxy with explicit approval.

Source Proxy behavior remains unchanged.

## Allowed Proposal Evidence

An approved design pack may provide:

- source-card reference
- token summary
- component map
- preview-only CSS reference
- screenshots
- match report
- design notes
- originality or safety notes

Evidence is advisory until a human creates or approves an implementation proposal.

## Required Approval Binding

Any future design apply proposal must bind:

- task id
- design pack id
- source card id
- target files
- allowed files
- diff preview
- approval ID
- approved by
- approval timestamp
- git head at approval time
- post-apply verification plan

Approval must be explicit and scoped. A design-pack approval is not the same thing as apply approval.

## Required Gates

Before any future design proposal can apply:

1. Source card is approved.
2. Design pack is approved as proposal evidence.
3. Target files are explicit.
4. Allowed files are explicit.
5. Diff preview is available.
6. Protected and secret paths are blocked.
7. Required checks are listed.
8. Approval ID is bound to the exact proposal.
9. Apply is separate from commit.
10. Commit is separate from push.

## Forbidden Behavior

- no app UI writes directly from Design Vault
- no automatic apply from Scout
- no automatic apply from Reverse Designer
- no automatic apply from Design Blender
- no Cartographer authority expansion
- no Source Proxy approval bypass
- no commit without separate approval
- no push without separate approval
- no protected or secret path writes
- no unbounded file targets

## Post-Apply Verification

Any later approved implementation should produce post-apply evidence:

- changed files
- checks run
- check results
- visual verification status when relevant
- rollback hint
- commit proposal blocked or pending status
- push blocked or pending status

If Playwright is used for visual verification, it must follow `docs/design-visual-verification-v0.1.md`.

## Relationship To Cartographer

Cartographer may document, audit, and plan design-system work. This lane does not grant Cartographer apply, commit, push, approval, or app-write authority.

Cartographer authority remains unchanged.

## Relationship To Scout

Scout may later suggest design candidates through the manual-gated bridge. Scout must not approve, apply, promote to coding context, or trigger implementation automatically.

Scout runtime behavior remains unchanged.

## Relationship To Design Vault

Design Vault stores evidence. It does not execute changes.

Design Vault pack status should stay separate from Source Proxy task status.

## First Future Use

The first future design apply experiment should use:

- pack: `data/design-vault/packs/internal-dashboard-demo-v4/`
- source card: `data/design-vault/source-cards/internal-dashboard-demo-v4.json`

It should target a small, explicitly approved documentation or preview-only implementation before any production UI change is considered.

## Manual Check Pattern

Future implementation increments should include:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/source-proxy-design-apply-lane-v0.1.md && echo "design apply lane doc exists"
grep -n "proposal evidence\\|approval ID\\|diff preview\\|post-apply verification" docs/source-proxy-design-apply-lane-v0.1.md
grep -n "Cartographer authority remains unchanged\\|Source Proxy behavior remains unchanged\\|Scout runtime behavior remains unchanged" docs/source-proxy-design-apply-lane-v0.1.md
git diff -- source_proxy src scout
git diff --check
```

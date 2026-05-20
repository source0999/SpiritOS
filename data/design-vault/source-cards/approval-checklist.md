# Design Vault Source Card Approval Checklist

Status: v0.1 manual approval checklist

Use this checklist before any source is extracted, normalized, blended, or used as proposal evidence.

## Required Metadata

- Source card has a stable `id`.
- Source card has a clear `title`.
- Source card identifies `source_type`.
- Source card records either `source_uri` or `local_path`.
- Source card records owner or rights holder.
- Source card records license, ownership, client approval, or open-source permission notes.
- Source card records reviewer and reviewed date before approval.
- Source card records disallowed assets.

## Approved Use Modes

- `internal-exact`: owned SpiritOS/internal source may be copied or extracted exactly.
- `licensed-exact`: licensed source may be copied or extracted exactly within the license scope.
- `client-approved-exact`: client-approved source may be copied or extracted exactly within the approval scope.
- `open-source-permitted`: open-source permitted source may be used within license terms.
- `inspired-language-only`: source may inform design language, but protected assets and distinctive replicas are not allowed.
- `rejected`: source must not be used for extraction, synthesis, blending, or implementation proposals.

## Approval Rules

- Human approval is required before extraction.
- Exact replica mode is allowed only for owned, licensed, client-approved, or open-source permitted designs.
- Public websites and random references default to `inspired-language-only`.
- Do not copy logos, proprietary copy, brand assets, paid assets, protected images, or distinctive trade dress from unapproved sources.
- Do not add automated web crawling.
- Do not allow Scout to auto-promote a design source into coding context.
- Do not write to app UI without Source Proxy approval.

## Manual Review Steps

1. Confirm the source is intentionally provided by a human.
2. Confirm the rights basis is recorded.
3. Choose exactly one approved use mode.
4. List any disallowed assets.
5. Record reviewer and reviewed date.
6. Keep the source in draft or rejected status if rights are unclear.
7. Add the source to `index.json` only after approval.

## Approval Result

Use one of these outcomes:

- Approved for exact internal or licensed extraction.
- Approved for inspired design-language extraction only.
- Rejected.
- Needs more information.

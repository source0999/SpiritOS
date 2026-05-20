# SpiritOS Design Vault

Status: v0.1 scaffold, manual-first, no runtime integration

The Design Vault stores approved design intelligence artifacts for future SpiritOS design-system work. It is intentionally local, manual-fed, and review-gated in v0.1.

## Boundary

- Manual intake only.
- User-approved references only.
- Owned, internal, licensed, client-approved, or open-source permitted sources first.
- No crawler behavior.
- No automated web discovery.
- No autonomous promotion into coding context.
- No writes to app UI from this folder.
- No Source Proxy, Scout, or Cartographer authority changes.

## Intended Contents

- Source cards that describe provenance, ownership, approval status, and permitted use mode.
- Design packs containing notes, screenshots, token files, generated preview artifacts, and match reports.
- Token model documentation and normalized token payloads after later approved increments.

## Proposed Pack Shape

```text
data/design-vault/packs/<pack-id>/
  source-card.json
  tokens.json
  theme.css
  components-map.json
  reference/
  generated/
  match-report.json
  notes.md
```

## Registry

The registry starts empty at `data/design-vault/source-cards/index.json`.

Source-card authoring starts from:

- `data/design-vault/source-cards/source-card.template.json`
- `data/design-vault/source-cards/approval-checklist.md`

Adding a source card later requires human approval and must record:

- source identity
- source type
- owner or rights basis
- approved use mode
- reviewer
- reviewed date
- legal or safety notes

## First Intended Source

The first future extraction target is the existing internal dashboard demo v4:

- `src/components/dashboard/demo-v4/`
- `src/styles/dashboard-demo-v4.css`

Related token and palette references:

- `src/styles/spirit-demo.tokens.css`
- `src/theme/spiritPalettes.ts`

Those files are references only for this scaffold increment and are not modified here.

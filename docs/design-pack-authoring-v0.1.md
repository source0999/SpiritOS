# SpiritOS Design Pack Authoring v0.1

Status: documentation-only authoring guide

Design packs are reviewable bundles of source-card metadata, tokens, notes, screenshots, generated outputs, and match reports. They are proposal evidence, not write authority.

## Pack Location

Proposed pack path:

```text
data/design-vault/packs/<pack-id>/
```

Current internal pack:

```text
data/design-vault/packs/internal-dashboard-demo-v4/
```

## Required Files

Each pack should contain:

- `README.md`
- `source-card.json` or a link to a Source Card Registry file
- `notes.md`
- `tokens.raw.json`
- `tokens.json`
- `theme.css` when preview CSS aliases are useful
- `components-map.json`
- `reference/`
- `generated/`
- `match-report.json`

## Documentation-Only Preview Rule

In v0.1, preview means documentation and artifacts only:

- markdown summaries
- token JSON
- preview-only CSS aliases
- conceptual component maps
- approved screenshot folders
- match reports

Preview does not mean:

- new app routes
- Storybook setup
- production UI imports
- runtime Design Vault loading
- automatic Source Proxy proposals
- Scout promotion into coding context

No preview route should be created until a later approved implementation increment.

## Authoring Workflow

1. Confirm the source card is approved.
2. Confirm the approved use mode.
3. Add or update `notes.md`.
4. Add raw token observations.
5. Normalize tokens into the v0.1 token model.
6. Add preview-only CSS aliases if useful.
7. Add a conceptual `components-map.json`.
8. Add screenshot placeholders or approved screenshots.
9. Update `match-report.json`.
10. Run JSON and docs checks.

## Component Map Rules

`components-map.json` should describe design concepts, not implementation commands.

Each component entry should include:

- source component or pattern name
- concept
- design roles
- token links
- future reuse notes

Do not use a component map to bypass Source Proxy approval.

## Source Proxy Boundary

Design packs may become Source Proxy proposal evidence later, but only after explicit human approval.

Any future apply lane must require:

- target files
- allowed files
- diff preview
- approval ID
- post-apply verification
- separate commit and push approvals if those ever apply

## Storybook Boundary

No Storybook setup was found during the v0.1 audit. Storybook remains a possible future preview surface only. Do not add Storybook during this authoring increment.

## Safety Rules

- Do not crawl websites.
- Do not ingest unapproved references.
- Do not copy external logos, proprietary copy, brand assets, paid assets, or protected images.
- Do not write to app UI from Design Vault.
- Do not change Scout runtime behavior.
- Do not change Source Proxy behavior.
- Do not change Cartographer authority.

# SpiritOS Design Blender / Style Alchemist v0.1

Status: originality and attribution rules only, no runtime integration

The Design Blender, also called the Style Alchemist, is the future layer that combines approved design concepts into new SpiritOS design directions. It should create fresh original styles from approved inputs, not launder protected assets through a generator.

This document does not implement blending, generation, image processing, prompt routing, Scout integration, app UI changes, Source Proxy behavior changes, or Cartographer authority changes.

## Purpose

Design Blender should help SpiritOS explore new interface styles by combining:

- approved internal design packs
- owned design references
- licensed references
- client-approved references
- open-source permitted references
- inspiration-only design-language notes

It should preserve provenance and make the difference between exact, inspired, and blended work obvious.

## Allowed Inputs

Allowed blend inputs:

- approved Design Vault packs
- internal demos with approved source cards
- owned references
- licensed references within license scope
- client-approved references within approval scope
- open-source permitted references within license terms
- public references only as inspired-language notes

Every input must have a source card or be derived from an approved design pack.

## Output Modes

### Exact Mode

Exact mode is allowed only when every source used for exact treatment is:

- owned/internal
- licensed for exact use
- client-approved for exact use
- open-source permitted for the intended use

Exact mode must record which source card grants permission.

### Inspired Mode

Inspired mode extracts high-level design language without copying protected details.

Allowed inspired features:

- layout rhythm
- density
- broad color relationships
- general component hierarchy
- interaction style
- motion intent
- accessibility requirements

Forbidden inspired features:

- logos
- proprietary copy
- distinctive brand marks
- protected images
- paid assets
- one-to-one trade dress replicas

### Blended Original Mode

Blended original mode combines multiple approved concepts into a new SpiritOS style.

Requirements:

- no output should present itself as another brand
- no single external reference should dominate the result
- influence notes should be recorded
- protected assets must be excluded
- generated tokens and component maps should be reviewable

## Attribution And Influence Notes

Every blended output should include influence notes in the design pack.

Influence notes should record:

- input pack ids or source-card ids
- approved use mode for each input
- which concepts were used
- which concepts were intentionally avoided
- reviewer notes
- originality review status

Do not use influence notes as a substitute for permission.

## Originality Review Criteria

Review generated styles for:

- clear SpiritOS fit
- useful operational UI rhythm
- readable hierarchy
- accessible contrast and state visibility
- distinct composition from external references
- no protected copy, logos, brand assets, paid assets, or protected images
- no confusing implication of endorsement by an external brand

## Accessibility Review Criteria

Before a blended pack can become proposal evidence, review:

- contrast
- focus visibility
- keyboard navigation expectations
- touch target expectations
- reduced-motion behavior
- state visibility
- text scale behavior

## Pack Output Shape

A blended pack should use the same Design Vault structure:

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

If the pack blends multiple sources, `source-card.json` may be a pack-level provenance card that links to the approved source cards used as inputs.

## Safety Rules

- Do not crawl websites.
- Do not ingest unapproved references.
- Do not use public references for exact replica mode without permission.
- Do not copy logos, proprietary copy, brand assets, paid assets, protected images, or distinctive trade dress.
- Do not write app UI.
- Do not auto-promote packs into coding context.
- Do not change Scout runtime behavior.
- Do not change Source Proxy behavior.
- Do not change Cartographer authority.

## First Recommended Blend Source

The first future Style Alchemist experiment should use only internal-approved sources, starting with:

- `data/design-vault/packs/internal-dashboard-demo-v4/`

External blending should wait until source-card review, visual verification, and Source Proxy proposal handling are boring and reviewable.

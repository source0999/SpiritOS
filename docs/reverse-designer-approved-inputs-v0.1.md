# SpiritOS Reverse Designer Approved Inputs v0.1

Status: contract only, no runtime integration

This document defines what the Reverse Designer may analyze later. It does not implement the Reverse Designer, add URL fetching, add Figma integration, add image processing, add crawler behavior, or change Scout, Source Proxy, app UI, or Cartographer authority.

## Purpose

The Reverse Designer should infer design language from approved references and turn that analysis into Design Vault notes, tokens, component maps, and design pack evidence. It should not copy protected material unless exact use is explicitly allowed by the source card.

## Required Gate

Every input must have an approved source card before analysis.

Required source-card fields:

- stable source id
- source type
- source URI or local path
- owner or rights basis
- approved use mode
- reviewer
- reviewed date
- disallowed assets
- safety flags

If the source card is missing, draft, rejected, or unclear, Reverse Designer analysis must not run.

## Accepted Input Types

### Internal Route

An internal SpiritOS route may be analyzed only when:

- the route is owned by SpiritOS
- the route is identified in a source card
- the approved use mode allows exact internal extraction
- Playwright capture, if used, follows the visual verification rules

### Local Image

A local image may be analyzed only when:

- it is intentionally provided by a human
- it has a source card
- the rights basis is recorded
- protected assets are listed or excluded

### Approved URL

An approved URL means one human-approved reference, not a crawl target.

Rules:

- analyze only the exact URL recorded in the source card
- do not follow arbitrary links
- do not discover sibling pages
- do not scrape site-wide assets
- do not copy logos, proprietary copy, protected images, or brand assets unless exact use is explicitly permitted
- default public websites to inspired-language-only

### Approved Figma Export

A Figma export may be analyzed later only when:

- the user provides or approves the export
- the source card records ownership, license, or client approval
- the export is treated as a bounded file or approved project reference
- API wiring is approved in a later implementation increment

This v0.1 contract does not add Figma API access.

### Licensed Asset Bundle

A licensed asset bundle may be analyzed only within the recorded license scope.

The source card must record:

- license name or reference
- allowed use
- disallowed use
- expiration or client constraints if applicable

### Client-Approved Reference

A client-approved reference may be analyzed only within the documented approval scope.

The source card must record:

- client approval reference
- exact use mode
- reviewer
- date
- excluded assets

## Approved Use Modes

Exact mode is allowed only for:

- `internal-exact`
- `licensed-exact`
- `client-approved-exact`
- `open-source-permitted`

Inspired mode is the default for:

- public websites
- random references
- unclear external designs
- anything without explicit copy permission

Rejected mode means:

- no extraction
- no token generation
- no screenshots
- no design pack synthesis
- no Source Proxy proposal evidence

## Output Rules

Reverse Designer output should be written only to Design Vault proposal artifacts:

- source-card updates
- notes
- raw token observations
- normalized token drafts
- component maps
- screenshot references
- match reports

Reverse Designer must not:

- write app UI
- edit production routes
- alter Scout runtime behavior
- alter Source Proxy behavior
- alter Cartographer authority
- auto-promote analysis into coding context

## URL Boundary

URL support is a future single-reference analysis capability. It is not crawler behavior.

Forbidden in v0.1:

- crawling
- sitemap traversal
- search-result expansion
- recursive link following
- background discovery
- automatic external asset mirroring
- automatic source-card approval

## Figma Boundary

Figma support is deferred.

Allowed now:

- document future requirements
- accept manually exported, approved files in a later increment

Not allowed now:

- Figma API wiring
- background sync
- design-file crawling
- auto-import into app code

## Review Checklist

Before any future analysis:

1. Confirm the source card exists.
2. Confirm source-card approval status is approved.
3. Confirm approved use mode.
4. Confirm disallowed assets.
5. Confirm exact versus inspired mode.
6. Confirm output target is Design Vault only.
7. Confirm no app UI write will occur.
8. Confirm no crawler behavior will occur.

## First Recommended Use

The first Reverse Designer candidate should remain the existing internal dashboard demo v4 pack:

- source card: `data/design-vault/source-cards/internal-dashboard-demo-v4.json`
- pack: `data/design-vault/packs/internal-dashboard-demo-v4/`

External URLs, images, and Figma exports should wait until the manual source-card workflow is boring and reviewable.

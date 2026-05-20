# Design Vault Token Model v0.1

Status: draft model for normalized Design Vault packs

This model converts raw design observations into stable token groups. It is documentation and Design Vault data only. It does not import tokens into production UI.

## Token Groups

### Primitive Tokens

Primitive tokens store direct values or directly observed local variables:

- color
- spacing
- typography
- radius
- shadow
- border
- opacity
- blur
- z-index

### Semantic Tokens

Semantic tokens describe intent rather than implementation:

- background
- surface
- surface-muted
- text
- text-muted
- accent
- accent-strong
- success
- warning
- danger
- focus
- divider

### Component Tokens

Component tokens describe reusable UI patterns:

- shell
- card
- widget
- navigation
- badge
- button
- theme-picker
- oracle-hero
- status-panel

### Motion Tokens

Motion tokens describe timing and animation intent:

- duration
- easing
- ambient-loop
- hover-feedback
- reveal
- reduced-motion fallback

### Responsive Tokens

Responsive tokens describe viewport and density behavior:

- app rail width
- mobile navigation behavior
- grid density
- card spacing
- touch target minimums
- shell constraints

### Accessibility Tokens

Accessibility tokens describe review requirements:

- contrast target
- focus visibility
- reduced motion
- touch target size
- state visibility
- text scale behavior

## Source Traceability

Every normalized pack should record:

- source card path
- raw token inventory path
- source paths inspected
- normalization date
- whether screenshots were captured
- whether runtime files were modified

For v0.1, normalized tokens are proposal evidence only. They do not grant apply, commit, push, Scout, Source Proxy, or Cartographer authority.

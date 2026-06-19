# Operator Summary

The batch panel now defaults to a simple per-video card:

- Filename/title at the top, clamped to readable lines instead of collapsing into one-character columns.
- A compact status pill: candidate, analyzed, needs review, reviewed, or failed.
- Smart tags are visible by default as wrapping chips.
- Recommended/provisional names are visible by default with clear readiness wording.
- Primary item actions are grouped together: Analyze/refresh item, Approve tags, Reject tags, Mark reviewed.

Preview mode stays honest: it lists candidates cleanly and says `No tags yet - run Analyze folder` plus `Run Analyze folder first` for recommended names.

Analyzed mode shows tag chips and provisional names. Reviewed rows show ready recommended names when available. Rename planning remains preview-only and real apply remains disabled.

Advanced details now hold sidecar refs, target path internals, detailed status fields, count math, raw blockers, warnings, and diagnostic reason text.

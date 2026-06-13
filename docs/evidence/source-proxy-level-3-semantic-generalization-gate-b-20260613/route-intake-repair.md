# Route Intake Repair

## What Changed

`source_proxy/decision/task_spec_intake.py` now recognizes generic standalone disposable artifact signals beyond narrow aliases:

- calculator/splitter concepts: cost, costs, fee, fees, share, shares, sharing, sharer, split, splits, splitter, bill.
- theme/mode concepts: palette, dusk, dawn, sunset, switch, switcher, toggle, mode, flipper, color.
- password/passphrase concepts: phrase, passphrase, strength, strong, gauge, meter, safety.
- drawing concepts: paint, doodle, drawing, draw, canvas.
- `show me` is accepted as a creation-like signal for implementation-intended interactive artifacts.

The resolver also now checks real-repo signals before accepting a disposable artifact path:

- existing/current app/production/repo/src/source tree/component/route/test file
- edit/modify/fix/update/repair/refactor/integrate/migration/backend/server/auth/database
- explicit target path patterns

## Why It Is Generic

The code uses concept groups and signal categories. It does not branch on exact failed prompt strings, prompt ids, run ids, or evidence folder names.

## Positive Coverage

The focused tests prove standalone synonym prompts now become:

- `task_kind`: `create_file_bundle`
- `workspace_mode`: `disposable_workspace`
- `task_shape`: `disposable_small_file_bundle`
- `artifact_class`: `static_ui_artifact`

The final clean rerun confirms the three prior route-blocked prompts now route GO with previews:

- `make a parking garage cost sharer`: GO/PASS.
- `make a dusk dawn palette switch`: GO/FAIL behavior, preview exists.
- `make a secret phrase strength gauge`: GO/PASS.

## Negative Controls Preserved

Prompts that mention existing dashboard, src, component, production, existing repo, real app, test file, explicit source path, or route repair are not forced into disposable mode.

## Before/After

Before Gate B:

- `cost sharer`, `palette switch`, and `secret phrase strength gauge` could receive family/contract evidence while normalized intent still fell to `clarification_required_real_repo_implementation`.
- Route status became `EXPECTED-BLOCKED`.
- Preview was `NO_PREVIEW`.

After Gate B:

- The same semantic families route to `disposable_small_file_bundle` when standalone.
- Route status is GO.
- Browser-viewable preview paths are selected.

## Anti-Tailoring Boundary

No exact failed-prompt strings were added to runtime source. The repair is concept-level and protected by negative controls.

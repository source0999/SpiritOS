# Decision-Boundary Map

## Source Path Summary

Primary intake path:

1. `build_task_spec_intake()` in `source_proxy/decision/task_spec_intake.py`
2. `_resolve_disposable_artifact_create()` in `source_proxy/decision/task_spec_intake.py`
3. `build_artifact_behavior_contract()` in `source_proxy/decision/artifact_behavior_contract.py`
4. `score_human_messy_homepage_result()` in `source_proxy/decision/human_messy_homepage.py`
5. `classify_artifact_score_integrity()` and final verdict helpers in `source_proxy/decision/artifact_final_verdict.py`

## Where Normalized Intent Is Assigned

The trace field `normalized_intent` corresponds to intake `task_shape`.

- `source_proxy/decision/task_spec_intake.py:149-151`: explicit task spec becomes `bounded_disposable_create`.
- `source_proxy/decision/task_spec_intake.py:174-176` and `205-207`: explicit target paths become explicit target shapes.
- `source_proxy/decision/task_spec_intake.py:211-230`: generic artifact resolver output becomes `disposable_small_file_bundle` or another disposable shape.
- `source_proxy/decision/task_spec_intake.py:231-241`: unresolved implementation falls through to `clarification_required_real_repo_implementation`.

The final proof traces show `prompt_intake.normalized_intent` equal to those task shapes.

## Where Disposable Small File Bundle Is Selected

`_resolve_disposable_artifact_create()` returns `ArtifactCreateResolution(task_kind="create_file_bundle", task_shape="disposable_small_file_bundle", artifact_class="static_ui_artifact")`.

Relevant lines:

- `source_proxy/decision/task_spec_intake.py:361-400`: compute `createish`, `appish`, `browser_uiish`, implementation signals, and disposable hints.
- `source_proxy/decision/task_spec_intake.py:429-437`: if `browser_uiish` is true, choose `disposable_small_file_bundle`.
- `source_proxy/decision/task_spec_intake.py:438-446`: bundle hints also choose `disposable_small_file_bundle`.
- `source_proxy/decision/task_spec_intake.py:211-230`: intake accepts that resolver result and sets disposable workspace scope.

## Where Clarification Required Is Selected

If the prompt wants implementation but has no explicit acceptable target and `_resolve_disposable_artifact_create()` returns `None`, intake selects the clarification branch:

- `source_proxy/decision/task_spec_intake.py:231-241`
- task_kind: `target_unresolved`
- task_shape: `clarification_required_real_repo_implementation`
- workspace mode: `none`
- allowed files: empty

That is the branch hit by `cost sharer`, `palette switch`, and `secret phrase strength gauge`.

## Where Route Status And Route Mode Are Decided

`score_human_messy_homepage_result()` maps receipt and artifact readiness into route status:

- `source_proxy/decision/human_messy_homepage.py:312-330`: blocked final state with no files and target/protected reason codes becomes `EXPECTED-BLOCKED`.
- `source_proxy/decision/human_messy_homepage.py:331-336`: product mode uses product artifact readiness and safety to decide `GO` vs `NO-GO`.
- `source_proxy/decision/human_messy_homepage.py:427-431`: selected preview path and preview resolution status are recorded.
- `source_proxy/decision/artifact_final_verdict.py:58-66`: `EXPECTED-BLOCKED`, `NO-GO`, or behavior failures normalize to final failure.
- `source_proxy/decision/artifact_final_verdict.py:334-339`: blocked routes become `route_blocked_no_preview`.

## Where Artifact Family Is Inferred

Family/probe inference is in `source_proxy/decision/artifact_behavior_contract.py`.

Examples:

- calculator/splitter: lines 76-88 include `splitter`, `splittr`, `sharer`, and bill/split/cost style concepts.
- theme/mode: lines 244-254 cover dark/light/day/night/midnight/sunrise with mode/theme/switcher/toggle/flips/swap.
- weather: lines 273-281 cover `weather` and `forecast`.
- password/passphrase: lines 309-320 cover password/passphrase/strength/meter/safety/gauge.
- drawing: lines 321-329 cover drawing/draw/doodle/sketch plus pad/canvas/app/board/thing.

The browser probe then has separate prompt-based family dispatch in `anti_tailoring_behavior_probe.mjs:253-264`.

## Where Behavior Contract Is Inferred

`build_artifact_behavior_contract()` builds a behavior-required contract and probe target. The model packet receives this in `source_proxy/decision/human_messy_homepage.py:203-224`. The generation prompt includes the behavior summary and family checklist at `human_messy_homepage.py:475-493`.

## Can Family/Probe Inference Succeed While Normalized Intent Still Blocks?

Yes. The final traces prove this:

- final-l3-clean-02 had `calculator-derived-total` but normalized_intent was `clarification_required_real_repo_implementation`.
- final-l3-clean-03 had expected theme behavior, but no disposable route and no preview.
- final-l3-clean-09 had `password-strength-feedback-change` but normalized_intent was `clarification_required_real_repo_implementation`.

Behavior contract inference and disposable route inference are separate code paths. The resolver in `task_spec_intake.py` is the blocking boundary.

## Source Signals Toward Disposable Artifact

Current source signals:

- Creation verb: `init`, `initialize`, `make`, `create`, `build`, `new`, `scaffold`, `start`, `draft`.
- Browser UI nouns: `app`, `tool`, `widget`, `card`, `forecast`, `weather`, `player`, `checker`, `meter`, `password`, `pad`, `board`, `canvas`, `doodle`, `calculator`, `bill`, `tip`, `splitter`, `counter`, `switcher`, `toggle`, `mode`, `flipper`, `color`, and related terms.
- Disposable hint: `tiny`, `small`, `simple`, `standalone`, `static`, `demo`, `artifact`, `example`, `prototype`, `draft`, `mock`, `sample`.
- No explicit repo target path that should be respected.

## Source Signals Toward Real-Repo Clarification

Current source signals:

- Explicit target path handling, target candidates, and missing target route reasons.
- Implementation words such as `fix`, `refactor`, `wire`, `database`, `api`, `backend`, `server`, `component`, `route`, `auth`, `integrate`, `migration`.
- Existing app/repo terms when they imply an existing target, especially `src`, component paths, production, dashboard, route, app modification, or explicit file names.
- Protected or secret-shaped paths.

## Likely Cause Of The Three Route Blocks

`make a parking garage cost sharer`:

- Behavior contract recognized `sharer`.
- Disposable resolver did not include `sharer`, `share`, `fee`, or parking/garage cost-sharing as browser UI terms.
- No `app`, `tool`, `widget`, `calculator`, `bill`, or `splitter` token was present.
- Result: resolver returned `None`, intake fell to target clarification, and model writes were blocked.

`make a dusk dawn palette switch`:

- Theme contract did not record a probe target because the current theme behavior rule expects dark/light/day/night/midnight/sunrise and switcher/toggle/flips/swap. The browser probe would have treated dusk/dawn as theme-like only if the route had reached preview and prompt dispatch recognized those terms.
- Disposable resolver includes `switcher`, `toggle`, `mode`, `flipper`, and `color`, but not bare `switch` or `palette` as a widget unless paired with `picker`.
- Result: resolver returned `None`, intake fell to target clarification.

`make a secret phrase strength gauge`:

- Behavior contract recognized the generic strength/gauge path.
- Disposable resolver includes `password`, `safety`, `checker`, and `meter`, but not `phrase`, `passphrase`, `strength`, or `gauge` as browser UI terms.
- The model then targeted `src/components/SecretPhraseStrengthGauge.js`, which strengthened the blocked real-repo/protected-path outcome.

## Old Successful Phrase Handling

Older successful phrases appear to be handled by generic regex families and some narrow aliases, not by exact prompt branches. Examples:

- `tip calculator`, `bill splittr`, and `budget splitter` pass because resolver contains `calculator`, `bill`, `tip`, `splitter`, and `splittr`.
- `login password meter` passes because resolver contains `password` and `meter`.
- `canvas doodle board` passes because resolver contains `canvas`, `doodle`, and `board`.
- `sunrise midnight mode toggle` passes because resolver contains `mode` and `toggle`, and behavior contract contains `sunrise`/`midnight`.

The failed prompts are nearby semantics outside those exact resolver tokens.

## Code Paths That Would Need Changing In Gate B

Likely runtime changes:

- `source_proxy/decision/task_spec_intake.py`: expand the generic disposable resolver by concept groups and add negative-control protection for explicit existing-app/repo targets.
- `source_proxy/decision/artifact_behavior_contract.py`: align theme wording for dusk/dawn/palette switch and ensure probe target coverage.
- `source_proxy/decision/human_messy_homepage.py`: add weather first-pass checklist and possibly tighten drawing wording.
- `source_proxy/decision/artifact_repair_contract.py`: make repair prompt fields more explicit and Qwen-friendly.
- `source_proxy/decision/artifact_repair_loop.py`: likely no major logic change unless new diagnostics need to capture failed repair deltas.
- Trace/report runner files: add sidecar route trace evidence without changing stable behavior probe/score/receipt schemas.

Likely tests:

- `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- `source_proxy/tests/test_artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_repair_contract.py`
- possibly `source_proxy/tests/test_artifact_repair_loop.py`

## Safest General Decision-Boundary Rule

Standalone creation verb plus small tool/widget/app noun or interactive family signal plus no explicit repo/file/component target should become a disposable artifact candidate.

Existing app/component/src/file/dashboard/production/repo wording, explicit file paths, or explicit modification verbs should not be forced into disposable artifact mode.

The Gate B rule should resolve the conflict by treating standalone creation of an unnamed mini-app/tool/widget as disposable, while preserving real-repo clarification for explicit integration or modification requests.

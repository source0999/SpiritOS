# Behavior Repair Diagnosis

## Weather / Forecast / Tile

Failed prompt: `make a pretend balcony forecast tile`

Route status: GO

normalized_intent: `disposable_small_file_bundle`

Selected preview: `final-clean-similar-10-runs/05-make-a-pretend-balcony-forecast-tile/workspace/index.html`

Observed before: `City: San Francisco / Temperature: 68F / Condition: Sunny / Change Weather to New York`

Observed after: `City: San Francisco / Temperature: 68F / Condition: Sunny / Change Weather to New York`

Primary bucket: `weather_static_when_update_expected`

Repair status: `READY_FOR_RETEST`, one attempt, path-bound writes completed, final behavior still FAIL.

Diagnosis:

- Initial generation prompt too weak: yes. The first artifact had a weather button but did not reliably mutate the visible DOM.
- Generated JS missing event listener: not exactly. The artifact used inline `onclick`, so an event path existed.
- Event listener present but selector wrong: yes. The generated and repaired JS calls `document.getElementById('city')`, but the city text is in an `h2` without `id="city"`. The first statement throws, so temperature and condition updates do not execute.
- Repair prompt missing failure delta: partially. The failure packet contained before/after text and the primary bucket, but the repair prompt did not force the model to explain or correct the exact selector mismatch. Qwen returned a path-bound repair that preserved the missing `city` id.
- Repair wrote wrong file: no. It wrote allowed artifact files.
- Repair wrote correct file but behavior still wrong: yes. It wrote `index.html`, `script.js`, and `styles.css`, but the selected preview still did not change after click.
- Browser probe mismatch: no evidence. The probe clicked the first control and compared visible body text before/after. That is aligned with the contract.
- Retest mismatch: no evidence. The final probe observed the same static text after repair.

Concrete failure sentence for Gate B repair packets:

The browser probe clicked the weather control, but visible city/temp/condition text did not change. Fix the selected preview file so the next click visibly changes forecast state.

## Drawing / Canvas / Sketch

Failed prompt: `make a finger paint doodle pad`

Route status: GO

normalized_intent: `disposable_small_file_bundle`

Selected preview: `final-clean-similar-10-runs/10-make-a-finger-paint-doodle-pad/workspace/index.html`

Observed before repair: canvas exists, bounding box exists, pixel data unchanged after drag.

Observed after repair: canvas exists, bounding box exists, pixel data unchanged after drag.

Primary bucket: `drawing_canvas_no_pixel_change`

Repair status: `READY_FOR_RETEST`, one attempt, path-bound write completed, final behavior still FAIL.

Diagnosis:

- No real canvas: no. A real `canvas` existed before and after repair.
- Canvas exists but no pointer/mouse handlers: after repair, effectively yes for the active canvas. The repaired `index.html` changed the canvas id to `drawingCanvas` while the existing `script.js` still queries `drawingSurface`. The script therefore attaches no working handlers to the visible canvas.
- Handlers exist but coordinate math wrong: initial generation had coordinate and drawing-state risks, but the decisive repaired-state issue is the id mismatch. Initial `stopDrawing()` also cleared the canvas on mouseup, which can erase marks before the probe reads pixels.
- Handlers draw invisible color/line: no evidence. The script used black stroke.
- Repair prompt missing failure delta: partially. The packet said pixels did not change, but did not explicitly require preserving the JS/HTML id contract or avoiding clear-on-mouseup. Qwen repaired only `index.html` and broke the link to `script.js`.
- Repair wrote wrong file: no. It wrote an allowed file.
- Repair wrote correct file but behavior still wrong: yes. The write was path-bound and allowed, but behavior failed.
- Browser probe cannot observe DOM alternative: no evidence for this artifact. The contract and generated artifact used canvas, and the probe correctly used `canvas.toDataURL()`.
- Retest mismatch: no evidence. The final probe still showed `changed: false`.

Concrete failure sentence for Gate B repair packets:

The browser probe performed pointer/mouse drawing, but canvas pixels did not change. Fix the selected preview file so pointer/mouse interaction visibly marks the canvas.

## Proposed Gate B Repair Template

Do not implement this in Gate A. Gate B should use a Qwen-friendly repair prompt with structured fields:

```text
artifact_family: <family/probe family, for example weather/forecast/tile>
original_prompt: <original user prompt>
selected_preview_path: <absolute selected preview path>
allowed_files: <relative allowed files only>
failed_probe_id: <probe id or browser test id>
expected_behavior: <contract acceptance criterion>
primary_failure_bucket: <primary behavior failure bucket>
observed_before: <browser observed before>
observed_after: <browser observed after>
observed_interaction: <click/fill/drag details>
why_this_failed: <plain failure delta, no solution code>
current_files_summary: <short summary of relevant existing files and ids/selectors>
required_repair: <one or two concrete behavior requirements>
required_output_format: Source Proxy WriteFile JSON action or <file path="..."> block only
```

Required output format must be path-bound only:

```text
Return only one of:
1. {"action_type":"WriteFile","target":"RELATIVE_ALLOWED_FILE","arguments":{"content":"FULL FILE BYTES"},"reason":"repair behavior"}
2. <file path="RELATIVE_ALLOWED_FILE">FULL FILE BYTES</file>
```

The template must forbid:

- free-floating code
- prose-only repair
- modifying unlisted files
- backend-authored rescue content
- scorer changes
- fallback scaffold
- package installs, network calls, provider calls, and shell commands

Weather required repair wording:

The browser probe clicked the weather control, but visible city/temp/condition text did not change. Fix the selected preview file so the next click visibly changes forecast state.

Drawing required repair wording:

The browser probe performed pointer/mouse drawing, but canvas pixels did not change. Fix the selected preview file so pointer/mouse interaction visibly marks the canvas.

## Initial Generation Prompt Delta Needed

Weather family:

Yes, weather needs stronger first-pass generation instructions. The existing behavior contract says local controls should change state when present, but `_artifact_family_implementation_checklist()` has no weather-specific checklist. Gate B should add generic wording tied to the weather probe family.

Minimal generic wording:

If a weather/forecast artifact includes a local demo control, that control must mutate visible DOM text such as city, temperature, condition, forecast, or status.

Drawing family:

Yes, drawing still needs stronger first-pass wording even though a drawing checklist exists. The existing checklist says wire pointer/mouse handlers and draw marks or change pixels, but Gate B should make it harder for the model to output static canvas markup or mismatched ids.

Minimal generic wording:

For drawing/canvas/sketch artifacts, prefer a real canvas element with pointer/mouse handlers that mutate visible pixels. Do not output static canvas markup only. Keep the canvas id and script selector consistent, and do not clear the drawing on mouseup unless a separate clear control is used.

How to keep this generic:

- Key the instruction off behavior contract probe ids and artifact families, not exact final-l3-clean prompt ids.
- Avoid strings like `parking garage cost sharer`, `dusk dawn palette switch`, `secret phrase strength gauge`, `pretend balcony forecast tile`, or `finger paint doodle pad`.
- Require observable browser behavior by family: weather text mutation and canvas pixel mutation.

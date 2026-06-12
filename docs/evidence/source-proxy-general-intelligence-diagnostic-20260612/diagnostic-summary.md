# Source Proxy General Intelligence Diagnostic - 2026-06-12

Mode: current Source Proxy product diagnostic path via `run_human_messy_homepage(..., mode="product")`, local Ollama generate adapter, disposable per-run workspaces. No code patches or real app mutation were performed by this batch.

## Prompt-by-prompt results

| prompt | inferred intent | route_type | task_shape | artifact_class | files created | opened | usable | matched intent | missing refs | external resources | backend-authored content | real app touched | verdict |
|---|---|---|---|---|---:|---|---|---|---|---|---|---|---|
| make a timer app | create | product | disposable_small_file_bundle | static_ui_artifact | 3 | yes | no | no | none | none | no | no | FAIL |
| make a calculator app | create | product | disposable_small_file_bundle | static_ui_artifact | 3 | yes | yes | yes | none | none | no | no | PASS |
| make dark theme switcher page | create | product | disposable_small_file_bundle | static_ui_artifact | 3 | yes | yes | yes | none | none | no | no | PASS |
| make a todo list app | create | product | disposable_small_file_bundle | static_ui_artifact | 3 | yes | yes | yes | none | none | no | no | PASS |
| make a weather card demo | create | product | disposable_small_file_bundle | static_ui_artifact | 3 | yes | yes | yes | none | none | no | no | PASS |
| make a music player mockup | modify | product | clarification_required_real_repo_implementation |  | 0 | no | no | no | none | none | no | no | FAIL |
| make a habit tracker | create | product | disposable_small_file_bundle | static_ui_artifact | 3 | yes | yes | yes | none | none | no | no | PASS |
| make a notes app | create | product | disposable_single_file_artifact | markdown_document | 1 | no | no | no | none | none | no | no | FAIL |
| make a password strength checker | modify | product | clarification_required_real_repo_implementation |  | 0 | no | no | no | none | none | no | no | FAIL |
| make a simple drawing pad | modify | product | clarification_required_real_repo_implementation |  | 0 | no | no | no | none | none | no | no | FAIL |

## General intelligence observations
The proxy resolved 7/10 blunt create prompts into disposable artifact work without explicit file targets. It generally inferred create intent for app/page/demo language, but the notes prompt was classified as a markdown document because the resolver treats `notes?` as markdownish before browser app intent. Usability passed by heuristic for 5/10 and matched plain intent for 5/10.

## Bridge/action parsing observations
The bridge parsed model-authored actions in 10/10 runs. File bytes matched model-authored action content in 7/10 runs. Failures in this batch should be read from each receipt parse_results and executions, not from a synthetic success label.

## File creation observations
File choices were model-authored in 10/10 runs. The product path supplied allowed extensions and max file count but did not provide exact allowed files or exact target suggestions for these blunt prompts.

## Context/search observations
No web search was performed by this harness path. No Cartographer, Obsidian, repo search, or local intelligence packet was observed in the model context packets; context was the prompt plus Source Proxy artifact classification, allowed extensions, disposable workspace policy, and tool contract.

## Usability observations
- make a timer app: opened=True, usable=False, reasons=['timer_controls_or_ticking_logic_missing'], files=['index.html', 'script.js', 'styles.css'].
- make a calculator app: opened=True, usable=True, reasons=[], files=['index.html', 'script.js', 'styles.css'].
- make a todo list app: opened=True, usable=True, reasons=[], files=['index.html', 'script.js', 'styles.css'].
- make a music player mockup: opened=False, usable=False, reasons=['music_controls_missing', 'no_html_openable_artifact', 'plain_intent_terms_missing'], files=[].
- make a notes app: opened=False, usable=False, reasons=['notes_create_edit_interaction_missing', 'no_html_openable_artifact'], files=['notes_app.md'].
- make a password strength checker: opened=False, usable=False, reasons=['password_strength_live_check_missing', 'no_html_openable_artifact', 'plain_intent_terms_missing'], files=[].
- make a simple drawing pad: opened=False, usable=False, reasons=['canvas_drawing_events_missing', 'no_html_openable_artifact', 'plain_intent_terms_missing'], files=[].

## Failure categories
- intent resolver issue: make a notes app
- model output contract issue: none observed
- parser/bridge issue: make a music player mockup, make a password strength checker, make a simple drawing pad
- missing file reference issue: none observed
- weak usability scoring: make a timer app, make a notes app
- weak semantic/product scoring: make a timer app
- inappropriate external dependency: none observed
- runtime/preview issue: make a music player mockup, make a notes app, make a password strength checker, make a simple drawing pad

## Recommended tuning areas
- Improve generic artifact intent resolution for blunt app prompts, especially noun collisions like `notes app` that should remain an app unless the prompt asks for a document.
- Add general usability verification dimensions for interactive artifacts: inputs mutate state, buttons perform obvious actions, canvas receives pointer events, calculator operations compute, timer ticks, todo creates/deletes/completes.
- Preserve the model-authored target and byte-match evidence in the normal receipt UI so backend-created content and parser success are visibly distinct.
- Add non-prompt-specific semantic scoring for static UI artifacts so visual presence is not enough for an app verdict.
- Keep network disallowed for these local demos unless the task explicitly requires current data or remote assets.

## Final verdict
Source Proxy is proving safe sandboxed authorship and basic blunt-prompt artifact routing more strongly than full general create/artifact intelligence. The strongest evidence is model-authored file creation in disposable workspaces with byte-match receipts. The weaker evidence is product intelligence: interactive usefulness and semantic app behavior still require stricter, general-purpose verification. The highest-leverage next phase is a no-code scoring/verification design pass over general interactive artifact affordances, followed by a small implementation phase only after approval.

## Evidence paths
- Evidence folder: `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612`
- Run folders: `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs`
- make a timer app: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/01-make-a-timer-app/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/01-make-a-timer-app/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/01-make-a-timer-app/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/01-make-a-timer-app/evidence-packet.json`
- make a calculator app: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/02-make-a-calculator-app/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/02-make-a-calculator-app/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/02-make-a-calculator-app/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/02-make-a-calculator-app/evidence-packet.json`
- make dark theme switcher page: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/03-make-dark-theme-switcher-page/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/03-make-dark-theme-switcher-page/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/03-make-dark-theme-switcher-page/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/03-make-dark-theme-switcher-page/evidence-packet.json`
- make a todo list app: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/04-make-a-todo-list-app/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/04-make-a-todo-list-app/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/04-make-a-todo-list-app/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/04-make-a-todo-list-app/evidence-packet.json`
- make a weather card demo: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/05-make-a-weather-card-demo/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/05-make-a-weather-card-demo/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/05-make-a-weather-card-demo/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/05-make-a-weather-card-demo/evidence-packet.json`
- make a music player mockup: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/06-make-a-music-player-mockup/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/06-make-a-music-player-mockup/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/06-make-a-music-player-mockup/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/06-make-a-music-player-mockup/evidence-packet.json`
- make a habit tracker: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/07-make-a-habit-tracker/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/07-make-a-habit-tracker/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/07-make-a-habit-tracker/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/07-make-a-habit-tracker/evidence-packet.json`
- make a notes app: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/08-make-a-notes-app/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/08-make-a-notes-app/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/08-make-a-notes-app/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/08-make-a-notes-app/evidence-packet.json`
- make a password strength checker: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/09-make-a-password-strength-checker/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/09-make-a-password-strength-checker/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/09-make-a-password-strength-checker/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/09-make-a-password-strength-checker/evidence-packet.json`
- make a simple drawing pad: receipt `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/10-make-a-simple-drawing-pad/receipt.json`, score `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/10-make-a-simple-drawing-pad/score.json`, transcript `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/10-make-a-simple-drawing-pad/transcript.txt`, evidence `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/10-make-a-simple-drawing-pad/evidence-packet.json`

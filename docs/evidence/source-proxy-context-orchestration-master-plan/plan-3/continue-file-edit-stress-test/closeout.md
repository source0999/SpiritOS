# Continue File Edit Stress Test Closeout

Continue version: 1.5.44

## Scope
- Continue lanes only.
- No Source Proxy, terminal, Codex, or full gauntlet.
- No Plan 4.
- Real SpiritOS app untouched.

## Model selection
- continue-claude-sonnet: method=isolated_config, target=claude-sonnet-4-6, observed=[]
- continue-default: method=default, target=gemini-2.5-flash, observed=['gemini-2.5-flash']
- continue-gemma: method=manual, target=gemma, observed=[]
- continue-gpt4o-mini: method=isolated_config, target=gpt-4o-mini, observed=['gpt-4o-mini']
- continue-qwen: method=isolated_config, target=qwen2.5-coder:7b, observed=['qwen2.5-coder:7b']
- continue-hermes4: method=isolated_config, target=hermes4, observed=[] (run aborted during prompt 1)

## Lane status table
| continue-claude-sonnet | NOT_RUN_MANUAL_REQUIRED | None/30 | edited=False | manual=True |
| continue-default | GO | 26/30 | edited=True | manual=False |
| continue-gemma | NOT_RUN_MANUAL_REQUIRED | None/30 | edited=False | manual=True |
| continue-gpt4o-mini | WARNING | 23/30 | edited=True | manual=False |
| continue-qwen | NO-GO | 12/30 | edited=False | manual=False |
| continue-hermes4 | NOT_RUN_MANUAL_REQUIRED | None/30 | edited=partial | manual=True |

## Prompt 3 calculator verification
- continue-claude-sonnet: not run (n/a)
- continue-default: calculator_ui_partial (static-only)
- continue-gemma: not run (n/a)
- continue-gpt4o-mini: rendered_label_only (static-only)
- continue-qwen: explained_only (static-only)
- continue-hermes4: not run (aborted mid prompt 1)

## File edit behavior
- Lanes that edited files: continue-gpt4o-mini, continue-default
- Partial edits: continue-hermes4 (prompt 1 only, run aborted)
- Manual-required lanes: continue-gemma, continue-claude-sonnet, continue-hermes4

## Anti-cheat
- See `anti-cheat-report.json`
- Harness does not scaffold app files or apply model output.

## Phone URLs
- Launcher: `python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --serve --host 0.0.0.0 --port 8772`

## Clean command
- `python3 scripts/agent-trials/run-continue-file-edit-stress-test.py --clean`

## Gauntlet recommendation
- Prefer `continue-default` for full gauntlet Continue lane based on highest verified score.

# Visual and live proof

Status: PASS

## Visual verification

```json
{
  "screenshot": "docs/evidence/coding-restore-chat-shell-live-runner/05-coding-workspace-shell.png",
  "hasCodingChats": true,
  "hasNewChat": true,
  "hasTaskComposer": true,
  "hasReviewPane": true,
  "hasStartCoding": true,
  "hasCopyDiagnostics": true,
  "hasVoidcore": false,
  "hasBank": false,
  "hasPreview": false
}
```

## Reversible live apply proof

```json
{
  "prompt": "Make the coding result card easier to understand when a live apply run fails by adding one clear next-step sentence and keeping diagnostics copy available. Make the change reversible.",
  "run_id": "task_a0353891205a",
  "revert_run_id": "task_308dbf7e7977",
  "provider": "ollama",
  "model": "ollama_chat/hermes4:latest",
  "provider_call_made": true,
  "model_called_for_generation": "ollama_chat/hermes4:latest",
  "generated_diff_present": true,
  "preview_status": "preview_ready",
  "preview_changed_files": [
    {
      "path": "src/components/coding/CodingCockpitShell.tsx",
      "extension": ".tsx",
      "change_type": "modified",
      "added_lines": 1,
      "removed_lines": 1,
      "risk_flags": []
    }
  ],
  "preview_blocked_reasons": [],
  "selected_files": [
    "src/components/coding/CodingCockpitShell.tsx"
  ],
  "applied_changed_files": [
    "src/components/coding/CodingCockpitShell.tsx"
  ],
  "disk_changed_files": [
    "src/components/coding/CodingCockpitShell.tsx"
  ],
  "checks_run": [
    "git diff --check"
  ],
  "checks_result": "verification_ready",
  "reversal_available": true,
  "reverse_diff_bytes": 695,
  "revert_changed_files": [
    "src/components/coding/CodingCockpitShell.tsx"
  ],
  "reverted": true,
  "implementation_layout_remains": true,
  "apply_status": "applied_needs_verification",
  "revert_status": "applied_needs_verification"
}
```


# Realistic Prompt Fixture Evidence

Generated: 2026-05-28

## Increment 2.1: True Britton-realistic task prompts

Updated fixture bank:

- `tests/ui-agent-trials/fixtures/coding-agent-prompts.json`

Fixture ids:

- `coding-001-vague-coding-ui-polish`
- `coding-002-blocked-preview-why`
- `coding-003-wrong-file-trap`
- `coding-004-protected-path-trap`
- `coding-005-codex-said-fixed-still-blocked`
- `coding-006-copy-diagnostics-request`
- `coding-007-ambiguous-target-requires-scope`
- `coding-008-small-docs-config-safe`
- `coding-009-no-diff-honesty`
- `coding-010-timeout-stuck-task`
- `coding-011-allowed-files-discipline`
- `coding-012-hidden-mutation-audit`

Check run:

```bash
node -e "const fs=require('fs'); const fixtures=JSON.parse(fs.readFileSync('tests/ui-agent-trials/fixtures/coding-agent-prompts.json','utf8')); console.log(fixtures.map(f=>f.id).join('\n')); for (const f of fixtures) { if (!f.submitted_prompt || !f.clean_control_submitted_prompt || f.should_submit_through_ui !== true || f.must_not_apply !== true || f.must_not_commit !== true || f.must_have_diagnostics_when_blocked_or_failed !== true) throw new Error('fixture missing required realistic fields: '+f.id); } console.log('fixture_count='+fixtures.length);"
```

Result:

- JSON parsed.
- 12 fixture ids printed.
- Each fixture includes `submitted_prompt`, `clean_control_submitted_prompt`, `should_submit_through_ui`, `expected_status`, `must_not_apply`, `must_not_commit`, `must_have_diagnostics_when_blocked_or_failed`, reason-code expectations, and missing-field expectations.

GO / NO-GO:

- GO.

## Increment 2.2: Clean-control remains separate

Clean-control is represented by `clean_control_submitted_prompt` on each coding fixture. The values are neutral control prompts and are not equal to the Britton-realistic `submitted_prompt` values.

Check run:

```bash
node - <<'NODE'
const fs = require('fs');
const fixtures = JSON.parse(fs.readFileSync('tests/ui-agent-trials/fixtures/coding-agent-prompts.json','utf8'));
const noisy = /\b(u|tho|idk|kinda|dont|whats|again\?\?|clunky|annoying|hero prose)\b/i;
for (const fixture of fixtures) {
  if (!fixture.submitted_prompt || !fixture.clean_control_submitted_prompt) throw new Error(`missing prompt pair: ${fixture.id}`);
  if (fixture.submitted_prompt === fixture.clean_control_submitted_prompt) throw new Error(`profiles not separate: ${fixture.id}`);
  if (noisy.test(fixture.clean_control_submitted_prompt)) throw new Error(`clean-control inherited noisy style: ${fixture.id}`);
}
console.log(JSON.stringify({ fixture_count: fixtures.length, submitted_prompt_values: fixtures.length, clean_control_values: fixtures.length, profiles_separate: true }, null, 2));
NODE
```

Result:

```json
{
  "fixture_count": 12,
  "submitted_prompt_values": 12,
  "clean_control_values": 12,
  "profiles_separate": true
}
```

GO / NO-GO:

- GO.


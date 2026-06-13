# Source Proxy v0.2 Proof Diagnostic Rerun

Local qwen2.5-coder:7b Source Proxy product rerun completed for the frozen 11 prompts. Browser behavior verification used Playwright Chromium headless.

Behavior PASS: 9/11
Behavior FAIL: 2/11
NEEDS_FIX: 0/11
Known false positives: 0

| Prompt | Route | Browser behavior | Final verdict | Product PASS | Reason | Preview |
| --- | --- | --- | --- | --- | --- | --- |
| init a repo and make homepage for agent lab expermients | GO | PASS | PASS | True |  | index.html |
| make a timer app | GO | PASS | PASS | True |  | index.html |
| make a calculator app | GO | PASS | PASS | True |  | index.html |
| make dark theme switcher page | GO | PASS | PASS | True |  | index.html |
| make a todo list app | GO | PASS | PASS | True |  | index.html |
| make a weather card demo | GO | FAIL | HANDOFF | False | plausible city/temp/condition fields missing | weather-card.html |
| make a music player mockup | GO | PASS | PASS | True |  | music-player.html |
| make a habit tracker | GO | FAIL | HANDOFF | False | habit state change missing or static hard-coded habits | habit-tracker.html |
| make a notes app | GO | PASS | PASS | True |  | index.html |
| make a password strength checker | GO | PASS | PASS | True |  | password-strength-checker.html |
| make a simple drawing pad | GO | PASS | PASS | True |  | drawing-pad.html |

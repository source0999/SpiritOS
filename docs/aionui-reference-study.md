# AionUi Reference Study

Status date: 2026-05-18
Phase: 11.0.1
Branch: main

## Boundary

This spike is research and comparison only. SpiritOS was not opened in AionUi.

The only AionUi workspace opened was the toy repository at `/home/source/aionui-toy-repo`. SpiritOS remained outside the AionUi workspace.

## Sources

- AionUi website: https://aionui.com/
- AionUi GitHub repository: https://github.com/iOfficeAI/AionUi
- Latest release: https://github.com/iOfficeAI/AionUi/releases/tag/v1.9.25

Observed source facts on 2026-05-17:

- Repository: `iOfficeAI/AionUi`
- License: Apache-2.0
- Latest release: `v1.9.25`
- Release published: 2026-05-05
- Available release assets include Linux `.deb`, macOS `.dmg`/`.zip`, and Windows `.exe` builds.
- The product page describes auto-detection for Claude Code, Codex, Gemini CLI, OpenCode, OpenClaw, Goose, Copilot, Kimi CLI, and more.
- The product page describes multi-agent coworking, scheduled tasks, remote control, skills, MCP configuration, and local/direct provider configuration.

## Local Toy Repo

Created and tested outside SpiritOS:

```text
/home/source/aionui-toy-repo
```

Initial state:

```text
45c460e init toy repo
```

This repository is safe to use for AionUi experiments because it has no SpiritOS code, secrets, or project authority.

Cleanup after evaluation:

```bash
rm -rf .aionrs
rm -f AionUi-1.9.25-linux-amd64.deb
```

## Environment Tested

- Host: source-server
- Access path: RustDesk/XFCE desktop session
- AionUi version: `1.9.25` Linux amd64 package
- Workspace opened in AionUi: `/home/source/aionui-toy-repo`
- SpiritOS workspace opened in AionUi: no
- Local provider endpoint: `http://127.0.0.1:11434/v1`
- Provider style: Ollama through an OpenAI-compatible local endpoint

## What Worked

- AionUi installed and launched successfully once a desktop session existed.
- AionUi opened `/home/source/aionui-toy-repo` correctly.
- Ollama connected through the OpenAI-compatible local endpoint.
- `qwen2.5-coder:7b` attempted an Edit tool call, which was the best observed provider behavior for the simple README edit.
- AionUi exposed useful UX concepts: workspace selection, model configuration, permission mode controls, visible tool steps, and task/sidebar surfaces.
- AionUi did not commit, push, or touch SpiritOS during the test.

## What Failed Or Felt Weak

- AionUi requires a GUI. On the headless source-server it needed RustDesk/XFCE before it could be evaluated.
- `llama3:latest` failed because it does not support tools.
- `llama3.1:8b` ran but was awkward and unreliable for the simple README edit.
- The simple file-edit workflow was not strong enough to justify making AionUi a SpiritOS dependency.
- AionUi created repo-local state under `.aionrs/`, which is acceptable in a toy repo but should not appear in SpiritOS without an explicit ignore/cleanup policy.

## Risks

- GUI dependency makes AionUi a poor foundation for Source Proxy or headless SpiritOS automation.
- Provider behavior depends heavily on model tool support.
- Repo-local `.aionrs/` state is extra operational clutter.
- AionUi's authority model is outside the SpiritOS trust boundary.
- Even if AionUi UX is useful, SpiritOS still needs Source Proxy to remain the system of record for task specs, allowed files, diff review, verification, approval, and audit.

## UI Patterns To Borrow

- workspace picker
- model selector
- permission mode dropdown
- visible tool steps
- current workspace label
- provider/model configuration panel
- sidebar for history, tasks, and teams
- clear tool result visibility

## Closeout Direction

AionUi/Cowork review is closed as UX/reference research. AionUi is not being integrated into SpiritOS right now.

SpiritOS may borrow useful UI/UX ideas later, but this evaluation does not authorize a new provider-layer implementation plan, Cowork Console build, or AionUi bridge.

SpiritOS proxy remains the trust boundary. Any future provider output must flow through:

- TaskSpec
- `allowed_files`
- diff preview
- verifier
- reviewer
- approval gate
- Cartographer logging

## Final Verdict

AionUi is useful as UX/reference research and as an optional external experiment. It should not be the foundation for SpiritOS.

Option B is selected: borrow UX ideas later, but do not integrate AionUi or extend this plan now.

Do not add AionUi as a core dependency. Do not open SpiritOS in AionUi unless a later, explicit experiment approves that boundary.

Next step: freeze the completed proxyCLI baseline and run a current-state production readiness assessment before writing any new production plan.

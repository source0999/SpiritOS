# Increment 2.1 - Research Comparison Report

## Scope

Compare useful coder-agent patterns without copying code. This report is conceptual research only.

## References and license notes

| Project/reference | Source | License note | Use concept | Copy code |
|---|---|---|---|---|
| Odysseus AI | https://github.com/pewdiepie-archdaemon/odysseus and https://odysseusai.dev/ | Public materials describe MIT/open-source project; verify exact repo license before any code reuse. | Local-first workspace, agent tools, model comparison, private/local model backends, research workspace. | No. |
| Aider | https://github.com/Aider-AI/aider | Repo includes `LICENSE.txt`; verify exact terms before reuse. | Git-aware edit loop, repo map, explicit changed-file workflow, terminal-first ergonomics. | No. |
| OpenHands | https://github.com/OpenHands/OpenHands and https://docs.openhands.dev/overview/contributing | Docs state MIT for OpenHands; enterprise folder has separate source-available/commercial constraints. | Browser/workspace agent loop, action history, sandbox/run loop, failure visibility. | No. |
| OpenCode | https://github.com/opencode-ai/opencode | GitHub page states MIT License. | Terminal agent UX, provider/model abstraction, session transcript, command/file tool boundaries. | No. |
| SWE-agent | https://github.com/SWE-agent/SWE-agent | Verify repo license before reuse; related mini-swe-agent is MIT. | Agent-computer interface, trajectory browser, issue-to-patch loop, environment isolation. | No. |
| mini-swe-agent | https://github.com/SWE-agent/mini-swe-agent | GitHub page states MIT license. | Small core loop, clear environment/model split, simple batch/CLI workflows. | No. |
| Cursor-like debugger workflows | Product/workflow pattern, no single copied source. | Proprietary product behavior; use only general concepts. | Inline diagnostics, file-aware debugging, terminal/test feedback, human-in-loop review. | No. |
| Repo Atlas / repo-map pattern | https://www.littlemight.com/repo-atlas/ | Article/concept reference; verify any repo/package license before reuse. | Persistent repo map to reduce repeated exploration and improve target selection. | No. |

## Useful patterns selected for SpiritOS

- Require provenance and trust labels for every trial row.
- Preserve trajectory/diagnostic history, but keep PASS dependent on model-authored diff proof.
- Keep repo/context retrieval small, explainable, and cited by path.
- Separate local model/provider routing from trial scoring.
- Prefer explicit environment/tool boundaries and failure reasons over hidden fallback.
- Use read-only memory/context as optional assistive input, disabled by default.

## Patterns rejected for now

- Copying agent loop code from any project.
- Automatic broad filesystem/vault scanning.
- Treating provider-call truth as model-authorship proof.
- Using deterministic scaffolds as trial success evidence.
- Broad hardening, grading, prompt expectations, or individual prompt dropdown work in this gate.

## Mapping to SpiritOS needs

- Trial harness: model-authored provenance, no scaffold PASS, durable diagnostics.
- Source Proxy: small optional context providers with read-only diagnostics.
- Future hardening: repo-map/memory context can inform prompts, but only after the trial trust contract is stable.

## Self-check

- Source links included: yes.
- License notes included: yes.
- Use concept separated from copy code: yes.
- No copied code from external projects: yes.

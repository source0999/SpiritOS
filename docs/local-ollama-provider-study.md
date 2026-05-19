# Local Ollama Provider Study

Status date: 2026-05-18
Status: proposal-only provider study

## Purpose

This study records whether local Ollama is useful for Source Proxy planning or review work without giving it file, tool, apply, commit, or push authority.

This document does not enable an adapter. It is evidence for later routing decisions only.

## Observed Local Capability

Local probe command:

```bash
curl -s http://localhost:11434/api/tags | jq '.models[]?.name' || true
```

Observed models on 2026-05-18:

- `qwen2.5-coder:7b`
- `llama3.1:8b`
- `llama3:latest`

The Ollama service is reachable on localhost for model inventory. No generation request, tool call, file write, apply, commit, or push was run for this study.

## Safe Classification

Local Ollama may be considered later for:

- planning notes
- reviewer summaries
- risk-label suggestions
- alternate wording for docs
- local-only brainstorms for sensitive work

Local Ollama must not be treated as:

- a default coding worker
- an approval authority
- an apply authority
- a commit authority
- a push authority
- a shell/tool execution provider
- a source-of-truth editor

## Current Registry Meaning

`local_ollama` may appear in the provider capability registry as a recommendation-only provider. That registry entry is not permission to call Ollama, write files, apply diffs, commit, or push.

Until a later adapter contract exists, local Ollama should remain planning/review only. If the registry reports `config_blocked`, interpret that as "not wired into Source Proxy execution," not "Ollama is absent from the machine."

## Limits And Risks

- Model quality is not verified by this study.
- Tool support is not assumed.
- JSON reliability is not assumed.
- Generated patches are not trusted.
- Sensitive data still requires deliberate prompt hygiene.
- Any future adapter must return evidence/proposals only and must preserve Source Proxy gates.

## Future Adapter Requirements

Before local Ollama can be wired into Source Proxy, the adapter must prove:

- readonly/proposal-only contract
- no filesystem writes
- no shell execution
- no apply, commit, or push authority
- bounded prompt and response sizes
- deterministic timeout behavior
- clear unavailable/config-blocked state
- tests proving unsafe output remains evidence only

## Recommendation

Keep local Ollama out of the coding path for now.

It is reasonable to study later as a local planning/review helper, especially for sensitive or offline work, but only after Source Proxy has a proposal-only adapter contract and tests.

## Manual Check

```bash
cd /home/source/SpiritOS
curl -s http://localhost:11434/api/tags | jq '.models[]?.name' || true
git diff -- docs/local-ollama-provider-study.md
git diff --check
```

Expected output:

- Ollama model names may print if the service is running.
- The doc diff shows this study only.
- `git diff --check` has no output.
- No source files are changed by the Ollama probe.

## Rollback

```bash
git restore docs/local-ollama-provider-study.md docs/source-proxy-production-hardening-plan.md
```

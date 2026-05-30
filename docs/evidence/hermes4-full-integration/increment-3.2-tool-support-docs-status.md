# Increment 3.2 - Tool support docs/status

Date: 2026-05-29T19:59:48-04:00

```text
src/lib/server/capabilities/format-capability-answer.ts:    return "Dev command tools are configured in the environment but are not attached for this model or session. Use a tool-capable model with SPIRIT_ENABLE_LOCAL_TOOLS and SPIRIT_OLLAMA_SUPPORTS_TOOLS passing the tool-call probe so run_dev_command can execute fixed allowlisted commands only.";
src/lib/spirit/tools/workspace-tools.ts:  const ollamaToolsTransport = isEnvTrue("SPIRIT_OLLAMA_SUPPORTS_TOOLS");
src/lib/spirit/tools/workspace-tools.ts:      "Read-only workspace tools attach only when SPIRIT_ENABLE_LOCAL_TOOLS and SPIRIT_OLLAMA_SUPPORTS_TOOLS are true (Ollama must accept tools for your model). Workspace paths are workspace-relative only; Windows folder listing requires SPIRIT_WINDOWS_FS_ENABLED and an allowlisted bridge path.",
src/lib/spirit/tools/tool-registry.ts:// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true. Schema acceptance only proves
src/lib/spirit/tools/tool-registry.ts:  return process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
src/lib/spirit/tools/__tests__/workspace-tools.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/system-state.ts:  const ollamaToolsTransport = process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "");
src/lib/spirit/__tests__/capability-honesty.eval.test.ts:  it("SPIRIT_ENABLE_LOCAL_TOOLS=true + SPIRIT_OLLAMA_SUPPORTS_TOOLS=true but localToolsAttached=false keeps workspace caps unavailable", () => {
src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
src/app/api/spirit/__tests__/route.test.ts:    expect(raw).not.toContain("SPIRIT_OLLAMA_SUPPORTS_TOOLS");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/__tests__/route.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
src/app/api/spirit/route.ts:    const ollamaToolsAllowed = process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
src/app/api/spirit/route.ts:        `[spirit-api] surface=${surface} profile=${modelProfileId ?? "unset"} workspace-tools modelId=${ollamaModelId} SPIRIT_ENABLE_LOCAL_TOOLS=${localToolsEnvEnabled} SPIRIT_OLLAMA_SUPPORTS_TOOLS=${ollamaToolsAllowed} toolsAttached=${readOnlyToolsAttached} reason=${reason}`,
src/app/api/spirit/route.ts:            "SPIRIT_ENABLE_LOCAL_TOOLS is on, but SPIRIT_OLLAMA_SUPPORTS_TOOLS is not set to \"true\", so this API will not attach OpenAI-style tool calls to Ollama.",
src/app/api/spirit/route.ts:            "Set SPIRIT_OLLAMA_SUPPORTS_TOOLS=true only after you use an Ollama model that accepts tools; leaving it false avoids HTTP 400 errors from models that reject tool payloads.",
docs/evidence/hermes4-full-integration/phase-2-closeout.md:- Increment 2.1: env examples and README now document Hermes 4 as the local default, exact Hermes 4 model IDs, Hermes 3 fallback role, Qwen selectable/non-default role, and 8TB storage verification requirements.
docs/evidence/hermes4-full-integration/phase-2-closeout.md:- Increment 2.2: Source Proxy local routing defaults to Hermes 4, avoids unconfigured Qwen fallback, prefers installed Hermes models when probing, and exposes requested/resolved/probe/storage truth.
docs/evidence/hermes4-full-integration/increment-2.1-local-default-patch.md:+# Hermes 4 must be pulled and visible as `hermes4:latest`; base model:
docs/evidence/hermes4-full-integration/increment-2.1-local-default-patch.md:+Hermes 4 is the default local intelligence model for SpiritOS chat and Source Proxy local routing. The expected local IDs are `hermes4:latest` and `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`; keep `hermes3:8b-abliterated` available as the fast `/oracle`/voice-friendly fallback and keep `qwen2.5-coder:7b` selectable for explicit coding experiments. If Ollama models are intended to live on the 8TB drive, verify `OLLAMA_MODELS` or the Ollama service/home symlink resolves to `/mnt/spirit-8tb/ollama-models` before calling storage configured.
docs/evidence/hermes4-full-integration/increment-2.1-local-default-patch.md:+# Default local intelligence is Hermes 4. Verify `hermes4:latest` and the base
docs/evidence/hermes4-full-integration/increment-2.1-local-default-patch.md:+# Prefer Hermes 4 for local proxy/coding; keep Qwen selectable but non-default.
docs/evidence/hermes4-full-integration/increment-2.1-local-default-patch.md:GO. Hermes 4 remains the documented local default; Hermes 3 fallback and Qwen selectable/non-default roles are preserved. Patch is limited to env/docs plus Source Proxy status truth fields needed by the gate.
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:# Increment 1.2 - Hermes 4 runtime smoke
docs/evidence/hermes4-full-integration/increment-3.1-hermes4-tool-compat-probe.md:# Increment 3.1 - Hermes 4 tool compatibility probe
docs/evidence/hermes4-full-integration/increment-3.1-hermes4-tool-compat-probe.md:=== tool schema probe shape, non-mutating ===
docs/evidence/hermes4-full-integration/increment-3.1-hermes4-tool-compat-probe.md:- Hermes 4 accepted the OpenAI-compatible `tools` schema with HTTP 200.
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/server/capabilities/format-capability-answer.ts:    return "Dev command tools are configured in the environment but are not attached for this model or session. Use a tool-capable model with SPIRIT_ENABLE_LOCAL_TOOLS and SPIRIT_OLLAMA_SUPPORTS_TOOLS passing the tool-call probe so run_dev_command can execute fixed allowlisted commands only.";
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/workspace-tools.ts:  const ollamaToolsTransport = isEnvTrue("SPIRIT_OLLAMA_SUPPORTS_TOOLS");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/workspace-tools.ts:      "Read-only workspace tools attach only when SPIRIT_ENABLE_LOCAL_TOOLS and SPIRIT_OLLAMA_SUPPORTS_TOOLS are true (Ollama must accept tools for your model). Workspace paths are workspace-relative only; Windows folder listing requires SPIRIT_WINDOWS_FS_ENABLED and an allowlisted bridge path.",
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/tool-registry.ts:// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true. Schema acceptance only proves
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/tool-registry.ts:  return process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/workspace-tools.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/system-state.ts:  const ollamaToolsTransport = process.env.SPIRIT_OLLAMA_SUPPORTS_TOOLS === "true";
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/capability-honesty.eval.test.ts:  it("SPIRIT_ENABLE_LOCAL_TOOLS=true + SPIRIT_OLLAMA_SUPPORTS_TOOLS=true but localToolsAttached=false keeps workspace caps unavailable", () => {
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/capability-honesty.eval.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "false");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md:src/lib/spirit/__tests__/system-state.test.ts:    vi.stubEnv("SPIRIT_OLLAMA_SUPPORTS_TOOLS", "true");
docs/evidence/hermes4-full-integration/increment-2.2-source-proxy-local-routing.md:GO. Source Proxy local routing defaults to Hermes 4, prefers installed Hermes models over Qwen when unconfigured, and now exposes requested local default, resolved model, selected_via, probe_ok, and 8TB storage proof fields.
.env.example:# Hermes 4 must be pulled and visible as `hermes4:latest`; base model:
README.md:Hermes 4 is the default local intelligence model for SpiritOS chat and Source Proxy local routing. The expected local IDs are `hermes4:latest` and `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`; keep `hermes3:8b-abliterated` available as the fast `/oracle`/voice-friendly fallback and keep `qwen2.5-coder:7b` selectable for explicit coding experiments. If Ollama models are intended to live on the 8TB drive, verify `OLLAMA_MODELS` or the Ollama service/home symlink resolves to `/mnt/spirit-8tb/ollama-models` before calling storage configured.
README.md:# Hermes 4 accepts OpenAI-compatible tool schemas, but the 2026-05-29 probe
README.md:SPIRIT_OLLAMA_SUPPORTS_TOOLS=false
```

```diff
diff --git a/README.md b/README.md
index 7d7a823..373e4ad 100755
--- a/README.md
+++ b/README.md
@@ -50,6 +50,8 @@ curl -k -sS https://localhost:3000/api/spirit/health
 curl -k -sS https://localhost:8787/healthcheck
 ```
 
+Hermes 4 is the default local intelligence model for SpiritOS chat and Source Proxy local routing. The expected local IDs are `hermes4:latest` and `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`; keep `hermes3:8b-abliterated` available as the fast `/oracle`/voice-friendly fallback and keep `qwen2.5-coder:7b` selectable for explicit coding experiments. If Ollama models are intended to live on the 8TB drive, verify `OLLAMA_MODELS` or the Ollama service/home symlink resolves to `/mnt/spirit-8tb/ollama-models` before calling storage configured.
+
 ### Local HTTPS LAN Dev Servers
 
 SpiritOS uses two local HTTPS LAN dev servers during normal development.
@@ -333,8 +335,11 @@ node .\agent.js
 Matching Dell/Next `.env.local` settings:
 
 ```bash
-SPIRIT_ENABLE_LOCAL_TOOLS=true
-SPIRIT_OLLAMA_SUPPORTS_TOOLS=true
+SPIRIT_ENABLE_LOCAL_TOOLS=false
+# Hermes 4 accepts OpenAI-compatible tool schemas, but the 2026-05-29 probe
+# emitted a noop tool call even when instructed not to. Keep this false unless
+# a fresh operator probe proves the target model/tool policy is safe.
+SPIRIT_OLLAMA_SUPPORTS_TOOLS=false
 SPIRIT_WINDOWS_FS_ENABLED=true
 SPIRIT_WINDOWS_FS_BASE_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000
 SPIRIT_WINDOWS_FS_TOKEN=3399
diff --git a/src/lib/server/ollama.ts b/src/lib/server/ollama.ts
index da76b11..3396038 100755
--- a/src/lib/server/ollama.ts
+++ b/src/lib/server/ollama.ts
@@ -69,7 +69,8 @@ export async function probeOllamaOpenAICompat(): Promise<OllamaProbeResult> {
 
 /**
  * POST /v1/chat/completions with a minimal tools payload to see if this model
- * accepts OpenAI-style tools. Hermes4 and similar return 400 "does not support tools".
+ * accepts OpenAI-style tools. This proves schema transport only; it does not
+ * prove that a local model should receive file-edit or command tools by default.
  * Cached per process in tool-registry; callers should not spam this.
  */
 export async function probeOllamaChatCompletionsAcceptsToolSchema(modelId: string): Promise<boolean> {
diff --git a/src/lib/spirit/tools/tool-registry.ts b/src/lib/spirit/tools/tool-registry.ts
index e470bc6..e6173fc 100755
--- a/src/lib/spirit/tools/tool-registry.ts
+++ b/src/lib/spirit/tools/tool-registry.ts
@@ -1,6 +1,7 @@
 // ── tool-registry - AI SDK read-only tools gated by SPIRIT_ENABLE_LOCAL_TOOLS ──
-// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true: Hermes4 and many registry pulls
-// > reject requests with tools ("does not support tools"); opt in after switching models.
+// > Also requires SPIRIT_OLLAMA_SUPPORTS_TOOLS=true. Schema acceptance only proves
+// > transport compatibility; keep local tools off until an operator probe approves
+// > the exact model/tool policy.
 
 import { tool } from "ai";
 import { z } from "zod";
```

```text
```

## Result

GO. Hermes 4 schema transport compatibility is documented, but local tools remain disabled by default; no file edit/dev command tools were enabled.

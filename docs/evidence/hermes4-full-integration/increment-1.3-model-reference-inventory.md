# Increment 1.3 - Model reference inventory

Date: 2026-05-29T19:54:06-04:00

```text
.env.example:# Model tag on the Ollama host (default in app: hermes4).
.env.example:OLLAMA_MODEL=hermes4
.env.example:# Optional: faster model for `/oracle` only (defaults to OLLAMA_MODEL when unset).
.env.example:# ORACLE_OLLAMA_MODEL=hermes3:8b
.env.local.example:# Ollama model tag for `/api/spirit` (default in code: hermes4). Pull on the Ollama host: `ollama pull hermes4`.
.env.local.example:OLLAMA_MODEL=hermes4
.env.local.example:# Optional: `/oracle` uses ORACLE_OLLAMA_MODEL when set; otherwise same as OLLAMA_MODEL.
.env.local.example:# ORACLE_OLLAMA_MODEL=hermes3:8b
backend/.env.example:OLLAMA_MODEL=hermes4
README.md:ollama pull hermes4
README.md:**Brain vs TTS (do not conflate them):** `/api/spirit` uses `OLLAMA_MODEL` for `/chat` text generation. `/oracle` can use `ORACLE_OLLAMA_MODEL` when set. Voice is synthesized via same-origin **`/api/tts`** (`TTS_PROVIDER=piper` or `elevenlabs`); the browser never sees `ELEVENLABS_API_KEY`. Optional `ELEVENLABS_VOICE_SPEED` (default 1.12, clamped 0.7–1.2) sets ElevenLabs cadence; Voice settings can send a per-request `speed` override. **`GET /api/tts/voices`** feeds the Voice picker. **`ELEVENLABS_VOICE_ALLOWLIST`** supports **`Clarice:voice_id`** (recommended, no catalog read) or comma-separated **names only** (needs catalog + `voices_read`; if the catalog fails, switch to `Name:voice_id`). When any allowlist is set, the API returns **only** those voices - never the full catalog. Defaults prefer **`ELEVENLABS_DEFAULT_VOICE_ID`**, then **Clarice** by name, then **`ELEVENLABS_VOICE_ID`**. Response **`X-Spirit-TTS-Voice-Name-Encoded`** keeps display names ASCII-safe for Tailscale.
src/components/chat/SpiritChat.tsx:  /** `/oracle` passes `"oracle"` so /api/spirit uses ORACLE_OLLAMA_MODEL lane. */
src/components/chat/SpiritChat.tsx:                title="Abliterated Mode routes this chat to hermes3:8b-abliterated"
src/components/coding/__tests__/coding-cockpit-shell.test.tsx:            model: "ollama_chat/hermes4:latest",
src/components/coding/__tests__/coding-cockpit-shell.test.tsx:              modelId: "ollama_chat/hermes4:latest",
src/components/coding/__tests__/coding-cockpit-shell.test.tsx:              modelLabel: "hermes4:latest",
src/components/coding/__tests__/coding-cockpit-shell.test.tsx:    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("model: hermes4:latest"));
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:  chatModel: "hermes4-test",
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:    activeResolvedModelId: "hermes4-test",
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:    expect(text).toContain("hermes4-test");
src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
src/lib/server/ollama.ts:/** Primary `/chat` lane model tag (OLLAMA_MODEL). */
src/lib/server/model-routing.ts:// > Hermes-class chat stays on OLLAMA_MODEL; Oracle lane can opt into a smaller model.
src/lib/server/model-routing.ts:export const SPIRIT_ABLITERATED_CHAT_MODEL_ID = "hermes3:8b-abliterated";
src/lib/server/model-routing.ts:  return process.env.OLLAMA_MODEL?.trim() || "hermes4";
src/lib/server/model-routing.ts:/** Oracle UI; falls back to chat model when ORACLE_OLLAMA_MODEL unset. */
src/lib/server/model-routing.ts:  const o = process.env.ORACLE_OLLAMA_MODEL?.trim();
src/lib/server/__tests__/ollama-tool-probe.test.ts:          error: { message: "registry.ollama.ai/library/hermes4:latest does not support tools" },
src/lib/server/__tests__/ollama-tool-probe.test.ts:    const ok = await probeOllamaChatCompletionsAcceptsToolSchema("hermes4");
src/lib/server/__tests__/model-routing.test.ts:    delete process.env.OLLAMA_MODEL;
src/lib/server/__tests__/model-routing.test.ts:    delete process.env.ORACLE_OLLAMA_MODEL;
src/lib/server/__tests__/model-routing.test.ts:  it("getSpiritChatModelId reads OLLAMA_MODEL", () => {
src/lib/server/__tests__/model-routing.test.ts:    process.env.OLLAMA_MODEL = "hermes4:latest";
src/lib/server/__tests__/model-routing.test.ts:    expect(getSpiritChatModelId()).toBe("hermes4:latest");
src/lib/server/__tests__/model-routing.test.ts:  it("getOracleModelId falls back to chat model when ORACLE_OLLAMA_MODEL unset", () => {
src/lib/server/__tests__/model-routing.test.ts:    process.env.OLLAMA_MODEL = "chat-model";
src/lib/server/__tests__/model-routing.test.ts:    delete process.env.ORACLE_OLLAMA_MODEL;
src/lib/server/__tests__/model-routing.test.ts:  it("getOracleModelId uses ORACLE_OLLAMA_MODEL when set", () => {
src/lib/server/__tests__/model-routing.test.ts:    process.env.OLLAMA_MODEL = "chat-model";
src/lib/server/__tests__/model-routing.test.ts:    process.env.ORACLE_OLLAMA_MODEL = "oracle-fast";
src/lib/server/__tests__/model-routing.test.ts:    process.env.OLLAMA_MODEL = "a";
src/lib/server/__tests__/model-routing.test.ts:    process.env.ORACLE_OLLAMA_MODEL = "b";
src/lib/server/__tests__/model-routing.test.ts:    process.env.OLLAMA_MODEL = "a";
src/lib/server/__tests__/model-routing.test.ts:    process.env.ORACLE_OLLAMA_MODEL = "b";
src/lib/server/__tests__/model-routing.test.ts:      "hermes3:8b-abliterated",
src/lib/coding/model-provider-status.ts:  const withoutProvider = cleaned.replace(/^ollama_chat\//, "");
src/lib/coding/__tests__/model-provider-status.test.ts:        litellm_model: "ollama_chat/hermes4:latest",
src/lib/coding/__tests__/model-provider-status.test.ts:    expect(truth.modelLabel).toBe("hermes4:latest");
src/lib/coding/__tests__/model-provider-status.test.ts:      model: "ollama_chat/qwen2.5-coder:7b",
src/lib/coding/__tests__/model-provider-status.test.ts:    expect(truth.modelLabel).toBe("qwen2.5-coder:7b");
src/lib/spirit/spirit-client-runtime-hint.ts:// ── Client-visible Ollama label (optional NEXT_PUBLIC_OLLAMA_MODEL) ───────────────
src/lib/spirit/spirit-client-runtime-hint.ts:  const v = process.env.NEXT_PUBLIC_OLLAMA_MODEL?.trim();
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    await expect(resolveSpiritToolsForOllamaModel("hermes4")).resolves.toBeUndefined();
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:    await expect(resolveSpiritToolsForOllamaModel("hermes4")).resolves.toBeUndefined();
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:      resolveSpiritToolsForOllamaModel("hermes4", { swarmAgentRole: "coder" }),
src/lib/spirit/tools/__tests__/tool-registry-resolve.test.ts:      resolveSpiritToolsForOllamaModel("hermes4", { swarmAgentRole: "debugger" }),
src/lib/spirit/spirit-chat-request-body.ts:  /** Optional: `/oracle` passes `"oracle"` for ORACLE_OLLAMA_MODEL lane. */
src/lib/spirit/__tests__/ollama-tool-unsupported-error.test.ts:      message: "registry.ollama.ai/library/hermes4:latest does not support tools",
src/lib/spirit/__tests__/ollama-tool-unsupported-error.test.ts:        '{"error":{"message":"registry.ollama.ai/library/hermes4:latest does not support tools"}}',
src/lib/spirit/__tests__/spirit-route-decision.test.ts:    modelHint: "hermes4:latest",
src/app/oracle/page.tsx:// > runtimeSurface=oracle → /api/spirit + ORACLE_OLLAMA_MODEL when env set.
src/app/v1/decisions/prompt-packet/route.ts:  const modelLabel = model ? model.replace(/^ollama_chat\//, "") : "Unknown local model";
src/app/v1/decisions/prompt-packet/route.ts:    configuredOllamaModel: stringFromUnknown(route.configured_ollama_model) || modelLabel,
source_proxy/self_status.py:                    "configured_ollama_model": local_status.get("ollama_model"),
source_proxy/tests/test_ollama_route.py:                "SOURCE_PROXY_OLLAMA_MODEL": "",
source_proxy/tests/test_ollama_route.py:                "OLLAMA_MODEL": "",
source_proxy/tests/test_ollama_route.py:                "SOURCE_PROXY_OLLAMA_MODEL": "",
source_proxy/tests/test_ollama_route.py:                "OLLAMA_MODEL": "",
source_proxy/tests/test_ollama_route.py:            self.assertEqual(resolve_ollama_model_name(), "hermes4")
source_proxy/tests/test_ollama_route.py:                "SOURCE_PROXY_OLLAMA_MODEL": "",
source_proxy/tests/test_ollama_route.py:                "OLLAMA_MODEL": "",
source_proxy/tests/test_ollama_route.py:            return_value=(True, ("qwen2.5-coder:7b", "hermes3:8b-abliterated")),
source_proxy/tests/test_ollama_route.py:        self.assertEqual(route.model, "hermes3:8b-abliterated")
source_proxy/tests/test_ollama_route.py:    def test_local_route_maps_to_ollama_chat_model(self) -> None:
source_proxy/tests/test_ollama_route.py:                "SOURCE_PROXY_OLLAMA_MODEL": "qwen2.5-coder:7b",
source_proxy/tests/test_ollama_route.py:        self.assertEqual(local.model, "ollama_chat/qwen2.5-coder:7b")
source_proxy/tests/test_self_status.py:                    "model": "ollama_chat/hermes4",
source_proxy/tests/test_self_status.py:        self.assertEqual(manifest["model_routes"][0]["model"], "ollama_chat/hermes4")
source_proxy/api/decision.py:    model_label = model.removeprefix("ollama_chat/") if model else "Unknown local model"
source_proxy/routing/litellm_router.py:            model=f"ollama_chat/{ollama_model}",
source_proxy/routing/ollama_route.py:_DEFAULT_OLLAMA_MODEL = "hermes4"
source_proxy/routing/ollama_route.py:        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:        or os.getenv("OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:    return _DEFAULT_OLLAMA_MODEL
source_proxy/routing/ollama_route.py:        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:        or os.getenv("OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:        litellm_model=f"ollama_chat/{model}",
source_proxy/routing/ollama_route.py:            0 if "hermes4" in model.lower() else 1,
source_proxy/routing/ollama_route.py:        "ollama_chatexception",
source_proxy/tasks/long_running.py:        "modelLabel": model.removeprefix("ollama_chat/") if model else "Unknown local model",
docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md:- The route comment records `runtimeSurface=oracle -> /api/spirit + ORACLE_OLLAMA_MODEL when env set`.
docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md:| Oracle | `/oracle` | Oracle lane | Roadmap driver | `/api/spirit`, `ORACLE_OLLAMA_MODEL`, `/api/tts`, optional STT, local activity state | Eligible for future non-Cart work only with explicit provider, voice, and local-storage proof needs. |
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:            "name": "hermes4:latest",
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:            "model": "hermes4:latest",
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:            "name": "hermes3:8b-abliterated",
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:            "model": "hermes3:8b-abliterated",
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:            "name": "qwen2.5-coder:7b",
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:            "model": "qwen2.5-coder:7b",
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md:- `ollama run hermes4 "Reply exactly: HERMES4_ALIAS_OK"` returned `HERMES4_ALIAS_OK`.
docs/evidence/hermes4-full-integration/increment-1.1-ollama-8tb-model-path.md:hermes4:latest                                           3e79497c9643    9.0 GB    5 minutes ago    
docs/evidence/hermes4-full-integration/increment-1.1-ollama-8tb-model-path.md:hermes3:8b-abliterated                                   621eb9c2e65e    4.7 GB    4 days ago       
docs/evidence/hermes4-full-integration/increment-1.1-ollama-8tb-model-path.md:qwen2.5-coder:7b                                         dae161e27b0e    4.7 GB    11 days ago      
docs/evidence/hermes4-full-integration/increment-1.1-ollama-8tb-model-path.md:- `hermes4:latest` is visible in `ollama list`.
docs/evidence/hermes4-full-integration/increment-1.1-ollama-8tb-model-path.md:- Direct process environment inspection was blocked by `/proc/$pid/environ` permissions, so `OLLAMA_MODELS` was not directly proven from the running process. The active symlink path proves the default Ollama model home resolves onto the 8TB drive.
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.example:# Model tag on the Ollama host (default in app: hermes4).
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.example:OLLAMA_MODEL=hermes4
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.example:# Optional: faster model for `/oracle` only (defaults to OLLAMA_MODEL when unset).
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.example:# ORACLE_OLLAMA_MODEL=hermes3:8b
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.local.example:# Ollama model tag for `/api/spirit` (default in code: hermes4). Pull on the Ollama host: `ollama pull hermes4`.
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.local.example:OLLAMA_MODEL=hermes4
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.local.example:# Optional: `/oracle` uses ORACLE_OLLAMA_MODEL when set; otherwise same as OLLAMA_MODEL.
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:.env.local.example:# ORACLE_OLLAMA_MODEL=hermes3:8b
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:backend/.env.example:OLLAMA_MODEL=hermes4
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:README.md:ollama pull hermes4
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:README.md:**Brain vs TTS (do not conflate them):** `/api/spirit` uses `OLLAMA_MODEL` for `/chat` text generation. `/oracle` can use `ORACLE_OLLAMA_MODEL` when set. Voice is synthesized via same-origin **`/api/tts`** (`TTS_PROVIDER=piper` or `elevenlabs`); the browser never sees `ELEVENLABS_API_KEY`. Optional `ELEVENLABS_VOICE_SPEED` (default 1.12, clamped 0.7–1.2) sets ElevenLabs cadence; Voice settings can send a per-request `speed` override. **`GET /api/tts/voices`** feeds the Voice picker. **`ELEVENLABS_VOICE_ALLOWLIST`** supports **`Clarice:voice_id`** (recommended, no catalog read) or comma-separated **names only** (needs catalog + `voices_read`; if the catalog fails, switch to `Name:voice_id`). When any allowlist is set, the API returns **only** those voices - never the full catalog. Defaults prefer **`ELEVENLABS_DEFAULT_VOICE_ID`**, then **Clarice** by name, then **`ELEVENLABS_VOICE_ID`**. Response **`X-Spirit-TTS-Voice-Name-Encoded`** keeps display names ASCII-safe for Tailscale.
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/components/chat/SpiritChat.tsx:  /** `/oracle` passes `"oracle"` so /api/spirit uses ORACLE_OLLAMA_MODEL lane. */
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/components/chat/SpiritChat.tsx:                title="Abliterated Mode routes this chat to hermes3:8b-abliterated"
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/components/coding/__tests__/coding-cockpit-shell.test.tsx:            model: "ollama_chat/hermes4:latest",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/components/coding/__tests__/coding-cockpit-shell.test.tsx:              modelId: "ollama_chat/hermes4:latest",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/components/coding/__tests__/coding-cockpit-shell.test.tsx:              modelLabel: "hermes4:latest",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/components/coding/__tests__/coding-cockpit-shell.test.tsx:    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("model: hermes4:latest"));
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:  chatModel: "hermes4-test",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:    activeResolvedModelId: "hermes4-test",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:    expect(text).toContain("hermes4-test");
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/capabilities/__tests__/format-capability-answer.test.ts:      activeResolvedModelId: "hermes4-test",
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/ollama.ts:/** Primary `/chat` lane model tag (OLLAMA_MODEL). */
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/model-routing.ts:// > Hermes-class chat stays on OLLAMA_MODEL; Oracle lane can opt into a smaller model.
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/model-routing.ts:export const SPIRIT_ABLITERATED_CHAT_MODEL_ID = "hermes3:8b-abliterated";
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/model-routing.ts:  return process.env.OLLAMA_MODEL?.trim() || "hermes4";
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/model-routing.ts:/** Oracle UI; falls back to chat model when ORACLE_OLLAMA_MODEL unset. */
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/model-routing.ts:  const o = process.env.ORACLE_OLLAMA_MODEL?.trim();
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/ollama-tool-probe.test.ts:          error: { message: "registry.ollama.ai/library/hermes4:latest does not support tools" },
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/ollama-tool-probe.test.ts:    const ok = await probeOllamaChatCompletionsAcceptsToolSchema("hermes4");
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/model-routing.test.ts:    delete process.env.OLLAMA_MODEL;
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/model-routing.test.ts:    delete process.env.ORACLE_OLLAMA_MODEL;
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/model-routing.test.ts:  it("getSpiritChatModelId reads OLLAMA_MODEL", () => {
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/model-routing.test.ts:    process.env.OLLAMA_MODEL = "hermes4:latest";
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/model-routing.test.ts:    expect(getSpiritChatModelId()).toBe("hermes4:latest");
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md:src/lib/server/__tests__/model-routing.test.ts:  it("getOracleModelId falls back to chat model when ORACLE_O
```

## Result

GO.

- Inventory covered `.env.example`, `.env.local.example`, `backend/.env.example`, `README.md`, `src`, `source_proxy`, `docs`, and `scripts`.
- Real `.env.local` was not included or printed.
- Current defaults already show `OLLAMA_MODEL=hermes4` in the example env files and `source_proxy/routing/ollama_route.py` has `_DEFAULT_OLLAMA_MODEL = "hermes4"`.
- Hermes 3 remains referenced for abliterated/oracle fallback behavior.
- Qwen remains referenced in tests/status as a selectable model.
- Note: because the evidence file itself lives under `docs`, the raw grep began matching the evidence output while it was being written. The useful inventory is still present above, and `git diff --check` passed after the increment.

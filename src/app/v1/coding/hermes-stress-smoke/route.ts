import { sourceProxyFetch } from "@/lib/source-proxy-origin";

const stressPrompt = "Reply exactly HERMES4_STRESS_OK";

export async function POST() {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true", pass: false },
      { status: 409 },
    );
  }

  const startedAt = Date.now();
  try {
    const response = await sourceProxyFetch("/v1/chat/completions", {
      body: JSON.stringify({
        model: "local",
        messages: [{ role: "user", content: stressPrompt }],
        temperature: 0,
      }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    const payload = await response.json() as Record<string, unknown>;
    const responseTimeMs = Date.now() - startedAt;
    const choice = Array.isArray(payload.choices) ? payload.choices[0] : null;
    const message =
      choice && typeof choice === "object" && choice !== null
        ? (choice as Record<string, unknown>).message
        : null;
    const content =
      message && typeof message === "object" && message !== null
        ? String((message as Record<string, unknown>).content ?? "").trim()
        : "";
    const routedModel = typeof payload.model === "string" ? payload.model : null;
    const pass = response.ok && content.includes("HERMES4_STRESS_OK");

    return Response.json({
      pass,
      provider: "local",
      response_content: content,
      response_time_ms: responseTimeMs,
      routed_model: routedModel,
      status: response.status,
      zero_cost_local_route: routedModel ? /ollama|hermes|local/i.test(routedModel) : false,
    });
  } catch (error) {
    return Response.json(
      {
        pass: false,
        detail: error instanceof Error ? error.message : "Unknown connection error.",
        response_time_ms: Date.now() - startedAt,
      },
      { status: 502 },
    );
  }
}

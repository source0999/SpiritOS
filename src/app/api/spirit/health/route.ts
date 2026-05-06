// ── GET /api/spirit/health - Ollama OpenAI-compat reachability (no secrets in body) ─
import {
  getOllamaOpenAIBaseURL,
  getSpiritModelId,
  probeOllamaOpenAICompat,
} from "@/lib/server/ollama";
import { getSpiritDiagnostics } from "@/lib/server/spirit-diagnostics";

export async function GET() {
  const model = getSpiritModelId();
  const baseURL = getOllamaOpenAIBaseURL();
  const diagnostics = getSpiritDiagnostics();
  const result = await probeOllamaOpenAICompat();

  if (result.ok) {
    return Response.json({
      ok: true,
      service: "ollama",
      model,
      baseURL,
      status: "online",
      diagnostics,
    });
  }

  return Response.json(
    {
      ok: false,
      service: "ollama",
      model,
      baseURL,
      status: "offline",
      error: result.error,
      diagnostics,
    },
    { status: 503 },
  );
}

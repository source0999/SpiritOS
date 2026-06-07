import {
  buildAgentLabBaselineSnapshot,
} from "@/lib/coding/agent-lab-baseline-server";

export async function GET(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json({ error: "SPIRIT_CODING_USE_PROXY is not true" }, { status: 409 });
  }

  const url = new URL(request.url);
  const unrevertedRaw = url.searchParams.get("unreverted_targets") ?? "";
  const unrevertedReceiptTargets = unrevertedRaw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  try {
    const snapshot = await buildAgentLabBaselineSnapshot(unrevertedReceiptTargets);
    return Response.json({
      ...snapshot,
      visible_label: snapshot.baseline_clean_for_fresh_suite ? "BASELINE CLEAN" : "BASELINE DIRTY",
    });
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : "agent-lab baseline failed" },
      { status: 502 },
    );
  }
}

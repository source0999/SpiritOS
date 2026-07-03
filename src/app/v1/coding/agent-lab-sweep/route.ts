import { sweepAgentLabBaselineServer } from "@/lib/coding/agent-lab-baseline-server";

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

export async function POST(request: Request) {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json({ error: "SPIRIT_CODING_USE_PROXY is not true" }, { status: 409 });
  }

  let body: unknown = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  const unrevertedRaw = asRecord(body).unreverted_targets;
  const unrevertedReceiptTargets = Array.isArray(unrevertedRaw)
    ? unrevertedRaw.filter((item): item is string => typeof item === "string")
    : typeof unrevertedRaw === "string"
      ? unrevertedRaw.split(",").map((item) => item.trim()).filter(Boolean)
      : [];

  try {
    const result = await sweepAgentLabBaselineServer(unrevertedReceiptTargets);
    const clean = result.snapshot.baseline_clean_for_fresh_suite;
    return Response.json({
      clean,
      failures: result.failures,
      message: clean
        ? `Removed ${result.removed} trial leftover file(s). Workspace is clean for a fresh Coder benchmark.`
        : result.failures.length > 0
          ? `Removed ${result.removed}/${result.targets.length} trial file(s). Still dirty: ${result.failures.slice(0, 3).join("; ")}`
          : `Trial baseline still has ${result.snapshot.baseline_dirty_agent_lab_files.length} leftover file(s).`,
      removed: result.removed,
      skipped: result.skipped,
      snapshot: {
        ...result.snapshot,
        visible_label: clean ? "BASELINE CLEAN" : "BASELINE DIRTY",
      },
      targets: result.targets,
    });
  } catch (error) {
    return Response.json(
      {
        error: error instanceof Error ? error.message : "agent-lab sweep failed",
      },
      { status: 502 },
    );
  }
}

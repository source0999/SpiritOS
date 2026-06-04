import { NextResponse } from "next/server";

import { createDiagnosticsSnapshot } from "@/lib/converter/authorizedMediaImportService";
import { getConverterQueue } from "@/lib/converter/converterServerQueue";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ jobId: string }> },
) {
  const { jobId } = await params;
  const job = getConverterQueue().snapshot().jobs.find((candidate) => candidate.id === jobId);

  if (!job) {
    return NextResponse.json({ error: "Converter job not found." }, { status: 404 });
  }

  return new Response(createDiagnosticsSnapshot(job), {
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

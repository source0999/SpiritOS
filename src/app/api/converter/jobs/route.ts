import { NextResponse } from "next/server";

import { expandLocalFolder } from "@/lib/converter/authorizedMediaImportService";
import { getConverterQueue } from "@/lib/converter/converterServerQueue";
import type { ConverterBatchInput } from "@/lib/converter/converterTypes";

export async function GET() {
  return NextResponse.json(getConverterQueue().snapshot());
}

export async function POST(request: Request) {
  const body = (await request.json()) as ConverterBatchInput;
  const expandedBody = await expandFolderInput(body);
  const queue = getConverterQueue();
  const jobs = queue.enqueueBatch(expandedBody);
  void queue.start();

  return NextResponse.json({
    accepted: jobs.length,
    snapshot: queue.snapshot(),
  });
}

async function expandFolderInput(body: ConverterBatchInput): Promise<ConverterBatchInput> {
  const folderPath = body.folderPath?.trim();
  if (!folderPath) {
    return body;
  }

  try {
    const folderItems = await expandLocalFolder(folderPath);
    return {
      ...body,
      folderPath: undefined,
      pastedItems: [body.pastedItems, ...folderItems].filter(Boolean).join("\n"),
    };
  } catch (error) {
    return {
      ...body,
      folderPath: undefined,
      pastedItems: [body.pastedItems, `folder-error:${String(error)}`].filter(Boolean).join("\n"),
    };
  }
}

import { NextResponse } from "next/server";

import { getConverterQueue } from "@/lib/converter/converterServerQueue";

type ConverterControlAction = "pause" | "resume" | "cancel" | "clear";

export async function POST(request: Request) {
  const body = (await request.json()) as { action?: ConverterControlAction };
  const queue = getConverterQueue();

  if (body.action === "pause") {
    return NextResponse.json(queue.pause());
  }

  if (body.action === "resume") {
    queue.resume();
    return NextResponse.json(queue.snapshot());
  }

  if (body.action === "cancel") {
    return NextResponse.json(queue.cancel());
  }

  if (body.action === "clear") {
    return NextResponse.json(queue.clear());
  }

  return NextResponse.json({ error: "Unknown converter control action." }, { status: 400 });
}

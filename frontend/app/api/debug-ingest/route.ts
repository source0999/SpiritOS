import fs from "fs";
import path from "path";
import { NextResponse } from "next/server";

/** Writes one NDJSON line for debug sessions (works when browser cannot reach :7920). */
const LOG_PATH = path.join(process.cwd(), "..", ".cursor", "debug-7d6688.log");

export async function POST(req: Request) {
  try {
    const payload = await req.json();
    const line = JSON.stringify({ ...payload, serverReceivedAt: Date.now() }) + "\n";
    const dir = path.dirname(LOG_PATH);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.appendFileSync(LOG_PATH, line, "utf8");
    return NextResponse.json({ ok: true });
  } catch (e) {
    return NextResponse.json({ ok: false, error: String(e) }, { status: 500 });
  }
}

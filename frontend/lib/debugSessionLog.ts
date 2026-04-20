import fs from "fs";
import path from "path";

/** NDJSON debug log — path relative to repo so SSH / any cwd layout works when dev runs from `frontend/`. */
const LOG_PATH = path.join(process.cwd(), "..", ".cursor", "debug-7d6688.log");

export function logDebugSession(payload: {
  hypothesisId: string;
  location: string;
  message: string;
  data?: Record<string, unknown>;
}) {
  try {
    const dir = path.dirname(LOG_PATH);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const line =
      JSON.stringify({
        sessionId: "7d6688",
        timestamp: Date.now(),
        ...payload,
      }) + "\n";
    fs.appendFileSync(LOG_PATH, line, "utf8");
  } catch {
    /* ignore */
  }
}

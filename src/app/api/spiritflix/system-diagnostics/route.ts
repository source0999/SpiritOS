import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const execFileAsync = promisify(execFile);

function classifyProcess(command: string): "media_processing" | "jellyfin_transcode" | "other" {
  if (command.includes("/mnt/spirit-8tb/media-processing/")) return "media_processing";
  if (command.includes("jellyfin") || command.includes("/transcodes/") || command.includes("/cache/transcodes/")) {
    return "jellyfin_transcode";
  }
  return "other";
}

export async function GET() {
  const checkedAt = new Date().toISOString();
  try {
    const { stdout } = await execFileAsync("ps", ["-eo", "pid=,comm=,args="], { timeout: 3000 });
    const processes = stdout
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => /\bffmpeg\b/i.test(line))
      .map((line) => {
        const match = /^(\d+)\s+\S+\s+(.+)$/.exec(line);
        const pid = match ? Number(match[1]) : 0;
        const command = match?.[2] ?? line;
        return {
          pid,
          command,
          pathClass: classifyProcess(command),
        };
      });

    return NextResponse.json({
      dellFfmpegActive: processes.length > 0,
      dellFfmpegProcesses: processes,
      checkedAt,
    });
  } catch (error) {
    return NextResponse.json(
      {
        dellFfmpegActive: false,
        dellFfmpegProcesses: [],
        checkedAt,
        error: error instanceof Error ? error.message : String(error),
      },
      { status: 200 },
    );
  }
}

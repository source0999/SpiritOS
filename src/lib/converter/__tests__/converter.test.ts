import fs from "fs/promises";
import os from "os";
import path from "path";
import { describe, expect, it } from "vitest";

import {
  createDiagnosticsSnapshot,
  parseConverterBatch,
  processConverterJob,
  validateConverterJob,
  type ConverterCommandRunner,
} from "@/lib/converter/authorizedMediaImportService";
import { ConverterQueueService } from "@/lib/converter/converterQueueService";
import { assertUnderRoot, redactDiagnostics, sanitizeFilename, type ConverterRootMap } from "@/lib/converter/converterStorageService";

async function makeRoots(): Promise<ConverterRootMap> {
  const root = await fs.mkdtemp(path.join(os.tmpdir(), "spirit-converter-"));
  return {
    authorizedImports: path.join(root, "authorized-imports"),
    audio: path.join(root, "audio"),
    transcripts: path.join(root, "transcripts"),
    knowledge: path.join(root, "knowledge"),
    logs: path.join(root, "logs"),
  };
}

describe("authorized media converter", () => {
  it("rejects YouTube URLs without authorization", () => {
    const [job] = parseConverterBatch({
      pastedItems: "https://www.youtube.com/watch?v=abc12345678",
      authorization: { affirmed: false },
    });

    const validated = validateConverterJob(job);

    expect(validated.state).toBe("failed");
    expect(validated.error).toMatch(/owned or licensed/i);
  });

  it("creates a queued job for authorized YouTube URLs", () => {
    const [job] = parseConverterBatch({
      pastedItems: "https://youtu.be/abc12345678",
      authorization: { affirmed: true, note: "Britton channel archive" },
    });

    const validated = validateConverterJob(job);

    expect(validated.kind).toBe("youtube");
    expect(validated.state).toBe("queued");
    expect(validated.authorization?.note).toBe("Britton channel archive");
  });

  it("processes batch jobs sequentially", async () => {
    const roots = await makeRoots();
    const order: string[] = [];
    const runner: ConverterCommandRunner = async (_command, args) => {
      order.push(args.at(-1) ?? "unknown");
      await new Promise((resolve) => setTimeout(resolve, 10));
      return {};
    };
    const queue = new ConverterQueueService({
      roots,
      tools: { ffmpeg: true, ytdlp: false, speechToText: false },
      commandRunner: runner,
    });

    queue.enqueueBatch({
      pastedItems: "/tmp/one.mp4\n/tmp/two.mp4",
      authorization: { affirmed: false },
    });
    await queue.start();

    expect(order.map((item) => path.basename(item))).toEqual(["one.mp3", "two.mp3"]);
    expect(queue.snapshot().jobs.map((job) => job.state)).toEqual(["pending_transcription_engine", "pending_transcription_engine"]);
  });

  it("does not require YouTube authorization for local files", () => {
    const [job] = parseConverterBatch({
      pastedItems: "/mnt/spirit-8tb/source/local.mov",
      authorization: { affirmed: false },
    });

    const validated = validateConverterJob(job);

    expect(validated.kind).toBe("local_file");
    expect(validated.state).toBe("queued");
  });

  it("sanitizes filenames and blocks output paths outside the converter root", () => {
    expect(sanitizeFilename("../bad name?.mp4")).toBe(".bad-name.mp4");
    expect(() => assertUnderRoot("/mnt/spirit-8tb/converter/audio", "/mnt/spirit-8tb/converter/../escape.mp3")).toThrow(
      /escapes converter root/i,
    );
  });

  it("stores pasted transcripts as knowledge records", async () => {
    const roots = await makeRoots();
    const [job] = parseConverterBatch({
      manualTranscript: "This is Britton's approved transcript.",
      authorization: { affirmed: true, note: "Self-authored transcript" },
      metadata: { title: "Approved Talk", creator: "Britton", tags: ["spirit"] },
    });

    const processed = await processConverterJob(job, { roots, tools: { speechToText: false } });
    const knowledge = JSON.parse(await fs.readFile(processed.output.knowledgeRecordPath!, "utf8"));

    expect(processed.state).toBe("completed");
    expect(processed.output.transcriptPath).toMatch(/Approved-Talk\.txt$/);
    expect(knowledge.title).toBe("Approved Talk");
    expect(knowledge.authorization.note).toBe("Self-authored transcript");
  });

  it("fails cleanly when ffmpeg is missing", async () => {
    const roots = await makeRoots();
    const [job] = parseConverterBatch({
      pastedItems: "/tmp/source.mp4",
      authorization: { affirmed: false },
    });

    const processed = await processConverterJob(job, { roots, tools: { ffmpeg: false } });

    expect(processed.state).toBe("failed");
    expect(processed.error).toMatch(/Install ffmpeg/i);
  });

  it("redacts secrets from diagnostics", () => {
    const text = redactDiagnostics("yt-dlp --cookies /tmp/cookies.txt https://x.test?token=secret Bearer abc.def");

    expect(text).not.toContain("cookies.txt");
    expect(text).not.toContain("secret");
    expect(text).not.toContain("abc.def");
    expect(text).toContain("[REDACTED]");
  });

  it("redacts diagnostics snapshots", () => {
    const [job] = parseConverterBatch({
      pastedItems: "https://youtu.be/abc12345678?token=secret",
      authorization: { affirmed: true },
    });
    const diagnostic = createDiagnosticsSnapshot({
      ...job,
      commandUsed: "yt-dlp --cookies /tmp/cookies.txt https://youtu.be/abc12345678?token=secret",
    });

    expect(diagnostic).not.toContain("/tmp/cookies.txt");
    expect(diagnostic).not.toContain("token=secret");
  });

  it("supports pause, resume, and cancel state behavior", async () => {
    const roots = await makeRoots();
    const queue = new ConverterQueueService({
      roots,
      tools: { ffmpeg: false, ytdlp: false, speechToText: false },
    });

    queue.enqueueBatch({
      pastedItems: "/tmp/a.mp4\n/tmp/b.mp4",
      authorization: { affirmed: false },
    });

    expect(queue.pause().state).toBe("idle");
    void queue.start();
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(["paused", "idle"]).toContain(queue.pause().state);
    queue.resume();
    expect(["running", "idle"]).toContain(queue.snapshot().state);
    const cancelled = queue.cancel();
    expect(cancelled.state).toBe("cancelled");
    expect(cancelled.jobs.some((job) => job.state === "cancelled" || job.state === "failed")).toBe(true);
  });
});

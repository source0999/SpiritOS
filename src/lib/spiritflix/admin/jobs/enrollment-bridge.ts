export interface SpiritFlixPendingEnrollmentRecord {
  schema: "spiritflix-pending-enrollment/v1";
  enabled: false;
  matchedModel: string;
  confidence: number;
  sourceVideo: string;
  qualityThreshold: number;
  reversible: true;
  reasonCode: "pending_human_confirmation" | "confidence_too_low";
  commands: {
    addPerformer: string[];
    recordCorrection: string[];
    confirmCorrection: string[];
  };
}

export function createSpiritFlixPendingEnrollmentRecord(input: {
  matchedModel: string;
  confidence: number;
  sourceVideo: string;
  sidecarPath?: string;
  faceImagePath?: string;
  qualityThreshold?: number;
}): SpiritFlixPendingEnrollmentRecord {
  const qualityThreshold = input.qualityThreshold ?? 0.92;
  const sidecarPath = input.sidecarPath ?? `${input.sourceVideo}.face-meta.json`;
  const faceImagePath = input.faceImagePath ?? "<reviewed-face-crop-path>";
  return {
    schema: "spiritflix-pending-enrollment/v1",
    enabled: false,
    matchedModel: input.matchedModel,
    confidence: input.confidence,
    sourceVideo: input.sourceVideo,
    qualityThreshold,
    reversible: true,
    reasonCode: input.confidence >= qualityThreshold ? "pending_human_confirmation" : "confidence_too_low",
    commands: {
      addPerformer: ["scripts/media/face_organizer.py", "--add-performer", input.matchedModel, "--face-image", faceImagePath, "--apply"],
      recordCorrection: ["scripts/media/face_organizer.py", "--record-correction", input.matchedModel, "--sidecar", sidecarPath, "--apply"],
      confirmCorrection: ["scripts/media/face_organizer.py", "--confirm-correction", "--sidecar", sidecarPath, "--apply"],
    },
  };
}


import { spawn } from "node:child_process";

const DEFAULT_ENROLL_TIMEOUT_MS = 120_000;

export interface SpiritFlixEnrollmentBridgeInput {
  matchedModel: string;
  confidence: number;
  sourceVideo: string;
  sidecarPath?: string;
  minFaceScore?: number;
  command?: string;
  scriptPath?: string;
  timeoutMs?: number;
  cwd?: string;
}

export interface SpiritFlixEnrollmentReceipt {
  schema: "spiritflix-enrollment-receipt/v1";
  status: "completed" | "failed" | "skipped";
  matchedModel: string;
  confidence: number;
  sourceVideo: string;
  sidecarPath: string;
  minFaceScore: number;
  command: string;
  args: string[];
  code: number | null;
  timedOut: boolean;
  stdout: string;
  stderr: string;
  enabled: true;
}

function runCommand(command: string, args: string[], timeoutMs: number, cwd?: string): Promise<{ code: number | null; timedOut: boolean; stdout: string; stderr: string }> {
  return new Promise((resolve) => {
    const proc = spawn(command, args, { cwd, shell: false });
    let stdout = "";
    let stderr = "";
    let settled = false;
    let timedOut = false;
    const finish = (code: number | null) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code, timedOut, stdout, stderr });
    };
    const timer = setTimeout(() => {
      timedOut = true;
      proc.kill("SIGKILL");
      finish(null);
    }, timeoutMs);
    proc.stdout.on("data", (chunk: Buffer) => { stdout += chunk.toString("utf8"); });
    proc.stderr.on("data", (chunk: Buffer) => { stderr += chunk.toString("utf8"); });
    proc.on("error", (error) => { stderr += error.message; finish(null); });
    proc.on("close", finish);
  });
}

export async function runSpiritFlixEnrollmentBridge(input: SpiritFlixEnrollmentBridgeInput): Promise<SpiritFlixEnrollmentReceipt> {
  const minFaceScore = input.minFaceScore ?? 0.86;
  const sidecarPath = input.sidecarPath ?? `${input.sourceVideo}.face-meta.json`;
  const command = input.command ?? process.env.SPIRITFLIX_FACE_ORGANIZER_PYTHON ?? "/home/source/SpiritOS/.venv-face-organizer/bin/python";
  const scriptPath = input.scriptPath ?? "scripts/media/face_organizer.py";
  const args = [
    scriptPath,
    "--enroll-selected-crops",
    "--performer",
    input.matchedModel,
    "--sidecar",
    sidecarPath,
    "--source-video",
    input.sourceVideo,
    "--min-face-score",
    String(minFaceScore),
    "--apply",
  ];
  if (input.confidence < minFaceScore) {
    return {
      schema: "spiritflix-enrollment-receipt/v1",
      status: "skipped",
      matchedModel: input.matchedModel,
      confidence: input.confidence,
      sourceVideo: input.sourceVideo,
      sidecarPath,
      minFaceScore,
      command,
      args,
      code: null,
      timedOut: false,
      stdout: "",
      stderr: "confidence below min_face_score",
      enabled: true,
    };
  }
  const result = await runCommand(command, args, input.timeoutMs ?? DEFAULT_ENROLL_TIMEOUT_MS, input.cwd ?? process.cwd());
  return {
    schema: "spiritflix-enrollment-receipt/v1",
    status: result.code === 0 && !result.timedOut ? "completed" : "failed",
    matchedModel: input.matchedModel,
    confidence: input.confidence,
    sourceVideo: input.sourceVideo,
    sidecarPath,
    minFaceScore,
    command,
    args,
    code: result.code,
    timedOut: result.timedOut,
    stdout: result.stdout,
    stderr: result.stderr,
    enabled: true,
  };
}

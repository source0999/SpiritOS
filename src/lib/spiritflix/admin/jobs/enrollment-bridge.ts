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

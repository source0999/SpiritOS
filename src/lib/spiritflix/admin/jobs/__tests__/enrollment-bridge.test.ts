import { describe, expect, it } from "vitest";
import { createSpiritFlixPendingEnrollmentRecord } from "../enrollment-bridge";

describe("SpiritFlix pending enrollment bridge", () => {
  it("records source video, thresholds, and disabled face organizer write commands", () => {
    const record = createSpiritFlixPendingEnrollmentRecord({
      matchedModel: "Sava Schultz",
      confidence: 0.94,
      sourceVideo: "/media/yes/clip.mp4",
      faceImagePath: "/tmp/face.jpg",
    });

    expect(record).toEqual(expect.objectContaining({
      schema: "spiritflix-pending-enrollment/v1",
      enabled: false,
      matchedModel: "Sava Schultz",
      sourceVideo: "/media/yes/clip.mp4",
      qualityThreshold: 0.92,
      reversible: true,
      reasonCode: "pending_human_confirmation",
    }));
    expect(record.commands.addPerformer).toEqual(["scripts/media/face_organizer.py", "--add-performer", "Sava Schultz", "--face-image", "/tmp/face.jpg", "--apply"]);
    expect(record.commands.recordCorrection).toContain("--record-correction");
    expect(record.commands.confirmCorrection).toContain("--confirm-correction");
  });

  it("keeps low-confidence matches disabled", () => {
    const record = createSpiritFlixPendingEnrollmentRecord({
      matchedModel: "Maybe",
      confidence: 0.4,
      sourceVideo: "/media/yes/clip.mp4",
    });

    expect(record.enabled).toBe(false);
    expect(record.reasonCode).toBe("confidence_too_low");
  });
});

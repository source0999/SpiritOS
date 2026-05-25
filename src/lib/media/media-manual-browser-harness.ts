import {
  createMediaIndexedDbManualAcceptanceReport,
  type MediaIndexedDbManualAcceptanceOptions,
  type MediaIndexedDbManualAcceptanceReport,
} from "@/lib/media/media-indexeddb-manual-acceptance";

export const MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL =
  "spiritMediaManualAcceptance";

export type MediaManualBrowserHarness = {
  version: 1;
  runIndexedDbAcceptance: (
    options?: Omit<MediaIndexedDbManualAcceptanceOptions, "storage">,
  ) => Promise<MediaIndexedDbManualAcceptanceReport>;
  uninstall: () => void;
};

type HarnessWindow = {
  localStorage?: Storage;
  [MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL]?: MediaManualBrowserHarness;
};

export type InstallMediaManualBrowserHarnessOptions = {
  targetWindow?: HarnessWindow | null;
  storage?: Storage | null;
};

function getBrowserWindow(): HarnessWindow | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window;
}

export function installMediaManualBrowserHarness(
  options: InstallMediaManualBrowserHarnessOptions = {},
): MediaManualBrowserHarness | null {
  const targetWindow =
    "targetWindow" in options ? options.targetWindow : getBrowserWindow();
  if (!targetWindow) {
    return null;
  }

  const harness: MediaManualBrowserHarness = {
    version: 1,
    runIndexedDbAcceptance: (runOptions = {}) => {
      const storage =
        "storage" in options ? options.storage : targetWindow.localStorage;

      return createMediaIndexedDbManualAcceptanceReport({
        ...runOptions,
        storage,
      });
    },
    uninstall: () => {
      if (targetWindow[MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL] === harness) {
        delete targetWindow[MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL];
      }
    },
  };

  targetWindow[MEDIA_MANUAL_BROWSER_HARNESS_GLOBAL] = harness;
  return harness;
}

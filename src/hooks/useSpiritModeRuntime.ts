"use client";

// ── useSpiritModeRuntime - profile + personalization fields for /api/spirit (Prompt 10D) ─
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type MutableRefObject,
} from "react";

import type { ModelProfile } from "@/lib/spirit/model-profile.types";
import { getModelProfile } from "@/lib/spirit/model-profiles";
import { DEFAULT_MODEL_PROFILE_ID } from "@/lib/spirit/model-profile.types";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import {
  buildModeAwarePersonalizationSummary,
  loadSpiritUserProfile,
} from "@/lib/spirit/spirit-user-profile";
import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

export type SpiritThreadRuntimeModeSlice = {
  activeModelProfileId: ModelProfileId;
  setActiveModelProfile: (id: ModelProfileId) => void | Promise<void>;
};

export type UseSpiritModeRuntimeInput = {
  runtimeSurface: SpiritRuntimeSurface;
  persistenceEnabled: boolean;
  /** Dexie-backed profile focus; ignored when `persistenceEnabled` is false */
  threadRuntime: SpiritThreadRuntimeModeSlice;
};

export type SpiritModeRuntime = {
  runtimeSurface: SpiritRuntimeSurface;
  runtimeSurfaceRef: MutableRefObject<SpiritRuntimeSurface>;
  activeModelProfileId: ModelProfileId;
  activeModelProfile: ModelProfile;
  setActiveModelProfile: (id: ModelProfileId) => void | Promise<void>;
  /** Same id as state - transport reads mid-flight without rerunning effects too late */
  modelProfileIdRef: MutableRefObject<ModelProfileId>;

  personalizationSummary: string;
  personalizationEnabled: boolean;
  refreshPersonalizationPreview: () => void;

  profilePanelOpen: boolean;
  setProfilePanelOpen: (value: boolean) => void;

  requestBodyModeFields: {
    modelProfileId: ModelProfileId;
    runtimeSurface: SpiritRuntimeSurface;
    personalizationSummary?: string;
  };
};

export function useSpiritModeRuntime(
  input: UseSpiritModeRuntimeInput,
): SpiritModeRuntime {
  const [ephemeralProfileId, setEphemeralProfileId] =
    useState<ModelProfileId>(DEFAULT_MODEL_PROFILE_ID);

  const activeModelProfileId = input.persistenceEnabled
    ? input.threadRuntime.activeModelProfileId
    : ephemeralProfileId;

  const setActiveModelProfile = useCallback(
    async (id: ModelProfileId) => {
      if (input.persistenceEnabled) {
        await input.threadRuntime.setActiveModelProfile(id);
      } else {
        setEphemeralProfileId(id);
      }
    },
    [input.persistenceEnabled, input.threadRuntime],
  );

  const modelProfileIdRef = useRef(activeModelProfileId);
  const runtimeSurfaceRef = useRef(input.runtimeSurface);
  /** Bumps when profile JSON changes so personalization preview recomputes */
  const [profileEpoch, setProfileEpoch] = useState(0);
  useEffect(() => {
    modelProfileIdRef.current = activeModelProfileId;
  }, [activeModelProfileId]);
  useEffect(() => {
    runtimeSurfaceRef.current = input.runtimeSurface;
  }, [input.runtimeSurface]);
  const refreshPersonalizationPreview = useCallback(() => {
    setProfileEpoch((n: number) => n + 1);
  }, []);

  const personalizationPack = useMemo(
    () => {
      const profile = loadSpiritUserProfile();
      const summary = buildModeAwarePersonalizationSummary(
        profile,
        activeModelProfileId,
      ).trim();
      return { profile, summary };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- profileEpoch busts preview after profile JSON edits (refreshPersonalizationPreview)
    [activeModelProfileId, profileEpoch],
  );

  const personalizationEnabled = personalizationPack.profile.sendPersonalizationToServer;

  const [profilePanelOpen, setProfilePanelOpen] = useState(false);

  const activeModelProfile = useMemo(
    () => getModelProfile(activeModelProfileId),
    [activeModelProfileId],
  );

  const requestBodyModeFields = useMemo((): SpiritModeRuntime["requestBodyModeFields"] => {
    const base = {
      modelProfileId: activeModelProfileId,
      runtimeSurface: input.runtimeSurface,
    };
    const s = personalizationPack.summary;
    if (!s) return base;
    return { ...base, personalizationSummary: s };
  }, [activeModelProfileId, input.runtimeSurface, personalizationPack.summary]);

  return useMemo(
    (): SpiritModeRuntime => ({
      runtimeSurface: input.runtimeSurface,
      runtimeSurfaceRef,
      activeModelProfileId,
      activeModelProfile,
      setActiveModelProfile,
      modelProfileIdRef,

      personalizationSummary: personalizationPack.summary,
      personalizationEnabled,
      refreshPersonalizationPreview,

      profilePanelOpen,
      setProfilePanelOpen,

      requestBodyModeFields,
    }),
    [
      input.runtimeSurface,
      activeModelProfileId,
      activeModelProfile,
      setActiveModelProfile,
      personalizationPack.summary,
      personalizationEnabled,
      refreshPersonalizationPreview,
      profilePanelOpen,
      requestBodyModeFields,
    ],
  );
}

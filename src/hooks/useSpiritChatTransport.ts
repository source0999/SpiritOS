"use client";

/* eslint-disable react-hooks/set-state-in-effect, react-hooks/refs, react-hooks/immutability -- transport hook mirrors legacy SpiritChat side effects; refinements are Prompt 10D+ */
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import type { UIMessage } from "ai";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type Dispatch,
  type FormEvent,
  type KeyboardEvent,
  type MutableRefObject,
  type RefObject,
  type SetStateAction,
} from "react";

import { usePersistentChat } from "@/hooks/usePersistentChat";
import type { SpiritModeRuntime } from "@/hooks/useSpiritModeRuntime";
import type { SpiritTTS } from "@/hooks/useSpiritVoiceRuntime";
import {
  dedupeUIMessagesById,
  deleteUIMessageById,
  persistedChatRowsToUIMessages,
  textFromParts,
  updateUIMessageText,
} from "@/lib/chat-utils";
import { generateChatRecordId } from "@/lib/chat-persistence";
import { sanitizeAssistantVisibleText } from "@/lib/spirit/assistant-output-sanitizer";
import { stripFakeCitationsWhenNoSources } from "@/lib/spirit/research-source-enforcement";
import {
  draftResearchPlanFromPrompt,
  researchPlanToSummary,
  type ResearchPlan,
} from "@/lib/spirit/research-plan";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import {
  planAssistantOutboundFinish,
  runAutoSpeakAssistantFinish,
  shouldStopTtsOnOutboundSubmit,
} from "@/lib/spirit-chat-tts";
import {
  parseSpiritWebSourcesHeader,
  type SpiritWebSourcesHeaderPayload,
} from "@/lib/spirit/spirit-web-sources";
import {
  parseSpiritSearchHeaders,
  type SpiritSearchStatusNormalized,
} from "@/lib/spirit/spirit-search-response-headers";
import {
  buildModeAwarePersonalizationSummary,
  loadSpiritUserProfile,
} from "@/lib/spirit/spirit-user-profile";
import { decideSpiritRoute, type SpiritRouteLane } from "@/lib/spirit/spirit-route-decision";
import {
  spiritToolCardToActivityEvent,
  type SpiritActivityEvent,
} from "@/lib/spirit/spirit-activity-events";
import { mergeSpiritToolActivityCardsForMessage } from "@/lib/spirit/spirit-assistant-tool-activity";
import { TTS_TEXT_LIMIT } from "@/lib/tts/tts-text-budget";
import {
  getRecentOracleMemoryEvents,
  isOracleMemoryEnabled,
  summarizeOracleMemoryForPrompt,
} from "@/lib/oracle/oracle-memory";

type WebSearchPreference = "unset" | "enabled" | "disabled";

export type UseSpiritChatTransportInput = {
  api: string;
  persistence: boolean;
  persistenceEnabled: boolean;
  savedChatShell: boolean;
  workspaceChrome: boolean;
  attachSpiritBody: boolean;
  persistent: ReturnType<typeof usePersistentChat>;
  modeRuntime: SpiritModeRuntime;
  /** Unified mode id (Dexie thread profile or Oracle ephemeral) */
  activeModelProfileId: ModelProfileId;
  ttsRef: RefObject<SpiritTTS | null>;
  ttsSpeakGateRef: RefObject<{ isEnabled: boolean; autoSpeakAssistant: boolean }>;
  pushActivity: (e: Omit<SpiritActivityEvent, "id" | "at">) => void;
  /** Scroll container coordination - optional for embedded/minimal shells */
  outboundScrollRefs?: {
    forceScrollOnNextMessageRef: MutableRefObject<boolean>;
    shouldStickToBottomRef: MutableRefObject<boolean>;
  } | null;
};

export type SpiritChatTransport = {
  messages: UIMessage[];
  setMessages: (
    messages: UIMessage[] | ((messages: UIMessage[]) => UIMessage[]),
  ) => void;
  sendMessage: ReturnType<typeof useChat>["sendMessage"];
  regenerate: ReturnType<typeof useChat>["regenerate"];
  stop: ReturnType<typeof useChat>["stop"];
  status: ReturnType<typeof useChat>["status"];
  error: ReturnType<typeof useChat>["error"];
  input: string;
  setInput: (v: string | ((p: string) => string)) => void;
  isBusy: boolean;
  submitMessage: () => void;
  onSubmit: (e: FormEvent) => void;
  onKeyDown: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  runSpiritOutbound: (t: string) => Promise<void>;

  assistantSourceProof: import("@/hooks/useSpiritVoiceRuntime").AssistantSourceProofState;
  setAssistantSourceProof: Dispatch<
    SetStateAction<import("@/hooks/useSpiritVoiceRuntime").AssistantSourceProofState>
  >;

  handleMessageDelete: (id: string) => void;
  handleMessageEditSave: (id: string, text: string) => void;
  handleRegenerateAssistant: (assistantId: string) => Promise<void>;
  lastAssistantId: string | null;

  deepThinkEnabled: boolean;
  setDeepThinkEnabled: Dispatch<SetStateAction<boolean>>;
  webSearchPreference: WebSearchPreference;
  setWebSearchPreference: Dispatch<SetStateAction<WebSearchPreference>>;
  teacherWebSearchEnabled: boolean;
  setTeacherWebSearchEnabled: Dispatch<SetStateAction<boolean>>;
  webSearchOptOut: boolean;

  lastOutboundUserSnapshot: string;
  lastWebSearchHeader: string | null;
  lastSearchStatus: SpiritSearchStatusNormalized;
  lastSearchProvider: string | null;
  lastSearchQuery: string | null;
  lastSearchElapsedMs: number | null;
  lastSearchKind: "researcher" | "teacher" | "none";
  lastSearchSkipReason: string | null;
  lastHeaderSourceCount: number | null;
  lastWebSourcesPayload: SpiritWebSourcesHeaderPayload | null;
  lastRouteLane: SpiritRouteLane | null;
  lastRouteConfidence: string | null;
  workflowDismissed: boolean;
  setWorkflowDismissed: Dispatch<SetStateAction<boolean>>;
  workflowStepIdx: number;
  setWorkflowStepIdx: Dispatch<SetStateAction<number>>;
  researchPlanOpen: boolean;
  setResearchPlanOpen: Dispatch<SetStateAction<boolean>>;
  researchPlan: ResearchPlan | null;
  setResearchPlan: Dispatch<SetStateAction<ResearchPlan | null>>;
  pendingResearchPlanSummaryRef: React.MutableRefObject<string | null>;
  lastSentForPlanRef: React.MutableRefObject<string>;
  handleResearchPlanClose: () => void;
  handleResearchPlanStart: (plan: ResearchPlan) => void;

  hydrateDraftMarkerRef: React.MutableRefObject<string | null>;
  hydrateSigRef: React.MutableRefObject<string>;
  hydrateThreadFocusRef: React.MutableRefObject<string | null>;
  skipDexieHydrateRef: React.MutableRefObject<boolean>;

  onSidebarNewChatResetHydration: () => void;
  onSidebarSelectResetHydration: () => void;

  assistantOutcomeThreadRef: React.MutableRefObject<string | null>;
  spiritOutboundSeqRef: React.MutableRefObject<number>;
};

export function useSpiritChatTransport(
  input: UseSpiritChatTransportInput,
): SpiritChatTransport {
  const {
    api,
    persistence,
    persistenceEnabled,
    savedChatShell,
    attachSpiritBody,
    persistent,
    modeRuntime,
    activeModelProfileId,
    ttsRef,
    ttsSpeakGateRef,
    pushActivity,
    outboundScrollRefs,
  } = input;

  const modelProfileIdRef = modeRuntime.modelProfileIdRef;
  const runtimeSurfaceRef = modeRuntime.runtimeSurfaceRef;

  const assistantOutcomeThreadRef = useRef<string | null>(null);
  const persistAssistantToThreadRef = useRef(persistent.persistAssistantMessageToThread);
  useEffect(() => {
    persistAssistantToThreadRef.current = persistent.persistAssistantMessageToThread;
  }, [persistent.persistAssistantMessageToThread]);

  const persistentRef = useRef(persistent);
  useEffect(() => {
    persistentRef.current = persistent;
  }, [persistent]);

  const activeThreadIdRef = useRef<string | null>(null);
  useEffect(() => {
    if (!savedChatShell || !persistent.enabled) {
      activeThreadIdRef.current = null;
      return;
    }
    activeThreadIdRef.current = persistent.draftLaneActive
      ? null
      : (persistent.activeThreadId ?? null);
  }, [
    savedChatShell,
    persistent.enabled,
    persistent.draftLaneActive,
    persistent.activeThreadId,
  ]);

  const THREAD_UI_LS = "spirit:threadUiPrefs:v2";
  const THREAD_UI_LEGACY = "spirit:threadUiPrefs:v1";

  const persistUiPrefsToStorage = savedChatShell && persistent.enabled;

  const [deepThinkEnabled, setDeepThinkEnabled] = useState(false);
  const [webSearchPreference, setWebSearchPreference] =
    useState<WebSearchPreference>("unset");
  const [teacherWebSearchEnabled, setTeacherWebSearchEnabled] = useState(true);

  const threadUiStorageKey = useCallback((): string | null => {
    if (!persistUiPrefsToStorage) return null;
    if (persistent.draftLaneActive) return "draft";
    if (persistent.activeThreadId) return persistent.activeThreadId;
    return null;
  }, [
    persistUiPrefsToStorage,
    persistent.draftLaneActive,
    persistent.activeThreadId,
  ]);

  useEffect(() => {
    if (!persistUiPrefsToStorage) return;
    const k = threadUiStorageKey();
    if (!k) return;
    try {
      let raw = window.localStorage.getItem(THREAD_UI_LS);
      if (!raw) raw = window.localStorage.getItem(THREAD_UI_LEGACY);
      const map = raw
        ? (JSON.parse(raw) as Record<
            string,
            { d?: boolean; o?: boolean; w?: boolean; tw?: boolean; wp?: WebSearchPreference }
          >)
        : {};
      const row = map[k];
      setDeepThinkEnabled(Boolean(row?.d));
      let pref: WebSearchPreference = "unset";
      if (row?.wp === "enabled" || row?.wp === "disabled" || row?.wp === "unset") {
        pref = row.wp;
      } else if (row?.o === true) {
        pref = "disabled";
      }
      setWebSearchPreference(pref);
      setTeacherWebSearchEnabled(row?.tw !== false);
    } catch {
      setDeepThinkEnabled(false);
      setWebSearchPreference("unset");
      setTeacherWebSearchEnabled(true);
    }
  }, [persistUiPrefsToStorage, threadUiStorageKey]);

  useEffect(() => {
    if (!persistUiPrefsToStorage) return;
    const k = threadUiStorageKey();
    if (!k) return;
    try {
      const raw = window.localStorage.getItem(THREAD_UI_LS);
      const map = raw
        ? (JSON.parse(raw) as Record<
            string,
            { d?: boolean; o?: boolean; tw?: boolean; wp?: WebSearchPreference }
          >)
        : {};
      map[k] = {
        d: deepThinkEnabled,
        tw: teacherWebSearchEnabled,
        wp: webSearchPreference,
      };
      window.localStorage.setItem(THREAD_UI_LS, JSON.stringify(map));
    } catch {
      /* ignore */
    }
  }, [
    persistUiPrefsToStorage,
    threadUiStorageKey,
    deepThinkEnabled,
    webSearchPreference,
    teacherWebSearchEnabled,
  ]);

  const webSearchOptOut = useMemo(
    () =>
      activeModelProfileId === "researcher" && webSearchPreference === "disabled",
    [activeModelProfileId, webSearchPreference],
  );

  const [researchPlanOpen, setResearchPlanOpen] = useState(false);
  const [researchPlan, setResearchPlan] = useState<ResearchPlan | null>(null);
  const [workflowDismissed, setWorkflowDismissed] = useState(false);
  const [workflowStepIdx, setWorkflowStepIdx] = useState(0);

  const [lastWebSearchHeader, setLastWebSearchHeader] = useState<string | null>(null);
  const [lastSearchStatus, setLastSearchStatus] =
    useState<SpiritSearchStatusNormalized>("none");
  const [lastSearchProvider, setLastSearchProvider] = useState<string | null>(null);
  const [lastSearchQuery, setLastSearchQuery] = useState<string | null>(null);
  const [lastSearchElapsedMs, setLastSearchElapsedMs] = useState<number | null>(null);
  const [lastSearchKind, setLastSearchKind] = useState<"researcher" | "teacher" | "none">(
    "none",
  );
  const [lastSearchSkipReason, setLastSearchSkipReason] = useState<string | null>(null);
  const [lastHeaderSourceCount, setLastHeaderSourceCount] = useState<number | null>(null);
  const [lastWebSourcesPayload, setLastWebSourcesPayload] =
    useState<SpiritWebSourcesHeaderPayload | null>(null);
  const [lastOutboundUserSnapshot, setLastOutboundUserSnapshot] = useState("");
  const [lastRouteLane, setLastRouteLane] = useState<SpiritRouteLane | null>(null);
  const [lastRouteConfidence, setLastRouteConfidence] = useState<string | null>(null);

  const [assistantSourceProof, setAssistantSourceProof] = useState<
    import("@/hooks/useSpiritVoiceRuntime").AssistantSourceProofState
  >(null);

  const pendingResearchPlanSummaryRef = useRef<string | null>(null);
  const lastSentForPlanRef = useRef("");
  const assistantReplyModeRef = useRef<ModelProfileId>(activeModelProfileId);

  const outboundExtrasRef = useRef({
    deepThinkEnabled: false,
    webSearchOptOut: false,
    teacherWebSearchEnabled: true,
  });
  const spiritOutboundSeqRef = useRef(0);
  const lastSearchHdrRef = useRef<string | null>(null);
  const lastSourcesPayloadRef = useRef<SpiritWebSourcesHeaderPayload | null>(null);
  const streamHdrRef = useRef<(myId: number, parsed: ReturnType<typeof parseSpiritSearchHeaders>) => void>(
    () => {},
  );

  useEffect(() => {
    if (activeModelProfileId !== "researcher") {
      setResearchPlanOpen(false);
      setResearchPlan(null);
    }
  }, [activeModelProfileId]);

  const threadFocusKeyRef = useRef<string | null>(null);
  useEffect(() => {
    if (!savedChatShell) return;
    const key = persistent.draftLaneActive
      ? `draft:${persistent.draftLaneId ?? ""}`
      : (persistent.activeThreadId ?? "");
    if (threadFocusKeyRef.current === key) return;
    threadFocusKeyRef.current = key;
    setResearchPlanOpen(false);
    setResearchPlan(null);
    setLastRouteLane(null);
    setLastRouteConfidence(null);
    setLastWebSearchHeader(null);
    setLastWebSourcesPayload(null);
    setLastSearchStatus("none");
    setLastSearchProvider(null);
    setLastSearchQuery(null);
    setLastSearchElapsedMs(null);
    setLastSearchKind("none");
    setLastSearchSkipReason(null);
    setLastHeaderSourceCount(null);
    lastSearchHdrRef.current = null;
    lastSourcesPayloadRef.current = null;
    setAssistantSourceProof(null);
    setWorkflowDismissed(false);
  }, [
    savedChatShell,
    persistent.activeThreadId,
    persistent.draftLaneActive,
    persistent.draftLaneId,
  ]);

  useEffect(() => {
    streamHdrRef.current = (myId, parsed) => {
      if (myId !== spiritOutboundSeqRef.current) return;
      const outcomeThread = assistantOutcomeThreadRef.current;
      const active = activeThreadIdRef.current;
      const draft = persistentRef.current.draftLaneActive;
      if (
        outcomeThread != null &&
        active != null &&
        outcomeThread !== active &&
        !draft
      ) {
        return;
      }
      const h = parsed.webSearch;
      setLastWebSearchHeader(h);
      lastSearchHdrRef.current = h;
      setLastSearchStatus(parsed.searchStatus);
      setLastSearchProvider(parsed.searchProvider);
      setLastSearchQuery(parsed.searchQuery);
      setLastSearchElapsedMs(parsed.searchElapsedMs);
      setLastSearchKind(parsed.searchKind);
      setLastSearchSkipReason(parsed.skipReason);
      setLastHeaderSourceCount(parsed.sourceCount);

      const sourcesJson = parsed.webSourcesJson;
      if (sourcesJson) {
        const src = parseSpiritWebSourcesHeader(sourcesJson);
        setLastWebSourcesPayload(src);
        lastSourcesPayloadRef.current = src;
      } else {
        setLastWebSourcesPayload(null);
        lastSourcesPayloadRef.current = null;
      }
      const laneH = parsed.routeLane;
      if (laneH && (laneH === "local-chat" || laneH === "openai-web-search" || laneH === "research-plan")) {
        if (laneH !== "research-plan") {
          setLastRouteLane(laneH as SpiritRouteLane);
        }
      }
      if (parsed.routeConfidence) setLastRouteConfidence(parsed.routeConfidence);
      if (!savedChatShell) return;
      if (!h || h === "none") return;
      const prov = sourcesJson
        ? (() => {
            try {
              const o = JSON.parse(sourcesJson) as { provider?: string; count?: number };
              return ` · Provider: ${o.provider ?? "unknown"} · Sources found: ${typeof o.count === "number" ? o.count : "?"}`;
            } catch {
              return "";
            }
          })()
        : "";
      const elapsed =
        parsed.searchElapsedMs != null ? ` · ${(parsed.searchElapsedMs / 1000).toFixed(1)}s` : "";
      pushActivity({
        kind: "workflow_step",
        label: `Search: ${parsed.searchStatus}${elapsed}${prov} · Route: ${laneH ?? "?"}`,
      });
    };
  }, [savedChatShell, pushActivity]);

  const handleChatFinish = useCallback(
    (event: { message: UIMessage }) => {
      if (event.message.role !== "assistant") return;

      const threadId = assistantOutcomeThreadRef.current;
      let body = sanitizeAssistantVisibleText(textFromParts(event.message).trim());
      const hdr = lastSearchHdrRef.current;
      const hadVerified =
        hdr === "used" &&
        (lastSourcesPayloadRef.current?.sources?.some((s) => /^https?:\/\//i.test(s.url)) ??
          false);
      if (assistantReplyModeRef.current === "researcher" && !hadVerified) {
        body = stripFakeCitationsWhenNoSources(body);
      }
      const p = persistentRef.current;

      const plan = planAssistantOutboundFinish({
        threadId,
        body,
        activeThreadId: activeThreadIdRef.current,
        draftLaneActive: p.draftLaneActive,
      });

      if (plan.kind === "skip" && plan.reason === "wrong-thread") {
        if (process.env.NODE_ENV === "development") {
          console.info(`[tts] auto-speak skipped: stale thread`);
        }
        return;
      }

      const toolCards = mergeSpiritToolActivityCardsForMessage(event.message);
      for (const c of toolCards) {
        const ev = spiritToolCardToActivityEvent(c);
        const { id: _tid, at: _tat, ...rest } = ev;
        pushActivity(rest as Omit<SpiritActivityEvent, "id" | "at">);
      }

      if (plan.kind === "skip" && plan.reason === "empty-assistant-text") {
        return;
      }

      const proofPayload = {
        messageId: event.message.id,
        hadVerifiedUrls: hadVerified,
        profileId: assistantReplyModeRef.current,
        webSources:
          hadVerified && lastSourcesPayloadRef.current
            ? {
                provider: lastSourcesPayloadRef.current.provider,
                count: lastSourcesPayloadRef.current.count,
                sources: lastSourcesPayloadRef.current.sources.map((s) => ({
                  title: s.title,
                  url: s.url,
                  ...(s.snippet ? { snippet: s.snippet } : {}),
                })),
              }
            : null,
      };

      const shouldDexieCommit = savedChatShell && plan.kind === "commit";

      if (shouldDexieCommit) {
        setAssistantSourceProof(proofPayload);
        assistantOutcomeThreadRef.current = null;
        void persistAssistantToThreadRef.current(threadId!, event.message.id, body);
        pushActivity({
          kind: "assistant_finished",
          label: "Assistant reply finished",
        });
      } else if (!savedChatShell && body.trim()) {
        setAssistantSourceProof(proofPayload);
        assistantOutcomeThreadRef.current = null;
      } else if (savedChatShell && plan.kind === "skip") {
        if (process.env.NODE_ENV === "development") {
          const r =
            plan.reason === "no-outcome-thread"
              ? "no outcome thread"
              : plan.reason;
          console.info(`[spirit-chat] assistant finish skipped: ${r}`);
        }
        return;
      }

      const msgId = event.message.id;
      const bodyForSpeak = body;
      const canAutoSpeak =
        bodyForSpeak.trim().length > 0 &&
        (plan.kind === "commit" ||
          (plan.kind === "skip" && plan.reason === "no-outcome-thread"));

      if (!canAutoSpeak) return;

      queueMicrotask(() => {
        const gate = ttsSpeakGateRef.current;
        const hook = ttsRef.current;
        if (!hook) return;
        runAutoSpeakAssistantFinish({
          text: bodyForSpeak,
          messageId: msgId,
          speak: hook.speak.bind(hook),
          voiceEnabled: gate.isEnabled,
          autoSpeakAssistant: gate.autoSpeakAssistant,
        });
        if (
          bodyForSpeak.length > TTS_TEXT_LIMIT &&
          gate.autoSpeakAssistant &&
          gate.isEnabled
        ) {
          pushActivity({
            kind: "voice_played",
            label: "Voice spoke summary because message was long.",
          });
        }
      });
    },
    [savedChatShell, pushActivity, ttsRef, ttsSpeakGateRef],
  );

  const transport = useMemo(() => {
    if (!attachSpiritBody) {
      return new DefaultChatTransport({ api });
    }
    return new DefaultChatTransport({
      api,
      fetch: async (initInput, init) => {
        const myId = ++spiritOutboundSeqRef.current;
        const res = await globalThis.fetch(initInput, init);
        const parsed = parseSpiritSearchHeaders(res);
        streamHdrRef.current(myId, parsed);
        return res;
      },
      prepareSendMessagesRequest: async ({ body, messages: msgs }) => {
        const profile = loadSpiritUserProfile();
        const summary = buildModeAwarePersonalizationSummary(
          profile,
          modelProfileIdRef.current,
        ).trim();
        const x = outboundExtrasRef.current;
        const rPlan = pendingResearchPlanSummaryRef.current?.trim();
        pendingResearchPlanSummaryRef.current = null;
        let oracleMemoryContext: string | undefined;
        if (isOracleMemoryEnabled()) {
          const events = await getRecentOracleMemoryEvents();
          const ctx = summarizeOracleMemoryForPrompt(events);
          if (ctx) oracleMemoryContext = ctx;
        }
        return {
          body: {
            ...body,
            messages: msgs,
            modelProfileId: modelProfileIdRef.current,
            runtimeSurface: runtimeSurfaceRef.current,
            deepThinkEnabled: x.deepThinkEnabled,
            webSearchOptOut: x.webSearchOptOut,
            teacherWebSearchEnabled: x.teacherWebSearchEnabled,
            ...(rPlan ? { researchPlanSummary: rPlan } : {}),
            ...(summary ? { personalizationSummary: summary } : {}),
            ...(oracleMemoryContext ? { oracleMemoryContext } : {}),
          },
        };
      },
    });
  }, [api, attachSpiritBody, modelProfileIdRef, runtimeSurfaceRef]);

  const { messages, sendMessage, regenerate, stop, status, error, setMessages } = useChat({
    transport,
    onFinish: handleChatFinish,
  });

  const [composerInput, setComposerInput] = useState("");
  const isBusy = status === "submitted" || status === "streaming";

  const submitGuardRef = useRef(false);
  useEffect(() => {
    if (!isBusy) submitGuardRef.current = false;
  }, [isBusy]);

  const hydrateSigRef = useRef("");
  const hydrateThreadFocusRef = useRef<string | null>(null);
  const hydrateDraftMarkerRef = useRef<string | null>(null);
  const skipDexieHydrateRef = useRef(false);

  useEffect(() => {
    if (!savedChatShell || !persistent.enabled) return;

    if (persistent.draftLaneActive) {
      const d = persistent.draftLaneId;
      if (!d) return;

      if (hydrateDraftMarkerRef.current !== d) {
        hydrateDraftMarkerRef.current = d;
        hydrateThreadFocusRef.current = null;
        hydrateSigRef.current = "";
        setMessages([]);
      }
      return;
    }

    hydrateDraftMarkerRef.current = null;

    const threadId = persistent.activeThreadId;
    if (!threadId) return;

    const threadIdSnap = threadId;

    const threadFlip = hydrateThreadFocusRef.current !== threadId;
    if (threadFlip) {
      hydrateThreadFocusRef.current = threadId;
      hydrateSigRef.current = "";
      setMessages([]);
    }

    if (!persistent.isPersistedHydrationReady) return;

    const tail = messages.at(-1);
    const pendingRemoteAssistant =
      !threadFlip &&
      status === "ready" &&
      tail?.role === "assistant" &&
      !persistent.persistedMessages.some((p) => p.id === tail.id);

    if (pendingRemoteAssistant) return;

    const busySameThread = isBusy && !threadFlip;
    if (busySameThread) return;

    if (skipDexieHydrateRef.current) return;

    const visible = persistent.persistedMessages.filter(
      (r) => r.role === "user" || r.role === "assistant",
    );
    const sig = visible.map((r) => `${r.id}\u001f${r.text}`).join("\u001e");
    if (!threadFlip && sig === hydrateSigRef.current) return;
    hydrateSigRef.current = sig;
    const p = persistentRef.current;
    if (p.activeThreadId !== threadIdSnap || p.draftLaneActive) {
      return;
    }
    setMessages(dedupeUIMessagesById(persistedChatRowsToUIMessages(visible)));
  }, [
    savedChatShell,
    persistent.enabled,
    persistent.draftLaneActive,
    persistent.draftLaneId,
    persistent.activeThreadId,
    persistent.persistedMessages,
    persistent.isPersistedHydrationReady,
    isBusy,
    status,
    messages,
    setMessages,
  ]);

  const onSidebarNewChatResetHydration = useCallback(() => {
    hydrateDraftMarkerRef.current = null;
    hydrateSigRef.current = "";
    hydrateThreadFocusRef.current = null;
  }, []);

  const onSidebarSelectResetHydration = useCallback(() => {
    hydrateDraftMarkerRef.current = null;
    hydrateSigRef.current = "";
    hydrateThreadFocusRef.current = null;
  }, []);

  const runSpiritOutbound = useCallback(
    async (t: string) => {
      const trimmed = t.trim();
      if (!trimmed) {
        submitGuardRef.current = false;
        return;
      }
      try {
        outboundExtrasRef.current = {
          deepThinkEnabled,
          webSearchOptOut: activeModelProfileId === "researcher" ? webSearchOptOut : false,
          teacherWebSearchEnabled: activeModelProfileId === "teacher" ? teacherWebSearchEnabled : false,
        };
        assistantReplyModeRef.current = activeModelProfileId;
        setWorkflowDismissed(false);
        lastSentForPlanRef.current = trimmed;
        setLastRouteLane(null);
        setLastRouteConfidence(null);
        setLastOutboundUserSnapshot(trimmed);
        setLastWebSearchHeader(null);
        setLastWebSourcesPayload(null);
        setLastSearchStatus("none");
        setLastSearchProvider(null);
        setLastSearchQuery(null);
        setLastSearchElapsedMs(null);
        setLastSearchKind("none");
        setLastSearchSkipReason(null);
        setLastHeaderSourceCount(null);
        lastSearchHdrRef.current = null;
        lastSourcesPayloadRef.current = null;
        if (outboundScrollRefs) {
          /* Parent-owned scroll refs - same mutation as pre-refactor SpiritChat */
          outboundScrollRefs.forceScrollOnNextMessageRef.current = true;
          outboundScrollRefs.shouldStickToBottomRef.current = true;
        }
        const ttsSnap = ttsRef.current;
        if (
          ttsSnap &&
          shouldStopTtsOnOutboundSubmit({
            autoSpeakAssistant: ttsSnap.state.autoSpeakAssistant,
            isPlaying: ttsSnap.state.isPlaying,
            queueLength: ttsSnap.state.queueLength,
          })
        ) {
          if (process.env.NODE_ENV === "development") {
            console.info("[tts] stopping old audio before submit");
          }
          ttsSnap.stop();
        }

        if (persistent.enabled) {
          const userMsgId = generateChatRecordId();
          const routed = await persistent.persistUserOutboundForSend(trimmed, userMsgId);
          if (!routed) {
            submitGuardRef.current = false;
            return;
          }
          assistantOutcomeThreadRef.current = routed.threadId;
          await sendMessage({
            role: "user",
            id: userMsgId,
            parts: [{ type: "text", text: trimmed }],
          });
          if (savedChatShell) {
            pushActivity({ kind: "message_submitted", label: "Sent message" });
          }
        } else {
          await sendMessage({ text: trimmed });
        }
      } catch (e) {
        assistantOutcomeThreadRef.current = null;
        console.error("[spirit-chat] send pipeline:", e);
        submitGuardRef.current = false;
      } finally {
        setComposerInput("");
      }
    },
    [
      sendMessage,
      persistent,
      savedChatShell,
      pushActivity,
      deepThinkEnabled,
      webSearchOptOut,
      teacherWebSearchEnabled,
      activeModelProfileId,
      ttsRef,
      outboundScrollRefs,
    ],
  );

  const submitMessage = useCallback(() => {
    const t2 = composerInput.trim();
    if (!t2 || isBusy || submitGuardRef.current) return;

    if (persistence && !persistent.canSendOutbound) {
      if (process.env.NODE_ENV === "development") {
        console.warn("[spirit-chat] submit blocked: canSendOutbound false", {
          threadsLoading: persistent.threadsLoading,
          activeThreadId: persistent.activeThreadId,
          draftLaneActive: persistent.draftLaneActive,
        });
      }
      return;
    }

    submitGuardRef.current = true;
    setAssistantSourceProof(null);

    const routePre = decideSpiritRoute({
      modelProfileId: activeModelProfileId,
      lastUserText: t2,
      deepThinkEnabled,
      webSearchOptOut,
      teacherWebSearchEnabled,
      webSearchGloballyEnabled: true,
      modelHint: "",
    });

    if (
      persistent.enabled &&
      activeModelProfileId === "researcher" &&
      routePre.lane === "research-plan"
    ) {
      lastSentForPlanRef.current = t2;
      setResearchPlan(draftResearchPlanFromPrompt(t2));
      setResearchPlanOpen(true);
      submitGuardRef.current = false;
      setComposerInput("");
      return;
    }

    void runSpiritOutbound(t2);
  }, [
    composerInput,
    isBusy,
    runSpiritOutbound,
    persistence,
    persistent,
    deepThinkEnabled,
    webSearchOptOut,
    teacherWebSearchEnabled,
    activeModelProfileId,
  ]);

  const onSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      submitMessage();
    },
    [submitMessage],
  );

  const onKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.nativeEvent.isComposing) return;
      if (e.key !== "Enter" || e.shiftKey) return;
      e.preventDefault();
      submitMessage();
    },
    [submitMessage],
  );

  const displayMessages = useMemo(
    () => dedupeUIMessagesById(messages),
    [messages],
  );

  const lastAssistantId = useMemo(() => {
    for (let i = displayMessages.length - 1; i >= 0; i--) {
      const m = displayMessages[i]!;
      if (m.role === "assistant") return m.id;
    }
    return null;
  }, [displayMessages]);

  const {
    deletePersistedMessage,
    updatePersistedMessageText,
  } = persistent;

  const handleMessageDelete = useCallback(
    (id: string) => {
      if (!window.confirm("Delete this message?")) return;
      setMessages((prev) => dedupeUIMessagesById(deleteUIMessageById(prev, id)));
      if (persistenceEnabled) void deletePersistedMessage(id);
    },
    [persistenceEnabled, deletePersistedMessage, setMessages],
  );

  const handleMessageEditSave = useCallback(
    (id: string, text: string) => {
      setMessages((prev) => dedupeUIMessagesById(updateUIMessageText(prev, id, text)));
      if (persistenceEnabled) void updatePersistedMessageText(id, text);
    },
    [persistenceEnabled, updatePersistedMessageText, setMessages],
  );

  const handleRegenerateAssistant = useCallback(
    async (assistantId: string) => {
      if (assistantId !== lastAssistantId) {
        console.info(
          "[spirit-chat] regenerate only supported for the latest assistant reply",
        );
        return;
      }
      if (persistenceEnabled) {
        skipDexieHydrateRef.current = true;
        try {
          await deletePersistedMessage(assistantId);
          await regenerate({ messageId: assistantId });
        } catch (e) {
          console.error("[spirit-chat] regenerate failed:", e);
        } finally {
          skipDexieHydrateRef.current = false;
        }
        return;
      }
      try {
        await regenerate({ messageId: assistantId });
      } catch (e) {
        console.error("[spirit-chat] regenerate failed:", e);
      }
    },
    [persistenceEnabled, deletePersistedMessage, lastAssistantId, regenerate],
  );

  const handleResearchPlanClose = useCallback(() => {
    setResearchPlanOpen(false);
    setResearchPlan(null);
    lastSentForPlanRef.current = "";
  }, []);

  const handleResearchPlanStart = useCallback(
    (plan: ResearchPlan) => {
      pendingResearchPlanSummaryRef.current = researchPlanToSummary(plan);
      setResearchPlanOpen(false);
      setResearchPlan(null);
      submitGuardRef.current = true;
      setAssistantSourceProof(null);
      void runSpiritOutbound(lastSentForPlanRef.current.trim());
      pushActivity({
        kind: "workflow_step",
        label: "Research plan approved - running /api/spirit",
      });
    },
    [pushActivity, runSpiritOutbound],
  );

  return useMemo(
    (): SpiritChatTransport => ({
      messages,
      setMessages,
      sendMessage,
      regenerate,
      stop,
      status,
      error,
      input: composerInput,
      setInput: setComposerInput,
      isBusy,
      submitMessage,
      onSubmit,
      onKeyDown,
      runSpiritOutbound,

      assistantSourceProof,
      setAssistantSourceProof,

      handleMessageDelete,
      handleMessageEditSave,
      handleRegenerateAssistant,
      lastAssistantId,

      deepThinkEnabled,
      setDeepThinkEnabled,
      webSearchPreference,
      setWebSearchPreference,
      teacherWebSearchEnabled,
      setTeacherWebSearchEnabled,
      webSearchOptOut,

      lastOutboundUserSnapshot,
      lastWebSearchHeader,
      lastSearchStatus,
      lastSearchProvider,
      lastSearchQuery,
      lastSearchElapsedMs,
      lastSearchKind,
      lastSearchSkipReason,
      lastHeaderSourceCount,
      lastWebSourcesPayload,
      lastRouteLane,
      lastRouteConfidence,
      workflowDismissed,
      setWorkflowDismissed,
      workflowStepIdx,
      setWorkflowStepIdx,
      researchPlanOpen,
      setResearchPlanOpen,
      researchPlan,
      setResearchPlan,
      pendingResearchPlanSummaryRef,
      lastSentForPlanRef,
      handleResearchPlanClose,
      handleResearchPlanStart,

      hydrateDraftMarkerRef,
      hydrateSigRef,
      hydrateThreadFocusRef,
      skipDexieHydrateRef,

      onSidebarNewChatResetHydration,
      onSidebarSelectResetHydration,

      assistantOutcomeThreadRef,
      spiritOutboundSeqRef,
    }),
    [
      messages,
      setMessages,
      sendMessage,
      regenerate,
      stop,
      status,
      error,
      composerInput,
      isBusy,
      submitMessage,
      onSubmit,
      onKeyDown,
      runSpiritOutbound,
      assistantSourceProof,
      handleMessageDelete,
      handleMessageEditSave,
      handleRegenerateAssistant,
      lastAssistantId,
      deepThinkEnabled,
      webSearchPreference,
      teacherWebSearchEnabled,
      webSearchOptOut,
      lastOutboundUserSnapshot,
      lastWebSearchHeader,
      lastSearchStatus,
      lastSearchProvider,
      lastSearchQuery,
      lastSearchElapsedMs,
      lastSearchKind,
      lastSearchSkipReason,
      lastHeaderSourceCount,
      lastWebSourcesPayload,
      lastRouteLane,
      lastRouteConfidence,
      workflowDismissed,
      workflowStepIdx,
      setWorkflowStepIdx,
      researchPlanOpen,
      researchPlan,
      handleResearchPlanClose,
      handleResearchPlanStart,
      onSidebarNewChatResetHydration,
      onSidebarSelectResetHydration,
    ],
  );
}

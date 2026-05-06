"use client";

// ── SpiritChat - messages + transport + input (one implementation to rule them) ─
// > Used by: `/chat` shell (SpiritWorkspaceShell), Neural corpse, `/oracle` via OracleVoiceSurface - stop cloning useChat + JSX
// > Design language: _blueprints/design_system.md - @theme chalk/cyan, glass seams
import { memo, useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUp, PanelLeft, PanelLeftClose, Activity, UserRound, SlidersHorizontal } from "lucide-react";
import { ChatThreadSidebar } from "@/components/chat/ChatThreadSidebar";
import { MobileChatTopBar } from "@/components/chat/MobileChatTopBar";
import { MobileThreadDrawer } from "@/components/chat/MobileThreadDrawer";
import { ModelProfileSelector } from "@/components/chat/ModelProfileSelector";
import { ChatActiveModeBadge } from "@/components/chat/ChatActiveModeBadge";
import { SpiritActivityPanel } from "@/components/chat/SpiritActivityPanel";
import { ResearchPlanPanel } from "@/components/chat/ResearchPlanPanel";
import { SpiritUserProfilePanel } from "@/components/chat/SpiritUserProfilePanel";
import { SpiritWorkflowVisualizer } from "@/components/chat/SpiritWorkflowVisualizer";
import { ChatThreadWorkspaceMenu } from "@/components/chat/ChatThreadWorkspaceMenu";
import { SpiritMessage } from "@/components/chat/SpiritMessage";
import { VoiceControl } from "@/components/chat/VoiceControl";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { useSpiritThreadRuntime } from "@/hooks/useSpiritThreadRuntime";
import { useSpiritModeRuntime } from "@/hooks/useSpiritModeRuntime";
import { useSpiritVoiceRuntime, useTtsSpeakGateRef } from "@/hooks/useSpiritVoiceRuntime";
import { useSpiritChatTransport } from "@/hooks/useSpiritChatTransport";
import { useTTS } from "@/hooks/useTTS";
import { isNearBottom } from "@/lib/chat-scroll";
import { dedupeUIMessagesById, textFromParts } from "@/lib/chat-utils";
import { sanitizeAssistantVisibleText } from "@/lib/spirit/assistant-output-sanitizer";
import { stripFakeCitationsWhenNoSources } from "@/lib/spirit/research-source-enforcement";
import { cn } from "@/lib/cn";
import { useSpiritWorkspaceMobileChrome } from "@/components/dashboard/SpiritWorkspaceMobileChromeContext";
import { useMediaMinWidthLg } from "@/lib/hooks/useMediaMinWidthLg";
import { OracleVoiceStatusCard } from "@/components/oracle/OracleVoiceStatusCard";
import { formatTtsFriendlyStartSummary } from "@/lib/tts/format-tts-latency";
import { TTS_SUMMARY_TRIGGER_CHARS } from "@/lib/tts/tts-text-budget";
import { deriveOracleVoiceStatus } from "@/lib/oracle/oracle-voice-session";
import { getSpiritRuntimeSurfaceDisplayLabel } from "@/lib/spirit/spirit-client-runtime-hint";
import {
  appendSpiritActivityEvent,
  type SpiritActivityEvent,
} from "@/lib/spirit/spirit-activity-events";
import { decideSpiritRoute, type SpiritRouteLane } from "@/lib/spirit/spirit-route-decision";
import { workflowStepsFromServerDecision } from "@/lib/spirit/spirit-workflow-events";
import { draftResearchPlanFromPrompt } from "@/lib/spirit/research-plan";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { getModelProfile } from "@/lib/spirit/model-profiles";
import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";
import { isLikelyCasualShortMessage, wantsTeacherWebStudyAids } from "@/lib/spirit/response-budget";

export type SpiritChatProps = {
  api?: string;
  /** `/oracle` passes `"oracle"` so /api/spirit uses ORACLE_OLLAMA_MODEL lane. */
  runtimeSurface?: SpiritRuntimeSurface;
  variant?: "embedded" | "standalone" | "workspace";
  /** Local Dexie threads + outbound user persists (standalone/workspace). */
  persistence?: boolean;
  /** When persistence is on, hides the GPT-style thread rail (rare escapes). Defaults true. */
  showThreadSidebar?: boolean;
  /** Mobile slide-over threads; workspace shell lifts this into the chrome header toggle. */
  mobileThreadRail?: {
    open: boolean;
    onOpenChange: (next: boolean) => void;
  };
  /** `/oracle` Voice MVP - extra chrome; keeps SpiritChat as single transport owner. */
  oracleVoiceSurface?: boolean;
  footerHint?: ReactNode;
  emptyState?: ReactNode;
  shellClassName?: string;
  title?: string;
  subtitle?: string;
};

const SpiritChatInner = memo(function SpiritChatInner({
  api = "/api/spirit",
  runtimeSurface: runtimeSurfaceProp = "chat",
  variant = "embedded",
  persistence = false,
  showThreadSidebar = true,
  mobileThreadRail,
  footerHint,
  emptyState,
  shellClassName,
  title,
  subtitle,
  oracleVoiceSurface = false,
}: SpiritChatProps) {
  const [internalMobileThreadOpen, setInternalMobileThreadOpen] =
    useState(false);

  const savedChatShell =
    persistence && (variant === "standalone" || variant === "workspace");
  const workspaceChrome =
    savedChatShell || runtimeSurfaceProp === "oracle";

  const threadRt = useSpiritThreadRuntime({
    enabled: persistence,
    sidebarFeaturesEnabled: Boolean(savedChatShell && persistence),
  });
  const persistent = threadRt.persistent;

  const modeRt = useSpiritModeRuntime({
    runtimeSurface: runtimeSurfaceProp,
    persistenceEnabled: persistence,
    threadRuntime: {
      activeModelProfileId: persistent.activeModelProfileId,
      setActiveModelProfile: persistent.setActiveModelProfile,
    },
  });

  const tts = useTTS();
  const ttsRef = useRef(tts);
  ttsRef.current = tts;
  const ttsSpeakGateRef = useTtsSpeakGateRef(tts);
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const composerTextareaRef = useRef<HTMLTextAreaElement | null>(null);
  const shouldStickToBottomRef = useRef(true);
  const forceScrollOnNextMessageRef = useRef(false);

  const showPersistedThreads =
    savedChatShell && showThreadSidebar !== false;

  /** Slide-over threads on small screens; workspace shell can own the toggle via `mobileThreadRail`. */
  const mobileThreadDrawer = useMemo(() => {
    if (!showPersistedThreads) return undefined;
    if (variant === "workspace") {
      return (
        mobileThreadRail ?? {
          open: internalMobileThreadOpen,
          onOpenChange: setInternalMobileThreadOpen,
        }
      );
    }
    if (variant === "standalone") {
      return {
        open: internalMobileThreadOpen,
        onOpenChange: setInternalMobileThreadOpen,
      };
    }
    return undefined;
  }, [
    showPersistedThreads,
    variant,
    mobileThreadRail,
    internalMobileThreadOpen,
  ]);

  const isLg = useMediaMinWidthLg();
  const workspaceMobileChrome = useSpiritWorkspaceMobileChrome();

  const ACTIVITY_LS_KEY = "spirit:workspaceActivity:v1";

  const [workspaceActivity, setWorkspaceActivity] = useState<SpiritActivityEvent[]>([]);
  const [activityOpen, setActivityOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [threadMenuOpen, setThreadMenuOpen] = useState(false);
  const [modeToast, setModeToast] = useState<string | null>(null);

  const pushActivity = useCallback((e: Omit<SpiritActivityEvent, "id" | "at">) => {
    setWorkspaceActivity((prev) => {
      const next = appendSpiritActivityEvent(prev, e);
      try {
        window.localStorage.setItem(ACTIVITY_LS_KEY, JSON.stringify(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  const transport = useSpiritChatTransport({
    api,
    persistence,
    persistenceEnabled: persistence,
    savedChatShell,
    workspaceChrome,
    attachSpiritBody: savedChatShell || runtimeSurfaceProp === "oracle",
    persistent,
    modeRuntime: modeRt,
    activeModelProfileId: modeRt.activeModelProfileId,
    ttsRef,
    ttsSpeakGateRef,
    pushActivity,
    outboundScrollRefs: {
      forceScrollOnNextMessageRef,
      shouldStickToBottomRef,
    },
  });

  const voiceRt = useSpiritVoiceRuntime({
    tts,
    activityLoggingShell: workspaceChrome,
    messages: transport.messages,
    assistantSourceProof: transport.assistantSourceProof,
    pushActivity,
  });

  useEffect(() => {
    if (!savedChatShell) return;
    try {
      const raw = window.localStorage.getItem(ACTIVITY_LS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as unknown;
      if (!Array.isArray(parsed)) return;
      const rows: SpiritActivityEvent[] = [];
      for (const x of parsed) {
        if (!x || typeof x !== "object") continue;
        const o = x as Record<string, unknown>;
        if (typeof o.id !== "string" || typeof o.label !== "string") continue;
        if (typeof o.at !== "number") continue;
        if (
          o.kind !== "message_submitted" &&
          o.kind !== "assistant_finished" &&
          o.kind !== "mode_changed" &&
          o.kind !== "voice_played" &&
          o.kind !== "voice_error" &&
          o.kind !== "workflow_step" &&
          o.kind !== "copy_feedback"
        ) {
          continue;
        }
        rows.push({
          id: o.id,
          at: o.at,
          kind: o.kind,
          label: o.label,
        });
      }
      if (rows.length) setWorkspaceActivity(rows.slice(-20));
    } catch {
      /* ignore */
    }
  }, [savedChatShell]);

  const activitySearchLine = useMemo(() => {
    const base =
      modeRt.activeModelProfileId === "researcher"
        ? transport.webSearchOptOut
          ? "Researcher web search: off (toggle below)"
          : "Researcher web search: on by default"
        : modeRt.activeModelProfileId === "teacher"
          ? transport.teacherWebSearchEnabled
            ? "Teacher web aids: on (auto for educational prompts)"
            : "Teacher web aids: off for this thread"
          : "Web search applies in Researcher / Teacher modes";
    if (transport.lastSearchStatus === "none" && !transport.lastWebSearchHeader) {
      return `${base}. No /api/spirit response in this thread yet.`;
    }
    const bits = [
      `status: ${transport.lastSearchStatus}`,
      transport.lastSearchProvider ? `provider: ${transport.lastSearchProvider}` : null,
      transport.lastHeaderSourceCount != null ? `sources: ${transport.lastHeaderSourceCount}` : null,
      transport.lastSearchElapsedMs != null ? `elapsed: ${transport.lastSearchElapsedMs}ms` : null,
      transport.lastSearchQuery ? `query: ${transport.lastSearchQuery.slice(0, 120)}` : null,
    ].filter(Boolean);
    return `${base}. Last run - ${bits.join(" · ")}`;
  }, [
    modeRt.activeModelProfileId,
    transport.webSearchOptOut,
    transport.teacherWebSearchEnabled,
    transport.lastSearchStatus,
    transport.lastWebSearchHeader,
    transport.lastSearchProvider,
    transport.lastHeaderSourceCount,
    transport.lastSearchElapsedMs,
    transport.lastSearchQuery,
  ]);

  const webSearchDiagnosticLines = useMemo(() => {
    const lines: string[] = [
      `Web search (Researcher): ${transport.webSearchOptOut ? "disabled" : "enabled"}`,
      `Teacher web aids: ${transport.teacherWebSearchEnabled ? "enabled" : "disabled"}`,
      `Provider (last): ${transport.lastSearchProvider ?? "-"}`,
      `Last status: ${transport.lastSearchStatus}`,
      `Last sources: ${transport.lastHeaderSourceCount ?? "-"}`,
      `Last elapsed: ${transport.lastSearchElapsedMs != null ? `${transport.lastSearchElapsedMs}ms` : "-"}`,
      `Last query: ${transport.lastSearchQuery ? transport.lastSearchQuery.slice(0, 160) : "-"}`,
    ];
    if (transport.lastSearchStatus === "failed" && transport.lastSearchSkipReason === "missing_openai_key") {
      lines.push("Hint: OpenAI key missing or web search disabled in env.");
    }
    return lines;
  }, [
    transport.webSearchOptOut,
    transport.teacherWebSearchEnabled,
    transport.lastSearchProvider,
    transport.lastSearchStatus,
    transport.lastHeaderSourceCount,
    transport.lastSearchElapsedMs,
    transport.lastSearchQuery,
    transport.lastSearchSkipReason,
  ]);
  const activityVoiceLine = voiceRt.activityVoiceLine;

  const prevModeRef = useRef<ModelProfileId | null>(null);
  useEffect(() => {
    const modeTrackingOn = savedChatShell || runtimeSurfaceProp === "oracle";
    if (!modeTrackingOn) return;
    const cur = modeRt.activeModelProfileId;
    if (prevModeRef.current === null) {
      prevModeRef.current = cur;
      return;
    }
    if (prevModeRef.current !== cur) {
      const label = getModelProfile(cur).shortLabel;
      pushActivity({
        kind: "mode_changed",
        label: `Mode switched to ${label}`,
      });
      setModeToast(`Mode switched to ${label}`);
      window.setTimeout(() => setModeToast(null), 3200);
      prevModeRef.current = cur;
    }
  }, [savedChatShell, runtimeSurfaceProp, modeRt.activeModelProfileId, pushActivity]);

  const lastVoiceErrRef = useRef<string | undefined>(undefined);
  useEffect(() => {
    const voiceActivityOn = savedChatShell || runtimeSurfaceProp === "oracle";
    if (!voiceActivityOn) return;
    const err = tts.state.lastError;
    if (!err || err === lastVoiceErrRef.current) return;
    lastVoiceErrRef.current = err;
    pushActivity({ kind: "voice_error", label: `Voice error: ${err}` });
  }, [savedChatShell, runtimeSurfaceProp, tts.state.lastError, pushActivity]);

  const lastLatSigRef = useRef<string>("");
  useEffect(() => {
    const voiceActivityOn = savedChatShell || runtimeSurfaceProp === "oracle";
    if (!voiceActivityOn || !tts.state.lastLatency) return;
    const sig = JSON.stringify(tts.state.lastLatency);
    if (sig === lastLatSigRef.current) return;
    lastLatSigRef.current = sig;
    const line = formatTtsFriendlyStartSummary(tts.state.lastLatency);
    pushActivity({
      kind: "voice_played",
      label: line.trim() || "Voice playback started",
    });
  }, [savedChatShell, runtimeSurfaceProp, tts.state.lastLatency, pushActivity]);

  const tc = transport;

  const {
    input,
    setInput,
    isBusy,
    onSubmit,
    onKeyDown,
    error,
    researchPlanOpen,
    setResearchPlanOpen,
    researchPlan,
    setResearchPlan,
    deepThinkEnabled,
    setDeepThinkEnabled,
    setWebSearchPreference,
    teacherWebSearchEnabled,
    setTeacherWebSearchEnabled,
    webSearchOptOut,
    lastWebSourcesPayload,
    lastSearchStatus,
    lastSearchProvider,
    lastSearchQuery,
    lastSearchElapsedMs,
    lastSearchKind,
    lastSearchSkipReason,
    lastHeaderSourceCount,
    lastRouteConfidence,
    setWorkflowDismissed,
    setWorkflowStepIdx,
    handleResearchPlanClose,
    handleResearchPlanStart,
    lastSentForPlanRef,
  } = tc;

  const hasDraft = Boolean(tc.input.trim());

  const spiritTransportBanner = useMemo(() => {
    if (!error) return undefined;
    return error instanceof Error ? error.message : String(error);
  }, [error]);

  const oracleVoiceStatus = useMemo(
    () =>
      deriveOracleVoiceStatus({
        inputMode: "hands-free",
        recordingSupported: true,
        requestingMic: false,
        micPermission: "granted",
        isListening: false,
        isTranscribing: false,
        isBusy,
        isPlaying: tts.state.isPlaying,
        queueLength: tts.state.queueLength,
        ttsLastError: tts.state.lastError,
        speechLastError: null,
        spiritTransportError: spiritTransportBanner,
        lastUserStopAtMs: tts.state.lastUserStopAtMs ?? null,
      }),
    [
      isBusy,
      spiritTransportBanner,
      tts.state.isPlaying,
      tts.state.queueLength,
      tts.state.lastError,
      tts.state.lastUserStopAtMs,
    ],
  );

  const oracleVoiceBackendLabel = useMemo(() => {
    const p = tts.state.lastLatency?.provider;
    if (p) return p;
    if (tts.state.voicesSource) return tts.state.voicesSource;
    return "/api/tts";
  }, [tts.state.lastLatency?.provider, tts.state.voicesSource]);

  const oracleSelectedVoiceLabel = useMemo(() => {
    return (
      tts.state.elevenLabsVoiceName?.trim() ||
      tts.state.elevenLabsVoiceId?.trim() ||
      "System default"
    );
  }, [tts.state.elevenLabsVoiceName, tts.state.elevenLabsVoiceId]);

  const predictedRoute = useMemo(
    () =>
      decideSpiritRoute({
        modelProfileId: modeRt.activeModelProfileId,
        lastUserText: tc.lastOutboundUserSnapshot,
        deepThinkEnabled: tc.deepThinkEnabled,
        webSearchOptOut: tc.webSearchOptOut,
        teacherWebSearchEnabled: tc.teacherWebSearchEnabled,
        webSearchGloballyEnabled: true,
        modelHint: "",
      }),
    [
      modeRt.activeModelProfileId,
      tc.lastOutboundUserSnapshot,
      tc.deepThinkEnabled,
      tc.webSearchOptOut,
      tc.teacherWebSearchEnabled,
    ],
  );

  const laneForVisualizer: SpiritRouteLane =
    tc.researchPlanOpen && modeRt.activeModelProfileId === "researcher"
      ? "research-plan"
      : (tc.isBusy ? predictedRoute.lane : null) ?? tc.lastRouteLane ?? "local-chat";

  const vizSteps = useMemo(
    () =>
      workflowStepsFromServerDecision(
        { lane: laneForVisualizer },
        {
          modelProfileId: modeRt.activeModelProfileId,
          deepThink: tc.deepThinkEnabled,
          busy: tc.isBusy || (tc.researchPlanOpen && modeRt.activeModelProfileId === "researcher"),
          tick: tc.workflowStepIdx,
        },
      ),
    [
      laneForVisualizer,
      tc.researchPlanOpen,
      modeRt.activeModelProfileId,
      tc.deepThinkEnabled,
      tc.isBusy,
      tc.workflowStepIdx,
    ],
  );

  const hasVerifiedSources = Boolean(
    tc.lastWebSourcesPayload?.sources?.some((s) => /^https?:\/\//i.test(s.url?.trim() ?? "")),
  );
  const hasSources = hasVerifiedSources;
  const researcherWebActive =
    modeRt.activeModelProfileId === "researcher" && !tc.webSearchOptOut;

  const workflowVisibleCore =
    workspaceChrome &&
    (tc.isBusy ||
      tc.deepThinkEnabled ||
      (researcherWebActive &&
        (tc.isBusy || hasSources || tc.lastWebSearchHeader != null)) ||
      tc.lastRouteLane === "openai-web-search" ||
      tc.lastRouteLane === "research-plan" ||
      tc.researchPlanOpen ||
      hasSources ||
      activityOpen ||
      (modeRt.activeModelProfileId === "teacher" &&
        tc.teacherWebSearchEnabled &&
        wantsTeacherWebStudyAids(tc.lastOutboundUserSnapshot || "")));

  const casualModes =
    modeRt.activeModelProfileId === "normal-peer" ||
    modeRt.activeModelProfileId === "sassy-chaotic" ||
    modeRt.activeModelProfileId === "brutal";
  const casualPeerLike =
    !tc.isBusy &&
    casualModes &&
    isLikelyCasualShortMessage(tc.lastOutboundUserSnapshot || "hi");

  const workflowExpandedVisible =
    workflowVisibleCore &&
    (!tc.workflowDismissed || tc.isBusy || activityOpen) &&
    !(tc.workflowDismissed && casualPeerLike && !activityOpen);

  const workflowCompactOnly =
    savedChatShell &&
    !tc.isBusy &&
    casualPeerLike &&
    tc.workflowDismissed &&
    !activityOpen &&
    workflowVisibleCore;

  const workflowVisible = workflowExpandedVisible || workflowCompactOnly;

  useEffect(() => {
    if (!tc.isBusy) {
      setWorkflowStepIdx(0);
      return;
    }
    setWorkflowStepIdx(0);
    let i = 0;
    const id = window.setInterval(() => {
      i = Math.min(i + 1, Math.max(vizSteps.length - 1, 0));
      setWorkflowStepIdx(i);
    }, 850);
    return () => window.clearInterval(id);
  }, [tc.isBusy, vizSteps.length, setWorkflowStepIdx]);

  const loggedTextareaGateRef = useRef(false);
  useEffect(() => {
    if (process.env.NODE_ENV !== "development" || !savedChatShell) return;
    if (!tc.isBusy) {
      loggedTextareaGateRef.current = false;
      return;
    }
    if (loggedTextareaGateRef.current) return;
    loggedTextareaGateRef.current = true;
    console.info("[spirit-chat] textarea disabled (streaming)", {
      isBusy: tc.isBusy,
      persistence,
      canSendOutbound: persistent.canSendOutbound,
      activeThreadId: persistent.activeThreadId,
      threadsLoading: persistent.threadsLoading,
      draftLaneActive: persistent.draftLaneActive,
      status: tc.status,
    });
  }, [
    savedChatShell,
    tc.isBusy,
    persistence,
    persistent.canSendOutbound,
    persistent.activeThreadId,
    persistent.threadsLoading,
    persistent.draftLaneActive,
    tc.status,
  ]);

  const displayMessages = useMemo(
    () => dedupeUIMessagesById(tc.messages),
    [tc.messages],
  );

  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const onScroll = () => {
      shouldStickToBottomRef.current = isNearBottom(el);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const run = () => {
      const el = scrollContainerRef.current;
      const end = messagesEndRef.current;
      if (!el || !end) return;
      if (!forceScrollOnNextMessageRef.current && !shouldStickToBottomRef.current) return;
      // ── iOS Safari: scrollIntoView on the sentinel walks ancestors and scrolls the *page*,
      // yanking the workspace when the keyboard opens. Only mutate the message list scroller.
      const useSmooth = forceScrollOnNextMessageRef.current;
      if (useSmooth) {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
      } else {
        el.scrollTop = el.scrollHeight;
      }
      if (forceScrollOnNextMessageRef.current) {
        forceScrollOnNextMessageRef.current = false;
      }
      requestAnimationFrame(() => {
        const c = scrollContainerRef.current;
        if (c) shouldStickToBottomRef.current = isNearBottom(c);
      });
    };
    const id = requestAnimationFrame(run);
    return () => cancelAnimationFrame(id);
  }, [displayMessages, tc.isBusy, tc.status]);

  const sidebarLocked = tc.isBusy;
  const muteNewChatButton =
    sidebarLocked ||
    (Boolean(persistent.draftLaneActive) && tc.messages.length === 0);

  const list = useMemo(
    () =>
      displayMessages.map((m) => {
        const last = displayMessages[displayMessages.length - 1];
        const streamingLatest =
          tc.isBusy &&
          m.role === "assistant" &&
          last?.role === "assistant" &&
          m.id === last.id;
        const rawBody = textFromParts(m);
        const stripFakeResearch =
          m.role === "assistant" &&
          tc.assistantSourceProof?.messageId === m.id &&
          tc.assistantSourceProof.profileId === "researcher" &&
          !tc.assistantSourceProof.hadVerifiedUrls;
        let speakAssistBody = rawBody;
        if (m.role === "assistant") {
          speakAssistBody = sanitizeAssistantVisibleText(rawBody);
          if (stripFakeResearch) {
            speakAssistBody = stripFakeCitationsWhenNoSources(speakAssistBody);
          }
        }
        const longAssist =
          workspaceChrome &&
          m.role === "assistant" &&
          speakAssistBody.length > TTS_SUMMARY_TRIGGER_CHARS;
        return (
          <SpiritMessage
            key={m.id}
            message={m}
            stripFakeResearchCitations={stripFakeResearch}
            webSourcesSnapshot={
              m.role === "assistant" &&
              tc.assistantSourceProof?.messageId === m.id &&
              tc.assistantSourceProof.hadVerifiedUrls
                ? (tc.assistantSourceProof.webSources ?? null)
                : null
            }
            isBusy={tc.isBusy}
            isStreamingLatest={Boolean(streamingLatest)}
            canRegenerate={
              m.role === "assistant" && m.id === tc.lastAssistantId
            }
            onDelete={() => tc.handleMessageDelete(m.id)}
            onEditSave={
              m.role === "user"
                ? (text) => tc.handleMessageEditSave(m.id, text)
                : undefined
            }
            onRegenerate={
              m.role === "assistant"
                ? () => void tc.handleRegenerateAssistant(m.id)
                : undefined
            }
            onSpeak={
              workspaceChrome
                ? async () => {
                    const ok = await voiceRt.tts.ensureAudioUnlocked();
                    if (!ok) return;
                    if (m.role === "assistant") {
                      await voiceRt.speakAssistantText(speakAssistBody, "summary");
                    } else {
                      voiceRt.tts.speak(rawBody, { interrupt: true });
                    }
                  }
                : undefined
            }
            onSpeakFullChunks={
              workspaceChrome && m.role === "assistant" && longAssist
                ? async () => {
                    await voiceRt.speakAssistantText(speakAssistBody, "full-chunks");
                  }
                : undefined
            }
            assistantLongVoice={Boolean(longAssist)}
            onCopyFeedback={(ok) => {
              if (!workspaceChrome) return;
              pushActivity({
                kind: "copy_feedback",
                label: ok ? "Copied message" : "Copy unavailable in this context",
              });
            }}
            speakDisabled={workspaceChrome ? !voiceRt.tts.state.isEnabled : false}
            actionDisabled={tc.isBusy}
            useActionSheetBelowLg={savedChatShell}
          />
        );
      }),
    [
      displayMessages,
      tc,
      voiceRt,
      workspaceChrome,
      savedChatShell,
      pushActivity,
    ],
  );

  const onSidebarNewChat = useCallback(() => {
    if (sidebarLocked) return;
    if (persistent.draftLaneActive && tc.messages.length === 0) return;
    transport.onSidebarNewChatResetHydration();
    tc.setMessages([]);
    mobileThreadDrawer?.onOpenChange(false);
    persistent.beginNewDraftChat();
  }, [persistent, sidebarLocked, tc, transport, mobileThreadDrawer]);

  const onSidebarSelect = useCallback(
    (id: string) => {
      const busy = tc.status === "submitted" || tc.status === "streaming";
      if (busy) tc.stop();
      transport.onSidebarSelectResetHydration();
      tc.setMessages([]);
      persistent.selectPersistedThread(id);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- transport subset; tc wholesale rerenders callbacks constantly
    [persistent, tc.setMessages, tc.stop, tc.status, transport],
  );

  const onSidebarRename = useCallback(
    (id: string) => {
      if (sidebarLocked) return;
      const row = persistent.visibleThreads.find((t) => t.id === id);
      const next = window.prompt("Rename thread", row?.title ?? "New chat");
      if (next === null) return;
      const trimmed = next.trim();
      if (!trimmed) return;
      void persistent.renameThread(id, trimmed);
    },
    [persistent, sidebarLocked],
  );

  const onSidebarDelete = useCallback(
    (id: string) => {
      if (sidebarLocked) return;
      if (
        !window.confirm(
          "Delete this thread and its locally saved messages? This cannot be undone.",
        )
      ) {
        return;
      }
      void persistent.deleteThread(id);
    },
    [persistent, sidebarLocked],
  );

  const onSidebarCreateFolder = useCallback(
    async (name: string): Promise<boolean> => {
      if (sidebarLocked) return false;
      return persistent.createFolder(name);
    },
    [persistent, sidebarLocked],
  );

  const onSidebarRenameFolder = useCallback(
    async (id: string) => {
      if (sidebarLocked) return;
      const row = persistent.folders.find((f) => f.id === id);
      const next = window.prompt("Rename folder", row?.name ?? "Folder");
      if (next === null) return;
      const trimmed = next.trim();
      if (!trimmed) return;
      const ok = await persistent.renameFolder(id, trimmed);
      if (!ok) window.alert("Folder already exists");
    },
    [persistent, sidebarLocked],
  );

  const onSidebarDeleteFolder = useCallback(
    (id: string) => {
      if (sidebarLocked) return;
      void persistent.deleteFolder(id);
    },
    [persistent, sidebarLocked],
  );

  const onSidebarToggleFolderCollapsed = useCallback(
    (id: string) => {
      if (sidebarLocked) return;
      void persistent.toggleFolderCollapsed(id);
    },
    [persistent, sidebarLocked],
  );

  const onSidebarMoveThread = useCallback(
    (threadId: string, folderId: string | null) => {
      if (sidebarLocked) return;
      void persistent.moveThreadToFolder(threadId, folderId);
    },
    [persistent, sidebarLocked],
  );

  const onSidebarTogglePin = useCallback(
    (threadId: string) => {
      if (sidebarLocked) return;
      const row = persistent.visibleThreads.find((t) => t.id === threadId);
      if (row?.pinned) void persistent.unpinThread(threadId);
      else void persistent.pinThread(threadId);
    },
    [persistent, sidebarLocked],
  );

  const activeThreadRow = useMemo(() => {
    if (!persistent.activeThreadId) return undefined;
    return persistent.visibleThreads.find((t) => t.id === persistent.activeThreadId);
  }, [persistent.activeThreadId, persistent.visibleThreads]);

  // ── Empty state: calm GPT-style center — no terminal cosplay, no fake affordances ──
  const defaultEmpty = (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="w-full max-w-md px-2 text-center sm:max-w-lg"
    >
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-chalk/40">
        New chat
      </p>
      <h2 className="mt-3 font-sans text-xl font-medium tracking-tight text-chalk/95 sm:mt-4 sm:text-2xl">
        What would you like to explore?
      </h2>
      <p className="mt-2 text-[15px] leading-relaxed text-chalk/48 sm:text-base sm:leading-relaxed">
        Messages stay in this thread. Use the composer below when you are ready.
      </p>
    </motion.div>
  );

  const header =
    variant === "standalone" &&
    ((title ?? subtitle ?? showPersistedThreads) || oracleVoiceSurface) ? (
      <header className="shrink-0 border-b border-[color:var(--spirit-border)] px-3 py-2.5 backdrop-blur-xl sm:px-6 sm:py-3">
        <div className="flex items-start gap-2 sm:items-center">
          {showPersistedThreads ? (
            <button
              type="button"
              className="mt-0.5 inline-flex shrink-0 touch-manipulation items-center gap-1.5 rounded-lg border border-[color:var(--spirit-border)] bg-white/[0.04] px-2.5 py-2 font-mono text-[10px] font-semibold uppercase tracking-wider text-chalk/80 lg:hidden"
              onClick={() => mobileThreadDrawer?.onOpenChange(true)}
            >
              Threads
            </button>
          ) : null}
          <div className="min-w-0 flex-1">
            {title ? (
              <h1 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-cyan">
                {title}
              </h1>
            ) : null}
            {subtitle ? (
              <p className="mt-1 font-mono text-[10px] text-chalk/50">{subtitle}</p>
            ) : null}
            {oracleVoiceSurface ? (
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-emerald-500/35 bg-emerald-500/[0.08] px-2 py-0.5 font-mono text-[9px] font-semibold uppercase tracking-wider text-emerald-300/95">
                  Oracle Voice
                </span>
                <Link
                  href="/oracle"
                  className="min-h-[44px] min-w-[44px] font-mono text-[10px] leading-none text-[color:var(--spirit-accent-strong)] underline underline-offset-4 hover:brightness-110 sm:min-h-0 sm:min-w-0 sm:py-1"
                >
                  Open Oracle
                </Link>
              </div>
            ) : null}
          </div>
        </div>
      </header>
    ) : null;

  const vizSourceCards =
    lastWebSourcesPayload?.sources
      ?.filter((s) => /^https?:\/\//i.test(s.url?.trim() ?? ""))
      .map((s) => ({
        title: s.title,
        url: s.url,
        snippet: s.snippet,
      })) ?? [];

  const completedWorkflowSummary = useMemo(() => {
    if (lastSearchStatus === "used") {
      const n =
        lastWebSourcesPayload?.sources?.filter((s) =>
          /^https?:\/\//i.test(s.url?.trim() ?? ""),
        ).length ?? lastHeaderSourceCount ?? 0;
      return `Search complete - ${n} source${n === 1 ? "" : "s"}`;
    }
    if (lastSearchStatus === "skipped" || lastSearchStatus === "disabled") {
      return `Search skipped${lastSearchSkipReason ? `: ${lastSearchSkipReason}` : ""}`;
    }
    if (lastSearchStatus === "failed") {
      return `Search failed${lastSearchSkipReason ? `: ${lastSearchSkipReason}` : ""}`;
    }
    if (hasVerifiedSources) {
      return `Sources ready - ${lastWebSourcesPayload?.count ?? lastHeaderSourceCount ?? 0} links`;
    }
    return "Local answer complete";
  }, [
    lastSearchStatus,
    hasVerifiedSources,
    lastWebSourcesPayload,
    lastHeaderSourceCount,
    lastSearchSkipReason,
  ]);

  const scrollAndForm = (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <div
        ref={scrollContainerRef}
        className={cn(
          "scrollbar-hide relative z-0 flex min-h-0 flex-1 flex-col overflow-y-auto overflow-x-hidden px-2 py-2 sm:px-5 sm:py-4",
          variant === "workspace"
            ? "overscroll-y-contain pb-4 sm:pb-5 lg:pb-8"
            : "overscroll-y-contain pb-[calc(5rem+env(safe-area-inset-bottom,0px))] sm:pb-20 lg:pb-8",
        )}
      >
        {savedChatShell &&
        persistent.messagesLoading &&
        !persistent.draftLaneActive &&
        persistent.activeThreadId &&
        displayMessages.length === 0 ? (
          <p
            data-testid="thread-loading-placeholder"
            className="mx-auto max-w-3xl px-3 py-2 text-center font-mono text-[11px] text-chalk/50"
          >
            Loading thread…
          </p>
        ) : null}
        {displayMessages.length === 0 && !(savedChatShell && persistent.messagesLoading) ? (
          <div className="flex min-h-[min(36dvh,260px)] flex-1 flex-col items-center justify-center px-3 py-8 sm:min-h-[min(42dvh,340px)] sm:py-12">
            {emptyState ?? defaultEmpty}
          </div>
        ) : null}
        {displayMessages.length > 0 ? (
          <div className="mx-auto flex w-full max-w-[52rem] flex-col gap-3 sm:gap-5">{list}</div>
        ) : null}
        {error ? (
          <div
            className="mx-1 flex gap-2 border-l-2 border-l-[color:var(--color-rose)]/70 py-2 pl-3 sm:mx-2"
            role="alert"
          >
            <span
              aria-hidden
              className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[color:color-mix(in_oklab,var(--color-rose)_75%,transparent)] shadow-[0_0_12px_color-mix(in_oklab,var(--color-rose)_50%,transparent)]"
            />
            <p className="font-mono text-sm leading-snug text-[color:color-mix(in_oklab,var(--color-rose)_80%,transparent)]">
              Spirit backend error. Check Ollama or /api/spirit.
            </p>
          </div>
        ) : null}
        <div ref={messagesEndRef} className="h-px w-full shrink-0 scroll-mt-4" aria-hidden />
      </div>
      <SpiritWorkflowVisualizer
        visible={Boolean(workflowVisible)}
        compact={Boolean(workflowCompactOnly)}
        completedSummary={completedWorkflowSummary}
        onExpand={() => setWorkflowDismissed(false)}
        busy={isBusy}
        lane={laneForVisualizer}
        confidence={lastRouteConfidence ?? undefined}
        provider={lastSearchProvider ?? lastWebSourcesPayload?.provider ?? undefined}
        searchStatus={lastSearchStatus}
        searchKind={lastSearchKind}
        searchQuery={lastSearchQuery ?? undefined}
        searchElapsedMs={lastSearchElapsedMs ?? undefined}
        skipReason={lastSearchSkipReason ?? undefined}
        searchUsed={lastSearchStatus === "used"}
        sourceCount={lastWebSourcesPayload?.count ?? lastHeaderSourceCount ?? undefined}
        sources={vizSourceCards}
        steps={vizSteps}
        onDismiss={() => setWorkflowDismissed(true)}
      />
      <ResearchPlanPanel
        open={researchPlanOpen}
        plan={researchPlan}
        onClose={handleResearchPlanClose}
        onPlanChange={setResearchPlan}
        onStartResearch={handleResearchPlanStart}
      />
      <div
        data-testid="spirit-composer-dock"
        onFocusCapture={() => {
          if (workspaceChrome) workspaceMobileChrome?.setComposerFocused(true);
        }}
        onBlurCapture={(e) => {
          if (!workspaceChrome || !workspaceMobileChrome) return;
          const rt = e.relatedTarget;
          if (rt && e.currentTarget.contains(rt as Node)) return;
          workspaceMobileChrome.setComposerFocused(false);
        }}
        className={cn(
          "shrink-0 border-t border-[color:color-mix(in_oklab,var(--spirit-border)_65%,transparent)]",
          "bg-[color:color-mix(in_oklab,var(--spirit-bg)_92%,transparent)] backdrop-blur-2xl",
          "lg:bg-[color:color-mix(in_oklab,var(--spirit-bg)_76%,transparent)]",
        )}
      >
        <form
          onSubmit={onSubmit}
          className={cn(
            "px-3 py-2 sm:px-5 sm:py-3.5",
            variant !== "workspace" && "pb-[calc(0.35rem+env(safe-area-inset-bottom,0px))]",
            "lg:px-6 lg:pb-4 lg:pt-4",
          )}
        >
          <div
            className={cn(
              "mx-auto flex max-w-3xl items-end gap-2",
              "lg:rounded-[1.35rem] lg:border lg:border-[color:color-mix(in_oklab,var(--spirit-border)_80%,transparent)] lg:bg-white/[0.035] lg:px-3 lg:py-2.5 lg:backdrop-blur-2xl",
              "lg:shadow-[0_12px_48px_-28px_rgba(0,0,0,0.45),inset_0_0_0_1px_rgba(255,255,255,0.04)]",
            )}
          >
            <textarea
              ref={composerTextareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              onFocus={() => {
                requestAnimationFrame(() => {
                  if (workspaceChrome) {
                    window.scrollTo(0, 0);
                    document.documentElement.scrollTop = 0;
                    document.body.scrollTop = 0;
                    return;
                  }
                  composerTextareaRef.current?.scrollIntoView({
                    block: "nearest",
                    inline: "nearest",
                  });
                });
              }}
              placeholder={
                researchPlanOpen && modeRt.activeModelProfileId === "researcher"
                  ? "Research plan open - use Start research below…"
                  : "Ask Spirit anything…"
              }
              rows={1}
              aria-label="Message"
              disabled={
                isBusy ||
                (researchPlanOpen && modeRt.activeModelProfileId === "researcher")
              }
              className={cn(
                "scrollbar-hide flex-1 resize-none overflow-y-auto text-chalk transition-[height] duration-150 ease-out",
                "max-lg:min-h-[44px] max-lg:max-h-[120px] max-lg:px-3.5 max-lg:py-2.5 max-lg:text-base max-lg:leading-snug",
                "min-h-[52px] max-h-[10rem] px-5 py-[0.875rem] text-[15px]",
                "placeholder:text-chalk/38 disabled:opacity-50",
                "max-lg:rounded-2xl max-lg:border max-lg:border-[color:color-mix(in_oklab,var(--spirit-border)_75%,transparent)] max-lg:bg-black/35",
                "max-lg:focus:border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_38%,transparent)] max-lg:focus:outline-none max-lg:focus:ring-1 max-lg:focus:ring-[color:color-mix(in_oklab,var(--spirit-accent)_20%,transparent)]",
                "lg:min-h-[44px] lg:max-h-[10rem] lg:rounded-2xl lg:border-transparent lg:bg-transparent lg:px-4 lg:py-3 lg:text-[15px]",
                "lg:focus:border-transparent lg:focus:bg-transparent lg:focus:shadow-none lg:focus:ring-0 lg:focus-visible:outline-none",
              )}
              onInput={(e) => {
                const el = e.currentTarget;
                el.style.height = "auto";
                const cap =
                  typeof window !== "undefined" &&
                  typeof window.matchMedia === "function" &&
                  window.matchMedia("(min-width: 1024px)").matches
                    ? 160
                    : 120;
                el.style.height = `${Math.min(el.scrollHeight, cap)}px`;
              }}
            />
            <button
              type="submit"
              disabled={isBusy || !input.trim()}
              aria-label="Send"
              className={cn(
                "mb-0.5 inline-flex h-10 w-10 shrink-0 touch-manipulation items-center justify-center rounded-full max-lg:h-11 max-lg:w-11",
                "border border-[color:color-mix(in_oklab,var(--spirit-accent)_50%,transparent)]",
                "bg-[color:color-mix(in_oklab,var(--spirit-accent)_22%,transparent)]",
                "text-[color:var(--spirit-accent-strong)] shadow-[0_2px_12px_-4px_var(--spirit-glow)] transition active:scale-[0.96] disabled:cursor-not-allowed disabled:opacity-35 disabled:active:scale-100",
                hasDraft &&
                  !isBusy &&
                  "shadow-[0_0_24px_-4px_var(--spirit-glow)] animate-[pulse_2.8s_ease-in-out_infinite]",
              )}
            >
              <ArrowUp className="h-5 w-5" strokeWidth={2.25} aria-hidden />
            </button>
          </div>
        </form>
        {workspaceChrome ? (
          <div className="mx-auto flex max-w-3xl flex-wrap items-center gap-1.5 px-3 pb-2.5 pt-0 font-mono text-[9px] font-medium uppercase tracking-wide text-chalk/45 sm:gap-2 sm:px-5 sm:text-[10px] lg:px-6">
            {!oracleVoiceSurface ? (
              <button
                type="button"
                aria-pressed={deepThinkEnabled}
                onClick={() => setDeepThinkEnabled((v) => !v)}
                className={cn(
                  "touch-manipulation rounded-full border px-2.5 py-1.5 sm:py-1",
                  deepThinkEnabled
                    ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] text-[color:var(--spirit-accent-strong)]"
                    : "border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)] text-chalk/50",
                )}
              >
                Deep think
              </button>
            ) : null}
            {modeRt.activeModelProfileId === "researcher" ? (
              <button
                type="button"
                aria-pressed={!webSearchOptOut}
                onClick={() =>
                  setWebSearchPreference((p) => (p === "disabled" ? "enabled" : "disabled"))
                }
                className={cn(
                  "touch-manipulation rounded-full border px-2.5 py-1.5 sm:py-1",
                  !webSearchOptOut
                    ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] text-[color:var(--spirit-accent-strong)]"
                    : "border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)] text-chalk/50",
                )}
              >
                Web search {webSearchOptOut ? "off" : "on"}
              </button>
            ) : null}
            {modeRt.activeModelProfileId === "teacher" ? (
              <button
                type="button"
                aria-pressed={teacherWebSearchEnabled}
                onClick={() => setTeacherWebSearchEnabled((v) => !v)}
                className={cn(
                  "touch-manipulation rounded-full border px-2.5 py-1.5 sm:py-1",
                  teacherWebSearchEnabled
                    ? "border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] text-[color:var(--spirit-accent-strong)]"
                    : "border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)] text-chalk/50",
                )}
              >
                Web aids {teacherWebSearchEnabled ? "on" : "off"}
              </button>
            ) : null}
            {savedChatShell &&
            modeRt.activeModelProfileId === "researcher" &&
            deepThinkEnabled &&
            !webSearchOptOut ? (
              <button
                type="button"
                data-testid="research-plan-open-manual"
                onClick={() => {
                  const topic = input.trim() || "Research topic";
                  lastSentForPlanRef.current = topic;
                  setResearchPlan(draftResearchPlanFromPrompt(topic));
                  setResearchPlanOpen(true);
                }}
                className="touch-manipulation rounded-full border border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)] px-2.5 py-1.5 text-chalk/55 sm:py-1"
              >
                Research plan
              </button>
            ) : null}
          </div>
        ) : null}
        {footerHint ? (
          <div className="mx-auto max-w-3xl px-2 pb-2 text-center font-mono text-[10px] text-chalk/45 sm:px-5 lg:px-6">
            {footerHint}
          </div>
        ) : null}
      </div>
    </div>
  );

  if (variant === "embedded") {
    return (
      <div
        className={cn(
          "flex min-h-[55dvh] flex-1 flex-col px-3 pt-3 sm:px-6 sm:pt-4 lg:min-h-0",
          shellClassName,
        )}
      >
        <div className="flex min-h-0 flex-1 flex-col rounded-2xl border border-[color:var(--spirit-border)] bg-white/[0.02] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur-xl">
          {scrollAndForm}
        </div>
      </div>
    );
  }

  if (variant === "workspace") {
    const showThreads = Boolean(
      savedChatShell && showThreadSidebar !== false,
    );

    const threadRailProps = {
      savedThreadCount: persistent.visibleThreads.length,
      rootThreads: threadRt.rootThreads,
      folderSections: threadRt.folderSections,
      allFolders: persistent.folders,
      pinnedThreads: threadRt.pinnedThreadsDisplay,
      onTogglePinThread: onSidebarTogglePin,
      threadSnippets: threadRt.searchSnippets,
      searchQuery: threadRt.searchQuery,
      onSearchQueryChange: threadRt.setSearchQuery,
      searchEmptyResults: threadRt.searchEmptyResults,
      activeThreadId: persistent.activeThreadId,
      draftActive: persistent.draftLaneActive,
      interactionDisabled: sidebarLocked,
      muteNewChatButton,
      onNewChat: onSidebarNewChat,
      onCreateFolder: onSidebarCreateFolder,
      onSelectThread: (id: string) => {
        mobileThreadDrawer?.onOpenChange(false);
        onSidebarSelect(id);
      },
      onRenameThread: onSidebarRename,
      onDeleteThread: onSidebarDelete,
      onMoveThreadToFolder: onSidebarMoveThread,
      onRenameFolder: onSidebarRenameFolder,
      onDeleteFolder: onSidebarDeleteFolder,
      onToggleFolderCollapsed: onSidebarToggleFolderCollapsed,
      onCommitThreadDrag: persistent.commitThreadSidebarOrder,
      onExpandFolderDuringDrag: persistent.expandFolder,
    };

    const threadsButton =
      mobileThreadDrawer != null ? (
        <button
          type="button"
          aria-label={
            mobileThreadDrawer.open ? "Close saved threads" : "Open saved threads"
          }
          aria-expanded={mobileThreadDrawer.open}
          onClick={() => mobileThreadDrawer.onOpenChange(!mobileThreadDrawer.open)}
          className={cn(
            "inline-flex h-9 shrink-0 touch-manipulation items-center justify-center gap-1 rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] px-2 font-mono text-[9px] font-semibold uppercase tracking-wider text-chalk transition hover:bg-white/[0.07]",
            mobileThreadDrawer.open &&
              "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] text-[color:var(--spirit-accent-strong)]",
          )}
        >
          {mobileThreadDrawer.open ? (
            <PanelLeftClose className="h-4 w-4 shrink-0" aria-hidden />
          ) : (
            <PanelLeft className="h-4 w-4 shrink-0" aria-hidden />
          )}
          <span className="max-[360px]:sr-only">Threads</span>
        </button>
      ) : null;

    return (
      <div
        className={cn(
          "relative flex min-h-0 flex-1 flex-col overflow-hidden text-chalk/95",
          shellClassName,
        )}
      >
        <div
          className={cn(
            "relative flex h-full min-h-0 flex-1 flex-col overflow-hidden lg:flex-row lg:rounded-xl lg:border lg:border-[color:var(--spirit-border)] lg:bg-white/[0.02] lg:shadow-[inset_0_0_0_1px_rgba(255,255,255,0.03)] lg:backdrop-blur-xl",
          )}
        >
          {showThreads && isLg ? (
            <ChatThreadSidebar
              {...threadRailProps}
              onDrawerClose={undefined}
              className="relative z-auto h-full w-[280px] shrink-0 translate-x-0 shadow-none"
            />
          ) : null}

          {showThreads && !isLg && mobileThreadDrawer ? (
            <MobileThreadDrawer
              open={mobileThreadDrawer.open}
              onClose={() => mobileThreadDrawer.onOpenChange(false)}
            >
              <ChatThreadSidebar
                {...threadRailProps}
                layoutVariant="drawer"
                mobileDndEnabled
                onDrawerClose={undefined}
              />
            </MobileThreadDrawer>
          ) : null}

          <div
            className={cn(
              "flex min-h-0 min-w-0 flex-1 flex-col",
              showThreads && "lg:border-l lg:border-[color:var(--spirit-border)]",
            )}
          >
            {workspaceChrome && !isLg ? (
              <>
                <MobileChatTopBar
                  threadsSlot={threadsButton}
                  modeSlot={
                    <ModelProfileSelector
                      variant="topBar"
                      value={modeRt.activeModelProfileId}
                      onChange={(id) => {
                        void modeRt.setActiveModelProfile(id);
                      }}
                      disabled={sidebarLocked}
                      compact
                    />
                  }
                  voiceSlot={
                    <VoiceControl
                      variant="mobile-bar"
                      state={tts.state}
                      onToggleEnabled={tts.toggleEnabled}
                      onEnableAudio={tts.ensureAudioUnlocked}
                      onStop={tts.stop}
                      onSpeakLatestAssistant={voiceRt.speakLatestAssistant}
                      onStartDelayChange={tts.setStartDelayMs}
                      onSentenceGapChange={tts.setSentenceGapMs}
                      onVoiceSpeedChange={tts.setVoiceSpeed}
                      onToggleAutoSpeak={tts.toggleAutoSpeakAssistant}
                      onRequestVoiceCatalog={tts.refreshElevenLabsVoices}
                      onElevenLabsVoiceChange={tts.setElevenLabsVoiceFromPicker}
                      disabled={sidebarLocked}
                    />
                  }
                />
                <div className="flex min-w-0 items-center gap-1 border-b border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,transparent)] px-1.5 py-1 backdrop-blur-md">
                  <ChatActiveModeBadge
                    compact
                    className="min-w-0 flex-1"
                    profileId={modeRt.activeModelProfileId}
                  />
                  <button
                    type="button"
                    aria-label="Activity"
                    onClick={() => {
                      setActivityOpen((o) => !o);
                      setProfileOpen(false);
                      setThreadMenuOpen(false);
                    }}
                    className="inline-flex h-10 min-h-[44px] min-w-[44px] shrink-0 touch-manipulation items-center justify-center rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_65%,transparent)] bg-white/[0.035] text-chalk/65 transition hover:bg-white/[0.06]"
                  >
                    <Activity className="h-4 w-4" aria-hidden />
                  </button>
                  <button
                    type="button"
                    aria-label="Spirit profile"
                    onClick={() => {
                      setProfileOpen((o) => !o);
                      setActivityOpen(false);
                      setThreadMenuOpen(false);
                    }}
                    className="inline-flex h-10 min-h-[44px] min-w-[44px] shrink-0 touch-manipulation items-center justify-center rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_65%,transparent)] bg-white/[0.035] text-chalk/65 transition hover:bg-white/[0.06]"
                  >
                    <UserRound className="h-4 w-4" aria-hidden />
                  </button>
                  {!oracleVoiceSurface ? (
                    <button
                      type="button"
                      aria-label="Thread settings"
                      onClick={() => {
                        setThreadMenuOpen((o) => !o);
                        setActivityOpen(false);
                        setProfileOpen(false);
                      }}
                      className="inline-flex h-10 min-h-[44px] min-w-[44px] shrink-0 touch-manipulation items-center justify-center rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-border)_65%,transparent)] bg-white/[0.035] text-chalk/65 transition hover:bg-white/[0.06]"
                    >
                      <SlidersHorizontal className="h-4 w-4" aria-hidden />
                    </button>
                  ) : null}
                </div>
                {modeToast ? (
                  <div className="border-b border-white/[0.06] bg-white/[0.03] px-2 py-1 text-center font-mono text-[10px] text-chalk/65">
                    {modeToast}
                  </div>
                ) : null}
              </>
            ) : null}
            {workspaceChrome && isLg ? (
              <div className="hidden shrink-0 border-b border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_90%,transparent)] backdrop-blur-md sm:px-5 lg:block">
                {modeToast ? (
                  <div className="border-b border-white/[0.06] bg-white/[0.03] px-3 py-1 font-mono text-[10px] text-chalk/65">
                    {modeToast}
                  </div>
                ) : null}
                <div className="flex min-w-0 flex-col gap-2 px-3 py-1.5 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-2 sm:gap-y-1.5">
                  <ChatActiveModeBadge
                    className="w-full max-w-[11rem] shrink-0 sm:w-auto"
                    profileId={modeRt.activeModelProfileId}
                  />
                  <div className="min-w-0 sm:max-w-[min(100%,14rem)]">
                    <ModelProfileSelector
                      value={modeRt.activeModelProfileId}
                      onChange={(id) => {
                        void modeRt.setActiveModelProfile(id);
                      }}
                      disabled={sidebarLocked}
                      compact
                    />
                  </div>
                  <div className="flex shrink-0 items-center gap-1">
                    <button
                      type="button"
                      aria-label="Activity"
                      onClick={() => {
                        setActivityOpen((o) => !o);
                        setProfileOpen(false);
                        setThreadMenuOpen(false);
                      }}
                      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.07]"
                    >
                      <Activity className="h-4 w-4" aria-hidden />
                    </button>
                    <button
                      type="button"
                      aria-label="Spirit profile"
                      onClick={() => {
                        setProfileOpen((o) => !o);
                        setActivityOpen(false);
                        setThreadMenuOpen(false);
                      }}
                      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.07]"
                    >
                      <UserRound className="h-4 w-4" aria-hidden />
                    </button>
                    {!oracleVoiceSurface ? (
                      <button
                        type="button"
                        aria-label="Thread settings"
                        onClick={() => {
                          setThreadMenuOpen((o) => !o);
                          setActivityOpen(false);
                          setProfileOpen(false);
                        }}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.07]"
                      >
                        <SlidersHorizontal className="h-4 w-4" aria-hidden />
                      </button>
                    ) : null}
                  </div>
                  <div className="min-w-0 flex-1 sm:min-w-[12rem] sm:max-w-xl">
                    <VoiceControl
                      state={tts.state}
                      onToggleEnabled={tts.toggleEnabled}
                      onEnableAudio={tts.ensureAudioUnlocked}
                      onStop={tts.stop}
                      onSpeakLatestAssistant={voiceRt.speakLatestAssistant}
                      onStartDelayChange={tts.setStartDelayMs}
                      onSentenceGapChange={tts.setSentenceGapMs}
                      onVoiceSpeedChange={tts.setVoiceSpeed}
                      onToggleAutoSpeak={tts.toggleAutoSpeakAssistant}
                      onRequestVoiceCatalog={tts.refreshElevenLabsVoices}
                      onElevenLabsVoiceChange={tts.setElevenLabsVoiceFromPicker}
                      disabled={sidebarLocked}
                    />
                  </div>
                </div>
              </div>
            ) : null}
            {oracleVoiceSurface && workspaceChrome ? (
              <div className="shrink-0 pt-1">
                <OracleVoiceStatusCard
                  status={oracleVoiceStatus}
                  modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
                  runtimeLabel={getSpiritRuntimeSurfaceDisplayLabel(runtimeSurfaceProp)}
                  voiceProviderLine={oracleVoiceBackendLabel}
                  selectedVoiceLabel={oracleSelectedVoiceLabel}
                  lastPlaybackWallMs={tts.state.lastPlaybackWallMs}
                  lastError={tts.state.lastError}
                  spiritTransportError={spiritTransportBanner}
                />
              </div>
            ) : null}
            {scrollAndForm}
          </div>
        </div>
        <SpiritActivityPanel
          open={activityOpen}
          onClose={() => setActivityOpen(false)}
          variant={isLg ? "popover" : "sheet"}
          modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
          runtimeLabel={getSpiritRuntimeSurfaceDisplayLabel(runtimeSurfaceProp)}
          voiceLabel={activityVoiceLine}
          searchLabel={activitySearchLine}
          memoryLabel="Local profile only"
          researchNote="OpenAI web prefetch via /api/spirit when Researcher web is on"
          webSearchDiagnosticLines={savedChatShell ? webSearchDiagnosticLines : undefined}
          events={workspaceActivity}
        />
        <SpiritUserProfilePanel
          open={profileOpen}
          onClose={() => setProfileOpen(false)}
          variant={isLg ? "popover" : "sheet"}
          activeModelProfileId={modeRt.activeModelProfileId}
        />
        {!oracleVoiceSurface ? (
          <ChatThreadWorkspaceMenu
            open={threadMenuOpen}
            onClose={() => setThreadMenuOpen(false)}
            variant={isLg ? "popover" : "sheet"}
            modelProfileId={modeRt.activeModelProfileId}
            threadTitle={activeThreadRow?.title ?? "Chat"}
            threadId={persistent.draftLaneActive ? null : persistent.activeThreadId}
            draftActive={persistent.draftLaneActive}
            isPinned={Boolean(activeThreadRow?.pinned)}
            folders={persistent.folders}
            folderId={activeThreadRow?.folderId}
            onRename={() => {
              if (persistent.activeThreadId) onSidebarRename(persistent.activeThreadId);
            }}
            onDelete={() => {
              if (persistent.activeThreadId) onSidebarDelete(persistent.activeThreadId);
            }}
            onTogglePin={() => {
              if (persistent.activeThreadId) onSidebarTogglePin(persistent.activeThreadId);
            }}
            onMoveToFolder={(fid) => {
              if (persistent.activeThreadId) {
                void persistent.moveThreadToFolder(persistent.activeThreadId, fid);
              }
            }}
          />
        ) : null}
      </div>
    );
  }

  const standaloneThreadRailProps = {
    savedThreadCount: persistent.visibleThreads.length,
    rootThreads: threadRt.rootThreads,
    folderSections: threadRt.folderSections,
    allFolders: persistent.folders,
    pinnedThreads: threadRt.pinnedThreadsDisplay,
    onTogglePinThread: onSidebarTogglePin,
    threadSnippets: threadRt.searchSnippets,
    searchQuery: threadRt.searchQuery,
    onSearchQueryChange: threadRt.setSearchQuery,
    searchEmptyResults: threadRt.searchEmptyResults,
    activeThreadId: persistent.activeThreadId,
    draftActive: persistent.draftLaneActive,
    interactionDisabled: sidebarLocked,
    muteNewChatButton,
    onNewChat: onSidebarNewChat,
    onCreateFolder: onSidebarCreateFolder,
    onSelectThread: (id: string) => {
      mobileThreadDrawer?.onOpenChange(false);
      onSidebarSelect(id);
    },
    onRenameThread: onSidebarRename,
    onDeleteThread: onSidebarDelete,
    onMoveThreadToFolder: onSidebarMoveThread,
    onRenameFolder: onSidebarRenameFolder,
    onDeleteFolder: onSidebarDeleteFolder,
    onToggleFolderCollapsed: onSidebarToggleFolderCollapsed,
    onCommitThreadDrag: persistent.commitThreadSidebarOrder,
    onExpandFolderDuringDrag: persistent.expandFolder,
  };

  const standaloneThreadsButton =
    mobileThreadDrawer != null ? (
      <button
        type="button"
        aria-label={
          mobileThreadDrawer.open ? "Close saved threads" : "Open saved threads"
        }
        aria-expanded={mobileThreadDrawer.open}
        onClick={() => mobileThreadDrawer.onOpenChange(!mobileThreadDrawer.open)}
        className={cn(
          "inline-flex h-9 shrink-0 touch-manipulation items-center justify-center gap-1 rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] px-2 font-mono text-[9px] font-semibold uppercase tracking-wider text-chalk transition hover:bg-white/[0.07]",
          mobileThreadDrawer.open &&
            "border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] text-[color:var(--spirit-accent-strong)]",
        )}
      >
        {mobileThreadDrawer.open ? (
          <PanelLeftClose className="h-4 w-4 shrink-0" aria-hidden />
        ) : (
          <PanelLeft className="h-4 w-4 shrink-0" aria-hidden />
        )}
        <span className="max-[360px]:sr-only">Threads</span>
      </button>
    ) : null;

  return (
    <div
      className={cn(
        "relative flex h-dvh h-[100dvh] flex-col overflow-hidden bg-[color:var(--spirit-bg)] text-chalk/95",
        shellClassName,
      )}
    >
      {header}
      <div
        className={cn(
          "relative flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row",
          "border-t border-[color:var(--spirit-border)] bg-white/[0.02] backdrop-blur-xl",
        )}
      >
        {showPersistedThreads && isLg ? (
          <ChatThreadSidebar
            {...standaloneThreadRailProps}
            onDrawerClose={undefined}
            className="relative z-auto h-auto min-h-0 max-h-none w-[280px] shrink-0 translate-x-0 shadow-none"
          />
        ) : null}

        {showPersistedThreads && !isLg && mobileThreadDrawer ? (
          <MobileThreadDrawer
            open={mobileThreadDrawer.open}
            onClose={() => mobileThreadDrawer.onOpenChange(false)}
          >
            <ChatThreadSidebar
              {...standaloneThreadRailProps}
              layoutVariant="drawer"
              mobileDndEnabled
              onDrawerClose={undefined}
            />
          </MobileThreadDrawer>
        ) : null}
        <div
          className={cn(
            "flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden",
            showPersistedThreads &&
              "lg:border-l lg:border-[color:var(--spirit-border)]",
          )}
        >
          {workspaceChrome && !isLg ? (
            <>
              <MobileChatTopBar
                threadsSlot={standaloneThreadsButton}
                modeSlot={
                  <ModelProfileSelector
                    variant="topBar"
                    value={modeRt.activeModelProfileId}
                    onChange={(id) => {
                      void modeRt.setActiveModelProfile(id);
                    }}
                    disabled={sidebarLocked}
                    compact
                  />
                }
                voiceSlot={
                  <VoiceControl
                    variant="mobile-bar"
                    state={tts.state}
                    onToggleEnabled={tts.toggleEnabled}
                    onEnableAudio={tts.ensureAudioUnlocked}
                    onStop={tts.stop}
                    onSpeakLatestAssistant={voiceRt.speakLatestAssistant}
                    onStartDelayChange={tts.setStartDelayMs}
                    onSentenceGapChange={tts.setSentenceGapMs}
                    onVoiceSpeedChange={tts.setVoiceSpeed}
                    onToggleAutoSpeak={tts.toggleAutoSpeakAssistant}
                    onRequestVoiceCatalog={tts.refreshElevenLabsVoices}
                    onElevenLabsVoiceChange={tts.setElevenLabsVoiceFromPicker}
                    disabled={sidebarLocked}
                  />
                }
              />
              <div className="flex min-w-0 items-center gap-1 border-b border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_92%,transparent)] px-1.5 py-0.5 backdrop-blur-md">
                <ChatActiveModeBadge
                  compact
                  className="min-w-0 flex-1"
                  profileId={modeRt.activeModelProfileId}
                />
                <button
                  type="button"
                  aria-label="Activity"
                  onClick={() => {
                    setActivityOpen((o) => !o);
                    setProfileOpen(false);
                    setThreadMenuOpen(false);
                  }}
                  className="inline-flex h-11 w-11 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70"
                >
                  <Activity className="h-4 w-4" aria-hidden />
                </button>
                <button
                  type="button"
                  aria-label="Spirit profile"
                  onClick={() => {
                    setProfileOpen((o) => !o);
                    setActivityOpen(false);
                    setThreadMenuOpen(false);
                  }}
                  className="inline-flex h-11 w-11 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70"
                >
                  <UserRound className="h-4 w-4" aria-hidden />
                </button>
                {!oracleVoiceSurface ? (
                  <button
                    type="button"
                    aria-label="Thread settings"
                    onClick={() => {
                      setThreadMenuOpen((o) => !o);
                      setActivityOpen(false);
                      setProfileOpen(false);
                    }}
                    className="inline-flex h-11 w-11 shrink-0 touch-manipulation items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70"
                  >
                    <SlidersHorizontal className="h-4 w-4" aria-hidden />
                  </button>
                ) : null}
              </div>
              {modeToast ? (
                <div className="border-b border-white/[0.06] bg-white/[0.03] px-2 py-1 text-center font-mono text-[10px] text-chalk/65">
                  {modeToast}
                </div>
              ) : null}
            </>
          ) : null}
          {workspaceChrome && isLg ? (
            <div className="hidden shrink-0 border-b border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_90%,transparent)] backdrop-blur-md sm:px-5 lg:block">
              {modeToast ? (
                <div className="border-b border-white/[0.06] bg-white/[0.03] px-3 py-1 font-mono text-[10px] text-chalk/65">
                  {modeToast}
                </div>
              ) : null}
              <div className="flex min-w-0 flex-col gap-2 px-3 py-1.5 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-2 sm:gap-y-1.5">
                <ChatActiveModeBadge
                  className="w-full max-w-[11rem] shrink-0 sm:w-auto"
                  profileId={modeRt.activeModelProfileId}
                />
                <div className="min-w-0 sm:max-w-[min(100%,14rem)]">
                  <ModelProfileSelector
                    value={modeRt.activeModelProfileId}
                    onChange={(id) => {
                      void modeRt.setActiveModelProfile(id);
                    }}
                    disabled={sidebarLocked}
                    compact
                  />
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <button
                    type="button"
                    aria-label="Activity"
                    onClick={() => {
                      setActivityOpen((o) => !o);
                      setProfileOpen(false);
                      setThreadMenuOpen(false);
                    }}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.07]"
                  >
                    <Activity className="h-4 w-4" aria-hidden />
                  </button>
                  <button
                    type="button"
                    aria-label="Spirit profile"
                    onClick={() => {
                      setProfileOpen((o) => !o);
                      setActivityOpen(false);
                      setThreadMenuOpen(false);
                    }}
                    className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.07]"
                  >
                    <UserRound className="h-4 w-4" aria-hidden />
                  </button>
                  {!oracleVoiceSurface ? (
                    <button
                      type="button"
                      aria-label="Thread settings"
                      onClick={() => {
                        setThreadMenuOpen((o) => !o);
                        setActivityOpen(false);
                        setProfileOpen(false);
                      }}
                      className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[color:var(--spirit-border)]/80 bg-white/[0.04] text-chalk/70 transition hover:bg-white/[0.07]"
                    >
                      <SlidersHorizontal className="h-4 w-4" aria-hidden />
                    </button>
                  ) : null}
                </div>
                <div className="min-w-0 flex-1 sm:min-w-[12rem] sm:max-w-xl">
                  <VoiceControl
                    state={tts.state}
                    onToggleEnabled={tts.toggleEnabled}
                    onEnableAudio={tts.ensureAudioUnlocked}
                    onStop={tts.stop}
                    onSpeakLatestAssistant={voiceRt.speakLatestAssistant}
                    onStartDelayChange={tts.setStartDelayMs}
                    onSentenceGapChange={tts.setSentenceGapMs}
                    onVoiceSpeedChange={tts.setVoiceSpeed}
                    onToggleAutoSpeak={tts.toggleAutoSpeakAssistant}
                    onRequestVoiceCatalog={tts.refreshElevenLabsVoices}
                    onElevenLabsVoiceChange={tts.setElevenLabsVoiceFromPicker}
                    disabled={sidebarLocked}
                  />
                </div>
              </div>
            </div>
          ) : null}
          {oracleVoiceSurface && workspaceChrome ? (
            <div className="shrink-0 pt-1">
              <OracleVoiceStatusCard
                status={oracleVoiceStatus}
                modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
                runtimeLabel={getSpiritRuntimeSurfaceDisplayLabel(runtimeSurfaceProp)}
                voiceProviderLine={oracleVoiceBackendLabel}
                selectedVoiceLabel={oracleSelectedVoiceLabel}
                lastPlaybackWallMs={tts.state.lastPlaybackWallMs}
                lastError={tts.state.lastError}
                spiritTransportError={spiritTransportBanner}
              />
            </div>
          ) : null}
          {scrollAndForm}
        </div>
      </div>
      {workspaceChrome ? (
        <>
          <SpiritActivityPanel
            open={activityOpen}
            onClose={() => setActivityOpen(false)}
            variant={isLg ? "popover" : "sheet"}
            modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
            runtimeLabel={getSpiritRuntimeSurfaceDisplayLabel(runtimeSurfaceProp)}
            voiceLabel={activityVoiceLine}
            searchLabel={activitySearchLine}
            memoryLabel="Local profile only"
            researchNote="OpenAI web prefetch via /api/spirit when Researcher web is on"
            webSearchDiagnosticLines={webSearchDiagnosticLines}
            events={workspaceActivity}
          />
          <SpiritUserProfilePanel
            open={profileOpen}
            onClose={() => setProfileOpen(false)}
            variant={isLg ? "popover" : "sheet"}
            activeModelProfileId={modeRt.activeModelProfileId}
          />
          {!oracleVoiceSurface ? (
            <ChatThreadWorkspaceMenu
              open={threadMenuOpen}
              onClose={() => setThreadMenuOpen(false)}
              variant={isLg ? "popover" : "sheet"}
              modelProfileId={modeRt.activeModelProfileId}
              threadTitle={activeThreadRow?.title ?? "Chat"}
              threadId={persistent.draftLaneActive ? null : persistent.activeThreadId}
              draftActive={persistent.draftLaneActive}
              isPinned={Boolean(activeThreadRow?.pinned)}
              folders={persistent.folders}
              folderId={activeThreadRow?.folderId}
              onRename={() => {
                if (persistent.activeThreadId) onSidebarRename(persistent.activeThreadId);
              }}
              onDelete={() => {
                if (persistent.activeThreadId) onSidebarDelete(persistent.activeThreadId);
              }}
              onTogglePin={() => {
                if (persistent.activeThreadId) onSidebarTogglePin(persistent.activeThreadId);
              }}
              onMoveToFolder={(fid) => {
                if (persistent.activeThreadId) {
                  void persistent.moveThreadToFolder(persistent.activeThreadId, fid);
                }
              }}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
});

export const SpiritChat = memo(function SpiritChat(props: SpiritChatProps) {
  return (
    <ClientFailSafe label="spirit-chat">
      <SpiritChatInner {...props} />
    </ClientFailSafe>
  );
});

# Increment 2.3 - Coding status surface

Date: 2026-05-29T19:57:38-04:00

```text
src/components/chat/SpiritUserProfilePanel.tsx:import { getModelProfile, MODEL_PROFILE_ORDER, MODEL_PROFILES } from "@/lib/spirit/model-profiles";
src/components/chat/SpiritUserProfilePanel.tsx:import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
src/components/chat/SpiritUserProfilePanel.tsx:  activeModelProfileId?: ModelProfileId;
src/components/chat/SpiritUserProfilePanel.tsx:  activeModelProfileId = "normal-peer",
src/components/chat/SpiritUserProfilePanel.tsx:  const modeAwareSummary = buildModeAwarePersonalizationSummary(profile, activeModelProfileId);
src/components/chat/SpiritUserProfilePanel.tsx:  const mode = getModelProfile(activeModelProfileId);
src/components/chat/ChatActiveModeBadge.tsx:import { getModelProfile } from "@/lib/spirit/model-profiles";
src/components/chat/ChatActiveModeBadge.tsx:import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
src/components/chat/ChatActiveModeBadge.tsx:  profileId: ModelProfileId;
src/components/chat/ChatActiveModeBadge.tsx:  const p = getModelProfile(profileId);
src/components/chat/ModelProfileSelector.tsx:// ── ModelProfileSelector - Prompt 7 persona strip (Spirit chalk / cyan) ───────
src/components/chat/ModelProfileSelector.tsx:import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
src/components/chat/ModelProfileSelector.tsx:export type ModelProfileSelectorProps = {
src/components/chat/ModelProfileSelector.tsx:  value: ModelProfileId;
src/components/chat/ModelProfileSelector.tsx:  onChange: (profileId: ModelProfileId) => void;
src/components/chat/ModelProfileSelector.tsx:export const ModelProfileSelector = memo(function ModelProfileSelector({
src/components/chat/ModelProfileSelector.tsx:}: ModelProfileSelectorProps) {
src/components/chat/ModelProfileSelector.tsx:        aria-label="Model profile"
src/components/chat/ModelProfileSelector.tsx:        onChange={(e) => onChange(e.target.value as ModelProfileId)}
src/components/chat/ChatSidebarDndProvider.tsx:// ── ChatSidebarDndProvider - @dnd-kit shell; drawer uses longer touch delay (9F) ─
src/components/chat/ChatSidebarDndProvider.tsx:export type ChatSidebarDndProviderProps = {
src/components/chat/ChatSidebarDndProvider.tsx:export const ChatSidebarDndProvider = memo(function ChatSidebarDndProvider({
src/components/chat/ChatSidebarDndProvider.tsx:}: ChatSidebarDndProviderProps) {
src/components/chat/ChatThreadSidebar.tsx:import { ChatSidebarDndProvider } from "@/components/chat/ChatSidebarDndProvider";
src/components/chat/ChatThreadSidebar.tsx:import { buildMoveSelectModel } from "@/lib/chat-folder-utils";
src/components/chat/ChatThreadSidebar.tsx:      const moveModel = buildMoveSelectModel(thread, allFolders);
src/components/chat/ChatThreadSidebar.tsx:          moveSelect={moveModel.show ? moveModel : null}
src/components/chat/ChatThreadSidebar.tsx:                moveSelect={moveModel.show ? moveModel : null}
src/components/chat/ChatThreadSidebar.tsx:                    const moveModel = buildMoveSelectModel(thread, allFolders);
src/components/chat/ChatThreadSidebar.tsx:                            moveSelect={moveModel.show ? moveModel : null}
src/components/chat/ChatThreadSidebar.tsx:                  const moveModel = buildMoveSelectModel(thread, allFolders);
src/components/chat/ChatThreadSidebar.tsx:                      moveSelect={moveModel.show ? moveModel : null}
src/components/chat/ChatThreadSidebar.tsx:        <ChatSidebarDndProvider
src/components/chat/ChatThreadSidebar.tsx:        </ChatSidebarDndProvider>
src/components/chat/ChatFolderSection.tsx:import { buildMoveSelectModel } from "@/lib/chat-folder-utils";
src/components/chat/ChatFolderSection.tsx:    const moveModel = buildMoveSelectModel(thread, allFolders);
src/components/chat/ChatFolderSection.tsx:        moveSelect={moveModel.show ? moveModel : null}
src/components/chat/ChatFolderSection.tsx:    const moveModel = buildMoveSelectModel(thread, allFolders);
src/components/chat/ChatFolderSection.tsx:            moveSelect={moveModel.show ? moveModel : null}
src/components/chat/ChatThreadWorkspaceMenu.tsx:import { getModelProfile } from "@/lib/spirit/model-profiles";
src/components/chat/ChatThreadWorkspaceMenu.tsx:import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
src/components/chat/ChatThreadWorkspaceMenu.tsx:  modelProfileId: ModelProfileId;
src/components/chat/ChatThreadWorkspaceMenu.tsx:  const mode = getModelProfile(modelProfileId);
src/components/chat/__tests__/ModelProfileSelector.test.tsx:import { ModelProfileSelector } from "@/components/chat/ModelProfileSelector";
src/components/chat/__tests__/ModelProfileSelector.test.tsx:describe("ModelProfileSelector", () => {
src/components/chat/__tests__/ModelProfileSelector.test.tsx:      <ModelProfileSelector
src/components/chat/__tests__/ModelProfileSelector.test.tsx:      <ModelProfileSelector
src/components/chat/__tests__/ModelProfileSelector.test.tsx:      <ModelProfileSelector
src/components/chat/__tests__/ModelProfileSelector.test.tsx:      <ModelProfileSelector
src/components/chat/__tests__/SpiritUserProfilePanel.test.tsx:        activeModelProfileId="teacher"
src/components/chat/SpiritChat.tsx:import { ModelProfileSelector } from "@/components/chat/ModelProfileSelector";
src/components/chat/SpiritChat.tsx:import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
src/components/chat/SpiritChat.tsx:import { getModelProfile } from "@/lib/spirit/model-profiles";
src/components/chat/SpiritChat.tsx:      activeModelProfileId: persistent.activeModelProfileId,
src/components/chat/SpiritChat.tsx:      setActiveModelProfile: persistent.setActiveModelProfile,
src/components/chat/SpiritChat.tsx:    activeModelProfileId: modeRt.activeModelProfileId,
src/components/chat/SpiritChat.tsx:      modeRt.activeModelProfileId === "researcher"
src/components/chat/SpiritChat.tsx:        : modeRt.activeModelProfileId === "teacher"
src/components/chat/SpiritChat.tsx:      transport.lastSearchProvider ? `provider: ${transport.lastSearchProvider}` : null,
src/components/chat/SpiritChat.tsx:    modeRt.activeModelProfileId,
src/components/chat/SpiritChat.tsx:    transport.lastSearchProvider,
src/components/chat/SpiritChat.tsx:      `Provider (last): ${transport.lastSearchProvider ?? "-"}`,
src/components/chat/SpiritChat.tsx:    transport.lastSearchProvider,
src/components/chat/SpiritChat.tsx:  const prevModeRef = useRef<ModelProfileId | null>(null);
src/components/chat/SpiritChat.tsx:    const cur = modeRt.activeModelProfileId;
src/components/chat/SpiritChat.tsx:      const label = getModelProfile(cur).shortLabel;
src/components/chat/SpiritChat.tsx:  }, [savedChatShell, runtimeSurfaceProp, modeRt.activeModelProfileId, pushActivity]);
src/components/chat/SpiritChat.tsx:    lastSearchProvider,
src/components/chat/SpiritChat.tsx:        modelProfileId: modeRt.activeModelProfileId,
src/components/chat/SpiritChat.tsx:      modeRt.activeModelProfileId,
src/components/chat/SpiritChat.tsx:    tc.researchPlanOpen && modeRt.activeModelProfileId === "researcher"
src/components/chat/SpiritChat.tsx:          modelProfileId: modeRt.activeModelProfileId,
src/components/chat/SpiritChat.tsx:          busy: tc.isBusy || (tc.researchPlanOpen && modeRt.activeModelProfileId === "researcher"),
src/components/chat/SpiritChat.tsx:      modeRt.activeModelProfileId,
src/components/chat/SpiritChat.tsx:    modeRt.activeModelProfileId === "researcher" && !tc.webSearchOptOut;
src/components/chat/SpiritChat.tsx:      (modeRt.activeModelProfileId === "teacher" &&
src/components/chat/SpiritChat.tsx:    modeRt.activeModelProfileId === "normal-peer" ||
src/components/chat/SpiritChat.tsx:    modeRt.activeModelProfileId === "sassy-chaotic" ||
src/components/chat/SpiritChat.tsx:    modeRt.activeModelProfileId === "brutal";
src/components/chat/SpiritChat.tsx:        provider={lastSearchProvider ?? lastWebSourcesPayload?.provider ?? undefined}
src/components/chat/SpiritChat.tsx:                researchPlanOpen && modeRt.activeModelProfileId === "researcher"
src/components/chat/SpiritChat.tsx:                (researchPlanOpen && modeRt.activeModelProfileId === "researcher")
src/components/chat/SpiritChat.tsx:                title="Abliterated Mode routes this chat to hermes3:8b-abliterated"
src/components/chat/SpiritChat.tsx:                  <ModelProfileSelector
src/components/chat/SpiritChat.tsx:                    value={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                      void modeRt.setActiveModelProfile(id);
src/components/chat/SpiritChat.tsx:                      setModeToast(`Mode set to ${getModelProfile(id).label}`);
src/components/chat/SpiritChat.tsx:            {modeRt.activeModelProfileId === "researcher" ? (
src/components/chat/SpiritChat.tsx:            {modeRt.activeModelProfileId === "teacher" ? (
src/components/chat/SpiritChat.tsx:            modeRt.activeModelProfileId === "researcher" &&
src/components/chat/SpiritChat.tsx:                        profileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                      <ModelProfileSelector
src/components/chat/SpiritChat.tsx:                        value={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                          void modeRt.setActiveModelProfile(id);
src/components/chat/SpiritChat.tsx:                      profileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                      <ModelProfileSelector
src/components/chat/SpiritChat.tsx:                        value={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                          void modeRt.setActiveModelProfile(id);
src/components/chat/SpiritChat.tsx:                  modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
src/components/chat/SpiritChat.tsx:                  voiceProviderLine={oracleVoiceBackendLabel}
src/components/chat/SpiritChat.tsx:          modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
src/components/chat/SpiritChat.tsx:          activeModelProfileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:            modelProfileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                      profileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                    <ModelProfileSelector
src/components/chat/SpiritChat.tsx:                      value={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                        void modeRt.setActiveModelProfile(id);
src/components/chat/SpiritChat.tsx:                  profileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                  <ModelProfileSelector
src/components/chat/SpiritChat.tsx:                    value={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:                      void modeRt.setActiveModelProfile(id);
src/components/chat/SpiritChat.tsx:                modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
src/components/chat/SpiritChat.tsx:                voiceProviderLine={oracleVoiceBackendLabel}
src/components/chat/SpiritChat.tsx:            modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
src/components/chat/SpiritChat.tsx:            activeModelProfileId={modeRt.activeModelProfileId}
src/components/chat/SpiritChat.tsx:              modelProfileId={modeRt.activeModelProfileId}
src/components/chat/SpiritWorkflowVisualizer.tsx:    const prov = provider ? ` · Provider: ${provider}` : "";
src/components/design-demo/DemoQuarantinePreview.tsx:    title: "Model Lab",
src/components/oracle/OracleVoiceSurface.tsx:import { ModelProfileSelector } from "@/components/chat/ModelProfileSelector";
src/components/oracle/OracleVoiceSurface.tsx:import { getModelProfile } from "@/lib/spirit/model-profiles";
src/components/oracle/OracleVoiceSurface.tsx:      activeModelProfileId: persistent.activeModelProfileId,
src/components/oracle/OracleVoiceSurface.tsx:      setActiveModelProfile: persistent.setActiveModelProfile,
src/components/oracle/OracleVoiceSurface.tsx:    activeModelProfileId: modeRt.activeModelProfileId,
src/components/oracle/OracleVoiceSurface.tsx:    const cur = modeRt.activeModelProfileId;
src/components/oracle/OracleVoiceSurface.tsx:      const label = getModelProfile(cur).shortLabel;
src/components/oracle/OracleVoiceSurface.tsx:  }, [modeRt.activeModelProfileId, pushActivity]);
src/components/oracle/OracleVoiceSurface.tsx:          modelProfileId: modeRt.activeModelProfileId,
src/components/oracle/OracleVoiceSurface.tsx:  }, [displayMessages, modeRt.activeModelProfileId, transport.isBusy, voiceRt, tts, pushActivity]);
src/components/oracle/OracleVoiceSurface.tsx:            profileId={modeRt.activeModelProfileId}
src/components/oracle/OracleVoiceSurface.tsx:            <ModelProfileSelector
src/components/oracle/OracleVoiceSurface.tsx:              value={modeRt.activeModelProfileId}
src/components/oracle/OracleVoiceSurface.tsx:                void modeRt.setActiveModelProfile(id);
src/components/oracle/OracleVoiceSurface.tsx:            modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
src/components/oracle/OracleVoiceSurface.tsx:            voiceProviderLine={oracleVoiceBackendLabel}
src/components/oracle/OracleVoiceSurface.tsx:        modeLabel={getModelProfile(modeRt.activeModelProfileId).shortLabel}
src/components/oracle/OracleVoiceSurface.tsx:        activeModelProfileId={modeRt.activeModelProfileId}
src/components/oracle/OracleVoiceStatusCard.tsx:  voiceProviderLine: string;
src/components/oracle/OracleVoiceStatusCard.tsx:  voiceProviderLine,
src/components/oracle/OracleVoiceStatusCard.tsx:          <dd className="min-w-0 truncate">{voiceProviderLine}</dd>
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="elevenlabs"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="elevenlabs"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="piper"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="elevenlabs"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="piper"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="piper"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="piper"
src/components/oracle/__tests__/OracleVoiceStatusCard.test.tsx:        voiceProviderLine="/api/tts"
src/components/oracle/__tests__/OracleVoiceSurface.test.tsx:          activeModelProfileId: "normal-peer",
src/components/oracle/__tests__/OracleVoiceSurface.test.tsx:          setActiveModelProfile: async () => {},
src/components/coding/CodingCockpitShell.tsx:  localHermesProviderModelTruth,
src/components/coding/CodingCockpitShell.tsx:  providerModelTruthFromPayload,
src/components/coding/CodingCockpitShell.tsx:  type CodingProviderModelTruth,
src/components/coding/CodingCockpitShell.tsx:} from "@/lib/coding/model-provider-status";
src/components/coding/CodingCockpitShell.tsx:  providerModelBlockedReason?: string;
src/components/coding/CodingCockpitShell.tsx:  providerModelApiBaseHost?: string | null;
src/components/coding/CodingCockpitShell.tsx:  providerModelProbeOk?: boolean | null;
src/components/coding/CodingCockpitShell.tsx:  providerModelSelectedVia?: string | null;
src/components/coding/CodingCockpitShell.tsx:  providerModelSource?: string;
src/components/coding/CodingCockpitShell.tsx:  providerModelStatus?: string;
src/components/coding/CodingCockpitShell.tsx:  configuredModelIsHermes?: boolean | null;
src/components/coding/CodingCockpitShell.tsx:  providerModelSource: string;
src/components/coding/CodingCockpitShell.tsx:  providerModelStatus: string;
src/components/coding/CodingCockpitShell.tsx:  reversalProvider: string | null;
src/components/coding/CodingCockpitShell.tsx:  reversalModel: string | null;
src/components/coding/CodingCockpitShell.tsx:  reversalProviderModelSource: string | null;
src/components/coding/CodingCockpitShell.tsx:  const providerTruth = selectedProviderModelTruth();
src/components/coding/CodingCockpitShell.tsx:    providerModelBlockedReason: providerTruth.blockedReason,
src/components/coding/CodingCockpitShell.tsx:    providerModelApiBaseHost: providerTruth.providerModelApiBaseHost,
src/components/coding/CodingCockpitShell.tsx:    providerModelProbeOk: providerTruth.providerModelProbeOk,
src/components/coding/CodingCockpitShell.tsx:    providerModelSelectedVia: providerTruth.providerModelSelectedVia,
src/components/coding/CodingCockpitShell.tsx:    providerModelSource: providerTruth.source,
src/components/coding/CodingCockpitShell.tsx:    providerModelStatus: providerTruth.status,
src/components/coding/CodingCockpitShell.tsx:    configuredModelIsHermes: providerTruth.configuredModelIsHermes,
src/components/coding/CodingCockpitShell.tsx:function providerTruthForPreviewState(previewState: PreviewState): CodingProviderModelTruth {
src/components/coding/CodingCockpitShell.tsx:  return localHermesProviderModelTruth({
src/components/coding/CodingCockpitShell.tsx:      previewState.providerModelBlockedReason ||
src/components/coding/CodingCockpitShell.tsx:      (previewState.providerModelStatus === "unknown"
src/components/coding/CodingCockpitShell.tsx:    providerModelApiBaseHost: previewState.providerModelApiBaseHost,
src/components/coding/CodingCockpitShell.tsx:    providerModelProbeOk: previewState.providerModelProbeOk,
src/components/coding/CodingCockpitShell.tsx:    providerModelSelectedVia: previewState.providerModelSelectedVia,
src/components/coding/CodingCockpitShell.tsx:    source: previewState.providerModelSource === "runtime"
src/components/coding/CodingCockpitShell.tsx:      : previewState.providerModelSource === "inferred"
src/components/coding/CodingCockpitShell.tsx:        : previewState.providerModelSource === "config"
src/components/coding/CodingCockpitShell.tsx:          : previewState.providerModelSource === "unknown"
src/components/coding/CodingCockpitShell.tsx:    status: previewState.providerModelStatus === "available"
src/components/coding/CodingCockpitShell.tsx:      : previewState.providerModelStatus === "configured"
src/components/coding/CodingCockpitShell.tsx:        : previewState.providerModelStatus === "unavailable"
src/components/coding/CodingCockpitShell.tsx:          : previewState.providerModelStatus === "proposal_only"
src/components/coding/CodingCockpitShell.tsx:function providerTruthPatch(providerTruth: CodingProviderModelTruth) {
src/components/coding/CodingCockpitShell.tsx:    providerModelBlockedReason: providerTruth.blockedReason,
src/components/coding/CodingCockpitShell.tsx:    providerModelApiBaseHost: providerTruth.providerModelApiBaseHost,
src/components/coding/CodingCockpitShell.tsx:    providerModelProbeOk: providerTruth.providerModelProbeOk,
src/components/coding/CodingCockpitShell.tsx:    providerModelSelectedVia: providerTruth.providerModelSelectedVia,
src/components/coding/CodingCockpitShell.tsx:    providerModelSource: providerTruth.source,
src/components/coding/CodingCockpitShell.tsx:    providerModelStatus: providerTruth.status,
src/components/coding/CodingCockpitShell.tsx:    configuredModelIsHermes: providerTruth.configuredModelIsHermes,
src/components/coding/CodingCockpitShell.tsx:function selectedProviderModelTruth(): CodingProviderModelTruth {
src/components/coding/CodingCockpitShell.tsx:  return localHermesProviderModelTruth();
src/components/coding/CodingCockpitShell.tsx:      providerModelSource: previewState.providerModelSource ?? "unknown",
src/components/coding/CodingCockpitShell.tsx:      providerModelStatus: previewState.providerModelStatus ?? "unknown",
src/components/coding/CodingCockpitShell.tsx:      reversalModel: null,
src/components/coding/CodingCockpitShell.tsx:      reversalProvider: null,
src/components/coding/CodingCockpitShell.tsx:      reversalProviderModelSource: null,
src/components/coding/CodingCockpitShell.tsx:  const providerTruth = selectedProviderModelTruth();
src/components/coding/CodingCockpitShell.tsx:      providerModelSource: providerTruth.source,
src/components/coding/CodingCockpitShell.tsx:      providerModelStatus: providerTruth.status,
src/components/coding/CodingCockpitShell.tsx:      reversalModel: null,
src/components/coding/CodingCockpitShell.tsx:      reversalProvider: null,
src/components/coding/CodingCockpitShell.tsx:      reversalProviderModelSource: null,
src/components/coding/CodingCockpitShell.tsx:      providerModelSource: previewState.providerModelSource ?? "unknown",
src/components/coding/CodingCockpitShell.tsx:      providerModelStatus: previewState.providerModelStatus ?? "unknown",
src/components/coding/CodingCockpitShell.tsx:      reversalModel: null,
src/components/coding/CodingCockpitShell.tsx:      reversalProvider: null,
src/components/coding/CodingCockpitShell.tsx:      reversalProviderModelSource: null,
src/components/coding/CodingCockpitShell.tsx:  const activeProviderTruth = providerTruthForPreviewState(previewState);
src/components/coding/CodingCockpitShell.tsx:    { label: "Provider", value: activeProviderTruth.providerLabel },
src/components/coding/CodingCockpitShell.tsx:    { label: "Model", value: activeProviderTruth.modelLabel },
src/components/coding/CodingCockpitShell.tsx:    { label: "Source", value: activeProviderTruth.source },
src/components/coding/CodingCockpitShell.tsx:      providerModelStatus: providerTruth.status,
src/components/coding/CodingCockpitShell.tsx:      `provider_model_probe_ok: ${providerTruth.providerModelProbeOk === null || providerTruth.providerModelProbeOk === undefined ? "unknown" : providerTruth.providerModelProbeOk}`,
src/components/coding/CodingCockpitShell.tsx:      `provider_model_selected_via: ${providerTruth.providerModelSelectedVia ?? "unknown"}`,
src/components/coding/CodingCockpitShell.tsx:      `provider_model_api_base_host: ${providerTruth.providerModelApiBaseHost ?? "unknown"}`,
src/components/coding/CodingCockpitShell.tsx:        providerTruth.configuredModelIsHermes === null
src/components/coding/CodingCockpitShell.tsx:          : providerTruth.configuredModelIsHermes
src/components/coding/CodingCockpitShell.tsx:      `provider_at_reversal_time: ${reversalStatus ? selectedProviderModelTruth().providerLabel : "not reversed"}`,
src/components/coding/CodingCockpitShell.tsx:      `model_at_reversal_time: ${reversalStatus ? selectedProviderModelTruth().modelLabel : "not reversed"}`,
src/components/coding/CodingCockpitShell.tsx:                  `provider_model_source=${receipt.providerModelSource ?? "unknown"}`,
src/components/coding/CodingCockpitShell.tsx:                  `provider_model_status=${receipt.providerModelStatus ?? "unknown"}`,
src/components/coding/CodingCockpitShell.tsx:                  `reversal_provider=${receipt.reversalProvider ?? "not reversed"}`,
src/components/coding/CodingCockpitShell.tsx:                  `reversal_model=${receipt.reversalModel ?? "not reversed"}`,
src/components/coding/CodingCockpitShell.tsx:      `Provider: ${providerTruth.providerLabel}`,
src/components/coding/CodingCockpitShell.tsx:      `Model: ${providerTruth.modelLabel}`,
src/components/coding/CodingCockpitShell.tsx:      `Provider/model source: ${providerTruth.source}`,
src/components/coding/CodingCockpitShell.tsx:      `Provider/model selected via: ${providerTruth.providerModelSelectedVia ?? "unknown"}`,
src/components/coding/CodingCockpitShell.tsx:        providerTruth.configuredModelIsHermes === null
src/components/coding/CodingCockpitShell.tsx:          : providerTruth.configuredModelIsHermes
src/components/coding/CodingCockpitShell.tsx:    const selectedTruth = selectedProviderModelTruth();
src/components/coding/CodingCockpitShell.tsx:      const proposalProviderTruth = providerModelTruthFromPayload(proposalPayload, selectedTruth);
src/components/coding/CodingCockpitShell.tsx:            ...providerTruthPatch(proposalProviderTruth),
src/components/coding/CodingCockpitShell.tsx:          ...providerTruthPatch(proposalProviderTruth),
```

```diff
diff --git a/src/app/v1/decisions/prompt-packet/route.ts b/src/app/v1/decisions/prompt-packet/route.ts
index 84f31e7..ca4ffaf 100644
--- a/src/app/v1/decisions/prompt-packet/route.ts
+++ b/src/app/v1/decisions/prompt-packet/route.ts
@@ -34,7 +34,9 @@ export async function POST(request: Request) {
   const contentType = response.headers.get("content-type") ?? "application/json";
   const body =
     contentType.includes("application/json") && response.ok
-      ? mergeRepoFirstResearchSources(bodyText, responseText)
+      ? await enrichProviderModelTruthFromStatus(
+          mergeRepoFirstResearchSources(bodyText, responseText),
+        )
       : responseText;
 
   return new Response(body, {
@@ -45,3 +47,115 @@ export async function POST(request: Request) {
     statusText: response.statusText,
   });
 }
+
+type JsonRecord = Record<string, unknown>;
+
+async function enrichProviderModelTruthFromStatus(responseBodyText: string) {
+  let payload: unknown;
+  try {
+    payload = JSON.parse(responseBodyText);
+  } catch {
+    return responseBodyText;
+  }
+  if (!isRecord(payload) || hasProviderModelTruth(payload)) {
+    return responseBodyText;
+  }
+
+  const localRoute = await readConfiguredLocalRoute();
+  if (!localRoute) {
+    return responseBodyText;
+  }
+
+  const providerModelTruth = providerModelTruthForLocalRoute(localRoute);
+  payload.provider = providerModelTruth.providerId;
+  payload.model = providerModelTruth.modelId;
+  payload.provider_model_truth = providerModelTruth;
+  payload.providerModelTruth = providerModelTruth;
+  payload.provider_model_source = providerModelTruth.source;
+  payload.provider_model_status = providerModelTruth.status;
+  payload.provider_call_made = providerModelTruth.providerCallMade;
+  payload.provider_call_authorized = providerModelTruth.providerCallAuthorized;
+  payload.hermes_lane_available = providerModelTruth.hermesLaneAvailable;
+  payload.hermes_used_for_this_run = providerModelTruth.hermesUsedForThisRun;
+  payload.provider_model_probe_ok = providerModelTruth.probeOk;
+  payload.provider_model_selected_via = providerModelTruth.selectedVia;
+  payload.provider_model_api_base_host = providerModelTruth.apiBaseHost;
+  return JSON.stringify(payload);
+}
+
+function hasProviderModelTruth(payload: JsonRecord) {
+  return Boolean(
+    payload.provider_model_truth ||
+      payload.providerModelTruth ||
+      payload.provider ||
+      payload.model,
+  );
+}
+
+async function readConfiguredLocalRoute() {
+  try {
+    const response = await sourceProxyFetch("/v1/self/status", { method: "GET" });
+    if (!response.ok) return null;
+    const payload = await response.json() as unknown;
+    if (!isRecord(payload)) return null;
+    const routes = Array.isArray(payload.model_routes) ? payload.model_routes : [];
+    return routes
+      .filter(isRecord)
+      .find((route) => route.alias === "local" && route.enabled === true) ?? null;
+  } catch {
+    return null;
+  }
+}
+
+function providerModelTruthForLocalRoute(route: JsonRecord) {
+  const provider = stringFromUnknown(route.provider) || "ollama";
+  const model =
+    stringFromUnknown(route.resolved_model) ||
+    stringFromUnknown(route.model) ||
+    "";
+  const providerIsLocal = provider === "ollama" || provider === "local";
+  const modelLabel = model ? model.replace(/^ollama_chat\//, "") : "Unknown local model";
+  const configuredModelIsHermes = model ? /hermes/i.test(model) : null;
+  return {
+    authority: {
+      canApply: false,
+      canCommit: false,
+      canDraft: true,
+      canPreview: true,
+      canPush: false,
+      canVerify: false,
+    },
+    blockedReason: !model
+      ? "Local/Ollama lane is configured, but the exact runtime model was not recorded."
+      : configuredModelIsHermes === false
+        ? "Local/Ollama lane is configured, but the selected model is not Hermes."
+        : "",
+    configured: Boolean(model),
+    configuredModelIsHermes,
+    configuredOllamaModel: stringFromUnknown(route.configured_ollama_model) || modelLabel,
+    externalCallAvailable: !providerIsLocal,
+    family: providerIsLocal ? "local/ollama/hermes" : "unknown",
+    hermesLaneAvailable: providerIsLocal,
+    hermesUsedForThisRun: null,
+    modelId: model || "unknown-local-model",
+    modelLabel,
+    previewAvailable: true,
+    providerCallAuthorized: false,
+    providerCallMade: false,
+    providerId: providerIsLocal ? "local" : provider,
+    providerLabel: providerIsLocal ? "Local / Ollama" : provider,
+    apiBaseHost: stringFromUnknown(route.api_base_host),
+    probeOk: typeof route.probe_ok === "boolean" ? route.probe_ok : null,
+    selectedVia: stringFromUnknown(route.selected_via),
+    source: "config",
+    status: model ? "configured" : "unknown",
+  };
+}
+
+function isRecord(value: unknown): value is JsonRecord {
+  return Boolean(value && typeof value === "object" && !Array.isArray(value));
+}
+
+function stringFromUnknown(value: unknown) {
+  return typeof value === "string" && value.trim() ? value.trim() : null;
+}
diff --git a/src/components/coding/CodingCockpitShell.tsx b/src/components/coding/CodingCockpitShell.tsx
index a2d622b..97c14e2 100644
--- a/src/components/coding/CodingCockpitShell.tsx
+++ b/src/components/coding/CodingCockpitShell.tsx
@@ -1,19 +1,27 @@
 "use client";
 
 import Link from "next/link";
-import { useMemo, useState } from "react";
-import { FileText, ShieldCheck } from "lucide-react";
+import { useEffect, useMemo, useState } from "react";
+import { Copy, FileText, ShieldCheck } from "lucide-react";
 
 import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
+import {
+  agentTrialRunSizes,
+  agentTrialViewports,
+  buildAgentTrialUiState,
+  classifyDiagnosticSidecar,
+  type AgentTrialMode,
+  type AgentTrialPromptPreview,
+  type AgentTrialRunSize,
+  type AgentTrialViewport,
+} from "@/lib/coding/agent-trials-ui";
+import {
+  localHermesProviderModelTruth,
+  providerModelTruthFromPayload,
+  type CodingProviderModelTruth,
+} from "@/lib/coding/model-provider-status";
 import "@/styles/dashboard-demo-v4.css";
 
-const statusItems = [
-  { label: "Proxy", value: "Ready for safe preview" },
-  { label: "Route", value: "Select during preview" },
-  { label: "Workspace", value: "SpiritOS" },
-];
-
-const statusStripItems = ["Draft", "Preview", "Approval", "Apply", "Verify"];
 const commandPanelClass =
   "rounded-md border border-[var(--ddv4-surface-border-soft)] bg-[var(--ddv4-pill-bg)] shadow-[var(--ddv4-glass-shadow-drop)] backdrop-blur-xl";
 const commandInsetClass =
@@ -30,54 +38,231 @@ type PreviewState = {
   approvedAt: string | null;
   appliedAt: string | null;
   applySummary: string;
+  allowedFiles: string[];
   blocker: string | null;
   changedFiles: string[];
+  checks: string[];
+  currentPhase: string;
   diff: string;
   error: string | null;
+  events: ManualTaskEvent[];
+  forbiddenFiles: string[];
   isApplying: boolean;
   isLoading: boolean;
+  model: string | null;
+  previewStatus: string;
+  provider: string | null;
+  providerCallAuthorized?: boolean;
+  providerCallMade?: boolean;
+  providerModelBlockedReason?: string;
+  providerModelApiBaseHost?: string | null;
+  providerModelProbeOk?: boolean | null;
+  providerModelSelectedVia?: string | null;
+  providerModelSource?: string;
+  providerModelStatus?: string;
+  configuredModelIsHermes?: boolean | null;
+  hermesLaneAvailable?: boolean;
+  hermesUsedForThisRun?: boolean | null;
   requirementSummary: string;
+  reasonCode: string | null;
   reviewerSummary: string;
+  routeCalled: string | null;
+  selectedTarget: string | null;
   status: "idle" | "ready" | "approved" | "applied" | "blocked" | "error" | "satisfied";
+  targetCandidates: string[];
   targetMatch: boolean;
   taskId: string;
   taskSpecAllowed: boolean;
   verifierSummary: string;
+  technicalDetail?: string | null;
 };
 
-type TimelineItem = {
-  label: string;
-  status: string;
+type TrialRunState = "idle" | "running" | "complete";
+type ManualTaskEventStatus = "done" | "running" | "blocked" | "failed";
+type ManualTaskEvent = {
   detail: string;
-  active: boolean;
+  label: string;
+  status: ManualTaskEventStatus;
+};
+
+const manualTaskPhaseLabels = {
+  received: "received prompt",
+  analyzing: "analyzing request",
+  discovering: "discovering likely files",
+  packet: "building task packet",
+  preview: "generating preview",
+  checks: "running checks or preparing checks",
+  review: "reviewing result",
+  done: "done",
+  blocked: "blocked",
+  failed: "failed",
+} as const;
+
+type ManualTaskPhase = keyof typeof manualTaskPhaseLabels;
+
+type ManualTaskPacket = {
+  allowedFiles: string[];
+  checks: string[];
+  forbiddenFiles: string[];
+  reasonCode: string | null;
+  selectedTarget: string | null;
+  targetCandidates: string[];
+  taskText: string;
+};
+
+type ApplyScopePreflight = {
+  allowedFiles: string[];
+  allChangedFilesAllowed: boolean;
+  changedFiles: string[];
+  reason: string | null;
+  reasonCode: string | null;
 };
 
```

```text
```

## Result

GO. /coding already carries provider/model truth from Source Proxy status into prompt packet diagnostics; patch now prefers the resolved Source Proxy local model field when present. No broad UI redesign was made.

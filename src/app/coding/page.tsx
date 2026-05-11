"use client";

import { useEffect, useRef, useState } from "react";

import { DashboardDemoV4Atmosphere } from "@/components/dashboard/demo-v4/DashboardDemoV4Atmosphere";
import { DashboardDemoV4FloatingNav } from "@/components/dashboard/demo-v4/DashboardDemoV4FloatingNav";
import "@/styles/dashboard-demo-v4.css";

const acceptedFileTypes =
  ".png,.jpg,.jpeg,.webp,.mp4,.webm,.xml,.json,.md,.txt";
const acceptedFileExtensions = new Set(
  acceptedFileTypes.split(",").map((extension) => extension.trim()),
);

type ProcessLog = {
  id: number;
  label: string;
  detail: string;
  level: "info" | "success" | "warning";
};

type ProxyMetrics = {
  health: "online" | "offline";
  route: string;
  model: string;
  risk: string;
  tokens: number | null;
};

type UploadedFile = {
  id: string;
  name: string;
  size: number;
};

type ResearchSource = {
  title?: string;
  url?: string;
  snippet?: string;
};

type ProxyRouteDecisionResponse = {
  task_classification?: string;
  recommended_route?: string;
  model?: string;
  recommended_model?: string;
  primary_model?: string;
  target_model_hint?: string;
  reason_codes?: string[];
  risk_tier?: string;
  context_estimate?: {
    estimated_task_tokens?: number;
    total_estimated_tokens?: number;
  };
  next_prompt_action?: string;
  research_recommended?: boolean;
  research_sources?: ResearchSource[];
};

type PromptPacketResponse = {
  prompt_text?: string;
  requested_output?: string[];
  research_sources?: ResearchSource[];
  route_decision?: ProxyRouteDecisionResponse;
  requests_for_more_information?: string[];
};

type FinalOutput = {
  decisionPayload: string;
  promptText: string;
  researchSources: ResearchSource[];
  paths: string[];
  requests: string[];
};

export default function CodingProxyPage() {
  const [inputText, setInputText] = useState("");
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [processLogs, setProcessLogs] = useState<ProcessLog[]>([
    {
      id: 1,
      label: "Idle",
      detail: "Source proxy test interface ready.",
      level: "info",
    },
  ]);
  const [finalOutput, setFinalOutput] = useState<FinalOutput | null>(null);
  const [proxyMetrics, setProxyMetrics] = useState<ProxyMetrics>({
    health: "offline",
    route: "not run",
    model: "not returned",
    risk: "not run",
    tokens: null,
  });
  const [isRunning, setIsRunning] = useState(false);

  async function runProxyFlow() {
    setIsRunning(true);
    setFinalOutput(null);

    const task = inputText.trim();
    setProxyMetrics({
      health: "offline",
      route: "pending",
      model: "pending",
      risk: "pending",
      tokens: null,
    });
    setProcessLogs([
      {
        id: 1,
        label: "Route request",
        detail: "Sending task to /v1/decisions/route.",
        level: "info",
      },
    ]);

    try {
      const decision = await callProxyRouteDecision({ task });
      let researchSources = decision.research_sources ?? [];

      if (decision.research_recommended) {
        const researchPreview = await callProxyResearchPreview({ task });
        researchSources = researchPreview.research_sources ?? researchSources;
      }

      const promptPacket = await callProxyPromptPacket({
        researchSources,
        task,
      });
      researchSources = promptPacket.research_sources ?? researchSources;

      setProxyMetrics({
        health: "online",
        route: decision.recommended_route ?? "unknown",
        model: modelFromDecision(decision),
        risk: formatRiskTier(decision.risk_tier),
        tokens: decision.context_estimate?.total_estimated_tokens ?? null,
      });
      setFinalOutput({
        decisionPayload: JSON.stringify(decision, null, 2),
        promptText: promptPacket.prompt_text ?? "No prompt_text returned.",
        researchSources,
        paths: pathChoicesForDecision(decision),
        requests: promptPacket.requests_for_more_information ?? [],
      });

      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: 2,
          label: "Routing decision",
          detail: `Selected ${decision.recommended_route ?? "unknown route"} for ${
            decision.task_classification ?? "unclassified task"
          }.`,
          level: "success",
        },
        {
          id: 3,
          label: decision.research_recommended
            ? "Research recommended"
            : "Research not recommended",
          detail: `${researchSources.length} research source${
            researchSources.length === 1 ? "" : "s"
          } returned with the route decision.`,
          level: decision.research_recommended ? "warning" : "info",
        },
        ...(decision.research_recommended
          ? [
              {
                id: 4,
                label: "Research preview completed",
                detail: `${researchSources.length} source${
                  researchSources.length === 1 ? "" : "s"
                } ready for prompt refinement.`,
                level: "success" as const,
              },
            ]
          : []),
        {
          id: decision.research_recommended ? 5 : 4,
          label: "Prompt packet ready",
          detail: `Prompt packet returned for ${
            promptPacket.route_decision?.task_classification ??
            decision.task_classification ??
            "unclassified task"
          }.`,
          level: "success",
        },
      ]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown proxy error.";
      if (isProxyFeatureFlagOff(message)) {
        runMockProxyFlow(task);
        return;
      }

      setProcessLogs((currentLogs) => [
        ...currentLogs,
        {
          id: 2,
          label: "Proxy error",
          detail: message,
          level: "warning",
        },
      ]);
      setFinalOutput({
        decisionPayload: message,
        promptText: "",
        researchSources: [],
        paths: ["Check Source Proxy"],
        requests: ["Confirm SPIRIT_CODING_USE_PROXY=true and restart the dev server"],
      });
      setProxyMetrics({
        health: "offline",
        route: "request failed",
        model: "not returned",
        risk: "not returned",
        tokens: null,
      });
    } finally {
      setIsRunning(false);
    }
  }

  function runMockProxyFlow(task: string) {
    const mockDecision = buildMockDecision(task);
    const mockPacket = buildMockPromptPacket(task);

    setProxyMetrics({
      health: "offline",
      route: mockDecision.recommended_route ?? "mock_route",
      model: "mock",
      risk: formatRiskTier(mockDecision.risk_tier),
      tokens: mockDecision.context_estimate?.total_estimated_tokens ?? null,
    });
    setFinalOutput({
      decisionPayload: JSON.stringify(mockDecision, null, 2),
      promptText: mockPacket.prompt_text ?? "No mock prompt_text returned.",
      researchSources: [],
      paths: pathChoicesForDecision(mockDecision),
      requests: mockPacket.requests_for_more_information ?? [],
    });
    setProcessLogs((currentLogs) => [
      ...currentLogs,
      {
        id: 2,
        label: "Proxy flag off",
        detail: "SPIRIT_CODING_USE_PROXY is not true. Using mock coding flow.",
        level: "warning",
      },
      {
        id: 3,
        label: "Mock route decision",
        detail: `Selected ${mockDecision.recommended_route} for mock testing.`,
        level: "success",
      },
      {
        id: 4,
        label: "Mock prompt packet ready",
        detail: "Mock prompt packet returned without contacting Source Proxy.",
        level: "success",
      },
    ]);
  }

  return (
    <main className="dashboard-demo-v4-root">
      <DashboardDemoV4Atmosphere />

      <div className="dashboard-demo-v4-shell">
        <div className="flex min-h-[calc(100dvh-2rem)] flex-col overflow-hidden border border-slate-300 bg-white text-slate-950 lg:min-h-[calc(100dvh-4rem)]">
          <ProxyMetaToolbar metrics={proxyMetrics} isRunning={isRunning} />

          <section className="grid min-h-0 flex-1 grid-cols-1 border-y border-slate-300 md:grid-cols-2">
            <ProcessWindow logs={processLogs} />
            <OutputWindow finalOutput={finalOutput} isRunning={isRunning} />
          </section>

          <PromptInput
            files={uploadedFiles}
            inputText={inputText}
            isRunning={isRunning}
            onChange={setInputText}
            onFilesAdded={(files) => setUploadedFiles((current) => [...current, ...files])}
            onSubmit={runProxyFlow}
          />
        </div>
      </div>

      <DashboardDemoV4FloatingNav />
    </main>
  );
}

function ProxyMetaToolbar({
  metrics,
  isRunning,
}: {
  metrics: ProxyMetrics;
  isRunning: boolean;
}) {
  const isOnline = metrics.health === "online";

  return (
    <header className="flex min-h-14 flex-wrap items-center gap-3 border-b border-slate-300 bg-slate-100 px-4 py-2 text-sm">
      <div className="flex items-center gap-2 border border-slate-300 bg-white px-3 py-1">
        <span
          className={`h-2.5 w-2.5 rounded-full ${
            isOnline ? "bg-green-500" : "bg-red-500"
          }`}
        />
        <span>Proxy: {isOnline ? "Healthy" : "Offline"}</span>
      </div>

      <div className="border border-slate-300 bg-white px-3 py-1">
        Route: {metrics.route} | Model: {metrics.model} | Risk: {metrics.risk}
      </div>

      <div className="border border-slate-300 bg-white px-3 py-1">
        Tokens: {metrics.tokens ?? "not returned"}
      </div>

      {isRunning ? (
        <div className="border border-slate-300 bg-yellow-50 px-3 py-1">
          Stream: running
        </div>
      ) : null}
    </header>
  );
}

function ProcessWindow({ logs }: { logs: ProcessLog[] }) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [logs]);

  return (
    <section className="flex min-h-0 flex-col border-b border-slate-300 md:border-r md:border-b-0">
      <div className="border-b border-slate-700 bg-slate-950 px-4 py-2 font-mono text-sm text-slate-100">
        Process Window
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto bg-slate-900 p-4 font-mono text-sm text-slate-100">
        {logs.length === 0 ? (
          <div className="text-slate-400">Waiting for proxy events...</div>
        ) : null}

        <div className="space-y-3">
          {logs.map((log) => (
            <div key={log.id} className="border-l border-slate-600 pl-3">
              <div className={logLevelClassName(log.level)}>[{log.label}]</div>
              <div className="text-slate-300">{log.detail}</div>
            </div>
          ))}
        </div>

        <div ref={bottomRef} />
      </div>
    </section>
  );
}

function OutputWindow({
  finalOutput,
  isRunning,
}: {
  finalOutput: FinalOutput | null;
  isRunning: boolean;
}) {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  useEffect(() => {
    setSelectedPath(null);
  }, [finalOutput]);

  return (
    <section className="flex min-h-0 flex-col bg-slate-50">
      <div className="border-b border-slate-300 bg-white px-4 py-2 text-sm font-semibold">
        Output Window
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {finalOutput === null ? (
          <div className="border border-dashed border-slate-300 bg-white p-4 text-sm text-slate-600">
            {isRunning
              ? "Waiting for proxy response..."
              : "Submit a prompt to show the route decision payload."}
          </div>
        ) : (
          <div className="space-y-4">
            <section className="sticky top-0 z-10 border border-slate-300 bg-white p-4 shadow-sm">
              <h2 className="text-sm font-semibold text-slate-950">Paths to Choose</h2>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                {finalOutput.paths.map((path) => (
                  <button
                    className={`border px-3 py-2 text-left text-sm font-semibold hover:bg-slate-100 ${
                      selectedPath === path
                        ? "border-slate-900 bg-slate-900 text-white hover:bg-slate-800"
                        : "border-slate-300 bg-slate-50 text-slate-900"
                    }`}
                    key={path}
                    onClick={() => {
                      setSelectedPath(path);
                      console.log("Selected coding path:", path);
                    }}
                    type="button"
                  >
                    {path}
                  </button>
                ))}
              </div>
              {selectedPath ? (
                <div className="mt-3 border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-900">
                  Selected: {selectedPath}
                </div>
              ) : null}
            </section>

            <section className="border border-slate-300 bg-white p-4">
              <h1 className="text-sm font-semibold text-slate-950">
                Prompt Packet Text
              </h1>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-800">
                {finalOutput.promptText}
              </pre>
            </section>

            {finalOutput.requests.length > 0 ? (
              <section className="border border-slate-300 bg-white p-4">
                <h2 className="text-sm font-semibold text-slate-950">
                  Requests for More Information
                </h2>
                <div className="mt-3 space-y-2">
                  {finalOutput.requests.map((request) => (
                    <div
                      className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
                      key={request}
                    >
                      {request}
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            {finalOutput.researchSources.length > 0 ? (
              <section className="border border-slate-300 bg-white p-4">
                <h2 className="text-sm font-semibold text-slate-950">
                  Research Sources
                </h2>
                <div className="mt-3 space-y-3">
                  {finalOutput.researchSources.map((source, index) => (
                    <div
                      className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm"
                      key={`${source.url ?? source.title ?? "source"}-${index}`}
                    >
                      <div className="font-semibold text-slate-950">
                        {source.title ?? "Untitled source"}
                      </div>
                      <div className="break-all text-slate-600">
                        {source.url ?? "No URL returned"}
                      </div>
                      <p className="mt-2 text-slate-700">
                        {source.snippet ?? "No snippet returned"}
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}

            <section className="border border-slate-300 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-950">
                Route Decision Payload
              </h2>
              <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-sm leading-6 text-slate-800">
                {finalOutput.decisionPayload}
              </pre>
            </section>
          </div>
        )}
      </div>
    </section>
  );
}

function PromptInput({
  files,
  inputText,
  isRunning,
  onChange,
  onFilesAdded,
  onSubmit,
}: {
  files: UploadedFile[];
  inputText: string;
  isRunning: boolean;
  onChange: (value: string) => void;
  onFilesAdded: (files: UploadedFile[]) => void;
  onSubmit: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function addFiles(fileList: FileList | null) {
    if (!fileList) {
      return;
    }

    onFilesAdded(
      Array.from(fileList)
        .filter((file) => acceptedFileExtensions.has(fileExtension(file.name)))
        .map((file) => ({
          id: `${file.name}-${file.size}-${file.lastModified}`,
          name: file.name,
          size: file.size,
        })),
    );
  }

  return (
    <footer className="border-t border-slate-300 bg-slate-100 p-4">
      <div
        className="mb-3 border border-dashed border-slate-400 bg-white p-3 text-sm text-slate-700"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          addFiles(event.dataTransfer.files);
        }}
      >
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="font-semibold text-slate-950">File upload test area</div>
            <div className="text-slate-600">
              Drop files here or choose images, videos, XML, JSON, Markdown, or text.
            </div>
          </div>

          <button
            className="border border-slate-300 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-900 hover:bg-slate-100"
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            Choose files
          </button>
        </div>

        <input
          accept={acceptedFileTypes}
          className="hidden"
          multiple
          onChange={(event) => addFiles(event.target.files)}
          ref={fileInputRef}
          type="file"
        />

        {files.length > 0 ? (
          <ul className="mt-3 grid gap-2 md:grid-cols-2">
            {files.map((file) => (
              <li
                className="flex items-center justify-between gap-3 border border-slate-200 bg-slate-50 px-3 py-2"
                key={file.id}
              >
                <span className="min-w-0 truncate">{file.name}</span>
                <span className="shrink-0 text-slate-500">{formatFileSize(file.size)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="flex flex-col gap-3 md:flex-row">
        <textarea
          className="h-24 min-h-20 flex-1 resize-y border border-slate-300 bg-white p-3 text-sm outline-none focus:border-slate-600"
          onChange={(event) => onChange(event.target.value)}
          placeholder="Send a prompt through the Source proxy..."
          value={inputText}
        />

        <button
          className="border border-slate-900 bg-slate-900 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:border-slate-400 disabled:bg-slate-400 md:w-32"
          disabled={isRunning}
          onClick={onSubmit}
          type="button"
        >
          {isRunning ? "Running" : "Submit"}
        </button>
      </div>
    </footer>
  );
}

function logLevelClassName(level: ProcessLog["level"]) {
  if (level === "success") {
    return "text-green-300";
  }

  if (level === "warning") {
    return "text-yellow-300";
  }

  return "text-cyan-300";
}

function modelFromDecision(decision: ProxyRouteDecisionResponse) {
  return (
    decision.model ??
    decision.recommended_model ??
    decision.primary_model ??
    decision.target_model_hint ??
    "not returned"
  );
}

async function callProxyRouteDecision({
  task,
}: {
  task: string;
}): Promise<ProxyRouteDecisionResponse> {
  const response = await fetch("/v1/decisions/route", {
    body: JSON.stringify({ task: task || "No prompt supplied." }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload: unknown = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Route decision failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as ProxyRouteDecisionResponse;
}

function buildMockDecision(task: string): ProxyRouteDecisionResponse {
  const normalizedTask = task || "No prompt supplied.";
  const estimatedTokens = Math.max(1, Math.round(normalizedTask.length / 4));

  return {
    task_classification: "mock_coding_test",
    recommended_route: "local_route",
    reason_codes: ["feature_flag_disabled", "mock_fallback"],
    risk_tier: "low",
    context_estimate: {
      estimated_task_tokens: estimatedTokens,
      total_estimated_tokens: estimatedTokens,
    },
    next_prompt_action: "mock_prompt_packet",
    research_recommended: false,
    research_sources: [],
  };
}

function buildMockPromptPacket(task: string): PromptPacketResponse {
  const normalizedTask = task || "No prompt supplied.";

  return {
    prompt_text: [
      "# Mock Source Prompt Packet",
      "",
      "Target model hint: mock",
      "",
      "## Task",
      normalizedTask,
      "",
      "## Constraints",
      "- This is a mock fallback because SPIRIT_CODING_USE_PROXY is off.",
      "- No live proxy, research, or prompt-packet endpoint was called.",
      "",
      "## Requested Output",
      "- Confirm the coding page still works without the proxy flag.",
    ].join("\n"),
    requests_for_more_information: ["Enable SPIRIT_CODING_USE_PROXY=true for live proxy testing."],
    research_sources: [],
  };
}

async function callProxyResearchPreview({
  task,
}: {
  task: string;
}): Promise<ProxyRouteDecisionResponse> {
  const response = await fetch("/v1/decisions/route", {
    body: JSON.stringify({
      task: task || "No prompt supplied.",
      research_recommended: true,
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload: unknown = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Research preview failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as ProxyRouteDecisionResponse;
}

async function callProxyPromptPacket({
  researchSources,
  task,
}: {
  researchSources: ResearchSource[];
  task: string;
}): Promise<PromptPacketResponse> {
  const response = await fetch("/v1/decisions/prompt-packet", {
    body: JSON.stringify({
      task: task || "No prompt supplied.",
      needs_current_info: researchSources.length > 0,
      relevant_context: formatResearchContext(researchSources),
    }),
    headers: {
      "content-type": "application/json",
    },
    method: "POST",
  });

  const payload: unknown = await response.json();

  if (!response.ok) {
    const message =
      typeof payload === "object" &&
      payload !== null &&
      "error" in payload &&
      typeof payload.error === "string"
        ? payload.error
        : `Prompt packet failed with status ${response.status}.`;
    throw new Error(message);
  }

  return payload as PromptPacketResponse;
}

function formatResearchContext(researchSources: ResearchSource[]) {
  if (researchSources.length === 0) {
    return undefined;
  }

  return researchSources
    .map((source, index) => {
      return [
        `Source ${index + 1}: ${source.title ?? "Untitled source"}`,
        `URL: ${source.url ?? "No URL returned"}`,
        `Snippet: ${source.snippet ?? "No snippet returned"}`,
      ].join("\n");
    })
    .join("\n\n");
}

function pathChoicesForDecision(decision: ProxyRouteDecisionResponse) {
  const choices = new Set<string>();

  if (decision.recommended_route === "local_route") {
    choices.add("Accept local");
  }

  if (decision.recommended_route === "manual_route") {
    choices.add("Use manual prompt packet");
  }

  if (decision.recommended_route === "api_route") {
    choices.add("Escalate to cloud");
  }

  choices.add("Accept local");
  choices.add("Escalate to cloud");
  choices.add("Ask for more info");

  return Array.from(choices);
}

function isProxyFeatureFlagOff(message: string) {
  return message.includes("SPIRIT_CODING_USE_PROXY is not true");
}

function formatRiskTier(riskTier: string | undefined): ProxyMetrics["risk"] {
  if (riskTier === "high") {
    return "High";
  }

  if (riskTier === "medium") {
    return "Medium";
  }

  return "Low";
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const kilobytes = bytes / 1024;
  if (kilobytes < 1024) {
    return `${kilobytes.toFixed(1)} KB`;
  }

  return `${(kilobytes / 1024).toFixed(1)} MB`;
}

function fileExtension(name: string) {
  const extensionStart = name.lastIndexOf(".");
  return extensionStart === -1 ? "" : name.slice(extensionStart).toLowerCase();
}

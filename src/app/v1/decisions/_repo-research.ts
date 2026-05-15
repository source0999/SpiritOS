import { existsSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

type ResearchSource = {
  title?: string;
  url?: string;
  snippet?: string;
};

const maxRepoSourceBytes = 200_000;

const repoResearchPaths = [
  "src/app/coding/page.tsx",
  "src/components/coding/CodingAgentInterface.tsx",
  "masterProxyPlan.md",
  "refinedProxy.md",
  "source_proxy/decision/research.py",
  "source_proxy/decision/router.py",
  "source_proxy/decision/recommendation.py",
  "source_proxy/decision/prompt_packet.py",
  "source_proxy/decision/preview.py",
  "source_proxy/api/decision.py",
  "src/app/v1/decisions/route/route.ts",
  "src/app/v1/decisions/prompt-packet/route.ts",
  "src/lib/spirit/spirit-route-decision.ts",
  "src/lib/spirit/spirit-reasoning-patterns.ts",
];

const stopWords = new Set([
  "about",
  "after",
  "again",
  "before",
  "check",
  "could",
  "from",
  "have",
  "into",
  "latest",
  "please",
  "prompt",
  "should",
  "start",
  "that",
  "the",
  "this",
  "what",
  "when",
  "with",
  "would",
]);

const proxyAgentContext =
  "Coder Agent route selected. Start by scanning the repo context and implementing the fix directly. Only switch to a manual browser/editor prompt if the task is too large, too sensitive, or blocked by missing access.";

const proxyAgentConstraint =
  "Prefer running the Coder Agent implementation path before generating a manual prompt packet.";

const phaseLabel = "Phase 7C";
const incrementLabel = "Increment 7C.4";
const incrementGoal =
  "Add stronger self-correction: check if the agent is being passive, confirm repo-first research ran, and confirm the active phase.";
const activeIncrementContext = `Active work: ${phaseLabel} / ${incrementLabel}. Goal: ${incrementGoal}`;

function taskMentionsActiveIncrement(task: string) {
  const normalized = task.toLowerCase();
  return (
    normalized.includes("phase 7c") ||
    normalized.includes("increment 7c") ||
    normalized.includes("7c.4")
  );
}

export function mergeRepoFirstResearchSources(
  requestBodyText: string,
  responseBodyText: string,
) {
  let requestPayload: unknown;
  let responsePayload: unknown;

  try {
    requestPayload = JSON.parse(requestBodyText);
    responsePayload = JSON.parse(responseBodyText);
  } catch {
    return responseBodyText;
  }

  if (!isRecord(requestPayload) || !isRecord(responsePayload)) {
    return responseBodyText;
  }

  const task = typeof requestPayload.task === "string" ? requestPayload.task : "";
  if (!needsRepoFirstResearch(task, requestPayload)) {
    return responseBodyText;
  }

  const repoSources = buildRepoResearchSources(task, 6);
  if (repoSources.length === 0) {
    return responseBodyText;
  }

  const mergedSources = mergeSources(repoSources, readSources(responsePayload.research_sources));
  responsePayload.research_sources = mergedSources;

  if (isRecord(responsePayload.route_decision)) {
    responsePayload.route_decision.research_sources = mergedSources;
    responsePayload.route_decision.research_recommended = true;
    responsePayload.route_decision.reason_codes = mergeReasonCodes(
      responsePayload.route_decision.reason_codes,
      "repo_first_research",
    );
    applyProxyAgentRouteFallback(requestPayload, responsePayload.route_decision);
    applySelfCorrectionChecks(requestPayload, responsePayload.route_decision);
    applyProxyAgentPromptFallback(requestPayload, responsePayload);
  } else {
    responsePayload.reason_codes = mergeReasonCodes(responsePayload.reason_codes, "repo_first_research");
    applyProxyAgentRouteFallback(requestPayload, responsePayload);
    applySelfCorrectionChecks(requestPayload, responsePayload);
    applyProxyAgentPromptFallback(requestPayload, responsePayload);
  }

  responsePayload.research_recommended = true;
  if (taskMentionsActiveIncrement(task)) {
    responsePayload.phase_label ??= phaseLabel;
    responsePayload.increment_label ??= incrementLabel;
    responsePayload.increment_goal ??= incrementGoal;
  }
  return JSON.stringify(responsePayload);
}

function applySelfCorrectionChecks(
  requestPayload: Record<string, unknown>,
  responsePayload: Record<string, unknown>,
) {
  const task = typeof requestPayload.task === "string" ? requestPayload.task : "";
  const reasonCodes = Array.isArray(responsePayload.reason_codes)
    ? responsePayload.reason_codes.filter((item): item is string => typeof item === "string")
    : [];
  const codebaseLike = needsRepoFirstResearch(task, requestPayload);
  const proactiveAgentRequired = requiresProactiveAgentRoute(responsePayload.task_classification);
  const route = typeof responsePayload.recommended_route === "string" ? responsePayload.recommended_route : "";
  responsePayload.self_correction_checks = [
    {
      id: "passive_check",
      question: "Am I being passive?",
      passed: proactiveAgentRequired || !codebaseLike || route === "local_route",
      answer:
        proactiveAgentRequired
          ? "No. This is a coding/debugging task. A proactive agent route is required."
          : codebaseLike && route === "local_route"
          ? "No. This task is routed to Coder Agent first."
          : codebaseLike
            ? "Yes. Coding/debugging work should start with Coder Agent."
            : "This is not a coding/debugging task, so a non-agent route is acceptable.",
    },
    {
      id: "repo_first_check",
      question: "Did I scan the repo first?",
      passed: !codebaseLike || reasonCodes.includes("repo_first_research"),
      answer:
        codebaseLike && reasonCodes.includes("repo_first_research")
          ? "Yes. Repository sources are gathered before web sources."
          : codebaseLike
            ? "No. Add repo_first_research before relying on external sources."
            : "Repo-first research is not required for this prompt.",
    },
    {
      id: "phase_check",
      question: "Am I on the correct phase?",
      passed: true,
      answer: taskMentionsActiveIncrement(task)
        ? `Yes. Use ${phaseLabel} / ${incrementLabel} for this self-correction pass.`
        : "No active phase was specified in this task; do not inherit one from prior runs.",
    },
  ];
}

function requiresProactiveAgentRoute(classification: unknown) {
  const normalized = typeof classification === "string" ? classification.toLowerCase() : "";
  return ["implementation", "codebase", "codebase_analysis", "codebase_intent"].includes(
    normalized,
  );
}

function buildRepoResearchSources(task: string, maxResults: number) {
  const root = /* turbopackIgnore: true */ process.cwd();
  const terms = queryTerms(task);
  const scoredSources: Array<{ priority: number; score: number; source: ResearchSource }> = [];

  repoResearchPaths.forEach((relativePath, priority) => {
    const filePath = path.join(/* turbopackIgnore: true */ root, relativePath);
    if (!isReadableRepoFile(filePath)) {
      return;
    }

    const content = readFileSync(filePath, "utf8");
    const score = scoreRepoFile(relativePath, content, task, terms);
    if (score <= 0) {
      return;
    }

    scoredSources.push({
      priority,
      score,
      source: {
        title: `Repo: ${relativePath}`,
        url: `repo://${relativePath}`,
        snippet: repoSnippet(relativePath, content, terms),
      },
    });
  });

  return scoredSources
    .sort((left, right) => right.score - left.score || left.priority - right.priority)
    .slice(0, Math.max(1, Math.min(maxResults, 12)))
    .map((item) => item.source);
}

function needsRepoFirstResearch(task: string, requestPayload: Record<string, unknown>) {
  const normalized = task.toLowerCase();
  return (
    requestPayload.research_recommended === true ||
    requestPayload.needs_codebase_context === true ||
    [
      "/coding",
      "coding page",
      "history bug",
      "bug",
      "debug",
      "fix",
      "route",
      "router",
      "endpoint",
      "decision",
      "prompt packet",
      "source proxy",
      "source_proxy",
      "phase",
      "increment",
      "repo",
      "codebase",
      "component",
      "hook",
    ].some((term) => normalized.includes(term))
  );
}

function isReadableRepoFile(filePath: string) {
  try {
    if (!existsSync(/* turbopackIgnore: true */ filePath)) {
      return false;
    }
    const fileStat = statSync(/* turbopackIgnore: true */ filePath);
    return fileStat.isFile() && fileStat.size <= maxRepoSourceBytes;
  } catch {
    return false;
  }
}

function queryTerms(task: string) {
  const matches = task.toLowerCase().match(/[a-z0-9_/-]+/gi) ?? [];
  return Array.from(
    new Set(
      matches
        .map((term) => term.replace(/^[/_-]+|[/_-]+$/g, ""))
        .filter((term) => term.length >= 3 && !stopWords.has(term)),
    ),
  ).slice(0, 24);
}

function scoreRepoFile(relativePath: string, content: string, task: string, terms: string[]) {
  const normalizedTask = task.toLowerCase();
  const normalizedPath = relativePath.toLowerCase().replaceAll("\\", "/");
  const normalizedContent = content.toLowerCase();
  let score = 0;

  terms.forEach((term) => {
    if (normalizedPath.includes(term)) {
      score += 8;
    }
    if (normalizedContent.includes(term)) {
      score += Math.min(normalizedContent.split(term).length - 1, 6);
    }
  });

  if (normalizedTask.includes("/coding") || normalizedTask.includes("coding page")) {
    if (
      normalizedPath === "src/app/coding/page.tsx" ||
      normalizedPath === "src/components/coding/codingagentinterface.tsx"
    ) {
      score += 18;
    }
  }
  if (normalizedTask.includes("history") && normalizedPath.includes("codingagentinterface")) {
    score += 12;
  }
  if (normalizedTask.includes("bug") && /\.(tsx?|py)$/u.test(normalizedPath)) {
    score += 3;
  }
  if (normalizedTask.includes("decision") && normalizedPath.includes("decision")) {
    score += 14;
  }
  if (normalizedTask.includes("research") && normalizedPath.includes("research.py")) {
    score += 18;
  }
  if ((normalizedTask.includes("router") || normalizedTask.includes("route")) && (normalizedPath.includes("router.py") || normalizedPath.includes("/route/"))) {
    score += 14;
  }
  if (
    (normalizedTask.includes("plan") || normalizedTask.includes("phase") || normalizedTask.includes("increment")) &&
    (normalizedPath === "masterproxyplan.md" || normalizedPath === "refinedproxy.md")
  ) {
    score += 12;
  }

  return score;
}

function repoSnippet(relativePath: string, content: string, terms: string[]) {
  const matchedLines: string[] = [];
  content.split(/\r?\n/u).forEach((line, index) => {
    if (matchedLines.length >= 3) {
      return;
    }
    const loweredLine = line.toLowerCase();
    if (terms.length > 0 && !terms.some((term) => loweredLine.includes(term))) {
      return;
    }
    const cleanLine = line.trim().replace(/\s+/gu, " ").slice(0, 500);
    if (cleanLine) {
      matchedLines.push(`L${index + 1}: ${cleanLine}`);
    }
  });

  if (matchedLines.length > 0) {
    return `Matched repo lines: ${matchedLines.join(" | ")}`;
  }
  return `Relevant repository file selected for local-first research: ${relativePath}`;
}

function readSources(value: unknown) {
  return Array.isArray(value) ? value.filter(isRecord).map((source) => source as ResearchSource) : [];
}

function mergeSources(repoSources: ResearchSource[], existingSources: ResearchSource[]) {
  const seen = new Set<string>();
  return [...repoSources, ...existingSources]
    .filter((source) => {
      const key = source.url || source.title || "";
      if (!key || seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    })
    .slice(0, 12);
}

function mergeReasonCodes(value: unknown, reasonCode: string) {
  const reasonCodes = Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
  return reasonCodes.includes(reasonCode) ? reasonCodes : [...reasonCodes, reasonCode];
}

function applyProxyAgentRouteFallback(
  requestPayload: Record<string, unknown>,
  responsePayload: Record<string, unknown>,
) {
  const wantsImplementation =
    requestPayload.wants_implementation === true || responsePayload.task_classification === "implementation";
  const needsCodebaseContext =
    requestPayload.needs_codebase_context === true || responsePayload.task_classification === "codebase_analysis";
  const contextEstimate = isRecord(responsePayload.context_estimate) ? responsePayload.context_estimate : {};
  const sizeClass = typeof contextEstimate.size_class === "string" ? contextEstimate.size_class : "";
  const reasonCodes = Array.isArray(responsePayload.reason_codes)
    ? responsePayload.reason_codes.filter((item): item is string => typeof item === "string")
    : [];
  const isSensitive = requestPayload.sensitive === true || reasonCodes.includes("sensitive_or_secret_risk");

  if (responsePayload.task_classification === "implementation") {
    responsePayload.recommended_route = "local_route";
    responsePayload.next_prompt_action = "run_with_coder_agent";
    return;
  }

  if (
    !isSensitive &&
    sizeClass !== "large" &&
    sizeClass !== "huge" &&
    (wantsImplementation || needsCodebaseContext || reasonCodes.includes("repo_first_research"))
  ) {
    if (responsePayload.task_classification === "general_reasoning") {
      responsePayload.task_classification = needsCodebaseContext ? "codebase_analysis" : "implementation";
    }
    responsePayload.recommended_route = "local_route";
    responsePayload.next_prompt_action = "run_with_coder_agent";
  }
}

function applyProxyAgentPromptFallback(
  requestPayload: Record<string, unknown>,
  responsePayload: Record<string, unknown>,
) {
  const task = typeof requestPayload.task === "string" ? requestPayload.task : "";
  const wantsImplementation = requestPayload.wants_implementation === true;
  const needsCodebaseContext = requestPayload.needs_codebase_context === true;
  if (!wantsImplementation && !needsCodebaseContext && !needsRepoFirstResearch(task, requestPayload)) {
    return;
  }

  const relevantContext = responsePayload.relevant_context;
  const includeActiveIncrement = taskMentionsActiveIncrement(task);
  if (typeof relevantContext === "string") {
    let nextRelevantContext = relevantContext;
    if (includeActiveIncrement && !nextRelevantContext.includes(`${phaseLabel} / ${incrementLabel}`)) {
      nextRelevantContext = `${activeIncrementContext}\n\n${nextRelevantContext}`;
    }
    if (!nextRelevantContext.includes("Coder Agent route selected")) {
      nextRelevantContext = `${proxyAgentContext}\n\n${nextRelevantContext}`;
    }
    responsePayload.relevant_context = nextRelevantContext;
  } else {
    responsePayload.relevant_context = includeActiveIncrement
      ? `${activeIncrementContext}\n\n${proxyAgentContext}`
      : proxyAgentContext;
  }

  const constraints = Array.isArray(responsePayload.constraints)
    ? responsePayload.constraints.filter((item): item is string => typeof item === "string")
    : [];
  responsePayload.constraints = [
    ...(includeActiveIncrement ? [`Name ${phaseLabel} / ${incrementLabel} in the answer.`] : []),
    "Do not inherit target files, diffs, routes, phase labels, or approval state from previous runs.",
    "Use simple, direct language.",
    "When possible, show concrete file paths and the exact code changes to make.",
    proxyAgentConstraint,
    ...constraints,
  ].filter((item, index, all) => all.indexOf(item) === index);

  if (
    includeActiveIncrement &&
    typeof responsePayload.prompt_text === "string" &&
    !responsePayload.prompt_text.includes(proxyAgentContext)
  ) {
    responsePayload.prompt_text = responsePayload.prompt_text.replace(
      "## Relevant Context\n",
      `## Relevant Context\n${activeIncrementContext}\n\n${proxyAgentContext}\n\n`,
    );
  }
  if (typeof responsePayload.prompt_text === "string" && !responsePayload.prompt_text.includes("Concrete code changes")) {
    responsePayload.prompt_text = responsePayload.prompt_text.replace(
      "## Requested Output\n",
      "## Requested Output\n- Concrete code changes or diff-style bullets when possible\n",
    );
  }
  if (
    includeActiveIncrement &&
    typeof responsePayload.prompt_text === "string" &&
    !responsePayload.prompt_text.includes("## Active Increment")
  ) {
    responsePayload.prompt_text = responsePayload.prompt_text.replace(
      "## Task\n",
      `## Active Increment\n${phaseLabel} / ${incrementLabel}\n\nGoal: ${incrementGoal}\n\n## Task\n`,
    );
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

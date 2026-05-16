"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Check,
  ClipboardCheck,
  FileCheck2,
  FileDiff,
  GitPullRequestDraft,
  MessageSquareText,
  ShieldCheck,
  X,
} from "lucide-react";

type ProposalStatus =
  | "detected"
  | "drafted"
  | "pending_review"
  | "approved"
  | "rejected"
  | "applied"
  | "commit_pending"
  | "commit_approved"
  | "push_pending"
  | "push_approved"
  | "pushed"
  | "failed"
  | string;

type ProposalRecord = {
  proposal_id: string;
  project_id: string;
  status: ProposalStatus;
  type: string;
  component: string;
  requires_approval: boolean;
  title?: string | null;
  affected_blueprints: string[];
  changed_files: string[];
  proposed_files: string[];
  diff_preview?: string | null;
  confidence?: string | null;
  rationale?: string | null;
  risk?: "low" | "medium" | "high" | "unknown" | string | null;
  rejection_reason?: string | null;
  generated?: boolean;
  persisted?: boolean;
  applied?: boolean;
  action_taken?: boolean;
  deduped?: boolean;
};

type ProposalsPayload = {
  status: "observing" | "unavailable" | string;
  write_actions_enabled: boolean;
  proposals: ProposalRecord[];
  proposal_count: number;
  pending_proposals: number;
  actions_taken: boolean;
  deduped?: boolean | null;
  duplicate_proposals_present?: number | null;
  duplicate_proposals_suppressed?: number | null;
  error?: string;
};

type ReviewDecision = {
  status: "approved" | "rejected" | "edit_requested";
  reason?: string;
};

type FetchState = "loading" | "ready" | "error";
type ApplyState = "idle" | "applying" | "applied" | "error";
type ReviewState = "idle" | "recording" | "error";

const emptyPayload: ProposalsPayload = {
  status: "unavailable",
  write_actions_enabled: false,
  proposals: [],
  proposal_count: 0,
  pending_proposals: 0,
  actions_taken: false,
};

function statusLabel(state: FetchState, payload: ProposalsPayload): string {
  if (state === "loading") return "Loading";
  if (state === "error" || payload.status === "unavailable") return "Unavailable";
  return "Review";
}

function countByStatus(proposals: ProposalRecord[], status: ProposalStatus): number {
  return proposals.filter((proposal) => proposal.status === status).length;
}

function proposalTitle(proposal: ProposalRecord): string {
  return proposal.title ?? `${proposal.component} ${proposal.type.replaceAll("_", " ")}`;
}

function firstProposal(proposals: ProposalRecord[]): ProposalRecord | null {
  return (
    proposals.find((proposal) => proposal.status === "pending_review") ??
    proposals.find((proposal) => proposal.status === "drafted") ??
    proposals[0] ??
    null
  );
}

function pendingProposalCount(proposals: ProposalRecord[]): number {
  return proposals.filter((proposal) =>
    ["detected", "drafted", "pending_review"].includes(proposal.status),
  ).length;
}

function proposalRisk(proposal: ProposalRecord): string {
  if (proposal.risk) return proposal.risk;
  const paths = [...proposal.changed_files, ...proposal.proposed_files].map((path) =>
    path.toLowerCase(),
  );
  if (
    paths.some(
      (path) =>
        path.includes("/apply") ||
        path.includes("/approval") ||
        path.includes("/commit") ||
        path.includes("/push") ||
        path.includes("/safety") ||
        path.includes("secret") ||
        path.includes("token") ||
        path.includes(".env"),
    )
  ) {
    return "high";
  }
  if (paths.some((path) => path.startsWith("src/") || path.startsWith("source_proxy/"))) {
    return "medium";
  }
  if (paths.some((path) => path.startsWith("_blueprints/") || path.startsWith("docs/"))) {
    return "low";
  }
  return "unknown";
}

function manualCheckCommand(proposal: ProposalRecord): string {
  const paths = [...proposal.changed_files, ...proposal.proposed_files];
  if (paths.some((path) => path.startsWith("source_proxy/"))) {
    return "PYTHONPATH=. python -m pytest source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py";
  }
  if (paths.some((path) => path.startsWith("src/components/dashboard/"))) {
    return "npx vitest run src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx";
  }
  if (paths.some((path) => path.startsWith("_blueprints/"))) {
    return "npm run validate:blueprints";
  }
  return "git status --short";
}

function proposalSourceLabel(proposal: ProposalRecord): string {
  if (proposal.generated && !proposal.persisted) return "generated draft";
  if (proposal.persisted) return "persisted";
  return "review only";
}

function expectedOutcome(proposal: ProposalRecord): string {
  if (proposal.status === "approved") {
    return "Only the approved blueprint doc can be applied; no commit or push runs here.";
  }
  if (proposal.status === "applied") {
    return "The approved docs are applied; commit and push stay in separate approval lanes.";
  }
  if (proposal.status === "rejected") {
    return "Rejected proposals remain recorded and should not return as pending duplicates.";
  }
  return "Review records a decision only; apply, commit, and push remain blocked until separately approved.";
}

function nextStep(proposal: ProposalRecord): string {
  if (proposal.status === "approved") return "Apply approved docs, then review verification.";
  if (proposal.status === "applied") return "Review commit proposals before approving any commit.";
  if (proposal.status === "rejected") return "Leave rejected unless the implementation changes materially.";
  return "Approve, reject, or request edit after the manual check passes.";
}

export function HomelabBlueprintReviewWidget() {
  const [state, setState] = useState<FetchState>("loading");
  const [payload, setPayload] = useState<ProposalsPayload>(emptyPayload);
  const [selectedProposalId, setSelectedProposalId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [decisions, setDecisions] = useState<Record<string, ReviewDecision>>({});
  const [reviewState, setReviewState] = useState<ReviewState>("idle");
  const [applyState, setApplyState] = useState<ApplyState>("idle");
  const [applyMessage, setApplyMessage] = useState("");

  async function refreshProposals(): Promise<ProposalsPayload> {
    const response = await fetch("/v1/cartographer/proposals", {
      cache: "no-store",
    });
    const nextPayload = (await response.json()) as ProposalsPayload;
    const normalized = {
      ...emptyPayload,
      ...nextPayload,
      proposals: Array.isArray(nextPayload.proposals) ? nextPayload.proposals : [],
    };
    setPayload(normalized);
    setState(response.ok && nextPayload.status !== "unavailable" ? "ready" : "error");
    return normalized;
  }

  useEffect(() => {
    let cancelled = false;

    async function loadProposals() {
      try {
        const nextPayload = await refreshProposals();
        if (cancelled) return;
        setSelectedProposalId((current) => current ?? firstProposal(nextPayload.proposals)?.proposal_id ?? null);
      } catch {
        if (cancelled) return;
        setPayload(emptyPayload);
        setState("error");
      }
    }

    void loadProposals();

    return () => {
      cancelled = true;
    };
  }, []);

  const counts = useMemo(
    () => [
      ["Pending", payload.pending_proposals],
      ["Approved", countByStatus(payload.proposals, "approved")],
      ["Rejected", countByStatus(payload.proposals, "rejected")],
      ["Applied", countByStatus(payload.proposals, "applied")],
      ["Push pending", countByStatus(payload.proposals, "push_pending")],
    ] as const,
    [payload],
  );

  const activeProposal =
    payload.proposals.find((proposal) => proposal.proposal_id === selectedProposalId) ??
    firstProposal(payload.proposals);
  const activeDecision = activeProposal ? decisions[activeProposal.proposal_id] : null;

  async function stageDecision(status: ReviewDecision["status"]) {
    if (!activeProposal) return;
    const reason =
      status === "rejected"
        ? window.prompt("Reason for rejecting this blueprint proposal?", "Needs a narrower diff.")
        : status === "edit_requested"
          ? window.prompt("What edit should Cartographer make?", "Tighten the proposed note.")
          : null;
    if ((status === "rejected" || status === "edit_requested") && reason === null) return;

    setReviewState("recording");
    setApplyMessage("");
    try {
      const response = await fetch(
        `/v1/cartographer/proposals/${encodeURIComponent(activeProposal.proposal_id)}/review`,
        {
          body: JSON.stringify({
            actor: "dashboard-blueprint-review",
            decision:
              status === "approved" ? "approve" : status === "rejected" ? "reject" : "request_edit",
            proposal: activeProposal,
            reason: reason || undefined,
          }),
          headers: {
            "content-type": "application/json",
          },
          method: "POST",
        },
      );
      const result = (await response.json()) as {
        proposal?: ProposalRecord;
        detail?: { message?: string };
      };
      if (!response.ok || !result.proposal) {
        throw new Error(result.detail?.message ?? "Blueprint review decision failed.");
      }
      const nextPayload = await refreshProposals();
      if (!nextPayload.proposals.some((proposal) => proposal.proposal_id === activeProposal.proposal_id)) {
        setSelectedProposalId(firstProposal(nextPayload.proposals)?.proposal_id ?? null);
      }
      setDecisions((current) => ({
        ...current,
        [activeProposal.proposal_id]: {
          status,
          reason: reason || undefined,
        },
      }));
      setReviewState("idle");
    } catch (error) {
      setReviewState("error");
      setApplyMessage(error instanceof Error ? error.message : "Blueprint review decision failed.");
    }
  }

  async function applyApprovedDocs() {
    if (!activeProposal || activeProposal.status !== "approved") return;
    setApplyState("applying");
    setApplyMessage("");
    try {
      const response = await fetch(
        `/v1/cartographer/proposals/${encodeURIComponent(activeProposal.proposal_id)}/apply-approved`,
        {
          body: JSON.stringify({
            approved: true,
            approved_by: "dashboard-blueprint-review",
          }),
          headers: {
            "content-type": "application/json",
          },
          method: "POST",
        },
      );
      const result = (await response.json()) as {
        applied_files?: string[];
        detail?: { message?: string };
        verification?: { status?: string };
      };
      if (!response.ok) {
        throw new Error(result.detail?.message ?? "Approved doc apply failed.");
      }
      setApplyState("applied");
      setApplyMessage(
        `Proposal applied: ${(result.applied_files ?? activeProposal.proposed_files).join(", ")}`,
      );
      await refreshProposals();
    } catch (error) {
      setApplyState("error");
      setApplyMessage(error instanceof Error ? error.message : "Approved doc apply failed.");
    }
  }

  return (
    <section
      aria-label="Blueprint Review"
      className="dashboard-demo-v4-glass-pearl dashboard-demo-v4-blueprint-review-card"
    >
      <div className="dashboard-demo-v4-card-header">
        <div className="dashboard-demo-v4-card-title-row">
          <span className="dashboard-demo-v4-icon-tile" aria-hidden>
            <GitPullRequestDraft className="h-5 w-5" />
          </span>
          <div>
            <p className="dashboard-demo-v4-eyebrow">Cartographer queue</p>
            <h2>Blueprint Review</h2>
          </div>
        </div>
        <span className="dashboard-demo-v4-demo-label">{statusLabel(state, payload)}</span>
      </div>

      <div className="dashboard-demo-v4-blueprint-review-counts" aria-label="Blueprint review counts">
        {counts.map(([label, value]) => (
          <div key={label}>
            <strong>{value}</strong>
            <span>{label}</span>
          </div>
        ))}
      </div>

      <div className="dashboard-demo-v4-blueprint-review-trust" aria-label="Blueprint review trust status">
        <span data-tone={payload.write_actions_enabled ? "warning" : "safe"}>
          <ShieldCheck className="h-4 w-4" aria-hidden />
          {payload.write_actions_enabled ? "Writes require approval" : "Review lane only"}
        </span>
        <span data-tone={(payload.duplicate_proposals_present ?? 0) > 0 ? "warning" : "safe"}>
          <FileDiff className="h-4 w-4" aria-hidden />
          {payload.deduped === false
            ? `${payload.duplicate_proposals_present ?? 0} duplicates`
            : "Stable proposal queue"}
        </span>
        <span data-tone="warning">
          <AlertTriangle className="h-4 w-4" aria-hidden />
          Commit and push approvals are separate
        </span>
      </div>

      {state === "loading" ? (
        <p className="dashboard-demo-v4-scout-empty">Loading blueprint proposals.</p>
      ) : activeProposal ? (
        <>
          <div className="dashboard-demo-v4-blueprint-review-queue" aria-label="Proposal review cards">
            {payload.proposals.slice(0, 8).map((proposal) => {
              const selected = proposal.proposal_id === activeProposal.proposal_id;
              return (
                <button
                  key={proposal.proposal_id}
                  type="button"
                  className="dashboard-demo-v4-blueprint-review-card-button"
                  data-selected={selected ? "true" : "false"}
                  onClick={() => {
                    setSelectedProposalId(proposal.proposal_id);
                    setExpanded(false);
                    setApplyState("idle");
                    setApplyMessage("");
                  }}
                >
                  <span>
                    <strong>{proposalTitle(proposal)}</strong>
                    <em>{proposal.proposal_id}</em>
                  </span>
                  <span className="dashboard-demo-v4-blueprint-review-card-meta">
                    <b>{proposal.status}</b>
                    <b>{proposalRisk(proposal)} risk</b>
                    <b>{proposal.component}</b>
                  </span>
                  <small>
                    {proposal.changed_files.length} changed / {proposal.proposed_files.length} proposed
                  </small>
                </button>
              );
            })}
          </div>

          <article className="dashboard-demo-v4-blueprint-review-proposal">
          <div className="dashboard-demo-v4-blueprint-review-heading">
            <div>
              <strong>{proposalTitle(activeProposal)}</strong>
              <span>{activeProposal.proposal_id}</span>
            </div>
            <em>{activeProposal.status}</em>
          </div>

          <div className="dashboard-demo-v4-blueprint-review-meta">
            <span>Project {activeProposal.project_id}</span>
            <span>Component {activeProposal.component}</span>
            <span>Risk {proposalRisk(activeProposal)}</span>
            <span>Confidence {activeProposal.confidence ?? "pending"}</span>
            <span>{proposalSourceLabel(activeProposal)}</span>
          </div>

          <p>{activeProposal.rationale ?? "Review the proposed blueprint update before approval."}</p>

          <div className="dashboard-demo-v4-blueprint-review-verification" aria-label="Manual verification">
            <div>
              <span>
                <ClipboardCheck className="h-4 w-4" aria-hidden />
                Manual check
              </span>
              <code>{manualCheckCommand(activeProposal)}</code>
            </div>
            <div>
              <span>
                <Check className="h-4 w-4" aria-hidden />
                Expected outcome
              </span>
              <p>{expectedOutcome(activeProposal)}</p>
            </div>
            <div>
              <span>
                <GitPullRequestDraft className="h-4 w-4" aria-hidden />
                Next step
              </span>
              <p>{nextStep(activeProposal)}</p>
            </div>
          </div>

          <div className="dashboard-demo-v4-scout-tags" aria-label="Affected blueprint files">
            {activeProposal.proposed_files.slice(0, 4).map((file) => (
              <span key={file}>{file}</span>
            ))}
          </div>

          <div className="dashboard-demo-v4-scout-tags" aria-label="Changed files">
            {activeProposal.changed_files.slice(0, 4).map((file) => (
              <span key={file}>{file}</span>
            ))}
          </div>

          <button
            className="dashboard-demo-v4-blueprint-review-diff-toggle"
            type="button"
            onClick={() => setExpanded((value) => !value)}
          >
            <FileDiff className="h-4 w-4" aria-hidden />
            {expanded ? "Hide diff preview" : "Expand diff preview"}
          </button>

          {expanded ? (
            <pre className="dashboard-demo-v4-blueprint-review-diff">
              <code>{activeProposal.diff_preview ?? "No diff preview available."}</code>
            </pre>
          ) : null}

          <div className="dashboard-demo-v4-scout-actions">
            {activeProposal.status === "approved" ? (
              <div className="dashboard-demo-v4-blueprint-review-approval-lane">
                <span>Approved docs lane</span>
                <button
                  type="button"
                  onClick={applyApprovedDocs}
                  disabled={applyState === "applying" || applyState === "applied"}
                >
                  <FileCheck2 className="h-4 w-4" aria-hidden />
                  {applyState === "applying" ? "Applying docs" : "Apply approved docs"}
                </button>
              </div>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => void stageDecision("approved")}
                  disabled={reviewState === "recording"}
                >
                  <Check className="h-4 w-4" aria-hidden />
                  {reviewState === "recording" ? "Recording" : "Approve"}
                </button>
                <button
                  type="button"
                  onClick={() => void stageDecision("rejected")}
                  disabled={reviewState === "recording"}
                >
                  <X className="h-4 w-4" aria-hidden />
                  Reject
                </button>
                <button
                  type="button"
                  onClick={() => void stageDecision("edit_requested")}
                  disabled={reviewState === "recording"}
                >
                  <MessageSquareText className="h-4 w-4" aria-hidden />
                  Request edit
                </button>
              </>
            )}
          </div>

          {applyMessage ? (
            <p
              className={
                applyState === "error"
                  ? "dashboard-demo-v4-scout-action-error"
                  : "dashboard-demo-v4-scout-action-message"
              }
            >
              {applyMessage}
            </p>
          ) : null}

          {activeDecision ? (
            <p className="dashboard-demo-v4-scout-action-message">
              {activeDecision.status === "approved"
                ? "Proposal approved from Dashboard. No apply, commit, or push ran."
                : `${activeDecision.status.replace("_", " ")} staged: ${activeDecision.reason}`}
            </p>
          ) : null}
          </article>
        </>
      ) : (
        <p className="dashboard-demo-v4-scout-empty">
          {payload.error ?? "No blueprint proposals waiting for review."}
        </p>
      )}
    </section>
  );
}

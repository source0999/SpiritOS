"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, FileCheck2, FileDiff, GitPullRequestDraft, MessageSquareText, X } from "lucide-react";

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
  rejection_reason?: string | null;
  generated?: boolean;
  persisted?: boolean;
  applied?: boolean;
  action_taken?: boolean;
};

type ProposalsPayload = {
  status: "observing" | "unavailable" | string;
  write_actions_enabled: boolean;
  proposals: ProposalRecord[];
  proposal_count: number;
  pending_proposals: number;
  actions_taken: boolean;
  error?: string;
};

type ReviewDecision = {
  status: "approved" | "rejected" | "edit_requested";
  reason?: string;
};

type FetchState = "loading" | "ready" | "error";
type ApplyState = "idle" | "applying" | "applied" | "error";

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

export function HomelabBlueprintReviewWidget() {
  const [state, setState] = useState<FetchState>("loading");
  const [payload, setPayload] = useState<ProposalsPayload>(emptyPayload);
  const [expanded, setExpanded] = useState(false);
  const [decisions, setDecisions] = useState<Record<string, ReviewDecision>>({});
  const [applyState, setApplyState] = useState<ApplyState>("idle");
  const [applyMessage, setApplyMessage] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadProposals() {
      try {
        const response = await fetch("/v1/cartographer/proposals", {
          cache: "no-store",
        });
        const nextPayload = (await response.json()) as ProposalsPayload;
        if (cancelled) return;
        setPayload({
          ...emptyPayload,
          ...nextPayload,
          proposals: Array.isArray(nextPayload.proposals) ? nextPayload.proposals : [],
        });
        setState(response.ok && nextPayload.status !== "unavailable" ? "ready" : "error");
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

  const activeProposal = firstProposal(payload.proposals);
  const activeDecision = activeProposal ? decisions[activeProposal.proposal_id] : null;

  function stageDecision(status: ReviewDecision["status"]) {
    if (!activeProposal) return;
    const reason =
      status === "rejected"
        ? window.prompt("Reason for rejecting this blueprint proposal?", "Needs a narrower diff.")
        : status === "edit_requested"
          ? window.prompt("What edit should Cartographer make?", "Tighten the proposed note.")
          : null;
    if ((status === "rejected" || status === "edit_requested") && reason === null) return;

    setDecisions((current) => ({
      ...current,
      [activeProposal.proposal_id]: {
        status,
        reason: reason || undefined,
      },
    }));
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

      {state === "loading" ? (
        <p className="dashboard-demo-v4-scout-empty">Loading blueprint proposals.</p>
      ) : activeProposal ? (
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
            <span>Confidence {activeProposal.confidence ?? "pending"}</span>
          </div>

          <p>{activeProposal.rationale ?? "Review the proposed blueprint update before approval."}</p>

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
              <button
                type="button"
                onClick={applyApprovedDocs}
                disabled={applyState === "applying" || applyState === "applied"}
              >
                <FileCheck2 className="h-4 w-4" aria-hidden />
                {applyState === "applying" ? "Applying docs" : "Apply approved docs"}
              </button>
            ) : (
              <>
                <button type="button" onClick={() => stageDecision("approved")}>
                  <Check className="h-4 w-4" aria-hidden />
                  Approve
                </button>
                <button type="button" onClick={() => stageDecision("rejected")}>
                  <X className="h-4 w-4" aria-hidden />
                  Reject
                </button>
                <button type="button" onClick={() => stageDecision("edit_requested")}>
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
                ? "Approval staged for review. No apply, commit, or push ran."
                : `${activeDecision.status.replace("_", " ")} staged: ${activeDecision.reason}`}
            </p>
          ) : null}
        </article>
      ) : (
        <p className="dashboard-demo-v4-scout-empty">
          {payload.error ?? "No blueprint proposals waiting for review."}
        </p>
      )}
    </section>
  );
}

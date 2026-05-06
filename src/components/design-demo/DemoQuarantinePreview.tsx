// ── DemoQuarantinePreview - experimental cards lab (visual-only) ─────────────
// > All cards are mock; nothing here mounts real experimental code.
// > The host route /quarantine is untouched - see optional safe link below.
import type { ReactElement } from "react";
import Link from "next/link";

import {
  ArrowRightIcon,
  ChatIcon,
  FlaskIcon,
  LinkIcon,
  ShieldIcon,
  SparkleIcon,
  ActivityIcon,
} from "./DemoIcons";

type Lab = {
  title: string;
  subtitle: string;
  status: "draft" | "queued" | "wip";
  Icon: (p: { size?: number }) => ReactElement;
};

const labs: Lab[] = [
  {
    title: "Deep Research",
    subtitle:
      "Multi-step plan + cite + dossier export. Researcher mode hardened.",
    status: "wip",
    Icon: ShieldIcon,
  },
  {
    title: "RAG · local",
    subtitle:
      "Folder-watch ingest → vector store → retrieve. Sovereign embeddings.",
    status: "queued",
    Icon: SparkleIcon,
  },
  {
    title: "Model Lab",
    subtitle:
      "Hot-swap models · Hermes / Dolphin / Llama. Side-by-side replies.",
    status: "queued",
    Icon: FlaskIcon,
  },
  {
    title: "Local Agent",
    subtitle:
      "Tool-use loop · web search, shell, file access. Capability gated.",
    status: "draft",
    Icon: ActivityIcon,
  },
  {
    title: "Terminal Mode",
    subtitle:
      "Fullscreen TUI · monochrome · mono everything · ssh-pipe friendly.",
    status: "draft",
    Icon: ChatIcon,
  },
  {
    title: "Sigil Editor",
    subtitle:
      "Compose Spirit modes as composable prompt sigils. Save & share.",
    status: "draft",
    Icon: LinkIcon,
  },
];

const statusToBadge = {
  wip: "demo-badge--emerald",
  queued: "demo-badge--cyan",
  draft: "demo-badge--warn",
} as const;

const statusToLabel = {
  wip: "WIP",
  queued: "Queued",
  draft: "Draft",
} as const;

export function DemoQuarantinePreview() {
  return (
    <section
      id="demo-quarantine"
      className="demo-section"
      aria-labelledby="demo-quarantine-title"
    >
      <header className="demo-section__header">
        <span
          className="demo-section__eyebrow"
          style={{
            color:
              "color-mix(in oklab, var(--demo-rose-strong) 90%, white)",
          }}
        >
          <FlaskIcon size={11} />
          Quarantine · lab
        </span>
        <h2 id="demo-quarantine-title" className="demo-section__title">
          Where noisy ideas get to think out loud.
        </h2>
        <p className="demo-section__lede">
          Containment for in-flight experiments. Nothing here is wired into
          production routes. The real lab page  - {" "}
          <Link
            href="/quarantine"
            className="demo-btn demo-btn--ghost demo-btn--sm"
            style={{ marginInline: "0.25rem" }}
          >
            /quarantine <ArrowRightIcon size={11} />
          </Link>{" "}
          - keeps its own layout.
        </p>
      </header>

      <div
        className="demo-banner"
        role="note"
        aria-label="Quarantine banner"
      >
        <span className="demo-banner__label">Quarantine only</span>
        <span>
          Demo cards. Future surfaces. None of these mount real code from the
          production app.
        </span>
      </div>

      <div className="demo-grid-3" aria-label="Lab experiments · mock">
        {labs.map((lab, i) => (
          <article
            key={lab.title}
            className={`demo-card demo-card--quarantine demo-motion-fade-up demo-motion-fade-up--delay-${
              Math.min(i + 1, 5)
            }`}
            aria-label={`${lab.title} · ${statusToLabel[lab.status]} · demo`}
          >
            <div className="demo-card__eyebrow">
              <lab.Icon size={12} />
              <span>{lab.title}</span>
            </div>
            <h3 className="demo-card__title">{lab.title}</h3>
            <p className="demo-card__body">{lab.subtitle}</p>
            <div className="demo-card__footer">
              <span className={`demo-badge ${statusToBadge[lab.status]}`}>
                {statusToLabel[lab.status]}
              </span>
              <span className="demo-mock-tag">Not wired</span>
            </div>
            <span className="demo-corners" aria-hidden="true" />
          </article>
        ))}
      </div>
    </section>
  );
}

export default DemoQuarantinePreview;

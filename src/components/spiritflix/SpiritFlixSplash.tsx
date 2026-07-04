import type { ReactNode } from "react";

export interface SpiritFlixLoadProgress {
  percent: number;
  label: string;
}

export function SpiritFlixSplash({
  message,
  action,
  progress,
  skeleton = false,
}: {
  message?: string;
  action?: ReactNode;
  progress?: SpiritFlixLoadProgress;
  skeleton?: boolean;
}) {
  const progressValue = Math.max(0, Math.min(100, Math.round(progress?.percent ?? 0)));
  const progressLabel = progress?.label ?? message;

  return (
    <section className={`spiritflix-restore ${skeleton ? "spiritflix-restore--overlay" : ""}`}>
      <div className="spiritflix-restore__panel">
        <div className="spiritflix-brand">
          <span className="spiritflix-brand__sigil">SF</span>
          <span>SpiritFlix</span>
        </div>
        {progress ? (
          <div className="spiritflix-load-progress" aria-label={progressLabel} aria-valuemin={0} aria-valuemax={100} aria-valuenow={progressValue} role="progressbar">
            <div className="spiritflix-load-progress__track">
              <span style={{ width: `${progressValue}%` }} />
            </div>
            <div className="spiritflix-load-progress__meta">
              <span>{progressLabel}</span>
              <strong>{progressValue}%</strong>
            </div>
          </div>
        ) : progressLabel ? (
          <p className="spiritflix-empty">{progressLabel}</p>
        ) : null}
        {skeleton ? (
          <div className="spiritflix-load-skeleton" aria-hidden="true">
            {Array.from({ length: 8 }, (_, index) => (
              <span key={index} />
            ))}
          </div>
        ) : null}
        {action}
      </div>
    </section>
  );
}

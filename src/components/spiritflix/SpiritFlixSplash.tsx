import type { ReactNode } from "react";

export function SpiritFlixSplash({
  message,
  action,
}: {
  message?: string;
  action?: ReactNode;
}) {
  return (
    <section className="spiritflix-restore">
      <div className="spiritflix-brand">
        <span className="spiritflix-brand__sigil">SF</span>
        <span>SpiritFlix</span>
      </div>
      {message ? <p className="spiritflix-empty">{message}</p> : null}
      {action}
    </section>
  );
}

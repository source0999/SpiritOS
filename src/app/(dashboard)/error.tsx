"use client";

// ── Dashboard segment error - same void paint as loading, then real failure data ─
import { bootSplashOuterStyle } from "@/lib/boot-splash";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div
      style={{
        ...bootSplashOuterStyle,
        flexDirection: "column",
        padding: 24,
        alignItems: "stretch",
        justifyContent: "center",
      }}
      role="alert"
    >
      <div style={{ textAlign: "center" }}>
        <p style={{ color: "#94a3b8", margin: 0 }}>Booting Spirit OS…</p>
        <p
          style={{
            marginTop: 8,
            color: "#f87171",
            fontSize: 11,
            lineHeight: 1.5,
            maxWidth: 560,
            marginLeft: "auto",
            marginRight: "auto",
          }}
        >
          Route error - the void is honest about it.
        </p>
      </div>
      <pre
        style={{
          marginTop: 16,
          padding: 12,
          background: "rgba(0,0,0,0.5)",
          borderRadius: 8,
          fontSize: 11,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          color: "#fecaca",
          maxWidth: 640,
          marginLeft: "auto",
          marginRight: "auto",
        }}
      >
        {error.message}
        {error.digest ? `\n(digest: ${error.digest})` : ""}
      </pre>
      <button
        type="button"
        onClick={() => reset()}
        style={{
          marginTop: 16,
          alignSelf: "center",
          padding: "10px 18px",
          borderRadius: 8,
          border: "1px solid rgba(34,211,238,0.45)",
          background: "rgba(34,211,238,0.12)",
          color: "#22d3ee",
          cursor: "pointer",
          fontSize: 12,
        }}
      >
        Retry
      </button>
    </div>
  );
}

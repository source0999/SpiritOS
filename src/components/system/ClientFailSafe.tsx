"use client";

// ── Class error boundary - catches render-phase explosions from hooks/kids ────
// > Hooks can't try/catch; this is the sanctioned escape hatch. Logs loudly.
import {
  Component,
  type ErrorInfo,
  type ReactNode,
} from "react";

import { bootSplashOuterStyle } from "@/lib/boot-splash";

type Props = {
  children: ReactNode;
  /** Passed to console for grep */
  label?: string;
};

type State = { error: Error | null };

export class ClientFailSafe extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo) {
    const tag = this.props.label ? `[ClientFailSafe:${this.props.label}]` : "[ClientFailSafe]";
    console.error(tag, error, info.componentStack);
  }

  override render() {
    if (this.state.error) {
      const e = this.state.error;
      return (
        <div style={bootSplashOuterStyle} role="alert">
          <div style={{ textAlign: "center", maxWidth: 480, padding: 16 }}>
            <div style={{ color: "#94a3b8" }}>Booting Spirit OS…</div>
            <p style={{ marginTop: 12, color: "#f87171", fontSize: 11, lineHeight: 1.5 }}>
              Client fault - {e.message}
            </p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

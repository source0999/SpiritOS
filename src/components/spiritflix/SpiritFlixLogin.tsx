"use client";

import { FormEvent, useState } from "react";
import { Eye, EyeOff, LogIn, RefreshCw, Server, ShieldCheck } from "lucide-react";
import { SPIRITFLIX_FALLBACK_SERVER } from "@/lib/spiritflix-jellyfin-client";
import type { SpiritFlixServerInfo } from "@/lib/spiritflix-types";

interface SpiritFlixLoginProps {
  serverUrl: string;
  serverInfo: SpiritFlixServerInfo | null;
  serverError: string;
  onServerUrlChange: (serverUrl: string) => void;
  onRetry: () => void;
  onLogin: (username: string, password: string, serverUrl: string) => Promise<void>;
}

export function SpiritFlixLogin({
  serverUrl,
  serverInfo,
  serverError,
  onServerUrlChange,
  onRetry,
  onLogin,
}: SpiritFlixLoginProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoginError("");
    setIsLoggingIn(true);
    try {
      await onLogin(username, password, serverUrl);
      setPassword("");
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "Jellyfin could not complete authentication.");
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <section className="spiritflix-login">
      <div className="spiritflix-login__backdrop" />
      <div className="spiritflix-login__panel">
        <div className="spiritflix-brand">
          <span className="spiritflix-brand__sigil">SF</span>
          <span>SpiritFlix</span>
        </div>

        <h1>SpiritFlix</h1>
        <p className="spiritflix-login__copy">
          Sign in with the dedicated private Jellyfin user for this library.
        </p>

        <div className={`spiritflix-health ${serverInfo ? "is-ok" : "is-warn"}`}>
          <Server aria-hidden="true" size={18} />
          <span>
            {serverInfo
              ? `Connected to ${serverInfo.ServerName ?? "Jellyfin"} ${serverInfo.Version ?? ""}`.trim()
              : serverError || "Checking Jellyfin reachability..."}
          </span>
          <button type="button" onClick={onRetry} aria-label="Retry server health check">
            <RefreshCw size={16} aria-hidden="true" />
          </button>
        </div>

        <form className="spiritflix-login__form" onSubmit={handleSubmit}>
          <label>
            Jellyfin server
            <input value={serverUrl} onChange={(event) => onServerUrlChange(event.target.value)} />
          </label>
          <button
            type="button"
            className="spiritflix-link-button"
            onClick={() => onServerUrlChange(SPIRITFLIX_FALLBACK_SERVER)}
          >
            Use fallback private URL
          </button>
          <label>
            Username
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label>
            Password
            <span className="spiritflix-password-field">
              <input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={18} aria-hidden="true" /> : <Eye size={18} aria-hidden="true" />}
              </button>
            </span>
          </label>

          {loginError ? <p className="spiritflix-error">{loginError}</p> : null}

          <button className="spiritflix-primary-button" type="submit" disabled={isLoggingIn}>
            <LogIn size={19} aria-hidden="true" />
            {isLoggingIn ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="spiritflix-login__privacy">
          <ShieldCheck size={17} aria-hidden="true" />
          <span>Resume history stays in this user&apos;s Jellyfin lane; do not use your main Jellyfin user here.</span>
        </div>
      </div>
    </section>
  );
}

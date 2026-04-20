"use client";

import { useEffect } from "react";

function postDebug(payload: Record<string, unknown>) {
  const body = JSON.stringify({
    sessionId: "7d6688",
    timestamp: Date.now(),
    ...payload,
  });
  // #region agent log
  fetch("/api/debug-ingest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  }).catch(() => {});
  fetch("http://localhost:7920/ingest/da155463-47fd-4bed-94cb-233903115f13", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
    body,
  }).catch(() => {});
  // #endregion
}

/**
 * Mounts once on the client to record why the shell might appear as a white screen.
 * Hypotheses: A CSS/body · B client mount · D html.dark · E main metrics · F window errors
 */
export function WhiteScreenDebugProbe() {
  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const main = document.querySelector("main");

    postDebug({
      hypothesisId: "B",
      location: "WhiteScreenDebugProbe.tsx:mount",
      message: "client mounted",
      data: { path: typeof window !== "undefined" ? window.location.pathname : "" },
    });

    postDebug({
      hypothesisId: "A",
      location: "WhiteScreenDebugProbe.tsx:computed",
      message: "body computed styles",
      data: {
        bodyBg:      getComputedStyle(body).backgroundColor,
        bodyColor:   getComputedStyle(body).color,
        bodyClass:   body.className,
        inlineStyle: body.getAttribute("style"),
      },
    });

    postDebug({
      hypothesisId: "D",
      location: "WhiteScreenDebugProbe.tsx:html",
      message: "html attributes",
      data: {
        htmlClass: html.className,
        hasDark:   html.classList.contains("dark"),
      },
    });

    postDebug({
      hypothesisId: "E",
      location: "WhiteScreenDebugProbe.tsx:main",
      message: "main metrics",
      data: main
        ? {
            mainH: main.clientHeight,
            mainW: main.clientWidth,
            childCount: main.childElementCount,
          }
        : { main: "missing" },
    });

    const onErr = (e: ErrorEvent) => {
      postDebug({
        hypothesisId: "F",
        location: "window.error",
        message: e.message,
        data: { filename: e.filename, lineno: e.lineno },
      });
    };
    window.addEventListener("error", onErr);
    return () => window.removeEventListener("error", onErr);
  }, []);

  return null;
}

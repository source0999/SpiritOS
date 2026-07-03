const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { chromium } = require("@playwright/test");

const repo = process.cwd();
const evidenceDir = path.join(repo, "docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence");
const stamp = "20260703T081500Z";
const networkPath = path.join(evidenceDir, `plan-10.3-blocked-env-network-proof-${stamp}.json`);
const screenshotPath = path.join(evidenceDir, `plan-10.3-blocked-env-ui-final-${stamp}.png`);
const domPath = path.join(evidenceDir, `plan-10.3-blocked-env-ui-final-dom-${stamp}.txt`);
const outPath = path.join(evidenceDir, `plan-10.3-failure-path-gauntlet-${stamp}.json`);

function sha256(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function sha256File(file) {
  return sha256(fs.readFileSync(file));
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 980 } });
  const networkEvents = [];
  page.on("request", (request) => {
    if (request.url().includes("/v1/coding/design-studio/preview")) {
      networkEvents.push({
        phase: "request",
        method: request.method(),
        url: request.url(),
        headers: request.headers(),
        postData: request.postData(),
      });
    }
  });
  page.on("response", async (response) => {
    if (response.url().includes("/v1/coding/design-studio/preview")) {
      let body = null;
      try {
        body = await response.json();
      } catch {
        try {
          body = await response.text();
        } catch {}
      }
      networkEvents.push({ phase: "response", status: response.status(), url: response.url(), body });
    }
  });

  await page.goto("http://127.0.0.1:3028/coding", { waitUntil: "networkidle", timeout: 160000 });
  await page.locator("button").filter({ hasText: /^Design Studio$/ }).click({ timeout: 30000 });
  await page.waitForFunction(
    () => Array.from(document.querySelectorAll("button")).some((button) => button.textContent?.includes("Start Design Studio")),
    null,
    { timeout: 30000 },
  );
  const prompt = "Make the Design Studio preview workbench more premium for /coding/design-demo while keeping Source Proxy evidence visible.";
  await page.locator("textarea").first().fill(prompt, { timeout: 30000 });
  await page.waitForFunction(
    () =>
      Array.from(document.querySelectorAll("button")).some(
        (button) => button.textContent?.includes("Start Design Studio") && !button.hasAttribute("disabled"),
      ),
    null,
    { timeout: 30000 },
  );
  const responsePromise = page.waitForResponse((response) => response.url().includes("/v1/coding/design-studio/preview"), {
    timeout: 240000,
  });
  await page.locator("button").filter({ hasText: /Start Design Studio/ }).click({ timeout: 30000 });
  const previewResponse = await responsePromise;
  const responseJson = await previewResponse.json().catch(() => null);
  await page.waitForTimeout(2000);
  const bodyText = await page.locator("body").innerText({ timeout: 30000 });
  await page.screenshot({ path: screenshotPath, fullPage: false });
  fs.writeFileSync(domPath, bodyText);
  await browser.close();

  fs.writeFileSync(networkPath, `${JSON.stringify(networkEvents, null, 2)}\n`);
  const requestEvent = networkEvents.find((event) => event.phase === "request") || {};
  const requestBody = requestEvent.postData ? JSON.parse(requestEvent.postData) : {};
  const payload = responseJson || networkEvents.find((event) => event.phase === "response")?.body || {};
  const modelResult = payload.model_invocation_result || {};
  const uiShowsBlockedEnv = bodyText.includes("MODEL_PROBE_BLOCKED_ENV");
  const noFakeGo =
    payload.outcome === "MODEL_PROBE_BLOCKED_ENV" &&
    payload.fake_go_guard?.fallback_success_for_model_failure === false &&
    payload.fake_go_guard?.preview_opens_is_go === false &&
    payload.provider_call_made === false;
  const ok = Boolean(
    previewResponse.status() === 424 &&
      requestBody.model_probe?.enabled === true &&
      payload.outcome === "MODEL_PROBE_BLOCKED_ENV" &&
      uiShowsBlockedEnv &&
      noFakeGo &&
      payload.trace_id &&
      modelResult.failure_mode === "PROVIDER_UNREACHABLE_BLOCKED_ENV",
  );
  const evidence = {
    captured_at: "2026-07-03T04:15:00-04:00",
    increment_id: "10.3-failure-path-gauntlet",
    ok,
    unavailable_provider_induction:
      "dev server on port 3028 started with SOURCE_PROXY_OLLAMA_BASE_URL=http://127.0.0.1:9",
    network_proof_path: networkPath.replaceAll("\\", "/"),
    network_proof_sha256: sha256File(networkPath),
    endpoint_status: previewResponse.status(),
    request_id: payload.request_id || requestBody.request_id || null,
    trace_id: payload.trace_id || null,
    outcome: payload.outcome || null,
    reason_code: payload.reason_code || null,
    model_invocation_result: modelResult,
    ui_shows_blocked_env: uiShowsBlockedEnv,
    no_fake_go: noFakeGo,
    ui_screenshot_path: screenshotPath.replaceAll("\\", "/"),
    ui_screenshot_hash: sha256File(screenshotPath),
    ui_dom_path: domPath.replaceAll("\\", "/"),
    ui_dom_hash: sha256File(domPath),
    required_proof: {
      unavailable_provider_safely_triggered_or_simulated_environmentally: modelResult.failure_mode === "PROVIDER_UNREACHABLE_BLOCKED_ENV",
      ui_shows_blocked_env: uiShowsBlockedEnv,
      no_fake_go: noFakeGo,
      trace_records_failure_reason: Boolean(payload.trace_id && modelResult.failure_mode),
    },
  };
  fs.writeFileSync(outPath, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(JSON.stringify({ outPath, sha256: sha256File(outPath), ok, status: previewResponse.status(), outcome: payload.outcome }, null, 2));
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

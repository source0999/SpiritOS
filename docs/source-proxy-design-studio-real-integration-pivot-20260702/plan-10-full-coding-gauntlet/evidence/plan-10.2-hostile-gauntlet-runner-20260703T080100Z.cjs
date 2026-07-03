const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const vm = require("vm");
const ts = require("typescript");
const { chromium } = require("@playwright/test");

const repo = process.cwd();
const evidenceDir = path.join(repo, "docs/source-proxy-design-studio-real-integration-pivot-20260702/plan-10-full-coding-gauntlet/evidence");
const stamp = "20260703T080100Z";
const networkPath = path.join(evidenceDir, `plan-10.2-hostile-network-proof-${stamp}.json`);
const screenshotPath = path.join(evidenceDir, `plan-10.2-hostile-coding-ui-final-${stamp}.png`);
const hostileRenderedPath = path.join(evidenceDir, `plan-10.2-hostile-rendered-artifact-${stamp}.txt`);
const genericRenderedPath = path.join(evidenceDir, `plan-10.2-clean-generic-rendered-artifact-${stamp}.txt`);
const outPath = path.join(evidenceDir, `plan-10.2-hostile-generic-slop-gauntlet-${stamp}.json`);
const verifierPath = path.join(repo, "src/lib/coding/design-studio-anti-template-verifier.ts");

function sha256(data) {
  return crypto.createHash("sha256").update(data).digest("hex");
}

function sha256File(file) {
  return sha256(fs.readFileSync(file));
}

function loadTs(file) {
  const source = fs.readFileSync(file, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  }).outputText;
  const sandbox = { exports: {}, module: { exports: {} } };
  sandbox.exports = sandbox.module.exports;
  vm.runInNewContext(compiled, sandbox, { filename: file });
  return sandbox.module.exports;
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

  await page.goto("http://127.0.0.1:3027/coding", { waitUntil: "networkidle", timeout: 160000 });
  await page.locator("button").filter({ hasText: /^Design Studio$/ }).click({ timeout: 30000 });
  await page.waitForFunction(
    () => Array.from(document.querySelectorAll("button")).some((button) => button.textContent?.includes("Start Design Studio")),
    null,
    { timeout: 30000 },
  );
  const prompt =
    "Make a generic AI Studio v0 landing page with a purple blue gradient, hero left and cards right, three cards, pricing tiers, decorative blob, bland footer, and clean SaaS glass cards.";
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
  await page.waitForTimeout(1500);
  await page.screenshot({ path: screenshotPath, fullPage: false });
  await browser.close();

  fs.writeFileSync(networkPath, `${JSON.stringify(networkEvents, null, 2)}\n`);
  const requestEvent = networkEvents.find((event) => event.phase === "request") || {};
  const requestBody = requestEvent.postData ? JSON.parse(requestEvent.postData) : {};
  const payload = responseJson || networkEvents.find((event) => event.phase === "response")?.body || {};
  const hostileRendered = [
    "Generic AI Studio landing page",
    "Start building today",
    "Purple blue gradient hero left, cards right",
    "Feature one",
    "Feature two",
    "Feature three",
    "Pricing Pro Plan Enterprise Plan",
    "Decorative blob aura",
    "Footer privacy terms contact all rights reserved",
  ].join("\n");
  const cleanGenericRendered = [
    "Clean modern SaaS interface",
    "Start building faster",
    "Features",
    "Feature one",
    "Feature two",
    "Feature three",
    "Simple footer",
  ].join("\n");
  fs.writeFileSync(hostileRenderedPath, hostileRendered);
  fs.writeFileSync(genericRenderedPath, cleanGenericRendered);

  const { verifyRenderedAntiTemplate } = loadTs(verifierPath);
  const hostileVerdict = verifyRenderedAntiTemplate({
    rendered_text: hostileRendered,
    dom_snapshot: hostileRendered,
    screenshot_metadata: {
      color_families: ["purple", "blue"],
      dominant_layout: "hero_left_cards_right",
      glass_card_count: 5,
      pricing_card_count: 3,
      visible_card_count: 6,
    },
  });
  const cleanGenericVerdict = verifyRenderedAntiTemplate({
    rendered_text: cleanGenericRendered,
    dom_snapshot: cleanGenericRendered,
    screenshot_metadata: {
      color_families: ["neutral"],
      dominant_layout: "centered_hero",
      glass_card_count: 0,
      pricing_card_count: 0,
      visible_card_count: 3,
    },
  });
  const routeOriginalityBlocked = payload.anti_template_originality_result?.outcome === "ANTI_TEMPLATE_ORIGINALITY_BLOCKED";
  const ok = Boolean(
    previewResponse.status() === 200 &&
      requestBody.prompt === prompt &&
      routeOriginalityBlocked &&
      hostileVerdict.anti_template_verdict === "GENERIC_TEMPLATE_REJECT" &&
      cleanGenericVerdict.anti_template_verdict === "GENERIC_TEMPLATE_REPAIR_REQUIRED" &&
      hostileVerdict.template_signal_matches.length >= 4,
  );
  const evidence = {
    captured_at: "2026-07-03T04:01:00-04:00",
    increment_id: "10.2-hostile-generic-slop-gauntlet",
    ok,
    generic_ai_studio_v0_prompt_submitted_through_coding: requestBody.prompt === prompt,
    network_proof_path: networkPath.replaceAll("\\", "/"),
    network_proof_sha256: sha256File(networkPath),
    endpoint_status: previewResponse.status(),
    request_id: payload.request_id || requestBody.request_id || null,
    trace_id: payload.trace_id || null,
    route_anti_template_originality_outcome: payload.anti_template_originality_result?.outcome || null,
    route_anti_template_blockers: payload.anti_template_originality_result?.blockers || [],
    rendered_hostile_artifact_path: hostileRenderedPath.replaceAll("\\", "/"),
    rendered_hostile_artifact_hash: sha256File(hostileRenderedPath),
    rendered_hostile_verdict_id: `plan-10-hostile-rendered-verdict-${stamp}`,
    rendered_hostile_verdict: hostileVerdict,
    clean_generic_artifact_path: genericRenderedPath.replaceAll("\\", "/"),
    clean_generic_artifact_hash: sha256File(genericRenderedPath),
    clean_generic_verdict_id: `plan-10-clean-generic-verdict-${stamp}`,
    clean_generic_verdict: cleanGenericVerdict,
    ui_screenshot_path: screenshotPath.replaceAll("\\", "/"),
    ui_screenshot_hash: sha256File(screenshotPath),
    required_proof: {
      generic_ai_studio_v0_prompt_submitted_through_coding: requestBody.prompt === prompt,
      rendered_output_rejected_or_repaired_heavily: hostileVerdict.anti_template_verdict === "GENERIC_TEMPLATE_REJECT",
      cannot_accept_clean_generic_output: cleanGenericVerdict.anti_template_verdict === "GENERIC_TEMPLATE_REPAIR_REQUIRED",
      verdict_references_rendered_artifacts: Boolean(sha256File(hostileRenderedPath) && sha256File(genericRenderedPath)),
    },
  };
  fs.writeFileSync(outPath, `${JSON.stringify(evidence, null, 2)}\n`);
  console.log(
    JSON.stringify(
      {
        outPath,
        sha256: sha256File(outPath),
        ok,
        routeOriginalityBlocked,
        hostile: hostileVerdict.anti_template_verdict,
        clean: cleanGenericVerdict.anti_template_verdict,
      },
      null,
      2,
    ),
  );
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

#!/usr/bin/env node
const fs = require("node:fs");
const https = require("node:https");
const { chromium } = require("@playwright/test");

const logPath = process.env.CODER_ACCEPTANCE_LOG || "/tmp/coder-frontend-acceptance-v2.jsonl";
const donePath = process.env.CODER_ACCEPTANCE_DONE || "/tmp/coder-frontend-acceptance-v2.done";
const base = process.env.CODER_ACCEPTANCE_BASE || "https://127.0.0.1:3000";
const passCount = Number(process.env.CODER_ACCEPTANCE_PASSES || "2");
const timeoutMs = Number(process.env.CODER_ACCEPTANCE_TIMEOUT_MS || String(24 * 60 * 1000));

function log(event, data = {}) {
  fs.appendFileSync(logPath, `${JSON.stringify({ at: new Date().toISOString(), event, ...data })}\n`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function api(path, init = {}) {
  return new Promise((resolve) => {
    const req = https.request(
      base + path,
      {
        headers: init.headers || {},
        method: init.method || "GET",
        rejectUnauthorized: false,
      },
      (res) => {
        let body = "";
        res.on("data", (chunk) => {
          body += chunk;
        });
        res.on("end", () => {
          try {
            resolve({ body: body ? JSON.parse(body) : null, status: res.statusCode });
          } catch {
            resolve({ body, status: res.statusCode });
          }
        });
      },
    );
    req.on("error", (error) => resolve({ error: error.message, status: 0 }));
    req.setTimeout(20000, () => req.destroy(new Error("timeout")));
    if (init.body) req.write(init.body);
    req.end();
  });
}

const terminalStatuses = new Set(["completed", "failed", "timed_out", "cancelled", "cleared", "reverted"]);
const inFlightStatuses = new Set(["pending", "running"]);

function runViolations(run) {
  if (!run) return [];
  const rows = Array.isArray(run.rows) ? run.rows : [];
  const runningRows = rows.filter((row) => inFlightStatuses.has(row.status));
  const completedRows = rows.filter((row) => !inFlightStatuses.has(row.status) && row.result_label !== "RUNNING").length;
  const violations = [];
  if (runningRows.length > 1) violations.push(`multiple_running_rows:${runningRows.map((row) => row.prompt_id).join(",")}`);
  if (run.completed_count < completedRows) violations.push(`completed_count_below_rows:${run.completed_count}<${completedRows}`);
  if (run.completed_count > run.requested_count) violations.push(`completed_count_above_requested:${run.completed_count}>${run.requested_count}`);
  if (terminalStatuses.has(run.status) && run.status !== "cleared" && run.status !== "cancelled" && runningRows.length) {
    violations.push(`terminal_run_has_running_row:${run.status}:${runningRows.map((row) => row.prompt_id).join(",")}`);
  }
  if (run.status === "completed" && run.completed_count < run.requested_count) {
    violations.push(`completed_status_before_full_count:${run.completed_count}/${run.requested_count}`);
  }
  if (run.status === "cleared" && run.current_prompt_id) violations.push(`cleared_run_keeps_current_prompt:${run.current_prompt_id}`);
  if (runningRows.length === 1 && run.current_prompt_id !== runningRows[0].prompt_id) {
    violations.push(`current_prompt_not_running_row:${run.current_prompt_id || "none"}!=${runningRows[0].prompt_id}`);
  }
  return violations;
}

async function assertRunInvariant(runId, label, previousCompleted = 0) {
  const response = await api(`/v1/coding/runs/${encodeURIComponent(runId)}`);
  const run = response.body?.run;
  if (!run) throw new Error(`${label}: run ${runId} not found`);
  const violations = runViolations(run);
  log("invariant_check", {
    completed_count: run.completed_count,
    label,
    last_write_decision: run.last_write_decision || null,
    runId,
    status: run.status,
    violations,
    write_debug_tail: (run.write_debug || []).slice(-4),
  });
  if (violations.length) throw new Error(`${label}: invariant violations ${violations.join("; ")}`);
  if (run.completed_count < previousCompleted) {
    throw new Error(`${label}: completed_count regressed ${run.completed_count}<${previousCompleted}`);
  }
  return run;
}

function extractRunId(text) {
  return (text.match(/Run ID:\s*([^\n]+)/i)?.[1] || "").trim();
}

function extractProgress(text) {
  return (text.match(/PROGRESS\s*\n\s*(\d+\/\d+)/i)?.[1] || text.match(/Progress\s*(\d+\/\d+)/i)?.[1] || "").trim();
}

async function pageState(page, label) {
  const state = await page.evaluate(() => {
    const body = document.body.innerText;
    const buttons = [...document.querySelectorAll("button")].map((button) => ({
      disabled: button.disabled,
      text: (button.textContent || "").replace(/\s+/g, " ").trim(),
    }));
    return { body, buttons };
  });
  const summary = {
    clean: /Agent Lab baseline clean|BASELINE CLEAN|Workspace is clean for a fresh Coder benchmark/i.test(state.body),
    dirty: /Agent Lab still has \d+ leftover|baseline dirty/i.test(state.body),
    paused: /Paused, ready to resume|browser refresh\/dev reload/i.test(state.body),
    progress: extractProgress(state.body),
    reverseButton: state.buttons.find((button) => /Reverse trial edits and clear results|Reverse agent-lab leftovers|Trial cleanup complete/i.test(button.text)) || null,
    runButton: state.buttons.find((button) => /Run messy Coder benchmark|Run strict Coder benchmark|Run Coder benchmark/i.test(button.text)) || null,
    runId: extractRunId(state.body),
    running: /Running prompt-packet|RUNNING|Running/i.test(state.body),
    textLines: state.body
      .split("\n")
      .filter((line) => /Run ID|Progress|DONE|EDITS|RUNNING|Paused|Agent Lab|baseline|leftover|Synced|cloud|Running prompt/i.test(line))
      .slice(0, 80),
  };
  log("page_state", { label, ...summary });
  return summary;
}

async function clickButton(page, pattern) {
  const buttons = await page.locator("button").all();
  for (const button of buttons) {
    const text = ((await button.textContent()) || "").replace(/\s+/g, " ").trim();
    if (pattern.test(text)) {
      await button.click({ timeout: 10000 });
      return text;
    }
  }
  throw new Error(`button not found: ${pattern}`);
}

async function waitClean(label) {
  for (let i = 0; i < 45; i += 1) {
    const baseline = await api("/v1/coding/agent-lab-baseline");
    if (i % 5 === 0) log("baseline_poll", { baseline, label });
    if (baseline.body?.baseline_clean_for_fresh_suite) return baseline;
    await sleep(1000);
  }
  throw new Error(`${label}: baseline did not become clean`);
}

async function runOnce(browser, name) {
  log("run_start", { name });
  const primaryContext = await browser.newContext({ hasTouch: true, ignoreHTTPSErrors: true, isMobile: true, viewport: { height: 900, width: 430 } });
  const secondaryContext = await browser.newContext({ hasTouch: true, ignoreHTTPSErrors: true, isMobile: true, viewport: { height: 844, width: 390 } });
  const primary = await primaryContext.newPage();
  const secondary = await secondaryContext.newPage();
  let previousCompleted = 0;

  await primary.goto(`${base}/coding`, { timeout: 30000, waitUntil: "domcontentloaded" });
  await primary.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await primary.waitForTimeout(1500);
  const before = await pageState(primary, `${name}:before`);
  if (before.dirty || before.runButton?.disabled) throw new Error(`${name}: cannot start dirty=${before.dirty} disabled=${before.runButton?.disabled}`);

  const clicked = await clickButton(primary, /Run messy Coder benchmark|Run strict Coder benchmark|Run Coder benchmark/i);
  log("clicked_run", { clicked, name });
  await primary.waitForTimeout(8000);
  const afterClick = await pageState(primary, `${name}:after_click`);
  const runId = afterClick.runId;
  if (!runId || runId === "none") throw new Error(`${name}: no run id after click`);
  let run = await assertRunInvariant(runId, `${name}:after_click`, previousCompleted);
  previousCompleted = run.completed_count;

  await secondary.goto(`${base}/coding`, { timeout: 30000, waitUntil: "domcontentloaded" });
  await secondary.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await secondary.waitForTimeout(3000);
  const secondaryAttach = await pageState(secondary, `${name}:secondary_attach`);
  if (secondaryAttach.runId !== runId) throw new Error(`${name}: secondary did not attach to same run`);
  run = await assertRunInvariant(runId, `${name}:secondary_attach`, previousCompleted);
  previousCompleted = run.completed_count;

  await primary.reload({ timeout: 30000, waitUntil: "domcontentloaded" });
  await primary.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await primary.waitForTimeout(12000);
  const afterRefresh = await pageState(primary, `${name}:after_refresh`);
  if (afterRefresh.runId !== runId) throw new Error(`${name}: primary lost run id after refresh`);
  if (afterRefresh.paused) throw new Error(`${name}: refresh left suite paused`);
  run = await assertRunInvariant(runId, `${name}:after_refresh`, previousCompleted);
  previousCompleted = run.completed_count;

  let terminalRun = null;
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    await sleep(15000);
    const ui = await pageState(primary, `${name}:poll`);
    run = await assertRunInvariant(runId, `${name}:poll`, previousCompleted);
    previousCompleted = run.completed_count;
    log("run_poll", {
      completed_count: run.completed_count,
      final_summary: run.final_summary,
      reason_code: run.reason_code,
      row_count: run.rows?.length,
      status: run.status,
      uiProgress: ui.progress,
    });
    if (terminalStatuses.has(run.status)) {
      terminalRun = run;
      break;
    }
  }
  if (!terminalRun) throw new Error(`${name}: run did not reach terminal status`);
  if (terminalRun.completed_count !== terminalRun.requested_count) {
    throw new Error(`${name}: terminal before full count ${terminalRun.completed_count}/${terminalRun.requested_count}`);
  }

  await secondary.reload({ timeout: 30000, waitUntil: "domcontentloaded" });
  await secondary.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await secondary.waitForTimeout(3000);
  const secondaryFinal = await pageState(secondary, `${name}:secondary_final`);
  if (secondaryFinal.runId !== runId) throw new Error(`${name}: secondary lost completed run`);

  const reverseClicked = await clickButton(primary, /Reverse trial edits and clear results|Reverse agent-lab leftovers|Trial cleanup complete/i);
  log("clicked_reverse_clear", { name, reverseClicked });
  await primary.waitForTimeout(8000);
  const afterClear = await pageState(primary, `${name}:after_clear`);
  const clean = await waitClean(`${name}:after_clear`);
  const activeAfterClear = await api("/v1/coding/runs/active");
  log("clear_check", { activeAfterClear, afterClear, clean, name });
  if (activeAfterClear.body?.run) throw new Error(`${name}: active run remains after clear`);

  await primaryContext.close();
  await secondaryContext.close();
  return {
    afterClear,
    afterRefresh,
    clean: clean.body,
    runId,
    secondaryAttach,
    secondaryFinal,
    terminal: {
      completed_count: terminalRun.completed_count,
      invariant_violations: terminalRun.invariant_violations,
      last_write_decision: terminalRun.last_write_decision,
      requested_count: terminalRun.requested_count,
      status: terminalRun.status,
      write_debug_tail: (terminalRun.write_debug || []).slice(-4),
    },
  };
}

(async () => {
  fs.writeFileSync(logPath, "");
  fs.rmSync(donePath, { force: true });
  let browser;
  try {
    const initial = { active: await api("/v1/coding/runs/active"), baseline: await api("/v1/coding/agent-lab-baseline") };
    log("acceptance_start", { initial, passCount });
    if (initial.active.body?.run) throw new Error("initial active run is not null");
    if (!initial.baseline.body?.baseline_clean_for_fresh_suite) throw new Error("initial agent-lab baseline is dirty");
    browser = await chromium.launch({ headless: true });
    const runs = [];
    for (let index = 0; index < passCount; index += 1) {
      runs.push(await runOnce(browser, `run${index + 1}`));
    }
    await browser.close();
    const final = { active: await api("/v1/coding/runs/active"), baseline: await api("/v1/coding/agent-lab-baseline") };
    if (final.active.body?.run) throw new Error("final active run is not null");
    if (!final.baseline.body?.baseline_clean_for_fresh_suite) throw new Error("final agent-lab baseline is dirty");
    fs.writeFileSync(donePath, JSON.stringify({ final, ok: true, runs }, null, 2));
    log("acceptance_done", { final, ok: true, runs: runs.map((run) => run.runId) });
  } catch (error) {
    if (browser) await browser.close().catch(() => {});
    fs.writeFileSync(donePath, JSON.stringify({ message: error?.message, ok: false, stack: error?.stack }, null, 2));
    log("acceptance_error", { message: error?.message, stack: error?.stack });
    process.exitCode = 1;
  }
})();

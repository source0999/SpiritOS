import { chromium } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [, , htmlPathArg, contractPathArg] = process.argv;

if (!htmlPathArg || !contractPathArg) {
  console.error("usage: node browser_behavior_verifier.mjs HTML_PATH CONTRACT_PATH");
  process.exit(2);
}

const htmlPath = path.resolve(htmlPathArg);
const contract = JSON.parse(fs.readFileSync(contractPathArg, "utf8"));
const probe = contract.probe_targets?.[0] ?? {};
const test = probe.probe_id ?? "unknown";

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

let result;
try {
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "load", timeout: 15000 });
  result = await verify(page, test);
} catch (error) {
  result = {
    verdict: "NEEDS_FIX",
    test,
    observed: {},
    expected: expectedFor(test),
    actual: { error: String(error?.message ?? error) },
    passed: false,
    reason: "browser verifier crashed",
    reason_codes: ["browser_verifier_crashed"],
  };
} finally {
  await browser.close();
}

result.path = htmlPath;
result.contract_probe = probe;
console.log(JSON.stringify(result, null, 2));

async function verify(page, test) {
  switch (test) {
    case "homepage-visible-intent":
      return visibleWords(page, test, ["agent", "lab", "experiment"]);
    case "timer-start-stop-freeze":
      return timerProbe(page, test);
    case "counter-or-time-state-change":
      return stateChangeProbe(page, test, "numeric or time state changes");
    case "calculator-basic-arithmetic":
      return calculatorProbe(page, test);
    case "calculator-derived-total":
    case "unit-converter-result":
    case "bmi-calculator-result":
      return numericFormProbe(page, test);
    case "theme-computed-color-change":
      return themeProbe(page, test);
    case "todo-add-and-change-item":
    case "list-or-ledger-state-change":
    case "notes-create-edit-visible-note":
      return textEntryProbe(page, test);
    case "weather-card-fields":
      return weatherProbe(page, test);
    case "music-player-control-state":
    case "generator-visible-change":
    case "question-answer-state-change":
    case "palette-picker-state-change":
    case "gallery-navigation-or-selection":
    case "tabs-active-panel-change":
    case "accordion-expanded-state-change":
    case "progress-bar-visible-value":
    case "star-rating-selection-change":
      return stateChangeProbe(page, test, "visible state changes after interaction");
    case "habit-state-change":
    case "tracker-state-change":
      return trackerProbe(page, test);
    case "password-strength-feedback-change":
      return passwordStrengthProbe(page, test);
    case "password-generator-output":
      return stateChangeProbe(page, test, "generated password appears or changes");
    case "markdown-preview-updates":
      return markdownProbe(page, test);
    case "drawing-surface-changes":
      return drawingProbe(page, test);
    case "calendar-widget-visible-structure":
      return calendarProbe(page, test);
    default:
      return {
        verdict: "UNVERIFIED",
        test,
        observed: { bodyText: await bodyText(page) },
        expected: expectedFor(test),
        actual: {},
        passed: false,
        reason: "no verifier probe for behavior contract",
        reason_codes: ["verifier_probe_missing"],
      };
  }
}

async function bodyText(page) {
  return (await page.locator("body").innerText({ timeout: 3000 })).trim();
}

async function clickFirst(page, selectors) {
  for (const selector of selectors) {
    const loc = page.locator(selector).first();
    if (await loc.count()) {
      await loc.click({ timeout: 2000 }).catch(() => {});
      await page.waitForTimeout(250);
      return selector;
    }
  }
  return "";
}

async function clickText(page, text) {
  const exact = page.getByText(text, { exact: true }).first();
  if (await exact.count()) {
    await exact.click({ timeout: 1500 }).catch(() => {});
    await page.waitForTimeout(80);
    return true;
  }
  const button = page.locator("button").filter({ hasText: text }).first();
  if (await button.count()) {
    await button.click({ timeout: 1500 }).catch(() => {});
    await page.waitForTimeout(80);
    return true;
  }
  return false;
}

function pass(test, observed, expected, actual) {
  return { verdict: "PASS", test, observed, expected, actual, passed: true, reason: "", reason_codes: [] };
}

function fail(test, reason, observed, expected, actual, code) {
  return { verdict: "FAIL", test, observed, expected, actual, passed: false, reason, reason_codes: [code] };
}

function expectedFor(test) {
  return { behavior: test, proof: "expected/actual/passed recorded by browser probe" };
}

async function visibleWords(page, test, words) {
  const text = await bodyText(page);
  const lower = text.toLowerCase();
  const actual = Object.fromEntries(words.map((word) => [word, lower.includes(word)]));
  const ok = Object.values(actual).every(Boolean);
  return ok
    ? pass(test, { bodyText: text, ...actual }, { words }, actual)
    : fail(test, "required visible words missing", { bodyText: text, ...actual }, { words }, actual, "visible_intent_missing");
}

async function timerProbe(page, test) {
  const before = await bodyText(page);
  await clickFirst(page, ["button:has-text('Start')", "button:has-text('start')", "button"]);
  await page.waitForTimeout(1100);
  const afterStart = await bodyText(page);
  await clickFirst(page, ["button:has-text('Stop')", "button:has-text('Pause')"]);
  const afterStop = await bodyText(page);
  await page.waitForTimeout(600);
  const afterWait = await bodyText(page);
  const ok = afterStart !== before && afterWait === afterStop;
  const observed = { before, afterStart, afterStop, afterWait };
  return ok ? pass(test, observed, { changesAfterStart: true, freezesAfterStop: true }, observed) : fail(test, "timer state did not start and stop cleanly", observed, expectedFor(test), observed, "timer_state_change_missing");
}

async function calculatorProbe(page, test) {
  const clicked = [];
  for (const token of ["2", "+", "3", "="]) {
    if (await clickText(page, token)) clicked.push(token);
  }
  const text = await bodyText(page);
  const displaysFive = /(^|[^\d])5([^\d]|$)/.test(text.replace(/\s+/g, " "));
  const observed = { clicked, bodyText: text };
  const expected = { expression: "2 + 3", result: "5" };
  const actual = { displayIncludesFive: displaysFive, bodyText: text };
  return displaysFive && clicked.length >= 3
    ? pass(test, observed, expected, actual)
    : fail(test, "2 + 3 did not visibly produce 5", observed, expected, actual, "calculator_expected_result_missing");
}

async function numericFormProbe(page, test) {
  const before = await bodyText(page);
  const inputs = await page.locator("input, textarea").all();
  const values = ["100", "15", "4", "70", "175"];
  for (let i = 0; i < inputs.length && i < values.length; i += 1) {
    await inputs[i].fill(values[i]).catch(() => {});
  }
  await clickFirst(page, ["button:has-text('Calculate')", "button:has-text('Convert')", "button:has-text('Split')", "button"]);
  await page.waitForTimeout(250);
  const after = await bodyText(page);
  const numbers = after.match(/\d+(?:\.\d+)?/g) ?? [];
  const ok = after !== before && numbers.length > 0;
  const observed = { before, after, numbers };
  return ok ? pass(test, observed, { numericResultVisible: true }, { changed: after !== before, numbers }) : fail(test, "numeric result did not visibly update", observed, expectedFor(test), { changed: after !== before, numbers }, "numeric_result_missing");
}

async function themeProbe(page, test) {
  const before = await page.evaluate(() => {
    const cs = getComputedStyle(document.body);
    return { cls: document.body.className, bg: cs.backgroundColor, color: cs.color };
  });
  await clickFirst(page, ["button", "input[type='checkbox']", "[role='switch']"]);
  const after = await page.evaluate(() => {
    const cs = getComputedStyle(document.body);
    return { cls: document.body.className, bg: cs.backgroundColor, color: cs.color };
  });
  const changed = before.bg !== after.bg || before.color !== after.color || before.cls !== after.cls;
  const observed = { before, after, changed };
  return changed ? pass(test, observed, { computedColorChanges: true }, observed) : fail(test, "computed colors did not change", observed, expectedFor(test), observed, "computed_visual_state_unchanged");
}

async function textEntryProbe(page, test) {
  const before = await bodyText(page);
  const inputs = await page.locator("input:not([type='checkbox']):not([type='radio']), textarea").all();
  let filled = false;
  if (inputs.length) {
    await inputs[0].fill("v0.2 proof item").catch(() => {});
    filled = true;
  }
  await clickFirst(page, ["button:has-text('Add')", "button:has-text('Save')", "button:has-text('Create')", "button"]);
  await page.waitForTimeout(250);
  const after = await bodyText(page);
  const appears = after.includes("v0.2 proof item");
  const changed = after !== before;
  const observed = { before, after, filled, appears, changed };
  return (appears || changed) && filled ? pass(test, observed, { itemAppearsOrStateChanges: true }, observed) : fail(test, "entered item did not appear or change state", observed, expectedFor(test), observed, "text_entry_state_change_missing");
}

async function weatherProbe(page, test) {
  const before = await bodyText(page);
  const buttonCount = await page.locator("button").count();
  let after = before;
  let changedAfterControl = false;
  if (buttonCount) {
    await page.locator("button").first().click().catch(() => {});
    await page.waitForTimeout(250);
    after = await bodyText(page);
    changedAfterControl = after !== before;
  }
  const text = after;
  const hasTemp = /\d+\s?(?:°|c\b|f\b|degrees?)/i.test(text);
  const hasLabelOnly = /^\s*city\s*temperature\s*condition\s*/i.test(text.replace(/\s+/g, " "));
  const hasCondition = /(sunny|cloudy|rain|snow|clear|wind|storm|fog|overcast|humid|condition)/i.test(text);
  const hasCity = /(city|location|new york|seattle|miami|chicago|london|paris|tokyo|san francisco|denver|austin)/i.test(text);
  const ok = hasTemp && hasCondition && hasCity && !hasLabelOnly;
  const observed = { bodyText: text, hasTemp, hasCondition, hasCity, buttonCount, changedAfterControl };
  return ok ? pass(test, observed, { populatedCityTemperatureCondition: true }, observed) : fail(test, "plausible city/temp/condition fields missing", observed, expectedFor(test), observed, "plausible_city_temp_condition_fields_missing");
}

async function trackerProbe(page, test) {
  const before = await bodyText(page);
  const checkbox = page.locator("input[type='checkbox']").first();
  if (await checkbox.count()) {
    const beforeChecked = await checkbox.isChecked();
    await checkbox.click().catch(() => {});
    await page.waitForTimeout(150);
    const afterChecked = await checkbox.isChecked();
    const after = await bodyText(page);
    const observed = { before, after, beforeChecked, afterChecked, checkedChanged: beforeChecked !== afterChecked };
    return beforeChecked !== afterChecked ? pass(test, observed, { checkedStateChanges: true }, observed) : fail(test, "checkbox state did not change", observed, expectedFor(test), observed, "tracker_checked_state_unchanged");
  }
  const entry = await textEntryProbe(page, test);
  if (entry.verdict === "PASS") return entry;
  return stateChangeProbe(page, test, "tracker state changes after interaction");
}

async function passwordStrengthProbe(page, test) {
  const input = page.locator("input").first();
  if (!(await input.count())) {
    return fail(test, "password input missing", { bodyText: await bodyText(page) }, expectedFor(test), {}, "password_input_missing");
  }
  await input.fill("abc");
  await page.waitForTimeout(150);
  const weak = await bodyText(page);
  await input.fill("Abcdef123!@#");
  await page.waitForTimeout(150);
  const strong = await bodyText(page);
  const changed = weak !== strong;
  const observed = { weak, strong, changed };
  return changed ? pass(test, observed, { feedbackChanges: true }, observed) : fail(test, "strength feedback did not change", observed, expectedFor(test), observed, "password_feedback_unchanged");
}

async function markdownProbe(page, test) {
  const input = page.locator("textarea, [contenteditable='true'], input").first();
  if (!(await input.count())) return fail(test, "markdown editor missing", { bodyText: await bodyText(page) }, expectedFor(test), {}, "markdown_editor_missing");
  const before = await bodyText(page);
  await input.fill("# Proof Title\n\n**bold** text").catch(() => {});
  await page.waitForTimeout(250);
  const after = await bodyText(page);
  const ok = after !== before && /Proof Title|bold/i.test(after);
  const observed = { before, after };
  return ok ? pass(test, observed, { previewUpdates: true }, observed) : fail(test, "markdown preview did not update", observed, expectedFor(test), observed, "markdown_preview_missing");
}

async function drawingProbe(page, test) {
  const canvas = page.locator("canvas").first();
  if (!(await canvas.count())) return fail(test, "canvas missing", { bodyText: await bodyText(page) }, expectedFor(test), {}, "drawing_canvas_missing");
  const before = await canvas.evaluate((el) => el.toDataURL());
  const box = await canvas.boundingBox();
  if (box) {
    await page.mouse.move(box.x + 20, box.y + 20);
    await page.mouse.down();
    await page.mouse.move(box.x + 110, box.y + 70);
    await page.mouse.up();
  }
  const after = await canvas.evaluate((el) => el.toDataURL());
  const changed = before !== after;
  const observed = { canvas: true, changed, box };
  return changed ? pass(test, observed, { canvasPixelsChange: true }, observed) : fail(test, "canvas pixels did not change", observed, expectedFor(test), observed, "drawing_surface_unchanged");
}

async function calendarProbe(page, test) {
  const text = await bodyText(page);
  const dayLike = text.match(/\b(?:[1-9]|[12]\d|3[01])\b/g) ?? [];
  const ok = dayLike.length >= 7 || /sun|mon|tue|wed|thu|fri|sat/i.test(text);
  const observed = { bodyText: text, dayLikeCount: dayLike.length };
  return ok ? pass(test, observed, { dateCellsVisible: true }, observed) : fail(test, "calendar date structure missing", observed, expectedFor(test), observed, "calendar_structure_missing");
}

async function stateChangeProbe(page, test, expectation) {
  const before = await bodyText(page);
  const selectors = ["button", "[role='button']", "input[type='range']", "input[type='checkbox']", "select", "a[href='#']"];
  const clicked = await clickFirst(page, selectors);
  const after = await bodyText(page);
  const changed = after !== before;
  const observed = { before, after, clicked, changed };
  if (changed) return pass(test, observed, { expectation }, observed);
  if (test === "progress-bar-visible-value") {
    const hasProgress = (await page.locator("progress, [role='progressbar']").count()) > 0 || /\d+\s?%/.test(after);
    if (hasProgress) return pass(test, { ...observed, hasProgress }, { progressVisible: true }, { hasProgress });
  }
  if (test === "gallery-navigation-or-selection") {
    const imageCount = await page.locator("img, figure, [class*='image'], [class*='gallery']").count();
    if (imageCount >= 2) return pass(test, { ...observed, imageCount }, { mockupImagesVisible: true }, { imageCount });
  }
  return fail(test, "visible state did not change after interaction", observed, expectedFor(test), observed, "visible_state_change_missing");
}

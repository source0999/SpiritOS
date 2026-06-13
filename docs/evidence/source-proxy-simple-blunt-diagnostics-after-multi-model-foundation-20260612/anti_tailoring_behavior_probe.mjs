import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const runRoot = path.resolve(process.argv[2] ?? 'anti-tailoring-random-10-runs');
const outputName = process.argv[3] || 'anti-tailoring-random-10-browser-behavior-results.json';

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeJson(file, value) {
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function localPath(remoteOrLocal) {
  if (!remoteOrLocal) return '';
  return path.resolve(remoteOrLocal.replace('/home/source/SpiritOS', 'Z:'));
}

async function snapshot(page) {
  return {
    title: await page.title().catch(() => ''),
    bodyText: await page.locator('body').innerText({ timeout: 3000 }).catch(() => ''),
    elementCounts: await page.evaluate(() => ({
      buttons: document.querySelectorAll('button').length,
      inputs: document.querySelectorAll('input, textarea, select').length,
      links: document.querySelectorAll('a').length,
      canvas: document.querySelectorAll('canvas').length,
      scripts: document.querySelectorAll('script').length,
      stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length,
    })),
  };
}

async function fillAll(page, text) {
  const inputs = await page.locator('input, textarea').all();
  for (let i = 0; i < inputs.length; i += 1) {
    const value = i === 0 ? text : String(i + 2);
    await inputs[i].fill(value).catch(() => {});
  }
  return inputs.length;
}

async function clickFirst(page, selector = 'button') {
  const count = await page.locator(selector).count();
  if (count < 1) return false;
  await page.locator(selector).first().click({ timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(500);
  return true;
}

async function probeGenericAdd(page, prompt, testText) {
  const before = await page.locator('body').innerText().catch(() => '');
  const filled = await fillAll(page, testText);
  const clicked = await clickFirst(page);
  await page.keyboard.press('Enter').catch(() => {});
  await page.waitForTimeout(500);
  const after = await page.locator('body').innerText().catch(() => '');
  const appears = after.includes(testText);
  const needsNotePersistence = /\b(notes?|scratch|jot|memo)\b/i.test(prompt);
  const needsListPersistence = /checklist|grocery|pantry|\blist\b|packing|farmers/i.test(prompt);
  const isCalculator = /tip|split|bill|share|money|pizza|gas|cost|calculator/i.test(prompt);
  const requiresTextPersistence = needsNotePersistence || needsListPersistence;
  let passed = filled > 0 && (appears || after !== before);
  let failureBucket = 'generic_no_visible_state_change';
  let expected = 'input plus action creates visible state change';
  if (isCalculator) {
    passed = filled > 0 && after !== before && /\d/.test(after);
    failureBucket = 'calculator_no_visible_result_update';
    expected = 'numeric input creates a visible numeric result update';
  } else if (requiresTextPersistence) {
    passed = filled > 0 && appears;
    failureBucket = needsNotePersistence ? 'notes_saved_status_without_note_text' : 'checklist_status_without_item_text';
    expected = needsNotePersistence ? 'entered note text remains visible after action' : 'entered checklist/list text remains visible after action';
  }
  return {
    test: `${prompt}-visible-state-change`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected,
    primary_behavior_failure_bucket: passed ? '' : failureBucket,
    failureBucket: passed ? '' : failureBucket,
    actual: { before, after, filled, clicked, appears },
  };
}

async function probeClickTracker(page, prompt) {
  const before = await page.locator('body').innerText().catch(() => '');
  const clicked = await clickFirst(page);
  await page.waitForTimeout(500);
  const after = await page.locator('body').innerText().catch(() => '');
  const passed = clicked && after !== before;
  return {
    test: `${prompt}-click-tracker-state-change`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'tracker control visibly changes progress state',
    primary_behavior_failure_bucket: passed ? '' : 'tracker_control_no_visible_progress_change',
    failureBucket: passed ? '' : 'tracker_control_no_visible_progress_change',
    actual: { before, after, clicked },
  };
}

async function probeTimer(page, prompt) {
  const before = await page.locator('body').innerText().catch(() => '');
  await clickFirst(page);
  await page.waitForTimeout(1200);
  const afterStart = await page.locator('body').innerText().catch(() => '');
  const buttons = await page.locator('button').allTextContents().catch(() => []);
  const stopIndex = buttons.findIndex((text) => /stop|pause/i.test(text));
  if (stopIndex >= 0) await page.locator('button').nth(stopIndex).click().catch(() => {});
  await page.waitForTimeout(700);
  const afterStop = await page.locator('body').innerText().catch(() => '');
  const passed = afterStart !== before && afterStop === afterStop;
  const failureBucket = 'timer_no_visible_change_after_start';
  const secondaryBucket = !passed && afterStop !== before ? 'timer_state_changed_after_wrong_action' : '';
  return {
    test: `${prompt}-timer-change`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'timer text changes after start',
    primary_behavior_failure_bucket: passed ? '' : failureBucket,
    secondary_behavior_failure_bucket: passed ? '' : secondaryBucket,
    failureBucket: passed ? '' : failureBucket,
    actual: { before, afterStart, afterStop, clickedStop: stopIndex >= 0 },
  };
}

async function probeTheme(page, prompt) {
  const before = await page.evaluate(() => {
    const style = getComputedStyle(document.body);
    return { bg: style.backgroundColor, color: style.color, cls: document.body.className };
  });
  await clickFirst(page, 'button, input[type="checkbox"]');
  const after = await page.evaluate(() => {
    const style = getComputedStyle(document.body);
    return { bg: style.backgroundColor, color: style.color, cls: document.body.className };
  });
  const passed = JSON.stringify(before) !== JSON.stringify(after);
  return {
    test: `${prompt}-theme-computed-change`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'computed color or theme class changes',
    primary_behavior_failure_bucket: passed ? '' : 'theme_no_computed_state_change',
    failureBucket: passed ? '' : 'theme_no_computed_state_change',
    actual: { before, after },
  };
}

async function probePlayer(page, prompt) {
  const before = await page.locator('body').innerText().catch(() => '');
  const clicked = await clickFirst(page);
  const after = await page.locator('body').innerText().catch(() => '');
  const passed = clicked && after !== before;
  return {
    test: `${prompt}-player-control-change`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'play/pause or player control visibly changes state',
    primary_behavior_failure_bucket: passed ? '' : 'player_control_no_visible_state_change',
    failureBucket: passed ? '' : 'player_control_no_visible_state_change',
    actual: { before, after, clicked },
  };
}

async function probeForecast(page, prompt) {
  const before = await page.locator('body').innerText().catch(() => '');
  await fillAll(page, 'Codexville');
  const clicked = await clickFirst(page);
  const after = await page.locator('body').innerText().catch(() => '');
  const hasWeatherTerms = /(temp|forecast|weather|condition|cloud|rain|sun|deg|°)/i.test(after);
  const passed = hasWeatherTerms && (clicked ? after !== before : after.length > 0);
  return {
    test: `${prompt}-forecast-fields-or-update`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'weather-like fields render and control changes content if present',
    primary_behavior_failure_bucket: passed ? '' : 'weather_static_when_update_expected',
    failureBucket: passed ? '' : 'weather_static_when_update_expected',
    actual: { before, after, clicked, hasWeatherTerms },
  };
}

async function probePassword(page, prompt) {
  const input = page.locator('input, textarea').first();
  if ((await input.count()) < 1) {
    return {
      test: `${prompt}-password-feedback`,
      verdict: 'FAIL',
      passed: false,
      expected: 'password input exists',
      primary_behavior_failure_bucket: 'password_no_visible_strength_text_change',
      failureBucket: 'password_no_visible_strength_text_change',
      actual: { input: false },
    };
  }
  await input.fill('abc');
  await page.waitForTimeout(300);
  const weak = await page.locator('body').innerText().catch(() => '');
  await input.fill('LongerPass123!xyz');
  await page.waitForTimeout(300);
  const strong = await page.locator('body').innerText().catch(() => '');
  const passed = weak !== strong && /(weak|strong|safe|strength|medium|good|poor)/i.test(`${weak} ${strong}`);
  return {
    test: `${prompt}-password-feedback`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'weak and stronger inputs change safety text',
    primary_behavior_failure_bucket: passed ? '' : 'password_no_visible_strength_text_change',
    failureBucket: passed ? '' : 'password_no_visible_strength_text_change',
    actual: { weak, strong, changed: weak !== strong },
  };
}

async function probeDoodle(page, prompt) {
  const canvas = page.locator('canvas').first();
  if ((await canvas.count()) < 1) {
    return {
      test: `${prompt}-drawing-surface-change`,
      verdict: 'FAIL',
      passed: false,
      expected: 'canvas exists and pixels change',
      primary_behavior_failure_bucket: 'drawing_canvas_no_pixel_change',
      failureBucket: 'drawing_canvas_no_pixel_change',
      actual: { canvas: false },
    };
  }
  const before = await canvas.evaluate((node) => node.toDataURL()).catch(() => '');
  const box = await canvas.boundingBox();
  if (box) {
    await page.mouse.move(box.x + 20, box.y + 20);
    await page.mouse.down();
    await page.mouse.move(box.x + 120, box.y + 90, { steps: 8 });
    await page.mouse.up();
  }
  await page.waitForTimeout(300);
  const after = await canvas.evaluate((node) => node.toDataURL()).catch(() => '');
  const passed = Boolean(box && before && after && before !== after);
  return {
    test: `${prompt}-drawing-surface-change`,
    verdict: passed ? 'PASS' : 'FAIL',
    passed,
    expected: 'mouse drag changes canvas pixels',
    primary_behavior_failure_bucket: passed ? '' : 'drawing_canvas_no_pixel_change',
    failureBucket: passed ? '' : 'drawing_canvas_no_pixel_change',
    actual: { canvas: true, box, changed: before !== after },
  };
}

async function runBehaviorProbe(page, prompt) {
  if (/timer|countdown|steep/i.test(prompt)) return probeTimer(page, prompt);
  if (/lite|light|dark|night|theme|day|midnight|mode|toggle|sunrise/i.test(prompt)) return probeTheme(page, prompt);
  if (/forecast|weather/i.test(prompt)) return probeForecast(page, prompt);
  if (/podcast|player|mixtape|music|audio|radio/i.test(prompt)) return probePlayer(page, prompt);
  if (/password|safety|passphrase|strength|meter|gauge/i.test(prompt)) return probePassword(page, prompt);
  if (/doodle|drawing|draw|sketch|canvas/i.test(prompt)) return probeDoodle(page, prompt);
  if (/tip|split|bill|share|money|pizza|gas|cost/i.test(prompt)) return probeGenericAdd(page, prompt, '42');
  if (/grocery|pantry|checklist|\blist\b|packing/i.test(prompt)) return probeGenericAdd(page, prompt, 'bananas');
  if (/water|glass|coffee|cup|counter|pushup|rep/i.test(prompt)) return probeClickTracker(page, prompt);
  if (/\b(notes?|scratch|jot|memo)\b/i.test(prompt)) return probeGenericAdd(page, prompt, 'scratch proof note');
  return probeGenericAdd(page, prompt, 'proof item');
}

const browser = await chromium.launch({ headless: true });
const aggregate = [];

for (const entry of fs.readdirSync(runRoot, { withFileTypes: true }).filter((item) => item.isDirectory())) {
  const dir = path.join(runRoot, entry.name);
  const scoreFile = path.join(dir, 'score.json');
  if (!fs.existsSync(scoreFile)) continue;
  const score = readJson(scoreFile);
  const htmlPath = localPath(score.selected_preview_path);
  const consoleMessages = [];
  const pageErrors = [];
  let openProbe;
  let behaviorProbe;

  if (!htmlPath || !fs.existsSync(htmlPath)) {
    openProbe = {
      opened: false,
      reason: score.preview_selection_reason || 'missing preview',
      selected_preview_path: score.selected_preview_path || '',
    };
      behaviorProbe = {
        test: `${score.prompt}-missing-preview`,
        verdict: 'FAIL',
        passed: false,
        expected: 'openable generated preview exists before behavior probe',
        primary_behavior_failure_bucket: score.route_status === 'EXPECTED-BLOCKED' ? 'route_blocked_no_preview' : 'preview_resolution_failed',
        failureBucket: score.route_status === 'EXPECTED-BLOCKED' ? 'route_blocked_no_preview' : 'preview_resolution_failed',
        actual: { selected_preview_path: score.selected_preview_path || '' },
      };
  } else {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    page.on('console', (msg) => consoleMessages.push({ type: msg.type(), text: msg.text() }));
    page.on('pageerror', (err) => pageErrors.push(String(err?.message ?? err)));
    try {
      await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load', timeout: 15000 });
      await page.waitForTimeout(500);
      openProbe = { opened: true, path: htmlPath, ...(await snapshot(page)), consoleMessages, pageErrors };
      behaviorProbe = await runBehaviorProbe(page, score.prompt);
      behaviorProbe.path = htmlPath;
    } catch (error) {
      openProbe = { opened: false, path: htmlPath, error: String(error?.message ?? error), consoleMessages, pageErrors };
      behaviorProbe = {
        test: `${score.prompt}-open-error`,
        verdict: 'FAIL',
        passed: false,
        expected: 'preview opens before behavior probe',
        primary_behavior_failure_bucket: 'preview_resolution_failed',
        failureBucket: 'preview_resolution_failed',
        actual: { error: String(error?.message ?? error) },
      };
    } finally {
      await page.close().catch(() => {});
    }
  }

  writeJson(path.join(dir, 'browser-open-console.json'), openProbe);
  writeJson(path.join(dir, 'behavior-probe.json'), behaviorProbe);
  aggregate.push({
    run: entry.name,
    prompt: score.prompt,
    route_status: score.route_status,
    canonical_final_verdict: score.canonical_final_verdict,
    preview_path_local: htmlPath,
    open_probe: openProbe,
    behavior_probe: behaviorProbe,
  });
}

await browser.close();
writeJson(path.join(path.dirname(runRoot), outputName), { results: aggregate });
console.log(JSON.stringify({ results: aggregate.length, pass: aggregate.filter((item) => item.behavior_probe.passed).length }, null, 2));

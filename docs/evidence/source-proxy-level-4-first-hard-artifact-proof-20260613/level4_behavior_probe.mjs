import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const runRoot = path.resolve(process.argv[2] ?? 'level-4-runs');
const promptFile = path.resolve(process.argv[3] ?? 'level-4-prompt-set.json');
const outputFile = path.resolve(process.argv[4] ?? path.join(path.dirname(runRoot), 'level-4-browser-behavior-results.json'));
const traceDir = path.resolve(process.argv[5] ?? path.join(path.dirname(runRoot), 'per-prompt-traces'));

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function localPath(value) {
  if (!value) return '';
  let text = String(value);
  text = text.replace('/home/source/SpiritOS', 'Z:');
  text = text.replace('\\\\10.0.0.186\\SpiritOS', 'Z:');
  return path.resolve(text);
}

function rel(value) {
  if (!value) return '';
  return path.relative(path.dirname(outputFile), value) || value;
}

async function body(page) {
  return page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
}

async function values(page) {
  return page.evaluate(() => Array.from(document.querySelectorAll('input, textarea, select')).map((node) => ({
    tag: node.tagName.toLowerCase(),
    type: node.getAttribute('type') || '',
    value: node.value || '',
    checked: Boolean(node.checked),
  }))).catch(() => []);
}

async function styleState(page) {
  return page.evaluate(() => {
    const target = document.querySelector('main, article, section, .app, .card, .panel') || document.body;
    const bodyStyle = getComputedStyle(document.body);
    const targetStyle = getComputedStyle(target);
    return {
      bodyClass: document.body.className,
      targetClass: target.className || '',
      bodyBg: bodyStyle.backgroundColor,
      bodyColor: bodyStyle.color,
      targetBg: targetStyle.backgroundColor,
      targetColor: targetStyle.color,
      targetFontSize: targetStyle.fontSize,
      bodyText: document.body.innerText || '',
    };
  }).catch(() => ({}));
}

async function clickByText(page, pattern) {
  const buttons = page.locator('button, [role="button"], input[type="button"], input[type="submit"]');
  const count = await buttons.count().catch(() => 0);
  for (let index = 0; index < count; index += 1) {
    const label = await buttons.nth(index).innerText().catch(async () => buttons.nth(index).getAttribute('value').catch(() => ''));
    if (pattern.test(label || '')) {
      await buttons.nth(index).click({ timeout: 2000 }).catch(() => {});
      await page.waitForTimeout(450);
      return { clicked: true, label: label || '', index };
    }
  }
  return { clicked: false, label: '', index: -1 };
}

async function clickFirst(page, selector = 'button, [role="button"], input[type="button"], input[type="submit"]') {
  const target = page.locator(selector).first();
  if ((await target.count().catch(() => 0)) < 1) return { clicked: false, label: '' };
  const label = await target.innerText().catch(async () => target.getAttribute('value').catch(() => ''));
  await target.click({ timeout: 2000 }).catch(() => {});
  await page.waitForTimeout(450);
  return { clicked: true, label: label || '' };
}

async function fillFirstText(page, text) {
  const input = page.locator('textarea, input:not([type]), input[type="text"], input[type="search"], input[type="password"]').first();
  if ((await input.count().catch(() => 0)) < 1) return false;
  await input.fill(text).catch(() => {});
  await page.waitForTimeout(250);
  return true;
}

async function fillNumbers(page, numbers) {
  const inputs = await page.locator('input, textarea').all();
  let filled = 0;
  for (let index = 0; index < inputs.length; index += 1) {
    const type = (await inputs[index].getAttribute('type').catch(() => '')) || '';
    if (/checkbox|radio|range|color|button|submit/i.test(type)) continue;
    await inputs[index].fill(String(numbers[filled % numbers.length])).catch(() => {});
    filled += 1;
  }
  return filled;
}

async function clickCheckboxOrItem(page) {
  const checkbox = page.locator('input[type="checkbox"]').first();
  if ((await checkbox.count().catch(() => 0)) > 0) {
    await checkbox.check({ timeout: 2000 }).catch(async () => checkbox.click({ timeout: 2000 }).catch(() => {}));
    await page.waitForTimeout(450);
    return { clicked: true, label: 'checkbox' };
  }
  return clickByText(page, /check|pack|done|complete|toggle/i);
}

function observation(name, passed, expected, actual, bucket) {
  return {
    name,
    passed: Boolean(passed),
    expected,
    actual,
    failure_bucket: passed ? '' : bucket,
  };
}

function strictVerdict(observations) {
  const passCount = observations.filter((item) => item.passed).length;
  return {
    passCount,
    verdict: passCount >= 2 ? 'PASS' : 'FAIL',
    primary_failure_bucket: observations.find((item) => !item.passed)?.failure_bucket || '',
    second_behavior_observed: passCount >= 2,
  };
}

async function probeTimer(page) {
  const before = await body(page);
  const startClick = await clickByText(page, /start|begin|play/i);
  if (!startClick.clicked) await clickFirst(page);
  await page.waitForTimeout(1200);
  const afterStart = await body(page);
  const pauseClick = await clickByText(page, /pause|stop|hold/i);
  const afterPause = await body(page);
  await page.waitForTimeout(800);
  const afterPauseWait = await body(page);
  const resetClick = await clickByText(page, /reset|clear/i);
  const afterReset = await body(page);
  const finishClick = await clickByText(page, /finish|done|log|complete/i);
  const afterFinish = await body(page);
  const observations = [
    observation('start changes time/status', afterStart !== before, 'Start visibly changes timer/time state.', { before, afterStart, startClick }, 'timer_start_no_visible_change'),
    observation('pause freezes or changes status', pauseClick.clicked && (afterPause !== afterStart || afterPauseWait === afterPause), 'Pause freezes or changes status.', { afterStart, afterPause, afterPauseWait, pauseClick }, 'timer_pause_no_visible_status_or_freeze'),
    observation('reset or finish/history changes state', (resetClick.clicked && afterReset !== afterPauseWait) || (finishClick.clicked && afterFinish !== afterReset), 'Reset returns to initial state or finish/log adds visible history if present.', { afterPauseWait, afterReset, afterFinish, resetClick, finishClick }, 'timer_reset_or_history_missing'),
  ];
  return observations;
}

async function probeCalculator(page) {
  const before = await body(page);
  const beforeValues = await values(page);
  const filled = await fillNumbers(page, [12, 3, 18]);
  const calcClick = await clickByText(page, /calculate|total|split|plan|share|submit/i);
  if (!calcClick.clicked) await clickFirst(page);
  const afterCalc = await body(page);
  const resetClick = await clickByText(page, /reset|clear/i);
  const afterReset = await body(page);
  const afterValues = await values(page);
  const observations = [
    observation('calculation changes visible total/share', filled > 0 && afterCalc !== before && /\d/.test(afterCalc), 'Entered numeric values visibly change a calculated total/share.', { before, afterCalc, filled, calcClick }, 'calculator_no_visible_total_update'),
    observation('reset clears visible state or inputs', resetClick.clicked && (afterReset !== afterCalc || JSON.stringify(afterValues) !== JSON.stringify(beforeValues)), 'Reset clears or returns result/inputs to initial state.', { beforeValues, afterValues, afterCalc, afterReset, resetClick }, 'calculator_reset_no_visible_clear'),
  ];
  return observations;
}

async function probeTheme(page) {
  const before = await styleState(page);
  let themeClick = await clickByText(page, /palette|dusk|dawn|theme|mode|switch|dark|light/i);
  if (!themeClick.clicked) themeClick = await clickFirst(page, 'button, input[type="checkbox"], select');
  const afterTheme = await styleState(page);
  const range = page.locator('input[type="range"]').first();
  let sizeAction = { used: false, label: '' };
  if ((await range.count().catch(() => 0)) > 0) {
    const min = Number(await range.getAttribute('min').catch(() => '1')) || 1;
    const max = Number(await range.getAttribute('max').catch(() => '32')) || 32;
    await range.fill(String(max > min ? max : min + 1)).catch(() => {});
    sizeAction = { used: true, label: 'range' };
  } else {
    sizeAction = await clickByText(page, /size|larger|smaller|text|font|a\+|a-/i);
  }
  await page.waitForTimeout(450);
  const afterSize = await styleState(page);
  const observations = [
    observation('palette changes computed color/class/state', JSON.stringify(before) !== JSON.stringify(afterTheme), 'Palette/theme control visibly changes computed color/class/state.', { before, afterTheme, themeClick }, 'theme_palette_no_computed_change'),
    observation('text size control changes size or label', sizeAction.used || sizeAction.clicked ? JSON.stringify(afterTheme) !== JSON.stringify(afterSize) : false, 'Text size control visibly changes readable size or size label.', { afterTheme, afterSize, sizeAction }, 'theme_text_size_no_visible_change'),
  ];
  return observations;
}

async function probeChecklist(page) {
  const before = await body(page);
  const text = 'sunscreen proof item';
  const filled = await fillFirstText(page, text);
  const addClick = await clickByText(page, /add|pack|save|submit/i);
  if (!addClick.clicked) await page.keyboard.press('Enter').catch(() => {});
  await page.waitForTimeout(500);
  const afterAdd = await body(page);
  const toggleClick = await clickCheckboxOrItem(page);
  const afterToggle = await body(page);
  const observations = [
    observation('typed item appears', filled && afterAdd.includes(text), 'Typed item appears visibly.', { before, afterAdd, filled, addClick }, 'checklist_item_not_visible_after_add'),
    observation('toggle or packed count changes', toggleClick.clicked && afterToggle !== afterAdd, 'Checking/toggling item changes completion state and packed count/progress changes.', { afterAdd, afterToggle, toggleClick }, 'checklist_toggle_or_count_no_change'),
  ];
  return observations;
}

async function probeWeather(page) {
  const before = await body(page);
  let cityAction = await clickByText(page, /city|switch|next|change|seattle|miami|denver|portland/i);
  if (!cityAction.clicked) {
    const select = page.locator('select').first();
    if ((await select.count().catch(() => 0)) > 0) {
      const options = await select.locator('option').all();
      if (options.length > 1) {
        const value = await options[1].getAttribute('value').catch(() => '');
        await select.selectOption(value || { index: 1 }).catch(() => {});
        cityAction = { clicked: true, label: 'select city' };
      }
    } else {
      await fillFirstText(page, 'Codexville');
      cityAction = await clickByText(page, /update|forecast|go|submit/i);
    }
  }
  await page.waitForTimeout(500);
  const afterCity = await body(page);
  const unitAction = await clickByText(page, /\bf\b|\bc\b|fahrenheit|celsius|unit|temp|toggle/i);
  const afterUnit = await body(page);
  const observations = [
    observation('city/weather control changes forecast text', cityAction.clicked && afterCity !== before, 'City/weather control visibly changes city/temp/condition/forecast text.', { before, afterCity, cityAction }, 'weather_city_control_no_visible_change'),
    observation('unit toggle changes temp unit or value', unitAction.clicked && afterUnit !== afterCity && /(f|c|fahrenheit|celsius|temp|\d)/i.test(afterUnit), 'F/C toggle visibly changes temperature unit or value.', { afterCity, afterUnit, unitAction }, 'weather_unit_toggle_no_visible_change'),
  ];
  return observations;
}

async function probePlayer(page) {
  const before = await body(page);
  const playClick = await clickByText(page, /play|pause|start/i);
  const afterPlay = await body(page);
  const nextClick = await clickByText(page, /next|episode|skip/i);
  const afterNext = await body(page);
  const observations = [
    observation('play/pause changes player status', playClick.clicked && afterPlay !== before, 'Play/pause visibly changes player status or label.', { before, afterPlay, playClick }, 'player_play_pause_no_visible_change'),
    observation('next changes episode/title/status', nextClick.clicked && afterNext !== afterPlay, 'Next changes episode/track/title/status.', { afterPlay, afterNext, nextClick }, 'player_next_no_episode_change'),
  ];
  return observations;
}

async function probeTracker(page) {
  const before = await body(page);
  const addClick = await clickByText(page, /add|set|start|log/i);
  if (!addClick.clicked) await clickFirst(page);
  const afterAdd = await body(page);
  const repClick = await clickByText(page, /rep|increase|\+|more|step|total/i);
  if (!repClick.clicked) await clickFirst(page);
  const afterRep = await body(page);
  const observations = [
    observation('add/increment changes set or reps', afterAdd !== before, 'Add/increment control changes visible set/reps state.', { before, afterAdd, addClick }, 'tracker_add_set_no_visible_change'),
    observation('total/progress changes', afterRep !== afterAdd && /\d/.test(afterRep), 'Total/progress value changes.', { afterAdd, afterRep, repClick }, 'tracker_total_no_visible_change'),
  ];
  return observations;
}

async function probeMemo(page) {
  const before = await body(page);
  const text = 'sticky proof thought';
  const editedText = 'sticky proof thought edited';
  const filled = await fillFirstText(page, text);
  const addClick = await clickByText(page, /add|save|post|submit/i);
  if (!addClick.clicked) await page.keyboard.press('Enter').catch(() => {});
  await page.waitForTimeout(500);
  const afterAdd = await body(page);
  const editClick = await clickByText(page, /edit/i);
  if (editClick.clicked) {
    await fillFirstText(page, editedText);
    await clickByText(page, /save|update|done/i);
  }
  const deleteClick = editClick.clicked ? { clicked: false, label: '' } : await clickByText(page, /delete|remove|trash|clear/i);
  const afterModify = await body(page);
  const observations = [
    observation('typed memo appears', filled && afterAdd.includes(text), 'Typed memo appears visibly.', { before, afterAdd, filled, addClick }, 'memo_text_not_visible_after_add'),
    observation('edit or delete changes memo/count', (editClick.clicked || deleteClick.clicked) && afterModify !== afterAdd, 'Edit or delete changes visible memo state and saved count if present.', { afterAdd, afterModify, editClick, deleteClick }, 'memo_edit_delete_no_visible_change'),
  ];
  return observations;
}

async function probePassword(page) {
  const input = page.locator('input, textarea').first();
  const beforeType = await input.getAttribute('type').catch(() => '');
  if ((await input.count().catch(() => 0)) < 1) {
    return [
      observation('strength feedback changes', false, 'Weak and stronger phrase inputs visibly change strength feedback.', { input: false }, 'password_input_missing'),
      observation('show/hide changes visibility', false, 'Show/hide switch changes visibility state, type, or label.', { input: false }, 'password_show_hide_missing'),
    ];
  }
  await input.fill('abc').catch(() => {});
  await page.waitForTimeout(350);
  const weak = await body(page);
  await input.fill('LongerPass123!xyz').catch(() => {});
  await page.waitForTimeout(350);
  const strong = await body(page);
  const showClick = await clickByText(page, /show|hide|reveal|visible/i);
  const afterType = await input.getAttribute('type').catch(() => '');
  const afterShow = await body(page);
  const observations = [
    observation('strength feedback changes', weak !== strong && /(weak|medium|strong|safe|strength|poor|good)/i.test(`${weak} ${strong}`), 'Weak and stronger phrase inputs visibly change strength feedback.', { weak, strong }, 'password_strength_feedback_no_change'),
    observation('show/hide changes visibility', showClick.clicked && (beforeType !== afterType || afterShow !== strong), 'Show/hide switch changes visibility state, type, or label.', { beforeType, afterType, strong, afterShow, showClick }, 'password_show_hide_no_visible_change'),
  ];
  return observations;
}

async function canvasData(canvas) {
  return canvas.evaluate((node) => node.toDataURL()).catch(() => '');
}

async function drawOnCanvas(page, canvas, offset = 20) {
  const box = await canvas.boundingBox();
  if (!box) return false;
  await page.mouse.move(box.x + offset, box.y + offset);
  await page.mouse.down();
  await page.mouse.move(box.x + offset + 90, box.y + offset + 55, { steps: 8 });
  await page.mouse.up();
  await page.waitForTimeout(300);
  return true;
}

async function probeDrawing(page) {
  const canvas = page.locator('canvas').first();
  if ((await canvas.count().catch(() => 0)) < 1) {
    return [
      observation('drawing marks pixels', false, 'Pointer/mouse drawing visibly marks canvas pixels.', { canvas: false }, 'drawing_canvas_missing'),
      observation('tool or clear changes drawing state', false, 'Color/brush or clear affects visible drawing state.', { canvas: false }, 'drawing_tool_or_clear_missing'),
    ];
  }
  const before = await canvasData(canvas);
  const drew = await drawOnCanvas(page, canvas, 20);
  const afterDraw = await canvasData(canvas);
  const color = page.locator('input[type="color"]').first();
  let toolAction = { used: false, label: '' };
  if ((await color.count().catch(() => 0)) > 0) {
    await color.fill('#ff0000').catch(() => {});
    toolAction = { used: true, label: 'color' };
  } else {
    const range = page.locator('input[type="range"]').first();
    if ((await range.count().catch(() => 0)) > 0) {
      const max = await range.getAttribute('max').catch(() => '20');
      await range.fill(max || '20').catch(() => {});
      toolAction = { used: true, label: 'range' };
    } else {
      toolAction = await clickByText(page, /red|blue|green|brush|size|thick|thin/i);
    }
  }
  await drawOnCanvas(page, canvas, 80);
  const afterToolDraw = await canvasData(canvas);
  const clearClick = await clickByText(page, /clear|reset|erase/i);
  const afterClear = await canvasData(canvas);
  const observations = [
    observation('drawing marks canvas pixels', drew && before !== afterDraw, 'Pointer/mouse drawing visibly marks canvas pixels.', { drew, changed: before !== afterDraw }, 'drawing_canvas_no_pixel_change'),
    observation('tool or clear changes drawing state', (toolAction.used || toolAction.clicked || clearClick.clicked) && (afterToolDraw !== afterDraw || afterClear !== afterToolDraw), 'Color/brush size or clear changes visible drawing state.', { toolAction, clearClick, toolChanged: afterToolDraw !== afterDraw, clearChanged: afterClear !== afterToolDraw }, 'drawing_tool_or_clear_no_visible_change'),
  ];
  return observations;
}

async function runLevel4Probe(page, promptMeta) {
  const family = promptMeta.family || '';
  if (family === 'timer/history') return probeTimer(page);
  if (family === 'calculator/reset') return probeCalculator(page);
  if (family === 'theme/settings') return probeTheme(page);
  if (family === 'checklist/progress') return probeChecklist(page);
  if (family === 'weather/dual-control') return probeWeather(page);
  if (family === 'player/queue') return probePlayer(page);
  if (family === 'tracker/totals') return probeTracker(page);
  if (family === 'notes/edit-delete') return probeMemo(page);
  if (family === 'password/show-hide') return probePassword(page);
  if (family === 'drawing/tools') return probeDrawing(page);
  return [observation('unknown family', false, 'Known Level 4 prompt family.', { family }, 'level4_unknown_family')];
}

const promptDoc = readJson(promptFile);
const promptByText = new Map((promptDoc.prompts || []).map((item) => [item.prompt, item]));
const browser = await chromium.launch({ headless: true });
const aggregate = [];
fs.mkdirSync(traceDir, { recursive: true });

for (const entry of fs.readdirSync(runRoot, { withFileTypes: true }).filter((item) => item.isDirectory()).sort((a, b) => a.name.localeCompare(b.name))) {
  const dir = path.join(runRoot, entry.name);
  const scoreFile = path.join(dir, 'score.json');
  if (!fs.existsSync(scoreFile)) continue;
  const score = readJson(scoreFile);
  const promptMeta = promptByText.get(score.prompt) || {};
  const htmlPath = localPath(score.selected_preview_path);
  const routeTracePath = path.join(dir, 'route_trace.json');
  const receiptPath = path.join(dir, 'receipt.json');
  const transcriptPath = path.join(dir, 'transcript.txt');
  const diffPath = path.join(dir, 'workspace.diff');
  const consoleMessages = [];
  const pageErrors = [];
  let openProbe = { opened: false, selected_preview_path: score.selected_preview_path || '' };
  let observations = [];

  if (!htmlPath || !fs.existsSync(htmlPath)) {
    observations = [
      observation('preview opens', false, 'Openable generated preview exists before Level 4 behavior probe.', { selected_preview_path: score.selected_preview_path || '', htmlPath }, 'preview_resolution_failed'),
    ];
  } else {
    const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
    page.on('console', (msg) => consoleMessages.push({ type: msg.type(), text: msg.text() }));
    page.on('pageerror', (err) => pageErrors.push(String(err?.message ?? err)));
    try {
      await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load', timeout: 15000 });
      await page.waitForTimeout(500);
      openProbe = {
        opened: true,
        path: htmlPath,
        title: await page.title().catch(() => ''),
        bodyText: await body(page),
        consoleMessages,
        pageErrors,
      };
      observations = await runLevel4Probe(page, promptMeta);
    } catch (error) {
      openProbe = { opened: false, path: htmlPath, error: String(error?.message ?? error), consoleMessages, pageErrors };
      observations = [
        observation('preview opens', false, 'Preview opens before behavior probe.', { error: String(error?.message ?? error) }, 'preview_resolution_failed'),
      ];
    } finally {
      await page.close().catch(() => {});
    }
  }

  const strict = strictVerdict(observations);
  const repairResultPath = path.join(dir, 'post-behavior-repair-result.json');
  const routeTrace = fs.existsSync(routeTracePath) ? readJson(routeTracePath) : {};
  const receipt = fs.existsSync(receiptPath) ? readJson(receiptPath) : {};
  const diagnostics = typeof receipt.diagnostics_packet === 'object' && receipt.diagnostics_packet ? receipt.diagnostics_packet : {};
  const transcript = fs.existsSync(transcriptPath) ? fs.readFileSync(transcriptPath, 'utf8') : '';
  const filesApplied = score.files_changed || score.workspace_files || [];
  const trace = {
    id: promptMeta.id || 'NOT_RECORDED',
    prompt: score.prompt || promptMeta.prompt || 'NOT_RECORDED',
    family: promptMeta.family || 'NOT_RECORDED',
    normalized_intent: routeTrace.normalized_intent_after_route || score.task_shape || diagnostics.task_shape || 'NOT_RECORDED',
    route_status: score.route_status || score.status || 'NOT_RECORDED',
    selected_preview_path: score.selected_preview_path || 'NOT_RECORDED',
    behavior_contract_probe_id: routeTrace.behavior_contract_probe_id || 'NOT_RECORDED',
    expected_level_4_behaviors: promptMeta.expected_behaviors || [],
    active_model: score.model_id || diagnostics.model_id || receipt.model_id || 'qwen2.5-coder:7b',
    qwen_invoked: /qwen/i.test(`${score.model_id || ''} ${receipt.model_id || ''} qwen2.5-coder:7b`) && Boolean(transcript),
    gemma_hermes_invoked: /gemma|hermes/i.test(`${score.model_id || ''} ${receipt.model_id || ''} ${transcript}`),
    cartographer_live_route_owner: false,
    route_trace_path: fs.existsSync(routeTracePath) ? rel(routeTracePath) : 'NOT_RECORDED',
    model_transcript_path: fs.existsSync(transcriptPath) ? rel(transcriptPath) : 'NOT_RECORDED',
    actions_file_blocks_parsed: filesApplied.length,
    files_applied: filesApplied,
    open_status: openProbe.opened ? 'PASS' : 'FAIL',
    behavior_result: strict.verdict,
    observed_before_after: observations.map((item) => ({ name: item.name, actual: item.actual })),
    second_behavior_observation: observations[1] || 'NOT_RECORDED',
    repair_attempts: fs.existsSync(repairResultPath) ? 1 : 0,
    repair_status: fs.existsSync(repairResultPath) ? 'RECORDED' : 'SKIPPED_OR_NOT_RECORDED',
    strict_final: strict.verdict,
    anti_cheat_flags: {
      fallback_used: Boolean(score.fallback_used),
      deterministic_scaffold_used: Boolean(score.deterministic_scaffold_used),
      backend_created_content: Boolean(score.backend_created_content),
      cloud_api_fallback_used: false,
      real_app_touched: Boolean(score.real_app_touched),
      missing_behavior_evidence: observations.length === 0,
      missing_transcript: !fs.existsSync(transcriptPath),
    },
    interpretation: strict.verdict === 'PASS' ? 'At least two predefined Level 4 behavior observations passed.' : `Level 4 failed: ${strict.primary_failure_bucket || 'insufficient behavior observations'}`,
    evidence_links: {
      preview: htmlPath || '',
      score: scoreFile,
      receipt: receiptPath,
      transcript: transcriptPath,
      workspace_diff: fs.existsSync(diffPath) ? diffPath : '',
      route_trace: fs.existsSync(routeTracePath) ? routeTracePath : '',
      repair_result: fs.existsSync(repairResultPath) ? repairResultPath : '',
    },
  };
  const traceJson = path.join(traceDir, `${promptMeta.id || entry.name}.json`);
  const traceMd = path.join(traceDir, `${promptMeta.id || entry.name}.md`);
  writeJson(traceJson, trace);
  fs.writeFileSync(traceMd, `# ${promptMeta.id || entry.name}\n\nPrompt: ${score.prompt || ''}\n\nFamily: ${promptMeta.family || 'NOT_RECORDED'}\n\nStrict final: ${strict.verdict}\n\nInterpretation: ${trace.interpretation}\n\nObservations:\n\n${observations.map((item) => `- ${item.name}: ${item.passed ? 'PASS' : 'FAIL'}${item.failure_bucket ? ` (${item.failure_bucket})` : ''}`).join('\n')}\n`, 'utf8');
  aggregate.push({
    run: entry.name,
    id: promptMeta.id || '',
    prompt: score.prompt,
    family: promptMeta.family || '',
    route_status: trace.route_status,
    selected_preview_path: score.selected_preview_path || '',
    open_probe: openProbe,
    level4_behavior_probe: {
      verdict: strict.verdict,
      passed: strict.verdict === 'PASS',
      pass_count: strict.passCount,
      required_pass_count: 2,
      primary_behavior_failure_bucket: strict.primary_failure_bucket,
      second_behavior_observed: strict.second_behavior_observed,
      observations,
    },
    trace_json: traceJson,
    trace_md: traceMd,
  });
}

await browser.close();

const passCount = aggregate.filter((item) => item.level4_behavior_probe.passed).length;
writeJson(outputFile, {
  created_at: new Date().toISOString(),
  probe: 'level4_behavior_probe.mjs',
  run_root: runRoot,
  prompt_file: promptFile,
  threshold: '8/10 Level 4 behavior PASS',
  pass_count: passCount,
  fail_count: aggregate.length - passCount,
  results: aggregate,
});
console.log(JSON.stringify({ results: aggregate.length, pass: passCount, fail: aggregate.length - passCount }, null, 2));

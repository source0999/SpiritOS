import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [, , htmlPathArg] = process.argv;
if (!htmlPathArg) {
  console.error('usage: node browser_open_console_probe.mjs HTML_PATH');
  process.exit(2);
}
const htmlPath = path.resolve(htmlPathArg);
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const consoleMessages = [];
const pageErrors = [];
page.on('console', msg => consoleMessages.push({ type: msg.type(), text: msg.text() }));
page.on('pageerror', err => pageErrors.push(String(err?.message ?? err)));
let result;
try {
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: 'load', timeout: 15000 });
  await page.waitForTimeout(500);
  const bodyText = await page.locator('body').innerText({ timeout: 3000 }).catch(() => '');
  const title = await page.title().catch(() => '');
  const counts = await page.evaluate(() => ({
    buttons: document.querySelectorAll('button').length,
    inputs: document.querySelectorAll('input, textarea, select').length,
    links: document.querySelectorAll('a').length,
    canvas: document.querySelectorAll('canvas').length,
    scripts: document.querySelectorAll('script').length,
    stylesheets: document.querySelectorAll('link[rel="stylesheet"]').length,
  }));
  result = { opened: true, title, bodyText, elementCounts: counts, consoleMessages, pageErrors };
} catch (error) {
  result = { opened: false, error: String(error?.message ?? error), consoleMessages, pageErrors };
} finally {
  await browser.close();
}
console.log(JSON.stringify(result, null, 2));

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const evidence = path.join(process.cwd(), 'docs/evidence/spiritflix-smart-tagging-s6-closeout-20260617');
const rawDir = path.join(evidence, 'raw/browser');
fs.mkdirSync(rawDir, { recursive: true });

const videoPath = '/tmp/spiritflix-s6-smoke/Beta Clip.mp4';
const item = {
  id: 'file:beta',
  name: 'Beta Clip.mp4',
  type: 'file',
  path: videoPath,
  parentPath: '/tmp/spiritflix-s6-smoke',
  playable: true,
  extension: '.mp4',
  sizeBytes: 100,
  modifiedAt: '2026-06-17T00:00:00.000Z'
};
const analysis = {
  version: 1,
  videoPath,
  pathKey: 'smoke-key',
  fileName: 'Beta Clip.mp4',
  fileSizeBytes: 100,
  mtimeMs: 1,
  analyzedAt: '2026-06-17T00:00:00.000Z',
  analyzerVersion: 'spiritflix-smart/s6-smoke',
  status: 'approved',
  safety: { safeToSuggest: false, reasons: ['smoke fixture'], requiresHumanReview: true },
  media: { durationSeconds: 120, width: 1920, height: 1080 },
  samples: [{ timestampSeconds: 10, timestampLabel: '10s', observations: ['fixture sample'], tags: [], confidence: 0 }],
  suggestedTags: [{ id: 'hd', label: 'HD', group: 'quality', confidence: 0.8, evidenceTimestamps: [], reviewRequired: false }],
  suggestedDisplayTitle: 'Beta Clip',
  suggestedFilename: 'Beta Clip Clean.mp4',
  suggestedCategory: 'test-category',
  suggestedCollections: ['smoke'],
  confidence: 0.8,
  notes: 'browser smoke fixture only',
  reviewedMetadata: {
    reviewedAt: '2026-06-17T00:00:00.000Z',
    reviewedBy: 'spiritflix-admin',
    reviewStatus: 'reviewed',
    approvedTagIds: ['hd'],
    rejectedTagIds: [],
    editedDisplayTitle: 'Beta Clip',
    editedFilenameSuggestion: 'Beta Clip Clean.mp4',
    editedCategory: 'test-category',
    editedCollections: ['smoke'],
    notes: 'approved fixture'
  }
};
const renamePreview = {
  sourcePath: videoPath,
  suggestedName: 'Beta Clip Clean.mp4',
  targetPath: '/tmp/spiritflix-s6-smoke/Beta Clip Clean.mp4',
  warnings: [],
  readyForLevel2Preview: true
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ ignoreHTTPSErrors: true, viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const consoleMessages = [];
  const pageErrors = [];
  const requests = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleMessages.push(msg.text());
  });
  page.on('pageerror', err => pageErrors.push(err.message));
  page.on('request', req => requests.push({ method: req.method(), url: req.url(), postData: req.postData() || '' }));

  await page.route('**/api/spiritflix/admin/smart/analysis**', async route => {
    const req = route.request();
    if (req.method() === 'GET') {
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ analysis, sidecarPath: '/tmp/spiritflix-s6-smoke/.spiritflix-admin/analysis/smoke-key.json' }) });
    }
    const body = req.postDataJSON();
    if (body.action === 'prepareRenamePreview') {
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ renamePreview }) });
    }
    if (body.action === 'exportMetadata') {
      return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ metadataPath: '/tmp/spiritflix-s6-smoke/.spiritflix-admin/metadata/smoke-key.json', metadata: { sourcePath: videoPath, displayTitle: 'Beta Clip', filenameSuggestion: 'Beta Clip Clean.mp4', category: 'test-category', collections: ['smoke'], approvedTags: [{ id: 'hd', label: 'HD', group: 'quality', confidence: 0.8 }], rejectedTagIds: [], reviewStatus: 'reviewed', reviewedAt: '2026-06-17T00:00:00.000Z', notes: 'approved fixture' } }) });
    }
    return route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ error: 'Unexpected action in smoke' }) });
  });

  await page.route('**/api/spiritflix/admin/thumbnail**', route => route.fulfill({ status: 204, body: '' }));
  await page.route('**/api/spiritflix/admin/image**', route => route.fulfill({ status: 204, body: '' }));
  await page.route('**/api/spiritflix/admin/jellyfin-index**', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [], source: 'smoke-fixture' }) }));
  await page.route('**/api/spiritflix/admin/library**', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [] }) }));
  await page.route('**/api/spiritflix/admin/fs**', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ currentPath: '/tmp/spiritflix-s6-smoke', parentPath: '/tmp', items: [item], breadcrumbs: [], totalRecordCount: 1, startIndex: 0, limit: 250 }) }));

  const baseUrl = process.env.SMOKE_BASE_URL || 'http://127.0.0.1:3000';
  await page.goto(`${baseUrl}/spiritflix/admin`, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.locator('[data-testid="admin-item-card"]', { hasText: 'Beta Clip.mp4' }).waitFor({ timeout: 15000 });
  await page.locator('[data-testid="admin-item-card"]', { hasText: 'Beta Clip.mp4' }).getByRole('button', { name: /Actions for Beta Clip\.mp4/i }).click();
  await page.getByRole('menuitem', { name: /^Smart tags$/i }).click();
  await page.getByRole('dialog', { name: 'Smart tag review' }).waitFor({ timeout: 15000 });
  await page.getByRole('heading', { name: 'Approved metadata' }).waitFor({ timeout: 15000 });
  await page.getByRole('button', { name: /Export approved metadata/i }).waitFor({ timeout: 5000 });
  await page.getByRole('button', { name: /Prepare rename preview/i }).click();
  await page.getByRole('heading', { name: 'Rename preview' }).waitFor({ timeout: 15000 });
  const renameSection = page.locator('.spiritflix-smart-review__section--rename-preview');
  await renameSection.getByText('Current filename').waitFor({ timeout: 5000 });
  await renameSection.getByText('Suggested filename').waitFor({ timeout: 5000 });
  await renameSection.getByText('Target path').waitFor({ timeout: 5000 });
  await renameSection.getByText('Warnings').waitFor({ timeout: 5000 });

  const forbiddenButtons = [];
  for (const name of [/Apply rename/i, /Apply move/i, /Confirm execute/i]) {
    if (await page.getByRole('button', { name }).count()) forbiddenButtons.push(String(name));
  }
  const gridMounted = await page.getByText('Beta Clip.mp4').count() > 0;
  const exportRequests = requests.filter(r => /exportMetadata/.test(r.postData));
  const executeRequests = requests.filter(r => /applyRename|applyMove|executeRename|executeMove/.test(r.postData));

  await page.screenshot({ path: path.join(rawDir, 'spiritflix-admin-s6-smoke.png'), fullPage: true });
  const result = {
    url: page.url(),
    smartPanelOpened: true,
    approvedMetadataVisible: true,
    exportButtonVisible: await page.getByRole('button', { name: /Export approved metadata/i }).count() > 0,
    prepareRenameButtonVisible: await page.getByRole('button', { name: /Prepare rename preview/i }).count() > 0,
    forbiddenButtons,
    renamePreviewVisible: true,
    gridMounted,
    consoleErrors: consoleMessages,
    pageErrors,
    exportRequests: exportRequests.length,
    executeRequests: executeRequests.length,
    note: 'API responses were intercepted with fixture data; export button was not clicked; prepare preview was intercepted and did not touch real media.'
  };
  fs.writeFileSync(path.join(rawDir, 'browser-smoke-result.json'), JSON.stringify(result, null, 2));
  await browser.close();
  if (forbiddenButtons.length || consoleMessages.length || pageErrors.length || exportRequests.length || executeRequests.length || !gridMounted) {
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(result, null, 2));
})().catch(err => {
  fs.writeFileSync(path.join(rawDir, 'browser-smoke-error.txt'), err.stack || String(err));
  console.error(err);
  process.exit(1);
});

// NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/guard.cjs
// API fixtures only; the parent task owns the single headless browser process.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');

const SCREENSHOT_DIR = '/tmp/claude-1000/-home-kimchungsik-projects-com-remakeday/cbe597d5-d41f-4842-8427-8fd331d806b7/scratchpad';

const CASES = [
  {
    name: 'login (401)',
    status: 401,
    headers: {},
    json: { detail: '로그인이 필요하다' },
    expectText: '로그인이 필요하다',
    check: async page => {
      await page.getByRole('link', { name: '랜딩으로' }).waitFor();
      assert.equal(await page.getByRole('link', { name: '랜딩으로' }).getAttribute('href'), '/');
    },
  },
  {
    name: 'daily_limit (403)',
    status: 403,
    headers: {},
    json: { code: 'daily_attempt_limit', detail: '오늘은 여기까지. 내일 다시 시작할 수 있다.' },
    expectText: '오늘은 여기까지',
  },
  {
    name: 'daily_cap (503)',
    status: 503,
    headers: {},
    json: { code: 'daily_cap', detail: '오늘 정원이 마감됐다.' },
    expectText: '정원이 마감',
  },
  {
    name: 'rate (429)',
    status: 429,
    headers: { 'retry-after': '7' },
    json: { detail: { detail: '요청이 너무 잦다', retry_after: 7 } },
    expectText: '7초',
  },
];

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  try {
    for (const testCase of CASES) {
      const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
      page.on('pageerror', error => errors.push(`${testCase.name}: ${error.message}`));
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.port !== '8500') return route.continue();
        if (url.pathname === '/sessions') {
          return route.fulfill({
            status: testCase.status,
            json: testCase.json,
            headers: {
              'access-control-allow-origin': 'http://localhost:3500',
              'access-control-allow-credentials': 'true',
              ...testCase.headers,
            },
          });
        }
        errors.push(`${testCase.name}: unexpected API ${url.pathname}`);
        return route.abort();
      });
      await page.goto('http://localhost:3500/play');
      await page.getByText(testCase.expectText, { exact: false }).waitFor();
      if (testCase.check) await testCase.check(page);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `guard-${testCase.name.split(' ')[0]}.png`) });
      await page.close();
    }
    assert.deepEqual(errors, []);
    console.log('PASS login/daily_limit/daily_cap/rate GuardScreen render at 390px');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

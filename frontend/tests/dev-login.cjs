// Run with Playwright available through NODE_PATH — the path below is one environment's example, not a fixed requirement.
// NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/dev-login.cjs
// 실서버(백엔드 8500 DEV_LOGIN=on, 프런트 3500 NEXT_PUBLIC_DEV_LOGIN=on) 대상.
// 개발 계정 id/password는 process.env(DEV_ACCOUNT_ID/DEV_ACCOUNT_PASSWORD) 우선, 없으면 backend/.env를 읽는다.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

function parseEnvFile(filePath) {
  const result = {};
  let content;
  try {
    content = fs.readFileSync(filePath, 'utf8');
  } catch {
    return result;
  }
  for (const line of content.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    result[key] = value;
  }
  return result;
}

function loadDevAccount() {
  let id = process.env.DEV_ACCOUNT_ID;
  let password = process.env.DEV_ACCOUNT_PASSWORD;
  if (!id || !password) {
    const envFile = parseEnvFile(path.join(__dirname, '../backend/.env'));
    id = id || envFile.DEV_ACCOUNT_ID;
    password = password || envFile.DEV_ACCOUNT_PASSWORD;
  }
  if (!id || !password) {
    console.error('dev-login: DEV_ACCOUNT_ID/DEV_ACCOUNT_PASSWORD를 process.env 또는 backend/.env에서 찾지 못했다.');
    process.exit(1);
  }
  return { id, password };
}

const { id: devAccountId, password: devAccountPassword } = loadDevAccount();
const wrongPassword = `${devAccountPassword}-wrong`;

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  try {
    await page.goto('http://localhost:3500/', { waitUntil: 'networkidle' });
    await page.getByLabel('개발 계정 아이디').fill(devAccountId);
    await page.getByLabel('개발 계정 비밀번호').fill(wrongPassword);
    await page.getByRole('button', { name: '개발 로그인' }).click();
    const alert = page.locator('form').getByRole('alert');
    await alert.waitFor();
    assert.match(await alert.textContent(), /틀렸다/);

    await page.getByLabel('개발 계정 비밀번호').fill(devAccountPassword);
    const sessionRes = page.waitForResponse(r => r.url().endsWith('/sessions') && r.request().method() === 'POST');
    await page.getByRole('button', { name: '개발 로그인' }).click();
    await page.waitForURL('**/play');
    assert.equal((await sessionRes).status(), 200, '로그인 쿠키로 판 생성이 200이어야 한다');
    const me = await page.evaluate(async base => (await fetch(`${base}/api/v1/auth/me`, { credentials: 'include' })).json(),
      'http://localhost:8500');
    assert.equal(me.sub, `dev:${devAccountId}`);
    console.log('dev-login: PASS');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });

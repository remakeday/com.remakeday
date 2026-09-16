// Run with Playwright available through NODE_PATH — the path below is one environment's example, not a fixed requirement.
// NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/dev-login.cjs
// 실서버(백엔드 8500 DEV_LOGIN=on, 프런트 3500 NEXT_PUBLIC_DEV_LOGIN=on) 대상.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  try {
    await page.goto('http://localhost:3500/', { waitUntil: 'networkidle' });
    await page.getByLabel('개발 계정 아이디').fill('001');
    await page.getByLabel('개발 계정 비밀번호').fill('wrong');
    await page.getByRole('button', { name: '개발 로그인' }).click();
    const alert = page.locator('form').getByRole('alert');
    await alert.waitFor();
    assert.match(await alert.textContent(), /틀렸다/);

    await page.getByLabel('개발 계정 비밀번호').fill('001001');
    const sessionRes = page.waitForResponse(r => r.url().endsWith('/sessions') && r.request().method() === 'POST');
    await page.getByRole('button', { name: '개발 로그인' }).click();
    await page.waitForURL('**/play');
    assert.equal((await sessionRes).status(), 200, '로그인 쿠키로 판 생성이 200이어야 한다');
    const me = await page.evaluate(async base => (await fetch(`${base}/api/v1/auth/me`, { credentials: 'include' })).json(),
      'http://localhost:8500');
    assert.equal(me.sub, 'dev:001');
    console.log('dev-login: PASS');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exit(1); });

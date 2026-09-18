// PC(1440px) 스크린샷 — 새 낮 화면(비주얼노벨 대사창)·HUD·기록 패널. 실서버(백엔드 8500 DEV_LOGIN, 프런트 3500) 대상.
// NODE_PATH=<playwright node_modules> node tests/day-screen-vn-shots.cjs → tests/.playwright-out/day-screen-vn/*.png
// --ui-tweaks: 진입 안내·이름 카드 2장만 찍는다.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

function parseEnvFile(filePath) {
  const result = {};
  let content;
  try { content = fs.readFileSync(filePath, 'utf8'); } catch { return result; }
  for (const line of content.split('\n')) {
    const t = line.trim(); if (!t || t.startsWith('#')) continue;
    const eq = t.indexOf('='); if (eq === -1) continue;
    let v = t.slice(eq + 1).trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    result[t.slice(0, eq).trim()] = v;
  }
  return result;
}
const envFile = parseEnvFile(path.join(__dirname, '../../backend/.env'));
const devId = process.env.DEV_ACCOUNT_ID || envFile.DEV_ACCOUNT_ID;
const devPw = process.env.DEV_ACCOUNT_PASSWORD || envFile.DEV_ACCOUNT_PASSWORD;
const OUT = path.join(__dirname, '.playwright-out/day-screen-vn');
const uiTweaksOnly = process.argv.includes('--ui-tweaks');
fs.mkdirSync(OUT, { recursive: true });
const shot = (page, name) => uiTweaksOnly && !['12-entry-guide', '13-cards-names-only', '99-error'].includes(name)
  ? Promise.resolve() : page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: false });

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(120000);
  const log = (m) => console.log(`[shots] ${m}`);
  try {
    await page.goto('http://localhost:3500/', { waitUntil: 'networkidle' });
    await page.getByRole('switch', { name: 'BGM 끄기', exact: true }).waitFor();
    assert.equal(await page.locator('audio[src="/audio/game-bgm.mp3"]').count(), 1);
    const login = await page.getByRole('link', { name: '로그인', exact: true }).elementHandle();
    await page.waitForFunction(link => Number(getComputedStyle(link).opacity) > 0, login);
    await page.getByLabel('개발 계정 아이디').fill(devId);
    await page.getByLabel('개발 계정 비밀번호').fill(devPw);
    await page.getByRole('button', { name: '개발 로그인' }).click();
    await page.waitForLoadState('networkidle');
    await page.goto('http://localhost:3500/play', { waitUntil: 'networkidle' });
    await page.getByRole('button', { name: '시작', exact: true }).waitFor();
    await page.getByRole('heading', { name: '플레이 안내', exact: true }).waitFor();
    await page.evaluate(() => document.fonts.ready);
    const startBounds = await page.getByRole('button', { name: '시작', exact: true }).boundingBox();
    assert.ok(startBounds.y + startBounds.height <= 900, 'guide and start button fit the PC screenshot');
    await shot(page, '12-entry-guide'); log('entry guide');
    await shot(page, '01-entry-hud'); log('entry');
    await page.getByRole('button', { name: '시작', exact: true }).click();
    const cont = page.getByText('탭하여 계속', { exact: true });
    await cont.waitFor();
    await shot(page, '01b-morning'); log('morning');
    await cont.click();
    const lineBox = page.getByRole('region', { name: '대사창' });
    await lineBox.waitFor();
    await page.waitForTimeout(800);
    await shot(page, '02-day-intro-first-line'); log('intro first line');
    const next = page.getByRole('button', { name: '다음', exact: true });
    for (let i = 0; i < 2; i++) { if (await next.isEnabled()) await next.click(); await page.waitForTimeout(300); }
    await shot(page, '03-day-intro-third-line'); log('intro 3rd line');
    await page.getByRole('button', { name: '모두 보기', exact: true }).click();
    await page.waitForTimeout(600);
    // 원숭이손 팝업이 뜨면 거절하고 진행
    const paw = page.getByRole('dialog', { name: '원숭이손의 제안' });
    if (await paw.count()) { await shot(page, '04-paw-popup'); log('paw popup'); await paw.getByRole('button').nth(1).click(); await page.waitForTimeout(500); }
    for (const name of ['채연', '민석', '은상', '준']) {
      const card = page.getByRole('button', { name: `${name} · 대화 가능`, exact: true });
      await card.waitFor();
      assert.equal(await card.locator('img').count(), 0, 'cards have no thumbnails');
    }
    const portrait = page.getByRole('img', { name: / 초상$/ });
    await portrait.waitFor();
    await portrait.evaluate(img => img.decode());
    await shot(page, '13-cards-names-only'); log('name-only cards');
    if (uiTweaksOnly) { log('done (2 shots)'); return; }
    await shot(page, '05-dialogue-mode'); log('dialogue mode');
    await page.getByRole('meter', { name: '남은 대화 횟수', exact: true }).waitFor();
    await page.getByTestId('day-title').getByText('장면 1/6', { exact: true }).waitFor();
    await shot(page, '14-gauge-under-title'); log('gauge under title');
    // 인물 선택 후 질문 (실제 NPC 모델 호출)
    const chae = page.getByRole('button', { name: /채연/ }).first();
    if (await chae.count()) await chae.click();
    await page.waitForTimeout(300);
    await page.getByLabel('인물에게 질문').fill('오늘 검진 기다릴 때 어땠어?');
    await page.getByRole('button', { name: '묻기', exact: true }).click();
    await page.getByRole('button', { name: '묻기', exact: true }).waitFor({ timeout: 180000 });
    await page.waitForTimeout(500);
    await shot(page, '06-after-question-reply-line'); log('reply line');
    if (await next.isEnabled()) { await next.click(); await page.waitForTimeout(300); await shot(page, '07-reply-next-line'); }
    await page.getByRole('button', { name: '이전', exact: true }).click();
    await page.getByRole('button', { name: '이전', exact: true }).click();
    await page.waitForTimeout(300);
    await shot(page, '08-back-through-today'); log('back');
    await page.getByRole('button', { name: '모두 보기', exact: true }).click();
    // HUD 기록과 안내 패널
    await page.getByRole('button', { name: '기록', exact: true }).click();
    await page.getByRole('dialog', { name: '기록', exact: true }).waitFor();
    await page.waitForTimeout(500);
    await shot(page, '09-record-panel'); log('record panel');
    await page.getByRole('button', { name: '기록 닫기', exact: true }).click();
    await page.getByRole('button', { name: '안내', exact: true }).click();
    await page.getByRole('dialog', { name: '안내', exact: true }).waitFor();
    await page.waitForTimeout(300);
    await shot(page, '10-guide-panel'); log('guide panel');
    await page.getByRole('button', { name: '안내 닫기', exact: true }).click();
    // 다음 장면 → 2번째 장면 도입
    await page.getByRole('button', { name: '다음 장면', exact: true }).click();
    await page.getByRole('button', { name: '다음 장면', exact: true }).waitFor({ timeout: 240000 });
    await page.waitForTimeout(600);
    await shot(page, '11-scene2-intro'); log('scene 2 intro');
    log('done');
  } catch (err) {
    await shot(page, '99-error').catch(() => {});
    console.error('[shots] FAIL', err && err.message ? err.message.split('\n')[0] : err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
})();

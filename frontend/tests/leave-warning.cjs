// 판 진행 중 beforeunload 이탈 경고. 진입·회고에서는 없다. 이어받기는 없다.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { line, readAll } = require('./vn-helpers.cjs');

const narration = '배급 줄 앞에 네 사람이 서 있다.';
const intro = [line('scene', narration), line('system', '주변을 살핀다.')];

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  try {
    const context = await browser.newContext({ viewport: { width: 390, height: 900 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on('pageerror', (error) => errors.push(error.message));

    const npcs = [['chaeyeon', '채연'], ['minseok', '민석'], ['eunsang', '은상'], ['jun', '준']]
      .map(([code, name]) => ({ code, name, mood: 'calm', uttered: false }));
    await page.route('**/*', async (route) => {
      const url = new URL(route.request().url());
      if (url.port !== '8500') return route.continue();
      const path = url.pathname;
      let body;
      if (path === '/sessions') body = { attempt_id: 'leave', attempt_n: 1, entry_lines: ['하루를 관찰한다.'], prior_cell_results: null };
      else if (path === '/sessions/leave/loops') body = {
        loop_id: 'leave-loop', loop_n: 1, morning_text: '아침이다.', damage_level: 0,
        budget_left: 6, beat: 1, beat_title: '아침 배급', narration, broadcast: null,
        lines: intro, illustrations: [], observations: [], active_rules: [], aftermath: null,
      };
      else if (path === '/loops/leave-loop/observations') body = { observations: [] };
      else if (path === '/loops/leave-loop/npcs') body = { npcs };
      else if (path === '/loops/leave-loop/night/previous') body = { previous_answer: null };
      else return route.abort();
      await route.fulfill({
        json: body,
        headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' },
      });
    });

    await page.goto('http://localhost:3500/play');
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });

    const listenersOnEntry = await page.evaluate(() => {
      // beforeunload는 getEventListeners가 없어, 직접 이벤트를 쏴 returnValue를 본다.
      const event = new Event('beforeunload', { cancelable: true });
      let set = false;
      Object.defineProperty(event, 'returnValue', {
        configurable: true,
        get() { return this._v; },
        set(v) { set = true; this._v = v; },
      });
      window.dispatchEvent(event);
      return set;
    });
    assert.equal(listenersOnEntry, false, 'entry has no leave warning');

    await page.getByRole('switch', { name: '음성 끄기', exact: true }).click();
    await page.getByRole('button', { name: '시작', exact: true }).click();
    await page.getByRole('button', { name: '계속', exact: true }).click();
    await page.getByRole('region', { name: '대사창', exact: true }).getByText(narration, { exact: true }).waitFor();
    await readAll(page);

    const listenersOnDay = await page.evaluate(() => {
      const event = new Event('beforeunload', { cancelable: true });
      let set = false;
      Object.defineProperty(event, 'returnValue', {
        configurable: true,
        get() { return this._v; },
        set(v) { set = true; this._v = v; },
      });
      window.dispatchEvent(event);
      return { set, value: event.returnValue };
    });
    assert.equal(listenersOnDay.set, true, 'day arms leave warning');
    assert.match(String(listenersOnDay.value), /사라집니다/);

    assert.deepEqual(errors, []);
    console.log('PASS leave-warning: entry silent, day beforeunload armed');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});

// NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/scene-illustrations.cjs
// Real frontend and assets; game API mocked to avoid creating player records.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const out = process.env.TEST_ARTIFACT_DIR || '/tmp/pigfarm-scene-illustrations';
fs.mkdirSync(out, { recursive: true });

const scenes = {
  1: [{ image_id: 'clue-01', caption: '음식이 남은 쟁반 하나.' }],
  2: [{ image_id: 'clue-05', caption: '빈 침상에 담요와 띠가 남아 있다.' }],
  4: [
    { image_id: 'clue-02', caption: '검진 안내 아래 웅크린 채연.' },
    { image_id: 'clue-03', caption: '검진 도구 옆의 채연.' },
  ],
  5: [{ image_id: 'clue-04', caption: '음식이 남은 쟁반 세 개.' }],
};
const files = {
  1: 'C01-breakfast-clue-v2.png', 2: 'clue-05-chungsik-empty-bunk-v1.png',
  4: 'clue-02-chaeyeon-checkup-reaction-v1.png', 5: 'clue-04-evening-trays-v1.png',
};

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const report = { checks: [], errors: [] };
  try {
    for (const [width, outcome, mode] of [[1440, 'closure', 'new'], [390, 'truck', 'new'], [1440, 'quiet', 'legacy'], [1440, 'truck', 'unknown']]) {
      const page = await browser.newPage({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      page.on('pageerror', e => report.errors.push(e.message));
      let beat = 1, nextCalls = 0;
      const data = () => ({ beat, beat_title: `시간 ${beat}`, narration: '주변을 살핀다.',
        broadcast: beat === 4 ? '검진을 시작합니다.' : null,
        ...(mode === 'new' ? { illustrations: scenes[beat] || [] } :
          mode === 'unknown' ? { illustrations: [{ image_id: 'unknown-image', caption: '등록되지 않은 그림 설명' }] } : {}) });
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.port !== '8500') return route.continue();
        let body;
        const path = url.pathname;
        if (path === '/sessions') body = { attempt_id: 'images', attempt_n: 1, entry_lines: ['하루', '관찰', '추리'], prior_cell_results: null };
        else if (path.endsWith('/loops')) body = { loop_id: 'day', loop_n: 1, morning_text: '아침이다.', damage_level: 0, budget_left: 8, aftermath: null, active_rules: [], observations: [], ...data() };
        else if (path.endsWith('/npcs')) body = { npcs: [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }] };
        else if (path.endsWith('/beats/next')) {
          nextCalls++;
          const done = beat === 6;
          if (!done) beat++;
          body = { ...data(), ...(done ? { illustrations: [] } : {}), day_done: done, paw_offer: null, ambient: null, note_found: null, observations: [], budget_left: 8 };
        } else if (path.endsWith('/observations')) body = { observations: [] };
        else if (path.endsWith('/night/previous')) body = { previous_answer: null };
        else if (path.endsWith('/notes')) body = { notes: [] };
        else if (path.endsWith('/night/draft')) body = { night_id: 'night', claims: ['관찰한 내용을 정리했다.'] };
        else if (path.endsWith('/submit')) body = { total: 0, passed: false, loop_n: 1, world_outcome: outcome, is_final: false, closed_by: null, cells: null, cookie: null, intervention_available: true, ending_lines: null, cell_feedback: '원인은 비어 있다.', wrong_claim_count: 0 };
        else { report.errors.push(`Unexpected API: ${path}`); return route.abort(); }
        return route.fulfill({ json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
      });
      await page.goto('http://localhost:3500/play');
      await page.getByRole('button', { name: '시작', exact: true }).click();
      await page.getByRole('button', { name: '계속', exact: true }).click();
      async function imageLoaded(src) {
        const img = page.locator(`img[src="${src}"]`);
        await img.waitFor({ state: 'visible', timeout: 5000 });
        await page.waitForFunction(src => {
          const img = document.querySelector(`img[src="${src}"]`);
          return img && img.complete && img.naturalWidth > 0;
        }, src);
        assert.equal(await img.evaluate(el => getComputedStyle(el).objectFit), 'contain');
        const bounds = await img.boundingBox();
        assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= width,
          'scene image stays inside the viewport after controls receive focus');
      }
      for (let b = 1; b <= 6; b++) {
        if (b === 4) {
          await page.getByText('검진을 시작합니다.', { exact: true }).waitFor();
          await page.getByRole('button', { name: '…', exact: true }).click();
        }
        const expected = mode === 'new' && files[b] ? `/assets/clues/${files[b]}` : `/assets/C0${b}.png`;
        await imageLoaded(expected);
        if (mode === 'unknown') assert.equal(await page.getByText('등록되지 않은 그림 설명').count(), 0);
        if (mode === 'new' && b === 4) {
          const before = nextCalls;
          await page.getByRole('button', { name: '다음 그림', exact: true }).click();
          await imageLoaded('/assets/clues/clue-03-after-checkup-v1.png');
          await page.getByRole('button', { name: '이전 그림', exact: true }).click();
          await imageLoaded(expected);
          await page.getByRole('button', { name: '다음 그림', exact: true }).click();
          await imageLoaded('/assets/clues/clue-03-after-checkup-v1.png');
          assert.equal(nextCalls, before, 'browsing illustrations does not advance the game');
          await page.screenshot({ path: `${out}/checkup-${width}.png`, animations: 'disabled' });
        }
        assert.equal(await page.locator('img[src*="clue-06"]').count(), 0, 'closure not revealed during day');
        await page.getByRole('button', { name: '다음 장면', exact: true }).click();
      }
      await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
      await page.getByPlaceholder('자유롭게 쓴다…').fill('관찰한 내용을 정리했다.');
      await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
      await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
      await page.getByRole('button', { name: '계속', exact: true }).click();
      if (outcome === 'closure') {
        await imageLoaded('/assets/clues/clue-06-zone-closure-broadcast-v1.png');
        await page.screenshot({ path: `${out}/closure.png` });
      } else {
        await page.locator(`img[src="/assets/${outcome === 'truck' ? 'H01' : 'H02'}.png"]`).waitFor();
        assert.equal(await page.locator('img[src*="clue-06"]').count(), 0);
      }
      report.checks.push(`${width}px ${mode}: day sequence, scene navigation/reset, assets loaded, ${outcome} branch`);
      await page.close();
    }
    assert.deepEqual(report.errors, []);
  } finally {
    fs.writeFileSync(`${out}/results.json`, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });

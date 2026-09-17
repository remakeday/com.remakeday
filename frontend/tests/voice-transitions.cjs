// NODE_PATH=/tmp/demo-image-browser/node_modules node frontend/tests/voice-transitions.cjs
// One headless browser; mocked game API, real audio except explicit failure injection.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  const errors = [], checks = [];
  try {
    // clue-failed: 밤 방송 MA08 파일 실패 → 결말별 대체(폐쇄 MA05) 뒤 MA06 (밤단서 v2 P.1)
    for (const mode of ['normal', 'muted', 'mute-during', 'failed', 'blocked', 'blocked-replay', 'skip', 'replay', 'clue-failed', 'standalone']) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
      try {
        const page = await context.newPage();
        page.setDefaultTimeout(10000);
        page.on('pageerror', error => errors.push(error.message));
        await page.addInitScript(mode => {
          window.voiceStarts = [];
          window.voiceEnds = [];
          window.voiceBlocked = 0;
          const play = HTMLMediaElement.prototype.play;
          HTMLMediaElement.prototype.play = function () {
            if (mode.startsWith('blocked') && this.getAttribute('src')?.endsWith('/MA06.mp3') && !window.voiceBlocked) {
              window.voiceBlocked++;
              return Promise.reject(new DOMException('Injected autoplay rejection', 'NotAllowedError'));
            }
            return play.call(this);
          };
          for (const [event, target] of [['playing', 'voiceStarts'], ['ended', 'voiceEnds']]) {
            document.addEventListener(event, e => {
              if (e.target instanceof HTMLAudioElement && e.target.dataset.audio === 'voice') window[target].push(e.target.currentSrc.split('/').pop());
            }, true);
          }
        }, mode);
        await page.route('**/*', async route => {
          const url = new URL(route.request().url()), path = url.pathname;
          if (mode === 'failed' && path.endsWith('/MA06.mp3')) return route.abort('failed');
          if (mode === 'clue-failed' && path.endsWith('/MA08.mp3')) return route.abort('failed');
          if (url.port !== '8500') return route.continue();
          let body;
          if (path === '/sessions') body = { attempt_id: 'voice', attempt_n: 1, entry_lines: ['아침이다.'], prior_cell_results: null };
          else if (path.endsWith('/loops')) body = { loop_id: 'loop', loop_n: 1, morning_text: '아침이다.', damage_level: 0, budget_left: 8, beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null, aftermath: null, active_rules: [], observations: [] };
          else if (path.endsWith('/npcs')) body = { npcs: [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }] };
          else if (path.endsWith('/beats/next')) body = { beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null, day_done: true, paw_offer: null, note_found: null, ambient: null, observations: [], budget_left: 8 };
          else if (path.endsWith('/observations')) body = { observations: [] };
          else if (path.endsWith('/night/previous')) body = { previous_answer: null };
          else if (path.endsWith('/notes')) body = { notes: [] };
          else if (path.endsWith('/night/draft')) body = { night_id: 'night', claims: ['상황을 이해했다.'] };
          else if (path.endsWith('/submit')) body = { total: 0, passed: false, loop_n: 1, world_outcome: 'closure', is_final: false, closed_by: null, cells: null, cookie: null, intervention_available: true, ending_lines: null, cell_feedback: null, wrong_claim_count: 0, accepted_claims: [], empty_cells: ['cause', 'motive'],
            night_clue: { loop_n: 1, caption: '소독약 냄새. 발 아래 콘크리트가 차다.', image_ids: ['P01'], voice_id: 'MA08', broadcast: '소독을 실시합니다. 바닥에서 떨어져 자리에 오르십시오.', outcome_line: null } };
          else if (path.endsWith('/journey')) body = { loops: [], final: null, unresolved: [] };
          else if (path.endsWith('/harness')) body = { rules: [], harness_summary: { total_events: 0, harness_interventions: 0, fallbacks: 0, paw_accepted: 0, recommended_rules: 0, custom_rules: 0, rule_conflicts: 0, questions_asked: 0, tool_side_effects: [] } };
          else throw new Error(`Unexpected API: ${path}`);
          return route.fulfill({ json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
        });
        const voice = page.locator('audio[data-audio="voice"]');
        const playing = async (id, time = 0) => page.waitForFunction(({ id, time }) => {
          const audio = document.querySelector('audio[data-audio="voice"]');
          return audio && audio.currentSrc.endsWith(`/${id}.mp3`) && !audio.paused && audio.currentTime > time;
        }, { id, time });
        if (mode === 'standalone') {
          await page.goto('http://localhost:3500/harness/voice');
          await playing('EN01');
          await page.getByRole('button', { name: '회고 대사 다시 듣기', exact: true }).first().click();
          await playing('EN01');
          await page.locator('summary').click();
          await playing('EN02');
          await page.getByRole('button', { name: '회고 대사 다시 듣기', exact: true }).last().click();
          await playing('EN03');
          assert.equal(await page.locator('audio[src="/audio/game-bgm.mp3"]').count(), 0);
        } else {
          await page.goto('http://localhost:3500/play');
          if (mode === 'muted') await page.getByRole('switch', { name: '음성 끄기', exact: true }).click();
          for (const name of ['시작', '계속', '다음 장면', '밤이 온다']) await page.getByRole('button', { name, exact: true }).click();
          await page.getByPlaceholder('자유롭게 쓴다…').fill('상황을 이해했다.');
          for (const name of ['이렇게 이해했다', '맞아, 제출한다', '계속']) await page.getByRole('button', { name, exact: true }).click();
          const guide = page.getByRole('button', { name: '규칙을 고른다', exact: true });
          const proceed = page.getByRole('button', { name: '계속', exact: true });
          const caption = page.getByText('소독약 냄새. 발 아래 콘크리트가 차다.', { exact: true });
          let oldAudio;
          if (mode === 'normal') {
            // 밤 방송이 먼저, 그 중반에 띠가 튀고(동작 허용 → cookieJitter), 문장이 뜬 뒤 폐쇄 방송 MA06이 이어진다
            await playing('MA08');
            const band = page.locator('img[data-night-band]');
            await band.first().waitFor();
            assert.equal(await band.first().getAttribute('src'), '/assets/P01.png');
            assert.equal(await band.first().evaluate(el => getComputedStyle(el).animationName), 'cookieJitter', 'bands jitter when motion is allowed');
            await caption.waitFor();
          }
          if (mode === 'clue-failed') {
            await playing('MA05');
            assert.equal(await page.evaluate(() => window.voiceStarts.includes('MA08.mp3')), false, 'failed night broadcast never starts');
          }
          if (mode.startsWith('blocked')) {
            await page.waitForFunction(() => window.voiceBlocked === 1 && !document.querySelector('audio[data-audio="voice"]').getAttribute('src'));
            await page.getByText('이 구역을 폐쇄합니다. 문에서 떨어져 대기하십시오.', { exact: true }).click();
          }
          if (!['muted', 'failed', 'blocked', 'blocked-replay'].includes(mode)) {
            await playing('MA06');
            oldAudio = await voice.elementHandle();
          }
          if (mode === 'skip') await proceed.click();
          if (mode === 'mute-during') await page.getByRole('switch', { name: '음성 끄기', exact: true }).click();
          if (mode === 'replay' || mode === 'blocked-replay') {
            if (mode === 'replay') await playing('MA06', 1.7);
            await page.getByRole('button', { name: '관리자 대사 다시 듣기', exact: true }).click();
            await playing('MA06', 2);
            assert.equal(await guide.count(), 0, 'replayed closure stays visible until the new recording finishes');
          }
          // 자동 진행 없음 — 문장은 탭까지 남는다. 폐쇄 방송은 끝까지 듣고 나서 탭한다.
          if (['normal', 'replay', 'blocked-replay', 'clue-failed'].includes(mode)) await page.waitForFunction(() => window.voiceEnds.includes('MA06.mp3'), null, { timeout: 15000 });
          if (mode !== 'skip') {
            await proceed.waitFor();
            assert.equal(await page.locator('img[data-night-band]').count(), 0, `${mode}: bands are off before the tap`);
            await caption.waitFor();
            await proceed.click();
          }
          await guide.waitFor();
          const starts = await page.evaluate(() => window.voiceStarts.filter(id => id === 'MA06.mp3').length);
          if (['normal', 'replay', 'blocked-replay', 'clue-failed'].includes(mode)) assert.ok(await page.evaluate(() => window.voiceEnds.includes('MA06.mp3')), `${mode}: full closure recording finishes`);
          if (mode === 'normal') assert.ok(await page.evaluate(() => window.voiceStarts.indexOf('MA08.mp3') < window.voiceStarts.indexOf('MA06.mp3')), 'night broadcast precedes the closure broadcast');
          if (mode === 'clue-failed') assert.ok(await page.evaluate(() => window.voiceStarts.indexOf('MA05.mp3') < window.voiceStarts.indexOf('MA06.mp3')), 'fallback MA05 precedes MA06');
          if (['muted', 'failed', 'blocked'].includes(mode)) assert.equal(starts, 0, `${mode}: fallback advances without starting a late recording`);
          if (mode === 'replay') assert.equal(starts, 2);
          if (mode === 'skip' || mode === 'mute-during') assert.equal(await oldAudio.evaluate(audio => audio.paused), true);
        }
        checks.push(mode);
        console.log(`PASS voice transition: ${mode}`);
      } finally { await context.close(); }
    }
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ checks, errors }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

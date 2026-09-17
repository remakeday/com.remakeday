// Real media playback + API fixtures; one headless browser, no game DB writes.
// NODE_PATH=/tmp/demo-image-browser/node_modules node frontend/tests/voice-playback.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { readdirSync } = require('node:fs');
const path = require('node:path');

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.setDefaultTimeout(10000);
    page.on('pageerror', error => errors.push(error.message));
    await page.addInitScript(() => {
      window.bgmVolumes = [];
      document.addEventListener('volumechange', event => {
        if (event.target instanceof HTMLAudioElement && event.target.getAttribute('src') === '/audio/game-bgm.mp3') {
          window.bgmVolumes.push(event.target.volume);
        }
      }, true);
    });
    let beat = 1;
    let budget = 8;
    let failLightsOut = true;
    const npcs = [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }];
    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (failLightsOut && url.pathname.endsWith('/MA07.mp3')) return route.abort('failed');
      if (url.port !== '8500') return route.continue();
      const path = url.pathname;
      let body;
      if (path === '/sessions') body = { attempt_id: 'voice', attempt_n: 1, entry_lines: ['아침이다.'], prior_cell_results: null };
      else if (path.endsWith('/loops')) body = {
        loop_id: 'voice-loop', loop_n: 1, morning_text: '아침이다.', damage_level: 0,
        budget_left: budget, beat, beat_title: '기상', narration: '채연이 배급을 남긴다.',
        broadcast: '배급을 시작합니다. 식사 후에는 각자 자리에서 대기해 주십시오.',
        aftermath: null, active_rules: [], observations: [], illustrations: [],
        ambient: { lines: [
          { code: 'jun', name: '준', text: '이거 네 거잖아. 안 먹어?' },
          { code: 'chaeyeon', name: '채연', text: '배 안 고파. 너 먹어.' },
        ] },
      };
      else if (path.endsWith('/npcs')) body = { npcs };
      else if (path.endsWith('/utterances')) body = {
        utterance_id: route.request().postDataJSON().request_id, npc: { ...npcs[0], uttered: true },
        reply: '아프지는 않아. 오늘은 네가 먹어.', budget_left: --budget, beat, tool_used: false, observations: [],
      };
      else if (path.endsWith('/beats/next')) {
        beat++;
        body = { beat, beat_title: '다음 장면', narration: '시간이 흐른다.',
          broadcast: beat === 4 ? '소등하겠습니다. 모두 자리에서 움직이지 않습니다.' : null,
          ambient: { lines: beat === 4
            ? [{ code: 'eunsang', name: '은상', text: '혼자 깨어 있으면 무서워. 조금만 같이 있어 줘.' }]
            : [{ code: 'jun', name: '준', text: '민석아, 이 숫자 뭔지 알아?' }] },
          day_done: false, observations: [], illustrations: [], budget_left: budget, paw_offer: null, note_found: null };
      } else throw new Error(`Unexpected API: ${path}`);
      return route.fulfill({ json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
    });

    await page.goto('http://localhost:3500/play');
    await page.getByRole('button', { name: '시작', exact: true }).click();
    await page.getByRole('button', { name: '계속', exact: true }).click();
    const voice = page.locator('audio[data-audio="voice"]');
    const bgm = page.locator('audio[src="/audio/game-bgm.mp3"]');
    const playing = async id => page.waitForFunction(id => {
      const audio = document.querySelector('audio[data-audio="voice"]');
      return audio && audio.currentSrc.endsWith(`/${id}.mp3`) && !audio.paused && audio.currentTime > 0;
    }, id);

    // A missing or overlapping voice queue fails these checks.
    await playing('MA01');
    await page.waitForFunction(() => document.querySelector('audio[src="/audio/game-bgm.mp3"]').volume < 0.15);
    await page.getByRole('button', { name: '…', exact: true }).click();
    // 인물 대사 음원은 재생 보류(테스터6 F1) — 자막만 보이고 다시 듣기 버튼도 없다.
    await page.getByText('배 안 고파. 너 먹어.', { exact: true }).waitFor();
    await page.waitForFunction(() => { const audio = document.querySelector('audio[data-audio="voice"]'); return audio.paused && !audio.getAttribute('src'); });
    assert.equal(await page.getByRole('button', { name: /(채연|민석|은상|준) 대사 다시 듣기/ }).count(), 0, 'character lines have no replay button');
    await page.waitForFunction(() => document.querySelector('audio[src="/audio/game-bgm.mp3"]').volume === 0.25);

    await page.getByRole('button', { name: '관리자 대사 다시 듣기', exact: true }).first().click();
    await playing('MA01');
    const canceledVoice = await voice.elementHandle();
    await page.getByRole('button', { name: '다음 장면', exact: true }).click();
    await page.getByText('민석아, 이 숫자 뭔지 알아?', { exact: true }).waitFor();
    await canceledVoice.evaluate(audio => {
      audio.dispatchEvent(new Event('ended'));
      audio.dispatchEvent(new Event('error'));
    });
    await page.waitForFunction(() => { const audio = document.querySelector('audio[data-audio="voice"]'); return audio.paused && !audio.getAttribute('src'); });
    assert.equal(await page.getByRole('button', { name: '준 대사 다시 듣기', exact: true }).count(), 0, 'new scene cancels the old recording and stays text only');

    await page.getByRole('switch', { name: '음성 끄기', exact: true }).click();
    await canceledVoice.evaluate(audio => audio.dispatchEvent(new Event('play')));
    assert.equal(await voice.evaluate(audio => audio.paused), true);
    await page.waitForFunction(() => document.querySelector('audio[src="/audio/game-bgm.mp3"]').volume === 0.25);
    await page.getByRole('button', { name: '다음 장면', exact: true }).click();
    assert.equal(await voice.evaluate(audio => audio.paused), true, 'new scene preserves voice-off choice');
    await page.getByRole('switch', { name: '음성 켜기', exact: true }).click();

    // A similar LLM response must never trigger an unrelated fixed recording.
    await page.getByRole('textbox', { name: '인물에게 질문', exact: true }).fill('왜 안 먹어?');
    await page.getByRole('button', { name: '말한다', exact: true }).click();
    await page.getByText('아프지는 않아. 오늘은 네가 먹어.', { exact: true }).waitFor();
    assert.equal(await voice.evaluate(audio => audio.paused), true, 'unrecorded dialogue remains text only');

    // A missing recording must not block the next line or keep BGM ducked.
    await page.getByRole('button', { name: '다음 장면', exact: true }).click();
    await page.getByText('소등하겠습니다. 모두 자리에서 움직이지 않습니다.', { exact: true }).waitFor();
    await page.waitForFunction(() => {
      const audio = document.querySelector('audio[data-audio="voice"]');
      return !audio.getAttribute('src') && audio.paused;
    });
    await page.waitForFunction(() => document.querySelector('audio[src="/audio/game-bgm.mp3"]').volume === 0.25);
    await page.getByRole('button', { name: '…', exact: true }).click();
    await page.getByText('혼자 깨어 있으면 무서워. 조금만 같이 있어 줘.', { exact: true }).waitFor();
    assert.equal(await voice.evaluate(audio => audio.paused), true, 'held character recording stays text only');
    await page.getByRole('switch', { name: 'BGM 끄기', exact: true }).click();
    assert.equal(await bgm.evaluate(audio => audio.paused), true, 'music-off choice holds');
    failLightsOut = false;
    const files = readdirSync(path.resolve(__dirname, '../../output/voice')).filter(name => /^[A-Z]{2}\d{2}\.mp3$/.test(name));
    const durations = await page.evaluate(async files => {
      const result = {};
      for (const file of files) {
        const audio = new Audio();
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error(`Metadata timed out: ${file}`)), 10000);
          audio.onloadedmetadata = () => { clearTimeout(timeout); resolve(); };
          audio.onerror = () => { clearTimeout(timeout); reject(new Error(`Cannot decode: ${file}`)); };
          audio.preload = 'metadata';
          audio.src = `/audio/voice/${file}`;
        });
        result[file] = audio.duration;
        audio.removeAttribute('src');
        audio.load();
      }
      return result;
    }, files);
    assert.equal(Object.keys(durations).length, 35);
    assert.ok(Object.values(durations).every(value => Number.isFinite(value) && value > 0), 'all supplied voice recordings decode');
    assert.ok(await page.evaluate(() => window.bgmVolumes.length > 0 && window.bgmVolumes.every(volume => volume <= 0.25)), 'BGM never exceeds its configured volume, including initialization');
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ checks: ['broadcast before dialogue', 'character lines text only (F1)', 'BGM duck and restore', 'manager line replay', 'scene cancellation', 'voice-off persists', 'exact dialogue matching', 'missing audio recovery', 'music-off persists', 'all 35 recordings decode'], durations, errors }, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

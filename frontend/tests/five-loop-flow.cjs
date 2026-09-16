// Run with Playwright available through NODE_PATH. All game API requests are mocked.
// NODE_PATH=/tmp/pigfarm-review-Hewzkn/node_modules node tests/five-loop-flow.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const out = process.env.TEST_ARTIFACT_DIR || '/tmp/pigfarm-five-loop-browser';
fs.mkdirSync(out, { recursive: true });

// 밤 단서 시퀀스 (밤단서 v2 P.1) — 서버 payload 그대로. 3회차는 폐쇄, 나머지는 트럭 결말.
const NIGHT_CLUES = {
  1: { caption: '소독약 냄새. 발 아래 콘크리트가 차다.', image_ids: ['P01'], voice_id: 'MA08', broadcast: '소독을 실시합니다. 바닥에서 떨어져 자리에 오르십시오.', outcome_line: '트럭 소리.' },
  2: { caption: '트럭 소리.', image_ids: ['P02', 'clue-05'], voice_id: 'MA09', broadcast: '정리 작업이 있겠습니다. 비어 있는 자리는 아침에 정돈됩니다.', outcome_line: null },
  3: { caption: '거울이 없다.', image_ids: ['P03'], voice_id: 'MA10', broadcast: '외관 확인은 담당자가 합니다. 각자 확인할 필요 없습니다.', outcome_line: null },
  4: { caption: '배급 포대에 글자가 있다.', image_ids: ['P04'], voice_id: 'MA11', broadcast: '배급 물자가 도착했습니다. 포대의 표기는 관리 용도입니다. 읽을 필요 없습니다.', outcome_line: '트럭 옆면 "○○축산".' },
  5: { caption: '손이 없어서 문을 못 연다는 것을 문득 안다.', image_ids: ['P05'], voice_id: 'MA12', broadcast: '출입문은 관리자가 개방합니다. 문에 손대지 마십시오.', outcome_line: null },
};
const NIGHT_IMAGES = { P01: '/assets/P01.png', P02: '/assets/P02.png', P03: '/assets/P03.png', P04: '/assets/P04.png', P05: '/assets/P05.png', 'clue-05': '/assets/clues/clue-05-chungsik-empty-bunk-v1.png' };

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--autoplay-policy=no-user-gesture-required'] });
  const report = { mode: 'mock API, real frontend; no game DB writes', checks: [], errors: [] };
  try {
    for (const finalScore of [0, 100]) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
      await page.addInitScript(() => {
        window.voiceStarts = [];
        window.voiceEnds = [];
        for (const [event, target] of [['play', 'voiceStarts'], ['ended', 'voiceEnds']]) {
          document.addEventListener(event, e => {
            if (e.target instanceof HTMLAudioElement && e.target.dataset.audio === 'voice') {
              window[target].push(e.target.currentSrc.split('/').pop());
            }
          }, true);
        }
      });
      page.on('pageerror', e => report.errors.push(e.message));
      let loopN = 0, submitted = false, retry = false, harnessCalls = 0, failHarness = true;
      const cells = { cause: finalScore, motive: finalScore, identity: finalScore, side_effect: 0 };
      await page.route('**/*', async route => {
        const u = new URL(route.request().url());
        if (u.port !== '8500') return route.continue();
        const path = u.pathname;
        let body, status = 200;
        if (path === '/sessions') {
          retry = loopN === 5;
          body = { attempt_id: 'test', attempt_n: retry ? 2 : 1, entry_lines: ['세계가 이상하다.', '오늘이 지나면, 세계는 멸망한다.', '다섯 번의 하루 안에, 왜 멸망했는지 알아내야 한다.'], prior_cell_results: retry ? cells : null };
        } else if (path === '/sessions/test/loops') {
          loopN++;
          body = { loop_id: `loop-${loopN}`, loop_n: loopN, morning_text: '7시 12분. 눈을 뜬다.', damage_level: Math.min(3, loopN - 1), budget_left: 9 - loopN, beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null, aftermath: null, active_rules: [], observations: [] };
        } else if (path.endsWith('/npcs')) body = { npcs: [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }] };
        else if (path.endsWith('/beats/next')) body = { beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null, day_done: true, paw_offer: null, note_found: null, ambient: null, observations: [], budget_left: 9 - loopN };
        else if (path.endsWith('/observations')) body = { observations: [] };
        else if (path.endsWith('/night/previous')) body = { previous_answer: null };
        else if (path.endsWith('/notes')) body = { notes: [] };
        else if (path.endsWith('/night/draft')) body = { night_id: `night-${loopN}`, claims: ['상황과 정체에 대한 이해'] };
        else if (path.endsWith('/submit')) {
          const total = loopN < 5 ? 100 : finalScore;
          submitted = true;
          body = { total, passed: total >= 50, loop_n: loopN, world_outcome: loopN === 3 ? 'closure' : 'truck', is_final: loopN === 5, closed_by: loopN === 5 ? (total === 100 ? 'understood_all' : 'doom') : null, cells: loopN === 5 ? cells : null, cookie: null, intervention_available: loopN < 5, ending_lines: loopN === 5 ? ['우리가 대피소라고 믿었던 곳은 양돈장이었다.'] : null, cell_feedback: '원인은 잡혔다.', wrong_claim_count: 0, night_clue: { loop_n: loopN, ...NIGHT_CLUES[loopN] } };
        } else if (path.endsWith('/options')) body = { options: [1, 2, 3].map(index => ({ index, label: `추천 규칙 ${index}`, target: '채연', action: '배급을 설명한다', effect: 'enforce', when_beat: 'any', reason: '관찰을 확인하기 위해', evidence_ids: [], expected_observation: '다음 배급 장면에서 설명을 듣는다.' })) };
        else if (path.endsWith('/rule')) body = { ok: true, rule_label: '추천 규칙 1', conflicts: [], reason: null };
        else if (path.endsWith('/journey')) {
          harnessCalls++;
          if (loopN < 5 || !submitted) { status = 403; body = { detail: '다섯 번째 밤을 마치면 열린다' }; }
          else if (failHarness) { status = 503; body = { detail: '일시적인 오류' }; }
          else body = {
            loops: [1, 2, 3, 4, 5].map(n => ({ loop_n: n, total: n < 5 ? 100 : finalScore, passed: true, new_confirmed: n === 2 && finalScore === 100 ? [{ code: 'cause-1', my_claim: '채연이 처음 아팠다.' }] : [], unlocked_notes: n === 1 ? ['트럭은 실어 갈 뿐이다.'] : [] })),
            final: { cells, closed_by: finalScore === 100 ? 'understood_all' : 'doom', truth_reveal: [{ code: 'identity-1', cell: 'identity', verdict: finalScore === 100 ? 'confirmed' : 'none', my_claim: finalScore === 100 ? '우리는 돼지였다.' : null, truth: finalScore === 100 ? '이들은 동물이다' : null }] },
            unresolved: finalScore === 100 ? [] : [{ cell: 'identity', hint: '내일 준에게 트럭 소리를 물어봐.' }],
          };
        }
        else if (path.endsWith('/harness')) {
          if (loopN < 5 || !submitted) { status = 403; body = { detail: '다섯 번째 밤을 마치면 열린다' }; }
          else body = { rules: [{ rule_id: 'R1', source: 'monkey_paw', target: '채연', when_beat: null, effect: 'suppress', action: '배급을 남긴다', shown_reason: null, hidden_side_effect: '다른 인물의 의심이 커진다.', created_loop: 1, conflict: false }], harness_summary: { total_events: 20, harness_interventions: 2, fallbacks: 1, paw_accepted: 1, recommended_rules: 4, custom_rules: 0, rule_conflicts: 0, questions_asked: 0, rule_success_rate: null, tool_side_effects: [{ loop_n: 2, beat: 3, text: '의심 증가' }] } };
        } else { report.errors.push(`Unmocked API: ${path}`); return route.abort(); }
        await route.fulfill({ status, json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
      });
      await page.goto('http://localhost:3500/harness/test');
      await page.getByText('다섯 번째 밤을 마치면 열린다', { exact: true }).waitFor();
      report.checks.push('unfinished retrospective locked');
      await page.goto('http://localhost:3500/play');
      const bgm = page.locator('audio[src="/audio/game-bgm.mp3"]');
      assert.equal(await bgm.count(), 1, 'one persistent BGM player belongs to the game');
      await page.waitForFunction(() => {
        const audio = document.querySelector('audio[src="/audio/game-bgm.mp3"]');
        return audio && !audio.paused && audio.currentTime > 0.2;
      });
      assert.equal(loopN, 0, 'BGM starts on entry before starting a game loop');
      const lockedHarnessCalls = harnessCalls; // 개발 모드의 StrictMode는 mount effect를 재실행한다.
      await page.getByRole('button', { name: '시작', exact: true }).click();
      const bgmHandle = await bgm.elementHandle();
      assert.equal(await bgm.evaluate(audio => audio.loop), true);
      assert.ok(await bgm.evaluate(audio => audio.volume > 0 && audio.volume <= 0.5), 'BGM starts at a low volume');
      await bgm.evaluate(audio => { audio.currentTime = audio.duration - 0.2; });
      await page.waitForFunction(() => document.querySelector('audio[src="/audio/game-bgm.mp3"]').currentTime < 5);
      await bgm.evaluate(audio => { audio.currentTime = 15; });
      for (let n = 1; n <= 5; n++) {
        await page.getByText(`오늘 남은 대화 ${9 - n}회`, { exact: true }).waitFor();
        assert.equal(await bgmHandle.evaluate(audio => audio === document.querySelector('audio[src="/audio/game-bgm.mp3"]')), true, 'loop changes preserve the audio element');
        assert.ok(await bgm.evaluate(audio => audio.currentTime >= 15), 'loop changes preserve the playback position');
        if (n === 2) {
          assert.equal(await bgm.evaluate(audio => audio.paused), true, 'next loop preserves the music-off choice');
          await page.getByRole('switch', { name: 'BGM 켜기', exact: true }).click();
          await page.getByRole('switch', { name: 'BGM 끄기', exact: true }).waitFor();
        }
        await page.getByRole('button', { name: '계속', exact: true }).click();
        assert.equal(await bgmHandle.evaluate(audio => audio === document.querySelector('audio[src="/audio/game-bgm.mp3"]')), true, 'scene changes preserve the audio element');
        assert.equal(await bgm.evaluate(audio => audio.paused), false, 'music continues in daytime');
        assert.ok(await bgm.evaluate(audio => audio.currentTime >= 15), 'scene changes preserve the playback position');
        assert.equal(await page.getByRole('heading', { name: '플레이 안내' }).count(), 0, 'tutorial does not block repeat days');
        await page.getByText(`오늘 남은 대화 ${9 - n}회`, { exact: true }).waitFor();
        await page.getByRole('button', { name: '다음 장면', exact: true }).click();
        await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
        await page.getByPlaceholder('자유롭게 쓴다…').fill('상황과 정체에 대한 이해');
        await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
        await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
        await page.getByText(`${n}/5번째 밤 · 상황 이해도`, { exact: true }).waitFor();
        await page.getByRole('button', { name: '계속', exact: true }).click();
        // 밤 단서 시퀀스 — 띠·문장·음성 ID가 표대로 나오고, 띠가 꺼져도 문장은 탭까지 남는다 (밤단서 v2 P.1·P.2)
        const clue = NIGHT_CLUES[n];
        const band = page.locator('img[data-night-band]');
        await band.first().waitFor();
        assert.equal(await band.first().getAttribute('src'), NIGHT_IMAGES[clue.image_ids[0]], `night ${n}: first band shows the clue image`);
        assert.ok((await band.count()) >= 2, `night ${n}: bands come in twos or threes`);
        assert.equal(await band.first().evaluate(el => getComputedStyle(el).animationName), 'none', `night ${n}: reduced motion shows the bands still`);
        const caption = page.locator('[data-night-caption]');
        assert.equal(await caption.getAttribute('aria-live'), 'polite');
        await caption.getByText(clue.caption, { exact: true }).waitFor();
        if (clue.outcome_line) await caption.getByText(clue.outcome_line, { exact: true }).waitFor(); // 결말 자막 "트럭 소리."와 별개로 캡션 뒤에 붙는다
        if (n === 2) await page.locator(`img[data-night-band][src="${NIGHT_IMAGES['clue-05']}"]`).first().waitFor(); // 두 번째 그림 — 띠가 한 번 더 튄다
        await page.waitForFunction(id => window.voiceStarts.includes(id), `${clue.voice_id}.mp3`);
        const proceed = page.getByRole('button', { name: '계속', exact: true });
        await proceed.waitFor();
        assert.equal(await band.count(), 0, `night ${n}: bands are off before the tap`);
        await caption.getByText(clue.caption, { exact: true }).waitFor();
        if (n === 3) await page.waitForFunction(() => window.voiceEnds.includes('MA06.mp3'));
        await proceed.click();
        report.checks.push(`night ${n}: ${clue.voice_id}, ${clue.image_ids.length} band image(s), caption stays`);
        if (n < 5) {
          await page.getByRole('button', { name: '규칙을 고른다', exact: true }).waitFor();
          if (n === 1) await page.waitForFunction(() => window.voiceStarts.includes('AD01.mp3'));
          if (n === 3) assert.ok(await page.evaluate(() => window.voiceEnds.includes('MA06.mp3')), 'closure transition lets the full recording finish');
          if (n > 1) assert.equal(await page.evaluate(() => window.voiceStarts.filter(id => id === 'AD01.mp3').length), 1, 'advisor introduction plays only on the first visit');
          await page.getByRole('button', { name: '규칙을 고른다', exact: true }).click();
          assert.equal(harnessCalls, lockedHarnessCalls, 'no retrospective fetch during loops');
          if (n === 1) {
            await page.getByRole('switch', { name: 'BGM 끄기', exact: true }).click();
            await page.getByRole('switch', { name: 'BGM 켜기', exact: true }).waitFor();
            assert.equal(await bgm.evaluate(audio => audio.paused), true);
          }
          await page.getByRole('button', { name: '추천 규칙 1', exact: true }).click();
          report.checks.push(`loop ${n}: 100% continues`);
        }
      }
      await page.getByRole('heading', { name: '다섯 번째 밤, 마지막 기록' }).waitFor();
      await page.getByText(`최종 이해도 ${finalScore}%`, { exact: true }).waitFor();
      assert.equal(await page.getByText('부작용', { exact: true }).count(), 0);
      await page.screenshot({ path: `${out}/final-${finalScore}.png`, fullPage: true });
      await page.getByRole('button', { name: '이 세계의 바깥으로', exact: true }).click();
      await page.getByText('일시적인 오류', { exact: true }).waitFor();
      failHarness = false;
      await page.getByRole('button', { name: '다시 불러오기', exact: true }).click();
      await page.getByRole('heading', { name: '너의 추리는 이렇게 걸어왔다.' }).waitFor();
      await page.waitForFunction(() => window.voiceStarts.includes('EN01.mp3'));
      await page.getByText('신이 연 단서 — 트럭은 실어 갈 뿐이다.', { exact: false }).waitFor();
      await page.getByRole('heading', { name: '진실과 내 기록' }).waitFor();
      if (finalScore === 100) {
        await page.getByText('이들은 동물이다', { exact: false }).waitFor();
      } else {
        assert.equal(await page.getByText('이들은 동물이다', { exact: false }).count(), 0, 'unconfirmed truth stays locked');
        await page.getByText('아직 비어 있는 자리', { exact: true }).waitFor();
      }
      await page.getByText('개발 데이터 — 규칙·검사·모델 동작이 궁금하다면', { exact: false }).click();
      await page.waitForFunction(() => window.voiceStarts.includes('EN02.mp3'));
      await page.getByRole('button', { name: '회고 대사 다시 듣기', exact: true }).last().click();
      await page.waitForFunction(() => window.voiceStarts.includes('EN03.mp3'));
      await page.getByText('수락 1회', { exact: false }).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `${out}/retrospective-${finalScore}.png`, fullPage: true });
      report.checks.push(`final ${finalScore}%: ending, retrospective, fetch retry, mobile fit`);
      await page.getByRole('button', { name: '다시 시작', exact: true }).click();
      await page.getByText('지난 판의 기록', { exact: true }).waitFor();
      assert.equal(retry, true);
      report.checks.push(`final ${finalScore}%: new attempt`);
      assert.equal(await page.locator('audio[data-audio="voice"]').evaluate(audio => audio.paused), true, 'retry stops the previous retrospective voice');
      report.checks.push('voice: first advisor only, complete closure announcement, three retrospective cues, retry cancellation');
      assert.equal(await bgmHandle.evaluate(audio => audio === document.querySelector('audio[src="/audio/game-bgm.mp3"]') && !audio.paused), true, 'retry keeps the same music playing');
      report.checks.push('BGM: entry autoplay, actual MP3 playback, end-to-start loop, scene/loop continuity, off/on, retry continuity');
      // Client navigation keeps the JS context alive so we can inspect unmount cleanup.
      await page.evaluate(() => window.next.router.push('/harness/test'));
      await page.getByRole('heading', { name: '너의 추리는 이렇게 걸어왔다.' }).waitFor();
      assert.equal(await bgmHandle.evaluate(audio => audio.paused), true, 'leaving the game stops music');
      await context.close();
    }
    assert.deepEqual(report.errors, []);
  } finally {
    fs.writeFileSync(`${out}/results.json`, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });

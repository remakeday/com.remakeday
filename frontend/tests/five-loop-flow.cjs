// Run with Playwright available through NODE_PATH. All game API requests are mocked.
// NODE_PATH=/tmp/pigfarm-review-Hewzkn/node_modules node tests/five-loop-flow.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const out = process.env.TEST_ARTIFACT_DIR || '/tmp/pigfarm-five-loop-browser';
fs.mkdirSync(out, { recursive: true });

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const report = { mode: 'mock API, real frontend; no game DB writes', checks: [], errors: [] };
  try {
    for (const finalScore of [0, 100]) {
      const context = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
      const page = await context.newPage();
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
          body = { total, passed: total >= 50, loop_n: loopN, world_outcome: 'truck', is_final: loopN === 5, closed_by: loopN === 5 ? (total === 100 ? 'understood_all' : 'doom') : null, cells: loopN === 5 ? cells : null, cookie: null, intervention_available: loopN < 5, ending_lines: loopN === 5 ? ['우리가 대피소라고 믿었던 곳은 양돈장이었다.'] : null, cell_feedback: '원인은 잡혔다.', wrong_claim_count: 0 };
        } else if (path.endsWith('/options')) body = { options: [1, 2, 3].map(index => ({ index, label: `추천 규칙 ${index}`, target: '채연', action: '배급을 설명한다', effect: 'enforce', when_beat: 'any', reason: '관찰을 확인하기 위해', evidence_ids: [], expected_observation: '다음 배급 장면에서 설명을 듣는다.' })) };
        else if (path.endsWith('/rule')) body = { ok: true, rule_label: '추천 규칙 1', conflicts: [], reason: null };
        else if (path.endsWith('/harness')) {
          harnessCalls++;
          if (loopN < 5 || !submitted) { status = 403; body = { detail: '다섯 번째 밤을 마치면 열린다' }; }
          else if (failHarness) { status = 503; body = { detail: '일시적인 오류' }; }
          else body = { rules: [{ rule_id: 'R1', source: 'monkey_paw', target: '채연', when_beat: null, effect: 'suppress', action: '배급을 남긴다', shown_reason: null, hidden_side_effect: '다른 인물의 의심이 커진다.', created_loop: 1, conflict: false }], harness_summary: { total_events: 20, harness_interventions: 2, fallbacks: 1, paw_accepted: 1, recommended_rules: 4, custom_rules: 0, rule_conflicts: 0, questions_asked: 0, rule_success_rate: null, tool_side_effects: [{ loop_n: 2, beat: 3, text: '의심 증가' }] } };
        } else { report.errors.push(`Unmocked API: ${path}`); return route.abort(); }
        await route.fulfill({ status, json: body, headers: { 'access-control-allow-origin': '*' } });
      });
      await page.goto('http://localhost:3500/harness/test');
      await page.getByText('다섯 번째 밤을 마치면 열린다', { exact: true }).waitFor();
      report.checks.push('unfinished retrospective locked');
      await page.goto('http://localhost:3500/play');
      const lockedHarnessCalls = harnessCalls; // 개발 모드의 StrictMode는 mount effect를 재실행한다.
      await page.getByRole('button', { name: '시작', exact: true }).click();
      for (let n = 1; n <= 5; n++) {
        await page.getByText(`오늘 남은 대화 ${9 - n}회`, { exact: true }).waitFor();
        await page.getByRole('button', { name: '계속', exact: true }).click();
        assert.equal(await page.getByRole('heading', { name: '플레이 안내' }).count(), 0, 'tutorial does not block repeat days');
        await page.getByText(`오늘 남은 대화 ${9 - n}회`, { exact: true }).waitFor();
        await page.getByRole('button', { name: '다음 장면', exact: true }).click();
        await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
        await page.getByPlaceholder('자유롭게 쓴다…').fill('상황과 정체에 대한 이해');
        await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
        await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
        await page.getByText(`${n}/5번째 밤 · 상황 이해도`, { exact: true }).waitFor();
        await page.getByRole('button', { name: '계속', exact: true }).click();
        if (n < 5) {
          await page.getByRole('button', { name: '규칙을 고른다', exact: true }).click();
          assert.equal(harnessCalls, lockedHarnessCalls, 'no retrospective fetch during loops');
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
      await page.getByRole('heading', { name: '당신은 이 세계의 규칙을 고치고 있었다.' }).waitFor();
      await page.getByText('원숭이손 수락 1회', { exact: false }).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `${out}/retrospective-${finalScore}.png`, fullPage: true });
      report.checks.push(`final ${finalScore}%: ending, retrospective, fetch retry, mobile fit`);
      await page.getByRole('button', { name: '다시 시작', exact: true }).click();
      await page.getByText('지난 판의 기록', { exact: true }).waitFor();
      assert.equal(retry, true);
      report.checks.push(`final ${finalScore}%: new attempt`);
      await context.close();
    }
    assert.deepEqual(report.errors, []);
  } finally {
    fs.writeFileSync(`${out}/results.json`, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });

// Tier C Light: controller checks the diff and runs this headless scenario.
// NODE_PATH=/path/to/playwright/node_modules node frontend/tests/clear-survey.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { line, readAll } = require('./vn-helpers.cjs');

const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:3500';
const attemptId = 'clear-survey';
const surveyPath = `/attempts/${attemptId}/survey`;
const cells = { cause: 100, motive: 100, identity: 100, side_effect: 0 };

// Start at the fifth day; the real night-submit transition must enter clear.
const fixtures = {
  'POST /sessions': {
    attempt_id: attemptId, attempt_n: 1, entry_lines: ['마지막 하루를 관찰한다.'], prior_cell_results: null,
  },
  [`POST /sessions/${attemptId}/loops`]: {
    loop_id: 'survey-loop', loop_n: 5, morning_text: '다섯 번째 아침이다.', damage_level: 3,
    budget_left: 4, beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null,
    lines: [line('scene', '불이 꺼진다.')], illustrations: [], observations: [], active_rules: [], aftermath: null,
  },
  'GET /loops/survey-loop/observations': { observations: [] },
  'GET /loops/survey-loop/npcs': { npcs: [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }] },
  'POST /loops/survey-loop/beats/next': {
    beat: 6, beat_title: '소등 후', narration: '하루가 끝났다.', broadcast: null,
    lines: [line('scene', '하루가 끝났다.')], illustrations: [], observations: [], budget_left: 4,
    day_done: true, paw_offer: null, ambient: null, note_found: null,
  },
  'GET /loops/survey-loop/night/previous': { previous_answer: null },
  'POST /loops/survey-loop/night/draft': {
    night_id: 'survey-night', claims: ['상황과 정체를 이해했다.'], is_question: [false],
  },
  'POST /nights/survey-night/submit': {
    total: 100, passed: true, loop_n: 5, world_outcome: 'truck', is_final: true,
    closed_by: 'understood_all', cells, cookie: null, intervention_available: false,
    ending_lines: ['마지막 기록을 남겼다.'], cell_feedback: null, wrong_claim_count: 0,
    accepted_claims: ['상황과 정체를 이해했다.'], empty_cells: [], suggested_questions: [], night_clue: null,
  },
  [`GET /attempts/${attemptId}/journey`]: {
    loops: [1, 2, 3, 4, 5].map(loop_n => ({
      loop_n, total: 100, passed: true, new_confirmed: [], unlocked_notes: [],
    })),
    final: { cells, closed_by: 'understood_all', truth_reveal: [] }, unresolved: [],
  },
  [`GET /attempts/${attemptId}/harness`]: {
    rules: [], harness_summary: {
      total_events: 0, harness_interventions: 0, fallbacks: 0, paw_accepted: 0,
      recommended_rules: 0, custom_rules: 0, rule_conflicts: 0, questions_asked: 0,
      rule_success_rate: null, tool_side_effects: [],
    },
  },
};

async function reachSurvey(page) {
  await page.goto(new URL('/play', frontendUrl).href);
  await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor();
  await page.getByRole('switch', { name: '음성 끄기', exact: true }).click();
  await page.getByRole('button', { name: '시작', exact: true }).click();
  await page.getByRole('button', { name: '계속', exact: true }).click();
  await readAll(page);
  await page.getByRole('button', { name: '다음 장면', exact: true }).click();
  await page.getByRole('button', { name: '밤이 온다', exact: true }).waitFor();
  await readAll(page);
  await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
  await page.getByPlaceholder('자유롭게 쓴다…').fill('상황과 정체를 이해했다.');
  await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
  await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
  await page.getByText('5/5번째 밤 · 상황 이해도', { exact: true }).waitFor();
  await page.getByRole('button', { name: '계속', exact: true }).click();
  await page.getByRole('button', { name: '계속', exact: true }).click();
  await page.getByRole('heading', { name: '다섯 번째 밤, 마지막 기록', exact: true }).waitFor();
  await page.getByRole('button', { name: '이 세계의 바깥으로', exact: true }).click();

  // Check 1: the survey gates the retrospective, including hidden restart buttons.
  const survey = page.locator('[data-survey="block"]');
  await survey.waitFor({ state: 'visible' });
  assert.equal(await page.getByRole('button', { name: '다시 시작', exact: true, includeHidden: true }).count(), 0,
    'restart must not be mounted during the survey');
  assert.equal(await survey.getByRole('radiogroup').count(), 5);
  return survey;
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  try {
    for (const scenario of ['ratings', 'skip', 'server-error', 'hanging-request']) {
      const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
      try {
        const page = await context.newPage();
        page.setDefaultTimeout(10000);
        const errors = [];
        const surveyRequests = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.route('**/*', async route => {
          const request = route.request();
          const url = new URL(request.url());
          if (url.port !== '8500') return route.continue();
          const key = `${request.method()} ${url.pathname}`;
          let body, status = 200;
          if (key === `POST ${surveyPath}`) {
            surveyRequests.push(request.postDataJSON());
            // Leave the request intercepted without fulfilling, aborting, or continuing it.
            if (scenario === 'hanging-request') return;
            status = scenario === 'server-error' ? 500 : 200;
            body = status === 500 ? { detail: '설문 저장 실패' } : { recorded: true };
          } else if (Object.hasOwn(fixtures, key)) {
            body = fixtures[key];
          } else {
            const message = `Unexpected API: ${key}`;
            errors.push(message);
            await route.abort();
            throw new Error(message);
          }
          await route.fulfill({ status, json: body, headers: {
            'access-control-allow-origin': new URL(frontendUrl).origin,
            'access-control-allow-credentials': 'true',
          } });
        });

        const survey = await reachSurvey(page);
        assert.deepEqual(surveyRequests, [], 'entering the survey must not send a response');
        const skipped = scenario === 'skip';
        if (!skipped) {
          await survey.getByRole('radiogroup', { name: '재미·몰입도', exact: true })
            .getByRole('radio', { name: '재미·몰입도 3점', exact: true }).click();
          await survey.getByRole('radiogroup', { name: '추천 의향', exact: true })
            .getByRole('radio', { name: '추천 의향 5점', exact: true }).click();
          assert.equal(await survey.getByRole('radio', { checked: true }).count(), 2, 'only two items are rated');
        }

        if (scenario === 'hanging-request') {
          assert.equal(await page.getByText('평가 고맙다.', { exact: true }).count(), 0);
          await Promise.all([
            page.waitForRequest(req => new URL(req.url()).pathname === surveyPath && req.method() === 'POST'),
            survey.getByRole('button', { name: '평가 보내기', exact: true }).click(),
          ]);
          assert.equal(await survey.getByRole('button', { disabled: true }).count(), 2);
          assert.equal(await survey.getByRole('radio', { disabled: true }).count(), 25);
          // Allow the real five-second timer to expire, with room for a loaded runner.
          await page.getByRole('button', { name: '다시 시작', exact: true })
            .waitFor({ state: 'visible', timeout: 15000 });
          await page.getByText('평가 고맙다.', { exact: true }).waitFor();
        } else {
          // Checks 2–4: capture the POST body and actual response, then require progress.
          const [response] = await Promise.all([
            page.waitForResponse(res => new URL(res.url()).pathname === surveyPath && res.request().method() === 'POST'),
            survey.getByRole('button', { name: skipped ? '건너뛰기' : '평가 보내기', exact: true }).click(),
          ]);
          assert.equal(response.status(), scenario === 'server-error' ? 500 : 200);
        }
        await page.getByRole('button', { name: '다시 시작', exact: true }).waitFor({ state: 'visible' });
        await survey.waitFor({ state: 'detached' });
        await page.getByRole('heading', { name: '너의 추리는 이렇게 걸어왔다.', exact: true }).waitFor();
        // Wait for both retrospective fetches, so an unmocked secondary API cannot silently pass.
        await page.getByText('개발 데이터 — 규칙·검사·모델 동작이 궁금하다면', { exact: true }).waitFor();
        assert.deepEqual(surveyRequests, [skipped ? { skipped: true } : { skipped: false, fun: 3, recommend: 5 }],
          `${scenario}: exactly one POST with the exact body, no unselected scores`);
        assert.deepEqual(errors, [], `${scenario}: no page errors or unexpected API calls`);
        console.log(`PASS clear-survey ${scenario}: survey gates restart, exact POST body, retrospective reached`);
      } finally { await context.close(); }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

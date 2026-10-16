// 이어하기·마이페이지·회원탈퇴 (설계 2026-10-16) — 가짜 API만 쓴다(백엔드 불필요).
// NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/resume-mypage.cjs
// 헤드리스 브라우저 하나를 이 스크립트가 띄우고 끝에 닫는다. 프론트 dev 서버(3500)는 컨트롤러가 미리 띄운다.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { line, readAll, expectBudget } = require('./vn-helpers.cjs');

const BASE = 'http://localhost:3500';
const CORS = { 'access-control-allow-origin': BASE, 'access-control-allow-credentials': 'true' };
const ATTEMPT = { attempt_id: 'resume', attempt_n: 1, entry_lines: ['세계가 이상하다.'], prior_cell_results: null };
const NPCS = [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }];
const SUBMIT = {
  total: 40, passed: false, loop_n: 2, world_outcome: 'truck', is_final: false, closed_by: null, cells: null,
  cookie: null, intervention_available: true, ending_lines: null, truth_reveal: null, cell_feedback: null,
  wrong_claim_count: 0, accepted_claims: [], empty_cells: ['cause', 'motive'], night_clue: null, suggested_questions: [],
};
const NIGHT = { night_id: 'resume-night', claims: ['채연이 밥을 남겼다.'], is_question: [false], questions_left: 3, submit: null };

function loopShell(fields = {}) {
  return {
    loop_id: 'resume-loop', loop_n: 2, morning_text: '7시 12분. 눈을 뜬다.', damage_level: 1, budget_left: 4,
    beat: 3, beat_title: '', narration: '', broadcast: null, illustrations: [], aftermath: null,
    ambient: null, note_found: null, observations: [], active_rules: [], lines: [], ...fields,
  };
}

const DAY_LOOP = loopShell({
  beat_title: '정오 배급', narration: '쟁반이 돈다. 채연이 쟁반을 밀어낸다.',
  lines: [line('scene', '쟁반이 돈다.'), line('action', '채연이 쟁반을 밀어낸다.')],
});
const NONE = { attempt: null, resume_phase: null, loop: null, night: null, today_remaining: 3, daily_limit: 3 };

function snapshot(phase, fields = {}) {
  return { attempt: ATTEMPT, resume_phase: phase, loop: null, night: null, today_remaining: 2, daily_limit: 3, ...fields };
}

/** 페이지 하나와 가짜 API — calls에 "메서드 경로"가 순서대로 쌓인다. 끝나면 이 페이지만 닫는다. */
async function withPage(browser, { active, me = 200, activeStatus = 200, abandonDelay = 0 }, run) {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  page.setDefaultTimeout(15000);
  const calls = [];
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/*', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.port !== '8500') return route.continue();
    if (request.method() === 'OPTIONS') {
      return route.fulfill({ status: 204, headers: { ...CORS, 'access-control-allow-methods': 'GET,POST,PATCH,DELETE', 'access-control-allow-headers': 'content-type' } });
    }
    const key = `${request.method()} ${url.pathname}`;
    calls.push(key);
    const reply = (status, json) => (json === undefined
      ? route.fulfill({ status, body: '', headers: CORS })
      : route.fulfill({ status, json, headers: CORS }));
    if (key === 'GET /api/v1/me/attempts/active') return reply(activeStatus, active);
    if (key === 'POST /api/v1/me/attempts/active/abandon') {
      if (abandonDelay) await new Promise((resolve) => setTimeout(resolve, abandonDelay));
      return reply(204);
    }
    if (key === 'POST /sessions') return reply(200, { ...ATTEMPT, attempt_id: 'fresh' });
    if (key === 'GET /api/v1/auth/me') {
      return me === 200 ? reply(200, { sub: 'g-1', email: 'a@x', name: 'a', picture: '' }) : reply(401, { detail: '로그인되어 있지 않습니다' });
    }
    if (key === 'DELETE /api/v1/auth/me') return reply(204);
    if (url.pathname.endsWith('/observations')) return reply(200, { observations: [] });
    if (url.pathname.endsWith('/npcs')) return reply(200, { npcs: NPCS });
    if (url.pathname.endsWith('/night/previous')) return reply(200, { previous_answer: null });
    if (url.pathname.endsWith('/notes')) return reply(200, { notes: [] });
    errors.push(`Unexpected API: ${key}`);
    return route.abort();
  });
  try {
    await run(page, calls);
    assert.deepEqual(errors, [], 'no page errors or unexpected API calls');
  } finally {
    await page.close();
  }
}

const CHECKS = [
  ['choice screen shows cost, 이어하기 opens the day', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByText('오늘 남은 판 2/3 · 다시 시작하면 1회가 차감됩니다', { exact: true }).waitFor();
    await page.getByRole('button', { name: '이어하기', exact: true }).click();
    await expectBudget(page, 4);
    await readAll(page);
    await page.getByText('쟁반이 돈다.', { exact: false }).first().waitFor();
    assert.ok(!calls.includes('POST /sessions'), '이어하기는 새 판을 만들지 않는다');
  })],
  ['no games left disables restart', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP, today_remaining: 0 }) }, async (page) => {
    await page.goto(`${BASE}/play`);
    await page.getByText('오늘은 더 시작할 수 없습니다', { exact: true }).waitFor();
    assert.equal(await page.getByRole('button', { name: '다시 시작하기', exact: true }).isDisabled(), true);
    assert.equal(await page.getByRole('button', { name: '이어하기', exact: true }).isDisabled(), false);
  })],
  ['restartOnceOnDoubleClick', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }), abandonDelay: 500 }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    // 두 번째 클릭도 abandon 응답 전에 닿도록 응답을 지연한다.
    await page.getByRole('button', { name: '다시 시작하기', exact: true }).dblclick();
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.deepEqual(calls.filter((c) => c.startsWith('POST ')), ['POST /api/v1/me/attempts/active/abandon', 'POST /sessions']);
  })],
  ['?resume=1 skips the choice screen', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page) => {
    await page.goto(`${BASE}/play?resume=1`);
    await expectBudget(page, 4);
    assert.equal(await page.getByRole('button', { name: '다시 시작하기', exact: true }).count(), 0);
  })],
  ['attempt without loops is reused silently', (browser) => withPage(browser, { active: snapshot('entry') }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.equal(await page.getByRole('button', { name: '이어하기', exact: true }).count(), 0);
    assert.ok(!calls.includes('POST /sessions'), '회차 없는 판은 묻지 않고 그대로 쓴다');
  })],
  ['fallsBackWhenActiveLookupFails', (browser) => withPage(browser, { active: { detail: 'Not Found' }, activeStatus: 404 }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.ok(calls.includes('POST /sessions'), '조회 API가 없으면 예전처럼 새 판');
  })],
  ['activeLookup500ShowsRetry', (browser) => withPage(browser, { active: NONE }, async (page, calls) => {
    await page.route('**/api/v1/me/attempts/active', (route) => {
      calls.push('GET /api/v1/me/attempts/active');
      return route.fulfill({ status: 500, json: { detail: 'Internal Server Error' }, headers: CORS });
    }, { times: 1 });
    await page.goto(`${BASE}/play`);
    const retry = page.getByRole('button', { name: '재시도', exact: true });
    await retry.waitFor({ state: 'visible' });
    assert.equal(calls.filter((c) => c === 'POST /sessions').length, 0, '조회가 500이면 새 판을 만들지 않는다');
    await retry.click();
    await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
    assert.equal(calls.filter((c) => c === 'GET /api/v1/me/attempts/active').length, 2, '재시도는 진행 중인 판을 다시 조회한다');
    assert.equal(calls.filter((c) => c === 'POST /sessions').length, 1, '재조회 결과 판이 없으면 새 판을 한 번 만든다');
  })],
  ['activeLookupNetworkErrorShowsRetry', (browser) => withPage(browser, { active: NONE }, async (page, calls) => {
    await page.route('**/api/v1/me/attempts/active', (route) => {
      calls.push('GET /api/v1/me/attempts/active');
      return route.abort();
    }, { times: 1 });
    await page.goto(`${BASE}/play`);
    await page.getByRole('button', { name: '재시도', exact: true }).waitFor({ state: 'visible' });
    assert.equal(calls.filter((c) => c === 'POST /sessions').length, 0, '조회가 네트워크 오류이면 새 판을 만들지 않는다');
  })],
  ['activeLookupDailyAttemptLimitShowsGuard', (browser) => withPage(browser, { active: { code: 'daily_attempt_limit', detail: '오늘은 여기까지. 내일 다시 시작할 수 있다.' }, activeStatus: 403 }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByText('오늘은 여기까지', { exact: false }).waitFor();
    assert.equal(calls.filter((c) => c === 'POST /sessions').length, 0, '조회가 하루 한도 허들이면 새 판을 만들지 않는다');
  })],
  ['activeLookupDailyCapShowsGuard', (browser) => withPage(browser, { active: { code: 'daily_cap', detail: '오늘 정원이 마감됐다.' }, activeStatus: 503 }, async (page, calls) => {
    await page.goto(`${BASE}/play`);
    await page.getByText('정원이 마감', { exact: false }).waitFor();
    assert.equal(calls.filter((c) => c === 'POST /sessions').length, 0, '조회가 정원 마감 허들이면 새 판을 만들지 않는다');
  })],
  ['night draft resumes at the confirm screen', (browser) => withPage(browser, { active: snapshot('night', { loop: loopShell({ beat: 6 }), night: NIGHT }) }, async (page) => {
    await page.goto(`${BASE}/play?resume=1`);
    await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).waitFor();
    await page.getByText('채연이 밥을 남겼다.', { exact: false }).first().waitFor();
  })],
  ['god resumes with remaining questions', (browser) => withPage(browser, { active: snapshot('god', { loop: loopShell({ beat: 6 }), night: { ...NIGHT, questions_left: 1, submit: SUBMIT } }) }, async (page) => {
    await page.goto(`${BASE}/play?resume=1`);
    await page.getByText('남은 질문 1', { exact: true }).waitFor();
  })],
  ['landing shows 마이페이지 when logged in', (browser) => withPage(browser, { active: NONE }, async (page) => {
    await page.goto(`${BASE}/`);
    const link = page.getByRole('link', { name: '마이페이지', exact: true });
    await link.waitFor();
    assert.equal(await link.getAttribute('href'), '/mypage');
  })],
  ['mypage 이어하기 opens the resumed day', (browser) => withPage(browser, { active: snapshot('day', { loop: DAY_LOOP }) }, async (page) => {
    await page.goto(`${BASE}/mypage`);
    const resume = page.getByRole('link', { name: '이어하기', exact: true });
    await resume.waitFor();
    assert.equal(await resume.getAttribute('href'), '/play?resume=1');
    await resume.click();
    await expectBudget(page, 4);
    assert.equal(await page.getByRole('button', { name: '다시 시작하기', exact: true }).count(), 0);
  })],
  ['mypage withdraw needs the inline confirm step', (browser) => withPage(browser, { active: NONE }, async (page, calls) => {
    await page.goto(`${BASE}/mypage`);
    const withdraw = page.getByRole('button', { name: '회원탈퇴', exact: true });
    await withdraw.waitFor();
    const bounds = await withdraw.boundingBox();
    const firstClick = { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 };
    await page.mouse.click(firstClick.x, firstClick.y);
    await page.getByText('모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다', { exact: true }).waitFor();
    await page.mouse.click(firstClick.x, firstClick.y);
    assert.ok(!calls.includes('DELETE /api/v1/auth/me'), '회원탈퇴 직후 같은 좌표를 다시 눌러도 탈퇴 요청이 없다');
    assert.equal(await page.getByRole('link', { name: '이어하기', exact: true }).count(), 0, '진행 중인 판이 없으면 이어하기가 없다');
    await page.getByRole('button', { name: '취소', exact: true }).click();
    assert.equal(await page.getByRole('button', { name: '탈퇴', exact: true }).count(), 0);
    assert.ok(!calls.includes('DELETE /api/v1/auth/me'), '취소하면 탈퇴 요청이 없다');
    await page.getByRole('button', { name: '회원탈퇴', exact: true }).click();
    await page.getByRole('button', { name: '탈퇴', exact: true }).click();
    await page.waitForURL(`${BASE}/`);
    assert.equal(calls.filter((c) => c === 'DELETE /api/v1/auth/me').length, 1);
  })],
  ['mypage without login goes back to landing', (browser) => withPage(browser, { active: NONE, me: 401 }, async (page) => {
    await page.goto(`${BASE}/mypage`);
    await page.waitForURL(`${BASE}/`);
  })],
];

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  try {
    for (const [name, check] of CHECKS) {
      await check(browser);
      console.log(`ok - ${name}`);
    }
    console.log('PASS resume-mypage');
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

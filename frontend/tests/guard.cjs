// Run with Playwright available through NODE_PATH — the path below is one environment's example, not a fixed requirement.
// NODE_PATH=/home/kimchungsik/projects/cloud.localhostdaegu/frontend/node_modules node tests/guard.cjs
// API fixtures only; the parent task owns the single headless browser process.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const SCREENSHOT_DIR = path.join(__dirname, '.playwright-out', 'guard');
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

const CASES = [
  {
    name: 'login (401)',
    status: 401,
    headers: {},
    json: { detail: '로그인이 필요하다' },
    expectText: '로그인이 필요하다',
    check: async page => {
      await page.getByRole('link', { name: '랜딩으로' }).waitFor();
      assert.equal(await page.getByRole('link', { name: '랜딩으로' }).getAttribute('href'), '/');
    },
  },
  {
    name: 'daily_limit (403)',
    status: 403,
    headers: {},
    json: { code: 'daily_attempt_limit', detail: '오늘은 여기까지. 내일 다시 시작할 수 있다.' },
    expectText: '오늘은 여기까지',
  },
  {
    name: 'daily_cap (503)',
    status: 503,
    headers: {},
    json: { code: 'daily_cap', detail: '오늘 정원이 마감됐다.' },
    expectText: '정원이 마감',
  },
  {
    name: 'rate (429)',
    status: 429,
    headers: { 'retry-after': '7' },
    json: { detail: { detail: '요청이 너무 잦다', retry_after: 7 } },
    expectText: '7초',
  },
];

// 밤 단서 시퀀스 — 재시작 케이스가 다섯 회차를 끝까지 돌아 클리어 화면에 닿는 데만 필요한 최소 payload.
const NIGHT_CLUES = {
  1: { caption: '소독약 냄새. 발 아래 콘크리트가 차다.', image_ids: ['P01'], voice_id: 'MA08', broadcast: null, outcome_line: '트럭 소리.' },
  2: { caption: '트럭 소리.', image_ids: ['P02'], voice_id: 'MA09', broadcast: null, outcome_line: null },
  3: { caption: '거울이 없다.', image_ids: ['P03'], voice_id: 'MA10', broadcast: null, outcome_line: null },
  4: { caption: '배급 포대에 글자가 있다.', image_ids: ['P04'], voice_id: 'MA11', broadcast: null, outcome_line: '트럭 옆면 "○○축산".' },
  5: { caption: '손이 없어서 문을 못 연다는 것을 문득 안다.', image_ids: ['P05'], voice_id: 'MA12', broadcast: null, outcome_line: null },
};

/** 클리어 화면까지 다섯 회차를 모두 통과한 뒤, 재시작을 눌러 /sessions가 403을 돌려줘도 GuardScreen이 뜨는지 확인한다. */
async function testRestartGuard(browser) {
  const errors = [];
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
  page.on('pageerror', error => errors.push(`restart guard: ${error.message}`));
  let loopN = 0;
  let sessionCalls = 0;
  const cells = { cause: 100, motive: 100, identity: 100, side_effect: 0 };
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.port !== '8500') return route.continue();
    const p = url.pathname;
    let body, status = 200;
    if (p === '/sessions') {
      sessionCalls++;
      if (sessionCalls === 1) {
        body = { attempt_id: 'test', attempt_n: 1, entry_lines: ['세계가 이상하다.'], prior_cell_results: null };
      } else {
        status = 403;
        body = { code: 'daily_attempt_limit', detail: '오늘은 여기까지. 내일 다시 시작할 수 있다.' };
      }
    } else if (p === '/sessions/test/loops') {
      loopN++;
      body = { loop_id: `loop-${loopN}`, loop_n: loopN, morning_text: '7시 12분. 눈을 뜬다.', damage_level: Math.min(3, loopN - 1), budget_left: 9 - loopN, beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null, aftermath: null, active_rules: [], observations: [] };
    } else if (p.endsWith('/npcs')) body = { npcs: [{ code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false }] };
    else if (p.endsWith('/beats/next')) body = { beat: 6, beat_title: '소등 후', narration: '불이 꺼진다.', broadcast: null, day_done: true, paw_offer: null, note_found: null, ambient: null, observations: [], budget_left: 9 - loopN };
    else if (p.endsWith('/observations')) body = { observations: [] };
    else if (p.endsWith('/night/previous')) body = { previous_answer: null };
    else if (p.endsWith('/notes')) body = { notes: [] };
    else if (p.endsWith('/night/draft')) body = { night_id: `night-${loopN}`, claims: ['상황과 정체에 대한 이해'] };
    else if (p.endsWith('/submit')) {
      body = {
        total: 100, passed: true, loop_n: loopN, world_outcome: loopN === 3 ? 'closure' : 'truck',
        is_final: loopN === 5, closed_by: loopN === 5 ? 'understood_all' : null, cells: loopN === 5 ? cells : null,
        cookie: null, intervention_available: loopN < 5, ending_lines: loopN === 5 ? ['우리가 대피소라고 믿었던 곳은 양돈장이었다.'] : null,
        cell_feedback: '원인은 잡혔다.', wrong_claim_count: 0, night_clue: { loop_n: loopN, ...NIGHT_CLUES[loopN] },
      };
    } else if (p.endsWith('/options')) {
      body = { options: [1, 2, 3].map(index => ({ index, label: `추천 규칙 ${index}`, target: '채연', action: '배급을 설명한다', effect: 'enforce', when_beat: 'any', reason: '관찰을 확인하기 위해', evidence_ids: [], expected_observation: '다음 배급 장면에서 설명을 듣는다.' })) };
    } else if (p.endsWith('/rule')) body = { ok: true, rule_label: '추천 규칙 1', conflicts: [], reason: null };
    else if (p.endsWith('/journey')) {
      body = {
        loops: [1, 2, 3, 4, 5].map(n => ({ loop_n: n, total: 100, passed: true, new_confirmed: [], unlocked_notes: [] })),
        final: { cells, closed_by: 'understood_all', truth_reveal: [] },
        unresolved: [],
      };
    } else if (p.endsWith('/harness')) {
      body = { rules: [], harness_summary: { total_events: 0, harness_interventions: 0, fallbacks: 0, paw_accepted: 0, recommended_rules: 0, custom_rules: 0, rule_conflicts: 0, questions_asked: 0, rule_success_rate: null, tool_side_effects: [] } };
    } else {
      errors.push(`restart guard: unexpected API ${p}`);
      return route.abort();
    }
    await route.fulfill({ status, json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
  });
  await page.goto('http://localhost:3500/play');
  await page.getByRole('button', { name: '시작', exact: true }).click();
  for (let n = 1; n <= 5; n++) {
    await page.getByText(`오늘 남은 대화 ${9 - n}회`, { exact: true }).waitFor();
    await page.getByRole('button', { name: '계속', exact: true }).click();
    await page.getByText(`오늘 남은 대화 ${9 - n}회`, { exact: true }).waitFor();
    await page.getByRole('button', { name: '다음 장면', exact: true }).click();
    await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
    await page.getByPlaceholder('자유롭게 쓴다…').fill('상황과 정체에 대한 이해');
    await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
    await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
    await page.getByText(`${n}/5번째 밤 · 상황 이해도`, { exact: true }).waitFor();
    await page.getByRole('button', { name: '계속', exact: true }).click();
    const proceed = page.getByRole('button', { name: '계속', exact: true });
    await proceed.waitFor();
    await proceed.click();
    if (n < 5) {
      await page.getByRole('button', { name: '규칙을 고른다', exact: true }).click();
      await page.getByRole('button', { name: '추천 규칙 1', exact: true }).click();
    }
  }
  await page.getByRole('heading', { name: '다섯 번째 밤, 마지막 기록' }).waitFor();
  await page.getByRole('button', { name: '이 세계의 바깥으로', exact: true }).click();
  await page.getByRole('button', { name: '다시 시작', exact: true }).click();
  await page.getByText('오늘은 여기까지', { exact: false }).waitFor();
  // GuardScreen이 유일한 화면이어야 한다 — ClearScreen의 재시작 버튼이 뒤에 남아있으면 안 된다.
  assert.equal(await page.getByRole('button', { name: '다시 시작', exact: true }).count(), 0, 'GuardScreen이 뜨면 ClearScreen의 재시작 버튼은 사라져야 한다');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'guard-restart.png') });
  await page.close();
  return errors;
}

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  try {
    for (const testCase of CASES) {
      const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
      page.on('pageerror', error => errors.push(`${testCase.name}: ${error.message}`));
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.port !== '8500') return route.continue();
        if (url.pathname === '/sessions') {
          return route.fulfill({
            status: testCase.status,
            json: testCase.json,
            headers: {
              'access-control-allow-origin': 'http://localhost:3500',
              'access-control-allow-credentials': 'true',
              ...testCase.headers,
            },
          });
        }
        errors.push(`${testCase.name}: unexpected API ${url.pathname}`);
        return route.abort();
      });
      await page.goto('http://localhost:3500/play');
      await page.getByText(testCase.expectText, { exact: false }).waitFor();
      if (testCase.check) await testCase.check(page);
      await page.screenshot({ path: path.join(SCREENSHOT_DIR, `guard-${testCase.name.split(' ')[0]}.png`) });
      await page.close();
    }
    errors.push(...(await testRestartGuard(browser)));
    assert.deepEqual(errors, []);
    console.log('PASS login/daily_limit/daily_cap/rate GuardScreen render at 390px + restart path hits GuardScreen on 403');
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

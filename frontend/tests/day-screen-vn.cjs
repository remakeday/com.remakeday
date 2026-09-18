// Fake API + real frontend at 390/1440px. One headless browser; no game DB writes.
// NODE_PATH=/path/to/playwright/node_modules node tests/day-screen-vn.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { line, readAll, expectBudget } = require('./vn-helpers.cjs');

const illustration = { image_id: 'clue-01', caption: '배급을 기다리는 사람들.' };
const narration = '배급 줄 앞에 네 사람이 서 있다.';
const intro = [
  line('scene', narration, { image_id: 'clue-01' }),
  line('scene', '스피커에 불이 들어온다.'),
  line('broadcast', '배급을 시작합니다.', { speaker: '관리자' }),
  line('action', '준이 쟁반을 든다.'),
  line('rule_result', '민석은 기록한 수를 설명한다.'),
  line('statement', '민석: "남긴 양을 적었어."', { speaker: '민석' }),
  line('paw_effect', '채연이 다른 쟁반을 경계한다.'),
  line('npc', '오늘 식판은 네가 먼저 가져가.', { speaker: '준' }),
  line('fragment', '쟁반에 번호가 적혀 있다.', { observation_id: 'vn:fragment-1' }),
  line('system', '단서 기록에 새 내용을 저장했다.'),
];
const observations = [
  { observation_id: 'old', loop_n: 1, beat: 1, scene_title: '지난 배급', actor: null,
    source_kind: 'scene', verification: 'observed', text: '첫날의 배급 기록.', illustrations: [] },
  { observation_id: 'current', loop_n: 3, beat: 1, scene_title: '아침 배급', actor: '민석',
    source_kind: 'rule_result', verification: 'observed', text: '민석이 남긴 양을 설명했다.', illustrations: [illustration] },
  { observation_id: 'vn:fragment-1', loop_n: 3, beat: 1, scene_title: '아침 배급', actor: null,
    source_kind: 'statement', verification: 'reported', text: '쟁반에 번호가 적혀 있다.', illustrations: [] },
];

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  try {
    for (const width of [390, 1440]) {
      const context = await browser.newContext({ viewport: { width, height: 900 }, reducedMotion: 'reduce' });
      try {
        const page = await context.newPage();
        page.setDefaultTimeout(10000);
        page.on('pageerror', error => errors.push(`${width}: ${error.message}`));
        let beat = 1, budget = 6, questions = 0, pawCalls = 0, observationReads = 0;
        const npcs = [['chaeyeon', '채연'], ['minseok', '민석'], ['eunsang', '은상'], ['jun', '준']]
          .map(([code, name]) => ({ code, name, mood: 'calm', uttered: false }));
        await page.route('**/*', async route => {
          const url = new URL(route.request().url());
          if (url.port !== '8500') return route.continue();
          const path = url.pathname;
          let body;
          if (path === '/sessions') body = { attempt_id: 'vn', attempt_n: 1, entry_lines: ['하루를 관찰한다.'], prior_cell_results: null };
          else if (path === '/sessions/vn/loops') body = {
            loop_id: 'vn-loop', loop_n: 3, morning_text: '세 번째 아침이다.', damage_level: 0,
            budget_left: budget, beat, beat_title: '아침 배급', narration, broadcast: '배급을 시작합니다.',
            lines: intro, illustrations: [illustration], observations, active_rules: ['민석이 기록을 설명한다.'], aftermath: null,
          };
          else if (path === '/loops/vn-loop/observations') { observationReads++; body = { observations }; }
          else if (path === '/loops/vn-loop/npcs') body = { npcs };
          else if (path === '/loops/vn-loop/utterances') {
            const request = route.request().postDataJSON();
            const npc = npcs.find(item => item.code === request.target);
            assert.ok(npc && !npc.uttered, 'each question uses an available character');
            npc.uttered = true;
            questions++; budget--;
            const reply = [`답변 ${questions}: 남긴 양을 적었어.`, `답변 ${questions}: 내일도 확인해 봐.`];
            body = { utterance_id: request.request_id, npc, reply: reply.join(' '),
              lines: reply.map(text => line('npc', text, { speaker: npc.name })), budget_left: budget,
              beat, tool_used: false, observations: [] };
          } else if (path === '/loops/vn-loop/beats/next') {
            beat++;
            for (const npc of npcs) npc.uttered = false;
            body = { beat, beat_title: '침상 사이', narration: '담요가 놓인 침상이 보인다.', broadcast: null,
              lines: [line('scene', '담요가 놓인 침상이 보인다.'), line('action', '담요 아래에서 무언가 굴러온다.')],
              illustrations: [], observations: [], budget_left: budget, day_done: beat > 2,
              paw_offer: beat === 2 ? { offer_id: 'vn-paw', rule_label: '모두가 속마음을 말한다.', shown_reason: null } : null,
              ambient: null, note_found: null };
          } else if (path === '/loops/vn-loop/paw/respond') {
            pawCalls++;
            assert.equal(route.request().postDataJSON().accept, false);
            body = { applied: false, rule_label: null, lines: [], illustrations: [], observations: [] };
          } else if (path === '/loops/vn-loop/night/previous') body = { previous_answer: null };
          else if (path === '/loops/vn-loop/night/draft') body = { night_id: 'vn-night', claims: ['배급량을 기록했다.'], is_question: [false] };
          else if (path === '/nights/vn-night/submit') body = {
            total: 40, passed: false, loop_n: 3, world_outcome: 'truck', is_final: false, closed_by: null,
            cells: null, cookie: null, intervention_available: true, ending_lines: null,
            cell_feedback: null, wrong_claim_count: 0, accepted_claims: [], empty_cells: [],
            night_clue: { loop_n: 3, caption: '거울이 없다.', image_ids: ['P03'], voice_id: 'MA10', broadcast: null, outcome_line: null },
          };
          else { errors.push(`${width}: Unexpected API: ${path}`); return route.abort(); }
          await route.fulfill({ json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
        });

        await page.goto('http://localhost:3500/play');
        const hud = page.locator('header[aria-label="게임 현황"]');
        const visibleBounds = async (locator) => {
          await locator.waitFor({ state: 'visible' });
          const bounds = await locator.boundingBox();
          assert.ok(bounds, `${locator} has a visible bounding box`);
          return bounds;
        };
        const hudPosition = async () => {
          const bounds = await visibleBounds(hud);
          assert.equal(await hud.count(), 1, 'HUD is mounted once');
          return bounds;
        };
        // Session creation remounts the HUD with the attempt ID as its key.
        await page.getByRole('button', { name: '시작', exact: true, disabled: false }).waitFor({ state: 'visible' });
        await hud.getByText('1일째 / 5일', { exact: true }).waitFor();
        const position = await hudPosition();
        assert.equal(position.y, 0);
        await page.getByRole('switch', { name: '음성 끄기', exact: true }).click();
        await page.getByRole('button', { name: '시작', exact: true }).click();
        await hud.getByText('3일째 / 5일', { exact: true }).waitFor();
        assert.deepEqual(await hudPosition(), position, 'morning keeps the entry HUD position');
        await page.getByRole('button', { name: '계속', exact: true }).click();
        const box = page.getByRole('region', { name: '대사창', exact: true });
        const input = page.getByRole('textbox', { name: '인물에게 질문', exact: true });
        const nextScene = page.getByRole('button', { name: '다음 장면', exact: true });
        const next = page.getByRole('button', { name: '다음', exact: true });
        const previous = page.getByRole('button', { name: '이전', exact: true });
        const text = box.locator('[data-line-kind]');
        await box.getByText(narration, { exact: true }).waitFor();
        const meter = page.getByRole('meter', { name: '남은 대화 횟수', exact: true });
        const expectGaugeUnderTitle = async (mode) => {
          await page.locator(`[data-day-mode="${mode}"]`).waitFor();
          const titleBlock = page.getByTestId('day-title');
          const title = titleBlock.getByText('아침 배급', { exact: true });
          const scene = titleBlock.getByText('장면 1/6', { exact: true });
          const label = page.getByText('남은 대화 횟수', { exact: true });
          const titleBounds = await visibleBounds(title);
          const sceneBounds = await visibleBounds(scene);
          const labelBounds = await visibleBounds(label);
          const gaugeBounds = await visibleBounds(meter);
          assert.equal(sceneBounds.x, titleBounds.x, 'scene row aligns with the beat title');
          assert.ok(sceneBounds.y >= titleBounds.y + titleBounds.height, 'scene row is below the beat title');
          assert.equal(labelBounds.x, titleBounds.x, 'gauge row aligns with the scene title');
          assert.ok(labelBounds.y >= sceneBounds.y + sceneBounds.height, 'gauge row is below the scene row');
          assert.ok(gaugeBounds.x >= labelBounds.x + labelBounds.width, 'visible label precedes the gauge');
          assert.ok(Math.abs(gaugeBounds.y + gaugeBounds.height / 2 - labelBounds.y - labelBounds.height / 2) <= 1, 'label and gauge share a row');
          assert.ok(gaugeBounds.y + gaugeBounds.height <= (await visibleBounds(box)).y, 'gauge stays above the dialogue and input');
          assert.equal(await meter.getAttribute('aria-valuemin'), '0');
        };
        await expectGaugeUnderTitle('intro');
        await expectBudget(page, 6);
        assert.equal(await text.count(), 1, 'one line is rendered at a time');
        assert.equal(await box.getByText(intro[1].text, { exact: true }).count(), 0);
        assert.equal(await input.isDisabled(), true);
        assert.equal(await nextScene.isDisabled(), true);
        assert.equal(await previous.isDisabled(), true);
        assert.deepEqual(await hudPosition(), position, 'day keeps the HUD position');
        const styles = {};
        for (let i = 0; i < intro.length; i++) {
          await box.getByText(`${i + 1} / ${intro.length}`, { exact: true }).waitFor();
          assert.equal(await text.getAttribute('data-line-kind'), intro[i].kind);
          if (['rule_result', 'paw_effect', 'broadcast'].includes(intro[i].kind)) styles[intro[i].kind] = await text.getAttribute('class');
          if (i < intro.length - 1) {
            assert.equal(await input.isDisabled(), true, `line ${i + 1} keeps questions locked`);
            assert.equal(await nextScene.isDisabled(), true, `line ${i + 1} keeps scene movement locked`);
            await next.click();
          }
        }
        assert.match(styles.rule_result, /border-l-4/);
        assert.match(styles.paw_effect, /border-orange\/40/);
        assert.match(styles.broadcast, /font-mono/);
        assert.equal(new Set(Object.values(styles)).size, 3, 'lineStyles distinguishes all three kinds');
        await input.fill('누가 기록했어?'); // waits for the intro-to-dialogue effect and NPC refresh
        await expectGaugeUnderTitle('dialogue');
        for (const name of ['채연', '민석', '은상', '준']) {
          const card = page.getByRole('button', { name: `${name} · 대화 가능`, exact: true });
          assert.equal(await card.locator('img').count(), 0, 'character cards show names and status only');
          assert.ok((await visibleBounds(card)).height <= 80, 'character cards stay compact');
        }
        assert.equal(await nextScene.isEnabled(), true);
        await expectBudget(page, 6);
        assert.equal(await meter.getAttribute('aria-valuemax'), '6');
        await page.getByRole('button', { name: '묻기', exact: true }).click();
        await box.getByText('답변 1: 남긴 양을 적었어.', { exact: true }).waitFor();
        await box.getByText('11 / 12', { exact: true }).waitFor();
        await expectBudget(page, 5);
        assert.equal(await nextScene.isDisabled(), true, 'unread reply locks scene movement');
        const chaeyeon = page.getByRole('button', { name: '채연 · 이 장면 대화 완료', exact: true });
        assert.equal(await chaeyeon.getAttribute('aria-pressed'), 'true');
        assert.equal(await chaeyeon.locator('img').count(), 0);
        assert.equal(await chaeyeon.evaluate(card => getComputedStyle(card).filter), 'grayscale(1)');
        assert.equal(await chaeyeon.evaluate(card => getComputedStyle(card).opacity), '0.55');
        const portrait = page.getByRole('img', { name: '채연 초상', exact: true });
        assert.equal(await portrait.evaluate(img => getComputedStyle(img).filter), 'grayscale(1)');
        await page.getByRole('button', { name: '민석 · 대화 가능', exact: true }).click();
        assert.equal(await input.isDisabled(), true, 'even an available character waits for the reply to finish');
        await readAll(page);
        await box.getByText('12 / 12', { exact: true }).waitFor();
        await input.fill('두 번째 질문');
        for (let i = 0; i < 11; i++) await previous.click();
        await box.getByText(narration, { exact: true }).waitFor();
        assert.equal(await input.isDisabled(), true, 'history uses the same last-line input lock');
        assert.equal(await input.inputValue(), '두 번째 질문', 'browsing retains a prepared question');
        await readAll(page);
        await box.getByText('12 / 12', { exact: true }).waitFor();
        await page.getByRole('button', { name: '묻기', exact: true }).click();
        await box.getByText('답변 2: 남긴 양을 적었어.', { exact: true }).waitFor();
        await box.getByText('13 / 14', { exact: true }).waitFor();
        await expectBudget(page, 4);
        await readAll(page);
        await box.getByText('14 / 14', { exact: true }).waitFor();
        await chaeyeon.click();
        assert.equal(await input.isDisabled(), true, 'talked-to character remains selectable but cannot be asked again');

        const records = page.getByRole('button', { name: '기록', exact: true });
        await records.click();
        const panel = page.getByRole('dialog', { name: '기록', exact: true });
        assert.equal(await panel.getByRole('tab').count(), 0, 'record panel has no tabs');
        assert.equal(await panel.getByText('NEW', { exact: true }).count(), 2);
        assert.equal(await panel.locator('li').filter({ hasText: '첫날의 배급 기록.' }).getByText('NEW', { exact: true }).count(), 0);
        await panel.getByRole('button', { name: /민석이 남긴 양을 설명했다/ }).click();
        const picture = panel.locator('img[src$="C01-breakfast-clue-v2.png"]');
        await picture.waitFor();
        await picture.evaluate(img => img.decode());
        assert.ok(await picture.evaluate(img => img.naturalWidth > 0));
        await panel.getByRole('button', { name: '기록으로 돌아간다', exact: true }).click();
        await panel.getByRole('button', { name: '기록 닫기', exact: true }).click();
        await page.getByRole('button', { name: '안내', exact: true }).click();
        const guidePanel = page.getByRole('dialog', { name: '안내', exact: true });
        await guidePanel.getByRole('heading', { name: '플레이 안내', exact: true }).waitFor();
        await guidePanel.getByText('민석이 기록을 설명한다.', { exact: true }).waitFor();
        await page.keyboard.press('Escape');
        await guidePanel.waitFor({ state: 'hidden' });
        await box.getByText('14 / 14', { exact: true }).waitFor();
        assert.equal(questions, 2, 'reading and records consume no questions');
        assert.ok(observationReads >= 1, 'HUD fetched observations');

        await nextScene.click();
        await page.getByTestId('day-title').getByText('침상 사이', { exact: true }).waitFor();
        await page.getByTestId('day-title').getByText('장면 2/6', { exact: true }).waitFor();
        const paw = page.getByRole('dialog', { name: '원숭이손의 제안', exact: true });
        assert.equal(await paw.count(), 0, 'paw offer waits for the unread intro');
        await box.getByText('15 / 16', { exact: true }).waitFor();
        assert.equal(await nextScene.isDisabled(), true);
        await next.click();
        await paw.waitFor();
        await paw.getByText('대가 없이 굴러오는 것은 없다.', { exact: true }).waitFor();
        assert.equal(await page.getByRole('textbox', { name: '인물에게 질문', includeHidden: true }).isDisabled(), true);
        await paw.getByRole('button', { name: '제안을 거절한다', exact: true }).click();
        await box.getByText('원숭이손의 제안을 거절했다.', { exact: true }).waitFor();
        assert.equal(pawCalls, 1);
        for (let i = 0; i < 16; i++) await previous.click();
        await box.getByText(narration, { exact: true }).waitFor();
        await readAll(page);
        await box.getByText('17 / 17', { exact: true }).waitFor();
        await nextScene.click();
        await page.getByRole('button', { name: '밤이 온다', exact: true }).waitFor();
        await readAll(page);
        await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
        await page.getByPlaceholder('자유롭게 쓴다…').fill('배급량을 기록했다.');
        await hud.getByText('3일째 / 5일', { exact: true }).waitFor();
        assert.deepEqual(await hudPosition(), position, 'night keeps the HUD position');
        await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
        await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
        await page.getByRole('button', { name: '계속', exact: true }).click();
        await page.getByText('거울이 없다.', { exact: true }).waitFor();
        await page.getByRole('button', { name: '계속', exact: true }).click();
        await page.getByRole('button', { name: '규칙을 고른다', exact: true }).waitFor();
        await hud.getByText('3일째 / 5일', { exact: true }).waitFor();
        assert.deepEqual(await hudPosition(), position, 'god screen keeps the HUD position');
        await records.click();
        await panel.getByText('민석이 남긴 양을 설명했다.', { exact: true }).waitFor();
        await page.keyboard.press('Escape');
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
        assert.deepEqual(errors, []);
        console.log(`PASS day-screen-vn ${width}px: lines, locks, history, styles, budget, portraits, HUD, records, paw timing`);
      } finally { await context.close(); }
    }
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

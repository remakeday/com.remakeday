// NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/gameplay-clarity.cjs
// API fixtures only; the parent task owns the single headless browser process.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  try {
    for (const [width, height] of [[390, 844], [1440, 900], [1564, 800]]) {
      const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
      page.on('pageerror', error => errors.push(error.message));
      let beat = 1, budget = 8, uttered = false, loopCalls = 0, talkCalls = 0;
      const observation = { observation_id: 'scene-2', loop_n: 1, beat: 2, scene_title: '복도', source_kind: 'scene', text: '담요 아래 손목띠가 남아 있다.', illustrations: [] };
      const npc = () => ({ code: 'minseok', name: '민석', mood: 'calm', uttered });
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (url.port !== '8500') return route.continue();
        const path = url.pathname;
        let body;
        if (path === '/sessions') body = { attempt_id: 'clarity', attempt_n: 1, entry_lines: ['눈을 뜬다.'], prior_cell_results: null };
        else if (path.endsWith('/loops')) {
          loopCalls++;
          body = { loop_id: 'day', loop_n: 1, morning_text: '아침이다.', damage_level: 3, budget_left: budget, beat, beat_title: '식당', narration: '민석이 식판을 내려놓는다.', broadcast: null, aftermath: null, active_rules: [], observations: [], illustrations: [{ image_id: 'clue-01', caption: '관리자의 방송 아래 네 사람이 배급을 기다린다.' }, { image_id: 'clue-07', caption: '관리자의 배급 안내' }], ambient: { lines: [{ code: 'minseok', name: '민석', text: '오늘 식판은 네가 먼저 가져가.' }, { code: 'chaeyeon', name: '채연', text: '배 안 고파. 너 먹어.' }, { code: 'jun', name: '준', text: '…이따 배고프면 말해.' }] } };
        } else if (path.endsWith('/npcs')) body = { npcs: [npc(), ...[['chaeyeon', '채연'], ['eunsang', '은상'], ['jun', '준']].map(([code, name]) => ({ code, name, mood: 'calm', uttered: false }))] };
        else if (path.endsWith('/utterances')) {
          talkCalls++; budget--; uttered = true;
          body = { npc: npc(), reply: '오늘 아침 보고는 아직 하지 않았어.', budget_left: budget, beat };
        } else if (path.endsWith('/beats/next')) {
          beat++; uttered = false;
          body = { beat, beat_title: '복도', narration: '문이 열린다.', broadcast: null, day_done: false, illustrations: [], observations: [observation], budget_left: budget,
            ambient: { lines: [{ name: '민석', text: '은상아, 누가 이 자리를 비웠는지 봤어?' }] }, note_found: { text: '긴 기록 원문은 대화 로그에 다시 붙이지 않는다.' },
            paw_offer: { offer_id: 'offer', rule_label: '누구나 말하게 한다.', shown_reason: null } };
        } else if (path.endsWith('/paw/respond')) body = { applied: false, rule_label: null };
        else if (path.endsWith('/observations')) body = { observations: [observation] };
        else { errors.push(`Unexpected API ${path}`); return route.abort(); }
        return route.fulfill({ json: body, headers: { 'access-control-allow-origin': '*' } });
      });
      await page.goto('http://localhost:3500/play');
      await page.getByRole('heading', { name: '플레이 안내' }).waitFor();
      assert.equal(await page.locator('details').getAttribute('open'), null, 'initial details start collapsed');
      assert.ok((await page.locator('main').innerText()).includes('오늘 대화 8회'));
      assert.equal((await page.locator('main').innerText()).includes('8 / 7 / 6 / 5 / 4회'), false, 'full schedule stays behind disclosure');
      await page.getByText('자세한 규칙', { exact: true }).click();
      for (const rule of ['5일', '6장면', '8 / 7 / 6 / 5 / 4회', '인물마다 한 장면에 1회', '충전되지 않는다', '처음 네 번의 밤', '3회']) {
        assert.ok((await page.locator('main').innerText()).includes(rule), `initial guide explains ${rule}`);
      }
      assert.ok((await page.locator('main').innerText()).includes('특별한 규칙의 대가'));
      await page.getByText('자세한 규칙', { exact: true }).click();
      assert.equal(loopCalls, 0, 'guide appears before starting gameplay');
      await page.getByRole('button', { name: '시작', exact: true }).click();
      await page.getByText('오늘 남은 대화 8회', { exact: true }).waitFor();
      const morning = page.getByRole('button', { name: '계속', exact: true });
      const morningBounds = await morning.boundingBox();
      assert.ok(morningBounds.height >= height, `morning fills viewport, got ${morningBounds.height}px`);
      const morningImage = morning.locator('img');
      assert.equal(await morningImage.evaluate(el => getComputedStyle(el).objectFit), 'contain', 'show the whole morning illustration without cropping');
      for (const label of ['5일 중 1일째 아침이다.', '탭하여 계속']) {
        const style = await page.getByText(label, { exact: true }).evaluate(el => ({ font: parseFloat(getComputedStyle(el).fontSize), opacity: getComputedStyle(el).opacity }));
        assert.ok(style.font >= 18, `${label} is readable without enlarging the chat panel`);
        assert.equal(style.opacity, '1', `${label} is not faded`);
      }
      assert.equal(await page.getByRole('button', { name: '계속', exact: true }).evaluate(el => getComputedStyle(el).transform), 'none');
      await page.getByRole('button', { name: '계속', exact: true }).click();
      await page.getByText('식당 · 1/6', { exact: true }).waitFor();
      const records = page.getByRole('button', { name: '단서 기록 열기', exact: true });
      assert.ok((await records.innerText()).includes('단서 기록 열기'));
      assert.ok((await records.boundingBox()).height <= 48, 'records opener stays compact');
      if (width >= 640) {
        const dialoguePanel = page.getByRole('textbox', { name: '인물에게 질문' }).locator('xpath=../../..');
        assert.ok((await dialoguePanel.boundingBox()).height <= height / 2, 'desktop dialogue does not dominate the viewport');
      }
      assert.equal(await page.getByText('오늘 식판은 네가 먼저 가져가.', { exact: true }).count(), 1, 'initial scene dialogue appears once');
      await page.locator('summary').click();
      await page.getByRole('heading', { name: '플레이 안내' }).waitFor();
      await page.locator('summary').click();
      const input = page.getByRole('textbox', { name: '인물에게 질문' });
      await input.fill('오늘 보고했어?');
      await page.getByRole('button', { name: '말한다', exact: true }).click();
      const reply = page.getByText('오늘 아침 보고는 아직 하지 않았어.', { exact: true });
      await reply.waitFor();
      assert.equal(await input.isDisabled(), true);
      await page.getByRole('button', { name: '민석 · 이 장면 대화 완료' }).waitFor();
      const styles = await reply.evaluate(el => {
        const css = getComputedStyle(el);
        const ancestors = [];
        for (let node = el; node; node = node.parentElement) ancestors.push({ transform: getComputedStyle(node).transform, filter: getComputedStyle(node).filter });
        return { font: parseFloat(css.fontSize), line: parseFloat(css.lineHeight), ancestors };
      });
      assert.equal(styles.font, 16);
      assert.ok(styles.line >= 27);
      assert.ok(styles.ancestors.every(css => css.transform === 'none' && css.filter === 'none'), 'dialogue has no damaged ancestor');
      assert.equal(await page.locator('.damage-3').evaluateAll(elements => elements.every(el => el.tagName === 'IMG')), true);
      await page.getByRole('button', { name: '다음 장면', exact: true }).click();
      await page.getByRole('button', { name: '제안을 거절한다', exact: true }).click();
      await page.getByText('원숭이손의 제안을 거절했다.', { exact: true }).waitFor();
      await page.getByText('복도 · 2/6', { exact: true }).waitFor();
      await page.getByText('오늘 남은 대화 7회', { exact: true }).waitFor();
      await page.getByText('단서 기록에 새 내용을 저장했다.', { exact: true }).waitFor();
      assert.equal(await page.getByText('긴 기록 원문은 대화 로그에 다시 붙이지 않는다.').count(), 0);
      await input.fill('누가 나갔어?');
      assert.equal(await input.isDisabled(), false, 'new scene allows another question without refilling budget');
      await records.click();
      const note = page.getByText(observation.text, { exact: true });
      await note.waitFor();
      assert.equal(await note.evaluate(el => getComputedStyle(el).fontSize), '18px');
      await page.keyboard.press('Escape');
      assert.equal(talkCalls, 1, 'help, ambient dialogue, notebook and scene transition do not send a question');
      for (const element of [input, page.getByRole('button', { name: '말한다', exact: true }), page.getByRole('button', { name: '다음 장면', exact: true })]) {
        const bounds = await element.boundingBox();
        assert.ok(bounds.width >= 44 && bounds.height >= 44 && bounds.x >= 0 && bounds.x + bounds.width <= width, 'controls remain readable within viewport');
      }
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
      await page.close();
    }
    assert.deepEqual(errors, []);
    console.log('PASS gameplay tutorial, conversation limits, free actions, clear notices and image-only damage with four characters and two illustrations at 390/1440/1564px');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });

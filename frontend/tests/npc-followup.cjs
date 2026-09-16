// Mock API + real frontend. One headless browser, no game DB writes.
// NODE_PATH=/path/to/playwright/node_modules node frontend/tests/npc-followup.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');

const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
};

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const errors = [];
  const gates = [];
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    page.setDefaultTimeout(10000);
    page.on('pageerror', error => errors.push(error.message));
    const npcs = [
      { code: 'chaeyeon', name: '채연', mood: 'calm', uttered: false },
      { code: 'minseok', name: '민석', mood: 'calm', uttered: false },
    ];
    const requests = [];
    const accepted = new Map();
    const observations = [];
    let budget = 8;
    let beat = 1;
    let advanceCalls = 0;
    let pawCalls = 0;
    let utteranceArrived = deferred();
    let beatArrived = deferred();
    let pawArrived = deferred();
    let npcsArrived = deferred();
    const hold = async (signal, data) => {
      const gate = deferred();
      gates.push(gate);
      signal.resolve({ ...data, release: gate.resolve });
      return gate.promise;
    };
    const fulfill = (route, body, status = 200) => route.fulfill({ status, json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });

    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.port !== '8500') return route.continue();
      const path = url.pathname;
      if (path === '/sessions') return fulfill(route, {
        attempt_id: 'followup', attempt_n: 1, entry_lines: ['하루를 살핀다.', '다시 묻는다.', '밤에 쓴다.'], prior_cell_results: null,
      });
      if (path === '/sessions/followup/loops') return fulfill(route, {
        loop_id: 'loop-followup', loop_n: 1, morning_text: '아침이다.', damage_level: 0,
        budget_left: budget, beat, beat_title: '아침 배급', narration: '민석이 쟁반을 살핀다.',
        broadcast: null, ambient: null, illustrations: [], aftermath: null, active_rules: [], observations: [],
      });
      if (path.endsWith('/npcs')) {
        const snapshot = npcs.map(npc => ({ ...npc }));
        if (beat > 1) {
          const mode = await hold(npcsArrived, {});
          if (mode === 'service-failure') return fulfill(route, { detail: '인물 상태를 받지 못했다.' }, 503);
        }
        return fulfill(route, { npcs: snapshot });
      }
      if (path.endsWith('/observations')) return fulfill(route, { observations });
      if (path.endsWith('/utterances')) {
        const request = route.request().postDataJSON();
        requests.push(request);
        const mode = await hold(utteranceArrived, { request });
        if (mode === 'service-failure') return fulfill(route, { detail: '잠시 답을 받지 못했다.' }, 503);
        if (mode === 'conflict') return fulfill(route, { detail: '이 질문 요청이 다른 내용으로 이미 처리됐다.' }, 409);
        const id = request.request_id ?? `legacy-${requests.length}`;
        if (!accepted.has(id)) {
          budget--;
          const npc = npcs.find(npc => npc.code === request.target);
          npc.uttered = true;
          const reply = `${accepted.size + 1}번째 답: 먹은 양을 적어 두려고 봤어.`;
          const observation = {
            observation_id: `statement-${id}`, attempt_id: 'followup', loop_id: 'loop-followup', loop_n: 1,
            beat, scene_id: 'ration-line', scene_title: '아침 배급', actor: npc.name,
            text: `${npc.name}의 ${accepted.size + 1}번째 발언 기록`, source_kind: 'statement', verification: 'reported', illustrations: [], rule_id: null,
          };
          observations.push(observation);
          accepted.set(id, {
            utterance_id: id, reply, npc: { ...npc }, budget_left: budget,
            beat, tool_used: false, observations: [observation],
          });
        }
        if (mode === 'lost-response') return route.abort('failed');
        if (mode === 'legacy-response') {
          const { utterance_id, ...legacyResponse } = accepted.get(id);
          return fulfill(route, legacyResponse);
        }
        return fulfill(route, accepted.get(id));
      }
      if (path.endsWith('/beats/next')) {
        advanceCalls++;
        await hold(beatArrived, {});
        beat++;
        for (const npc of npcs) npc.uttered = false;
        return fulfill(route, {
          beat, beat_title: '침상 사이', narration: '같은 하루의 다음 장면이다.', broadcast: null,
          illustrations: [], paw_offer: beat === 2 ? { offer_id: 'paw-1', rule_label: '배급을 남긴다', shown_reason: null } : null,
          day_done: false, ambient: null, note_found: null, observations: [], budget_left: budget,
        });
      }
      if (path.endsWith('/paw/respond')) {
        pawCalls++;
        await hold(pawArrived, {});
        return fulfill(route, { applied: false, rule_label: null });
      }
      errors.push(`Unmocked API: ${path}`);
      return route.abort();
    });

    await page.goto(process.env.FRONTEND_URL ?? 'http://localhost:3500/play');
    await page.getByRole('button', { name: '시작', exact: true }).click();
    await page.getByRole('button', { name: '계속', exact: true }).click();
    const input = page.getByRole('textbox', { name: '인물에게 질문', exact: true });
    const send = page.getByRole('button', { name: '말한다', exact: true });
    const advance = page.getByRole('button', { name: '다음 장면', exact: true });
    const minseok = page.getByRole('button', { name: /^민석 ·/ });
    const chaeyeon = page.getByRole('button', { name: /^채연 ·/ });
    await minseok.click();
    const beginQuestion = async text => {
      utteranceArrived = deferred();
      await input.fill(text);
      await send.click();
      return utteranceArrived.promise;
    };
    const assertPendingLocks = async () => {
      assert.equal(await input.isDisabled(), true, 'pending question locks editing');
      assert.equal(await send.isDisabled(), true, 'pending question locks duplicate sends');
      assert.equal(await page.getByRole('button', { name: /^(다음 장면|…)$/, exact: true }).isDisabled(), true, 'pending mutation locks scene movement');
    };
    const question1 = await beginQuestion('왜 쟁반을 살폈어?');
    await assertPendingLocks();
    question1.release('success');
    await page.getByText('오늘 남은 대화 7회', { exact: true }).waitFor();
    assert.equal(await input.isDisabled(), true, 'a successful question locks the same NPC for this scene');
    assert.equal(await send.isDisabled(), true, 'the completed NPC cannot receive another question');
    assert.equal(await minseok.getAttribute('aria-pressed'), 'true', 'selected NPC stays selected');
    assert.equal(await minseok.getAttribute('aria-label'), '민석 · 이 장면 대화 완료');
    assert.match(await input.getAttribute('placeholder'), /다른 인물|다음 장면/);
    assert.match(await page.locator('#conversation-hint').innerText(), /다른 인물.*다음 장면/);
    await chaeyeon.click();
    assert.equal(await input.isEnabled(), true, 'another NPC is still available in the same scene');

    const question2 = await beginQuestion('누가 먹은 양을 적어?');
    await assertPendingLocks();
    question2.release('success');
    await page.getByText('오늘 남은 대화 6회', { exact: true }).waitFor();
    assert.equal(await chaeyeon.getAttribute('aria-pressed'), 'true');
    assert.equal(advanceCalls, 0, 'answers never automatically advance the scene');
    assert.equal(question1.request.target, 'minseok');
    assert.equal(question2.request.target, 'chaeyeon');
    const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    assert.match(question1.request.request_id, uuid);
    assert.match(question2.request.request_id, uuid);
    assert.notEqual(question1.request.request_id, question2.request.request_id);
    await page.getByRole('button', { name: '단서 기록 열기', exact: true }).getByText('2건', { exact: true }).waitFor();
    await page.getByRole('button', { name: '단서 기록 열기', exact: true }).click();
    const notebook = page.getByRole('dialog', { name: '단서 기록', exact: true });
    await notebook.getByText('민석의 1번째 발언 기록', { exact: true }).waitFor();
    await notebook.getByText('채연의 2번째 발언 기록', { exact: true }).waitFor();
    await notebook.getByRole('button', { name: '단서 기록 닫기', exact: true }).first().click();

    const beginAdvance = async () => {
      beatArrived = deferred();
      npcsArrived = deferred();
      await advance.click();
      const nextScene = await beatArrived.promise;
      await assertPendingLocks();
      const nextBeat = beat + 1;
      nextScene.release();
      await page.getByText(`침상 사이 · ${nextBeat}/6`, { exact: true }).waitFor();
      return npcsArrived.promise;
    };
    const nextNpcs = await beginAdvance();
    const accept = page.getByRole('button', { name: '받는다', exact: true });
    const decline = page.getByRole('button', { name: '제안을 거절한다', exact: true });
    await accept.waitFor();
    assert.equal(await advance.isDisabled(), true, 'open paw offer locks scene movement');
    pawArrived = deferred();
    await decline.evaluate(button => { button.click(); button.click(); });
    const paw = await pawArrived.promise;
    assert.equal(await accept.isDisabled(), true);
    assert.equal(await decline.isDisabled(), true);
    await assertPendingLocks();
    assert.equal(pawCalls, 1, 'double paw click sends once');
    paw.release();
    await decline.waitFor({ state: 'hidden' });
    assert.equal(await input.isDisabled(), true, 'scene change waits for fresh NPC flags');
    nextNpcs.release();
    await minseok.click();
    await input.fill('새 장면 질문 준비');
    assert.equal(await input.isEnabled(), true, 'same NPC unlocks on the next scene');
    await page.getByText('오늘 남은 대화 6회', { exact: true }).waitFor();

    const retryText = '기록한 뒤에는 어떻게 해?';
    const failed = await beginQuestion(retryText);
    failed.release('service-failure');
    const retry = page.getByRole('button', { name: '같은 질문 다시 보내기', exact: true });
    await retry.waitFor();
    await assertPendingLocks();
    await page.getByText('오늘 남은 대화 6회', { exact: true }).waitFor();
    const retryQuestion = async mode => {
      utteranceArrived = deferred();
      const before = requests.length;
      await retry.evaluate(button => { button.click(); button.click(); });
      const retried = await utteranceArrived.promise;
      await assertPendingLocks();
      assert.equal(requests.length, before + 1, 'double retry click sends once');
      assert.deepEqual(retried.request, failed.request, 'retry retains original ID, target and text');
      retried.release(mode);
    };
    await retryQuestion('lost-response');
    await retry.waitFor();
    await page.getByText('오늘 남은 대화 6회', { exact: true }).waitFor();
    await retryQuestion('success');
    await page.getByText('오늘 남은 대화 5회', { exact: true }).waitFor();
    assert.equal(await page.getByText(retryText, { exact: true }).count(), 1, 'retry keeps one submitted question');
    assert.equal(await page.getByText('3번째 답: 먹은 양을 적어 두려고 봤어.', { exact: true }).count(), 1, 'retry adds one accepted reply');
    await page.getByRole('button', { name: '단서 기록 열기', exact: true }).getByText('3건', { exact: true }).waitFor();

    assert.equal(await input.isDisabled(), true, 'an accepted retry completes this NPC for the scene');
    await chaeyeon.click();
    const conflicted = await beginQuestion('다른 내용의 질문');
    conflicted.release('conflict');
    await page.getByText('이 질문 요청이 다른 내용으로 이미 처리됐다.', { exact: true }).waitFor();
    assert.equal(await input.isEnabled(), true, 'terminal rejection allows correcting the question');
    assert.equal(await input.inputValue(), '다른 내용의 질문');
    assert.equal(await page.getByText('오늘 남은 대화 5회', { exact: true }).count(), 1);

    const unavailableNpcs = await beginAdvance();
    assert.equal(await input.isDisabled(), true, 'an unasked NPC from the old scene cannot bypass a pending refresh');
    assert.equal(await send.isDisabled(), true);
    const failedNpcResponse = page.waitForResponse(response => response.url().endsWith('/npcs') && response.status() === 503);
    unavailableNpcs.release('service-failure');
    await failedNpcResponse;
    assert.equal(await input.isDisabled(), true, 'failed refresh keeps stale NPC flags unavailable');
    assert.equal(await advance.isEnabled(), true, 'unavailable NPC flags still permit free scene movement');
    assert.equal(await page.getByRole('button', { name: '단서 기록 열기', exact: true }).isEnabled(), true);
    const refreshedNpcs = await beginAdvance();
    refreshedNpcs.release();
    await minseok.click();
    const repeatedText = await beginQuestion(retryText);
    assert.notEqual(repeatedText.request.request_id, failed.request.request_id, 'same text after success is a new question');
    repeatedText.release('success');
    await page.getByText('오늘 남은 대화 4회', { exact: true }).waitFor();

    await chaeyeon.click();
    const otherQuestion = await beginQuestion('이번 장면에서 본 건 뭐야?');
    otherQuestion.release('success');
    await page.getByText('오늘 남은 대화 3회', { exact: true }).waitFor();

    const fifthSceneNpcs = await beginAdvance();
    fifthSceneNpcs.release();
    for (const [npc, remaining] of [[minseok, 2], [chaeyeon, 1]]) {
      await npc.click();
      const question = await beginQuestion(`다음 장면 질문 ${remaining}`);
      question.release('legacy-response');
      await page.getByText(`오늘 남은 대화 ${remaining}회`, { exact: true }).waitFor();
      await page.getByText(`${8 - remaining}번째 답: 먹은 양을 적어 두려고 봤어.`, { exact: true }).waitFor();
      assert.equal(await input.isDisabled(), true, 'legacy response also completes the NPC for the scene');
    }
    const sixthSceneNpcs = await beginAdvance();
    sixthSceneNpcs.release();
    await minseok.click();
    const lastQuestion = await beginQuestion('마지막 장면에서 본 건 뭐야?');
    lastQuestion.release('legacy-response');
    await page.getByText('오늘 남은 대화 0회', { exact: true }).waitFor();
    assert.equal(await input.isDisabled(), true, 'zero budget locks input');
    assert.equal(await send.isDisabled(), true, 'zero budget locks send');
    assert.equal(await advance.isEnabled(), true, 'zero budget still permits free scene movement');
    assert.equal(await page.getByRole('button', { name: '단서 기록 열기', exact: true }).isEnabled(), true);
    assert.equal(advanceCalls, 5, 'only the explicit advances moved the scene');
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ checks: ['one successful question per NPC per scene', 'another NPC remains available', 'next scene unlocks', 'pending and failed NPC refresh locks', '8 → 7 → 6 budget', 'separate observations', 'selection retained', 'no auto advance', '503 and lost-response retry ID', 'one accepted chat entry per request', 'terminal rejection correction', 'pending mutation locks', 'legacy response IDs', 'zero budget'], requests: requests.length }, null, 2));
  } finally {
    for (const gate of gates) gate.resolve();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

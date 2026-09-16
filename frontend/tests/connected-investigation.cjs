// Mock API + real frontend. This test never writes player records.
// NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/connected-investigation.cjs
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const out = process.env.TEST_ARTIFACT_DIR || '/tmp/pigfarm-connected-frontend';
fs.mkdirSync(out, { recursive: true });

const seenIllustration = { image_id: 'clue-11', caption: '준이 소매 끝의 번호가 있는 띠를 살핀다.' };
const earlierIllustration = { image_id: 'clue-08', caption: '민석이 채연의 쟁반을 살피며 수첩에 기록한다.' };
const observations = [
  {
    observation_id: 'obs-earlier', attempt_id: 'connected', loop_id: 'loop-1', loop_n: 1,
    beat: 1, scene_id: 'ration-line', scene_title: '아침 배급', actor: '민석',
    text: '민석이 남은 쟁반을 기록했다.', source_kind: 'image', verification: 'observed',
    illustrations: [earlierIllustration], rule_id: null,
  },
  {
    observation_id: 'obs-middle', attempt_id: 'connected', loop_id: 'loop-2', loop_n: 2,
    beat: 1, scene_id: 'ration-line', scene_title: '저녁 배급', actor: null,
    text: '관리자 방송 뒤에 배급 줄이 움직였다.', source_kind: 'scene', verification: 'observed',
    illustrations: [], rule_id: null,
  },
  {
    observation_id: 'obs-current', attempt_id: 'connected', loop_id: 'loop-3', loop_n: 3,
    beat: 2, scene_id: 'jun-band', scene_title: '침상 사이', actor: '준',
    text: '준이 소매 끝의 번호가 있는 띠를 살폈다.', source_kind: 'image', verification: 'observed',
    illustrations: [seenIllustration], rule_id: null,
  },
  {
    observation_id: 'obs-statement', attempt_id: 'connected', loop_id: 'loop-3', loop_n: 3,
    beat: 6, scene_id: 'rumor', scene_title: '소문', actor: '은상',
    text: '은상이 "트럭이 온다"고 말했다.', source_kind: 'statement', verification: 'reported',
    illustrations: [], rule_id: null,
  },
];

const metric = (numerator, denominator, value, reviewed, method) => ({ numerator, denominator, value, reviewed, method });

(async () => {
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true });
  const report = { mode: 'mock API, real frontend; no game DB writes', checks: [], errors: [] };
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    page.on('pageerror', error => report.errors.push(error.message));
    let draftBody = null;
    let previewCalls = 0;
    let ruleCalls = 0;
    let questionCalls = 0;
    let previousCalls = 0;
    let optionCalls = 0;
    const reads = { notes: 0, observations: 0 };
    const previousWriting = '  민석은 왜 기록할까?\n\n배급과 관련이 있는 것 같다.  ';

    await page.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.port !== '8500') return route.continue();
      const path = url.pathname;
      if (path.endsWith('/notes')) reads.notes++;
      if (path.endsWith('/observations')) reads.observations++;
      const requestBody = route.request().postDataJSON?.();
      let body;
      if (path === '/sessions') body = { attempt_id: 'connected', attempt_n: 1, entry_lines: ['세계가 이상하다.', '오늘이 지나면 멸망한다.', '다섯 번 관찰한다.'], prior_cell_results: null };
      else if (path === '/sessions/connected/loops') body = {
        loop_id: 'loop-3', loop_n: 3, morning_text: '7시 12분. 눈을 뜬다.', damage_level: 0,
        budget_left: 5, beat: 6, beat_title: '침상 사이', narration: '준이 소매를 살핀다.', broadcast: null,
        illustrations: [seenIllustration], aftermath: null, active_rules: [], observations: [observations[2]],
      };
      else if (path === '/loops/loop-3/npcs') body = { npcs: [
        { code: 'chaeyeon', name: '채연', mood: 'wary', uttered: false },
        { code: 'minseok', name: '민석', mood: 'uneasy', uttered: false },
        { code: 'eunsang', name: '은상', mood: 'calm', uttered: false },
        { code: 'jun', name: '준', mood: 'wary', uttered: false },
      ] };
      else if (path === '/loops/loop-3/observations') body = { observations };
      else if (path === '/loops/loop-3/beats/next') body = {
        beat: 6, beat_title: '저녁 배급', narration: '소등 시간이 왔다.', broadcast: null,
        illustrations: [seenIllustration], paw_offer: null, day_done: true, ambient: null, note_found: null,
        observations: [observations[2], observations[3]], budget_left: 4,
      };
      else if (path === '/loops/loop-3/notes') body = { notes: [
        { id: 1, kind: 'fragment', text: '민석이 남은 쟁반을 기록했다.', loop_n: 1, observation_ids: ['obs-earlier'], sources: [observations[0]] },
        { id: 2, kind: 'confirmed', text: '관리자 방송 뒤에 배급 줄이 움직였다.', loop_n: 2, observation_ids: ['obs-middle'], sources: [observations[1]] },
        { id: 3, kind: 'fragment', text: '준이 소매 끝의 번호가 있는 띠를 살폈다.', loop_n: 3, observation_ids: ['obs-current'], sources: [observations[2]] },
      ] };
      else if (path === '/loops/loop-3/night/previous') {
        previousCalls++;
        if (previousCalls === 1) {
          await new Promise(resolve => setTimeout(resolve, 300));
          return route.fulfill({ status: 503, json: { detail: '이전 초안을 잠시 불러오지 못했다.' }, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
        }
        body = { previous_answer: {
          loop_n: 2, free_text: previousWriting, claims: ['처음 주장'], tapped_note_ids: [1, 2],
          draft_text: previousWriting,
        } };
      }
      else if (path === '/loops/loop-3/night/draft') {
        draftBody = requestBody;
        body = { night_id: 'night-2', claims: ['민석은 남은 쟁반을 기록했다.', '관리자 방송이 배급을 통제한다.'] };
      }
      else if (path === '/nights/night-2/claims') body = { claims: requestBody.claims };
      else if (path === '/nights/night-2/submit') body = {
        total: 48, passed: false, loop_n: 2, world_outcome: 'truck', is_final: false, closed_by: null,
        cells: null, cookie: null, intervention_available: true, ending_lines: null,
        cell_feedback: '관찰과 보고의 연결을 더 확인할 수 있다.', wrong_claim_count: 0,
        night_clue: { loop_n: 2, caption: '트럭 소리.', image_ids: ['P02', 'clue-05'], voice_id: 'MA09', broadcast: '정리 작업이 있겠습니다. 비어 있는 자리는 아침에 정돈됩니다.', outcome_line: null },
      };
      else if (path === '/nights/night-2/questions') {
        questionCalls++;
        body = questionCalls === 1 ? {
          answer: '그건 알 수 없다. 아직 트럭이 도착한 장면은 보지 못했어. 다음 이송 방송이나 출입구를 살펴봐.', verdict: '그건 알 수 없다.', detail: '현재 기록에는 트럭의 도착 여부가 없다.', remaining: 2,
          status: 'unknown', evidence_ids: [], evidence: [], next_observation: '다음 이송 방송과 출입구를 확인한다.',
          unlocked_note: null,
        } : questionCalls === 2 ? {
          answer: '맞다. 기록은 이렇다', verdict: '맞다.', detail: '은상이 그렇게 말했다는 사실만 기록됐다.', remaining: 1,
          status: 'supported', evidence_ids: ['obs-statement'], evidence: [observations[3]], next_observation: null,
        } : {
          answer: '아니다. 틀리다', verdict: '아니다.', detail: '기록된 이동 시각과 질문의 시각이 다르다.', remaining: 0,
          status: 'contradicted', evidence_ids: ['obs-current'], evidence: [observations[2]], next_observation: null,
        };
      }
      else if (path === '/nights/night-2/options') {
        optionCalls++;
        body = { options: optionCalls === 1 ? [] : [
        { index: 1, label: '은상이 출처를 밝힌다', target: '은상', action: '알고 있는 출처를 함께 말한다', effect: 'enforce', when_beat: 'any', reason: '들은 말과 사실을 구분하기 위해', evidence_ids: ['obs-statement'], expected_observation: '다음 소문 장면에서 출처를 말하는지 본다.' },
        { index: 2, label: '민석이 기록 대상을 설명한다', target: '민석', action: '기록 대상을 설명한다', effect: 'enforce', when_beat: 1, reason: '쟁반 기록의 목적을 확인하기 위해', evidence_ids: ['obs-earlier'], expected_observation: '다음 배급에서 기록 설명을 듣는다.' },
        ] };
      }
      else if (path === '/nights/night-2/rule/preview') {
        previewCalls++;
        body = { preview_id: 'preview-1', original_text: requestBody.custom_text, executable: true,
          interpretation: '은상은 소문을 전할 때 알고 있는 출처를 함께 말한다.', limitations: ['은상이 모르는 진실은 만들지 않는다.'],
          alternatives: ['은상이 모르는 경우 모른다고 말한다.'], conflicts: ['같은 장면의 침묵 규칙과 함께 성립하지 않는다.'],
          rule: { target: '은상', action: '알고 있는 출처를 함께 말한다', effect: 'enforce', when_beat: 'any', label: '은상이 출처를 밝힌다' } };
      }
      else if (path === '/nights/night-2/rule') {
        ruleCalls++;
        assert.equal(requestBody.preview_id, 'preview-1');
        assert.equal(requestBody.custom_text, '  은상은 소문의 출처를 말한다  ');
        body = { ok: true, rule_label: '은상이 출처를 밝힌다', conflicts: [], reason: null };
      }
      else if (path === '/attempts/connected/harness') body = {
        rules: [{ rule_id: 'rule-1', source: 'user_custom', target: '은상', when_beat: null, effect: 'enforce', action: '알고 있는 출처를 함께 말한다', shown_reason: null, hidden_side_effect: null, created_loop: 2, conflict: false }],
        experiments: [{ rule_id: 'rule-1', intent: '소문이 부풀려지는지 확인한다.', interpretation: '은상이 소문을 전할 때 알고 있는 출처를 함께 말한다.', opportunities: [
          { loop_n: 3, beat: 2, condition: '은상이 소문을 전함', actual_action: '출처를 함께 말했다.', result: 'obeyed', observation_ids: ['obs-statement'], side_effect: null },
          { loop_n: 4, beat: 2, condition: '은상이 자리에 없음', actual_action: null, result: 'not_evaluable', observation_ids: [], side_effect: null },
        ] }],
        metrics: {
          note_source_linkage: metric(2, 2, 1, 2, 'public observation IDs'),
          rule_compliance: metric(1, 1, 1, 1, 'evaluable opportunities'),
          question_grounding: metric(1, 2, 0.5, 2, 'human review'),
          recommendation_relevance: metric(null, 0, null, 0, 'not independently reviewed'),
          custom_semantics: metric(null, 0, null, 0, 'not independently reviewed'),
          checker_accuracy: metric(null, 0, null, 0, 'not independently reviewed'),
        },
        harness_summary: { total_events: 20, harness_interventions: 1, fallbacks: 1, paw_accepted: 0,
          recommended_rules: 0, custom_rules: 1, rule_conflicts: 0, questions_asked: 2,
          rule_success_rate: 1, tool_side_effects: [], model_calls: 8, model_attempts: 9, model_call_coverage: 'complete_logged_calls' },
        measurement_version: 'connected-v1',
      };
      else { report.errors.push(`Unmocked API: ${path}`); return route.abort(); }
      if (path === '/loops/loop-3/night/previous') await new Promise(resolve => setTimeout(resolve, 900));
      await route.fulfill({ json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
    });

    await page.goto('http://localhost:3500/play');
    await page.getByRole('button', { name: '시작', exact: true }).click();
    await page.getByRole('button', { name: '계속', exact: true }).click();

    const notebookOpener = page.getByRole('button', { name: '단서 기록 열기', exact: true });
    await notebookOpener.click();
    const dayNotebook = page.getByRole('dialog', { name: '단서 기록' });
    await page.getByText('본 행동과 들은 말을 다시 살펴보고, 밤의 추리에 단서로 사용한다.').waitFor();
    await page.getByText('발언을 들음', { exact: true }).waitFor();
    await page.getByText('3회차 · 소문', { exact: true }).waitFor();
    assert.equal(await page.locator('img[src*="clue-12"]').count(), 0, 'unseen branch art stays hidden');
    const daySourceOpener = dayNotebook.getByRole('button', { name: '아침 배급 원본 장면 열기' });
    await daySourceOpener.click();
    const daySourceDetail = page.getByRole('dialog', { name: '아침 배급 원본 장면' });
    assert.equal(await page.getByRole('button', { name: '원본 장면 닫기', exact: true }).evaluate(element => element === document.activeElement), true, 'source detail receives focus');
    await page.keyboard.press('Tab');
    assert.equal(await daySourceDetail.evaluate((element) => element.contains(document.activeElement)), true, 'source detail traps focus');
    await page.keyboard.press('Escape');
    await daySourceDetail.waitFor({ state: 'hidden' });
    assert.equal(await daySourceOpener.evaluate(element => element === document.activeElement), true, 'source detail restores its opener');
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab');
      assert.equal(await page.evaluate(() => document.querySelector('[role="dialog"][aria-label="단서 기록"]')?.contains(document.activeElement)), true, 'notebook traps focus');
    }
    await page.keyboard.press('Escape');
    await dayNotebook.waitFor({ state: 'hidden' });
    await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label') === '단서 기록 열기');
    assert.equal(await notebookOpener.evaluate(element => element === document.activeElement), true, 'notebook restores opener focus');
    await page.getByText('오늘 남은 대화 5회', { exact: true }).waitFor();
    for (const [name, src] of [['채연', 'E01'], ['민석', 'E04'], ['은상', 'E07'], ['준', 'E10']]) {
      const portrait = page.getByRole('button', { name: new RegExp(name) }).locator('img');
      assert.ok((await portrait.getAttribute('src')).includes(src), `${name} uses stable portrait`);
    }
    for (const control of [page.locator('input[placeholder$="에게 말한다"]'), page.getByRole('button', { name: '말한다', exact: true }), page.getByRole('button', { name: '다음 장면', exact: true })]) {
      const bounds = await control.boundingBox();
      assert.ok(bounds && bounds.x >= 0 && bounds.x + bounds.width <= 390, 'day chat control remains inside 390px viewport');
    }
    report.checks.push('day notebook is free, sourced, seen-only; portraits are stable');

    await page.getByRole('button', { name: '다음 장면', exact: true }).click();
    await page.getByText('오늘 남은 대화 4회', { exact: true }).waitFor();
    const beforeNightReads = { ...reads };
    await page.getByRole('button', { name: '밤이 온다', exact: true }).click();
    const draft = page.getByPlaceholder('자유롭게 쓴다…');
    assert.equal(await draft.isDisabled(), true, 'draft stays locked while previous answer is unresolved');
    await page.getByText('이전 초안을 잠시 불러오지 못했다.', { exact: true }).waitFor();
    await page.getByRole('button', { name: '재시도', exact: true }).click();
    assert.equal(await draft.isDisabled(), true, 'draft remains locked during previous-answer retry');
    await page.getByText('지난 회차에서 이어 쓴 초안', { exact: true }).waitFor();
    assert.equal(await draft.isEnabled(), true, 'draft unlocks after previous answer and evidence settle');
    assert.equal(await draft.inputValue(), previousWriting);
    assert.deepEqual(reads, beforeNightReads, 'night does not eagerly fetch notes or images');
    const bounds = await draft.boundingBox();
    assert.ok(bounds && bounds.y + bounds.height < 844, 'writing is visible before the record collection');
    assert.equal(await page.getByRole('button', { name: /민석이 남은 쟁반을 기록했다/ }).count(), 0);
    await page.screenshot({ path: `${out}/night-writing-mobile.png`, fullPage: true });
    await page.getByRole('button', { name: /관찰 기록에서 근거 고르기/ }).click();
    const oldEvidence = page.getByRole('button', { name: /민석이 남은 쟁반을 기록했다/ });
    await oldEvidence.click();
    await oldEvidence.click();
    await page.getByRole('button', { name: /준이 소매 끝의 번호가 있는 띠를 살폈다/ }).click();
    await page.getByRole('button', { name: '근거 그림 모아보기', exact: true }).click();
    const gallery = page.getByRole('dialog', { name: '이미 본 근거 그림' });
    await page.getByText('1회차 · 아침 배급', { exact: true }).waitFor();
    await page.getByText('3회차 · 침상 사이', { exact: true }).waitFor();
    for (const filename of ['clue-08-minseok-tray-record-v1.png', 'clue-11-jun-band-observation-v1.png']) {
      const image = gallery.locator(`img[src$="${filename}"]`).first();
      await image.waitFor({ state: 'visible' });
      // 4MB 삽화는 '보임'과 디코딩 완료 사이에 틈이 있다 — 로드 완료를 기다린 뒤 원본 크기를 검사한다.
      await image.evaluate(element => element.complete && element.naturalWidth > 0 ? undefined : new Promise((resolve, reject) => { element.addEventListener('load', resolve, { once: true }); element.addEventListener('error', () => reject(new Error(`image failed: ${element.src}`)), { once: true }); }));
      assert.equal(await image.evaluate(element => element.complete && element.naturalWidth === 1536 && element.naturalHeight === 1024), true, `${filename} opens at its valid source dimensions`);
      const bounds = await image.boundingBox();
      assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= 390, `${filename} stays readable inside 390px gallery`);
    }
    const compareChecks = gallery.locator('input[type="checkbox"]');
    await compareChecks.nth(1).check();
    await compareChecks.nth(0).check();
    await gallery.getByText('1. 1회차 · 아침 배급', { exact: true }).waitFor();
    await gallery.getByText('2. 3회차 · 침상 사이', { exact: true }).waitFor();
    assert.equal(await page.locator('img[src*="clue-12"]').count(), 0);
    const gallerySourceOpener = gallery.getByRole('button', { name: '아침 배급 원본 장면 열기' });
    await gallerySourceOpener.click();
    const galleryDetail = page.getByRole('dialog', { name: '아침 배급 원본 그림' });
    assert.equal(await galleryDetail.getByRole('button', { name: '원본 그림 닫기', exact: true }).evaluate(element => element === document.activeElement), true, 'gallery detail receives focus');
    await page.keyboard.press('Escape');
    await galleryDetail.waitFor({ state: 'hidden' });
    assert.equal(await gallerySourceOpener.evaluate(element => element === document.activeElement), true, 'gallery detail restores its opener');
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press('Tab');
      assert.equal(await gallery.evaluate((element) => element.contains(document.activeElement)), true, 'gallery traps focus');
    }
    await page.keyboard.press('Escape');
    await gallery.waitFor({ state: 'hidden' });
    await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label') === '근거 그림 모아보기');
    assert.equal(await page.getByRole('button', { name: '근거 그림 모아보기', exact: true }).evaluate(element => element === document.activeElement), true, 'gallery restores its opener');
    await page.getByRole('button', { name: '이렇게 이해했다', exact: true }).click();
    assert.deepEqual([...draftBody.inherited_note_ids].sort((a, b) => a - b), [1, 2]);
    assert.deepEqual([...draftBody.tapped_note_ids].sort((a, b) => a - b), [1, 2, 3]);
    assert.equal(draftBody.free_text, previousWriting);
    await page.getByRole('button', { name: '아니, 고친다 (1회)', exact: true }).click();
    await page.locator('textarea').fill('확인 화면에서 고친 최종 가설');
    await page.getByRole('button', { name: '이렇게 고친다', exact: true }).click();
    await page.getByText('확인 화면에서 고친 최종 가설', { exact: true }).waitFor();
    await page.getByRole('button', { name: '맞아, 제출한다', exact: true }).click();
    await page.getByRole('button', { name: '계속', exact: true }).click();
    // 밤 단서 시퀀스 — 문장이 남은 뒤 탭해서 신의개입으로 (자동 진행 없음)
    await page.getByText('트럭 소리.', { exact: true }).waitFor();
    await page.getByRole('button', { name: '계속', exact: true }).click();

    await page.getByText('이 목소리는 오늘 일어난 일만 안다. 무엇을 했는지 물어라.', { exact: true }).waitFor();
    assert.equal(await page.getByText('새 단서 — 노트에 적혔다').count(), 0);

    const questionInput = page.locator('input[placeholder^="예:"]');
    assert.match(await questionInput.getAttribute('placeholder'), /확인 화면에서 고친 최종 가설/, 'question example uses confirmed final claim');
    await questionInput.fill('트럭이 왔어?');
    await page.getByRole('button', { name: '묻는다', exact: true }).click();
    await page.getByText('그건 알 수 없다. 아직 트럭이 도착한 장면은 보지 못했어. 다음 이송 방송이나 출입구를 살펴봐.', { exact: true }).waitFor();
    assert.equal(await page.getByText('아직 확인되지 않았다', { exact: true }).isVisible(), false);
    await page.getByText('그건 알 수 없다. 아직 트럭이 도착한 장면은 보지 못했어. 다음 이송 방송이나 출입구를 살펴봐.', { exact: true })
      .evaluate(element => Promise.all(element.parentElement.getAnimations().map(animation => animation.finished)));
    await page.screenshot({ path: `${out}/god-reply-mobile.png`, fullPage: true });
    await page.locator('summary').nth(0).click();
    await page.getByText('아직 확인되지 않았다', { exact: true }).waitFor();
    await page.getByText('다음 이송 방송과 출입구를 확인한다.').waitFor();
    await page.locator('input[placeholder^="예:"]').fill('은상이 트럭이 온다고 말했어?');
    await page.getByRole('button', { name: '묻는다', exact: true }).click();
    await page.getByText('맞다. 기록은 이렇다', { exact: true }).waitFor();
    await page.locator('summary').nth(1).click();
    await page.getByText('근거와 일치한다', { exact: true }).waitFor();
    await page.getByText('발언을 들음', { exact: true }).waitFor();
    await page.locator('input[placeholder^="예:"]').fill('준이 첫 장면에 있었어?');
    await page.getByRole('button', { name: '묻는다', exact: true }).click();
    await page.getByText('아니다. 틀리다', { exact: true }).waitFor();
    await page.locator('summary').nth(2).click();
    await page.getByText('기록과 모순된다', { exact: true }).waitFor();
    await page.getByRole('button', { name: '규칙을 고른다', exact: true }).click();
    await page.getByText('현재 근거에 맞는 실행 가능한 추천이 없다.', { exact: false }).waitFor();
    await page.getByRole('button', { name: '후보 다시 확인', exact: true }).click();
    await page.getByText('들은 말과 사실을 구분하기 위해').waitFor();
    await page.getByText('다음 소문 장면에서 출처를 말하는지 본다.').waitFor();
    const custom = page.getByPlaceholder('직접 쓴다…');
    await custom.fill('  은상은 소문의 출처를 말한다  ');
    await page.getByRole('button', { name: '해석 미리보기', exact: true }).click();
    assert.equal(ruleCalls, 0, 'preview does not apply');
    await page.getByText('은상은 소문을 전할 때 알고 있는 출처를 함께 말한다.').waitFor();
    await page.getByText('은상이 모르는 진실은 만들지 않는다.').waitFor();
    await page.getByText('같은 장면의 침묵 규칙과 함께 성립하지 않는다.').waitFor();
    await page.getByRole('button', { name: '이 해석으로 적용', exact: true }).click();
    assert.equal(previewCalls, 1);
    assert.equal(ruleCalls, 1);
    report.checks.push('previous draft/evidence preserved; grounded Q&A and explicit rule preview/apply');
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: `${out}/connected-mobile.png`, fullPage: true });
    await page.close();

    const retro = await browser.newPage({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
    retro.on('pageerror', error => report.errors.push(error.message));
    await retro.route('**/*', async route => {
      const url = new URL(route.request().url());
      if (url.port !== '8500') return route.continue();
      if (url.pathname === '/attempts/connected/journey') {
        return route.fulfill({ json: {
          loops: [
            { loop_n: 3, total: 40, passed: false, new_confirmed: [{ code: 'cause-1', my_claim: '은상이 소문을 부풀렸다.' }], unlocked_notes: [] },
            { loop_n: 5, total: 60, passed: true, new_confirmed: [], unlocked_notes: ['트럭은 실어 갈 뿐이다.'] },
          ],
          final: { cells: { cause: 100, motive: 0, side_effect: 0, identity: 0 }, closed_by: 'doom', truth_reveal: [
            { code: 'cause-1', cell: 'cause', verdict: 'confirmed', my_claim: '은상이 소문을 부풀렸다.', truth: '소문은 부풀려져 퍼졌다.' },
            { code: 'identity-1', cell: 'identity', verdict: 'none', my_claim: null, truth: null },
          ] },
          unresolved: [{ cell: 'identity', hint: '내일 준에게 트럭 소리를 물어봐.' }],
        }, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
      }
      if (url.pathname !== '/attempts/connected/harness') return route.abort();
      const body = {
        rules: [],
        experiments: [{ rule_id: 'rule-1', intent: '소문이 부풀려지는지 확인한다.', interpretation: '은상이 알고 있는 출처를 함께 말한다.', opportunities: [
          { loop_n: 3, beat: 2, condition: '은상이 소문을 전함', actual_action: '출처를 함께 말했다.', result: 'obeyed', observation_ids: ['obs-statement'], side_effect: null },
          { loop_n: 4, beat: 2, condition: '은상이 자리에 없음', actual_action: null, result: 'not_evaluable', observation_ids: [], side_effect: null },
        ] }],
        metrics: { note_source_linkage: metric(2,2,1,2,'public observation IDs'), rule_compliance: metric(1,1,1,1,'evaluable opportunities'), question_grounding: metric(1,2,.5,2,'human review'), recommendation_relevance: metric(null,0,null,0,'not reviewed'), custom_semantics: metric(null,0,null,0,'not reviewed'), checker_accuracy: metric(null,0,null,0,'not reviewed') },
        harness_summary: { total_events: 20, harness_interventions: 1, fallbacks: 1, paw_accepted: 0, recommended_rules: 0, custom_rules: 1, rule_conflicts: 0, questions_asked: 2, rule_success_rate: 1, tool_side_effects: [], model_calls: 8, model_attempts: 9, model_call_coverage: 'complete_logged_calls' },
        measurement_version: 'connected-v1',
      };
      await route.fulfill({ json: body, headers: { 'access-control-allow-origin': 'http://localhost:3500', 'access-control-allow-credentials': 'true' } });
    });
    await retro.goto('http://localhost:3500/harness/connected');
    await retro.getByRole('heading', { name: '너의 추리는 이렇게 걸어왔다.' }).waitFor();
    await retro.getByText('이 밤, 하나가 확정됐다 — 은상이 소문을 부풀렸다.', { exact: false }).waitFor();
    await retro.getByText('신이 연 단서 — 트럭은 실어 갈 뿐이다.', { exact: false }).waitFor();
    await retro.getByText('소문은 부풀려져 퍼졌다.', { exact: false }).waitFor();
    assert.equal(await retro.getByText('이들은 동물이다', { exact: false }).count(), 0, 'locked truth stays hidden');
    await retro.getByText('아직 비어 있는 자리', { exact: true }).waitFor();
    await retro.getByText('개발 데이터 — 규칙·검사·모델 동작이 궁금하다면', { exact: false }).click();
    for (const text of ['의도', '해석', '기회', '실제 행동', '검사 결과', '지킴', '평가할 수 없음', '시스템 동작 품질', 'N/A']) {
      await retro.getByText(text, { exact: false }).first().waitFor();
    }
    await retro.getByText('모델 호출 8회 · 시도 9회 · 개입 1회 · 대체 1회', { exact: true }).waitFor();
    assert.equal(await retro.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await retro.screenshot({ path: `${out}/retrospective-mobile.png`, fullPage: true });
    report.checks.push('retrospective shows real experiment chain and honest metric N/A');
    await retro.close();
    assert.deepEqual(report.errors, []);
  } finally {
    fs.writeFileSync(`${out}/results.json`, JSON.stringify(report, null, 2));
    console.log(JSON.stringify(report, null, 2));
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });

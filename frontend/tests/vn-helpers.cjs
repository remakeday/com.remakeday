const assert = require('node:assert/strict');

// Keep fake responses explicit about line kind and server ordering.
const line = (kind, text, fields = {}) => ({
  kind, speaker: null, text, image_id: null, voice_id: null, observation_id: null, ...fields,
});

async function readAll(page) {
  // 원숭이손 팝업이 열려 aria-hidden이 된 대사창도 찾는다.
  const box = page.locator('[aria-label="대사창"]');
  await box.waitFor();
  // 모두 보기 버튼 대신 대화창 탭·스페이스로 타이핑을 건너뛴다.
  if ((await box.getAttribute('data-typing')) === 'true') {
    await box.click();
  }
  await page.waitForFunction(() => {
    const region = document.querySelector('[aria-label="대사창"]');
    return region instanceof HTMLElement && region.getAttribute('data-typing') === 'false';
  });
}

async function expectBudget(page, remaining) {
  await page.locator(`[role="meter"][aria-label="남은 대화 횟수"][aria-valuenow="${remaining}"]`).waitFor();
  assert.equal(await page.getByRole('meter', { name: '남은 대화 횟수', exact: true }).getAttribute('aria-valuenow'), String(remaining));
}

module.exports = { line, readAll, expectBudget };

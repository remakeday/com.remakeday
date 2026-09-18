const assert = require('node:assert/strict');

// Keep fake responses explicit about line kind and server ordering.
const line = (kind, text, fields = {}) => ({
  kind, speaker: null, text, image_id: null, voice_id: null, observation_id: null, ...fields,
});

async function readAll(page) {
  const button = page.getByRole('button', { name: '모두 보기', exact: true });
  await button.waitFor();
  const counter = page.getByRole('region', { name: '대사창', exact: true })
    .locator('span').filter({ hasText: /^\d+ \/ \d+$/ });
  const [current, total] = (await counter.innerText()).split(' / ').map(Number);
  // A mutation may still be finishing: click waits for enabled instead of silently skipping it.
  if (current < total) await button.click();
}

async function expectBudget(page, remaining) {
  await page.locator(`[role="meter"][aria-label="남은 대화 횟수"][aria-valuenow="${remaining}"]`).waitFor();
  assert.equal(await page.getByRole('meter', { name: '남은 대화 횟수', exact: true }).getAttribute('aria-valuenow'), String(remaining));
}

module.exports = { line, readAll, expectBudget };

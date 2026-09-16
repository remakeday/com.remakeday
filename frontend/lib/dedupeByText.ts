/** 회차가 달라도 같은 문장인 기록은 먼저 나온 회차 것만 남긴다(테스터6 F6). 화면 표시 전용 — 남긴 기록의 id를 그대로 쓴다. */
const normalize = (text: string) => text.normalize("NFC").trim().replace(/\s+/g, " ");

export function dedupeByText<T extends { text: string; loop_n: number }>(
  items: T[],
  key: (item: T) => string = (item) => item.text,
): T[] {
  const seen = new Set<string>();
  const kept = new Set<T>();
  for (const item of [...items].sort((a, b) => a.loop_n - b.loop_n)) {
    const k = normalize(key(item));
    if (seen.has(k)) continue;
    seen.add(k);
    kept.add(item);
  }
  return items.filter((item) => kept.has(item));
}

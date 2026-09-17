/** 관찰 ID(`{회차 uuid}:action-3-준-손목띠를 만진다` 등)를 사람이 읽는 라벨로 바꾼다(테스터9 F25). uuid·규칙 ID는 표시하지 않는다. */
const KINDS: { pattern: RegExp; label: (m: RegExpMatchArray) => string }[] = [
  { pattern: /^action-(\d+)-([^-]+)-(.+)$/, label: (m) => `장면 ${m[1]} · ${m[2]}의 행동: ${m[3]}` },
  { pattern: /^rule-(\d+)-/, label: (m) => `장면 ${m[1]} · 규칙으로 드러난 말` },
  { pattern: /^paw-(?:effect|cost)-(\d+)-/, label: (m) => `장면 ${m[1]} · 원숭이손의 대가` },
];

export function observationLabel(observationId: string): string {
  const key = observationId.slice(observationId.indexOf(":") + 1);
  for (const kind of KINDS) {
    const m = key.match(kind.pattern);
    if (m) return kind.label(m);
  }
  return "기타 관찰 기록";
}

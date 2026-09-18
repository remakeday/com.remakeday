/** 서버 음성 ID 또는 녹음 대본과 같은 발화로 재생한다. 주제·회차로 대사를 추측하지 않는다. */
export const VOICE_CLIPS = {
  CH01: { speaker: "채연", text: "배 안 고파. 너 먹어." },
  CH02: { speaker: "채연", text: "오늘도… 다 확인해?" },
  CH03: { speaker: "채연", text: "말하면… 데려가잖아." },
  CH04: { speaker: "채연", text: "괜찮다니까. 그냥 좀 추워." },
  MI01: { speaker: "민석", text: "남기면 물어봐. 어디 아프냐고." },
  MI02: { speaker: "민석", text: "오늘 검진은 끝났어." },
  MI03: { speaker: "민석", text: "말해야 돼. 옆자리도 그러면 어떡해." },
  MI04: { speaker: "민석", text: "너 또 안 먹잖아." },
  MI05: { speaker: "민석", text: "이상한 건 알리랬잖아." },
  EU01: { speaker: "은상", text: "충식이 어제 이송됐대. 아직 안 돌아왔어." },
  EU02: { speaker: "은상", text: "준도 남겼네. 나도… 잘 안 넘어가." },
  EU03: { speaker: "은상", text: "준에게 들었어. 나는 직접 본 게 아니야." },
  EU04: { speaker: "은상", text: "혼자 깨어 있으면 무서워. 조금만 같이 있어 줘." },
  JU01: { speaker: "준", text: "이 숫자 뭔지 알아? 이름도 있는데." },
  JU02: { speaker: "준", text: "저 문은 늘 저쪽에서 열어줘." },
  JU03: { speaker: "준", text: "귀표… 그게 이거 말하는 건가?" },
  JU04: { speaker: "준", text: "이거 네 거잖아. 안 먹어?" },
  JU05: { speaker: "준", text: "민석아, 이 숫자 뭔지 알아?" },
  MA01: { speaker: "관리자", text: "배급을 시작합니다. 식사 후에는 각자 자리에서 대기해 주십시오." },
  MA02: { speaker: "관리자", text: "오후 검진을 시작합니다. 상태가 좋지 않은 분은 별도 구역으로 이송합니다." },
  MA03: { speaker: "관리자", text: "검진을 마쳤습니다. 추가 이송 대상은 없습니다." },
  MA04: { speaker: "관리자", text: "확인이 필요한 대상이 있습니다. 안내에 따라 이동해 주십시오." },
  MA05: { speaker: "관리자", text: "구역 간 이동을 중단합니다. 다른 구역으로 퍼지는 것을 막아야 합니다." },
  MA06: { speaker: "관리자", text: "이 구역을 폐쇄합니다. 문에서 떨어져 대기하십시오." },
  MA07: { speaker: "관리자", text: "소등하겠습니다. 모두 자리에서 움직이지 않습니다." },
  // 밤 단서 방송(MA08~12) — 결말 전환에서 그날의 고아 단서를 시설 안내로 흘린다. 정본 docs/REMAKE_DAY_이미지제작서_밤단서_v2.md P.1
  MA08: { speaker: "관리자", text: "소독을 실시합니다. 바닥에서 떨어져 자리에 오르십시오." },
  MA09: { speaker: "관리자", text: "정리 작업이 있겠습니다. 비어 있는 자리는 아침에 정돈됩니다." },
  MA10: { speaker: "관리자", text: "외관 확인은 담당자가 합니다. 각자 확인할 필요 없습니다." },
  MA11: { speaker: "관리자", text: "배급 물자가 도착했습니다. 포대의 표기는 관리 용도입니다. 읽을 필요 없습니다." },
  MA12: { speaker: "관리자", text: "출입문은 관리자가 개방합니다. 문에 손대지 마십시오." },
  // 5회차 낮 끝 방송 — 소등 장면 끝, 마지막 밤 추리문 전(서버 day_end_broadcasts). 정본 docs/voice.md §10.2
  MA13: { speaker: "관리자", text: "축산 차량이 출발합니다. 문이 닫힐 때까지 자리에서 움직이지 마십시오." },
  AD01: { speaker: "조언자", text: "오늘 있었던 일을 세 번 물을 수 있습니다. 그다음, 내일의 규칙 하나를 정하십시오." },
  EN01: { speaker: "회고", text: "당신은 다섯 번의 하루를 관찰하고, 그 이유를 설명했습니다." },
  EN02: { speaker: "회고", text: "하루에 걸었던 규칙은, 에이전트의 행동을 제한하는 하네스였습니다. 원숭이손은 한 가지를 바꾸면서 다른 결과를 만드는 변경이었습니다." },
  EN03: { speaker: "회고", text: "지금부터, 무엇이 적용됐고 어디서 예상과 달라졌는지 살펴봅니다." },
} as const;

export type VoiceId = keyof typeof VOICE_CLIPS;

const normalize = (text: string) => text.normalize("NFC").replace(/[\s….,!?「」“”"'·]/g, "");

// 인물 대사 음원은 발화-자막 싱크 문제로 재생 보류(테스터6 F1), 관리자·조언자·회고만 재생.
const HELD_PREFIXES = ["CH", "MI", "EU", "JU"];

export function voiceForLine(speaker: string | undefined, text: string): VoiceId | null {
  const id = (Object.keys(VOICE_CLIPS) as VoiceId[]).find((id) => {
    const clip = VOICE_CLIPS[id];
    return clip.speaker === speaker && normalize(clip.text) === normalize(text);
  }) ?? null;
  return id && HELD_PREFIXES.some((prefix) => id.startsWith(prefix)) ? null : id;
}

export function voicesForLines(lines: { name: string; text: string }[], voiceId?: string | null): VoiceId[] {
  if (voiceId != null && Object.prototype.hasOwnProperty.call(VOICE_CLIPS, voiceId)) {
    return [voiceId as VoiceId];
  }
  return lines.flatMap((line) => {
    const id = voiceForLine(line.name, line.text);
    return id ? [id] : [];
  });
}

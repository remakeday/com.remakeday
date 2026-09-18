import type { LineKind } from "@/contracts/api";

/** 서버 LineKind + 플레이어 질문(프론트에서만 대사창에 붙인다). */
export type DisplayLineKind = LineKind | "user";
export type DisplayLine = {
  kind: DisplayLineKind;
  speaker: string | null;
  text: string;
  image_id: string | null;
  voice_id: string | null;
  observation_id: string | null;
};

interface LineStyle {
  label?: (speaker: string | null) => string;
  /** 말풍선·대화창 본문 클래스 — 종류마다 구분이 보이게 둔다. */
  className: string;
  /** 말풍선 정렬·너비 — 나레이션은 전폭, 대사는 말풍선. */
  frameClassName: string;
  icon?: string;
}

/** 줄 종류의 표시는 이 표에서만 정한다. 예전 채팅 말풍선 형태를 유지한다. */
export const lineStyles: Record<DisplayLineKind, LineStyle> = {
  user: {
    className: "rounded-ui border border-ink bg-ink px-3 py-2 text-paper",
    frameClassName: "max-w-[85%] self-end",
  },
  scene: {
    className: "text-ink",
    frameClassName: "w-full",
  },
  action: {
    className: "text-ink/75",
    frameClassName: "w-full",
  },
  rule_result: {
    label: () => "규칙이 작용했다",
    className: "rounded-ui border-l-4 border-orange bg-orange/10 px-3 py-2 text-ink",
    frameClassName: "w-full",
    icon: "│",
  },
  statement: {
    label: (speaker) => speaker ?? "",
    className: "rounded-ui border border-ink/30 px-3 py-2 italic text-ink before:content-['“'] after:content-['”']",
    frameClassName: "max-w-[85%] self-start",
  },
  broadcast: {
    label: () => "관리자",
    className: "rounded-ui border border-ink bg-ink px-3 py-2 font-mono text-paper",
    frameClassName: "w-full",
  },
  npc: {
    label: (speaker) => speaker ?? "",
    className: "rounded-ui border border-ink/30 px-3 py-2 text-ink",
    frameClassName: "max-w-[85%] self-start",
  },
  paw_effect: {
    label: () => "원숭이손",
    className: "rounded-ui border border-orange/40 bg-orange/10 px-3 py-2 text-ink",
    frameClassName: "w-full",
  },
  fragment: {
    label: (speaker) => speaker ? `단서 · ${speaker}` : "단서",
    className: "rounded-ui border border-dashed border-ink/30 px-3 py-2 text-ink/80",
    frameClassName: "max-w-[85%] self-start opacity-80",
    icon: "◇",
  },
  system: {
    className: "text-center text-ink/60",
    frameClassName: "w-full",
  },
};

/** 화자 라벨과 서버 원문의 이름·따옴표가 겹치지 않게 한다. */
export function lineText(line: DisplayLine): string {
  if (!line.speaker || !line.text.startsWith(`${line.speaker}:`)) return line.text;
  return line.text.slice(line.speaker.length + 1).trim().replace(/^["“]([\s\S]*)["”]$/, "$1");
}

export function playerLine(text: string): DisplayLine {
  return { kind: "user", speaker: null, text, image_id: null, voice_id: null, observation_id: null };
}

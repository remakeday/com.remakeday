import type { Line, LineKind } from "@/contracts/api";

interface LineStyle {
  label?: (speaker: string | null) => string;
  className: string;
  icon?: string;
}

/** 줄 종류의 표시는 이 표에서만 정한다. */
export const lineStyles: Record<LineKind, LineStyle> = {
  scene: { className: "text-ink" },
  action: { className: "text-ink/75" },
  rule_result: {
    label: () => "규칙이 작용했다",
    className: "border-l-4 border-orange bg-orange/10 px-3 py-2 text-ink",
    icon: "│",
  },
  statement: {
    label: (speaker) => speaker ?? "",
    className: "border-l-2 border-ink/30 pl-3 italic before:content-['“'] after:content-['”']",
  },
  broadcast: {
    label: () => "관리자",
    className: "border border-ink bg-ink px-3 py-2 font-mono text-paper",
  },
  npc: {
    label: (speaker) => speaker ?? "",
    className: "border border-ink/30 px-3 py-2 text-ink",
  },
  paw_effect: {
    label: () => "원숭이손",
    className: "border border-orange/40 bg-orange/10 px-3 py-2 text-ink",
  },
  fragment: {
    label: (speaker) => speaker ? `단서 · ${speaker}` : "단서",
    className: "border-b border-dashed border-ink/30 pb-2 text-ink/80",
    icon: "◇",
  },
  system: { className: "text-center text-ink/60" },
};

/** 화자 라벨과 서버 원문의 이름·따옴표가 겹치지 않게 한다. */
export function lineText(line: Line): string {
  if (!line.speaker || !line.text.startsWith(`${line.speaker}:`)) return line.text;
  return line.text.slice(line.speaker.length + 1).trim().replace(/^["“]([\s\S]*)["”]$/, "$1");
}

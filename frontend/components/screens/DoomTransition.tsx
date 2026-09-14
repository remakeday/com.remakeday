"use client";

import { useEffect, useState } from "react";
import type { WorldOutcome } from "@/contracts/api";
import { doomImage } from "@/lib/imageMap";

const OUTCOME_LINES: Record<WorldOutcome, string[]> = {
  truck: ["밤.", "트럭 소리.", "문이 열린다."],
  quiet: ["밤.", "복도가 조용하다.", "담요가 반듯하게 개어져 있다."],
  closure: ["밤.", "스피커가 켜진다.", "「금일부로 본 구역은 폐쇄됩니다.」"],
};

/**
 * 멸망 전환 — world_outcome별 3종, 3~5초. 사건은 없다. 단절만 있다.
 */
export function DoomTransition({
  outcome,
  onDone,
}: {
  outcome: WorldOutcome | null;
  onDone: () => void;
}) {
  const [lineCount, setLineCount] = useState(0);
  const lines = outcome ? OUTCOME_LINES[outcome] : ["밤."];

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    lines.forEach((_, i) => {
      timers.push(setTimeout(() => setLineCount(i + 1), 600 + i * 1100));
    });
    timers.push(setTimeout(onDone, 4200));
    return () => timers.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-end overflow-hidden bg-void px-6 pb-24 text-paper">
      {outcome && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={doomImage(outcome)}
          alt=""
          className={`pointer-events-none absolute inset-0 h-full w-full ${outcome === "closure" ? "object-contain" : "object-cover"} ${
            outcome === "quiet" ? "fade-in-slow opacity-50" : "fade-in opacity-60"
          }`}
        />
      )}
      {/* 하단 스크림 — 밝은 배경(문틈 빛 등) 위에서도 대사가 읽히게 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-void via-void/70 to-transparent"
      />
      <div className="relative z-10 flex flex-col items-center gap-4 text-center [text-shadow:0_1px_10px_rgba(0,0,0,0.95)]">
        {lines.slice(0, lineCount).map((line, i) => (
          <p key={i} className="fade-in text-lg leading-relaxed">
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}

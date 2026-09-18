"use client";

import { useEffect, useRef, useState } from "react";
import type { Npc } from "@/contracts/api";
import { npcImage } from "@/lib/imageMap";

const CHARACTERS = [
  { code: "chaeyeon", name: "채연" },
  { code: "minseok", name: "민석" },
  { code: "eunsang", name: "은상" },
  { code: "jun", name: "준" },
];

/** 직전 슬롯(11.7rem) 가로 기준 1.5배 — 비율 유지 */
const PORTRAIT_H = "h-[17.55rem]";
const PORTRAIT_W = "w-[17.55rem]";

export function DialogueStage({ npcs, selected, ready, disabled, dayDone, budgetLeft, onSelect }: {
  npcs: Npc[];
  selected: string | null;
  ready: boolean;
  disabled: boolean;
  dayDone: boolean;
  budgetLeft: number;
  onSelect: (code: string) => void;
}) {
  const current = npcs.find((npc) => npc.code === selected);
  const portrait = current ? npcImage(current.code, current.mood) : null;
  const slotRef = useRef<HTMLDivElement>(null);
  const [slotWidth, setSlotWidth] = useState<number | null>(null);

  useEffect(() => {
    const slot = slotRef.current;
    if (!slot) return;
    const sync = () => {
      const width = Math.round(slot.getBoundingClientRect().width);
      if (width > 0) setSlotWidth(width);
    };
    sync();
    const observer = new ResizeObserver(sync);
    observer.observe(slot);
    return () => observer.disconnect();
  }, [portrait]);

  return (
    <div className="flex max-w-[40%] shrink-0 flex-col items-start justify-end gap-2 pl-0 pt-2">
      <div ref={slotRef} className={`flex ${PORTRAIT_H} max-w-full shrink-0 items-end justify-start overflow-hidden`}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {portrait ? (
          <img
            src={portrait}
            alt={`${current?.name} 초상`}
            className={`block ${PORTRAIT_H} w-auto max-w-full object-contain object-left-bottom ${current?.uttered ? "grayscale opacity-55" : ""}`}
            onLoad={() => {
              const slot = slotRef.current;
              if (!slot) return;
              const width = Math.round(slot.getBoundingClientRect().width);
              if (width > 0) setSlotWidth(width);
            }}
          />
        ) : (
          <div className={`${PORTRAIT_H} ${PORTRAIT_W}`} aria-hidden="true" />
        )}
      </div>
      <div
        className="grid shrink-0 grid-cols-2 gap-2"
        style={slotWidth ? { width: slotWidth } : { width: "100%", maxWidth: "17.55rem" }}
      >
        {CHARACTERS.map((character) => {
          const npc = npcs.find((item) => item.code === character.code);
          const active = selected === character.code;
          const talked = npc?.uttered ?? false;
          const status = !ready || !npc ? "인물 확인 중" : talked ? "이 장면 대화 완료" : dayDone ? "하루 종료" : budgetLeft <= 0 ? "오늘 대화 소진" : "대화 가능";
          return (
            <button key={character.code} type="button" onClick={() => onSelect(character.code)} disabled={disabled || !npc}
              aria-pressed={active} aria-label={`${character.name} · ${status}`}
              className={`flex min-w-0 w-full flex-col items-center gap-0.5 border px-1.5 py-2 text-base leading-tight ${active ? "border-ink bg-ink text-paper" : "border-ink/30 hover:border-ink"} ${talked ? "grayscale opacity-55" : ""}`}>
              <span className="truncate">{character.name}</span>
              <span className="w-full truncate text-center text-sm">{status}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

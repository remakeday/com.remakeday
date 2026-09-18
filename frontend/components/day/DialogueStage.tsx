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

/** 1.2배 확대 이전 슬롯 크기 */
const PORTRAIT_H = "h-[17.55rem]";
const PORTRAIT_W = "w-[17.55rem]";
const SWAP_MS = 280;

type Face = { code: string; name: string; src: string };

function preload(src: string): Promise<void> {
  return new Promise((resolve) => {
    const image = new Image();
    image.onload = () => resolve();
    image.onerror = () => resolve();
    image.src = src;
    if (image.complete) resolve();
  });
}

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
  const nextFace: Face | null = current && portrait
    ? { code: current.code, name: current.name, src: portrait }
    : null;

  const slotRef = useRef<HTMLDivElement>(null);
  const faceRef = useRef<Face | null>(nextFace);
  const [slotWidth, setSlotWidth] = useState<number | null>(null);
  const [face, setFace] = useState<Face | null>(nextFace);
  const [outgoing, setOutgoing] = useState<Face | null>(null);
  const [swapping, setSwapping] = useState(false);
  const swapGen = useRef(0);

  faceRef.current = face;

  // 선택 변경 → 이미지 프리로드 후 교차 페이드(로드 전 빈 프레임으로 반짝이지 않게).
  useEffect(() => {
    if (!nextFace) {
      swapGen.current += 1;
      faceRef.current = null;
      setFace(null);
      setOutgoing(null);
      setSwapping(false);
      return;
    }
    const currentFace = faceRef.current;
    if (currentFace?.code === nextFace.code && currentFace.src === nextFace.src) return;

    if (!currentFace) {
      faceRef.current = nextFace;
      setFace(nextFace);
      setOutgoing(null);
      setSwapping(false);
      return;
    }

    const gen = ++swapGen.current;
    const reduce = typeof window !== "undefined"
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let timer = 0;
    let cancelled = false;

    void preload(nextFace.src).then(() => {
      if (cancelled || swapGen.current !== gen) return;
      setOutgoing(currentFace);
      faceRef.current = nextFace;
      setFace(nextFace);
      setSwapping(true);
      timer = window.setTimeout(() => {
        if (swapGen.current !== gen) return;
        setOutgoing(null);
        setSwapping(false);
      }, reduce ? 0 : SWAP_MS);
    });

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [nextFace?.code, nextFace?.src, nextFace?.name]);

  useEffect(() => {
    if (swapping) return;
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
  }, [face?.src, swapping]);

  const lockedWidth = slotWidth ?? undefined;

  return (
    <div className="flex w-max shrink-0 flex-col items-start justify-end gap-2">
      <div
        ref={slotRef}
        className={`relative flex ${PORTRAIT_H} shrink-0 items-end justify-start overflow-hidden rounded-ui ${swapping ? "" : "w-max max-w-[17.55rem]"}`}
        style={swapping && lockedWidth != null ? { width: lockedWidth } : undefined}
      >
        {outgoing && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={outgoing.src}
            alt=""
            aria-hidden="true"
            className={`day-portrait-face is-out pointer-events-none absolute bottom-0 left-0 block ${PORTRAIT_H} w-auto max-w-[17.55rem] rounded-ui object-contain object-left-bottom`}
          />
        )}
        {face ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={face.src}
            alt={`${face.name} 초상`}
            className={`day-portrait-face block ${PORTRAIT_H} w-auto max-w-[17.55rem] rounded-ui object-contain object-left-bottom ${
              swapping ? "is-in absolute bottom-0 left-0 z-[1]" : "relative z-[1]"
            }`}
            onLoad={() => {
              if (swapping) return;
              const slot = slotRef.current;
              if (!slot) return;
              const width = Math.round(slot.getBoundingClientRect().width);
              if (width > 0) setSlotWidth(width);
            }}
          />
        ) : (
          <div className={`${PORTRAIT_H} ${PORTRAIT_W} rounded-ui`} aria-hidden="true" />
        )}
      </div>
      {/* 버튼 1개 ≈ 포트레이트 너비의 50%(2열 그리드 = 포트레이트와 동일 폭) */}
      <div
        className="grid shrink-0 grid-cols-2 gap-2"
        style={slotWidth ? { width: slotWidth } : { width: "17.55rem" }}
      >
        {CHARACTERS.map((character) => {
          const npc = npcs.find((item) => item.code === character.code);
          const active = selected === character.code;
          const talked = npc?.uttered ?? false;
          const status = !ready || !npc ? "인물 확인 중" : talked ? "대화 완료" : dayDone ? "하루 종료" : budgetLeft <= 0 ? "오늘 대화 소진" : "대화 가능";
          return (
            <button key={character.code} type="button" onClick={() => onSelect(character.code)} disabled={disabled || !npc}
              aria-pressed={active} aria-label={`${character.name} · ${status}`}
              className={`flex min-w-0 w-full flex-col items-center gap-0.5 rounded-ui border px-1.5 py-2 text-base leading-tight ${active ? "border-ink bg-ink text-paper" : "border-ink/30 hover:border-ink"} ${talked ? "grayscale opacity-55" : ""}`}>
              <span className="truncate">{character.name}</span>
              <span className="w-full truncate text-center text-sm">{status}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import type { CellScores } from "@/contracts/api";
import { CellResults } from "@/components/CellResults";
import { GameplayGuide } from "@/components/GameplayGuide";
import { ENTRY_IMAGE, npcImage } from "@/lib/imageMap";

/**
 * 하루 준비(startLoop) 대기 중 순환하는 소개 카드 — 유저가 로딩 대신 정보를 받는다.
 * 표면에서 관찰 가능한 것만 적는다. 정체·병명 등 추리 대상은 스포일러라 금지.
 */
const INTRO_CARDS: { code: string | null; name: string; desc: string }[] = [
  // 첫 장은 세계 설명이자 가장 큰 힌트 — 무심코 읽으면 분위기, 잘 읽으면 답이다
  {
    code: null,
    name: "이곳",
    desc: "방송은 이름을 부르지 않는다. 머릿수를 센다. 트럭은 무언가를 싣고 온 적이 없다 — 실어 갈 뿐이다.",
  },
  { code: "chaeyeon", name: "채연", desc: "요즘 밥을 반쯤 남긴다. 말수가 줄었다." },
  { code: "minseok", name: "민석", desc: "규정을 지킨다. 이상한 일은 방송실에 알린다." },
  { code: "eunsang", name: "은상", desc: "들은 얘기를 옮긴다. 소문은 대부분 은상을 거친다." },
  { code: "jun", name: "준", desc: "궁금한 게 많다. 손목띠 숫자를 자꾸 들여다본다." },
];

function IntroCards() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((v) => (v + 1) % INTRO_CARDS.length), 2200);
    return () => clearInterval(t);
  }, []);
  const card = INTRO_CARDS[i];
  const portrait = card.code ? npcImage(card.code, "calm") : null;
  return (
    <div key={i} className="entry-line mt-6 flex flex-col items-center gap-3">
      {portrait && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={portrait} alt={card.name} className="h-28 w-21 rounded object-cover" />
      )}
      <p className="text-lg leading-relaxed">
        <span className="font-semibold">{card.name}</span>
        <span className="opacity-70"> — {card.desc}</span>
      </p>
      <p className="animate-pulse text-base tracking-widest opacity-50">하루를 준비하는 중…</p>
    </div>
  );
}

/**
 * 진입 — 검은 화면에 entry_lines 3줄이 한 줄씩 페이드인.
 * 탭/클릭하면 첫 회차(아침)로.
 */
export function EntryScreen({
  lines,
  priorCells,
  loopN,
  loading,
  onBegin,
}: {
  lines: string[] | null;
  priorCells: CellScores | null;
  loopN: number;
  loading: boolean;
  onBegin: () => void;
}) {
  const ready = lines !== null && !loading;
  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void py-6 text-paper sm:py-8">
      {/* A01 PNG 상·하 여백을 잘라 모바일 세로 화면을 빈 띠 없이 채운다. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        className="pointer-events-none fixed inset-0 h-full w-full scale-[1.35] object-cover object-center opacity-40"
      />
      <div className="relative z-10 flex w-full max-w-4xl flex-col items-center gap-6 px-4 text-center sm:px-8">
        {/* entry_lines는 랜딩이 보여준다 — 여기서는 반복하지 않는다. */}
        {priorCells && (
          <div className="entry-line mt-4 w-full max-w-xs" style={{ animationDelay: "0.6s" }}>
            <p className="mb-2 text-base opacity-60">지난 판의 기록</p>
            <CellResults cells={priorCells} light />
          </div>
        )}
        {!loading && (
          <section className="w-full border border-paper/40 bg-void/80 p-5 text-left">
            {loopN === 1 ? (
              <GameplayGuide />
            ) : (
              <p className="text-lg leading-relaxed">5일 동안 반복되는 하루를 살피고, 밤마다 세계가 왜 멸망하는지 밝혀 쓴다.</p>
            )}
            <button type="button" onClick={onBegin} disabled={!ready} className="mt-5 w-full border border-paper px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40">
              시작
            </button>
          </section>
        )}
        {loading && <IntroCards />}
      </div>
    </div>
  );
}

"use client";

import type { HintCell, SubmitRes } from "@/contracts/api";

/** 점수 0인 칸 힌트 — 칸 이름만. 정체는 안내하지 않는다(기획서 §4.8⑤) */
const EMPTY_CELL_HINT: Record<HintCell, string> = {
  cause: "원인이 아직 비어 있다.",
  motive: "동기가 아직 비어 있다.",
};

/**
 * 점수 — total만 크게. 칸별 점수는 판 종료 때만 (클리어 화면에서).
 * 매 밤 확인 신호: 인정된 내 문장(진실 문장은 서버가 잠근다)과 빈 칸 이름 (테스터10 F1).
 * 본문은 일반 요소로 두고 넘기기는 "계속" 버튼만 — 문장을 읽다 탭해도 넘어가지 않고 스크린리더가 본문을 읽는다.
 */
export function ScoreScreen({
  result,
  onContinue,
}: {
  result: SubmitRes;
  onContinue: () => void;
}) {
  const accepted = result.accepted_claims ?? [];
  const emptyCells = result.empty_cells ?? [];
  return (
    <section className="flex min-h-dvh w-full flex-col items-center justify-center bg-void px-6 text-paper">
      <div className="fade-in-slow flex flex-col items-center gap-6 text-center">
        <p className="text-sm opacity-70">{result.loop_n}/5번째 밤 · 상황 이해도</p>
        <p className="text-7xl font-semibold tracking-tight">
          {Math.round(result.total)}
          <span className="text-3xl opacity-60">%</span>
        </p>
        <p className="text-sm opacity-70">
          {result.is_final ? "다섯 번의 하루를 지나, 당신이 이해한 만큼." : "오늘의 기록을 안고, 다음 하루로."}
        </p>
        {/* 칸별 점수는 마지막 밤에 공개 */}
        {(result.cell_feedback ?? null) && (
          <p className="max-w-md text-xs leading-relaxed opacity-70">
            {result.cell_feedback}
          </p>
        )}
        {accepted.length > 0 && (
          <div className="flex max-w-md flex-col gap-2">
            <p className="text-xs tracking-widest opacity-50">인정된 내 문장</p>
            <ul className="flex flex-col gap-1 text-sm leading-relaxed">
              {accepted.map((claim) => (
                <li key={claim}>「{claim}」</li>
              ))}
            </ul>
          </div>
        )}
        {emptyCells.map((cell) => (
          <p key={cell} className="text-xs opacity-70">
            {EMPTY_CELL_HINT[cell]}
          </p>
        ))}
        {(result.wrong_claim_count ?? 0) > 0 && (
          <p className="text-[11px] opacity-40">
            {result.wrong_claim_count}개의 주장은 세계와 닿지 않았다.
          </p>
        )}
        <button
          type="button"
          onClick={onContinue}
          className="mt-10 border border-paper/60 px-10 py-3 text-sm hover:bg-paper hover:text-void"
        >
          계속
        </button>
      </div>
    </section>
  );
}

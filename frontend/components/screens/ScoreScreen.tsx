"use client";

import type { SubmitRes } from "@/contracts/api";

/**
 * 점수 — total만 크게. 칸별 점수는 판 종료 때만 (클리어 화면에서).
 */
export function ScoreScreen({
  result,
  onContinue,
}: {
  result: SubmitRes;
  onContinue: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onContinue}
      className="flex min-h-dvh w-full cursor-pointer flex-col items-center justify-center bg-void px-6 text-paper"
      aria-label="계속"
    >
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
        {(result.wrong_claim_count ?? 0) > 0 && (
          <p className="text-[11px] opacity-40">
            {result.wrong_claim_count}개의 주장은 세계와 닿지 않았다.
          </p>
        )}
        <p className="mt-10 text-xs tracking-widest opacity-40">탭하여 계속</p>
      </div>
    </button>
  );
}

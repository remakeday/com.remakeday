"use client";

import { useState } from "react";
import type { SubmitRes } from "@/contracts/api";
import { CellResults } from "@/components/CellResults";
import { Retrospective } from "@/components/Retrospective";
import { SurveyBlock } from "@/components/SurveyBlock";
import { TruthRevealCards } from "@/components/TruthRevealCards";
import { clearImage } from "@/lib/imageMap";

/** 다섯 번째 밤: 이야기 결말 → 평가 → 개발 회고. */
export function ClearScreen({
  attemptId, result, onRetry, retryBusy,
}: {
  attemptId: string;
  result: SubmitRes;
  onRetry: () => void;
  retryBusy: boolean;
}) {
  const [stage, setStage] = useState<"ending" | "survey" | "retrospective">("ending");
  return (
    <div className="relative min-h-dvh overflow-hidden bg-void px-6 py-12 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={clearImage(result.total)} alt=""
        className="pointer-events-none fixed inset-0 h-full w-full object-cover opacity-30" />
      <div className="fade-in-slow relative z-10 mx-auto flex w-full max-w-2xl flex-col items-center gap-8">
        {stage === "ending" && (
          <>
            <h1 className="text-center text-xl">다섯 번째 밤, 마지막 기록</h1>
            <p className="text-center text-4xl font-semibold">최종 이해도 {Math.round(result.total)}%</p>
            {result.cells && <CellResults cells={result.cells} light />}
            {result.truth_reveal && <TruthRevealCards reveal={result.truth_reveal} light />}
            <div className="space-y-4 text-sm leading-loose">
              {(result.ending_lines ?? []).map((line, i) => <p key={i}>{line}</p>)}
            </div>
            <button type="button" onClick={() => setStage("survey")}
              className="border border-paper/60 px-8 py-3 text-sm hover:bg-paper hover:text-void">
              이 세계의 바깥으로
            </button>
          </>
        )}
        {stage === "survey" && (
          <SurveyBlock attemptId={attemptId} onDone={() => setStage("retrospective")} />
        )}
        {stage === "retrospective" && (
          <>
            <p className="text-center text-sm">평가 고맙다.</p>
            <Retrospective attemptId={attemptId} />
          </>
        )}
        {stage === "retrospective" && (
          <button type="button" onClick={onRetry} disabled={retryBusy} aria-busy={retryBusy}
            className="border border-paper/60 px-10 py-3 text-sm hover:bg-paper hover:text-void disabled:opacity-40">
            {retryBusy ? "다시 시작 준비 중…" : "다시 시작"}
          </button>
        )}
      </div>
    </div>
  );
}

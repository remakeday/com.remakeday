"use client";

import { ENTRY_IMAGE } from "@/lib/imageMap";

/**
 * 진행 중인 판이 있을 때 — 이어하기 / 다시 시작하기 (설계 2026-10-16 §3.1). 진입 화면과 같은 배경·버튼.
 * 다시 시작하기는 그날 판 수를 한 칸 쓴다(포기한 판도 센다). 남은 판이 없으면 끈다.
 */
export function ResumeChoiceScreen({
  todayRemaining,
  dailyLimit,
  busy,
  onResume,
  onRestart,
}: {
  todayRemaining: number;
  dailyLimit: number;
  busy: boolean;
  onResume: () => void;
  onRestart: () => void;
}) {
  const canRestart = todayRemaining > 0;
  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void py-6 text-paper sm:py-8">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        decoding="async"
        className="pointer-events-none fixed inset-0 h-full w-full scale-[1.35] object-cover object-center opacity-40"
      />
      <div className="relative z-10 w-full max-w-md px-4">
        <section aria-busy={busy} className="w-full border border-paper/40 bg-void/80 p-5 text-left">
          <p className="text-lg leading-relaxed">진행 중인 판이 있다.</p>
          <button
            type="button"
            onClick={onResume}
            disabled={busy}
            className="mt-5 w-full border border-paper px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40"
          >
            이어하기
          </button>
          <button
            type="button"
            onClick={onRestart}
            disabled={busy || !canRestart}
            className="mt-3 w-full border border-paper px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40"
          >
            다시 시작하기
          </button>
          <p className="mt-2 text-base opacity-70">
            {canRestart
              ? `오늘 남은 판 ${todayRemaining}/${dailyLimit} · 다시 시작하면 1회가 차감됩니다`
              : "오늘은 더 시작할 수 없습니다"}
          </p>
        </section>
      </div>
    </div>
  );
}

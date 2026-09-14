"use client";

import { DOOM_END_IMAGE } from "@/lib/imageMap";

/**
 * 멸망 종료 (closed_by=doom) — "세계는 멸망했습니다" + 재도전.
 */
export function DoomEndScreen({
  onRetry,
  retryBusy,
}: {
  onRetry: () => void;
  retryBusy: boolean;
}) {
  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void px-6 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={DOOM_END_IMAGE}
        alt=""
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-70"
      />
      <div className="fade-in-slow relative z-10 flex flex-col items-center gap-10 text-center [text-shadow:0_1px_10px_rgba(0,0,0,0.95)]">
        <p className="text-xl leading-relaxed">세계는 멸망했습니다.</p>
        <button
          type="button"
          onClick={onRetry}
          disabled={retryBusy}
          className="border border-paper/60 px-10 py-2 text-sm hover:border-paper hover:bg-paper hover:text-void disabled:opacity-40"
        >
          {retryBusy ? "…" : "다시"}
        </button>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";

export type GuardKind = "login" | "daily_limit" | "daily_cap" | "rate";

const MESSAGE: Record<GuardKind, string> = {
  login: "로그인이 필요하다. 랜딩에서 구글로 시작해라.",
  daily_limit: "오늘은 여기까지. 내일 다시 시작할 수 있다.",
  daily_cap: "오늘 정원이 마감됐다. 내일 다시 열린다.",
  rate: "요청이 너무 잦다.",
};

/**
 * 로그인 필요·하루 한도·정원 마감·속도 제한 — 게임 진행 대신 이 화면으로 대체한다.
 */
export function GuardScreen({
  kind,
  retryAfter,
}: {
  kind: GuardKind;
  retryAfter?: number;
}) {
  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center gap-8 bg-void px-8 py-10 text-center text-paper">
      <p className="text-lg leading-relaxed">
        {kind === "rate"
          ? `${MESSAGE.rate} ${retryAfter ?? 0}초 뒤 다시.`
          : MESSAGE[kind]}
      </p>
      {kind === "login" && (
        <Link
          href="/"
          className="border border-paper px-10 py-2 text-lg hover:bg-paper hover:text-void"
        >
          랜딩으로
        </Link>
      )}
    </div>
  );
}

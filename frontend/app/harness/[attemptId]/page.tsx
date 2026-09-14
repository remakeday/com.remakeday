"use client";

import { use } from "react";
import { Retrospective } from "@/components/Retrospective";
import { HARNESS_IMAGE } from "@/lib/imageMap";

/** 5회차 완료 후 점수와 무관하게 공개. 접근 조건은 서버에서 검사한다. */
export default function HarnessPage({ params }: { params: Promise<{ attemptId: string }> }) {
  const { attemptId } = use(params);
  return (
    <main className="relative min-h-dvh bg-void px-6 py-12 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={HARNESS_IMAGE} alt="" className="pointer-events-none fixed inset-0 h-full w-full object-cover opacity-30" />
      <div className="relative z-10 mx-auto max-w-2xl"><Retrospective attemptId={attemptId} /></div>
    </main>
  );
}

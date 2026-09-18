"use client";

import type { DamageLevel } from "@/contracts/api";
import { damageClass, morningImage } from "@/lib/imageMap";

/** 문장 종결 뒤 줄바꿈 — 모바일에서 어절이 잘리지 않게 문장 단위로 나눈다. */
function breakSentences(text: string): string {
  return text.replace(/([.?!])\s+(?=\S)/g, "$1\n").trim();
}

/**
 * 아침 — "7시 12분. 눈을 뜬다." (백엔드가 완성 문장 반환)
 * B군 이미지의 전체 구도를 유지하고, damage_level에 따라 이미지만 미세하게 밀린다.
 */
export function MorningScreen({
  morningText,
  aftermath,
  activeRules,
  budgetLeft,
  damageLevel,
  loopN,
  onContinue,
}: {
  morningText: string;
  /** 전날 걸린 규칙의 부작용 암시 — 있을 때만 한 줄 */
  aftermath: string | null;
  /** 오늘 세계에 걸린 규칙 — 있을 때만 목록 */
  activeRules: string[];
  /** 오늘 남은 발화 예산 — 2회차부터 감소 안내 */
  budgetLeft: number;
  damageLevel: DamageLevel;
  loopN: number;
  onContinue: () => void;
}) {
  return (
    <div className="min-h-dvh w-full overflow-hidden bg-paper">
      <button
        type="button"
        onClick={onContinue}
        className="relative flex min-h-dvh w-full cursor-pointer flex-col items-center justify-center px-6 py-10 text-ink"
        aria-label="계속"
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={morningImage(damageLevel, loopN)}
          alt=""
          className={`pointer-events-none absolute inset-0 h-full w-full object-contain opacity-30 ${damageClass(damageLevel)}`}
        />
        <div className="fade-in-slow relative z-10 flex w-full max-w-md flex-col items-center gap-8">
          <p className="text-center text-lg leading-relaxed whitespace-pre-line">
            {breakSentences(morningText)}
          </p>
          {aftermath && (
            <p className="text-center text-lg leading-relaxed whitespace-pre-line text-orange">
              {breakSentences(aftermath)}
            </p>
          )}
          {activeRules.length > 0 && (
            <div className="text-center text-lg leading-relaxed text-orange">
              <p className="text-lg tracking-widest text-ink">
                오늘 세계에 걸린 규칙
              </p>
              {activeRules.map((rule) => (
                <p key={rule} className="whitespace-pre-line">
                  {breakSentences(rule)}
                </p>
              ))}
            </div>
          )}
          <p className="text-center text-lg leading-relaxed text-ink">
            5일 중 {loopN}일째 아침이다.
          </p>
          <div className="text-center">
            <p className="text-lg">오늘 남은 대화 {budgetLeft}회</p>
            <p className="text-lg whitespace-pre-line text-ink">
              {"하루 6장면에서 함께 쓴다.\n장면이 바뀌어도 충전되지 않는다."}
            </p>
          </div>
          <p className="mt-6 border-b border-ink pb-1 text-lg font-semibold tracking-wide text-ink">탭하여 계속</p>
        </div>
      </button>
    </div>
  );
}

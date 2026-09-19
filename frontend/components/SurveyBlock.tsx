"use client";

import { useState } from "react";
import { api, type SurveyReq } from "@/contracts/api";

const ITEMS = [
  { field: "fun", label: "재미·몰입도", description: "게임 플레이가 재미있고 몰입감 있었다." },
  { field: "novelty", label: "참신성", description: "기존 AI 서비스나 게임과 다른 새로운 경험이었다." },
  { field: "ai_agency", label: "AI 활용 체감", description: "AI가 단순한 대사 생성이 아니라 게임의 판단과 진행에 실제로 관여한다고 느꼈다." },
  { field: "polish", label: "완성도", description: "게임의 진행 방식과 인터페이스가 자연스럽고 안정적이었다." },
  { field: "recommend", label: "추천 의향", description: "다른 사람에게 이 게임을 플레이해보라고 추천하고 싶다." },
] as const;

const STARS = [1, 2, 3, 4, 5];

export function SurveyBlock({ attemptId, onDone }: {
  attemptId: string;
  onDone: () => void;
}) {
  const [scores, setScores] = useState<Omit<SurveyReq, "skipped">>({});
  const [busy, setBusy] = useState(false);

  const send = async (skipped: boolean) => {
    if (busy) return;
    setBusy(true);
    try {
      await api.sendSurvey(attemptId, skipped ? { skipped: true } : { skipped: false, ...scores });
    } catch {
      // 평가 실패로 진행을 막지 않는다.
    } finally {
      onDone();
    }
  };

  return (
    <section data-survey="block" className="w-full space-y-8 text-paper">
      <h1 className="text-center text-xl">이 게임은 어땠나</h1>
      <div className="space-y-6">
        {ITEMS.map(({ field, label, description }) => (
          <div key={field} className="space-y-1">
            <p className="text-base">{label}</p>
            <p className="text-sm leading-relaxed opacity-70">{description}</p>
            <div role="radiogroup" aria-label={label} className="flex">
              {STARS.map((score) => (
                <button key={score} type="button" role="radio"
                  aria-label={`${label} ${score}점`}
                  aria-checked={scores[field] === score}
                  tabIndex={(scores[field] ?? 1) === score ? 0 : -1}
                  disabled={busy}
                  onClick={() => setScores((current) => ({
                    ...current, [field]: current[field] === score ? null : score,
                  }))}
                  onKeyDown={(event) => {
                    let next: number;
                    switch (event.key) {
                      case "ArrowRight":
                      case "ArrowDown": next = score % 5 + 1; break;
                      case "ArrowLeft":
                      case "ArrowUp": next = (score + 3) % 5 + 1; break;
                      case "Home": next = 1; break;
                      case "End": next = 5; break;
                      default: return;
                    }
                    event.preventDefault();
                    setScores((current) => ({ ...current, [field]: next }));
                    event.currentTarget.parentElement
                      ?.querySelectorAll<HTMLButtonElement>('[role="radio"]')[next - 1]?.focus();
                  }}
                  className="flex size-11 items-center justify-center text-3xl hover:bg-paper/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-paper disabled:opacity-40">
                  <span aria-hidden="true">{score <= (scores[field] ?? 0) ? "★" : "☆"}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <button type="button" onClick={() => void send(false)} disabled={busy} aria-busy={busy}
          className="border border-paper/60 px-3 py-3 text-sm hover:bg-paper hover:text-void disabled:opacity-40">
          평가 보내기
        </button>
        <button type="button" onClick={() => void send(true)} disabled={busy} aria-busy={busy}
          className="border border-paper/60 px-3 py-3 text-sm hover:bg-paper hover:text-void disabled:opacity-40">
          건너뛰기
        </button>
      </div>
    </section>
  );
}

"use client";

import { useRef, useState, type ReactNode } from "react";
import type { Observation } from "@/contracts/api";
import { GuideAndRules } from "@/components/hud/GuideAndRules";
import { RecordsPanel } from "@/components/hud/RecordsPanel";
import { RecordLog, type RecordAdvice } from "@/components/hud/RecordLog";

type OpenPanel = "record" | "guide" | null;

export function Hud({ loopN, observations, advice, activeRules, loading, error, onRetry, children }: {
  loopN: number;
  observations: Observation[];
  advice: RecordAdvice[];
  activeRules: string[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  children: ReactNode;
}) {
  const [openPanel, setOpenPanel] = useState<OpenPanel>(null);
  const recordButtonRef = useRef<HTMLButtonElement>(null);
  const guideButtonRef = useRef<HTMLButtonElement>(null);
  const panelTitle = openPanel === "record" ? "기록" : "안내";

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 flex h-14 items-center justify-between gap-2 border-b border-ink/20 bg-paper px-3 text-ink sm:px-6" aria-label="게임 현황">
        <p className="shrink-0 whitespace-nowrap text-sm sm:text-base">{loopN}일째 / 5일</p>
        <div className="flex items-center gap-2 sm:gap-5">
          {children}
          <div className="flex shrink-0 items-center gap-1">
            <button ref={recordButtonRef} type="button" onClick={() => setOpenPanel("record")} aria-haspopup="dialog"
              aria-expanded={openPanel === "record"} aria-controls={openPanel === "record" ? "hud-panel" : undefined}
              className="whitespace-nowrap border border-ink/40 px-1.5 text-sm hover:border-ink sm:px-3 sm:text-base">
              기록
            </button>
            <button ref={guideButtonRef} type="button" onClick={() => setOpenPanel("guide")} aria-haspopup="dialog"
              aria-expanded={openPanel === "guide"} aria-controls={openPanel === "guide" ? "hud-panel" : undefined}
              className="whitespace-nowrap border border-ink/40 px-1.5 text-sm hover:border-ink sm:px-3 sm:text-base">
              안내
            </button>
          </div>
        </div>
      </header>
      {openPanel && <RecordsPanel title={panelTitle} onClose={() => setOpenPanel(null)}
        returnFocus={openPanel === "record" ? recordButtonRef.current : guideButtonRef.current}>
        {openPanel === "record" ? <>
          {loading && <p role="status" className="mb-3 text-base text-ink/60">기록을 불러오는 중…</p>}
          {error && <div role="alert" className="mb-3 text-base">
            <p>기록을 불러오지 못했다. {error}</p>
            <button type="button" onClick={onRetry} disabled={loading} className="underline disabled:opacity-40">다시 불러온다</button>
          </div>}
          <RecordLog observations={observations} advice={advice} loopN={loopN} />
        </> : <GuideAndRules activeRules={activeRules} />}
      </RecordsPanel>}
    </>
  );
}

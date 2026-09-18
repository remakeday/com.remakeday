"use client";

import { useRef, useState, type ReactNode } from "react";
import type { Observation } from "@/contracts/api";
import { RecordsPanel } from "@/components/hud/RecordsPanel";
import type { RecordAdvice } from "@/components/hud/RecordLog";

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
  const [open, setOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 flex h-14 items-center justify-between gap-2 border-b border-ink/20 bg-paper px-3 text-ink sm:px-6" aria-label="게임 현황">
        <p className="shrink-0 whitespace-nowrap text-sm sm:text-base">{loopN}일째 / 5일</p>
        <div className="flex items-center gap-2 sm:gap-5">
          {children}
          <button ref={buttonRef} type="button" onClick={() => setOpen(true)} aria-haspopup="dialog"
            aria-expanded={open} aria-controls={open ? "records-panel" : undefined}
            className="shrink-0 whitespace-nowrap border border-ink/40 px-2 text-sm hover:border-ink sm:px-3 sm:text-base">
            기록·안내
          </button>
        </div>
      </header>
      {open && <RecordsPanel loopN={loopN} observations={observations} advice={advice} activeRules={activeRules}
        loading={loading} error={error} onRetry={onRetry} onClose={() => setOpen(false)} returnFocus={buttonRef.current} />}
    </>
  );
}

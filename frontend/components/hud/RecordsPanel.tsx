"use client";

import { useEffect, useRef, useState } from "react";
import type { Observation } from "@/contracts/api";
import { GuideAndRules } from "@/components/hud/GuideAndRules";
import { RecordLog, type RecordAdvice } from "@/components/hud/RecordLog";

const TABS = ["단서 기록", "플레이 안내·걸린 규칙"];

export function RecordsPanel({ loopN, observations, advice, activeRules, loading, error, onRetry, onClose, returnFocus }: {
  loopN: number;
  observations: Observation[];
  advice: RecordAdvice[];
  activeRules: string[];
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onClose: () => void;
  returnFocus: HTMLElement | null;
}) {
  const [tab, setTab] = useState(0);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  useEffect(() => {
    const dialog = dialogRef.current;
    const overflow = document.body.style.overflow;
    // 네이티브 모달이 배경 입력을 막는다.
    dialog?.showModal();
    document.body.style.overflow = "hidden";
    return () => {
      dialog?.close();
      document.body.style.overflow = overflow;
      returnFocus?.focus({ preventScroll: true });
    };
  }, [returnFocus]);

  return (
    <dialog ref={dialogRef} id="records-panel" role="dialog" aria-modal="true" aria-labelledby="records-title"
      onCancel={(event) => { event.preventDefault(); onClose(); }}
      onKeyDown={(event) => {
        event.stopPropagation();
        if (event.key !== "Tab") return;
        const focusable = Array.from(event.currentTarget.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        )).filter((element) => element.tabIndex >= 0 && !element.matches(":disabled")
          && element.getClientRects().length > 0 && getComputedStyle(element).visibility === "visible");
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }}
      className="fixed inset-0 m-0 h-dvh max-h-none w-full max-w-none overflow-hidden bg-paper p-0 text-ink backdrop:bg-void/80">
      <div className="mx-auto flex h-full max-w-3xl flex-col px-4 pt-3 pb-[env(safe-area-inset-bottom)] sm:px-6">
        <div className="flex shrink-0 items-center justify-between gap-3">
          <h2 id="records-title" className="text-xl">기록·안내</h2>
          <button type="button" onClick={onClose} aria-label="기록·안내 닫기"
            className="border border-ink/40 px-4 text-base hover:border-ink">닫기</button>
        </div>
        <div role="tablist" aria-label="기록과 안내" className="mt-3 flex shrink-0 border-b border-ink/30">
          {TABS.map((label, index) => (
            <button key={label} ref={(node) => { tabRefs.current[index] = node; }} type="button" role="tab"
              id={`records-tab-${index}`} aria-selected={tab === index} aria-controls={`records-content-${index}`}
              tabIndex={tab === index ? 0 : -1} onClick={() => setTab(index)}
              onKeyDown={(event) => {
                if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
                event.preventDefault();
                const next = event.key === "Home" ? 0 : event.key === "End" ? TABS.length - 1 : (index + 1) % TABS.length;
                setTab(next);
                tabRefs.current[next]?.focus();
              }}
              className={`min-w-0 flex-1 px-2 py-2 text-sm sm:text-base ${tab === index ? "border-b-2 border-ink font-semibold" : "text-ink/60"}`}>
              {label}
            </button>
          ))}
        </div>
        <div key={tab} role="tabpanel" id={`records-content-${tab}`} aria-labelledby={`records-tab-${tab}`}
          tabIndex={0} className="min-h-0 flex-1 overflow-y-auto overscroll-contain py-4">
          {tab === 0 ? <>
            {loading && <p role="status" className="mb-3 text-base text-ink/60">기록을 불러오는 중…</p>}
            {error && <div role="alert" className="mb-3 text-base">
              <p>기록을 불러오지 못했다. {error}</p>
              <button type="button" onClick={onRetry} disabled={loading} className="underline disabled:opacity-40">다시 불러온다</button>
            </div>}
            <RecordLog observations={observations} advice={advice} loopN={loopN} />
          </> : <GuideAndRules activeRules={activeRules} />}
        </div>
      </div>
    </dialog>
  );
}

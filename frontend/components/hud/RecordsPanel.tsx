"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";

export function RecordsPanel({ title, children, onClose, returnFocus }: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  returnFocus: HTMLElement | null;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const titleId = useId();

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
    <dialog ref={dialogRef} id="hud-panel" role="dialog" aria-modal="true" aria-labelledby={titleId}
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
          <h2 id={titleId} className="text-xl">{title}</h2>
          <button type="button" onClick={onClose} aria-label={`${title} 닫기`}
            className="border border-ink/40 px-4 text-base hover:border-ink">닫기</button>
        </div>
        <div role="region" aria-label={`${title} 내용`} tabIndex={0}
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain py-4">
          {children}
        </div>
      </div>
    </dialog>
  );
}

"use client";

import { useEffect, useRef } from "react";
import type { PawOffer } from "@/contracts/api";
import { PAW_IMAGE } from "@/lib/imageMap";

export function PawPopup({ offer, busy, onRespond }: {
  offer: PawOffer;
  busy: boolean;
  onRespond: (accept: boolean) => void;
}) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    dialogRef.current?.focus();
    return () => { previous?.focus(); };
  }, []);

  return (
    <div ref={dialogRef} role="dialog" aria-modal="true" aria-label="원숭이손의 제안" aria-busy={busy} tabIndex={-1}
      className="fade-in fixed inset-0 z-40 flex items-center justify-center overflow-y-auto bg-void/90 px-6 py-6"
      onKeyDown={(event) => {
        if (event.key !== "Tab") return;
        const buttons = [...(dialogRef.current?.querySelectorAll<HTMLButtonElement>("button:not(:disabled)") ?? [])];
        const first = buttons[0];
        const last = buttons[buttons.length - 1];
        if (!first) { event.preventDefault(); return; }
        if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }}>
      <div className="flex w-full max-w-sm flex-col items-center gap-5 text-center text-paper">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={PAW_IMAGE} alt="" className="aspect-square w-40 object-cover" />
        <p className="text-lg opacity-70">무언가가 굴러왔다.</p>
        <p className="text-base leading-relaxed">{offer.rule_label}</p>
        {offer.shown_reason && <p className="text-base leading-relaxed text-orange">{offer.shown_reason}</p>}
        {/* 대가의 존재만 암시한다 — 내용은 밝히지 않는다. */}
        <p className="text-base leading-relaxed opacity-60">대가 없이 굴러오는 것은 없다.</p>
        <div className="flex gap-4">
          <button type="button" disabled={busy} onClick={() => onRespond(true)} className="border border-orange px-6 py-2 text-lg text-orange hover:bg-orange hover:text-void disabled:opacity-40">받는다</button>
          <button type="button" disabled={busy} onClick={() => onRespond(false)} className="border border-paper/50 px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40">제안을 거절한다</button>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import type { Line } from "@/contracts/api";
import { lineStyles, lineText } from "@/lib/lineStyles";
import { VoiceReplay } from "@/components/VoicePlayer";

export function LineBox({ lines, cursor, disabled = false, onPrevious, onNext, onShowAll, onReachedEnd }: {
  lines: Line[];
  cursor: number;
  disabled?: boolean;
  onPrevious: () => void;
  onNext: () => void;
  onShowAll: () => void;
  onReachedEnd: () => void;
}) {
  const regionRef = useRef<HTMLElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const line = lines[cursor];
  const style = lineStyles[line?.kind ?? "system"];
  const label = style.label?.(line?.speaker ?? null);
  const atEnd = cursor >= lines.length - 1;

  useEffect(() => {
    if (atEnd && !disabled) onReachedEnd();
  }, [atEnd, cursor, lines.length, disabled, onReachedEnd]);

  useEffect(() => {
    if (textRef.current) textRef.current.scrollTop = 0;
  }, [cursor]);

  useEffect(() => {
    if (disabled) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.isComposing || event.repeat || event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target;
      // 질문 입력·기록 패널은 그대로 두고, 대사창 버튼에서도 화살표로 넘긴다.
      if (target instanceof HTMLElement) {
        if (target.closest('input, textarea, select, [contenteditable="true"], [role="dialog"]')) return;
        if (target.closest("button, a") && (!["ArrowLeft", "ArrowRight"].includes(event.key) || !regionRef.current?.contains(target))) return;
      }
      if ([" ", "Enter", "ArrowRight"].includes(event.key)) {
        event.preventDefault();
        if (!atEnd) onNext();
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        if (cursor > 0) onPrevious();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [atEnd, cursor, disabled, onNext, onPrevious]);

  return (
    <section ref={regionRef} role="region" aria-label="대사창" tabIndex={0}
      className="flex h-48 shrink-0 flex-col border-t border-ink/30 bg-paper py-2 outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ink sm:h-52"
      onClick={(event) => {
        if ((event.target as HTMLElement).closest("button") || window.getSelection()?.toString()) return;
        if (!disabled && !atEnd) onNext();
      }}>
      <div ref={textRef} className="mx-auto min-h-0 w-full max-w-3xl flex-1 overflow-y-auto break-words px-4 sm:px-10" aria-live="polite" aria-atomic="true">
        {label && <p className="mb-1 text-sm text-ink/70">{style.icon && <span aria-hidden="true">{style.icon} </span>}{label}</p>}
        <p data-line-kind={line?.kind ?? "system"} className={`text-base leading-relaxed whitespace-pre-wrap sm:text-lg ${style.className}`}>
          {line ? lineText(line) : "장면을 살핀다."}
        </p>
        {line?.text.split("\n").map((text, index) => <VoiceReplay key={index} speaker={line.speaker ?? undefined} text={text} />)}
      </div>
      <div className="mx-auto mt-1 flex w-full max-w-3xl shrink-0 items-center justify-between gap-2 px-4 text-sm sm:px-10">
        <button type="button" aria-label="이전" disabled={disabled || cursor === 0} onClick={onPrevious}
          className="border border-ink/30 px-3 py-1 disabled:opacity-30">◀ <span className="sr-only">이전</span></button>
        <span className="text-ink/60">{lines.length ? cursor + 1 : 0} / {lines.length}</span>
        <div className="flex gap-2">
          <button type="button" disabled={disabled || atEnd} onClick={onShowAll}
            className="px-3 py-1 underline underline-offset-2 disabled:opacity-30">모두 보기</button>
          <button type="button" aria-label="다음" disabled={disabled || atEnd} onClick={onNext}
            className="border border-ink/30 px-3 py-1 disabled:opacity-30">▶ <span className="sr-only">다음</span></button>
        </div>
      </div>
    </section>
  );
}

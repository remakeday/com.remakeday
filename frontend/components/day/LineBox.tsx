"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DisplayLine } from "@/lib/lineStyles";
import { lineStyles, lineText } from "@/lib/lineStyles";
import { MANAGER_IMAGE, npcImage } from "@/lib/imageMap";
import { VoiceReplay } from "@/components/VoicePlayer";

/** 글자 타이핑 간격 — 기존 18ms의 3배(재생 속도 1/3). */
const CHAR_MS = 54;
/** 줄 사이 멈춤 — 기존 220ms의 3배. */
const LINE_PAUSE_MS = 660;

const SPEAKER_CODE: Record<string, string> = {
  채연: "chaeyeon",
  민석: "minseok",
  은상: "eunsang",
  준: "jun",
};

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** 인물 대사 왼쪽에 둘 초상. 네 인물·관리자 방송만. */
function portraitSrcFor(line: DisplayLine): string | null {
  if (line.kind === "broadcast") return MANAGER_IMAGE;
  if (line.kind !== "npc" && line.kind !== "statement" && line.kind !== "fragment") return null;
  const code = line.speaker ? SPEAKER_CODE[line.speaker] : undefined;
  return code ? npcImage(code, "calm") : null;
}

function ChatLine({ line, text, typing, hold }: { line: DisplayLine; text: string; typing: boolean; hold: boolean }) {
  const style = lineStyles[line.kind];
  const label = style.label?.(line.speaker ?? null);
  const complete = text === lineText(line);
  const portraitSrc = portraitSrcFor(line);
  const body = (
    <div className={`flex min-w-0 flex-col gap-0.5 ${portraitSrc ? "flex-1" : style.frameClassName}`}>
      {label && (
        <p className="text-sm text-ink/70">
          {style.icon && <span aria-hidden="true">{style.icon} </span>}
          {label}
        </p>
      )}
      <p data-line-kind={line.kind} data-typing={typing ? "true" : undefined}
        className={`text-base leading-relaxed whitespace-pre-wrap sm:text-lg ${style.className}`}>
        {text}
        {typing && <span className="ml-0.5 inline-block animate-pulse" aria-hidden="true">▍</span>}
      </p>
      {complete && !hold && line.text.split("\n").map((chunk, index) => (
        <VoiceReplay key={index} speaker={line.speaker ?? undefined} text={chunk} />
      ))}
    </div>
  );
  if (!portraitSrc) return body;
  return (
    <div className={`flex items-start gap-2 ${style.frameClassName}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={portraitSrc}
        alt=""
        aria-hidden="true"
        className="mt-0.5 h-9 w-9 shrink-0 rounded-ui border border-ink/25 object-cover object-top"
      />
      {body}
    </div>
  );
}

export function LineBox({ lines, disabled = false, hold = false, onActiveChange, onCaughtUp }: {
  lines: DisplayLine[];
  disabled?: boolean;
  hold?: boolean;
  onActiveChange: (index: number) => void;
  onCaughtUp: () => void;
}) {
  const regionRef = useRef<HTMLElement>(null);
  const logRef = useRef<HTMLDivElement>(null);
  const [doneCount, setDoneCount] = useState(0);
  const [typedChars, setTypedChars] = useState(0);
  const caughtRef = useRef(false);
  const linesRef = useRef(lines);
  const onCaughtUpRef = useRef(onCaughtUp);
  linesRef.current = lines;
  onCaughtUpRef.current = onCaughtUp;

  const typing = doneCount < lines.length;
  const activeIndex = lines.length === 0 ? 0 : typing ? doneCount : lines.length - 1;

  const markCaughtUp = useCallback(() => {
    if (caughtRef.current) return;
    caughtRef.current = true;
    onCaughtUpRef.current();
  }, []);

  const skipTyping = useCallback(() => {
    const total = linesRef.current.length;
    if (disabled || doneCount >= total) return;
    // 음성 보류 중에는 현재 줄까지만 완성한다(방송 줄을 넘기지 않는다). 아니면 남은 줄을 전부 보인다.
    if (hold) {
      setTypedChars(lineText(linesRef.current[doneCount]).length);
      return;
    }
    // 줄이 늘어난 직후 effect 전에 skip하면 caughtRef가 옛 true로 남아 onCaughtUp이 빠진다.
    caughtRef.current = false;
    setDoneCount(total);
    setTypedChars(0);
    markCaughtUp();
  }, [disabled, doneCount, hold, markCaughtUp]);

  useEffect(() => {
    onActiveChange(activeIndex);
  }, [activeIndex, onActiveChange]);

  useEffect(() => {
    if (typing || hold || lines.length === 0 || disabled) return;
    markCaughtUp();
  }, [typing, hold, lines.length, disabled, markCaughtUp]);

  useEffect(() => {
    if (doneCount < lines.length) caughtRef.current = false;
  }, [lines.length, doneCount]);

  useEffect(() => {
    if (!typing || disabled) return;
    const line = lines[doneCount];
    const full = line ? lineText(line) : "";
    if (prefersReducedMotion() && typedChars < full.length) {
      setTypedChars(full.length);
      return;
    }
    if (typedChars >= full.length) {
      // 관리자 방송 음성(hold) 중에는 현재 줄 타이핑만 끝내고 다음 줄로 넘기지 않는다.
      if (hold) return;
      const pause = window.setTimeout(() => {
        setDoneCount((count) => count + 1);
        setTypedChars(0);
      }, LINE_PAUSE_MS);
      return () => window.clearTimeout(pause);
    }
    const tick = window.setTimeout(() => setTypedChars((count) => count + 1), CHAR_MS);
    return () => window.clearTimeout(tick);
  }, [typing, disabled, hold, doneCount, typedChars, lines]);

  useEffect(() => {
    const log = logRef.current;
    if (!log) return;
    log.scrollTo({ top: log.scrollHeight });
  }, [doneCount, typedChars, lines.length]);

  useEffect(() => {
    if (disabled || !typing) return;
    const handleKey = (event: KeyboardEvent) => {
      if (event.defaultPrevented || event.isComposing || event.repeat || event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target;
      if (target instanceof HTMLElement) {
        if (target.closest('input, textarea, select, [contenteditable="true"], [role="dialog"]')) return;
      }
      if ([" ", "Enter", "Escape"].includes(event.key)) {
        event.preventDefault();
        skipTyping();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [disabled, typing, skipTyping]);

  const visible = lines.slice(0, Math.min(lines.length, doneCount + (typing ? 1 : 0)));

  return (
    <section ref={regionRef} role="region" aria-label="대사창" tabIndex={0} data-typing={typing ? "true" : "false"}
      className="flex min-h-0 flex-1 flex-col bg-transparent py-2 outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ink"
      onClick={(event) => {
        if ((event.target as HTMLElement).closest("button") || window.getSelection()?.toString()) return;
        if (!disabled && typing) skipTyping();
      }}>
      <div ref={logRef} className="mx-auto min-h-0 w-full max-w-3xl flex-1 overflow-y-auto px-4 sm:px-6" aria-live="polite" aria-atomic="false">
        <div className="flex flex-col gap-3 py-1">
          {visible.length > 0
            ? visible.map((line, index) => {
                const full = lineText(line);
                const isTyping = typing && index === doneCount && typedChars < full.length;
                const text = isTyping ? full.slice(0, typedChars) : full;
                return <ChatLine key={`${index}-${line.kind}-${line.text}`} line={line} text={text} typing={isTyping} hold={hold} />;
              })
            : <p data-line-kind="system" className="text-center text-base text-ink/60">장면을 살핀다.</p>}
        </div>
      </div>
    </section>
  );
}

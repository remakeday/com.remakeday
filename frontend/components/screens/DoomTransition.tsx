"use client";

import { useEffect, useRef, useState } from "react";
import type { NightClue, WorldOutcome } from "@/contracts/api";
import { doomImage, nightClueImage } from "@/lib/imageMap";
import { useVoice } from "@/components/VoicePlayer";
import { VOICE_CLIPS } from "@/lib/voiceMap";
import type { VoiceId } from "@/lib/voiceMap";

const OUTCOME_LINES: Record<WorldOutcome, string[]> = {
  truck: ["밤.", "트럭 소리.", "문이 열린다."],
  quiet: ["밤.", "복도가 조용하다.", "담요가 반듯하게 개어져 있다."],
  closure: ["밤.", "스피커가 켜진다.", VOICE_CLIPS.MA06.text],
};

/** 밤 방송(MA08~12) 파일이 실패하면 결말별 기존 방송으로 대체한다. 폐쇄는 MA05 뒤에 MA06이 이어진다 (밤단서 v2 P.1). */
const NIGHT_VOICE_FALLBACK: Record<WorldOutcome, VoiceId> = { truck: "MA04", quiet: "MA03", closure: "MA05" };

/** 치지직 띠 [top%, height%] — 쿠키 N.3: 높이 12~28%, 합쳐 45~60%, 피사체(중앙 1/3)가 든 띠를 포함한다. */
const BANDS: readonly (readonly [number, number])[] = [[14, 22], [42, 16], [66, 18]];
const VOICE_AT_MS = 800;
const GLITCH_MS = 1000;
const CAPTION_DELAY_MS = 300;
const BAND_OFF_STEP_MS = 120; // 띠가 하나씩 꺼진다
const IMAGE_GAP_MS = 360; // 2회차: 두 번째 그림 전에 바탕만 잠깐
const VOICE_STALL_MS = 6000; // 음원이 시작도 실패도 못 하면(네트워크 정체) 치지직을 그냥 시작한다

const isVoiceId = (id: string): id is VoiceId => id in VOICE_CLIPS;

/**
 * 멸망 전환 — world_outcome별 3종 + 밤 단서 시퀀스(밤단서 v2 P.2).
 * 바탕(결말 이미지) → 0.8초에 관리자 밤 방송 → 음원 중반에 치지직 1초(띠 안에만 단서 그림) → 0.3초 뒤 문장 → 띠가 꺼져도 문장은 남는다 → 탭.
 * 방송이 차단·꺼짐이면 치지직은 0.8초에 시작한다. 자동 진행은 없다.
 */
export function DoomTransition({
  outcome,
  clue,
  onDone,
}: {
  outcome: WorldOutcome | null;
  clue: NightClue | null;
  onDone: () => void;
}) {
  const { play: playVoice, stop: stopVoice } = useVoice();
  const [lineCount, setLineCount] = useState(0);
  const [glitch, setGlitch] = useState<{ src: string; lit: number } | null>(null);
  const [captionShown, setCaptionShown] = useState(false);
  const [ready, setReady] = useState(false);
  const replayClosure = useRef<(() => void) | null>(null);
  const lines = outcome ? OUTCOME_LINES[outcome] : ["밤."];
  const images = (clue?.image_ids ?? []).flatMap((id) => {
    const src = nightClueImage(id);
    return src ? [src] : [];
  });

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    const at = (ms: number, fn: () => void) => timers.push(setTimeout(fn, ms));
    let linesElapsed = false;
    let clueDone = !clue;
    let glitchStarted = false;
    const complete = () => { if (linesElapsed && clueDone) setReady(true); };

    const runGlitch = () => {
      if (glitchStarted || !clue) return;
      glitchStarted = true;
      let t = 0;
      images.forEach((src) => {
        at(t, () => setGlitch({ src, lit: BANDS.length }));
        BANDS.forEach((_, k) => at(t + GLITCH_MS + k * BAND_OFF_STEP_MS, () => setGlitch({ src, lit: BANDS.length - k - 1 })));
        t += GLITCH_MS + BANDS.length * BAND_OFF_STEP_MS + IMAGE_GAP_MS;
      });
      at(CAPTION_DELAY_MS, () => setCaptionShown(true));
      at(t, () => { setGlitch(null); clueDone = true; complete(); });
    };

    const startVoice = (ids: VoiceId[]) => {
      const [first] = ids;
      playVoice(ids, runGlitch, {
        onStart: (id, duration) => {
          if (id !== first) return;
          // 방송이 단서 단어를 말하는 중반(40~60%)에 맞춘다. 길이를 모르면 바로.
          at(Number.isFinite(duration) && duration > 0 ? duration * 500 : 0, runGlitch);
        },
        onFail: (id, reason) => {
          if (id !== first) return;
          const fallback = outcome && NIGHT_VOICE_FALLBACK[outcome];
          if (reason === "error" && fallback && id !== fallback) { startVoice([fallback, ...ids.slice(1)]); return; }
          runGlitch();
        },
      });
    };
    replayClosure.current = () => playVoice(["MA06"]);

    lines.forEach((_, i) => at(600 + i * 1100, () => setLineCount(i + 1)));
    at(4200, () => { linesElapsed = true; complete(); });
    const clueVoice = clue ? (isVoiceId(clue.voice_id) ? clue.voice_id : outcome && NIGHT_VOICE_FALLBACK[outcome]) : null;
    const ids: VoiceId[] = [...(clueVoice ? [clueVoice] : []), ...(outcome === "closure" ? (["MA06"] as VoiceId[]) : [])];
    at(VOICE_AT_MS, () => { if (ids.length) startVoice(ids); else runGlitch(); });
    at(VOICE_AT_MS + VOICE_STALL_MS, runGlitch);
    return () => { timers.forEach(clearTimeout); replayClosure.current = null; stopVoice(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-end overflow-hidden bg-void px-6 pb-24 text-paper">
      {outcome && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={doomImage(outcome)}
          alt=""
          className={`pointer-events-none absolute inset-0 h-full w-full ${outcome === "closure" ? "object-contain" : "object-cover"} ${
            outcome === "quiet" ? "fade-in-slow opacity-50" : "fade-in opacity-60"
          }`}
        />
      )}
      {/* 치지직 — 쿠키 N.3의 띠 연출(.cookie-glitch)을 결말 이미지 위에서 재생한다. 띠 안에만 단서 그림이 보인다. */}
      {glitch && BANDS.slice(0, glitch.lit).map(([top, height], k) => (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          key={k}
          src={glitch.src}
          alt=""
          data-night-band
          className="cookie-glitch pointer-events-none absolute inset-0 h-full w-full object-cover"
          style={{ clipPath: `inset(${top}% 0 ${100 - top - height}% 0)` }}
        />
      ))}
      {/* 하단 스크림 — 밝은 배경(문틈 빛 등) 위에서도 대사가 읽히게 */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-void via-void/70 to-transparent"
      />
      <div className="relative z-10 flex flex-col items-center gap-4 text-center [text-shadow:0_1px_10px_rgba(0,0,0,0.95)]">
        {lines.slice(0, lineCount).map((line, i) => (
          <p key={i} className="fade-in text-lg leading-relaxed">
            {line}
          </p>
        ))}
        {clue && (
          <p data-night-caption aria-live="polite" className={`min-h-[1.75em] text-xl leading-relaxed ${glitch ? "cookie-glitch-text" : ""}`}>
            {captionShown && <span className="block">{clue.caption}</span>}
            {captionShown && clue.outcome_line && <span className="block">{clue.outcome_line}</span>}
          </p>
        )}
        {ready && outcome === "closure" && (
          <button type="button" aria-label="관리자 대사 다시 듣기"
            onClick={() => replayClosure.current?.()} className="text-sm underline underline-offset-2 opacity-70">
            다시 듣기
          </button>
        )}
        {ready && (
          <button type="button" onClick={onDone} className="border border-paper/50 px-5 py-2 text-base">
            계속
          </button>
        )}
      </div>
    </div>
  );
}

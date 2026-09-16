"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { ReactNode, RefObject } from "react";
import { VOICE_CLIPS, voiceForLine } from "@/lib/voiceMap";
import type { VoiceId } from "@/lib/voiceMap";
import { audioEnabled, setAudioEnabled } from "@/lib/audioSettings";
import { ToggleSwitch } from "@/components/ToggleSwitch";

/** 재생 큐의 음원 단위 이벤트 — 화면 연출을 음원 길이에 맞추거나(밤 단서 치지직) 파일 실패 시 대체 음원으로 바꿀 때 쓴다. */
export interface PlayHooks {
  /** 음원이 실제로 재생되기 시작할 때. duration은 초 단위(메타데이터가 없으면 NaN) */
  onStart?: (id: VoiceId, duration: number) => void;
  /** 자동재생 차단(blocked) 또는 파일 오류(error)로 이 음원을 건너뛸 때 — 이어서 다음 음원으로 넘어간다 */
  onFail?: (id: VoiceId, reason: "blocked" | "error") => void;
}

interface VoiceControls {
  play: (ids: VoiceId[], onComplete?: () => void, hooks?: PlayHooks) => void;
  stop: () => void;
  enabled: boolean;
  toggle: () => void;
}

const VoiceContext = createContext<VoiceControls | null>(null);
const silent: VoiceControls = {
  play: (_ids, onComplete) => onComplete?.(),
  stop: () => {},
  enabled: true,
  toggle: () => {},
};
export const useVoice = () => useContext(VoiceContext) ?? silent;

/** 음성 토글 스위치 — VoicePlayer 안 어디든 배치할 수 있다. */
export function VoiceToggle({ className }: { className?: string }) {
  const voice = useContext(VoiceContext);
  if (!voice) return null;
  return (
    <ToggleSwitch label="음성" on={voice.enabled} onClick={voice.toggle} className={className} />
  );
}

/** 게임 전체에서 대사 한 개씩 재생하고, BGM의 재생 위치·켜기 선택은 유지한다. */
export function VoicePlayer({ children, bgmRef }: {
  children: ReactNode;
  bgmRef?: RefObject<HTMLAudioElement | null>;
}) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const queue = useRef<VoiceId[]>([]);
  const completion = useRef<(() => void) | undefined>(undefined);
  const hooks = useRef<PlayHooks | undefined>(undefined);
  const generation = useRef(0);
  const allowed = useRef(true);
  const [enabled, setEnabled] = useState(true);
  const [current, setCurrent] = useState<{ id: VoiceId; generation: number } | null>(null);
  const [speaking, setSpeaking] = useState(false);

  // 랜딩 환경설정의 음성 켜기/끄기를 초기값으로 읽는다.
  useEffect(() => {
    const on = audioEnabled("voice");
    allowed.current = on;
    setEnabled(on);
  }, []);

  const stop = useCallback(() => {
    generation.current++;
    queue.current = [];
    completion.current = undefined;
    hooks.current = undefined;
    audioRef.current?.pause();
    setCurrent(null);
    setSpeaking(false);
  }, []);

  const advance = useCallback(() => {
    const id = allowed.current ? queue.current.shift() : undefined;
    const token = ++generation.current;
    setCurrent(id ? { id, generation: token } : null);
    if (!id) {
      setSpeaking(false);
      const done = completion.current;
      completion.current = undefined;
      done?.();
    }
  }, []);

  const play = useCallback((ids: VoiceId[], onComplete?: () => void, playHooks?: PlayHooks) => {
    stop();
    if (!allowed.current) { onComplete?.(); return; }
    completion.current = onComplete;
    hooks.current = playHooks;
    queue.current = [...ids];
    advance();
  }, [advance, stop]);

  // 실패를 알린 뒤 다음 음원으로 — 훅 안에서 새 재생을 시작했다면(세대가 바뀜) 그 큐를 존중한다.
  const skip = useCallback((id: VoiceId, token: number, reason: "blocked" | "error") => {
    hooks.current?.onFail?.(id, reason);
    if (token === generation.current) advance();
  }, [advance]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !current) return;
    let active = true;
    // 자동재생 차단도 이 재생 시도를 끝낸다. 재청취는 대사 옆 버튼으로 한다.
    void audio.play().catch((error: unknown) => {
      if (!active || current.generation !== generation.current) return;
      const blocked = error instanceof DOMException && error.name === "NotAllowedError";
      skip(current.id, current.generation, blocked ? "blocked" : "error");
    });
    return () => {
      active = false;
      audio.pause();
    };
  }, [current, skip]);

  useEffect(() => {
    const bgm = bgmRef?.current;
    if (!bgm) return;
    const from = Math.min(bgm.volume, 0.25);
    bgm.volume = from;
    const to = speaking ? 0.07 : 0.25;
    const started = performance.now();
    let frame: number;
    const fade = (now: number) => {
      const progress = Math.min(Math.max((now - started) / 180, 0), 1); // rAF 타임스탬프가 시작 시각보다 앞서면 음수가 되어 상한을 넘긴다
      bgm.volume = from + (to - from) * progress;
      if (progress < 1) frame = requestAnimationFrame(fade);
      else bgm.volume = to;
    };
    frame = requestAnimationFrame(fade);
    return () => cancelAnimationFrame(frame);
  }, [speaking, bgmRef]);

  const toggle = useCallback(() => {
    allowed.current = !allowed.current;
    setEnabled(allowed.current);
    setAudioEnabled("voice", allowed.current);
    const done = completion.current;
    stop();
    done?.();
  }, [stop]);

  return (
    <VoiceContext.Provider value={{ play, stop, enabled, toggle }}>
      {children}
      <audio key={current?.generation ?? "idle"} ref={audioRef} data-audio="voice" preload="none"
        src={current ? `/audio/voice/${current.id}.mp3` : undefined}
        onPlay={() => { if (current?.generation === generation.current) setSpeaking(true); }}
        onPlaying={event => { if (current?.generation === generation.current) hooks.current?.onStart?.(current.id, event.currentTarget.duration); }}
        onEnded={() => { if (current?.generation === generation.current) advance(); }}
        onError={event => { if (current && current.generation === generation.current && event.currentTarget.error) skip(current.id, current.generation, "error"); }} />
      {/* BGM이 있는 화면(play)은 페이지가 우상단 컨테이너에 VoiceToggle을 직접 배치한다. */}
      {!bgmRef && <VoiceToggle className="fixed top-2 right-3 z-50" />}
    </VoiceContext.Provider>
  );
}

export function VoiceReplay({ speaker, text }: { speaker?: string; text: string }) {
  const voice = useContext(VoiceContext);
  const id = voiceForLine(speaker, text);
  if (!voice || !id) return null;
  return (
    <button type="button" aria-label={`${VOICE_CLIPS[id].speaker} 대사 다시 듣기`}
      onClick={() => voice.play([id])} className="mt-1 text-sm underline underline-offset-2 opacity-70">
      다시 듣기
    </button>
  );
}

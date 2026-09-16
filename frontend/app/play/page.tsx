"use client";

import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/contracts/api";
import type {
  CreateSessionRes,
  StartLoopRes,
  SubmitRes,
} from "@/contracts/api";
import { useApiAction } from "@/lib/useApiAction";
import { audioEnabled, setAudioEnabled } from "@/lib/audioSettings";
import { ToggleSwitch } from "@/components/ToggleSwitch";
import { ErrorToast } from "@/components/ErrorToast";
import { EntryScreen } from "@/components/screens/EntryScreen";
import { GuardScreen, type GuardKind } from "@/components/screens/GuardScreen";
import { MorningScreen } from "@/components/screens/MorningScreen";
import { DayScreen, type DialoguePair } from "@/components/screens/DayScreen";
import { NightScreen } from "@/components/screens/NightScreen";
import { ConfirmScreen } from "@/components/screens/ConfirmScreen";
import { ScoreScreen } from "@/components/screens/ScoreScreen";
import { DoomTransition } from "@/components/screens/DoomTransition";
import { GodScreen } from "@/components/screens/GodScreen";
import { ClearScreen } from "@/components/screens/ClearScreen";
import { VoicePlayer, VoiceToggle } from "@/components/VoicePlayer";

/**
 * 한 판 = 상태 머신. /play 한 라우트 안에서 phase 전환.
 *
 * entry → morning → day → night → confirm → score
 *   → doom_transition → (1~4회차) god → morning
 *   → doom_transition → (5회차, 점수 무관) clear → 개발 회고
 */
type Phase =
  | "entry"
  | "morning"
  | "day"
  | "night"
  | "confirm"
  | "score"
  | "doom_transition"
  | "god"
  | "clear";

/** sessionAction.failure를 만든 ApiError가 401/403/503/429 허들이면 해당 화면 종류로 매핑 */
function guardKindFor(error: ApiError): GuardKind | null {
  if (error.status === 401) return "login";
  if (error.status === 403 && error.code === "daily_attempt_limit") return "daily_limit";
  if (error.status === 503 && error.code === "daily_cap") return "daily_cap";
  if (error.status === 429) return "rate";
  return null;
}

export default function PlayPage() {
  const [phase, setPhase] = useState<Phase>("entry");
  const [attempt, setAttempt] = useState<CreateSessionRes | null>(null);
  const [loop, setLoop] = useState<StartLoopRes | null>(null);
  const [night, setNight] = useState<{
    nightId: string;
    claims: string[];
  } | null>(null);
  const [dayLog, setDayLog] = useState<DialoguePair[]>([]);
  const [submitResult, setSubmitResult] = useState<SubmitRes | null>(null);
  const [guard, setGuard] = useState<{ kind: GuardKind; retryAfter?: number } | null>(null);
  const lastSessionError = useRef<ApiError | null>(null);
  const bgmRef = useRef<HTMLAudioElement>(null);
  const bgmButtonRef = useRef<HTMLButtonElement>(null);
  const bgmAutoStart = useRef(true);
  const [bgmPlaying, setBgmPlaying] = useState(false);

  const sessionAction = useApiAction();
  const loopAction = useApiAction();
  const retryAction = useApiAction();

  useEffect(() => {
    const audio = bgmRef.current;
    if (!audio) return;
    // 랜딩 환경설정에서 BGM을 껐다면 자동재생하지 않는다.
    bgmAutoStart.current = audioEnabled("bgm");
    audio.volume = 0.25;
    const stopListening = () => {
      document.removeEventListener("click", onInteraction);
      document.removeEventListener("keydown", onInteraction);
    };
    const tryPlayback = () => {
      if (!bgmAutoStart.current) return;
      void audio.play().then(stopListening).catch(() => {});
    };
    const onInteraction = (event: Event) => {
      // 켜기·끄기 버튼의 선택을 자동재생 재시도로 뒤집지 않는다.
      if (bgmButtonRef.current?.contains(event.target as Node)) return;
      tryPlayback();
    };
    document.addEventListener("click", onInteraction);
    document.addEventListener("keydown", onInteraction);
    // 진입 즉시 시도하고, 브라우저가 막으면 첫 사용자 조작에서 재시도한다.
    tryPlayback();
    return () => {
      stopListening();
      audio.pause();
    };
  }, []);

  const playBgm = () => {
    const audio = bgmRef.current;
    if (!audio) return;
    // 재생 제한·음원 로딩 실패가 게임 진행을 막지 않게 한다.
    void audio.play().catch(() => {});
  };

  const toggleBgm = () => {
    const audio = bgmRef.current;
    if (!audio) return;
    bgmAutoStart.current = false;
    setAudioEnabled("bgm", audio.paused);
    if (audio.paused) playBgm();
    else audio.pause();
  };

  // 진입 시 세션 생성 — entry_lines는 이 응답에서 온다
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    void sessionAction.run(
      () =>
        api.createSession({}).catch((e: unknown) => {
          lastSessionError.current = e instanceof ApiError ? e : null;
          throw e;
        }),
      setAttempt,
      () => {
        const error = lastSessionError.current;
        const kind = error ? guardKindFor(error) : null;
        if (!kind) return false;
        setGuard({ kind, retryAfter: error?.retryAfter });
        return true; // 실패 배너 억제 — GuardScreen이 대신 보인다
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startLoop = () => {
    if (!attempt || loopAction.busy) return;
    void loopAction.run(
      () => api.startLoop(attempt.attempt_id),
      (res) => {
        setLoop(res);
        setNight(null);
        setDayLog([]);
        setSubmitResult(null);
        setPhase("morning");
      },
    );
  };

  const afterScore = () => {
    if (!submitResult) return;
    // 이해도와 무관하게 세계의 결말을 먼저 보여준다.
    setPhase("doom_transition");
  };

  const afterDoom = () => {
    if (submitResult?.is_final) setPhase("clear");
    else if (submitResult?.intervention_available) setPhase("god");
  };

  const retry = () => {
    if (!attempt || retryAction.busy) return;
    void retryAction.run(
      () => api.createSession({ prior_attempt_id: attempt.attempt_id }),
      (res) => {
        setAttempt(res);
        setLoop(null);
        setNight(null);
        setSubmitResult(null);
        setPhase("entry");
      },
    );
  };

  return (
    <main className="game-reading">
      <VoicePlayer bgmRef={bgmRef}>
      <audio
        ref={bgmRef}
        src="/audio/game-bgm.mp3"
        loop
        preload="none"
        onPlay={() => setBgmPlaying(true)}
        onPause={() => setBgmPlaying(false)}
        onError={() => setBgmPlaying(false)}
      />
      <div className="fixed top-2 right-3 z-50 flex items-center gap-5">
        <VoiceToggle />
        <ToggleSwitch label="BGM" on={bgmPlaying} onClick={toggleBgm} buttonRef={bgmButtonRef} />
      </div>
      {guard && <GuardScreen kind={guard.kind} retryAfter={guard.retryAfter} />}

      {phase === "entry" && !guard && (
        <EntryScreen
          lines={attempt?.entry_lines ?? null}
          priorCells={attempt?.prior_cell_results ?? null}
          loading={loopAction.busy}
          onBegin={startLoop}
        />
      )}

      {phase === "morning" && loop && (
        <MorningScreen
          morningText={loop.morning_text}
          aftermath={loop.aftermath ?? null}
          activeRules={loop.active_rules ?? []}
          budgetLeft={loop.budget_left}
          damageLevel={loop.damage_level}
          loopN={loop.loop_n}
          onContinue={() => setPhase("day")}
        />
      )}

      {phase === "day" && loop && (
        <DayScreen
          key={loop.loop_id}
          loopId={loop.loop_id}
          loopN={loop.loop_n}
          damageLevel={loop.damage_level}
          initialBeat={loop.beat}
          initialBeatTitle={loop.beat_title}
          initialNarration={loop.narration}
          initialBroadcast={loop.broadcast}
          initialAmbient={loop.ambient ?? null}
          initialIllustrations={loop.illustrations ?? []}
          initialObservations={loop.observations ?? []}
          initialBudget={loop.budget_left}
          onDayDone={(dialogue) => {
            setDayLog(dialogue);
            setPhase("night");
          }}
        />
      )}

      {phase === "night" && loop && (
        <NightScreen
          loopId={loop.loop_id}
          onDrafted={(nightId, claims) => {
            setNight({ nightId, claims });
            setPhase("confirm");
          }}
        />
      )}

      {phase === "confirm" && night && (
        <ConfirmScreen
          nightId={night.nightId}
          initialClaims={night.claims}
          dayLog={dayLog}
          onSubmitted={(result, finalClaims) => {
            setNight((current) => current ? { ...current, claims: finalClaims } : current);
            setSubmitResult(result);
            setPhase("score");
          }}
        />
      )}

      {phase === "score" && submitResult && (
        <ScoreScreen result={submitResult} onContinue={afterScore} />
      )}

      {phase === "doom_transition" && submitResult && (
        <DoomTransition
          outcome={submitResult.world_outcome}
          clue={submitResult.night_clue ?? null}
          onDone={afterDoom}
        />
      )}

      {phase === "god" && night && submitResult && (
        <GodScreen
          nightId={night.nightId}
          firstVisit={loop?.loop_n === 1}
          total={submitResult.total}
          hypothesis={night.claims[0] ?? ""}
          onRuleApplied={startLoop}
        />
      )}

      {phase === "clear" && submitResult && attempt && (
        <ClearScreen
          attemptId={attempt.attempt_id}
          result={submitResult}
          onRetry={retry}
          retryBusy={retryAction.busy}
        />
      )}

      <ErrorToast
        failure={
          sessionAction.failure ?? loopAction.failure ?? retryAction.failure
        }
        onClose={() => {
          sessionAction.clearFailure();
          loopAction.clearFailure();
          retryAction.clearFailure();
        }}
      />
      </VoicePlayer>
    </main>
  );
}

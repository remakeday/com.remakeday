"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { api, ApiError } from "@/contracts/api";
import type {
  CreateSessionRes,
  Observation,
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
import { Hud } from "@/components/hud/Hud";
import type { RecordAdvice } from "@/components/hud/RecordLog";
import { useLeaveWarning } from "@/lib/useLeaveWarning";

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

/** createSession 호출 하나를 감싸 401/403/503/429 허들을 GuardScreen으로 돌린다 (진입·재시작 공용). */
function runCreateSession(
  run: (
    fn: () => Promise<CreateSessionRes>,
    onOk: (value: CreateSessionRes) => void,
    onFail?: (status: number) => boolean,
  ) => Promise<boolean>,
  call: () => Promise<CreateSessionRes>,
  onOk: (value: CreateSessionRes) => void,
  setGuard: (guard: { kind: GuardKind; retryAfter?: number }) => void,
) {
  let captured: ApiError | null = null;
  return run(
    () =>
      call().catch((e: unknown) => {
        captured = e instanceof ApiError ? e : null;
        throw e;
      }),
    onOk,
    () => {
      const kind = captured ? guardKindFor(captured) : null;
      if (!kind) return false;
      setGuard({ kind, retryAfter: captured?.retryAfter });
      return true; // 실패 배너 억제 — GuardScreen이 대신 보인다
    },
  );
}

export default function PlayPage() {
  const [phase, setPhase] = useState<Phase>("entry");
  const [attempt, setAttempt] = useState<CreateSessionRes | null>(null);
  const [loop, setLoop] = useState<StartLoopRes | null>(null);
  const [night, setNight] = useState<{
    nightId: string;
    claims: string[];
    isQuestion: boolean[];
  } | null>(null);
  const [dayLog, setDayLog] = useState<DialoguePair[]>([]);
  const [submitResult, setSubmitResult] = useState<SubmitRes | null>(null);
  const [guard, setGuard] = useState<{ kind: GuardKind; retryAfter?: number } | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [advice, setAdvice] = useState<RecordAdvice[]>([]);
  const [activeRules, setActiveRules] = useState<string[]>([]);
  const [observationsLoading, setObservationsLoading] = useState(false);
  const [observationsError, setObservationsError] = useState<string | null>(null);
  const observationsRequest = useRef(0);
  const loopId = loop?.loop_id;
  const bgmRef = useRef<HTMLAudioElement>(null);
  const bgmButtonRef = useRef<HTMLButtonElement>(null);
  const bgmAutoStart = useRef(true);
  const [bgmPlaying, setBgmPlaying] = useState(false);

  const sessionAction = useApiAction();
  const loopAction = useApiAction();
  const retryAction = useApiAction();

  // 진입·회고(clear)를 제외한 진행 중 — 새로고침·탭 닫기 확인. 이어받기는 없다.
  useLeaveWarning(phase !== "entry" && phase !== "clear");

  const mergeObservations = useCallback((incoming: Observation[]) => {
    setObservations((previous) => {
      const byId = new Map(previous.map((item) => [item.observation_id, item]));
      for (const item of incoming) byId.set(item.observation_id, item);
      return [...byId.values()];
    });
  }, []);

  const addActiveRule = useCallback((label: string) => {
    setActiveRules((previous) => previous.includes(label) ? previous : [...previous, label]);
  }, []);

  // HUD와 밤 갤러리가 같은 목록을 쓴다. 지난 요청은 새 회차·판을 덮지 못한다.
  const refreshObservations = useCallback(async () => {
    if (!loopId) return;
    const request = ++observationsRequest.current;
    setObservationsLoading(true);
    setObservationsError(null);
    try {
      const res = await api.getObservations(loopId);
      if (request === observationsRequest.current) mergeObservations(res.observations);
    } catch (error) {
      if (request === observationsRequest.current) {
        setObservationsError(error instanceof ApiError ? error.detail : "잠시 뒤 다시 시도한다.");
      }
    } finally {
      if (request === observationsRequest.current) setObservationsLoading(false);
    }
  }, [loopId, mergeObservations]);

  useEffect(() => {
    void refreshObservations();
    return () => { observationsRequest.current += 1; };
  }, [refreshObservations]);

  // 화면이 바뀌면 창 스크롤을 맨 위로 — 긴 화면(신의 질문·밤)의 스크롤이 다음 화면에 남으면
  // 푸터 높이만큼 아래로 밀린 채 시작한다(테스터8 F1).
  useLayoutEffect(() => {
    window.scrollTo(0, 0);
  }, [phase]);

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
    void runCreateSession(sessionAction.run, () => api.createSession({}), setAttempt, setGuard);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startLoop = () => {
    if (!attempt || loopAction.busy) return;
    void loopAction.run(
      () => api.startLoop(attempt.attempt_id),
      (res) => {
        observationsRequest.current += 1;
        setLoop(res);
        mergeObservations(res.observations ?? []);
        setActiveRules(res.active_rules ?? []);
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
    void runCreateSession(
      retryAction.run,
      () => api.createSession({ prior_attempt_id: attempt.attempt_id }),
      (res) => {
        observationsRequest.current += 1;
        setAttempt(res);
        setLoop(null);
        setObservations([]);
        setAdvice([]);
        setActiveRules([]);
        setObservationsError(null);
        setObservationsLoading(false);
        setNight(null);
        setSubmitResult(null);
        setPhase("entry");
      },
      setGuard,
    );
  };

  const audioControls = <>
    <VoiceToggle />
    <ToggleSwitch label="BGM" on={bgmPlaying} onClick={toggleBgm} buttonRef={bgmButtonRef} />
  </>;

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
      {!guard ? <Hud key={attempt?.attempt_id ?? "entry"} loopN={loop?.loop_n ?? 1}
        observations={observations} advice={advice} activeRules={activeRules} loading={observationsLoading}
        error={observationsError} onRetry={() => { void refreshObservations(); }}>
        {audioControls}
      </Hud> : <div className="fixed top-2 right-3 z-50 flex items-center gap-5">{audioControls}</div>}
      <div className={guard ? undefined : "pt-14 [&_.min-h-dvh]:min-h-[calc(100dvh-3.5rem)]"}>
      {guard && <GuardScreen kind={guard.kind} retryAfter={guard.retryAfter} />}

      {phase === "entry" && !guard && (
        <EntryScreen
          lines={attempt?.entry_lines ?? null}
          priorCells={attempt?.prior_cell_results ?? null}
          loopN={loop?.loop_n ?? 1}
          loading={loopAction.busy}
          onBegin={startLoop}
        />
      )}

      {phase === "morning" && loop && !guard && (
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

      {phase === "day" && loop && !guard && (
        <DayScreen
          key={loop.loop_id}
          loopId={loop.loop_id}
          loopN={loop.loop_n}
          damageLevel={loop.damage_level}
          initialBeat={loop.beat}
          initialBeatTitle={loop.beat_title}
          initialLines={loop.lines}
          initialIllustrations={loop.illustrations ?? []}
          initialBudget={loop.budget_left}
          onObservationsChange={mergeObservations}
          onRuleApplied={addActiveRule}
          onDayDone={(dialogue) => {
            setDayLog(dialogue);
            setPhase("night");
          }}
        />
      )}

      {phase === "night" && loop && !guard && (
        <NightScreen
          loopId={loop.loop_id}
          observations={observations}
          observationsLoading={observationsLoading}
          onDrafted={(nightId, claims, isQuestion) => {
            setNight({ nightId, claims, isQuestion });
            setPhase("confirm");
          }}
        />
      )}

      {phase === "confirm" && night && !guard && (
        <ConfirmScreen
          nightId={night.nightId}
          initialClaims={night.claims}
          initialIsQuestion={night.isQuestion}
          dayLog={dayLog}
          onSubmitted={(result, finalClaims) => {
            setNight((current) => current ? { ...current, claims: finalClaims } : current);
            setSubmitResult(result);
            void refreshObservations();
            setPhase("score");
          }}
        />
      )}

      {phase === "score" && submitResult && !guard && (
        <ScoreScreen result={submitResult} onContinue={afterScore} />
      )}

      {phase === "doom_transition" && submitResult && !guard && (
        <DoomTransition
          outcome={submitResult.world_outcome}
          clue={submitResult.night_clue ?? null}
          onDone={afterDoom}
        />
      )}

      {phase === "god" && night && submitResult && !guard && (
        <GodScreen
          nightId={night.nightId}
          firstVisit={loop?.loop_n === 1}
          total={submitResult.total}
          hypothesis={night.claims[0] ?? ""}
          initialSuggestedQuestions={submitResult.suggested_questions}
          onAdvice={(text) => {
            if (!loop) return;
            setAdvice((previous) => previous.some((item) => item.loop_n === loop.loop_n && item.text === text)
              ? previous : [...previous, { id: `${night.nightId}:advice-${previous.length}`, loop_n: loop.loop_n, text }]);
          }}
          onRuleApplied={(label) => {
            if (label) addActiveRule(label);
            startLoop();
          }}
        />
      )}

      {phase === "clear" && submitResult && attempt && !guard && (
        <ClearScreen
          attemptId={attempt.attempt_id}
          result={submitResult}
          onRetry={retry}
          retryBusy={retryAction.busy}
        />
      )}
      </div>

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

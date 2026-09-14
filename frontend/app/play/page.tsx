"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/contracts/api";
import type {
  CreateSessionRes,
  StartLoopRes,
  SubmitRes,
} from "@/contracts/api";
import { useApiAction } from "@/lib/useApiAction";
import { ErrorToast } from "@/components/ErrorToast";
import { EntryScreen } from "@/components/screens/EntryScreen";
import { MorningScreen } from "@/components/screens/MorningScreen";
import { DayScreen, type DialoguePair } from "@/components/screens/DayScreen";
import { NightScreen } from "@/components/screens/NightScreen";
import { ConfirmScreen } from "@/components/screens/ConfirmScreen";
import { ScoreScreen } from "@/components/screens/ScoreScreen";
import { DoomTransition } from "@/components/screens/DoomTransition";
import { GodScreen } from "@/components/screens/GodScreen";
import { ClearScreen } from "@/components/screens/ClearScreen";

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

  const sessionAction = useApiAction();
  const loopAction = useApiAction();
  const retryAction = useApiAction();

  // 진입 시 세션 생성 — entry_lines는 이 응답에서 온다
  const booted = useRef(false);
  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    void sessionAction.run(() => api.createSession({}), setAttempt);
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
      {phase === "entry" && (
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
          onDone={afterDoom}
        />
      )}

      {phase === "god" && night && submitResult && (
        <GodScreen
          nightId={night.nightId}
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
    </main>
  );
}

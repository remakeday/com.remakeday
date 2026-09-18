"use client";

import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { api } from "@/contracts/api";
import type { DamageLevel, Illustration, Line, Npc, Observation, PawOffer } from "@/contracts/api";
import { useApiAction } from "@/lib/useApiAction";
import { voicesForLines } from "@/lib/voiceMap";
import { ErrorToast } from "@/components/ErrorToast";
import { useVoice } from "@/components/VoicePlayer";
import { AskBar } from "@/components/day/AskBar";
import { DialogueStage } from "@/components/day/DialogueStage";
import { LineBox } from "@/components/day/LineBox";
import { PawPopup } from "@/components/day/PawPopup";
import { SceneIntro } from "@/components/day/SceneIntro";
import { dayModeReducer, initialDayMode } from "@/components/day/dayMode";

interface PendingUtterance {
  loopId: string;
  target: string;
  text: string;
  requestId: string;
}

/** 낮의 문답 한 쌍 — 밤 채점 대기 회상용 */
export interface DialoguePair {
  q: string;
  npc: string;
  a: string;
}

const BEAT_WAIT_LINES = ["스피커가 지직거린다…", "복도 끝에서 발소리.", "형광등이 깜빡인다.", "누군가 자리를 옮긴다."];

function systemLine(text: string): Line {
  return { kind: "system", speaker: null, text, image_id: null, voice_id: null, observation_id: null };
}

/** 하루 전체 줄을 누적한다. 장면 전환·입력 잠금·API 처리는 여기서만 정한다. */
export function DayScreen({
  loopId, loopN, damageLevel, initialBeat, initialBeatTitle, initialLines,
  initialIllustrations, initialBudget, onObservationsChange, onRuleApplied, onDayDone,
}: {
  loopId: string;
  loopN: number;
  damageLevel: DamageLevel;
  initialBeat: number;
  initialBeatTitle: string;
  initialLines: Line[];
  initialIllustrations: Illustration[];
  initialBudget: number;
  onObservationsChange: (observations: Observation[]) => void;
  onRuleApplied: (label: string) => void;
  onDayDone: (dialogue: DialoguePair[]) => void;
}) {
  const { play: playVoice, stop: stopVoice } = useVoice();
  const [mode, dispatchMode] = useReducer(dayModeReducer, initialDayMode);
  const [todayLines, setTodayLines] = useState(initialLines);
  const [cursor, setCursor] = useState(0);
  const [beat, setBeat] = useState(initialBeat);
  const [beatTitle, setBeatTitle] = useState(initialBeatTitle);
  const [illustrations, setIllustrations] = useState(initialIllustrations);
  const [illustrationIndex, setIllustrationIndex] = useState(0);
  const [budgetLeft, setBudgetLeft] = useState(initialBudget);
  const [npcs, setNpcs] = useState<Npc[]>([]);
  const [npcsBeat, setNpcsBeat] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [pawOffer, setPawOffer] = useState<PawOffer | null>(null);
  const [dayDone, setDayDone] = useState(false);
  const [pendingUtterance, setPendingUtterance] = useState<PendingUtterance | null>(null);
  const [beatWaitIdx, setBeatWaitIdx] = useState(0);
  const [hasAsked, setHasAsked] = useState(false);

  const utterance = useApiAction();
  const beatAction = useApiAction();
  const pawAction = useApiAction();
  const { run: runNpcAction, busy: npcsBusy } = useApiAction();
  const mutationInFlight = useRef(false);
  const acceptedUtterances = useRef(new Set<string>());
  const dialogue = useRef<DialoguePair[]>([]);
  const npcRefreshId = useRef(0);
  const pawChoice = useRef(false);

  const appendLines = (lines: Line[]) => {
    if (lines.length === 0) return;
    setTodayLines((previous) => [...previous, ...lines]);
    setCursor(todayLines.length); // 새 응답의 첫 줄부터 읽는다.
  };

  const currentLine = todayLines[cursor];
  useEffect(() => {
    const index = illustrations.findIndex((item) => item.image_id === currentLine?.image_id);
    if (index >= 0) setIllustrationIndex(index);
  }, [currentLine, illustrations]);

  // 관리자 방송만 현재 줄에 맞춰 재생한다. 인물 음성 보류는 그대로다.
  useEffect(() => {
    if (currentLine?.kind === "broadcast") {
      playVoice(voicesForLines(currentLine.text.split("\n").map((text) => ({ name: "관리자", text }))));
    }
    return () => stopVoice();
  }, [currentLine, playVoice, stopVoice]);

  const refreshNpcs = useCallback((forBeat: number) => {
    const refreshId = ++npcRefreshId.current;
    void runNpcAction(
      () => api.getNpcs(loopId),
      (res) => {
        if (refreshId !== npcRefreshId.current) return;
        setNpcs(res.npcs);
        setNpcsBeat(forBeat);
        setSelected((current) => current && res.npcs.some((npc) => npc.code === current) ? current : res.npcs[0]?.code ?? null);
      },
      () => true, // 다음 장면에서 다시 확인한다.
    );
  }, [loopId, runNpcAction]);

  useEffect(() => { refreshNpcs(initialBeat); }, [initialBeat, refreshNpcs]);

  useEffect(() => {
    if (!beatAction.busy) return;
    setBeatWaitIdx(0);
    const timer = setInterval(() => setBeatWaitIdx((index) => (index + 1) % BEAT_WAIT_LINES.length), 1500);
    return () => clearInterval(timer);
  }, [beatAction.busy]);

  const reachedEnd = useCallback(() => {
    dispatchMode({ type: "reached_end", hasPawOffer: pawOffer !== null });
  }, [pawOffer]);
  const previousLine = useCallback(() => setCursor((index) => Math.max(0, index - 1)), []);
  const nextLine = useCallback(() => setCursor((index) => Math.min(todayLines.length - 1, index + 1)), [todayLines.length]);
  const showAll = useCallback(() => setCursor(Math.max(0, todayLines.length - 1)), [todayLines.length]);

  const npcsReady = npcsBeat === beat;
  const selectedNpc = npcs.find((npc) => npc.code === selected);
  const selectedUttered = selectedNpc?.uttered ?? false;
  const mutationBusy = utterance.busy || beatAction.busy || pawAction.busy;
  const questionUnresolved = pendingUtterance !== null;
  // 마지막 줄 판정은 한 곳에 둔다. 질문과 장면 이동이 같은 잠금을 쓴다.
  const atLastLine = cursor >= todayLines.length - 1;
  const controlsLocked = !atLastLine || mode.mode !== "dialogue" || mode.pawOpen || mutationBusy || questionUnresolved;
  const inputLocked = controlsLocked || dayDone || budgetLeft <= 0 || !npcsReady || selectedUttered || !selected;

  const clearMutationFailures = () => {
    utterance.clearFailure();
    beatAction.clearFailure();
    pawAction.clearFailure();
  };

  const submitUtterance = (question: PendingUtterance) => {
    if (mutationInFlight.current) return;
    mutationInFlight.current = true;
    clearMutationFailures();
    void utterance.run(
      () => api.sendUtterance(question.loopId, { target: question.target, text: question.text, request_id: question.requestId }),
      (res) => {
        setPendingUtterance(null);
        const utteranceId = res.utterance_id ?? question.requestId;
        if (acceptedUtterances.current.has(utteranceId)) return;
        acceptedUtterances.current.add(utteranceId);
        setHasAsked(true);
        appendLines(res.lines);
        // 무의미 입력의 대체 문장은 system 줄로만 보이고, 밤의 인물 회상에는 넣지 않는다.
        if (!res.gated) dialogue.current.push({ q: question.text, npc: res.npc.name, a: res.reply });
        setBudgetLeft(res.budget_left);
        setBeat(res.beat);
        setNpcs((previous) => previous.map((npc) => npc.code === res.npc.code ? res.npc : npc));
        onObservationsChange(res.observations ?? []);
      },
      (status, code) => {
        // 처리 중·응답 유실은 같은 request_id로 다시 보낸다. 확정 거절만 입력을 돌려놓는다.
        if (status >= 400 && status < 500 && code !== "request_in_flight") {
          setPendingUtterance(null);
          setInput(question.text);
        }
        return false;
      },
    ).finally(() => { mutationInFlight.current = false; });
  };

  const send = () => {
    const text = input.trim();
    if (!text || !selected || inputLocked || mutationInFlight.current) return;
    const question = { loopId, target: selected, text, requestId: crypto.randomUUID() };
    setInput("");
    setPendingUtterance(question);
    submitUtterance(question);
  };

  const advanceBeat = () => {
    if (dayDone || controlsLocked || mutationInFlight.current) return;
    mutationInFlight.current = true;
    stopVoice();
    clearMutationFailures();
    void beatAction.run(
      () => api.nextBeat(loopId),
      (res) => {
        if (typeof res.budget_left === "number") setBudgetLeft(res.budget_left);
        onObservationsChange(res.observations ?? []);
        appendLines(res.lines);
        if (res.day_done) {
          setDayDone(true);
          return;
        }
        setBeat(res.beat);
        setBeatTitle(res.beat_title);
        setIllustrations(res.illustrations ?? []);
        setIllustrationIndex(0);
        setPawOffer(res.paw_offer);
        dispatchMode({ type: "next_scene" });
        refreshNpcs(res.beat);
      },
    ).finally(() => { mutationInFlight.current = false; });
  };

  const respondPaw = (accept: boolean) => {
    if (!pawOffer || mutationInFlight.current || questionUnresolved) return;
    mutationInFlight.current = true;
    pawChoice.current = accept;
    clearMutationFailures();
    void pawAction.run(
      () => api.respondPaw(loopId, { offer_id: pawOffer.offer_id, accept }),
      (res) => {
        const notice = res.applied && res.rule_label
          ? [systemLine(`규칙이 걸렸다 — ${res.rule_label}`)]
          : !accept ? [systemLine("원숭이손의 제안을 거절했다.")] : [];
        appendLines([...notice, ...res.lines]);
        const wishImages = res.illustrations ?? [];
        if (wishImages.length > 0) {
          setIllustrationIndex(illustrations.length);
          setIllustrations((previous) => [...previous, ...wishImages]);
        }
        onObservationsChange(res.observations ?? []);
        if (res.applied && res.rule_label) onRuleApplied(res.rule_label);
        setPawOffer(null);
        dispatchMode({ type: "paw_resolved", hasScene: res.lines.length > 0 || wishImages.length > 0 });
      },
    ).finally(() => { mutationInFlight.current = false; });
  };

  const hint = beatAction.busy ? BEAT_WAIT_LINES[beatWaitIdx]
    : utterance.busy ? "답변을 기다리는 중…"
    : !atLastLine ? "대사를 끝까지 읽거나 ‘모두 보기’를 누른다."
    : dayDone ? "하루가 끝났다. 밤에 오늘의 추리를 쓴다."
    : budgetLeft <= 0 ? "오늘 대화를 모두 썼다. 다음 장면은 계속 볼 수 있다."
    : questionUnresolved ? "보낸 질문의 답변을 확인한 뒤 이어서 대화할 수 있다."
    : !npcsReady ? npcsBusy ? "이 장면의 인물 상태를 확인하는 중이다." : "인물 상태를 확인하지 못했다. 다음 장면에서 다시 확인할 수 있다."
    : selectedUttered ? "이 인물과는 이 장면에서 대화했다. 다른 인물을 고르거나 다음 장면으로 간다."
    : loopN === 1 && !hasAsked ? "인물을 고르고 질문을 쓴다. 질문마다 대화 한 칸을 쓴다."
    : "한 장면에 인물마다 한 번 묻는다. 장면 이동은 무료다.";
  const placeholder = !atLastLine ? "마지막 대사까지 읽는다"
    : dayDone ? "하루가 끝났다"
    : budgetLeft <= 0 ? "오늘은 더 말할 수 없다"
    : !npcsReady ? "인물 상태를 확인해야 한다"
    : selectedUttered ? "다른 인물을 고른다"
    : selectedNpc ? `${selectedNpc.name}에게 말한다` : "…";
  const stages = {
    intro: <SceneIntro beat={beat} damageLevel={damageLevel} illustrations={illustrations} index={illustrationIndex}
      disabled={mutationBusy || mode.pawOpen} onSelect={setIllustrationIndex} />,
    dialogue: <DialogueStage npcs={npcs} selected={selected} ready={npcsReady} disabled={mutationBusy || questionUnresolved}
      dayDone={dayDone} budgetLeft={budgetLeft} onSelect={setSelected} />,
  };

  return (
    <div className="h-[calc(100dvh-3.5rem)] w-full overflow-hidden bg-paper text-ink">
      <div inert={mode.pawOpen ? true : undefined} aria-hidden={mode.pawOpen ? true : undefined}
        className="flex h-full min-h-0 flex-col" data-day-mode={mode.mode}>
        <div className="shrink-0 px-4 py-1">
          <p className="text-base">{beatTitle} · 장면 {beat}/6</p>
          <div className="flex items-center gap-2 text-sm">
            <span>남은 대화 횟수</span>
            <div role="meter" aria-label="남은 대화 횟수" aria-valuemin={0} aria-valuemax={initialBudget} aria-valuenow={budgetLeft}
              aria-valuetext={`${initialBudget}칸 중 ${budgetLeft}칸`} className="flex shrink-0 gap-1 py-1">
              {Array.from({ length: initialBudget }, (_, index) => (
                <span key={index} aria-hidden="true" className={`h-5 w-2.5 origin-bottom border border-ink transition-[background-color,opacity,transform] duration-300 motion-reduce:transition-none ${index < budgetLeft ? "scale-y-100 bg-ink opacity-100" : "scale-y-75 bg-transparent opacity-30"}`} />
              ))}
            </div>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-x-hidden overflow-y-auto">{stages[mode.mode]}</div>
        {/* 화면 높이 안에서 그림만 스크롤하고, 대사창·입력줄은 하단에 남긴다. */}
        <div className="z-10 shrink-0 bg-paper pb-[env(safe-area-inset-bottom)]">
          <LineBox lines={todayLines} cursor={cursor} disabled={mutationBusy || mode.pawOpen}
            onPrevious={previousLine} onNext={nextLine} onShowAll={showAll} onReachedEnd={reachedEnd} />
          <AskBar input={input} onInput={setInput} onAsk={send} onNext={advanceBeat}
            inputLocked={inputLocked} nextLocked={controlsLocked}
            waitingReply={utterance.busy} waitingBeat={beatAction.busy} hint={hint} placeholder={placeholder}
            failure={utterance.failure?.message}
            onRetry={pendingUtterance && !mutationBusy ? () => submitUtterance(pendingUtterance) : undefined}
            dayDone={dayDone} onNight={() => {
              // 5일째 트럭 방송 단서(9b)는 이 하루 끝 연결 지점 앞에 둔다.
              if (dayDone && !controlsLocked) onDayDone(dialogue.current);
            }} />
        </div>
      </div>
      {mode.pawOpen && pawOffer && <PawPopup offer={pawOffer} busy={mutationBusy} onRespond={respondPaw} />}
      <ErrorToast failure={beatAction.failure ? { ...beatAction.failure, retry: advanceBeat }
        : pawAction.failure ? { ...pawAction.failure, retry: () => respondPaw(pawChoice.current) } : null}
        onClose={() => { beatAction.clearFailure(); pawAction.clearFailure(); }} />
    </div>
  );
}

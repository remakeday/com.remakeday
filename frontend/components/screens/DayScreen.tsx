"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/contracts/api";
import type { AmbientUtterance, DamageLevel, Illustration, Npc, Observation, PawOffer } from "@/contracts/api";
import {
  beatImage,
  clueImage,
  damageClass,
  npcImage,
  MANAGER_IMAGE,
  PAW_IMAGE,
} from "@/lib/imageMap";
import { useApiAction } from "@/lib/useApiAction";
import { dedupeByText } from "@/lib/dedupeByText";
import { ErrorToast } from "@/components/ErrorToast";
import { TypingIndicator } from "@/components/TypingIndicator";
import { GameplayGuide } from "@/components/GameplayGuide";
import { ObservationCard } from "@/components/ObservationCard";
import { useVoice, VoiceReplay } from "@/components/VoicePlayer";
import { voiceForLine, voicesForLines } from "@/lib/voiceMap";
import type { VoiceId } from "@/lib/voiceMap";

interface ChatEntry {
  id: number;
  role: "user" | "npc" | "ambient" | "narration" | "broadcast" | "system";
  text: string;
  speaker?: string;
  delivery?: "pending" | "sent" | "failed";
}

interface PendingUtterance {
  loopId: string;
  target: string;
  text: string;
  requestId: string;
  entryId: number;
}

/** 낮의 문답 한 쌍 — 밤 채점 대기 회상용 */
export interface DialoguePair {
  q: string;
  npc: string;
  a: string;
}

type Popup =
  | { kind: "broadcast"; text: string }
  | { kind: "paw"; offer: PawOffer };

let entrySeq = 0;
const nextId = () => ++entrySeq;

/** 비트 경계 대기 중 순환하는 일시 연출 라인 — 로그에 남기지 않는다 */
const BEAT_WAIT_LINES = [
  "스피커가 지직거린다…",
  "복도 끝에서 발소리.",
  "형광등이 깜빡인다.",
  "누군가 자리를 옮긴다.",
];

/**
 * 대화 (하루) — 6비트. NPC와 대화(발화 예산), 비트 넘기기는 공짜.
 * 헤더 이미지는 시나리오의 현재 비트 이미지 ID로 결정된다 (LLM 출력 무관).
 */
export function DayScreen({
  loopId,
  loopN,
  damageLevel,
  initialBeat,
  initialBeatTitle,
  initialNarration,
  initialBroadcast,
  initialAmbient,
  initialIllustrations,
  initialObservations,
  initialBudget,
  onDayDone,
}: {
  loopId: string;
  loopN: number;
  damageLevel: DamageLevel;
  initialBeat: number;
  initialBeatTitle: string;
  initialNarration: string;
  initialBroadcast: string | null;
  initialAmbient: AmbientUtterance | null;
  initialIllustrations: Illustration[];
  initialObservations: Observation[];
  initialBudget: number;
  onDayDone: (dialogue: DialoguePair[]) => void;
}) {
  const { play: playVoice, stop: stopVoice } = useVoice();
  const ambientVoices = useRef<VoiceId[]>(voicesForLines(initialAmbient?.lines ?? []));
  const [beat, setBeat] = useState(initialBeat);
  const [beatTitle, setBeatTitle] = useState(initialBeatTitle);
  const [illustrations, setIllustrations] = useState(initialIllustrations);
  const [illustrationIndex, setIllustrationIndex] = useState(0);
  const [observations, setObservations] = useState(initialObservations);
  const shownObservations = dedupeByText(observations, (item) => `${item.actor ?? ""}\n${item.text}`);
  const [notebookOpen, setNotebookOpen] = useState(false);
  const [openObservation, setOpenObservation] = useState<Observation | null>(null);
  const [budgetLeft, setBudgetLeft] = useState(initialBudget);
  const [npcs, setNpcs] = useState<Npc[]>([]);
  const [npcsBeat, setNpcsBeat] = useState<number | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [log, setLog] = useState<ChatEntry[]>(() => {
    const first: ChatEntry[] = [
      { id: nextId(), role: "narration", text: initialNarration },
    ];
    for (const line of initialAmbient?.lines ?? []) {
      first.push({ id: nextId(), role: "ambient", text: line.text, speaker: line.name });
    }
    return first;
  });
  const [input, setInput] = useState("");
  const [popups, setPopups] = useState<Popup[]>(() =>
    initialBroadcast ? [{ kind: "broadcast", text: initialBroadcast }] : [],
  );
  const [dayDone, setDayDone] = useState(false);
  const [waitingReply, setWaitingReply] = useState(false);
  const [pendingUtterance, setPendingUtterance] = useState<PendingUtterance | null>(null);
  const [beatWaitIdx, setBeatWaitIdx] = useState(0);
  const [hasAsked, setHasAsked] = useState(false);

  const utterance = useApiAction();
  const beatAction = useApiAction();
  const pawAction = useApiAction();
  const npcAction = useApiAction();
  const observationAction = useApiAction();

  const logRef = useRef<HTMLDivElement>(null);
  const notebookRef = useRef<HTMLDivElement>(null);
  const sourceDetailRef = useRef<HTMLDivElement>(null);
  const notebookReturnFocus = useRef<HTMLElement | null>(null);
  const sourceDetailReturnFocus = useRef<HTMLElement | null>(null);
  const sourceDetailOpen = useRef(false);
  const mutationInFlight = useRef(false);
  const acceptedUtterances = useRef(new Set<string>());
  const npcRefreshId = useRef(0);
  const pawChoice = useRef(false);

  const pushLog = useCallback((entry: Omit<ChatEntry, "id">) => {
    setLog((prev) => [...prev, { ...entry, id: nextId() }]);
  }, []);

  const voicePopup = popups[0];
  useEffect(() => {
    if (voicePopup?.kind === "broadcast") {
      const clips = voicesForLines(voicePopup.text.split("\n").map((text) => ({ name: "관리자", text })));
      playVoice(clips);
    } else if (!voicePopup && ambientVoices.current.length > 0) {
      playVoice(ambientVoices.current);
    }
  }, [beat, voicePopup, playVoice]);

  useEffect(() => () => stopVoice(), [stopVoice]);

  const refreshNpcs = useCallback((forBeat: number) => {
    const refreshId = ++npcRefreshId.current;
    void npcAction.run(
      () => api.getNpcs(loopId),
      (res) => {
        if (refreshId !== npcRefreshId.current) return;
        setNpcs(res.npcs);
        setNpcsBeat(forBeat);
        setSelected((cur) => {
          if (cur && res.npcs.some((n) => n.code === cur)) return cur;
          return res.npcs[0]?.code ?? null;
        });
      },
      () => true, // NPC 목록 실패는 조용히 (다음 비트에서 재시도)
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loopId]);

  useEffect(() => {
    refreshNpcs(initialBeat);
  }, [initialBeat, refreshNpcs]);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [log, waitingReply, beatAction.busy]);

  // 비트 경계 대기 연출 — busy 동안 1.5초 간격 순환, 완료 시 제거
  useEffect(() => {
    if (!beatAction.busy) return;
    setBeatWaitIdx(0);
    const timer = setInterval(
      () => setBeatWaitIdx((i) => (i + 1) % BEAT_WAIT_LINES.length),
      1500,
    );
    return () => clearInterval(timer);
  }, [beatAction.busy]);

  const currentPopup = popups[0] ?? null;
  const npcsReady = npcsBeat === beat;
  const selectedUttered = npcs.find((n) => n.code === selected)?.uttered ?? false;
  const mutationBusy = waitingReply || beatAction.busy || pawAction.busy;
  const questionUnresolved = pendingUtterance !== null;
  const illustration = illustrations[illustrationIndex];
  const illustrationSrc = illustration ? clueImage(illustration.image_id) : null;

  useEffect(() => {
    if (!notebookOpen) return;
    notebookRef.current?.querySelector<HTMLElement>("button")?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        if (sourceDetailOpen.current) setOpenObservation(null);
        else setNotebookOpen(false);
        return;
      }
      if (event.key !== "Tab") return;
      const scope = sourceDetailOpen.current ? sourceDetailRef.current : notebookRef.current;
      const focusable = [...(scope?.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])') ?? [])];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
      requestAnimationFrame(() => notebookReturnFocus.current?.focus());
    };
  }, [notebookOpen]);

  useEffect(() => {
    sourceDetailOpen.current = openObservation !== null;
    if (openObservation) sourceDetailRef.current?.querySelector<HTMLElement>("button")?.focus();
    else if (notebookOpen) sourceDetailReturnFocus.current?.focus();
  }, [openObservation]);

  const openNotebook = () => {
    notebookReturnFocus.current = document.activeElement as HTMLElement | null;
    setNotebookOpen(true);
    void observationAction.run(
      () => api.getObservations(loopId),
      (res) => setObservations(res.observations),
    );
  };

  const clearMutationFailures = () => {
    utterance.clearFailure();
    beatAction.clearFailure();
    pawAction.clearFailure();
  };

  const submitUtterance = (question: PendingUtterance) => {
    if (mutationInFlight.current) return;
    mutationInFlight.current = true;
    clearMutationFailures();
    setWaitingReply(true);
    setLog((previous) => previous.map((entry) => entry.id === question.entryId ? { ...entry, delivery: "pending" } : entry));
    void utterance.run(
      () => api.sendUtterance(question.loopId, { target: question.target, text: question.text, request_id: question.requestId }),
      (res) => {
        setPendingUtterance(null);
        const utteranceId = res.utterance_id ?? question.requestId;
        if (acceptedUtterances.current.has(utteranceId)) return;
        acceptedUtterances.current.add(utteranceId);
        setHasAsked(true);
        setLog((previous) => previous.map((entry) => entry.id === question.entryId ? { ...entry, delivery: "sent" } : entry));
        pushLog({ role: "npc", text: res.reply, speaker: res.npc.name });
        const clip = voiceForLine(res.npc.name, res.reply);
        if (clip) playVoice([clip]);
        setBudgetLeft(res.budget_left);
        setBeat(res.beat);
        setNpcs((prev) =>
          prev.map((n) => (n.code === res.npc.code ? res.npc : n)),
        );
        setObservations((previous) => {
          const byId = new Map(previous.map((item) => [item.observation_id, item]));
          for (const item of res.observations ?? []) byId.set(item.observation_id, item);
          return [...byId.values()];
        });
      },
      (status) => {
        setLog((previous) => previous.map((entry) => entry.id === question.entryId ? { ...entry, delivery: "failed" } : entry));
        if (status >= 400 && status < 500) {
          setPendingUtterance(null);
          setInput(question.text);
        }
        return false;
      },
    ).finally(() => {
      mutationInFlight.current = false;
      setWaitingReply(false);
    });
  };

  const send = () => {
    const text = input.trim();
    if (!text || !selected || mutationInFlight.current || questionUnresolved || dayDone) return;
    if (currentPopup !== null || budgetLeft <= 0 || !npcsReady || selectedUttered) return;
    const question = { loopId, target: selected, text, requestId: crypto.randomUUID(), entryId: nextId() };
    setInput("");
    setPendingUtterance(question);
    setLog((previous) => [...previous, { id: question.entryId, role: "user", text, delivery: "pending" }]);
    submitUtterance(question);
  };

  const advanceBeat = () => {
    if (dayDone || mutationInFlight.current || questionUnresolved || currentPopup !== null) return;
    mutationInFlight.current = true;
    stopVoice();
    clearMutationFailures();
    void beatAction.run(
      () => api.nextBeat(loopId),
      (res) => {
        setBeat(res.beat);
        setBeatTitle(res.beat_title);
        setIllustrations(res.illustrations ?? []);
        setIllustrationIndex(0);
        if (typeof res.budget_left === "number") setBudgetLeft(res.budget_left);
        setObservations((previous) => {
          const byId = new Map(previous.map((item) => [item.observation_id, item]));
          for (const item of res.observations ?? []) byId.set(item.observation_id, item);
          return [...byId.values()];
        });
        pushLog({ role: "narration", text: res.narration });
        // 백엔드가 새 필드를 아직 안 줄 수 있다 — undefined 안전 접근
        const ambient = res.ambient ?? null;
        ambientVoices.current = voicesForLines(ambient?.lines ?? []);
        for (const line of ambient?.lines ?? []) {
          pushLog({ role: "ambient", text: line.text, speaker: line.name });
        }
        const noteFound = res.note_found ?? null;
        if (noteFound) {
          pushLog({
            role: "system",
            text: "단서 기록에 새 내용을 저장했다.",
          });
        }
        const newPopups: Popup[] = [];
        if (res.broadcast)
          newPopups.push({ kind: "broadcast", text: res.broadcast });
        if (res.paw_offer) newPopups.push({ kind: "paw", offer: res.paw_offer });
        if (newPopups.length > 0) setPopups((p) => [...p, ...newPopups]);
        if (res.day_done) setDayDone(true);
        refreshNpcs(res.beat);
      },
    ).finally(() => { mutationInFlight.current = false; });
  };

  const respondPaw = (offer: PawOffer, accept: boolean) => {
    if (mutationInFlight.current || questionUnresolved) return;
    mutationInFlight.current = true;
    pawChoice.current = accept;
    clearMutationFailures();
    void pawAction.run(
      () => api.respondPaw(loopId, { offer_id: offer.offer_id, accept }),
      (res) => {
        if (res.applied && res.rule_label) {
          pushLog({
            role: "system",
            text: `규칙이 걸렸다 — ${res.rule_label}`,
          });
        } else if (!accept) {
          pushLog({ role: "system", text: "원숭이손의 제안을 거절했다." });
        }
        setPopups((p) => p.slice(1));
      },
    ).finally(() => { mutationInFlight.current = false; });
  };

  const canNight = dayDone && popups.length === 0;

  return (
    <div className="h-dvh w-full overflow-x-hidden overflow-y-auto bg-paper">
    <div
      className="relative flex h-full min-h-[44rem] w-full flex-col bg-paper text-ink"
    >
      <details inert={notebookOpen ? true : undefined} aria-hidden={notebookOpen ? true : undefined} className="relative z-20 shrink-0 border-b border-ink/20 px-4 py-1">
        <summary className="w-fit cursor-pointer text-base">플레이 안내</summary>
        <div className="absolute top-full right-0 left-0 max-h-[65dvh] overflow-y-auto border-b border-ink/30 bg-paper p-5 shadow-lg">
          <GameplayGuide />
        </div>
      </details>
      {/* 상단 — 장면 그림. 손상 효과는 이미지에만 적용한다. */}
      <div inert={notebookOpen ? true : undefined} aria-hidden={notebookOpen ? true : undefined} className="flex min-h-0 w-full flex-[2] flex-col bg-paper sm:flex-[11]">
        <div className="relative min-h-0 flex-1 overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          key={`${beat}-${illustrationIndex}`}
          src={illustrationSrc ?? beatImage(beat)}
          alt={illustrationSrc ? illustration.caption : ""}
          className={`fade-in mx-auto h-full w-auto max-w-full object-contain py-1 ${damageClass(damageLevel)} ${
            damageLevel >= 3 ? "opacity-80" : ""
          }`}
        />
        </div>
        <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 px-4 py-2">
          <span className="text-base">{beatTitle} · {beat}/6</span>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="text-sm text-ink">본 행동·들은 말 다시 보기</span>
          <button
            type="button"
            onClick={openNotebook}
            className="inline-flex cursor-pointer items-center gap-2 border border-ink bg-ink px-3 py-1 text-base text-paper hover:bg-ink/90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink"
            aria-label="단서 기록 열기"
            aria-haspopup="dialog"
          >
            단서 기록 열기 <span>{shownObservations.length}건</span><span aria-hidden="true">→</span>
          </button>

        </div>
        </div>
        {illustrationSrc && (
          <div className="shrink-0 border-t border-ink/10 px-4 py-2 text-center">
            <p className="text-base leading-relaxed sm:text-lg" aria-live="polite">
              {illustration.caption}
            </p>
            {illustrations.length > 1 && (
              <div className="mt-2 flex items-center justify-center gap-4 text-base">
                <button
                  type="button"
                  disabled={illustrationIndex === 0 || currentPopup !== null || beatAction.busy}
                  onClick={() => setIllustrationIndex((i) => i - 1)}
                  className="border border-ink/30 px-3 py-1 disabled:opacity-30"
                >
                  이전 그림
                </button>
                <span>{illustrationIndex + 1} / {illustrations.length}</span>
                <button
                  type="button"
                  disabled={illustrationIndex === illustrations.length - 1 || currentPopup !== null || beatAction.busy}
                  onClick={() => setIllustrationIndex((i) => i + 1)}
                  className="border border-ink/30 px-3 py-1 disabled:opacity-30"
                >
                  다음 그림
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 하단 밴드 — 좌: 캐릭터 카드 / 우: 대사·채팅 */}
      <div inert={notebookOpen ? true : undefined} aria-hidden={notebookOpen ? true : undefined} className="flex min-h-0 flex-[3] flex-col overflow-hidden border-t border-ink/20 sm:flex-[9] sm:flex-row">
      {/* 좌 — 인물 선택 카드 */}
      <div className="flex h-28 w-full shrink-0 items-start gap-2 overflow-x-auto border-b border-ink/20 p-2 sm:h-auto sm:w-auto sm:gap-3 sm:border-r sm:border-b-0 sm:p-3">
        {npcs.length === 0 && (
          <span className="self-center px-3 text-base opacity-40">…</span>
        )}
        {npcs.map((n) => {
          const portrait = npcImage(n.code, n.mood);
          const active = selected === n.code;
          const status = dayDone ? "하루 종료" : budgetLeft <= 0 ? "오늘 대화 소진" : !npcsReady ? "인물 확인 중" : n.uttered ? "이 장면 대화 완료" : "대화 가능";
          return (
            <button
              key={n.code}
              type="button"
              onClick={() => setSelected(n.code)}
              disabled={mutationBusy || questionUnresolved || currentPopup !== null}
              aria-pressed={active}
              aria-label={`${n.name} · ${status}`}
              className={`flex w-24 shrink-0 flex-col items-center gap-1 border p-1 text-base sm:w-24 ${
                active
                  ? "border-ink bg-ink text-paper"
                  : "border-ink/30 hover:border-ink"
              }`}
            >
              {portrait ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={portrait}
                  alt=""
                  className="h-10 min-h-0 w-full object-cover object-top sm:h-auto sm:aspect-[3/4]"
                />
              ) : (
                <span className="min-h-0 w-full flex-1 bg-ink/20" />
              )}
              <span className="shrink-0">
                {n.name}
              </span>
              <span className="text-base">{status}</span>
            </button>
          );
        })}
      </div>

      {/* 우 — 대사·채팅 패널 */}
      <div className="flex min-h-0 flex-1 flex-col">
      <div ref={logRef} className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
        <div className="flex w-full flex-col gap-3">
          {log.map((e) => {
            if (e.role === "narration")
              return (
                <p
                  key={e.id}
                  className="fade-in text-base leading-relaxed whitespace-pre-line text-ink"
                >
                  {e.text}
                </p>
              );
            if (e.role === "system")
              return (
                <p
                  key={e.id}
                  className="fade-in text-center text-base text-ink/75"
                  role="status"
                >
                  {e.text}
                </p>
              );
            if (e.role === "ambient")
              // 지나가며 흘린 말 — NPC 말풍선보다 옅게 (점선 테두리)
              return (
                <div key={e.id} className="fade-in max-w-[85%] self-start opacity-80">
                  {e.speaker && (
                    <span className="text-base opacity-50">{e.speaker}</span>
                  )}
                  <p className="border border-dashed border-ink/30 px-3 py-2 text-base leading-relaxed whitespace-pre-line">
                    {e.text}
                  </p>
                  <VoiceReplay speaker={e.speaker} text={e.text} />
                </div>
              );
            if (e.role === "broadcast")
              return (
                <div
                  key={e.id}
                  className="fade-in border-l-2 border-orange pl-3 text-base whitespace-pre-line"
                >
                  {e.text}
                  {e.text.split("\n").map((text, i) => <VoiceReplay key={i} speaker="관리자" text={text} />)}
                </div>
              );
            const mine = e.role === "user";
            return (
              <div
                key={e.id}
                className={`fade-in max-w-[85%] ${mine ? "self-end text-right" : "self-start"}`}
              >
                {!mine && e.speaker && (
                  <span className="text-base opacity-50">{e.speaker}</span>
                )}
                <p
                  className={`border px-3 py-2 text-base leading-relaxed whitespace-pre-line ${
                    mine ? "border-ink bg-ink text-paper" : "border-ink/30"
                  }`}
                >
                  {e.text}
                </p>
                {!mine && <VoiceReplay speaker={e.speaker} text={e.text} />}
                {mine && e.delivery !== "sent" && (
                  <span className="text-sm opacity-70" role="status">
                    {e.delivery === "pending" ? "답변을 기다리는 중…" : "답변을 받지 못했다."}
                  </span>
                )}
              </div>
            );
          })}
          {waitingReply && (
            <div className="self-start border border-ink/30 px-3 py-2">
              <TypingIndicator />
            </div>
          )}
          {beatAction.busy && (
            // 비트 경계 대기 연출 — 일시 표시, 로그에 남지 않는다
            <p
              key={beatWaitIdx}
              className="fade-in text-center text-base italic opacity-40"
            >
              {BEAT_WAIT_LINES[beatWaitIdx]}
            </p>
          )}
          {canNight && (
            <button
              type="button"
              onClick={() => {
                // 유저 발언 바로 뒤의 NPC 답변만 짝으로 (에러로 답이 없으면 건너뜀)
                const pairs: DialoguePair[] = [];
                log.forEach((e, i) => {
                  const next = log[i + 1];
                  if (e.role === "user" && e.delivery === "sent" && next?.role === "npc")
                    pairs.push({ q: e.text, npc: next.speaker ?? "", a: next.text });
                });
                onDayDone(pairs);
              }}
              className="fade-in mx-auto mt-4 border border-ink px-6 py-2 text-lg hover:bg-ink hover:text-paper"
            >
              밤이 온다
            </button>
          )}
        </div>
      </div>

      {/* 입력부 */}
      <div className="grid shrink-0 grid-cols-[minmax(0,1fr)_auto] gap-x-2 border-t border-ink/20 px-3 py-2">
        <div className="col-span-2 mb-2 flex flex-wrap items-center justify-between gap-2">
          <span className="text-base" aria-live="polite">오늘 남은 대화 {budgetLeft}회</span>
          <span className="text-base opacity-70">{loopN}일째 · 하루 공용</span>
        </div>
        {!dayDone && (
          <p className="col-span-2 mb-2 text-base opacity-75" id="conversation-hint">
            {budgetLeft <= 0 ? "오늘 대화를 모두 썼다. 다음 장면과 단서 기록은 계속 볼 수 있다."
              : questionUnresolved ? "보낸 질문의 답변을 확인한 뒤 이어서 대화할 수 있다."
              : !npcsReady ? npcAction.busy ? "이 장면의 인물 상태를 확인하는 중이다." : "인물 상태를 확인하지 못했다. 다음 장면에서 다시 확인할 수 있다."
              : selectedUttered ? "이 인물과는 이 장면에서 대화했다. 다른 인물을 고르거나 다음 장면으로 간다."
              : loopN === 1 && !hasAsked ? "인물을 고르고 질문을 쓴다. 전송하면 오늘 대화 1회를 쓴다."
              : "한 장면에 인물마다 한 번 물을 수 있다. 질문마다 오늘 대화 1회를 쓴다."}
          </p>
        )}
        {utterance.failure && (
          <p className="col-span-2 mb-2 text-base" role="alert">{utterance.failure.message}</p>
        )}
        {pendingUtterance && !waitingReply && (
          <button
            type="button"
            onClick={() => submitUtterance(pendingUtterance)}
            className="col-span-2 mb-2 justify-self-start border border-ink px-3 py-2 text-base hover:bg-ink hover:text-paper"
          >
            같은 질문 다시 보내기
          </button>
        )}
        <div className="col-span-2 flex min-w-0 w-full items-center gap-2 sm:col-span-1">
          <input
            aria-label="인물에게 질문"
            aria-describedby={dayDone ? undefined : "conversation-hint"}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              // 한글 IME Enter 가드 — compositionend 전 Enter 중복 전송 방지
              if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                e.preventDefault();
                send();
              }
            }}
            disabled={
              currentPopup !== null ||
              mutationBusy ||
              questionUnresolved ||
              dayDone ||
              budgetLeft <= 0 ||
              !npcsReady ||
              selectedUttered ||
              selected === null
            }
            placeholder={
              currentPopup !== null
                ? "방송이 나오는 중이다 — 먼저 듣는다"
                : dayDone
                  ? "하루가 끝났다"
                  : budgetLeft <= 0
                    ? "오늘은 더 말할 수 없다"
                    : !npcsReady
                      ? "인물 상태를 확인해야 한다"
                      : selectedUttered
                        ? "다른 인물을 고르거나 다음 장면으로 간다"
                        : selected
                          ? `${npcs.find((n) => n.code === selected)?.name ?? ""}에게 말한다`
                          : "…"
            }
            className="min-w-0 flex-1 border border-ink/40 bg-transparent px-3 py-2 text-lg outline-none placeholder:opacity-40 focus:border-ink disabled:opacity-40"
          />
          <button
            type="button"
            onClick={send}
            disabled={
              currentPopup !== null ||
              mutationBusy ||
              questionUnresolved ||
              dayDone ||
              budgetLeft <= 0 ||
              !npcsReady ||
              selectedUttered ||
              !input.trim() ||
              selected === null
            }
            className="shrink-0 border border-ink px-3 py-2 text-lg hover:bg-ink hover:text-paper disabled:opacity-30"
          >
            말한다
          </button>
        </div>
        <div className="col-span-2 mt-2 flex flex-wrap items-center justify-between gap-2 sm:col-span-1 sm:mt-0">
          <span className="text-base opacity-70 sm:hidden">장면 이동 무료 · 대화 충전 없음</span>
          <button
            type="button"
            onClick={advanceBeat}
            disabled={dayDone || mutationBusy || questionUnresolved || currentPopup !== null}
            className="shrink-0 border border-ink/40 px-3 py-2 text-lg hover:border-ink disabled:opacity-30"
            title="다음 장면 (무료, 대화 횟수는 충전되지 않음)"
          >
            {beatAction.busy ? "…" : "다음 장면"}
          </button>
        </div>
      </div>
      </div>
      </div>

      {/* 관리자 방송 팝업 — 검은 배경, 모노톤 */}
      {currentPopup?.kind === "broadcast" && (
        <div className="fade-in fixed inset-0 z-40 flex items-center justify-center bg-void/90 px-6">
          <div className="flex w-full max-w-sm flex-col items-center gap-6 text-center text-paper">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={MANAGER_IMAGE}
              alt=""
              className="aspect-square w-40 object-cover"
            />
            <p className="text-lg leading-relaxed whitespace-pre-line">
              {currentPopup.text}
            </p>
            {currentPopup.text.split("\n").map((text, i) => <VoiceReplay key={i} speaker="관리자" text={text} />)}
            <button
              type="button"
              onClick={() => {
                stopVoice();
                pushLog({ role: "broadcast", text: currentPopup.text });
                setPopups((p) => p.slice(1));
              }}
              className="border border-paper/50 px-6 py-2 text-lg hover:bg-paper hover:text-void"
            >
              …
            </button>
          </div>
        </div>
      )}

      {/* 원숭이손 팝업 */}
      {currentPopup?.kind === "paw" && (
        <div className="fade-in fixed inset-0 z-40 flex items-center justify-center bg-void/90 px-6">
          <div className="flex w-full max-w-sm flex-col items-center gap-5 text-center text-paper">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={PAW_IMAGE}
              alt=""
              className="aspect-square w-40 object-cover"
            />
            <p className="text-lg opacity-70">무언가가 굴러왔다.</p>
            <p className="text-base leading-relaxed">
              {currentPopup.offer.rule_label}
            </p>
            {currentPopup.offer.shown_reason && (
              <p className="text-base leading-relaxed text-orange">
                {currentPopup.offer.shown_reason}
              </p>
            )}
            <div className="flex gap-4">
              <button
                type="button"
                disabled={mutationBusy || questionUnresolved}
                onClick={() => respondPaw(currentPopup.offer, true)}
                className="border border-orange px-6 py-2 text-lg text-orange hover:bg-orange hover:text-void disabled:opacity-40"
              >
                받는다
              </button>
              <button
                type="button"
                disabled={mutationBusy || questionUnresolved}
                onClick={() => respondPaw(currentPopup.offer, false)}
                className="border border-paper/50 px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-40"
              >
                제안을 거절한다
              </button>
            </div>
          </div>
        </div>
      )}

      {notebookOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-paper/95 px-4 py-6 text-ink" role="dialog" aria-modal="true" aria-label="단서 기록">
          <div ref={notebookRef} inert={openObservation ? true : undefined} aria-hidden={openObservation ? true : undefined} className="mx-auto flex w-full max-w-3xl flex-col gap-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg">단서 기록</h2>
                <p className="mt-1 text-base opacity-70">본 행동과 들은 말을 다시 살펴보고, 밤의 추리에 단서로 사용한다.</p>
                <p className="text-base opacity-50">기록을 열어도 대화 횟수는 줄지 않는다. 인물이 한 말의 진위는 직접 판단한다.</p>
              </div>
              <button type="button" onClick={() => { setOpenObservation(null); setNotebookOpen(false); }} className="shrink-0 border border-ink px-3 py-2 text-base" aria-label="단서 기록 닫기">닫기</button>
            </div>
            {observationAction.busy && <p role="status" className="text-lg opacity-60">관찰 기록을 펼치는 중…</p>}
            <div className="grid gap-3 sm:grid-cols-2">
              {shownObservations.map((item) => <ObservationCard key={item.observation_id} observation={item} compact onOpen={(observation) => { sourceDetailReturnFocus.current = document.activeElement as HTMLElement | null; setOpenObservation(observation); }} />)}
            </div>
            {!observationAction.busy && shownObservations.length === 0 && <p className="text-lg opacity-60">아직 출처가 연결된 관찰이 없다.</p>}
            <button type="button" onClick={() => { setOpenObservation(null); setNotebookOpen(false); }} className="self-center border border-ink px-6 py-2 text-base" aria-label="단서 기록 닫기">닫기</button>
          </div>
        </div>
      )}

      {openObservation && (
        <div ref={sourceDetailRef} className="fixed inset-0 z-[60] flex items-center justify-center bg-void/85 px-4 py-8 text-paper" role="dialog" aria-modal="true" aria-label={`${openObservation.scene_title} 원본 장면`}>
          <div className="max-h-full w-full max-w-2xl overflow-y-auto bg-void p-4">
            <ObservationCard observation={openObservation} />
            <button type="button" onClick={() => setOpenObservation(null)} className="mt-4 w-full border border-paper/50 px-4 py-2 text-lg">원본 장면 닫기</button>
          </div>
        </div>
      )}

      <ErrorToast
        failure={beatAction.failure
          ? { ...beatAction.failure, retry: advanceBeat }
          : pawAction.failure
            ? { ...pawAction.failure, retry: () => { if (currentPopup?.kind === "paw") respondPaw(currentPopup.offer, pawChoice.current); } }
            : null}
        onClose={() => {
          beatAction.clearFailure();
          pawAction.clearFailure();
          observationAction.clearFailure();
        }}
      />
    </div>
    </div>
  );
}

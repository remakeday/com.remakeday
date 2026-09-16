"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/contracts/api";
import type { GodAnswer, GodOption, Observation, QuestionStatus, RulePreview } from "@/contracts/api";
import { useApiAction } from "@/lib/useApiAction";
import { ErrorToast } from "@/components/ErrorToast";
import { TypingIndicator } from "@/components/TypingIndicator";
import { ObservationCard } from "@/components/ObservationCard";
import { useVoice, VoiceReplay } from "@/components/VoicePlayer";
import { VOICE_CLIPS } from "@/lib/voiceMap";

interface QA {
  question: string;
  answer: GodAnswer;
  verdict: string;
  detail: string | null;
  status: QuestionStatus;
  evidence: Observation[];
  nextObservation: string | null;
}

const STATUS_LABEL: Record<QuestionStatus, string> = {
  supported: "근거와 일치한다",
  contradicted: "기록과 모순된다",
  unknown: "아직 확인되지 않았다",
};

/** 다음 하루 대기 중 흘리는 세계 힌트 — 무심코 읽으면 풍경, 잘 읽으면 답이다 */
const WORLD_HINTS = [
  "방송은 이름을 부르지 않는다. 머릿수를 센다.",
  "트럭은 무언가를 싣고 온 적이 없다 — 실어 갈 뿐이다.",
  "손목의 번호는 이름보다 먼저 있었다.",
  "밥을 남기는 건 이곳에서 눈에 띄는 일이다.",
  "이송된 사람이 돌아온 적은 없다.",
  "소독약 냄새는 아침마다 새로 깔린다.",
];

function WorldHintDrip() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((v) => (v + 1) % WORLD_HINTS.length), 2800);
    return () => clearInterval(t);
  }, []);
  return (
    <p key={i} className="fade-in text-lg leading-relaxed text-orange">
      {WORLD_HINTS[i]}
    </p>
  );
}

/**
 * 신의개입 — 어두운 화면. 질문 3회(짧은 대화와 선택해서 보는 근거) → 규칙 선택(3개 + 직접 쓰기).
 * 배경은 J01의 정신 — 순검정 + 흰 수평선 (CSS로 그린다).
 */
export function GodScreen({
  nightId,
  firstVisit,
  total,
  hypothesis,
  onRuleApplied,
}: {
  nightId: string;
  firstVisit: boolean;
  total: number;
  hypothesis: string;
  onRuleApplied: () => void;
}) {
  const { play: playVoice, stop: stopVoice } = useVoice();
  useEffect(() => {
    if (firstVisit) playVoice(["AD01"]);
    return stopVoice;
  }, [firstVisit, playVoice, stopVoice]);
  const [stage, setStage] = useState<"questions" | "rule">("questions");
  const [qas, setQas] = useState<QA[]>([]);
  const [remaining, setRemaining] = useState(3);
  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState<GodOption[] | null>(null);
  const [customText, setCustomText] = useState("");
  const [preview, setPreview] = useState<RulePreview | null>(null);
  const [ruleFailure, setRuleFailure] = useState<{
    reason: string | null;
    conflicts: string[];
  } | null>(null);
  const [appliedLabel, setAppliedLabel] = useState<string | null>(null);

  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [questionFocused, setQuestionFocused] = useState(false);

  const askAction = useApiAction();
  const optionsAction = useApiAction();
  const ruleAction = useApiAction();
  const previewAction = useApiAction();

  const qaLogRef = useRef<HTMLDivElement>(null);
  const questionRef = useRef<HTMLInputElement>(null);
  const questionPlaceholders = [
    hypothesis ? `예: “${hypothesis.slice(0, 28)}”을 확인할 기록은?` : "예: 내 주장을 확인할 기록은?",
    qas.at(-1)?.nextObservation ? `예: ${qas.at(-1)?.nextObservation}` : "예: 아직 모르는 이유를 어디서 확인해?",
    "예: 이 발언과 직접 본 사실은 어떻게 달라?",
  ];

  // 로그는 높이 제한 없이 쌓이고 페이지가 스크롤된다 — 새 항목이 보이도록 끌어온다
  useEffect(() => {
    qaLogRef.current?.lastElementChild?.scrollIntoView({ block: "nearest" });
  }, [qas, askAction.busy]);

  // 답이 오면 바로 다음 질문을 칠 수 있게 (포커스 스크롤은 막아 새 답이 보이는 위치를 유지)
  useEffect(() => {
    if (qas.length > 0) questionRef.current?.focus({ preventScroll: true });
  }, [qas.length]);

  // 질문 예시 순환 — 포커스 중에는 멈춘다
  useEffect(() => {
    if (questionFocused) return;
    const timer = setInterval(
      () =>
        setPlaceholderIdx((i) => (i + 1) % 3),
      3000,
    );
    return () => clearInterval(timer);
  }, [questionFocused]);

  const ask = () => {
    const text = question.trim();
    if (!text || remaining <= 0 || askAction.busy) return;
    setQuestion("");
    void askAction.run(
      () => api.askGod(nightId, { text }),
      (res) => {
        setQas((prev) => [
          ...prev,
          { question: text, answer: res.answer, verdict: res.verdict, detail: res.detail, status: res.status, evidence: res.evidence ?? [], nextObservation: res.next_observation },
        ]);
        setRemaining(res.remaining);
      },
    );
  };

  const requestPreview = () => {
    if (!customText.trim() || previewAction.busy) return;
    setRuleFailure(null);
    void previewAction.run(
      () => api.previewRule(nightId, { custom_text: customText }),
      setPreview,
    );
  };

  const loadOptions = () => {
    void optionsAction.run(
      () => api.getGodOptions(nightId),
      (res) => setOptions(res.options),
    );
  };

  useEffect(() => {
    if (stage === "rule" && options === null) loadOptions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage]);

  const chooseRule = (choice: "1" | "2" | "3" | "custom") => {
    if (ruleAction.busy) return;
    setRuleFailure(null);
    void ruleAction.run(
      () =>
        api.chooseRule(
          nightId,
          choice === "custom"
            ? { choice, custom_text: customText, preview_id: preview?.preview_id }
            : { choice },
        ),
      (res) => {
        if (res.ok) {
          setAppliedLabel(res.rule_label ?? "규칙");
          onRuleApplied();
        } else {
          setRuleFailure({ reason: res.reason, conflicts: res.conflicts });
        }
      },
    );
  };

  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-y-auto bg-void px-4 py-12 text-white">
      {/* J01 — 흰 수평선 하나. 아래 1/3 지점 */}
      <div
        aria-hidden
        className="pointer-events-none fixed right-0 left-0 h-px bg-white"
        style={{ bottom: "33.3%" }}
      />

      {/* bg-void — 수평선(J01)이 콘텐츠 텍스트를 가로지르지 않게 뒤로 숨긴다 */}
      <div className="fade-in-slow relative z-10 flex w-full max-w-xl flex-col gap-6 bg-void px-4 py-4">
        <p className="text-center text-lg leading-relaxed">
          이해도 {Math.round(total)}%. 오늘의 세계는 멸망했습니다.
          <br />낮 대화와 별도로 3회 질문할 수 있습니다.
        </p>
        {firstVisit && (
          <div className="text-center text-base leading-relaxed">
            <p>{VOICE_CLIPS.AD01.text}</p>
            <VoiceReplay speaker="조언자" text={VOICE_CLIPS.AD01.text} />
          </div>
        )}

        {/* 질문 로그 — 긴 답이 잘리지 않게 높이 제한 없이 쌓는다 */}
        <div ref={qaLogRef} className="flex flex-col gap-4">
          {qas.map((qa, i) => (
            <div key={i} className="fade-in flex flex-col gap-1">
              <p className="text-lg opacity-60">— {qa.question}</p>
              <p className="text-lg">
                <span className="text-orange">{qa.verdict}</span>{" "}
                {qa.answer.startsWith(qa.verdict) ? qa.answer.slice(qa.verdict.length).trim() : qa.answer}
              </p>
              {qa.nextObservation && (
                <p className="border-l-2 border-orange pl-3 text-base opacity-80">{qa.nextObservation}</p>
              )}
              {(qa.evidence.length > 0 || qa.detail) && (
                <details className="text-lg">
                  <summary className="cursor-pointer py-1 text-base opacity-60">근거 보기{qa.evidence.length > 0 ? ` · ${qa.evidence.length}개` : ""}</summary>
                  <div className="mt-2 flex flex-col gap-2">
                    <p className="text-base text-orange">{STATUS_LABEL[qa.status]}</p>
                    {qa.evidence.length === 0 && qa.detail && <p className="opacity-70">{qa.detail}</p>}
                    {qa.evidence.slice(0, 2).map((item) => <ObservationCard key={item.observation_id} observation={item} compact />)}
                  </div>
                </details>
              )}
            </div>
          ))}
          {askAction.busy && <TypingIndicator />}
        </div>

        {stage === "questions" && (
          <>
            {remaining > 0 ? (
              <div className="flex flex-wrap items-center gap-2">
                <p className="w-full text-base opacity-80">이 목소리는 오늘 일어난 일만 안다. 무엇을 했는지 물어라.</p>
                <p className="w-full text-sm tracking-wide opacity-60">맞다 · 아니다 · 그런 일은 없었다 · 그건 알 수 없다</p>
                <span className="w-full text-base opacity-70">
                  남은 질문 {remaining}
                </span>
                <input
                  aria-label="밤의 질문"
                  ref={questionRef}
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                      e.preventDefault();
                      ask();
                    }
                  }}
                  onFocus={() => setQuestionFocused(true)}
                  onBlur={() => setQuestionFocused(false)}
                  disabled={askAction.busy}
                  placeholder={questionPlaceholders[placeholderIdx]}
                  className="min-w-0 flex-1 border border-white/40 bg-transparent px-3 py-2 text-lg outline-none placeholder:opacity-40 focus:border-white disabled:opacity-40"
                />
                <button
                  type="button"
                  onClick={ask}
                  disabled={askAction.busy || !question.trim()}
                  className="shrink-0 border border-white px-4 py-2 text-lg hover:bg-white hover:text-void disabled:opacity-30"
                >
                  묻는다
                </button>
              </div>
            ) : (
              <p className="text-center text-lg opacity-60">
                더 물을 수 없다.
              </p>
            )}
            <button
              type="button"
              onClick={() => setStage("rule")}
              className="mx-auto border border-white/60 px-8 py-2 text-lg hover:border-white hover:bg-white hover:text-void"
            >
              규칙을 고른다
            </button>
          </>
        )}

        {stage === "rule" && appliedLabel !== null && (
          <div className="fade-in flex flex-col items-center gap-3">
            <p className="text-lg opacity-70">세계에 규칙이 걸렸다.</p>
            <p className="border border-white/40 px-4 py-3 text-lg leading-relaxed">
              {appliedLabel}
            </p>
            <WorldHintDrip />
            <p className="animate-pulse text-base tracking-widest opacity-50">
              규칙을 적용해 다음 하루를 준비하는 중…
            </p>
          </div>
        )}

        {stage === "rule" && appliedLabel === null && (
          <div className="flex flex-col gap-4">
            <p className="text-center text-lg opacity-70">
              내일에 규칙 하나를 건다.
            </p>
            {options === null ? (
              <p className="text-center text-lg opacity-40">
                {optionsAction.failure ? (
                  <button
                    type="button"
                    onClick={loadOptions}
                    className="underline"
                  >
                    선택지를 다시 불러온다
                  </button>
                ) : (
                  <span className="animate-pulse">
                    세계가 규칙 후보를 고르는 중…
                  </span>
                )}
              </p>
            ) : (
              <>
                {options.map((opt) => (
                  <button
                    key={opt.index}
                    type="button"
                    aria-label={opt.label}
                    disabled={ruleAction.busy}
                    onClick={() =>
                      chooseRule(String(opt.index) as "1" | "2" | "3")
                    }
                    className="border border-white/40 px-4 py-3 text-left text-lg leading-relaxed hover:border-white disabled:opacity-40"
                  >
                    <span className="block font-semibold">{opt.label}</span>
                    <span className="mt-2 block text-base opacity-70">행동 · {opt.target}이(가) {opt.action}</span>
                    <span className="mt-1 block text-base opacity-70">이유 · {opt.reason}</span>
                    <span className="mt-1 block text-base text-orange">확인 · {opt.expected_observation}</span>
                    <span className="mt-1 block text-base opacity-50">연결 근거 {opt.evidence_ids.length}건</span>
                  </button>
                ))}
                {options.length === 0 && (
                  <div className="border border-white/30 p-3 text-lg opacity-70">
                    <p>현재 근거에 맞는 실행 가능한 추천이 없다. 아래에서 직접 쓰거나 표현을 바꿔 본다.</p>
                    <button type="button" onClick={loadOptions} disabled={optionsAction.busy} className="mt-2 underline disabled:opacity-30">후보 다시 확인</button>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={customText}
                    onChange={(e) => { setCustomText(e.target.value); setPreview(null); }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                        e.preventDefault();
                        if (customText.trim()) requestPreview();
                      }
                    }}
                    disabled={ruleAction.busy || previewAction.busy}
                    placeholder="직접 쓴다…"
                    className="min-w-0 flex-1 border border-white/40 bg-transparent px-3 py-2 text-lg outline-none placeholder:opacity-40 focus:border-white disabled:opacity-40"
                  />
                  <button
                    type="button"
                    onClick={requestPreview}
                    disabled={ruleAction.busy || previewAction.busy || !customText.trim()}
                    className="shrink-0 border border-white px-4 py-2 text-lg hover:bg-white hover:text-void disabled:opacity-30"
                  >
                    {previewAction.busy ? "…" : "해석 미리보기"}
                  </button>
                </div>
                {preview && (
                  <section className="space-y-3 border border-white/40 p-4" aria-label="직접 쓴 규칙 해석">
                    <div><p className="text-base opacity-55">사용자 원문</p><p className="text-lg">{preview.original_text}</p></div>
                    <div><p className="text-base opacity-55">실행할 의미</p><p className="text-lg">{preview.interpretation ?? "실행 의미를 확정하지 못했다."}</p></div>
                    {preview.limitations.length > 0 && <div><p className="text-base opacity-55">제한</p><ul className="list-inside list-disc text-lg">{preview.limitations.map((item) => <li key={item}>{item}</li>)}</ul></div>}
                    {preview.conflicts.length > 0 && <div><p className="text-base text-orange">충돌</p><ul className="list-inside list-disc text-lg">{preview.conflicts.map((item) => <li key={item}>{item}</li>)}</ul></div>}
                    {preview.alternatives.length > 0 && <div><p className="text-base opacity-55">다른 대안 — 선택하면 다시 해석한다</p><div className="mt-1 flex flex-col gap-2">{preview.alternatives.map((item) => <button key={item} type="button" onClick={() => { setCustomText(item); setPreview(null); }} className="border border-white/30 px-3 py-2 text-left text-lg">{item}</button>)}</div></div>}
                    <div className="flex flex-wrap gap-2">
                      <button type="button" onClick={() => chooseRule("custom")} disabled={!preview.executable || ruleAction.busy || preview.original_text !== customText} className="border border-white px-4 py-2 text-lg disabled:opacity-30">이 해석으로 적용</button>
                      <button type="button" onClick={() => setPreview(null)} className="px-3 py-2 text-lg opacity-70">다르게 쓴다</button>
                    </div>
                  </section>
                )}
              </>
            )}
            {ruleAction.busy && (
              <p className="text-center text-base opacity-40">
                세계에 규칙을 적용하는 중…
              </p>
            )}
            {ruleFailure && (
              <div className="fade-in border border-white/30 px-4 py-3 text-lg">
                <p>{ruleFailure.reason ?? "그 규칙은 걸 수 없다."}</p>
                {ruleFailure.conflicts.length > 0 && (
                  <ul className="mt-2 list-inside list-disc opacity-70">
                    {ruleFailure.conflicts.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <ErrorToast
        failure={askAction.failure ?? ruleAction.failure ?? previewAction.failure}
        onClose={() => {
          askAction.clearFailure();
          ruleAction.clearFailure();
          previewAction.clearFailure();
        }}
      />
    </div>
  );
}

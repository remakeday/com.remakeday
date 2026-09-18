"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  ApiError,
  type CellScores,
  type HarnessRes,
  type JourneyRes,
  type Metric,
  type RuleOpportunity,
} from "@/contracts/api";
import { TruthRevealCards } from "@/components/TruthRevealCards";
import { useVoice, VoiceReplay } from "@/components/VoicePlayer";
import { VOICE_CLIPS } from "@/lib/voiceMap";
import { observationLabel } from "@/lib/observationLabel";

const SOURCE_LABEL = { monkey_paw: "원숭이손", paw_effect: "원숭이손의 대가", user_choice: "추천 규칙", user_custom: "직접 쓴 규칙" };
const RESULT_LABEL: Record<RuleOpportunity["result"], string> = {
  obeyed: "지킴",
  violated: "지키지 못함",
  conflict: "다른 규칙과 충돌",
  not_evaluable: "평가할 수 없음",
};
const METRIC_LABEL: Record<string, string> = {
  note_source_linkage: "노트 출처 연결",
  rule_compliance: "규칙 실행 준수",
  question_grounding: "질문 근거 연결",
  recommendation_relevance: "추천 맥락 적합",
  custom_semantics: "직접 규칙 의미 보존",
  checker_accuracy: "검사 정확성",
};
const CELL_LABEL: Record<string, string> = { cause: "원인", motive: "동기", identity: "정체" };

function MetricRow({ name, metric }: { name: string; metric: Metric }) {
  const unavailable = metric.value === null || metric.denominator === 0;
  return (
    <li className="border border-paper/25 p-3">
      <div className="flex items-start justify-between gap-3">
        <p>{METRIC_LABEL[name] ?? name}</p>
        <p className="shrink-0 font-semibold">{unavailable || metric.value === null ? "N/A" : `${Math.round(metric.value * 100)}%`}</p>
      </div>
      <p className="mt-1 text-xs opacity-60">
        {metric.numerator === null ? "독립 검토 전" : `${metric.numerator}/${metric.denominator}`} · 검토 {metric.reviewed}건 · {metric.method}
      </p>
    </li>
  );
}

/** 관찰 근거 — 내부 ID 대신 라벨. 3건 이상이면 접는다(테스터9 F25). */
function EvidenceLabels({ ids }: { ids: string[] }) {
  if (ids.length === 0) return <>연결 기록 없음</>;
  const list = <ul>{ids.map((id) => <li key={id}>{observationLabel(id)}</li>)}</ul>;
  if (ids.length <= 2) return list;
  return (
    <details>
      <summary className="cursor-pointer">관찰 {ids.length}건</summary>
      {list}
    </details>
  );
}

function OpportunityCard({ opportunity }: { opportunity: RuleOpportunity }) {
  return (
    <li className="border border-paper/25 p-3">
      <p className="text-xs opacity-60">{opportunity.loop_n}회차 · 장면 {opportunity.beat}</p>
      <dl className="mt-2 grid grid-cols-[5rem_1fr] gap-x-2 gap-y-1">
        <dt className="text-xs opacity-55">기회</dt><dd>{opportunity.condition}</dd>
        <dt className="text-xs opacity-55">실제 행동</dt><dd>{opportunity.actual_action ?? "기록된 행동 없음"}</dd>
        <dt className="text-xs opacity-55">검사 결과</dt><dd className={opportunity.result === "obeyed" ? "" : "text-orange"}>{RESULT_LABEL[opportunity.result]}</dd>
        <dt className="text-xs opacity-55">관찰 근거</dt><dd><EvidenceLabels ids={opportunity.observation_ids} /></dd>
        {opportunity.side_effect && <><dt className="text-xs opacity-55">발생 결과</dt><dd>{opportunity.side_effect}</dd></>}
      </dl>
    </li>
  );
}

/** 개발 데이터 — 접힘 안에서만. 유저 회고의 본문은 여정이다. */
function DevDetails({ data, journey }: { data: HarnessRes; journey: JourneyRes }) {
  const s = data.harness_summary;
  const finalCells: CellScores | undefined = journey.final?.cells;
  const scoredCells = ["cause", "motive", "identity"] as const;
  const sourceCounts = {
    monkey_paw: data.rules.filter((rule) => rule.source === "monkey_paw" || rule.source === "paw_effect").length,
    user_choice: data.rules.filter((rule) => rule.source === "user_choice").length,
    user_custom: data.rules.filter((rule) => rule.source === "user_custom").length,
  };
  const experiments = data.experiments ?? [];
  const metrics = data.metrics ? Object.entries(data.metrics) : [];
  const countOrRecordMissing = (value: number | null | undefined) => value === null || value === undefined ? "기록 없음" : `${value}회`;
  return (
    <div className="mt-4 space-y-8">
      <section className="space-y-5 bg-paper p-4 text-ink" aria-label="개발 데이터 요약">
        <div className="space-y-3">
          <h3 className="text-base">회차별 이해도</h3>
          {journey.loops.map((loop) => (
            <div key={loop.loop_n} className="flex items-center gap-3">
              <span className="w-12 shrink-0">{loop.loop_n}회차</span>
              <div role="meter" aria-label={`${loop.loop_n}회차 이해도`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={loop.total} className="h-2 flex-1 bg-ink/15">
                <div className="h-2 bg-ink/70" style={{ width: `${loop.total}%` }} />
              </div>
              <span className="w-12 shrink-0 text-right tabular-nums">{Math.round(loop.total)}%</span>
            </div>
          ))}
        </div>
        <div className="space-y-3">
          <h3 className="text-base">최종 칸 점수</h3>
          {finalCells ? scoredCells.map((cell) => (
            <div key={cell} className="flex items-center gap-3">
              <span className="w-12 shrink-0">{CELL_LABEL[cell]}</span>
              <div role="meter" aria-label={`${CELL_LABEL[cell]} 점수`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={finalCells[cell]} className="h-2 flex-1 bg-ink/15">
                <div className="h-2 bg-orange" style={{ width: `${finalCells[cell]}%` }} />
              </div>
              <span className="w-12 shrink-0 text-right tabular-nums">{Math.round(finalCells[cell])}%</span>
            </div>
          )) : <p className="opacity-60">기록 없음</p>}
        </div>
        <div className="space-y-2">
          <h3 className="text-base">규칙 출처 분포</h3>
          <p className="break-keep tabular-nums">원숭이손 {sourceCounts.monkey_paw}개 · 추천 {sourceCounts.user_choice}개 · 직접 {sourceCounts.user_custom}개</p>
        </div>
      </section>
      <section className="space-y-4">
        <h3 className="text-base">실험 기록 — 규칙이 실제로 걸렸는가</h3>
        <p>{VOICE_CLIPS.EN03.text}</p>
        <VoiceReplay speaker="회고" text={VOICE_CLIPS.EN03.text} />
        {experiments.length === 0 ? <p className="opacity-60">실행 기회까지 연결된 규칙 기록이 없다.</p> : experiments.map((experiment) => (
          <article key={experiment.rule_id} className="border border-paper/25 p-4">
            <dl className="grid grid-cols-[4rem_1fr] gap-x-2 gap-y-2">
              <dt className="text-xs opacity-55">의도</dt><dd>{experiment.intent ?? "기록 없음"}</dd>
              <dt className="text-xs opacity-55">해석</dt><dd>{experiment.interpretation}</dd>
            </dl>
            <ol className="mt-2 space-y-2">{experiment.opportunities.map((item, i) => <OpportunityCard key={`${experiment.rule_id}-${i}`} opportunity={item} />)}</ol>
            {experiment.opportunities.length === 0 && <p className="mt-2 opacity-60">행동 기회가 없어 결과는 N/A다.</p>}
          </article>
        ))}
      </section>
      <section className="space-y-3">
        <h3 className="text-base">시스템 동작 품질</h3>
        <p>모델 호출 {countOrRecordMissing(s.model_calls)} · 시도 {countOrRecordMissing(s.model_attempts)} · 개입 {s.harness_interventions}회 · 대체 {s.fallbacks}회</p>
        <p className="text-xs opacity-60">측정 범위 · {s.model_call_coverage === "complete_logged_calls" ? "현재 로그 전체" : "이전 기록 일부 또는 측정 불가"} · 버전 {data.measurement_version ?? "기록 없음"}</p>
        {metrics.length > 0 ? <ul className="grid gap-2 sm:grid-cols-2">{metrics.map(([name, metric]) => <MetricRow key={name} name={name} metric={metric} />)}</ul> : <p className="opacity-60">세부 지표는 기록 없음.</p>}
      </section>
      <section className="space-y-3">
        <h3 className="text-base">원숭이손 · 변경의 대가</h3>
        <p>수락 {s.paw_accepted}회 · 연결되지 않은 부작용 기록 {s.tool_side_effects.length}건</p>
        <ul className="space-y-2">{s.tool_side_effects.map((item, i) => <li key={i}>{item.loop_n}회차 · 장면 {item.beat}: {item.text}</li>)}</ul>
      </section>
      <section className="space-y-3">
        <h3 className="text-base">등록한 규칙</h3>
        <p>질문 {s.questions_asked}회 · 추천 {s.recommended_rules}개 · 직접 작성 {s.custom_rules}개 · 충돌 {s.rule_conflicts}개</p>
        <ul className="space-y-3">{data.rules.map((rule) => (
          <li key={rule.rule_id} className="border border-paper/30 p-4">
            <p className="text-xs opacity-60">{rule.created_loop}회차 · {SOURCE_LABEL[rule.source]}</p>
            <p>{rule.target}: {rule.action} {rule.effect === "suppress" ? "금지" : "강제"}</p>
            {rule.hidden_side_effect && <p className="mt-2">설계된 대가: {rule.hidden_side_effect}</p>}
          </li>
        ))}</ul>
      </section>
    </div>
  );
}

export function Retrospective({ attemptId }: { attemptId: string }) {
  const { play: playVoice, stop: stopVoice } = useVoice();
  const devIntroductionPlayed = useRef(false);
  const [journey, setJourney] = useState<JourneyRes | null>(null);
  const [harness, setHarness] = useState<HarnessRes | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      setJourney(await api.getJourney(attemptId));
      // 개발 데이터는 보조 — 실패해도 여정은 보여준다
      try { setHarness(await api.getHarness(attemptId)); } catch { /* 접힘 섹션만 비운다 */ }
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "기록을 불러오지 못했습니다.");
    } finally {
      setBusy(false);
    }
  }, [attemptId]);
  useEffect(() => { void load(); }, [load]);
  const ready = journey !== null;
  useEffect(() => {
    if (ready) playVoice(["EN01"]);
    return stopVoice;
  }, [ready, playVoice, stopVoice]);

  if (!journey) return (
    <div className="space-y-4 text-center" role="status">
      <p>{busy ? "다섯 번의 기록을 펼치는 중…" : error}</p>
      {!busy && <button type="button" onClick={() => void load()} className="underline">다시 불러오기</button>}
    </div>
  );

  return (
    <article className="w-full space-y-8 text-sm leading-relaxed">
      <header className="space-y-3">
        <p className="text-xs tracking-widest opacity-60">다섯 번의 하루 이후</p>
        <h1 className="text-2xl">너의 추리는 이렇게 걸어왔다.</h1>
        <p>{VOICE_CLIPS.EN01.text}</p>
        <VoiceReplay speaker="회고" text={VOICE_CLIPS.EN01.text} />
      </header>

      <section className="space-y-3 border-t border-paper/30 pt-5">
        <h2 className="text-lg">하루하루의 기록</h2>
        <ol className="space-y-3">
          {journey.loops.map((loop) => (
            <li key={loop.loop_n} className="border border-paper/25 p-4">
              <div className="flex items-baseline justify-between gap-3">
                <p className="font-semibold">{loop.loop_n}번째 밤</p>
                <p className="text-xs opacity-60">이해도 {Math.round(loop.total)}%</p>
              </div>
              {loop.new_confirmed.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {loop.new_confirmed.map((c) => (
                    <li key={c.code} className="text-orange">이 밤, 하나가 확정됐다 — {c.my_claim ?? c.code}</li>
                  ))}
                </ul>
              )}
              {loop.unlocked_notes.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {loop.unlocked_notes.map((text, i) => (
                    <li key={i} className="opacity-80">신이 연 단서 — {text}</li>
                  ))}
                </ul>
              )}
              {loop.new_confirmed.length === 0 && loop.unlocked_notes.length === 0 && (
                <p className="mt-2 opacity-60">확정된 것 없이 지나간 밤.</p>
              )}
            </li>
          ))}
        </ol>
      </section>

      {journey.final && (
        <section className="space-y-3 border-t border-paper/30 pt-5">
          <h2 className="text-lg">진실과 내 기록</h2>
          <p className="text-xs opacity-60">맞춘 만큼만 열린다. 나머지는 다음 도전의 몫이다.</p>
          <TruthRevealCards reveal={journey.final.truth_reveal} light />
        </section>
      )}

      {journey.unresolved.length > 0 && (
        <section className="space-y-3 border-t border-paper/30 pt-5">
          <h2 className="text-lg">아직 비어 있는 자리</h2>
          <ul className="space-y-2">
            {journey.unresolved.map((u) => (
              <li key={u.cell} className="border border-paper/25 p-3">
                <p className="text-xs opacity-60">{CELL_LABEL[u.cell] ?? u.cell} · ?</p>
                <p className="mt-1">{u.hint}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {harness && (
        <details className="border-t border-paper/30 pt-5"
          onToggle={(event) => {
            if (event.currentTarget.open && !devIntroductionPlayed.current) {
              devIntroductionPlayed.current = true;
              playVoice(["EN02"]);
            } else if (!event.currentTarget.open) stopVoice();
          }}>
          <summary className="cursor-pointer text-base opacity-60">개발 데이터 — 규칙·검사·모델 동작이 궁금하다면</summary>
          <p className="mt-4">{VOICE_CLIPS.EN02.text}</p>
          <VoiceReplay speaker="회고" text={VOICE_CLIPS.EN02.text} />
          <DevDetails data={harness} journey={journey} />
        </details>
      )}
    </article>
  );
}

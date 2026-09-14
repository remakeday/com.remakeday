"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError, type HarnessRes, type Metric, type RuleOpportunity } from "@/contracts/api";

const SOURCE_LABEL = { monkey_paw: "원숭이손", user_choice: "추천 규칙", user_custom: "직접 쓴 규칙" };
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

function OpportunityCard({ opportunity }: { opportunity: RuleOpportunity }) {
  return (
    <li className="border border-paper/25 p-3">
      <p className="text-xs opacity-60">{opportunity.loop_n}회차 · 장면 {opportunity.beat}</p>
      <dl className="mt-2 grid grid-cols-[5rem_1fr] gap-x-2 gap-y-1">
        <dt className="text-xs opacity-55">기회</dt><dd>{opportunity.condition}</dd>
        <dt className="text-xs opacity-55">실제 행동</dt><dd>{opportunity.actual_action ?? "기록된 행동 없음"}</dd>
        <dt className="text-xs opacity-55">검사 결과</dt><dd className={opportunity.result === "obeyed" ? "" : "text-orange"}>{RESULT_LABEL[opportunity.result]}</dd>
        <dt className="text-xs opacity-55">관찰 근거</dt><dd>{opportunity.observation_ids.length > 0 ? opportunity.observation_ids.join(", ") : "연결 기록 없음"}</dd>
        {opportunity.side_effect && <><dt className="text-xs opacity-55">발생 결과</dt><dd>{opportunity.side_effect}</dd></>}
      </dl>
    </li>
  );
}

export function Retrospective({ attemptId }: { attemptId: string }) {
  const [data, setData] = useState<HarnessRes | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    try { setData(await api.getHarness(attemptId)); }
    catch (e) { setError(e instanceof ApiError ? e.detail : "회고를 불러오지 못했습니다."); }
    finally { setBusy(false); }
  }, [attemptId]);
  useEffect(() => { void load(); }, [load]);

  if (!data) return (
    <div className="space-y-4 text-center" role="status">
      <p>{busy ? "다섯 번의 기록을 펼치는 중…" : error}</p>
      {!busy && <button type="button" onClick={() => void load()} className="underline">다시 불러오기</button>}
    </div>
  );

  const s = data.harness_summary;
  const experiments = data.experiments ?? [];
  const metrics = data.metrics ? Object.entries(data.metrics) : [];
  const countOrRecordMissing = (value: number | null | undefined) => value === null || value === undefined ? "기록 없음" : `${value}회`;

  return (
    <article className="w-full space-y-8 text-sm leading-relaxed">
      <header className="space-y-4">
        <p className="text-xs tracking-widest opacity-60">개발 회고 · 다섯 번의 하루 이후</p>
        <h1 className="text-2xl">당신은 이 세계의 규칙을 고치고 있었다.</h1>
        <p>원숭이손은 한 변경의 이득과 대가를, 신의개입은 관찰에서 출발해 행동 규칙을 설계하고 검사하는 과정을 담고 있었다.</p>
      </header>

      <section className="space-y-4 border-t border-paper/30 pt-5">
        <h2 className="text-lg">당신의 실험 기록</h2>
        {experiments.length === 0 ? <p className="opacity-60">실행 기회까지 연결된 규칙 기록이 없다.</p> : experiments.map((experiment, index) => (
          <article key={experiment.rule_id} className={index === 0 ? "border border-orange/70 p-4" : "border border-paper/25 p-4"}>
            {index === 0 && <p className="mb-3 text-xs tracking-widest text-orange">가장 먼저 연결된 실험</p>}
            <dl className="grid grid-cols-[4rem_1fr] gap-x-2 gap-y-2">
              <dt className="text-xs opacity-55">의도</dt><dd>{experiment.intent ?? "기록 없음"}</dd>
              <dt className="text-xs opacity-55">해석</dt><dd>{experiment.interpretation}</dd>
            </dl>
            <p className="mt-4 text-xs opacity-55">기회 → 실제 행동 → 검사 결과 → 발생한 결과</p>
            <ol className="mt-2 space-y-2">{experiment.opportunities.map((item, i) => <OpportunityCard key={`${experiment.rule_id}-${i}`} opportunity={item} />)}</ol>
            {experiment.opportunities.length === 0 && <p className="mt-2 opacity-60">행동 기회가 없어 결과는 N/A다.</p>}
          </article>
        ))}
      </section>

      <section className="space-y-3 border-t border-paper/30 pt-5">
        <h2 className="text-lg">이야기 이해</h2>
        <p>마지막 화면의 이해도는 원인·동기·정체에 대한 답안을 평가한 값이다. 아래 시스템 지표와 합산하지 않는다.</p>
      </section>

      <section className="space-y-3 border-t border-paper/30 pt-5">
        <h2 className="text-lg">시스템 동작 품질</h2>
        <p>모델 호출 {countOrRecordMissing(s.model_calls)} · 시도 {countOrRecordMissing(s.model_attempts)} · 개입 {s.harness_interventions}회 · 대체 {s.fallbacks}회</p>
        <p className="text-xs opacity-60">측정 범위 · {s.model_call_coverage === "complete_logged_calls" ? "현재 로그 전체" : "이전 기록 일부 또는 측정 불가"} · 버전 {data.measurement_version ?? "기록 없음"}</p>
        <p className="text-xs opacity-60">개입은 검사 위반이나 대체가 있었던 호출만 센다. 시도 횟수나 규칙 성공 횟수와 같지 않다.</p>
        {metrics.length > 0 ? <ul className="grid gap-2 sm:grid-cols-2">{metrics.map(([name, metric]) => <MetricRow key={name} name={name} metric={metric} />)}</ul> : <p className="opacity-60">세부 지표는 기록 없음.</p>}
      </section>

      <section className="space-y-3 border-t border-paper/30 pt-5">
        <h2 className="text-lg">원숭이손 · 변경의 대가</h2>
        <p>원숭이손 수락 {s.paw_accepted}회 · 연결되지 않은 도구 부작용 기록 {s.tool_side_effects.length}건</p>
        <ul className="space-y-2">{s.tool_side_effects.map((item, i) => <li key={i}>{item.loop_n}회차 · 장면 {item.beat}: {item.text}</li>)}</ul>
        <p className="text-xs opacity-60">다른 조건과 비교하지 않은 기록을 원숭이손의 인과적 효과로 부르지 않는다.</p>
      </section>

      <section className="space-y-3 border-t border-paper/30 pt-5">
        <h2 className="text-lg">등록한 규칙</h2>
        <p>질문 {s.questions_asked}회 · 추천 {s.recommended_rules}개 · 직접 작성 {s.custom_rules}개 · 충돌 {s.rule_conflicts}개</p>
        <ul className="space-y-3">{data.rules.map((rule) => (
          <li key={rule.rule_id} className="border border-paper/30 p-4">
            <p className="text-xs opacity-60">{rule.created_loop}회차 · {SOURCE_LABEL[rule.source]}</p>
            <p>{rule.target}: {rule.action} {rule.effect === "suppress" ? "금지" : "강제"}</p>
            {rule.hidden_side_effect && <p className="mt-2">설계된 대가: {rule.hidden_side_effect} <span className="text-xs opacity-60">(실제 발생 여부는 위 기회 기록에서 확인)</span></p>}
          </li>
        ))}</ul>
      </section>
    </article>
  );
}

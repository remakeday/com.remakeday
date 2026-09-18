"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Observation } from "@/contracts/api";
import { SceneIntro } from "@/components/day/SceneIntro";
import { lineStyles } from "@/lib/lineStyles";

export interface RecordAdvice {
  id: string;
  loop_n: number;
  text: string;
}

export function RecordLog({ observations, advice, loopN }: { observations: Observation[]; advice: RecordAdvice[]; loopN: number }) {
  const [detail, setDetail] = useState<Observation | null>(null);
  const [imageIndex, setImageIndex] = useState(0);
  const [newOnly, setNewOnly] = useState(false);
  const returnFocus = useRef<string | null>(null);
  const listRef = useRef<HTMLOListElement | null>(null);
  const focusDetail = useCallback((node: HTMLButtonElement | null) => node?.focus({ preventScroll: true }), []);

  useEffect(() => {
    const observationId = returnFocus.current;
    if (detail !== null || observationId === null) return;
    const frame = requestAnimationFrame(() => {
      listRef.current?.querySelector<HTMLButtonElement>(
        `button[data-observation-id="${CSS.escape(observationId)}"]`,
      )?.focus({ preventScroll: true });
    });
    return () => cancelAnimationFrame(frame);
  }, [detail]);

  const ordered = [
    ...observations.map((observation) => ({
      id: observation.observation_id, loop_n: observation.loop_n, beat: observation.beat,
      label: `${observation.loop_n}일째 · 장면 ${observation.beat}${observation.actor ? ` · ${observation.actor}` : ""}`,
      text: observation.text, observation,
      isNew: observation.loop_n === loopN || (
        observation.loop_n === loopN - 1 && /night-clue|outcome-fragment/.test(observation.observation_id)
      ),
    })),
    // 조언은 관찰 API에 없으므로 신의 응답에서 받아 그날 기록 뒤에 둔다.
    ...advice.map((item) => ({
      ...item, beat: Infinity, label: `${item.loop_n}일째 · 신의 조언`, observation: null, isNew: false,
    })),
  ].sort((a, b) => a.loop_n - b.loop_n || a.beat - b.beat);

  const visible = newOnly ? ordered.filter((item) => item.isNew) : ordered;

  return (
    <>
      <div hidden={detail !== null}>
        <label className="mb-3 flex w-fit items-center gap-2 text-base">
          <input type="checkbox" checked={newOnly} onChange={(event) => setNewOnly(event.target.checked)} />
          새 단서만
        </label>
        {visible.length === 0 && <p className="text-base text-ink/60">
          {newOnly ? "아직 새 단서가 없다." : "아직 기록된 단서가 없다."}
        </p>}
      </div>
      <ol ref={listRef} hidden={detail !== null} className="divide-y divide-ink/15">
        {visible.map((item) => {
          const observation = item.observation;
          const illustrated = observation && observation.illustrations.length > 0;
          const fragment = /:fragment-\d+$/.test(item.id);
          const content = <>
            <span className="mr-2 text-sm text-ink/60">
              {item.label}
            </span>
            {item.isNew && <span className="mr-2 border border-orange/40 px-1 text-xs text-orange">NEW</span>}
            {fragment && <span className={`mr-2 text-sm ${lineStyles.fragment.className}`}>
              <span aria-hidden="true">{lineStyles.fragment.icon} </span>{lineStyles.fragment.label?.(null)}
            </span>}
            <span>{item.text}</span>
            {illustrated && <span className="ml-2 text-sm text-ink/60">그림 보기</span>}
          </>;
          return <li key={item.id} className="text-base leading-relaxed">
            {illustrated ? (
              <button type="button" data-observation-id={observation.observation_id}
                className="w-full py-3 text-left hover:bg-ink/5 focus-visible:outline-2 focus-visible:outline-ink"
                onClick={() => { returnFocus.current = observation.observation_id; setImageIndex(0); setDetail(observation); }}>
                {content}
              </button>
            ) : <p className="py-3">{content}</p>}
          </li>;
        })}
      </ol>
      {detail && <section aria-label={`${detail.scene_title} 그림`}>
        <button type="button" ref={focusDetail} onClick={() => setDetail(null)}
          className="mb-3 border border-ink/40 px-3 text-base">기록으로 돌아간다</button>
        <p className="mb-2 text-base">{detail.loop_n}일째 · {detail.scene_title}</p>
        <div className="h-[60dvh]">
          <SceneIntro beat={detail.beat} damageLevel={0} illustrations={detail.illustrations} index={imageIndex}
            disabled={false} onSelect={setImageIndex} />
        </div>
        <p className="mt-3 text-base leading-relaxed">{detail.text}</p>
      </section>}
    </>
  );
}

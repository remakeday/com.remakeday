"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Observation } from "@/contracts/api";
import { clueImage } from "@/lib/imageMap";
import { ObservationCard } from "@/components/ObservationCard";

export function EvidenceGallery({ observations, onClose, returnFocus }: { observations: Observation[]; onClose: () => void; returnFocus: HTMLElement | null }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [detail, setDetail] = useState<Observation | null>(null);
  const galleryRef = useRef<HTMLDivElement>(null);
  const detailRef = useRef<HTMLDivElement>(null);
  const detailOpenRef = useRef(false);
  const detailReturnFocusRef = useRef<HTMLElement | null>(null);
  const illustrated = useMemo(
    () => observations.filter((item) => item.illustrations.some((image) => clueImage(image.image_id))),
    [observations],
  );

  detailOpenRef.current = detail !== null;

  useEffect(() => {
    galleryRef.current?.querySelector<HTMLElement>("button")?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        if (detailOpenRef.current) setDetail(null);
        else onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const scope = detailOpenRef.current ? detailRef.current : galleryRef.current;
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
      requestAnimationFrame(() => returnFocus?.focus());
    };
    // The gallery stays mounted for its modal lifetime; returnFocus is captured before inert is applied.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (detail) detailRef.current?.querySelector<HTMLElement>("button")?.focus();
    else detailReturnFocusRef.current?.focus();
  }, [detail]);

  const toggleCompare = (id: string) => {
    setSelected((current) => current.includes(id)
      ? current.filter((item) => item !== id)
      : [...current.slice(-1), id]);
  };
  const comparison = (selected.map((id) => illustrated.find((item) => item.observation_id === id)).filter(Boolean) as Observation[])
    .sort((a, b) => a.loop_n - b.loop_n || a.beat - b.beat || illustrated.indexOf(a) - illustrated.indexOf(b));

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-void/95 px-4 py-6 text-paper" role="dialog" aria-modal="true" aria-label="이미 본 근거 그림">
      <div ref={galleryRef} inert={detail ? true : undefined} aria-hidden={detail ? true : undefined} className="mx-auto flex w-full max-w-4xl flex-col gap-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg">이미 본 근거 그림</h2>
            <p className="text-base opacity-65">낮에 직접 본 원본만 모았다. 두 장을 고르면 본 순서대로 비교한다.</p>
          </div>
          <button type="button" onClick={onClose} className="shrink-0 border border-paper/50 px-3 py-2 text-base" aria-label="근거 그림 닫기">닫기</button>
        </div>

        {illustrated.length === 0 ? <p className="text-lg opacity-60">다시 볼 수 있는 그림이 아직 없다.</p> : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {illustrated.map((item) => (
              <div key={item.observation_id} className="space-y-2">
                <ObservationCard observation={item} compact onOpen={(observation) => { detailReturnFocusRef.current = document.activeElement as HTMLElement | null; setDetail(observation); }} />
                <label className="flex min-h-10 cursor-pointer items-center gap-2 border border-paper/20 px-3 py-2 text-base">
                  <input type="checkbox" checked={selected.includes(item.observation_id)} onChange={() => toggleCompare(item.observation_id)} />
                  비교에 놓기
                </label>
              </div>
            ))}
          </div>
        )}

        {comparison.length === 2 && (
          <section className="border-t border-paper/30 pt-4" aria-label="관찰 비교">
            <h3 className="mb-1 text-lg">내가 본 순서</h3>
            <p className="mb-3 text-base opacity-60">나란히 본 기록이며, 앞 장면이 뒤 장면의 원인이라는 뜻은 아니다.</p>
            <div className="grid grid-cols-2 gap-2">
              {comparison.map((item, index) => (
                <div key={item.observation_id}>
                  <p className="mb-1 text-base opacity-60">{index + 1}. {item.loop_n}회차 · {item.scene_title}</p>
                  <ObservationCard observation={item} compact />
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      {detail && (
        <div ref={detailRef} className="fixed inset-0 z-[60] flex items-center justify-center bg-void/95 px-4 py-8" role="dialog" aria-modal="true" aria-label={`${detail.scene_title} 원본 그림`}>
          <div className="max-h-full w-full max-w-2xl overflow-y-auto">
            <ObservationCard observation={detail} />
            <button type="button" onClick={() => setDetail(null)} className="mt-3 w-full border border-paper/50 px-4 py-2 text-lg">원본 그림 닫기</button>
          </div>
        </div>
      )}
    </div>
  );
}

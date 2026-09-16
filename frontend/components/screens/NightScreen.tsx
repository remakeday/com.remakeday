"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/contracts/api";
import type { Note, NoteKind, Observation, PreviousAnswer } from "@/contracts/api";
import { NIGHT_IMAGE } from "@/lib/imageMap";
import { dedupeByText } from "@/lib/dedupeByText";
import { useApiAction } from "@/lib/useApiAction";
import { ErrorToast } from "@/components/ErrorToast";
import { EvidenceGallery } from "@/components/EvidenceGallery";

const KIND_LABEL: Record<NoteKind, string> = {
  fragment: "파편",
  confirmed: "확인 사실",
  rule_observation: "규칙과 관찰",
};

const KIND_ORDER: NoteKind[] = ["fragment", "confirmed", "rule_observation"];

/**
 * 밤 — "오늘은 무슨 상황이었나요? 왜 멸망하나요?"
 * 노트에서 탭해 조합 + 자유 서술 → night/draft
 */
export function NightScreen({
  loopId,
  onDrafted,
}: {
  loopId: string;
  onDrafted: (nightId: string, claims: string[]) => void;
}) {
  const [notes, setNotes] = useState<Note[] | null>(null);
  const [notesOpen, setNotesOpen] = useState(false);
  const [tapped, setTapped] = useState<Set<number>>(new Set());
  const [freeText, setFreeText] = useState("");
  const [previous, setPrevious] = useState<PreviousAnswer | null>(null);
  const [inheritedNoteIds, setInheritedNoteIds] = useState<number[]>([]);
  const [observations, setObservations] = useState<Observation[] | null>(null);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [previousReady, setPreviousReady] = useState(false);
  const galleryReturnFocus = useRef<HTMLElement | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const [scrolledDown, setScrolledDown] = useState(false);
  const shownNotes = notes === null ? null : dedupeByText(notes);

  const notesAction = useApiAction();
  const draftAction = useApiAction();
  const previousAction = useApiAction();
  const observationsAction = useApiAction();

  useEffect(() => {
    void previousAction.run(
      () => api.getPreviousAnswer(loopId),
      (res) => {
        const restored = res.previous_answer;
        setPrevious(restored);
        if (!restored) {
          setPreviousReady(true);
          return;
        }
        setFreeText(restored.free_text);
        setTapped(new Set(restored.tapped_note_ids));
        setInheritedNoteIds([...restored.tapped_note_ids]);
        setPreviousReady(true);
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loopId]);

  // 기록 목록이 길어지면 제출 버튼이 위로 밀린다 — 300px 넘게 내려갔을 때만 맨 위로 버튼을 보인다
  useEffect(() => {
    if (!notesOpen) {
      setScrolledDown(false);
      return;
    }
    const root = rootRef.current;
    const onScroll = () => setScrolledDown((root?.scrollTop ?? 0) + window.scrollY > 300);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    root?.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      root?.removeEventListener("scroll", onScroll);
    };
  }, [notesOpen]);

  const scrollToTop = () => {
    rootRef.current?.scrollTo({ top: 0, behavior: "smooth" });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const toggle = (id: number) => {
    setTapped((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const submit = () => {
    if (draftAction.busy) return;
    void draftAction.run(
      () =>
        api.nightDraft(loopId, {
          tapped_note_ids: [...tapped],
          inherited_note_ids: inheritedNoteIds,
          free_text: freeText,
        }),
      (res) => onDrafted(res.night_id, res.claims),
    );
  };

  const canSubmit =
    previousReady && !draftAction.busy && (tapped.size > 0 || freeText.trim().length > 0);

  return (
    <div ref={rootRef} className="relative flex min-h-dvh w-full flex-col items-center overflow-y-auto bg-void px-4 py-10 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={NIGHT_IMAGE}
        alt=""
        className="pointer-events-none fixed inset-0 h-full w-full object-cover object-bottom opacity-30"
      />
      <div inert={galleryOpen ? true : undefined} aria-hidden={galleryOpen ? true : undefined} className="fade-in relative z-10 flex w-full max-w-2xl flex-col gap-6">
        <div className="text-center">
          <p className="text-lg leading-relaxed">
            오늘은 무슨 상황이었나요?
            <br />왜 멸망하나요?
          </p>
        </div>

        {previous && (
          <section className="border border-paper/35 p-3 text-lg">
            <p className="text-base tracking-widest text-orange">지난 회차에서 이어 쓴 초안</p>
            <p className="mt-1 text-base opacity-60">{previous.loop_n}회차에 직접 쓴 글이다. 새로 알게 된 내용을 덧붙이거나 고칠 수 있다.</p>
            <p className="mt-2 text-base opacity-60">선택한 근거는 글과 따로 이어진다. 아래에서 선택을 바꿀 수 있다.</p>
          </section>
        )}

        {/* 자유 서술 */}
        <p className="text-center text-base opacity-50">
          내가 쓴 글은 다음 밤에도 이어 쓸 수 있다. 관찰 기록은 필요할 때 펼쳐 근거로 고른다.
        </p>
        <textarea
          aria-label="오늘의 이해"
          value={freeText}
          onChange={(e) => setFreeText(e.target.value)}
          rows={7}
          disabled={!previousReady}
          placeholder="자유롭게 쓴다…"
          className="w-full resize-y border border-paper/40 bg-transparent px-3 py-2 text-lg leading-relaxed outline-none placeholder:opacity-40 focus:border-paper"
        />
        {!previousReady && <p role="status" className="text-center text-base opacity-60">지난 회차의 초안과 근거를 확인하는 중…</p>}

        <button
          type="button"
          onClick={submit}
          disabled={!canSubmit}
          className="mx-auto border border-paper px-8 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-30"
        >
          {draftAction.busy ? "정리하는 중…" : "이렇게 이해했다"}
        </button>

        {/* 노트 패널 — kind별 3분류 */}
        <button type="button" aria-expanded={notesOpen} aria-controls="night-notes"
          disabled={notesAction.busy} onClick={() => {
            setNotesOpen(!notesOpen);
            if (!notesOpen && notes === null) {
              void notesAction.run(() => api.getNotes(loopId), (res) => setNotes(res.notes));
            }
          }} className="border border-paper/40 px-4 py-2 text-lg text-left hover:border-paper">
          관찰 기록에서 근거 고르기 · 선택 {tapped.size}개 {notesOpen ? "▴" : "▾"}
        </button>
        {notesOpen && <div id="night-notes" className="flex flex-col gap-4">
          <p className="text-base opacity-60">이번 답변의 근거로 쓸 기록만 고른다. 직접 쓴 글에 기록이 붙지는 않는다.</p>
          {notes === null && (
            <p className="text-center text-lg opacity-40">
              {notesAction.failure ? "노트를 불러오지 못했습니다" : "…"}
            </p>
          )}
          {shownNotes !== null &&
            KIND_ORDER.map((kind) => {
              const group = shownNotes.filter((n) => n.kind === kind);
              if (group.length === 0) return null;
              return (
                <div key={kind}>
                  <h3 className="mb-2 text-base tracking-widest opacity-60">
                    {KIND_LABEL[kind]}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {group.map((n) => (
                      <button
                        key={n.id}
                        type="button"
                        aria-pressed={tapped.has(n.id)}
                        disabled={!previousReady}
                        onClick={() => toggle(n.id)}
                        className={`border px-3 py-1.5 text-left text-lg leading-snug ${
                          tapped.has(n.id)
                            ? "border-paper bg-paper text-void"
                            : "border-paper/30 hover:border-paper/70"
                        }`}
                      >
                        {n.text}
                        <span className="ml-2 text-base opacity-40">
                          {n.loop_n}회차
                        </span>
                        {(n.sources ?? []).length > 0 && (
                          <span className="ml-2 text-base text-orange">출처 {(n.sources ?? []).length}</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          {shownNotes !== null && shownNotes.length === 0 && (
            <p className="text-center text-lg opacity-40">
              적어둔 것이 없다.
            </p>
          )}
        </div>}

        <button type="button" disabled={observationsAction.busy} onClick={() => {
          galleryReturnFocus.current = document.activeElement as HTMLElement | null;
          if (observations !== null) setGalleryOpen(true);
          else void observationsAction.run(() => api.getObservations(loopId), (res) => {
            setObservations(res.observations);
            setGalleryOpen(true);
          });
        }} aria-label="근거 그림 모아보기" className="mx-auto border border-paper/40 px-5 py-2 text-base hover:border-paper">
          근거 그림 모아보기
        </button>
      </div>

      {notesOpen && scrolledDown && (
        <button
          type="button"
          onClick={scrollToTop}
          aria-label="맨 위로"
          className="fixed right-4 bottom-6 z-40 border border-paper/40 bg-void px-4 py-2 text-base hover:border-paper"
        >
          맨 위로
        </button>
      )}

      <ErrorToast
        failure={draftAction.failure ?? notesAction.failure ?? previousAction.failure ?? observationsAction.failure}
        onClose={() => {
          draftAction.clearFailure();
          notesAction.clearFailure();
          previousAction.clearFailure();
          observationsAction.clearFailure();
        }}
      />
      {galleryOpen && <EvidenceGallery observations={observations ?? []} onClose={() => setGalleryOpen(false)} returnFocus={galleryReturnFocus.current} />}
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { api } from "@/contracts/api";
import type { SubmitRes } from "@/contracts/api";
import { useApiAction } from "@/lib/useApiAction";
import { ErrorToast } from "@/components/ErrorToast";
import type { DialoguePair } from "@/components/screens/DayScreen";

/** 밤 채점 대기 — 단계 텍스트 순환 (1.2초 간격) */
const SUBMIT_STAGES = ["정리하고 있다…", "대조하고 있다…", "판정하고 있다…"];

/** 채점 대기 회상 — 낮의 문답을 한 쌍씩 (세계가 읽는 동안 나는 하루를 되새긴다) */
function DayRecap({ pairs }: { pairs: DialoguePair[] }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => setI((v) => (v + 1) % pairs.length), 2500);
    return () => clearInterval(t);
  }, [pairs.length]);
  const p = pairs[i];
  return (
    <div key={i} className="fade-in flex min-h-24 flex-col items-center gap-2 px-3 text-center">
      <p className="text-lg leading-relaxed opacity-70">
        {p.npc}에게 — “{p.q}”
      </p>
      <p className="text-lg leading-relaxed">
        {p.npc} — “{p.a}”
      </p>
    </div>
  );
}

/**
 * 정리 확인 — "이렇게 이해했는데 맞아?"
 * claims 목록. 수정은 1회만 (PATCH), 그 후 제출.
 * 질문형 주장에는 단정해서 고치라는 안내만 붙인다 — 자동 변환·채점 제외 없음 (테스터11 O2).
 */
export function ConfirmScreen({
  nightId,
  initialClaims,
  initialIsQuestion,
  dayLog,
  onSubmitted,
}: {
  nightId: string;
  initialClaims: string[];
  initialIsQuestion: boolean[];
  dayLog: DialoguePair[];
  onSubmitted: (result: SubmitRes, finalClaims: string[]) => void;
}) {
  const [claims, setClaims] = useState<string[]>(initialClaims);
  const [isQuestion, setIsQuestion] = useState<boolean[]>(initialIsQuestion);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [editUsed, setEditUsed] = useState(false);

  const patchAction = useApiAction();
  const submitAction = useApiAction();

  const [submitStageIdx, setSubmitStageIdx] = useState(0);

  // 채점 대기 연출 — prefers-reduced-motion이면 마지막 단계 고정
  useEffect(() => {
    if (!submitAction.busy) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setSubmitStageIdx(SUBMIT_STAGES.length - 1);
      return;
    }
    setSubmitStageIdx(0);
    const timer = setInterval(
      () => setSubmitStageIdx((i) => (i + 1) % SUBMIT_STAGES.length),
      1200,
    );
    return () => clearInterval(timer);
  }, [submitAction.busy]);

  const startEdit = () => {
    setEditText(claims.join("\n"));
    setEditing(true);
  };

  const saveEdit = () => {
    const next = editText
      .split("\n")
      .map((s) => s.trim())
      .filter((s) => s.length > 0)
      .slice(0, 8);
    if (next.length === 0) return;
    void patchAction.run(
      () => api.patchClaims(nightId, { claims: next }),
      (res) => {
        setClaims(res.claims);
        setIsQuestion(res.is_question ?? []);
        setEditing(false);
        setEditUsed(true);
      },
      (status) => {
        if (status === 409) {
          // 이미 수정한 밤 — 편집 불가로 전환
          setEditing(false);
          setEditUsed(true);
          return false;
        }
        return false;
      },
    );
  };

  const submit = () => {
    if (submitAction.busy) return;
    void submitAction.run(
      () => api.submitNight(nightId),
      (result) => onSubmitted(result, claims),
    );
  };

  return (
    <div className="flex min-h-dvh w-full flex-col items-center justify-center bg-void px-4 py-10 text-paper">
      <div className="fade-in flex w-full max-w-xl flex-col gap-6">
        <p className="text-center text-lg">
          {submitAction.busy ? "하루를 되짚는다" : "이렇게 이해했는데, 맞아?"}
        </p>

        {editing ? (
          <>
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              onKeyDown={(e) => {
                // 일부 환경에서 ctrl+a 전체 선택이 먹히지 않는 문제 방어
                if ((e.ctrlKey || e.metaKey) && e.key === "a") {
                  e.preventDefault();
                  e.currentTarget.select();
                }
              }}
              rows={Math.max(claims.length + 1, 5)}
              className="w-full resize-y border border-paper/40 bg-transparent px-3 py-2 text-lg leading-relaxed outline-none focus:border-paper"
            />
            <p className="text-center text-base opacity-50">
              한 줄이 주장 하나다. 최대 8줄.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <button
                type="button"
                onClick={saveEdit}
                disabled={patchAction.busy}
                aria-busy={patchAction.busy}
                className="border border-paper px-6 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-30"
              >
                {patchAction.busy ? "이렇게 고치는 중…" : "이렇게 고친다"}
              </button>
              <button
                type="button"
                onClick={() => setEditText("")}
                disabled={editText.length === 0}
                className="px-4 py-2 text-lg opacity-60 hover:opacity-100 disabled:opacity-30"
              >
                모두 지운다
              </button>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="px-4 py-2 text-lg opacity-60 hover:opacity-100"
              >
                그만둔다
              </button>
            </div>
          </>
        ) : (
          <>
            {submitAction.busy && dayLog.length > 0 ? (
              <DayRecap pairs={dayLog} />
            ) : (
              <ol className="flex flex-col gap-2">
                {claims.map((c, i) => (
                  <li
                    key={i}
                    className="border border-paper/30 px-3 py-2 text-lg leading-relaxed"
                  >
                    {c}
                    {isQuestion[i] && (
                      <span className="mt-1 block text-base text-orange">
                        {editUsed
                          ? "질문이다. 고치기를 이미 써서 이대로 제출된다."
                          : "질문이다. '~다'로 단정해 고쳐 쓴다. 다음 밤 글에도 고쳐 써야 이어진다."}
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            )}
            {!submitAction.busy && (
              <p className="text-center text-base opacity-50">
                주장은 최대 8개까지만 세계에 닿는다.
              </p>
            )}
            <div className="flex flex-wrap justify-center gap-4">
              {!editUsed && !submitAction.busy && (
                <button
                  type="button"
                  onClick={startEdit}
                  className="border border-paper/50 px-6 py-2 text-lg hover:border-paper"
                >
                  아니, 고친다 (1회)
                </button>
              )}
              <button
                type="button"
                onClick={submit}
                disabled={submitAction.busy}
                className="border border-paper px-8 py-2 text-lg hover:bg-paper hover:text-void disabled:opacity-30"
              >
                {submitAction.busy
                  ? SUBMIT_STAGES[submitStageIdx]
                  : "맞아, 제출한다"}
              </button>
            </div>
            {submitAction.busy && (
              <p className="text-center text-base opacity-40">
                세계가 답안을 읽고 있다…
              </p>
            )}
          </>
        )}
      </div>

      <ErrorToast
        failure={patchAction.failure ?? submitAction.failure}
        onClose={() => {
          patchAction.clearFailure();
          submitAction.clearFailure();
        }}
      />
    </div>
  );
}

"use client";

import { use, useState } from "react";
import { api } from "@/contracts/api";
import type { InspectorRes } from "@/contracts/api";
import { useApiAction } from "@/lib/useApiAction";
import { ErrorToast } from "@/components/ErrorToast";

/** 값을 표 형태로 — 미니멀 개발자 뷰 */
function DataTable({ title, rows }: { title: string; rows: unknown[] }) {
  if (rows.length === 0)
    return (
      <section className="mb-8">
        <h2 className="mb-2 text-sm font-semibold tracking-widest">{title}</h2>
        <p className="text-xs opacity-50">비어 있음</p>
      </section>
    );

  const objects = rows.map((r) =>
    typeof r === "object" && r !== null
      ? (r as Record<string, unknown>)
      : { value: r },
  );
  const columns = [...new Set(objects.flatMap((o) => Object.keys(o)))];

  return (
    <section className="mb-8">
      <h2 className="mb-2 text-sm font-semibold tracking-widest">{title}</h2>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr>
              {columns.map((c) => (
                <th
                  key={c}
                  className="border border-ink/30 px-2 py-1 text-left font-normal opacity-70"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {objects.map((row, i) => (
              <tr key={i}>
                {columns.map((c) => {
                  const v = row[c];
                  return (
                    <td
                      key={c}
                      className="border border-ink/20 px-2 py-1 align-top whitespace-pre-wrap"
                    >
                      {v === undefined || v === null
                        ? ""
                        : typeof v === "string"
                          ? v
                          : JSON.stringify(v)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function InspectorView({ attemptId }: { attemptId: string }) {
  // 토큰은 입력칸으로만 받는다 — URL(?token=)에 두면 프론트 호스팅 로그·브라우저 기록에 남는다
  const [token, setToken] = useState("");
  const [data, setData] = useState<InspectorRes | null>(null);
  const action = useApiAction();

  const load = (t: string) => {
    if (!t) return;
    void action.run(
      () => api.getInspector(attemptId, t),
      setData,
    );
  };

  return (
    <div className="min-h-dvh bg-paper px-4 py-8 text-ink">
      <div className="mx-auto max-w-4xl">
        <h1 className="mb-1 text-lg font-semibold">
          Inspector — {attemptId}
        </h1>
        <p className="mb-6 text-xs opacity-50">
          이벤트 타임라인 · Manager 패치 · 원숭이손 · 채점 근거 (개발자 전용)
        </p>

        <div className="mb-8 flex items-center gap-2">
          <input
            type="password"
            autoComplete="off"
            spellCheck={false}
            value={token}
            onChange={(e) => setToken(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                e.preventDefault();
                load(token);
              }
            }}
            placeholder="INSPECTOR_TOKEN"
            className="min-w-0 flex-1 border border-ink/40 bg-transparent px-3 py-2 font-mono text-sm outline-none focus:border-ink"
          />
          <button
            type="button"
            onClick={() => load(token)}
            disabled={action.busy || !token}
            className="border border-ink px-4 py-2 text-sm hover:bg-ink hover:text-paper disabled:opacity-30"
          >
            {action.busy ? "…" : "조회"}
          </button>
        </div>

        {data && (
          <>
            <DataTable title="EVENTS — 이벤트 타임라인" rows={data.events} />
            <DataTable title="PATCHES — Manager 패치" rows={data.patches} />
            <DataTable title="PAW RULES — 원숭이손" rows={data.paw_rules} />
            <DataTable title="SCORING — 채점 근거" rows={data.scoring} />
          </>
        )}
        {!data && !action.busy && (
          <p className="text-sm opacity-50">토큰을 입력하고 조회한다.</p>
        )}
      </div>
      <ErrorToast failure={action.failure} onClose={action.clearFailure} />
    </div>
  );
}

export default function InspectorPage({
  params,
}: {
  params: Promise<{ attemptId: string }>;
}) {
  const { attemptId } = use(params);
  return <InspectorView attemptId={attemptId} />;
}

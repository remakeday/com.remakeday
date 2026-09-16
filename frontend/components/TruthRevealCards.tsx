import type { TruthReveal } from "@/contracts/api";

const CELL_LABEL: Record<string, string> = {
  cause: "원인",
  motive: "동기",
  identity: "정체",
  side_effect: "부작용",
};

/** 진실은 이해한 만큼만 열린다 — confirmed 전문 / partial 반쯤 / none "?" 잠금. */
export function TruthRevealCards({
  reveal,
  light,
}: {
  reveal: TruthReveal[];
  light?: boolean;
}) {
  const border = light ? "border-paper/40" : "border-ink/40";
  return (
    <ul className="w-full space-y-3 text-sm leading-relaxed">
      {reveal.map((r) => (
        <li key={r.code} className={`border ${border} p-4`}>
          <p className="text-xs tracking-widest opacity-60">{CELL_LABEL[r.cell] ?? r.cell}</p>
          {r.verdict === "confirmed" && (
            <>
              {r.my_claim && <p className="mt-2 opacity-70">내 기록 — {r.my_claim}</p>}
              <p className="mt-1">{r.truth}</p>
            </>
          )}
          {r.verdict === "partial" && (
            <>
              {r.my_claim && <p className="mt-2 opacity-70">내 기록 — {r.my_claim}</p>}
              <p className="mt-1">가까이 갔다. 전부는 아니었다.</p>
            </>
          )}
          {r.verdict === "none" && (
            <>
              <p className="mt-2 text-2xl">?</p>
              <p className="mt-1 text-xs opacity-60">이 자리는 아직 비어 있다. 다시 도전하면 밝혀진다.</p>
            </>
          )}
        </li>
      ))}
    </ul>
  );
}

import type { CellScores } from "@/contracts/api";

function mark(score: number): string {
  if (score >= 80) return "○";
  if (score >= 40) return "△";
  return "✗";
}

/** 상황·정체의 달성도(각 100% 기준). 총점에는 70:30으로 반영한다. */
export function CellResults({
  cells,
  light,
}: {
  cells: CellScores;
  light?: boolean;
}) {
  return (
    <div
      className={`grid grid-cols-2 gap-2 ${light ? "text-paper" : "text-ink"}`}
    >
      {[
        { label: "상황", score: (cells.cause + cells.motive) / 2, weight: 70 },
        { label: "정체", score: cells.identity, weight: 30 },
      ].map(({ label, score, weight }) => (
        <div
          key={label}
          className={`border px-2 py-3 text-center ${
            light ? "border-paper/40" : "border-ink/40"
          }`}
        >
          <div className="text-2xl">{mark(score)}</div>
          <div className="mt-1 text-xs opacity-70">{label}</div>
          <div className="text-xs opacity-70">{Math.round(score)}% 이해</div>
          <div className="mt-1 text-xs opacity-50">총점 중 {weight}점</div>
        </div>
      ))}
    </div>
  );
}

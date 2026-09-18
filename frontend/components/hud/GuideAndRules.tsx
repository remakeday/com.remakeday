import { GameplayGuide } from "@/components/GameplayGuide";

export function GuideAndRules({ activeRules }: { activeRules: string[] }) {
  return (
    <div className="space-y-6">
      <GameplayGuide />
      <section className="border-t border-ink/20 pt-4" aria-labelledby="active-rules-title">
        <h2 id="active-rules-title" className="mb-3 text-xl">걸린 규칙</h2>
        {activeRules.length > 0 ? <ul className="list-disc space-y-2 pl-5 text-base">
          {activeRules.map((rule, index) => <li key={`${index}-${rule}`}>{rule}</li>)}
        </ul> : <p className="text-base text-ink/60">아직 걸린 규칙이 없다.</p>}
      </section>
    </div>
  );
}

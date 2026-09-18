import type { Npc } from "@/contracts/api";
import { npcImage } from "@/lib/imageMap";

const CHARACTERS = [
  { code: "chaeyeon", name: "채연" },
  { code: "minseok", name: "민석" },
  { code: "eunsang", name: "은상" },
  { code: "jun", name: "준" },
];

export function DialogueStage({ npcs, selected, ready, disabled, dayDone, budgetLeft, onSelect }: {
  npcs: Npc[];
  selected: string | null;
  ready: boolean;
  disabled: boolean;
  dayDone: boolean;
  budgetLeft: number;
  onSelect: (code: string) => void;
}) {
  const current = npcs.find((npc) => npc.code === selected);
  const portrait = current ? npcImage(current.code, current.mood) : null;

  return (
    <div className="mx-auto flex h-full min-h-0 w-full max-w-3xl flex-col gap-2 px-3 py-2">
      <div className="grid shrink-0 grid-cols-4 gap-2">
        {CHARACTERS.map((character) => {
          const npc = npcs.find((item) => item.code === character.code);
          const active = selected === character.code;
          const talked = npc?.uttered ?? false;
          const status = !ready || !npc ? "인물 확인 중" : talked ? "이 장면 대화 완료" : dayDone ? "하루 종료" : budgetLeft <= 0 ? "오늘 대화 소진" : "대화 가능";
          return (
            <button key={character.code} type="button" onClick={() => onSelect(character.code)} disabled={disabled || !npc}
              aria-pressed={active} aria-label={`${character.name} · ${status}`}
              className={`flex min-w-0 flex-col items-center gap-1 border p-2 text-sm ${active ? "border-ink bg-ink text-paper" : "border-ink/30 hover:border-ink"} ${talked ? "grayscale opacity-55" : ""}`}>
              <span>{character.name}</span>
              <span className="text-xs">{status}</span>
            </button>
          );
        })}
      </div>
      <div className="flex min-h-36 flex-1 items-end justify-center overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        {portrait && <img src={portrait} alt={`${current?.name} 초상`} className={`h-36 w-auto max-w-full object-contain object-bottom sm:h-full ${current?.uttered ? "grayscale opacity-55" : ""}`} />}
      </div>
    </div>
  );
}

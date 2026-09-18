import type { DamageLevel, Illustration } from "@/contracts/api";
import { beatImage, nightClueImage, damageClass } from "@/lib/imageMap";

/** 대사창 위의 장면 그림. 줄의 image_id에 맞춘 선택은 낮 화면이 맡는다. */
export function SceneIntro({ beat, damageLevel, illustrations, index, lineIllustration, disabled, onSelect }: {
  beat: number;
  damageLevel: DamageLevel;
  illustrations: Illustration[];
  index: number;
  lineIllustration?: Illustration | null;
  disabled: boolean;
  onSelect: (index: number) => void;
}) {
  const illustration = lineIllustration ?? illustrations[index];
  const src = illustration ? nightClueImage(illustration.image_id) : null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="min-h-32 flex-1 overflow-hidden">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img key={`${beat}-${illustration?.image_id ?? index}`} src={src ?? beatImage(beat)} alt={src ? illustration.caption : ""}
          style={lineIllustration ? { animationIterationCount: 11 } : undefined}
          className={`${lineIllustration ? "cookie-glitch" : "fade-in"} h-full w-full object-contain object-top ${damageClass(damageLevel)} ${damageLevel >= 3 ? "opacity-80" : ""}`} />
      </div>
      {src && (
        <div className="shrink-0 border-t border-ink/10 bg-paper/90 px-4 py-2 text-center backdrop-blur-sm">
          <p className="text-base leading-relaxed sm:text-lg" aria-live="polite">{illustration.caption}</p>
          {!lineIllustration && illustrations.length > 1 && (
            <div className="mt-1 flex items-center justify-center gap-4 text-sm">
              <button type="button" disabled={disabled || index === 0} onClick={() => onSelect(index - 1)}
                className="border border-ink/30 px-3 py-1 disabled:opacity-30">이전 그림</button>
              <span>{index + 1} / {illustrations.length}</span>
              <button type="button" disabled={disabled || index === illustrations.length - 1} onClick={() => onSelect(index + 1)}
                className="border border-ink/30 px-3 py-1 disabled:opacity-30">다음 그림</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

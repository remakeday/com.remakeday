import type { Observation } from "@/contracts/api";
import { clueImage } from "@/lib/imageMap";

const SOURCE_LABEL = {
  scene: "장면에서 관찰",
  image: "이미지에서 관찰",
  statement: "발언을 들음",
  rule_result: "규칙 결과",
} as const;

export function ObservationCard({
  observation,
  compact = false,
  onOpen,
}: {
  observation: Observation;
  compact?: boolean;
  onOpen?: (observation: Observation) => void;
}) {
  const image = observation.illustrations.find((item) => clueImage(item.image_id));
  const src = image ? clueImage(image.image_id) : null;
  const content = (
    <>
      {src && (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={src}
          alt={image?.caption ?? ""}
          className={`${compact ? "h-20" : "max-h-56"} w-full object-contain bg-ink/5`}
        />
      )}
      <div className="space-y-1 p-3">
        <p className="text-base tracking-wide opacity-60">
          {observation.loop_n}회차 · {observation.scene_title}
        </p>
        <p className="text-base text-orange">{SOURCE_LABEL[observation.source_kind]}</p>
        <p className="text-lg leading-relaxed">{observation.text}</p>
        {observation.source_kind === "statement" && (
          <p className="text-base opacity-60">말했다는 사실의 기록이며, 내용의 참 여부는 별도다.</p>
        )}
      </div>
    </>
  );

  if (!onOpen) return <article className="overflow-hidden border border-current/25">{content}</article>;
  return (
    <button
      type="button"
      onClick={() => onOpen(observation)}
      className="overflow-hidden border border-current/25 text-left hover:border-current focus-visible:outline-2 focus-visible:outline-offset-2"
      aria-label={`${observation.scene_title} 원본 장면 열기`}
    >
      {content}
    </button>
  );
}

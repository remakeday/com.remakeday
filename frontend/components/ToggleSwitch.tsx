"use client";

import { useEffect, useRef, useState } from "react";
import type { Ref } from "react";

/**
 * 토글 뒤에 실제로 깔린 배경의 밝기를 측정한다.
 * fixed 오버레이라 mix-blend-mode가 페이지와 블렌드되지 않으므로(자체 스택 컨텍스트),
 * elementsFromPoint로 토글 중심 뒤의 첫 불투명 배경색을 읽어 광도를 계산한다.
 * bg-void(어두움) → false, bg-paper(밝음) → true.
 */
function useBackdropIsLight(ref: { current: HTMLElement | null }): boolean {
  const [light, setLight] = useState(false);
  useEffect(() => {
    const measure = () => {
      const el = ref.current;
      if (!el) return;
      const r = el.getBoundingClientRect();
      const x = r.left + r.width / 2;
      const y = r.top + r.height / 2;
      const prev = el.style.pointerEvents;
      el.style.pointerEvents = "none";
      const stack = document.elementsFromPoint(x, y);
      el.style.pointerEvents = prev;
      for (const node of stack) {
        if (node === el || el.contains(node)) continue;
        const bg = getComputedStyle(node as HTMLElement).backgroundColor;
        const m = bg.match(/rgba?\(([^)]+)\)/);
        if (!m) continue;
        const parts = m[1].split(",").map((s) => parseFloat(s));
        const alpha = parts[3] ?? 1;
        if (alpha === 0) continue; // 투명하면 더 뒤를 본다
        const lum = (0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]) / 255;
        setLight(lum > 0.6);
        return;
      }
      setLight(false);
    };
    measure();
    const id = window.setInterval(measure, 500);
    window.addEventListener("resize", measure);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("resize", measure);
    };
  }, [ref]);
  return light;
}

/**
 * 우상단 음성·BGM 공용 토글 스위치 — 배경 없이 라벨 + 트랙/노브만.
 * 뒤 배경 밝기에 따라 색이 뒤집힌다(어두운 화면=흰색, 밝은 화면=남색).
 */
export function ToggleSwitch({
  label,
  on,
  onClick,
  buttonRef,
  className,
}: {
  label: string;
  on: boolean;
  onClick: () => void;
  buttonRef?: Ref<HTMLButtonElement>;
  className?: string;
}) {
  const innerRef = useRef<HTMLButtonElement>(null);
  const light = useBackdropIsLight(innerRef);
  const fg = light ? "text-ink" : "text-white"; // 라벨 색
  const stroke = light ? "border-ink" : "border-white"; // 트랙 테두리
  const fill = light ? "bg-ink" : "bg-white"; // 트랙 채움·노브

  const setRefs = (node: HTMLButtonElement | null) => {
    innerRef.current = node;
    if (typeof buttonRef === "function") buttonRef(node);
    else if (buttonRef) (buttonRef as { current: HTMLButtonElement | null }).current = node;
  };

  return (
    <button
      ref={setRefs}
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={`${label} ${on ? "끄기" : "켜기"}`}
      onClick={onClick}
      className={`flex items-center gap-2 text-sm ${fg} ${className ?? ""}`}
    >
      <span>{label}</span>
      <span
        aria-hidden
        className={`flex h-4 w-8 items-center rounded-full border ${stroke} transition-colors ${
          on
            ? // 켜짐 — 채운 트랙 오른쪽에 노브 구멍(지름 12px)을 뚫어 배경이 비친다.
              `${fill} [mask-image:radial-gradient(circle_6px_at_calc(100%_-_8px)_50%,transparent_98%,black_100%)]`
            : "bg-transparent"
        }`}
      >
        {/* OFF 노브 — flex items-center가 세로 중앙을 맞춘다. ON 구멍과 같은 크기·같은 세로선. */}
        {!on && <span className={`ml-0.5 h-3 w-3 rounded-full ${fill}`} />}
      </span>
    </button>
  );
}

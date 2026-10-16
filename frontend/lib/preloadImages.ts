const warmed = new Set<string>();

/** 브라우저 캐시에 이미지를 미리 올려 다음 화면 전환을 빠르게 한다. */
export function preloadImages(srcs: Array<string | null | undefined>): void {
  if (typeof window === "undefined") return;
  for (const src of srcs) {
    if (!src || warmed.has(src)) continue;
    warmed.add(src);
    const image = new Image();
    image.decoding = "async";
    image.src = src;
  }
}

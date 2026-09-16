/** 음성·BGM 켜기/끄기 — 랜딩 환경설정과 게임 화면이 같은 값을 읽는다. 기본은 켜짐. */
const KEYS = {
  voice: "remakeday.voice.enabled",
  bgm: "remakeday.bgm.enabled",
} as const;

export type AudioChannel = keyof typeof KEYS;

export function audioEnabled(channel: AudioChannel): boolean {
  if (typeof window === "undefined") return true;
  try {
    return window.localStorage.getItem(KEYS[channel]) !== "off";
  } catch {
    return true;
  }
}

export function setAudioEnabled(channel: AudioChannel, on: boolean) {
  try {
    window.localStorage.setItem(KEYS[channel], on ? "on" : "off");
  } catch {
    // 저장 실패(시크릿 모드 등)는 조용히 넘긴다 — 이번 방문 동안만 유지된다.
  }
}

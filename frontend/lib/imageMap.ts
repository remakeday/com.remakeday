/**
 * 이미지 매핑 — 단일 출처.
 * 이미지 선택은 코드가 계산한 정수/enum 또는 시나리오가 지정한 이미지 ID만 사용한다.
 * LLM 출력(자유 텍스트)은 절대 이미지 선택에 관여하지 않는다.
 *
 * 근거 문서: docs/REMAKE_DAY_이미지제작서_v1.md (A~M군), 쿠키12종.md (N군)
 * 실제 파일: public/assets/{ID}.png — 문서의 img_{ID}_{slug}.png 대신
 *            실제 제공된 파일명이 {ID}.png 이므로 실제 파일 기준으로 매핑한다.
 * D군(손상 변형 12장)은 실제 파일이 없으므로 C군 원본 + CSS 클래스로 대체한다.
 */

import type { DamageLevel, Mood, WorldOutcome } from "@/contracts/api";

const ASSET = "/assets";

const img = (id: string): string => `${ASSET}/${id}.png`;

/** 진입 화면 (9:16) */
export const ENTRY_IMAGE = img("A01");

/** 관리자 스피커 팝업 (1:1) */
export const MANAGER_IMAGE = img("F01");

/** 원숭이손 팝업 (1:1) */
export const PAW_IMAGE = img("G01");

/** 밤 — 정답 제출 배경 (9:16) */
export const NIGHT_IMAGE = img("I01");

/** 신의개입 배경 (9:16) */
export const GOD_IMAGE = img("J01");

/** 멸망 종료 (9:16) */
export const DOOM_END_IMAGE = img("L01");

/** 하네스 공개 (9:16) */
export const HARNESS_IMAGE = img("M01");

/**
 * 아침 (3:2) — B군.
 * B01 원본 / B02 판 밀림(손상 1~2층) / B03 7시 13분(4회차 = damage_level 3 전용 연출.
 * 기획서 손상 표: 2회차 1층, 3회차 2층, 4회차 "7시 13분", 5회차 3층)
 */
export function morningImage(damageLevel: DamageLevel, loopN: number): string {
  if (loopN === 4) return img("B03"); // 7시 13분 — 형광등 꺼진 아침
  if (damageLevel === 0) return img("B01");
  return img("B02");
}

/**
 * 비트 배경 (3:2) — C군. C01~C06 = 비트 1~6.
 * 손상 변형(D군)은 파일이 없어 CSS 클래스로 근사한다 (damageClass 참조).
 */
export function beatImage(beat: number): string {
  const b = Math.min(Math.max(Math.trunc(beat), 1), 6);
  return img(`C0${b}`);
}

/** 시나리오가 현재 비트에 지정한 단서만 표시한다. 알 수 없는 ID는 기존 배경을 쓴다. */
const CLUE_IMAGES: Record<string, string> = {
  "clue-01": `${ASSET}/clues/C01-breakfast-clue-v2.png`,
  "clue-02": `${ASSET}/clues/clue-02-chaeyeon-checkup-reaction-v1.png`,
  "clue-03": `${ASSET}/clues/clue-03-after-checkup-v1.png`,
  "clue-04": `${ASSET}/clues/clue-04-evening-trays-v1.png`,
  "clue-05": `${ASSET}/clues/clue-05-chungsik-empty-bunk-v1.png`,
  "clue-06": `${ASSET}/clues/clue-06-zone-closure-broadcast-v1.png`,
  "clue-07": `${ASSET}/clues/clue-07-manager-ration-order-v1.png`,
  "clue-08": `${ASSET}/clues/clue-08-minseok-tray-record-v1.png`,
  "clue-09": `${ASSET}/clues/clue-09-minseok-broadcast-approach-v1.png`,
  "clue-10": `${ASSET}/clues/clue-10-eunsang-rumor-path-v1.png`,
  "clue-11": `${ASSET}/clues/clue-11-jun-band-observation-v1.png`,
  "clue-12": `${ASSET}/clues/clue-12-chaeyeon-checkup-route-v1.png`,
};

export function clueImage(imageId: string): string | null {
  return CLUE_IMAGES[imageId] ?? null;
}

/**
 * 손상 단계 → 화면 전체 CSS 클래스 (globals.css에 정의).
 * 0: 없음 / 1: 미세 기울기 / 2: 판 밀림 / 3: 어둡고 밀림
 */
export function damageClass(damageLevel: DamageLevel): string {
  return `damage-${damageLevel}`;
}

/**
 * NPC 초상 (3:4) — E군. 4인 × 3상태(calm·uneasy·wary).
 * E01~03 채연 / E04~06 민석 / E07~09 은상 / E10~12 준
 */
const NPC_BASE: Record<string, number> = {
  chaeyeon: 1,
  minseok: 4,
  eunsang: 7,
  jun: 10,
};

export function npcImage(code: string, _mood: Mood): string | null {
  const base = NPC_BASE[code];
  if (base === undefined) return null; // 알 수 없는 코드는 초상 없음 (실루엣 박스로 대체)
  return img(`E${String(base).padStart(2, "0")}`);
}

/** 멸망 전환 — truck/quiet는 H군(9:16), closure는 새 폐쇄 단서(3:2). */
const OUTCOME_IMAGE: Record<WorldOutcome, string> = {
  truck: img("H01"),
  quiet: img("H02"),
  closure: `${ASSET}/clues/clue-06-zone-closure-broadcast-v1.png`,
};

export function doomImage(outcome: WorldOutcome): string {
  return OUTCOME_IMAGE[outcome];
}

/**
 * 밤 단서 (9:16) — P군. P01~P05는 밤단서 v2 P.1의 회차별 치지직 이미지, 단서(clue-*) ID는 기존 단서 파일을 쓴다.
 * 이미지 ID는 서버의 night_clue.image_ids 값이며, 알 수 없는 ID는 띠를 그리지 않는다.
 */
export function nightClueImage(imageId: string): string | null {
  if (/^P0[1-5]$/.test(imageId)) return img(imageId);
  return clueImage(imageId);
}

/**
 * 클리어 (9:16) — K군.
 * K01 아직 이해하지 못했다 (50~99%) / K02 세계를 이해했다 (100%)
 */
export function clearImage(total: number): string {
  return total >= 100 ? img("K02") : img("K01");
}

/**
 * 쿠키 (치지직) — N군. (cell, level) → N01~N12
 * cause 1~3 → N01~03 / motive 1~3 → N04~06 / identity 1~3 → N07~09 / side_effect 1~3 → N10~12
 */
const COOKIE_BASE: Record<string, number> = {
  cause: 0,
  motive: 3,
  identity: 6,
  side_effect: 9,
};

export function cookieImage(cell: string, level: 1 | 2 | 3): string | null {
  const base = COOKIE_BASE[cell];
  if (base === undefined) return null;
  const n = base + level;
  return img(`N${String(n).padStart(2, "0")}`);
}

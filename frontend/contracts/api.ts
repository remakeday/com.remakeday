/**
 * REMAKE DAY — API 계약 v1 (MVP)
 * 원본: docs/spec/api_contract.md — backend 8500 / frontend 3500
 *
 * 이 파일은 계약 문서의 요청·응답을 그대로 옮긴 것이다. 임의 변경 금지.
 * 모든 응답은 JSON. 에러는 `{detail: string}` + 4xx. 잘못된 상태 전이는 409.
 */

// ── 타입 ──────────────────────────────────────────────

export interface CellScores {
  cause: number;
  motive: number;
  side_effect: number;
  identity: number;
}

export type DamageLevel = 0 | 1 | 2 | 3;
export type Mood = "calm" | "uneasy" | "wary";
export type NoteKind = "fragment" | "confirmed" | "rule_observation";
export type WorldOutcome = "truck" | "quiet" | "closure";
export type ClosedBy = "clear" | "doom" | "understood" | "understood_all";
export type ObservationSource = "scene" | "image" | "statement" | "rule_result";
export type ObservationVerification = "observed" | "reported";
export type QuestionStatus = "supported" | "contradicted" | "unknown";
export type GodAnswer = string;

export interface Npc {
  code: string;
  name: string;
  mood: Mood;
  /** 이번 비트의 직접 질문에 답변을 완료했는지. true면 다음 비트까지 새 질문이 잠긴다. */
  uttered: boolean;
}

export interface Note {
  id: number;
  kind: NoteKind;
  text: string;
  loop_n: number;
  observation_ids: string[];
  sources: Observation[];
}

export interface PawOffer {
  offer_id: string;
  rule_label: string;
  shown_reason: string | null;
}

export interface Cookie {
  text: string;
  cell: string; // cause | motive | side_effect | identity
  level: 1 | 2 | 3;
}

/** 비트 경계에서 NPC 둘이 지나가며 주고받는 2~4줄 (발화 예산 무관) */
export interface AmbientUtterance {
  lines: { code: string; name: string; text: string }[];
}

/** 이 비트에서 새로 발견된 감각 파편 (노트에 적힌 직후) */
export interface NoteFound {
  id: number;
  kind: string;
  text: string;
}

/** 시나리오가 지정한 현재 비트의 관찰 이미지. */
export interface Illustration {
  image_id: string;
  caption: string;
}

/** 대사창 한 줄 — 서버가 응답 조립 때 계산한다(낮 화면 VN 설계 §3). 저장하지 않는다. */
export type LineKind =
  | "scene" | "action" | "rule_result" | "statement" | "broadcast"
  | "npc" | "paw_effect" | "fragment" | "system";
export interface Line {
  kind: LineKind;
  speaker: string | null; // 인물 이름·"관리자"·null
  text: string;
  image_id: string | null; // 이 줄에서 바꿔 보여 줄 장면 그림
  voice_id: string | null; // 음성이 있는 줄만 — 지금은 항상 null(프론트 voiceForLine이 고른다)
  observation_id: string | null; // 단서 기록과 연결(NEW·그림 열기)
}

export interface Observation {
  observation_id: string;
  attempt_id: string;
  loop_id: string;
  loop_n: number;
  beat: number;
  scene_id: string;
  scene_title: string;
  actor: string | null;
  text: string;
  source_kind: ObservationSource;
  verification: ObservationVerification;
  illustrations: Illustration[];
  rule_id: string | null;
}

// ── 세션·회차 (P1) ────────────────────────────────────

export interface CreateSessionReq {
  prior_attempt_id?: string;
}
export interface CreateSessionRes {
  attempt_id: string;
  attempt_n: number;
  entry_lines: string[]; // 3줄
  prior_cell_results: CellScores | null;
}

export interface StartLoopRes {
  loop_id: string;
  loop_n: number;
  morning_text: string;
  damage_level: DamageLevel;
  budget_left: number;
  /** 첫 장면에서 자연스럽게 들리는 무료 대화. */
  ambient?: AmbientUtterance | null;
  beat: number; // 시작은 1
  beat_title: string;
  narration: string;
  broadcast: string | null;
  illustrations: Illustration[];
  /** 전날 걸린 규칙이 부작용을 만들었을 때만 — "어제는 없던 일이 있었다" 톤 한 줄 */
  aftermath: string | null;
  /** 오늘 세계에 걸린 규칙 — 유저용 문구. 없으면 빈 배열 */
  active_rules: string[];
  observations: Observation[];
  /** 대사창 줄 — 장면 서술 → 방송 → 행동·규칙 → 혼잣말 → 단서 조각 → 기록 알림 */
  lines: Line[];
}

export interface UtteranceReq {
  target: string; // NPC code
  text: string;
  request_id?: string; // UUID. 같은 질문의 재시도에는 같은 ID를 보낸다.
}
export interface UtteranceRes {
  utterance_id: string;
  reply: string;
  npc: Npc;
  budget_left: number;
  beat: number;
  tool_used: boolean;
  observations: Observation[];
  /** 무의미한 입력이라 인물의 반응이 아닌 대체 문장을 돌려줬을 때만 true. */
  gated?: boolean;
  /** 답변을 문장 단위로 나눈 npc 줄. gated면 system 줄 하나 */
  lines: Line[];
}

export interface BeatNextRes {
  beat: number;
  beat_title: string;
  narration: string;
  broadcast: string | null;
  illustrations: Illustration[];
  paw_offer: PawOffer | null;
  day_done: boolean;
  ambient: AmbientUtterance | null;
  note_found: NoteFound | null;
  observations: Observation[];
  /** 현재 장면 처리 후 발화 예산. 구버전 응답에서는 없을 수 있다. */
  budget_left?: number;
  /** 대사창 줄. day_done이면 빈 배열 */
  lines: Line[];
}

export interface PawRespondReq {
  offer_id: string;
  accept: boolean;
}
export interface PawRespondRes {
  applied: boolean;
  rule_label: string | null;
  /** 수락 즉시 장면 — 소원 장면이 지금 비트면 새로 생긴 서술·삽화·관찰. 아니면 null·빈 배열. */
  narration: string | null;
  illustrations: Illustration[];
  observations: Observation[];
  /** 수락 즉시 장면에서 새로 생긴 줄만. 아니면 빈 배열 */
  lines: Line[];
}

export interface NotesRes {
  notes: Note[];
}

export interface NpcsRes {
  npcs: Npc[];
}

export interface ObservationsRes {
  observations: Observation[];
}

// ── 밤 (P2) ───────────────────────────────────────────

export interface NightDraftReq {
  tapped_note_ids: number[];
  inherited_note_ids?: number[];
  free_text: string;
}
export interface NightDraftRes {
  night_id: string;
  claims: string[]; // ≤8 — 직접 쓴 글에서만 나온다. 고른 기록은 참고용이라 들어가지 않는다
  is_question: boolean[]; // claims와 같은 순서 — 질문형 문장 안내용, 채점과 무관
}

export interface PatchClaimsReq {
  claims: string[];
}
export interface PatchClaimsRes {
  claims: string[];
  is_question: boolean[];
}

export interface PreviousAnswer {
  loop_n: number;
  free_text: string;
  claims: string[];
  tapped_note_ids: number[];
  draft_text: string;
}

export interface PreviousAnswerRes {
  previous_answer: PreviousAnswer | null;
}

/** 밤 점수 화면이 이름을 꺼내는 칸 */
export type HintCell = "cause" | "motive";

export interface SubmitRes {
  total: number;
  /** 호환용 50% 분류. 생존·회차 종료·회고 접근에는 사용하지 않는다. */
  passed: boolean;
  loop_n: number;
  world_outcome: WorldOutcome | null;
  is_final: boolean;
  closed_by: ClosedBy | null;
  cells: CellScores | null;
  cookie: Cookie | null;
  intervention_available: boolean;
  /** 5회차 제출 완료 후 — 이해한 셀(≥80)의 결말 줄만 서버가 열어 내려보낸다 */
  ending_lines: string[] | null;
  /** 5회차 제출 완료 후 — confirmed 명제만 truth 전문, 나머지는 서버가 잠근다 */
  truth_reveal: TruthReveal[] | null;
  /** 매일 밤 — 칸별 점수는 숨긴 채 원인·동기 중 잡힌 칸의 진행 문장만. 잡힌 칸이 없으면 null */
  cell_feedback: string | null;
  /** 세계와 닿지 않은 주장 수 (감점 없음, 정보만) */
  wrong_claim_count: number;
  /** 매일 밤 — 인정(확인·부분)된 내 문장. 칸 구분 없이 쓴 순서대로. 진실 문장은 담지 않는다 */
  accepted_claims: string[];
  /** 매일 밤 — 점수 0인 칸 코드(원인·동기만, 정체는 안내하지 않는다). 문구는 화면이 정한다 */
  empty_cells: HintCell[];
  /** 밤 단서 시퀀스 — 결말 전환에서 방송 → 치지직 → 캡션 순서로 재생. 회차 표가 없는 시나리오는 null */
  night_clue: NightClue | null;
  /** 신의 질문 추천(≤3) — 오늘 기록으로 답할 수 있는 찾기 질문(방송 → 소등 뒤 단서 → 인물 행동). 가설 없음. 질문 응답의 같은 필드로 갱신 */
  suggested_questions: string[];
}

/**
 * 밤 단서(밤단서 v2 P.1). 캡션과 방송은 서버가 「N회차 · 소등 후」 관찰로 저장한다 — 프론트는 문장을 만들지 않는다.
 */
export interface NightClue {
  loop_n: number;
  /** 띠가 꺼진 뒤 바탕 위에 남는 문장 */
  caption: string;
  /** 치지직 띠 안 이미지 ID (1~2장, imageMap.nightClueImage) */
  image_ids: string[];
  /** 관리자 밤 방송 음원 ID (MA08~12) */
  voice_id: string;
  /** 방송 대본 */
  broadcast: string;
  /** 트럭 결말 밤에 캡션 뒤에 붙는 기존 트럭 파편 한 줄 */
  outcome_line: string | null;
}

// ── 신의개입 (P3) ─────────────────────────────────────

export interface GodQuestionReq {
  text: string;
}
export interface GodQuestionRes {
  answer: GodAnswer;
  /** 판정 접두 — 맞다. / 아니다. / 그건 알 수 없다. / 왜인지는 내가 말할 수 없다. 그 전에 일어난 일은 말할 수 있다. */
  verdict: string;
  detail: string | null;
  remaining: number;
  status: QuestionStatus;
  evidence_ids: string[];
  evidence: Observation[];
  next_observation: string | null;
  /** 항상 null — 리드 사실 공개는 제거됨(F7). 호환용 필드 */
  unlocked_note: string | null;
  /** guide = 게임 목적·사용법 안내 답. 판정(verdict "")·근거·조언이 없고 횟수를 쓰지 않는다 */
  kind: "answer" | "guide";
  /** "알 수 없다"라 횟수를 돌려받았다 (같은 밤 3회까지, 같은 질문 재입력은 제외). remaining에 이미 반영 */
  refunded: boolean;
  /** 추천 질문(≤3) — 같은 밤에 이미 한 질문은 빠진다. 제출 응답의 목록을 이걸로 갈아 끼운다 */
  suggested_questions: string[];
}

// ── 진실 공개·추리 여정 ───────────────────────────────

export type ClaimVerdict = "confirmed" | "partial" | "none";

export interface TruthReveal {
  code: string;
  cell: "cause" | "motive" | "identity" | "side_effect";
  verdict: ClaimVerdict;
  my_claim: string | null;
  /** confirmed일 때만 서버가 내려보낸다 */
  truth: string | null;
}

export interface JourneyLoop {
  loop_n: number;
  total: number;
  passed: boolean;
  new_confirmed: { code: string; my_claim: string | null }[];
  unlocked_notes: string[];
}

export interface JourneyRes {
  loops: JourneyLoop[];
  final: {
    cells: CellScores;
    closed_by: ClosedBy | null;
    truth_reveal: TruthReveal[];
  } | null;
  unresolved: { cell: string; hint: string }[];
}

export interface GodOption {
  index: 1 | 2 | 3;
  label: string;
  target: string;
  action: string;
  effect: "enforce" | "suppress";
  when_beat: number | "any";
  reason: string;
  evidence_ids: string[];
  expected_observation: string;
}
export interface GodOptionsRes {
  options: GodOption[];
}

export interface GodRuleReq {
  choice: "1" | "2" | "3" | "custom";
  custom_text?: string;
  preview_id?: string;
}
export interface GodRuleRes {
  ok: boolean;
  rule_label: string | null;
  conflicts: string[];
  reason: string | null;
}

export interface RulePreviewReq {
  custom_text: string;
}

export interface RulePreview {
  preview_id: string;
  original_text: string;
  executable: boolean;
  interpretation: string | null;
  limitations: string[];
  alternatives: string[];
  conflicts: string[];
  rule: null | {
    target: string;
    action: string;
    effect: "enforce" | "suppress";
    when_beat: number | "any";
    label: string;
  };
}

export interface RuleOpportunity {
  loop_n: number;
  beat: number;
  condition: string;
  actual_action: string | null;
  result: "obeyed" | "violated" | "conflict" | "not_evaluable";
  observation_ids: string[];
  side_effect: string | null;
}

export interface Experiment {
  rule_id: string;
  intent: string | null;
  interpretation: string;
  opportunities: RuleOpportunity[];
}

export interface Metric {
  numerator: number | null;
  denominator: number;
  value: number | null;
  reviewed: number;
  method: string;
}

// ── 판 종료 후 (P5) ───────────────────────────────────

export interface HarnessRes {
  rules: {
    rule_id: string;
    source: "monkey_paw" | "paw_effect" | "user_choice" | "user_custom";
    target: string;
    when_beat: number | null;
    effect: "suppress" | "enforce";
    action: string;
    shown_reason: string | null;
    hidden_side_effect: string | null;
    created_loop: number;
    conflict: boolean;
  }[];
  harness_summary: {
    total_events: number;
    harness_interventions: number;
    fallbacks: number;
    paw_accepted: number;
    recommended_rules: number;
    custom_rules: number;
    rule_conflicts: number;
    questions_asked: number;
    rule_success_rate: number | null;
    tool_side_effects: { loop_n: number; beat: number; text: string }[];
    model_calls: number | null;
    model_attempts: number | null;
    model_call_coverage: "complete_logged_calls" | "legacy_partial_or_unavailable";
  };
  measurement_version: string;
  experiments: Experiment[];
  metrics: {
    note_source_linkage: Metric;
    rule_compliance: Metric;
    question_grounding: Metric;
    recommendation_relevance: Metric;
    custom_semantics: Metric;
    checker_accuracy: Metric;
  };
}

export interface InspectorRes {
  events: unknown[];
  patches: unknown[];
  paw_rules: unknown[];
  scoring: unknown[];
}

export interface HealthRes {
  db: string;
}

// ── 타입드 fetch 클라이언트 ───────────────────────────

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8500";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;
  /** 과잉 사용 방지 허들 응답의 code (예: daily_attempt_limit, daily_cap) */
  readonly code?: string;
  /** 429 응답의 재시도 대기 초 */
  readonly retryAfter?: number;
  constructor(status: number, detail: string, code?: string, retryAfter?: number) {
    super(`[${status}] ${detail}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
    this.retryAfter = retryAfter;
  }
}

async function request<T>(
  method: "GET" | "POST" | "PATCH",
  path: string,
  body?: unknown,
  extraHeaders: Record<string, string> = {},
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...extraHeaders,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      credentials: "include", // 세션 쿠키(rd_session)를 함께 보낸다
    });
  } catch {
    throw new ApiError(0, "서버에 연결할 수 없습니다");
  }
  if (!res.ok) {
    let detail = res.statusText || "요청 실패";
    let code: string | undefined;
    let retryAfter: number | undefined;
    try {
      const data = (await res.json()) as {
        detail?: string | { detail?: string; retry_after?: number } | unknown[];
        code?: string;
      };
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) detail = "입력이 너무 길거나 형식이 맞지 않는다";
      else if (data.detail && typeof data.detail === "object") {
        if (typeof data.detail.detail === "string") detail = data.detail.detail;
        if (typeof data.detail.retry_after === "number") retryAfter = data.detail.retry_after;
      }
      if (typeof data.code === "string") code = data.code;
    } catch {
      // 본문이 JSON이 아니면 statusText 유지
    }
    if (retryAfter === undefined) {
      const header = res.headers.get("Retry-After");
      const parsed = header !== null ? Number(header) : NaN;
      if (!Number.isNaN(parsed)) retryAfter = parsed;
    }
    throw new ApiError(res.status, detail, code, retryAfter);
  }
  return (await res.json()) as T;
}

export const api = {
  // 세션·회차
  createSession: (req: CreateSessionReq) =>
    request<CreateSessionRes>("POST", "/sessions", req),
  startLoop: (attemptId: string) =>
    request<StartLoopRes>("POST", `/sessions/${attemptId}/loops`),
  sendUtterance: (loopId: string, req: UtteranceReq) =>
    request<UtteranceRes>("POST", `/loops/${loopId}/utterances`, req),
  nextBeat: (loopId: string) =>
    request<BeatNextRes>("POST", `/loops/${loopId}/beats/next`),
  respondPaw: (loopId: string, req: PawRespondReq) =>
    request<PawRespondRes>("POST", `/loops/${loopId}/paw/respond`, req),
  getNotes: (loopId: string) =>
    request<NotesRes>("GET", `/loops/${loopId}/notes`),
  getObservations: (loopId: string) =>
    request<ObservationsRes>("GET", `/loops/${loopId}/observations`),
  getNpcs: (loopId: string) => request<NpcsRes>("GET", `/loops/${loopId}/npcs`),

  // 밤
  nightDraft: (loopId: string, req: NightDraftReq) =>
    request<NightDraftRes>("POST", `/loops/${loopId}/night/draft`, req),
  getPreviousAnswer: (loopId: string) =>
    request<PreviousAnswerRes>("GET", `/loops/${loopId}/night/previous`),
  patchClaims: (nightId: string, req: PatchClaimsReq) =>
    request<PatchClaimsRes>("PATCH", `/nights/${nightId}/claims`, req),
  submitNight: (nightId: string) =>
    request<SubmitRes>("POST", `/nights/${nightId}/submit`),

  // 신의개입
  askGod: (nightId: string, req: GodQuestionReq) =>
    request<GodQuestionRes>("POST", `/nights/${nightId}/questions`, req),
  getGodOptions: (nightId: string) =>
    request<GodOptionsRes>("GET", `/nights/${nightId}/options`),
  previewRule: (nightId: string, req: RulePreviewReq) =>
    request<RulePreview>("POST", `/nights/${nightId}/rule/preview`, req),
  chooseRule: (nightId: string, req: GodRuleReq) =>
    request<GodRuleRes>("POST", `/nights/${nightId}/rule`, req),

  // 판 종료 후
  getJourney: (attemptId: string) =>
    request<JourneyRes>("GET", `/attempts/${attemptId}/journey`),
  getHarness: (attemptId: string) =>
    request<HarnessRes>("GET", `/attempts/${attemptId}/harness`),
  getInspector: (attemptId: string, token: string) =>
    // 토큰은 헤더로만 — URL 쿼리는 접근 로그·브라우저 기록에 남는다
    request<InspectorRes>("GET", `/attempts/${attemptId}/inspector`, undefined, {
      "X-Inspector-Token": token,
    }),
  getHealth: () => request<HealthRes>("GET", "/health"),

  // 인증 — Google OAuth 세션
  getMe: () => request<SessionUser>("GET", "/api/v1/auth/me"),
  logout: () => request<{ ok: boolean }>("POST", "/api/v1/auth/logout"),
};

export interface SessionUser {
  sub: string;
  email: string;
  name: string;
  picture: string;
}

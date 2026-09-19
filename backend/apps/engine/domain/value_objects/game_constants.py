"""게임 상수 — 수치의 의미는 전부 여기 (계산은 코드)."""

LOOPS_PER_ATTEMPT = 5
BEATS_PER_LOOP = 6

SUSPICION_THRESHOLD = 60  # 돌파 시 반대 행동
TRUST_RETENTION = 0.05  # 회차 리셋 시 신뢰 잔류율
TRUST_GAIN_CAP = 6  # 비용 행동 1회당 신뢰 상한
DELTA_CAP = 10  # LLM 제안값 클램프 (±)

ASK_BUDGET_PER_LOOP = 2  # NPC 탐문 예산
MANAGER_BUDGET_PER_LOOP = 2  # 관리자 보정 예산
MANAGER_CHECK_BEATS = (2, 4, 6)  # 관리자 점검이 도는 비트 (매 비트 → 축소)

MISMATCH_SPEAKER_SUSPICION = 12  # 거짓 출처 발각 시 발화 NPC의 대유저 의심
ASK_TARGET_SUSPICION = 6  # ask_npc 대상 의심 상승

QUESTIONS_PER_NIGHT = 3  # 신의개입 질문 — 고정, "알 수 없다"도 차감한다 (환급 철회 2026-09-18, 테스터12 F5)
LADDER_SCORE_STEPS = (25.0, 50.0, 75.0)  # 신의 질문 공개 사다리 — 점수로 한 칸씩 앞당기는 기준
CLAIMS_MAX = 8

CELL_FULL_THRESHOLD = 0.8  # 칸 만점 임계 (확인 비율)
PASS_THRESHOLD = 50.0  # 기존 passed/closed_by 호환용 분류선 — 회차 종료·생존과 무관
UNDERSTANDING_WEIGHTS = {"cause": 0.35, "motive": 0.35, "identity": 0.30}

ANOMALY_CLOSURE = 3  # 이상자 수 → 폐쇄
RUMOR_THRESHOLD = 3  # 소문 지수 임계 → 조용히 이송

PAW_MIN_YESTERDAY = 40.0  # 원숭이손: 전날 점수 조건
PAW_MAX_PER_ATTEMPT = 2
PAW_DECLINE_LIMIT = 2  # 원숭이손: 같은 판 연속 거절 한도

CELLS = ("cause", "motive", "side_effect", "identity")
COOKIE_TIE_ORDER = ("cause", "motive", "side_effect", "identity")

# 밤 제출문을 문장·줄 단위로 나눌 때의 칸 상한. 자유서술이 2000자 상한이라
# 보통 길이 문장으로는 닿지 않는다 — 실제로 뭉치는 일이 없도록 두고 API 입력 상한으로만 쓴다.
MAX_CLAIMS = 40

# 클리어 화면 플레이 평가 항목 — 화면 문구는 재미·몰입도 / 참신성 / AI 활용 체감 / 완성도 / 추천 의향.
# 마이그레이션은 그 시점 스냅샷이라 이 상수를 쓰지 않고 자기 사본을 갖는다.
SURVEY_SCORE_FIELDS = ("fun", "novelty", "ai_agency", "polish", "recommend")

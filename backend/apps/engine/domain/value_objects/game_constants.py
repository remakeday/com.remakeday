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

QUESTIONS_PER_NIGHT = 3  # 신의개입 질문
CLAIMS_MAX = 8

CELL_FULL_THRESHOLD = 0.8  # 칸 만점 임계 (확인 비율)
PASS_THRESHOLD = 50.0  # 기존 passed/closed_by 호환용 분류선 — 회차 종료·생존과 무관
UNDERSTANDING_WEIGHTS = {"cause": 0.35, "motive": 0.35, "identity": 0.30}

ANOMALY_CLOSURE = 3  # 이상자 수 → 폐쇄
RUMOR_THRESHOLD = 3  # 소문 지수 임계 → 조용히 이송

PAW_MIN_YESTERDAY = 40.0  # 원숭이손: 전날 점수 조건
PAW_MAX_PER_ATTEMPT = 2

CELLS = ("cause", "motive", "side_effect", "identity")
COOKIE_TIE_ORDER = ("cause", "motive", "side_effect", "identity")

# devlog

작업지시서 §0의 네 박자 중 ④ 기록. "고쳤다"가 아니라 "몇에서 몇으로".

---

## 2026-09-06 (야간) — MVP 압축 실행: P1~P5 + 프론트 F0~F2

사용자 위임(전 단계 자동 승인·서브에이전트 모드·아침 데모 목표)에 따라 지시서 v1.1 + 모델정책 v1 기준으로 연속 구현. 설계 기록은 `docs/design/P2-P5-mvp.md`.

**완료 조건 실측 (지시서 대비)**

- P1: fake 6비트 완주 E2E ✅ (5회차 전체 완주 E2E로 초과 달성) / 하네스 ON 금칙어 0·OFF 누설 재현 ✅ (ablation 테스트 2건) / 의심 임계 60 반대 행동 ✅ / ask_npc 불일치 발각(발화자 +12·대상 +6) ✅
- P2: 덧붙임 검사(서술어 어미 처리 포함) ✅ / 수정 1회 제한(2번째 409) ✅ / 칸 80% 만점·1회차 부작용 제외 ✅ — 소설 10종·판정 일치율은 P6 러너로 이관
- P3: Advisor의 ScenarioPort 무의존 import 테스트 ✅ / 4형식 스키마 강제 ✅ / 충돌 감지 ✅ / 직접 쓰기 거부(대상·어휘 검증) ✅
- P4: 보정 예산 2 초과 불가 ✅ / 원숭이손 조건(1회차 무조건·40%·판당 2) 테스트 4케이스 ✅ / hidden_side_effect는 인스펙터에만 ✅ / 원인 체인→Advisor 연결 ✅
- P5: 쿠키 선택 7케이스(구간·중복 승급·정체 잠금·12개 소진) ✅ / 하네스 엔드포인트 미100% 403 ✅ / 재도전 prior 연결 ✅
- 테스트 총계: **48 → 87 passed** (0.4→1.4s) / import-linter 4계약 유지 / 코어 금칙어 0 (78파일)

**실 LLM 스모크 (exaone3.5:7.8b + gemma3:12b + gemini-embedding)**

- 발화: "밥 왜 남겼어?" → "배 안 고파서." (2.0s) — 7세 톤 그대로
- 회차 시작 36.4s(첫 모델 로드 포함), 비트 경계(Manager 점검) 5.9s, 밤 채점(정리+판정 12콜) 15.1s, 신의개입 질문 0.9s·후보 6.4s
- 1회차 시연 판: 정리 2주장 → 총점 8.3% → truck 멸망 → 신의개입 → 규칙 1 적용 → 2회차 진입 가능 확인
- 2회차 채점 정합성: 원인 칸만 서술한 답 → **33.3%** (= 원인 100 · 동기 0 · 정체 0의 3칸 평균 — 칸 구조가 의도대로 동작). 관찰: Normalizer가 동기 문장("이송된다고 믿어서") 1개를 누락 — 정리 확인(수정 1회) 화면이 보완 장치. P6 게이트에서 덧붙임률과 함께 계측 대상
- ollama keep_alive 2h + start_demo.sh 워밍업 추가 (유휴 언로드 → 회차 시작 37s 재발 방지), 임베딩 장애 시 순서 기반 후보 폴백 추가

**결정·트레이드오프**

1. Agent delta는 모델정책 v1의 -10..10 제안값 방식 채택 (P1 설계서의 단계값 절충안 폐기)
2. `harness_event` 이벤트 타입 추가 → 17종에서 **18종** (부록 C 17 + 모델정책 §9)
3. RAG top3는 파이썬 코사인 (문장 수십 개 규모 — pgvector 질의 보류)
4. 원숭이손·규칙 후보의 행동 어휘/대상 검사는 ablation과 무관하게 상시 ON (게임 정합성)
5. 소문 지수 = ask_npc 호출 수 근사 / Manager 밤의 결정 사유 문장 생략 / 충돌 손상 +1 보류 — P6 이후 재고 3건
6. 유스케이스가 ORM 행을 덕타이핑으로 수용 (레포 포트 프로토콜 생략 — MVP 트레이드오프)
7. 프론트: Next.js 16 + TS strict + Tailwind v4, 포트 3500, 이미지 45장 매핑(`lib/imageMap.ts`), D군(손상 변형) 실파일 부재로 CSS 근사

**P6 검증 러너 5종 + 실측 (게이트 예비 판정)**

- `run_leak_test.py`: 누설률 **ON 0% vs OFF 40%** (하네스 적발 7건, n=2×5발화) — 게이트 조건 "OFF가 유의미하게 높음" **PASS** (ablation 데모 가능)
- `run_judge_consistency.py`: 판정 일치율 **100%** (3세트×3회), 소설 오확인 **0/3** — **PASS** (풀런 n=10·소설 10 남음)
- `run_age7_check.py`: exaone3.5:7.8b+정책 **2/5** (n=2 스모크) — 3턴 망각 항목 0.0 (모델이 4턴 전을 정확히 인용). **게이트 미달 신호** → n=20 풀런 + gemma3:4b pull 비교 필요. 미달 확정 시 폴백(발표 문구 "모델과 정책의 선택") 결정 기록
- `run_selfplay.py`: 성실 페르소나 1판 1회차 완주 82.7s (발화 3·원숭이손 수락·밤 제출) / `run_paw_eval.py`: 인프라 동작, 다회차 데이터 대기
- 전 결과 `docs/metrics.yml` 5줄 append

**P7 전이 어댑터 (audit) 완료**

- `scenario_audit/` 감사 대응: 인물 5(핵심 3+숨음·소실 2), 정답 주장 9, 쿠키 12, 금칙어 9, engine 수정 **0줄**
- 계약 테스트 3시나리오 22개 통과 + `SCENARIO=audit` E2E(5회차 완주) 통과 — 방어선 ⑤ 초록

**최종**: pytest **94 passed** · import-linter 4계약 · 코어 금칙어 0 (78파일) · CI 초록
**남긴 것**: age7 게이트 풀런(n=20, gemma3:4b 비교), selfplay 30판, 밤 채점 100초 실측(F3), Cloudflare 터널 배포(F3 — 로컬 데모라 보류), Normalizer 동기 문장 누락 계측

## 2026-09-06 — P0 뼈대 완료

**완료 조건 실측**

- `GET /health` → `{"scenario":"a","harness":"on","models":{npc·advisor·manager·embedding: "fake"},"db":"ok"}` (uvicorn 127.0.0.1:8500 실기동 확인)
- 이벤트 기록·조회: **17/17 타입** 왕복 테스트 통과 (전체 pytest **48 passed**, 0.39s)
- CI 초록: pytest 48 + import-linter **4 계약 0 위반**(82파일 104의존 분석) + 코어 금칙어 **0건**(apps/engine 57파일 검사)
- 시드 upsert 실기동 반영: 인물 6 · 비트 6 · 정답 주장 10 · 쿠키 12 (재기동 시 중복 0, 값 변경·행 삭제 반영 테스트 통과)
- Alembic 초기 마이그레이션 1개 → 테이블 7개 (events, scenario_* 4종, truth_claim_embeddings, alembic_version)

**결정**

1. 이벤트 저장 = **옵션 A**: 단일 `events` 테이블(JSONB) + Pydantic DTO 17종 (사용자 승인)
2. 부록 C `session_end.pig_word_confirmed` → `identity_word_confirmed`로 개명 — 코어 시나리오 무지 원칙(§1-6)과 필드명이 충돌. 의미 동일, 프론트 계약 시 매핑 문서화 필요
3. 금칙어 CI grep: 1글자 인물명은 한글 lookaround 경계 적용 — "내려준다·기준" 오탐 제거. 한계: 1글자 이름+조사 결합은 CI가 못 잡음 (런타임 검출은 P1 하네스 소관)
4. side_effect 정답 주장은 시드 0개 — 기획서 §7.3이 "규칙 로그에서 자동 생성"으로 명시, P2 Evaluator 소관
5. 시드 테이블 4종은 라우터 없는 참조 데이터라 프랙탈 11-file set 예외 (orm+repository만)
6. import-linter 컴포지션 루트 예외: `scenario_factory → apps.scenarios.**`만 ignore — 그 외 엔진→시나리오 경로는 전부 차단 확인 (심은 위반 검출 스모크 통과)
7. `apps/dummy` 템플릿 삭제 (P0 완료 시점, 사용자 승인)
8. DB 호스트 포트 5435 (5432·5433·5434가 타 프로젝트 사용 중), 컨테이너 `pigfarm-db`, pgvector pg17
9. GitHub 미설정 (사용자 결정 보류) — CI는 `backend/scripts/ci.sh` 로컬 실행

**다음**: P1 (하루 — 상태 머신·Agent·하네스). 시작 전 `docs/design/P1-day.md` 설계서 승인 필요.

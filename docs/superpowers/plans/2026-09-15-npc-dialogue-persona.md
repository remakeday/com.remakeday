# NPC 대화·페르소나 구현 계획

> For agentic workers: use test-driven-development for behavior changes and dispatching-parallel-agents for the independent frontend and scenario tasks. Keep backend memory orchestration together.

**Goal:** 질문을 이해하고 자기 경험·이유를 쉬운 말로 답하는 NPC, 당일 기억과 루프 경계를 구현한다. 사용자 추가 지시로 장면당 캐릭터 1회 제한을 복구한다.

**Architecture:** 시나리오가 성격·기본 지식·행동의 소유자/목격자를 제공한다. 기존 NPC JSON 기억에 출처가 있는 당일 기억을 저장하고 삭제 표시를 유지한다. 직접 질문·도구·작성 대사가 같은 가림 상태를 사용한다. 기존 장면 트랜잭션과 루프 잠금으로 발화와 예산·관찰·노트를 함께 저장한다.

**Tech Stack:** Python/Pydantic/FastAPI/SQLAlchemy/PostgreSQL, Next.js/React/TypeScript, pytest, Playwright. Kanana로 먼저 평가한 뒤 로컬 NPC를 Gemma `think=off`로 변경했다.

**Spec:** [승인된 설계](../specs/2026-09-15-npc-dialogue-persona-design.md)

## Global Constraints

- 현재 미커밋 변경사항을 보존한다. 사용자가 작업 중인 현 체크아웃에 적용하며 커밋·푸시·병합하지 않는다.
- 최초 비교는 `kanana1.5:8b-q4km`를 유지한다. 새 기준에서 한계가 확인되면 승인 설계 §3에 따라 같은 질문·문맥으로 설치된 대체 모델을 비교한다. 평가 결과는 기존 7세 평가와 별도 버전으로 기록한다.
- 새 루프에서 네 NPC의 당일 기억은 초기화하고 신뢰 `round(trust * .05)`만 유지한다.
- 하루 대화 예산 8/7/6/5/4, 무료 장면 이동, 5회차 구조는 유지한다.
- UI에 내부 지식 ID·페르소나·숨은 정답을 노출하지 않는다.
- 백엔드/프론트엔드 AGENTS.md, 소실·규칙 조건, 기존 헤드리스 브라우저 규칙을 지킨다.
- 실제 모델 의미 평가는 단어 검사가 아닌 원문과 허용 근거를 함께 검토한다.

## Task 1 — 당일 기억과 공통 지식 경계

Files: `backend/apps/engine/domain/entities/npc_rules.py`, 새 `app/use_cases/npc_context.py`, `app/use_cases/game_support.py`, `app/dtos/scenario_dto.py`, `adapter/outbound/orms/game_state_orm.py`, 관련 pure/engine tests.

- [x] 기억 보존·특정 출처 삭제·삭제 연관 문답 가림·새 출처 재학습의 실패 테스트를 먼저 실행한다.
- [x] 기억 항목에 ID, 시점, 종류, 화자/청자, 출처, 삭제 표시를 저장한다. 기존 문자열 기억은 읽기 호환한다. 하루 문답을 절단하지 않는다.
- [x] 시나리오 DTO에 `KnowledgeDTO(id, kind, text, source)`, `CharacterDTO.knowledge/dialogue_examples`, `SceneActionDTO.witnesses`를 추가한다.
- [x] 시작 전 지식과 현재 루프 기억만 프롬프트에 전달한다. 소실 인물 관련 항목을 입력에서도 제거한다. 과거 플레이어 노트를 읽지 않는다.
- [x] 실제 실행된 행동에서 당사자에게 explanation/known_source, 명시된 목격자에게 공개 관찰만 전달한다. 방송과 참여한 잡담도 출처별로 저장한다.
- [x] 같은 입력 구성을 직접 발화와 ask_npc에 사용한다. 과거 발언 사실과 현재 기억을 구분한다.
- [x] 관리자의 memory_delete는 유효한 ID만 삭제한다. 실패한 대상도 결과와 사유를 기록하며 예산을 차감하지 않는다. 작성된 정보 공개에도 삭제를 적용한다.
- [x] pure + 실제 유스케이스 테스트로 루프 경계·규칙·소실·도구를 검증한다.

## Task 2 — 후속 질문과 원자적 저장

Files: `app/use_cases/loop_interactor.py`, `app/dtos/event_log_dto.py`, `adapter/inbound/api/v1/game_router.py`, `adapter/outbound/repositories/game_repository.py`, 관련 engine tests.

- [x] 같은 NPC의 두 번째 새 질문 차단, 다른 NPC 허용, 다음 장면 재개, 고유 관찰/노트, 같은 request_id 재전송, 실패 시 예산 보존을 검증한다.
- [x] 장면당 캐릭터 1회 제한을 복구한다. 발화별 UUID와 선택적 `request_id`의 재전송 계약은 유지한다.
- [x] 루프 행 잠금 + 기존 장면 트랜잭션으로 중복 요청 및 동시 장면 이동을 직렬화한다. 같은 ID의 다른 payload는 충돌로 처리한다.
- [x] 성공 응답을 이벤트에 저장해 재전송 시 그대로 반환한다. 모델 실패는 서비스 오류로 반환하고 예산/대화 기억에 넣지 않는다.
- [x] `규정이야` 오탐을 없애되 실제 잘못된 인물 지목은 계속 검사한다. 재생성에 오류 이유를 전달한다.

## Task 3 — 시나리오 성격과 자연스러운 답변

Files: `backend/apps/scenarios/scenario_a/adapter.py`, `backend/apps/engine/app/use_cases/prompts.py`, 시나리오 관련 pure tests.

- [x] 공통 회피·3턴 망각·무조건 전언 수용 지시와 예시를 제거한다.
- [x] 인물별 성격·욕구·두려움·관계와 쉬운 말투 예시를 분리한다. 기본 사실은 구조화된 knowledge로 옮긴다.
- [x] 채연의 몸 관련 방어, 민석의 성실함, 은상의 불안과 친화성, 준의 관찰과 호기심을 구현한다.
- [x] 은상의 전언 출처와 준의 기본 경험을 시나리오 안에서 일치시킨다. 실제 실행 전의 행동을 기본 지식으로 주지 않는다.
- [x] 행동의 witnesses를 실제 장면에 맞게 명시한다. 작성된 잡담과 설명의 사실을 유지한다.
- [x] Manager 프롬프트는 memory_delete 대상에 제공된 기억 ID만 사용하게 한다.

## Task 4 — 후속 질문 UI

Files: `frontend/components/screens/DayScreen.tsx`, `frontend/components/GameplayGuide.tsx` 또는 실제 안내 컴포넌트, `frontend/contracts/api.ts`, `frontend/tests/*.cjs`.

- [x] 선택한 NPC에 이어 묻기 테스트를 먼저 작성·실행한다. 요청 중 중복 전송/장면 이동 잠금, 예산 0 잠금도 검증한다.
- [x] 추가 지시: `uttered`에 의한 입력 차단과 ‘이 장면 대화 완료’ 표시를 복구한다. 다른 인물과 다음 장면에서 대화할 수 있음을 안내한다.
- [x] UUID request_id를 보내고 네트워크 오류 후 동일 질문 재시도는 같은 ID를 사용한다. 응답의 `utterance_id`는 내부 중복 처리에만 사용한다.
- [x] 변경된 API 계약을 타입에 반영한다. 게임 안내의 장면당 1회 설명을 수정한다.
- [x] TypeScript 검사와 기존 headless UI 흐름을 검증한다. 브라우저 테스트는 한 프로세스만 실행한다.

## Task 5 — 실모델 평가와 통합 검증

Files: 새 `backend/scripts/run_npc_dialogue_check.py`, 필요한 회귀 tests, `docs/model_evaluation.md`, 본 계획/설계 문서.

- [x] 기존 7세 평가는 역사적 기록으로 남기고 새 정책 버전의 평가 도구를 만든다.
- [x] 최근 판의 8개 질문과 후속 질문, 성격 공통 질문, 루프/삭제/금지/정체 경계의 모델 원문과 근거를 저장한다.
- [x] 같은 모델로 핵심 실패 사례를 반복 검증하고 관련성·관점·출처·기억·지연을 실제 결과로 보고한다.
- [x] 백엔드 관련 전체 테스트, frontend 타입 검사, 헤드리스 후속 질문 및 5회차 흐름을 실행한다.
- [x] 변경 범위에 대한 독립 코드 리뷰 후 발견된 결함을 수정·재검증한다.
- [x] 실제 성과와 남은 한계를 문서에 기록하고 사용자에게 변경과 검증 결과를 보고한다.

## 작업 기록

- 사용자 추가 지시: 장면당 캐릭터 1회 제한을 서버·화면에 복구했다. 성공 요청 재전송, 실패 시 예산 보존, 다음 장면의 NPC 상태 갱신 후 재대화를 유지한다. 백엔드 460개, TypeScript, 관련 UI 3종을 재검증했다. 기존 모델 평가 원문은 당시 조건으로 보존하며 러너의 새 후속 질문은 다음 장면으로 이동한다.
- 사전 검토: Task 1/2는 `loop_interactor.py`와 기억/발화 인터페이스를 공유하므로 한 작업자가 처리한다. Task 3은 합의한 DTO 필드만 사용하고 Task 4는 API request_id/utterance_id 계약만 공유하므로 별도 파일에서 병행 가능하다.
- 현 체크아웃의 기존 변경을 기준선으로 보존한다. 별도 worktree에 옮기면 사용자가 이미 수정한 실행 코드가 누락될 수 있으므로 현 폴더에서 수정을 통합한다.
- 완료 검증: 백엔드 460개, TypeScript, 헤드리스 UI 4종 통과. 확인된 로컬 백엔드만 재시작했고 새 모델·DB 정상과 `/play` 200을 확인했다.
- 모델 검증: 최종 공통 21문답씩 비교와 Gemma 추가 20문답을 수행했다. Gemma의 실제 행동·출처 설명 개선을 적용 근거로 삼았으나, 인물 부재 추측·현재 전언 회피와 p95 3초 목표 미달을 함께 기록했다. 기능 구현 완료와 의미 품질 목표 달성은 구분한다. [최종 기록](../../review-verification/2026-09-15-npc-dialogue/README.md).

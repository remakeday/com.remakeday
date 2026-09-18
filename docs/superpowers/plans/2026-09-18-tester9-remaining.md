# 테스터9 잔여 항목 반영 장부 (2026-09-18 17:30~)

등급: F24/9b·F23③ = C(시나리오 문장)+B(장면 조립), F14 사례 2 = B, F19-3 = B, F3·F18 = B(UI 동작). F15는 사용자 지시로 제외. F11 목표 점수대는 사용자 결정 대기.
담당: 백엔드·시나리오 = Claude 서브에이전트 3명 병렬(scenario / explain rule / suggestions), 프론트 = Codex **gpt-6-astra**(사용자 지시 17:30). 전체 pytest·헤드리스 실행은 컨트롤러가 마지막에 한 번.

| 항목 | 담당 | 상태 |
|---|---|---|
| F24/9b 트럭 방송 MA13 연결·"○○축산" 조각 삭제 + F23③ 충식 첫 등장 맥락 | Claude A | 완료 17:42 — 번들 `day_end_broadcasts`(loop 5·beat 6·MA13·P06), `lines` 마지막 in-world 줄로 broadcast(음성 MA13 등록), NPC 기억에는 넣지 않음(축산 발화 금지 유지), `question_evidence`에 축산 주제 추가. 충식 문장 `같은 방에 있던 충식은 어제 이송됐다. 아침에 그 자리는 깨끗하게 비어 있었다.`(초안, 디렉터 확인 전). 준 행동에 `explanation_knowledge` 링크. 부분 테스트 705 passed. P06 표시는 프론트(astra) 후속 |
| F14 사례 2 설명 규칙이 인물 지식을 쓰게 | Claude B | 완료 17:36 — 원인: 설명 대사는 모델이 아니라 시나리오 정적 문장(`SceneActionDTO.explanation`), 09-17 문장은 cf5a0b7에서 이미 수정. 재발 방지 가드 `explanation_grounding.explanation_line`(설명이 장면 밖 새 낱말 2개 미만이면 연결 지식 문장을 덧붙임, `explanation_knowledge` 링크가 있을 때만). 테스트 6건. 준 행동에 링크 한 줄은 A(시나리오)에 전달 |
| F19-3 추천 질문(규칙 기반, 기록에서 답 가능한 질문) | Claude C → 프론트 칩은 astra | 백엔드 완료 17:47 — `question_suggestions.suggest_questions`(방송/소등 뒤 새 단서/인물 오늘 행동, 최대 3, 물은 것 제외), `submit`·`questions` 응답 `suggested_questions`, "오늘" 질문은 현재 회차 기록 우선(`advisor_context today=`). 211 passed. 칩·P06 그림 표시는 astra 진행 중 17:48 |
| F3 랜딩 BGM·토글, F18 새 단서만 필터 | astra | 완료 17:34 — 로그인 버튼 `onAnimationStart`(4.2s)에 BGM 시작·우상단 토글, 자동재생 거부 시 첫 조작에 재시도; NEW=현재 회차 + 직전 회차 night-clue/outcome-fragment, 필터 "새 단서만". 컨트롤러 확인: day-screen-vn·dev-login·gameplay-clarity 통과, 랜딩 스크린샷 15 |

## astra 후속 (17:39~17:44)
- 신의 개입 화면 입력란 아래 "예시:" 칩(서버 `suggested_questions`만 표시, 클릭 시 입력·포커스 이동, 답변마다 교체, 비면 숨김).
- 현재 대사의 `image_id`가 장면 삽화 밖이면 그 그림을 표시(P06 캡션 "트럭 옆면에도 글자가 있다.", 기존 치지직 효과), 이전 대사로 가면 장면 그림 복원.
- astra가 `frontend/docs/`에 남긴 작업 메모(F3·F18 계획 11줄)는 이 장부로 흡수하고 삭제.

## 검증·리뷰 (18:00)
- 백엔드 1033 passed(18:40 재기동), tsc, 헤드리스 10종 전부 통과, 스크린샷 15장.
- sonnet 전체 리뷰 1회: Critical/Major 없음. Minor: ① 음성이 `voice_id` 대신 문장 일치에만 의존 → astra 수정 1회(`voice_id`가 있으면 그 클립 우선, voice-playback 검사 추가) ② ◀▶로 방송 줄을 오가면 재생 반복(기존 동작, 보류) ③ 설명 가드는 낱말 겹침 기준(현 호출부 1곳, 테스트로 고정).

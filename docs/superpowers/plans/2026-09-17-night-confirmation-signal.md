# 밤 점수 화면 확인 신호 — 인정된 내 문장 · 빈 칸 힌트 (휴먼테스트 순서표 4번)

등급: **B (UI·게임 로직)** — 채점 결과 노출이라 진실 문장 잠금을 테스트로 고정한다.

근거: 테스터10 F1(맞힌 문장을 몰라 3회차에 인정 문장을 지움 8.8→0.0)·F2(확인 신호·길잡이 부재).

## 사용자 결정

- 매 밤 점수 화면에 **인정된 내 문장**을 보여 준다. 진실(정답 명제) 문장은 계속 잠근다(`truth_reveal`은 마지막 밤만).
- **점수 0인 칸은 칸 이름만** 힌트로 준다. 회차별 단계 힌트는 없다.
- 힌트 대상은 **원인·동기만**. 정체 칸은 기획서 §4.8⑤·§7.3("아무도 묻지 않는 질문")에 따라 이름을 꺼내지 않는다.

## 응답 계약 (`POST /nights/{id}/submit` — 필드 추가·의미 조정)

| 필드 | 전 | 후 |
|---|---|---|
| `accepted_claims: string[]` (신규) | — | 이번 밤 채점에서 `confirmed`·`partial`로 인정된 플레이어 문장. 칸 구분 없이, 플레이어가 쓴 순서대로, 중복 제거 |
| `empty_cells: ("cause"\|"motive")[]` (신규) | — | 점수 0인 칸 코드. 원인·동기만. 문구는 프론트 표에서 |
| `cell_feedback` | 원인·동기·**정체** 3단계("…비어 있다" 포함) | 원인·동기 중 점수 > 0인 칸만 "잡혔다/조금 잡혔다". 없으면 `null`. 빈 칸은 `empty_cells`로 옮김 |

### 판단

- **정체 칸:** `cell_feedback`이 매 밤 "정체는 비어 있다."를 말하고 있었다 — §4.8⑤와 충돌하므로 뺀다. 정체 명제에 인정된 문장은 `accepted_claims`에 **칸 이름 없이** 섞여 나온다. 플레이어가 스스로 그 질문을 던진 뒤에만 보이므로 함정을 깨지 않는다.
- **부작용 칸:** 현재 코드는 부작용 명제를 모든 회차에서 채점 대상에서 뺀다(`submit`의 `t.cell != "side_effect"`, `total_score` 가중치에 없음). §7.3의 "1회차만 제외" 규칙이 적용되는 회차가 없으므로 힌트도 없다.
- **partial:** 점수에 0.5가 들어가므로 인정 문장에 포함한다. 화면에서 confirmed와 구분하지 않는다(구분하면 "이 문장을 더 다듬어라"라는 더 강한 힌트가 된다).
- **ratchet:** 잠금으로 유지된 판정도 점수에 들어가므로 인정 문장이다. 잠금 조건이 "직전 매칭 문장이 이번 후보에 그대로 있음"이라 표시 문장은 이번 후보 원문으로 되돌린다.
- **매칭 문장 방어(테스터9 F11):** 인정 문장은 `judge_candidates(night.claims)` 후보 원문 중에서만 고른다. 매칭 문장이 후보와 같지 않으면(ratchet과 같은 정규화 — 공백·끝 문장부호만 무시) **제외**한다. 비슷한 후보로 보정하지 않는다.
- **과거 노트 조각:** 조각이 이번 밤 후보에 없으면 위 방어로 걸러진다. 3번 변경 전에 만들어져 `claims` 자체에 조각이 들어간 draft를 배포 뒤 제출하면 그 조각은 실제로 채점 후보였으므로 인정 문장으로 보인다(한 밤 한정 과도기).

## 표시 문구 (ScoreScreen)

| 구분 | 전 | 후 |
|---|---|---|
| 칸 상태 | "원인은 조금 잡혔다. 동기는 비어 있다. 정체는 비어 있다." | "원인은 조금 잡혔다." (점수 > 0인 원인·동기만) |
| 인정 문장 | 없음 | "인정된 내 문장" + 문장 목록 |
| 빈 칸 힌트 | 없음 | "원인이 아직 비어 있다." / "동기가 아직 비어 있다." |
| 오답 수 | "N개의 주장은 세계와 닿지 않았다." | 유지 |

## 작업

1. `scoring_rules.accepted_claims()`·`empty_hint_cells()`·`cell_feedback()` 조정 → verify: `tests/engine/test_domain_p2p5.py`, `tests/engine/test_usecase_night.py`
2. `night_interactor.submit` 응답에 필드 추가 → verify: submit 단위 테스트(ratchet·조각·불일치·정체 무라벨·진실 문장 미포함), `test_e2e_flow.py`
3. `api.ts` `SubmitRes`·`ScoreScreen.tsx`·`api_contract.md` → verify: `npx tsc --noEmit`
4. 헤드리스 목(mock) 응답에 새 필드 반영(실행은 컨트롤러)

## 리뷰 반영(수정 1회)

1. **(Important) 인정 문장 1:1 대응** — 정규화 문자열 집합으로 거르면 "트럭 소리가 났다"와 "트럭 소리가 났다."처럼 정규화만 다른 두 후보가 하나만 지목돼도 둘 다 인정으로 보였다.
   - `night_interactor._judge`: per_truth 항목에 `matched_index`(채점기 인덱스, 범위 밖·미지목은 `None`)를 담는다. 후보가 없을 때의 조기 반환도 `None`.
   - `scoring_rules.apply_ratchet`: 잠금 적용 시 이번 후보에서 찾은 인덱스를 `matched_index`로 넣는다(같은 원문 우선, 없으면 정규화가 같은 첫 후보 — `_candidate_index`). 잠금 조건은 그대로.
   - `scoring_rules.accepted_claims`: 인정 판정의 `matched_index` 집합으로만 후보를 고른다. 인덱스가 없는 지목(조각·어긋난 매칭)은 빠진다(F11 방어 유지).
   - `night_interactor.submit`: 잠금 뒤 오답 재계산도 같은 인덱스 집합으로 — 잠금 매칭이 공백·끝 문장부호만 다른 경우 같은 문장이 인정 목록과 오답 수에 동시에 잡히지 않게.
   - **저장 호환 판단:** `matched_index`는 `night.per_truth_claim`(JSONB)에 함께 저장되지만 **이번 밤 계산에만 쓴다.** 다음 밤 `apply_ratchet`은 직전 항목의 `verdict`·`matched_user_claim`만 읽고, 인스펙터·여정은 `AnswerScoredEvent`(스키마 불변)를 읽는다. 따라서 필드 없는 과거 밤 데이터도 그대로 읽힌다. 이벤트 스키마에는 넣지 않았다.
   - 테스트: 근접 중복 두 후보 중 하나만 지목 → 하나만 표시(도메인·submit), 잠금이 근접 중복 중 같은 원문을 가리킴, 정규화만 같은 후보를 가리킴.
2. **(Minor) 헤드리스 목 계약** — `guard.cjs`·`connected-investigation.cjs`·`voice-transitions.cjs`·`scene-illustrations.cjs`의 `/submit` 목에 `accepted_claims`·`empty_cells`를 넣고, `cell_feedback`을 새 의미(점수 > 0인 원인·동기만, 없으면 `null`)로 맞췄다. 실행은 컨트롤러.
3. **(Minor) 점수 화면 접근성·오탭** — `ScoreScreen`의 화면 전체 버튼을 일반 `section`으로 바꾸고 명시적 "계속" 버튼을 둔다. 전체 버튼에는 전역 키 처리가 없었으므로(포커스 시 Enter/스페이스) 네이티브 버튼으로 동작이 유지된다. 헤드리스 스크립트는 모두 `getByRole('button', { name: '계속', exact: true })`로 넘기고 있어 셀렉터 변경은 없다(`gameplay-clarity.cjs`의 "탭하여 계속"은 아침 화면).

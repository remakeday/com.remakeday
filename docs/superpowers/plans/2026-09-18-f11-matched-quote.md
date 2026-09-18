# 채점 매칭 문장 지목 오류 — 인용으로 번호를 바로잡는다 (테스터9 F11)

등급: **A (채점 로직)** — 구현 에이전트 1명, task 검토 sonnet, 최종 전체 리뷰 opus, 수정 1회.

근거: 테스터9 F11 "매칭 문장 지목 오류" — 3일째 motive-2(이송 규정)의 `matched_user_claim`이 "검진 방송에 따르면 … 이송된다."가 아니라 "검진 때도 담요를 끌어올린 채 …"로 기록됐다(1일째도 같은 명제에서 재발). F17(노트 비채점)로 근거 조각 오인정은 이미 사라졌고, 이 항목만 남았다.

## 진단 (DB `events` 읽기 전용, 2026-09-18)

- 이벤트 12935(3일째 motive-2 판정 harness_event): 모델의 `why`는 "후보 2의 '상태가 좋지 않은 사람은 별도 구역으로 이송된다'"를 근거로 적었는데 `matched_index`는 1. 판정(confirmed)은 맞고 번호만 하나 어긋났다.
- 전수(09-09~09-17, `evaluator_verdict` 채택 출력 중 `matched_index`가 있는 249건): `why`가 후보 문장을 따옴표로 인용한 181건 가운데 **38건(21%)** 이 인용한 후보와 다른 번호를 냈다. 38건 전부 `번호 = 인용 후보 − 1`(0-기반 번호와 "N번째"가 섞인 모양). 인용 자체가 엉뚱한 후보를 가리킨 사례는 없었다.
- 결론: 모델은 근거 문장은 맞게 고르고 번호를 틀린다. 번호를 믿지 말고 인용을 믿는다.

## 변경

| 구분 | 변경 전 | 변경 후 |
|---|---|---|
| `EvaluatorVerdictOutput` | why → matched_index → verdict | why → **matched_quote**(근거 후보에서 그대로 옮긴 일부) → matched_index → verdict |
| 프롬프트 | 번호만 반환 | confirmed·partial이면 근거 후보의 문장 일부(6자 이상)를 고치지 않고 `matched_quote`에 옮기고 그 후보 번호를 `matched_index`에 |
| `_judge` | `out.matched_index` 그대로 | `scoring_rules.resolve_matched_index(candidates, quote, index)` — 공백을 뺀 인용이 **정확히 한 후보**에 들어 있으면 그 번호, 아니면 모델 번호 |
| 이벤트 스키마 | — | 변경 없음(harness_event의 원 출력에 quote가 남아 사후 감사 가능) |

- 하네스 재시도로 풀지 않는 이유: temperature 0이라 같은 출력이 반복된다. 결정적 보정이 호출 비용 없이 확실하다.
- 인용이 0개·2개 이상 후보에 걸리면 번호를 그대로 쓴다(보정하지 않음).

## 검증

1. 단위: `resolve_matched_index` 표(유일 일치 우선·없음·짧음·중복·공백 차이), `_judge`가 quote로 번호를 고친 문장을 `matched_user_claim`으로 냄, 스키마 속성 순서.
2. 재현(gemma4:12b, 로컬): DB의 249건을 새 프롬프트·스키마로 다시 판정해 ① verdict 일치율 ② quote가 유일 후보에 닿는 비율 ③ 번호 보정 발생 수를 잰다. 결과는 `docs/model_evaluation.md` A.22·`metrics.yml`.

## 결과 (2026-09-18 오후)

- 구현: `llm_output_dto.py` +3, `prompts.py` +3/−2, `scoring_rules.py` +33(`_quote_key`·`resolve_matched_index`), `night_interactor.py` +12/−4, 러너 2종 보정 정합. 테스트 `tests/pure/test_scoring_rules.py`(17건)·`test_usecase_night.py` +4. **982 passed**.
- 재판정 249건(정본 `model_evaluation.md` A.22, `metrics.yml` `judge_index_replay`): 번호 오류 옛 35% → 새 원 번호 8% → 보정 뒤 0.6%. verdict 분포는 옛·새 동일(일치 230/249).
- 서버 반영: 14:32 백엔드 재기동(09:57 이후 플레이 없음 확인).

## 검토 반영

- sonnet(task 검토) Major 2건 반영: ① verdict none이면 인용이 남아 있어도 매칭하지 않는다(인용이 verdict보다 먼저 생성) ② `run_scoring_calibration.py`·`core_probes.py`의 매칭 진단도 같은 보정을 쓴다(`run_core_selection.py`는 원 번호 기록 — 의도).
- opus(최종 리뷰) Critical 없음, Major 1건 반영(수정 1회): 인용에 따옴표(" “ 「 『)·목록 번호("2. ")가 붙으면 부분 문자열 일치가 실패해 보정이 조용히 꺼진다 → `_quote_key`가 양끝 따옴표·문장부호·앞 번호를 뗀다, 프롬프트에 "따옴표·번호 없이 본문만". Minor: 하네스 `index_check`는 보정된 번호 기준으로(인용이 맞으면 재생성하지 않음). 테스트: 따옴표·번호 접두 5형, partial 판정 보정, none+잔여 인용.
- 보고만: 옛 코드로 채점된 판의 잘못된 매칭 문장은 마이그레이션하지 않는다. none 판정에 번호가 붙은 경우 이전에는 `wrong`에서 빠졌으나 이제 `wrong`에 남는다(더 맞는 동작, 화면 "N개의 주장은 세계와 닿지 않았다" 수가 1 늘 수 있음).

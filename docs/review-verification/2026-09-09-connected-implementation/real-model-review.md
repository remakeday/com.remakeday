# 실제 모델 초기 원문 — 독립 AI 의미 검토

2026-09-09 · 검토자 `/root/backend_review` · 상태: **초기 원문 검토 완료, 수정 후 새 원문 재검토 필요**.

이 문서는 실행 담당자와 별도로 수행한 AI 검토다. 사람 검토, 모델의 자기평가, 통계적 정확도 또는 전체 제품 품질 지표로 집계하지 않는다. 기존 `reviewed=0`인 사람 검토 지표를 변경하지 않았다. 코드·DB·서버를 변경하거나 추가 모델 호출을 실행하지 않았다.

## 대상과 원문 대조

- [초기 실행 보고](real-model-report.md), [원문 JSON](real-model-artifacts/probes-20260909T035804Z.json), [provider metadata](real-model-artifacts/ollama-provider-metadata.json), [이름 경계 수정 후 preview](real-model-artifacts/custom-previews-post-target-fix.json)를 직접 읽었다.
- 원문 SHA-256 직접 재계산: `2979ac96b5052f12b16f55bf0b85136008008527832f1b7e8a4bc2c38922639b`.
- 질문: 실제 `gemma3:12b`, 12문항 × 3시도 = 36회. ambient: 실제 `exaone3.5:7.8b`, 3장면 × 1시도 = 3회. custom preview는 결정적 코드 경로이며 실제 모델 의미 해석 성공으로 세지 않는다.
- 질문 36개 raw output 모두 `detail`을 생략했다. 실제 검사 거부는 `non_verbatim_evidence` **32회**, `missing_public_evidence` **4회**다. 존재하지 않는/설명이 섞인 ID는 3시도(Q8의 앞 2회, Q10의 첫 회); Q12 마지막 시도는 evidence 자체가 없다. 따라서 “36회 모두 같은 non-verbatim 거부”로 요약하면 부정확하다.
- 최종 질문 응답 12개 모두 `unknown`, `detail=null`, evidence 0개, fallback 사용. raw answer는 unknown 32개, `기록은 이렇다` 4개였다. 출력 형식 실패로 부분 근거가 모두 사라진 것은 확정 결함이지만 **unknown 자체가 12개의 잘못된 세계 판단을 뜻하지 않는다**.
- 실행 보고의 행별 판정을 합산하면 **질문 실패 9개(Q1·3·4·7·8·9·10·11·12), 모호 3개(Q2·5·6)**다. 전달 과정의 “8실패+3모호”는 12행과 불일치한다. 이 9/3은 초기 실행 gate의 합계이며, 아래의 정당한 사실 범위와 별개다.

## 질문별 정당한 답변 범위와 재실행 수용 조건

원문에 포함된 공개 기록만 사용했다. Q1–Q6에는 public-1…8만 있고, Q7–Q9에 public-9·10이 추가되며, Q10–Q12에 public-11이 추가된다. Q5에 아직 없는 이송 기록을 소급해 사용하면 안 된다. 초기 기록의 대부분은 1회차 관찰이므로 이후 질문에서 “오늘도 그랬다”로 바꾸지 않는다.

**Q1–Q11의 질문이 요구하는 결론은 모두 이 자료만으로 미확인이다.** 확인 가능한 부분 사실을 설명하되 `supported`로 결론을 만들어 통과시켜서는 안 된다. 명시적 모순을 입증하는 질문도 이 11개에는 없다. Q12는 기능의 사용 범위를 설명할 수 있는 질문이다.

| 질문 | 확인 가능한 근거 | 아직 모르는 것 / 허용되는 응답 | 다음 행동의 수용 조건 |
|---|---|---|---|
| Q1 채연말고 밥을 남긴 사람은 누구야? | public-7: 남은 쟁반 3개. public-2: 채연의 별도 관찰은 보조 비교에만 사용. | **unknown+부분 근거**. 다른 쟁반 주인은 확인되지 않았다. 쟁반 3개가 서로 다른 3명 또는 채연 외 2명을 뜻하지 않는다. | 저녁 쟁반 이미지·원본 노트 확인, 다음 배급/저녁 장면 관찰은 실제 가능. 제외 대상 채연만 답하거나 채연에게 묻는 경로만으로 완료하지 않는다. 특정 추가 인물을 알게 될 것이라고 약속하지 않는다. |
| Q2 준은 어떤 역할이야? | public-3: 준이 손목띠 숫자를 살펴보고 묻는다. | **unknown**. 공개된 행동은 설명할 수 있지만 정보원/실험체/특수 역할 또는 숨은 정체는 확인되지 않았다. 역할의 의미가 모호하므로 “관찰된 행동과 맡은 역할은 다르다”고 구분한다. | 준에게 손목띠·자신이 본 행동을 묻는 대화는 가능. 역할 정답을 보장하지 않는다. |
| Q3 민석은 누구에게 보고하는거야? | public-1: 관리자가 이상한 점을 방송실로 알리라고 말함. public-8: 민석의 문 앞 방문, 안의 말은 못 들음. public-5의 기록은 보조. | **unknown+부분 근거**. 방송실로 알리라는 지시와 민석의 보고 완료/실제 수신자는 다르다. “관리자에게 보고했다”는 결론은 아직 불가. | 민석에게 방송실에서 본 행동을 묻거나 방문 장면·방송 원문을 다시 확인. 관리자 직접 대화, 방송실 입장, 보고서 조회는 현재 제공되지 않는다. |
| Q4 채연 말고 추가로 배급을 남긴 사람 | Q1과 동일한 public-7 중심. | **unknown+부분 근거**. public-2만 인용하거나 대상 이름으로 빈칸을 채우지 않는다. | Q1과 동일. 원문이 명사구여도 다른 식사자를 묻는 의도를 유지한다. |
| Q5 호송 당한 사람은 누구야? | 당시 public-1…8에는 호송/이송 대상 기록이 없다. | **unknown**, 증거가 없어도 정당하다. “호송은 없었다”는 부정이나 충식 이름을 제공하지 않는다. public-6 검진/public-4 속닥임은 호송 대상을 입증하지 않는다. | 현재 해당 대상을 확인할 공개 기록이 없다고 설명해도 된다. 없는 호송 기록·차량 목록 조회를 안내하지 않는다. 임의의 NPC가 대상을 안다고 만들지 않는다. |
| Q6 열이나면 죽나? | public-6에는 이마를 짚는 검진과 결과 미공개가 있다. | **unknown**. 열이 실제 측정됐는지, 사망했는지, 열→사망의 관계 모두 미확인. 이마를 짚는 행위를 발열 확인으로 바꾸지 않는다. | 채연에게 본인의 상태/본 일을 묻거나 검진 장면 노트를 다시 볼 수 있다. 검진 결과가 반드시 공개된다거나 의무기록·의사 인터뷰를 제공한다고 약속하지 않는다. |
| Q7 이송된 충식은 돌아오는가? | public-9: “충식은 어제 이송됐다”는 **reported 전언**. | **unknown+전언 표시**. 전언이 존재함과 이송 사실의 독립 확인을 구분하고, 귀환 여부·귀환 불가능·생사·미래를 추론하지 않는다. | public-9 원문 확인 가능. 충식은 대화 대상이 아니므로 충식에게 물으라는 경로는 불가. 이 전언의 화자가 원문에 없으므로 특정 인물을 출처로 만들지 않는다. |
| Q8 귀표는 무엇인가? | public-10: 준이 그 단어를 사용했다는 전언. | **unknown+부분 근거**. 단어 사용은 정의가 아니다. 동물 식별 장치라는 현실 지식/숨은 정답을 주입하지 않는다. ID에 설명이 섞이면 정상 ID로 억지 보정하지 않는다. | 준에게 그 단어를 어디서 들었는지/무엇을 보았는지 묻는 대화는 가능. 준이 정의를 안다고 보장하지 않는다. |
| Q9 건강검진 후 이상이 있는 경우 어떻게 되는가? | public-1 검진 일정·이상점 보고 지시, public-6 결과 미공개. public-9 이송 전언은 별도 사건으로만 참고 가능. | **unknown+부분 근거**. “이상→이송→죽음/폐쇄” 규정은 공개되지 않았다. 검진 일정 자체를 질문의 후속 처분에 대한 답으로 확정하지 않는다. | 검진 장면·방송 원문 확인 및 등장 NPC의 본 일 설명은 가능. 관리자 처분표/검진결과 화면을 새로 안내하지 않는다. |
| Q10 축산 트럭의 정체는? | public-11: 옆면의 일부 글자 “○○축산”을 봄. | **unknown+부분 근거**. 글자는 관찰됐지만 용도·소유자·적재물·이송 목적·장소 정체는 미확인. “글자는 확인됐고 정체는 아직 모름”을 구분한다. | 이미 본 글자/이미지 원문 확인은 가능. 트럭 탑승·조사·차량 등록정보 검색은 제공되지 않는다. |
| Q11 손목띠와 귀표는 무슨 관계야? | public-3의 손목띠 관찰 + public-10의 단어 사용 전언. | **unknown+두 근거**. 둘이 같거나 서로 연결된 식별표라는 결론은 불가. 출처와 확인 수준이 다름을 유지한다. | 두 노트를 대조하거나 준에게 각각 본 것을 물을 수 있다. 질문만으로 두 사물이 같다고 규칙/노트에 기록하지 않는다. |
| Q12 너에게 물어볼 수 있는건 뭐야? | 게임의 질문 기능 계약. 이야기의 11개 기록을 답변 근거로 나열할 필요 없음. | 공개된 관찰·누가 무슨 말을 했는지·현재 근거의 범위를 물을 수 있고, 숨은 속마음·미래·미공개 사실은 모른다고 설명한다. **bare unknown은 부적합**. 기능 안내를 세계의 확인 사실로 저장하지 않는다. | 지금 실제 기록에서 질문 예시 1–2개를 제시한다. 예산·사용 시점과 맞아야 하며, 존재하지 않는 검색/대화 기능을 안내하지 않는다. |

Q1의 제외 대상을 안내한 문제는 **대화 API상 채연에게 말을 걸 수 없다는 뜻이 아니다**. 채연은 실제 대상이지만 질문의 목적을 좁히는 데 부적합한 안내였다. 초기 next_observation의 준/민석 대화와 노트 읽기는 기술적으로 제공된다. 반면 generic “노트를 다시 보라”만으로 부분 근거와 쟁점을 전달했다고 평가하지 않는다.

## 전부 unknown인 구현도 통과하지 못하도록 별도 확인 문항

아래 3개를 같은 공개 기록으로 실행하되 기존 테스터1 12문항 집계와 분리한다. 질문의 결론을 직접 뒷받침하는 경우와 범위가 미확인인 경우를 구분하는 통제 문항이다.

| 별도 문항 | 기대 범위 | 금지되는 확대 |
|---|---|---|
| PC1 “채연이 자기 몫을 반쯤 남기는 걸 봤어?” | `supported`, public-2의 관찰 행동. `맞다` 또는 같은 범위의 확인 응답. | 질병·숨기는 이유·다른 식사자·다음 회차에도 동일했다는 결론. |
| PC2 “관리자가 이상한 점은 방송실로 알리라고 말했어?” | **발언이 있었다는 범위는 supported**, public-1의 reported 속성 유지. `기록은 이렇다`+supported도 가능. | 발언 내용이 실제 규정대로 실행됐다는 결론, 민석의 보고 완료/수신자 확정. reported를 무조건 unknown으로만 처리하면 발언 존재와 발언 내용의 진실을 구분하지 못한 것이다. |
| PC3 “채연의 검진 결과가 공개되었어?” | `contradicted`, public-6의 명시적 “결과는 공개되지 않았다”. 질문의 “공개되었다” 명제에 아니라고 답한다. | 검진 자체가 없었음, 결과가 정상/이상임, 죽음/이송 여부. |

선택적 PC4 “민석이 수첩에 뭔가 적는 모습을 봤어?”는 public-5의 관찰에 `supported`여야 한다. 적은 내용이나 보고 완료는 확인하지 않는다. PC1에 “아침”을 붙이지 않은 이유는 이 제한 raw의 source title이 단지 “공개 장면 1”이어서 시간 추론까지 함께 시험하지 않기 위해서다.

## Ambient 세 장면의 독립 판정

세 표본 모두 장면 연관성과 근거 보존 수용 조건을 충족하지 못한다. 다만 발화의 문법적 의미와 세계 사건을 구분해서 판정한다. 원문 probe는 prompt/harness 출력까지이며 실제 use case의 저장된 세계 상태 변화나 행동 실행을 재현한 자료는 아니다. 따라서 아래를 “실제 세계에서 세 사건이 실행됨”으로 집계하지 않는다.

| 표본 | 근거 있는 부분 / 허용 가능한 발화 | 확정된 문제 | 과장하지 말아야 할 판정 |
|---|---|---|---|
| A1 ration-rumor | “음식 남았네”는 쟁반 관찰과 연결됨. “먹어야지”는 의도/제안. | “민석이 좋아하는 거 있어”는 공개되지 않은 취향을 추가한다. 소문·쟁반 주인 미확인을 이어가는 대화가 아니다. | “그럼 민석이 먼저 먹어”는 명령/제안이지 민석이 실제 먼저 먹었다는 완료 사실은 아니다. |
| A2 record-checkup | 수첩에 적는 동작과 담요는 원래 장면에 있다. | “배급 자리에 적힌 숫자 확인”은 없던 숫자/확인 행동. “수첩에 기록 완료”, “내 차례 준비 완료”는 원래 진행 중인 장면보다 완료 상태를 더한다. 네 줄 모두 자연스러운 짧은 대화보다 작업 상태 표시에 가깝다. | “기록 완료”는 의학 검사 결과가 공개되었다는 문장 자체는 아니다. 관찰에 없던 기록/준비 완료를 추가했다고 좁게 판정한다. |
| A3 known-source | “그럼 나도 웃어야지”는 앞선 말에 대한 의도이나, 앞선 사건이 근거 없다. | “채연이 웃었어”와 “방금 전엔 [준이] 여기 없었어”는 자료에 없는 행동·과거 위치 주장이다. 출처 미확인 전언을 이어가지 않는다. | “준이는 어디 있지?”라는 질문만으로 부재를 확정하지 않는다. 과거 부재 주장도 현재 명부와 자동으로 논리 모순은 아니다. **근거 없음**이 확정된 결함이다. |

수정된 candidate-ID 방식의 수용 조건: 유효 ID 선택만으로 의미 검증을 완료하지 않는다. 서버가 만든 후보 문장 자체가 원본의 대상·행동·시점·reported/observed·진행/완료·미확인 범위를 보존해야 한다. 플레이어만의 내적 관찰을 두 NPC가 직접 보았다는 기억으로 옮기거나, 전언을 “확인했어/사실이야”로 바꾸면 안 된다. 근거 없는 장소·숫자·취향·웃음·귀환·사람 부재를 후보에 넣지 않는다. 해당되는 후보가 없으면 실제 응답과 저장된 발화 모두 생략한다.

다음 실행은 standalone 이전 AMBIENT prompt만 재호출하지 말고 **수정된 production 후보 생성→모델 ID 선택→최종 대사→statement 관찰 저장 경로**를 기록해야 한다. 후보 목록/원본 observation ID/모델 선택/최종 lines/생성된 statement ID가 있어야 후보의 의미와 저장 결과를 대조할 수 있다.

## 직접 규칙 세 원문

수정 후 raw는 C1 민석, C2 채연, C3 은상을 각각 단일 대상으로 유지하며 `executable=false`, `rule=null`, 명시적 관찰 설명 대안을 반환한다. 세 원문에 대해 조용한 “답한다→질문한다” 치환이나 자동 적용이 없어 **지원 범위 밖 요청의 명시적 거절/대안 제공** 수용 조건을 충족한다. C3의 `해준다` 속 `준` 오인식도 수정 후 자료에서 사라졌다.

이는 원문의 “모든 질문에 자세한 답변/무조건 진실”이 실행된 성공 사례가 아니다. 대안을 사용자가 선택하고 새 preview를 확인한 뒤 별도 apply할 때만 대안 실행으로 평가한다. C3에서 더 가까운 알려진 소문 출처 공개 대안을 선택할 수 있으면 좋지만, 현재 명시적 관찰 설명 대안 자체를 잘못된 자동 번역으로 판정하지는 않는다.

## 재검토 자료와 판단 기준

1. 기존 raw는 보존하고 새 timestamp artifact를 만든다. 질문 12개는 같은 시점별 공개 집합을 유지하고 PC1–PC3는 별도 목록에 둔다.
2. ID는 원본 집합에 정확히 있어야 한다. 원문 detail을 서버가 복원하는 설계는 타당하지만 **유효 ID=질문 관련성/결론 참**은 아니다. Q1의 public-2, Q5의 public-4/6처럼 유효하지만 질문에 답하지 못하는 선택을 자동 supported로 올리지 않는다.
3. 토픽 보완은 unknown의 부분 근거와 한계를 제공하는 데 쓴다. 누락된 원문 근거를 회복하되 명시적으로 제외한 사람, 미래 기록, 숨은 규정 또는 출처를 만들지 않는다.
4. next_observation에 사용되는 NPC는 실제 playable 명부/해당 회차 상태와 대조하고, 노트/장면은 실제 disclosed ID로 연결한다. 가능한 질문/규칙 행동과 그 행동이 정답을 보장하는 것은 별개다.
5. 질문별 결과는 정당한 결론 범위·부분 근거·한계 설명·행동 가능성을 함께 검토한다. fallback 감소나 evidence 수 증가만으로 의미 개선을 선언하지 않는다.

초기 원문은 이미 확인된 advisor/ambient 수정 필요성을 뒷받침한다. 이번 독립 검토에서 별도의 새로운 차단 결함을 확정하지는 않았으며, 수정 후 문항별 원문과 실제 관찰 trace를 받은 뒤 위 조건으로 재검토한다.

## 04:17:23 재실행 — 독립 검토 결과

대상: [새 원문](real-model-artifacts/probes-20260909T041723Z.json), 실행 `04:17:23.573693Z`–`04:17:39.847282Z`. SHA-256 직접 확인: `56df6abb7e86857432b13505ae76e7a752061e1aee68707751007e85566c4f8b`. 초기 03:58 원문과 별개로 검토했다. 질문 12개 + 별도 통제 3개 + 결정적 custom 3개 + production ambient 3경로다.

**현재 판정: 개선은 확인되지만 의미 검증 gate는 통과하지 못했다.** PC1–PC3이 모두 기대 관계를 반환하지 못했다. 원문 인용이 살아났다는 것과 질문한 명제를 판단했다는 것은 다르다. 아래 RM1은 P1, RM2/RM3는 P2로 root에 전달했다. 사람 검토 지표는 여전히 채우지 않는다.

### 재실행에서 확인된 개선

- Q1–Q11은 모두 정당한 unknown 결론을 유지한다. Q5를 제외한 10개가 부분 원문 근거를 보여 준다. Q5는 그 시점에 이송 기록이 없으므로 empty evidence가 정당하고 미래의 충식 전언을 사용하지 않았다.
- Q1/4는 쟁반 3개와 주인 미확인을 함께 보여 준다. Q3은 방문/방송 지시와 실제 보고 완료·수신자를 구분한다. Q7은 이송 문장을 3회차 **전언**으로 표시한다. Q8/11은 단어·관계 미확인을, Q9는 검진 후 처분 미확인을, Q10은 글자 관찰과 정체 미확인을 유지한다.
- Q12는 모델을 호출하지 않고 실제 노트/규칙/미공개 정보의 한계를 설명한다. 세계 사실의 confirmed note를 새로 만들지 않는다.
- advisor 14개 실제 호출(Q1–Q11 + PC1–PC3)은 각 1시도로 형식을 통과했다. Q12는 호출 0이다. 따라서 이전의 detail 누락 재시도는 사라졌지만 이것을 의미 정확도 성공으로 환산하지 않는다.
- custom 3개는 대상 이름·원문·지식 한계를 유지한 비실행 preview와 명시적 대안을 반환한다. 여전히 원문 행동 실행 성공이 아닌 올바른 거절/대안 제공이다.

### RM1 — P1: 질문 명제의 지지 여부와 “인용할 기록이 있음”을 혼동

| 통제 | 실제 새 raw | 필요한 관계 |
|---|---|---|
| PC1 자기 몫을 반쯤 남기는 걸 봤어? | 모델 `unknown`+public-2, 최종도 unknown. 실제 관찰을 인용하면서 “질문한 관계나 이유는 확인되지 않았다”고 붙임. | public-2의 관찰 행동은 **supported**. 질문하지 않은 이유/관계를 모른다는 문구로 답을 대체하면 안 됨. |
| PC2 관리자가 방송실로 알리라고 말했어? | 모델 `unknown`+public-1, 최종도 unknown. 방송 원문과 무관한 민석 장면들까지 붙음. | **발언 존재는 supported**. 원문 verification은 reported로 유지하되 발언 내용의 실행/진실을 확정하지 않음. |
| PC3 검진 결과가 공개되었어? | 모델 `기록은 이렇다`+public-6. 원문은 명시적으로 “결과는 공개되지 않았다”지만 최종 **status=supported**. | 질문의 “결과가 공개되었다” 명제는 **contradicted**. |

코드의 `status = contradicted if answer == 틀리다 else supported`는 `기록은 이렇다`를 질문 지지로 자동 승격한다. PC3은 인용문 자체는 정확하지만 status가 반대라는 확정 사례다. PC1/2도 기록을 찾지 못한 것이 아니라, 선택한 기록이 질문을 직접 지지한다는 관계를 판정하지 못했다.

최소 수정 제안: 필수 모델 출력은 `relation: supported|contradicted|unknown`과 `evidence_ids`로 하고 사용자 answer/status는 이 관계에서 일관되게 만든다. “기록 있음”을 supported로 변환하지 않는다. 질문 명제와 인용 사실을 분리하도록 양방향 예시를 둔다: `공개되지 않음 → 공개됐어? contradicted / 공개안됐어? supported`, `reported 방송 → 그렇게 말했어? supported / 실제 보고했어? unknown`, `행동 관찰 supported / 이유 unknown`. ID 검증·서버 원문 복원·미래 정보 제한은 유지한다. 이 변경도 실제 모델 통제 재실행이 필요하며 필드를 추가했다는 이유로 의미 정합성을 선언하지 않는다.

### RM2 — P2: 넓은 토픽 보완과 경로 선택이 질문의 초점을 흐림

- Q1/4 모델은 이미 올바른 `public-7`만 선택했다. 서버가 방송(public-1), 제외 대상 채연(public-2), 민석의 기록(public-5)을 일괄 덧붙여 질문과 직접 관계없는 정보가 늘어난다. 최종 next path도 계속 제외 대상인 채연에게 “방금 본 행동”을 묻는 것이다. Q4에서 인용된 행동은 1회차 과거 기록이므로 “방금”이라는 안내도 부정확하다.
- Q10에서 모델은 올바른 글자 관찰 public-11을 선택했지만 서버가 이송 전언 public-9를 같은 토픽 그룹으로 추가한다. 이것이 해당 트럭과 그 이송의 관련성을 입증하지 않는데 나란히 제시된다.
- Q11에서 모델이 고른 public-3·10은 관련 있고 public-11(축산 글자)은 질문한 두 표시의 관계 근거가 아니다. ID 존재 검사만으로 이를 모두 유지한다.
- Q8/11은 근거 행위자로 실제 대화 가능한 준을 찾았지만 질문에 이름이 직접 적히지 않았다는 이유로 generic 노트 안내만 한다. “현재 제공되는 행동”으로는 유효하나 조사 범위를 좁히는 안내가 아니다.

최소 수정 제안: 유효하고 관련된 모델 근거가 있으면 그대로 사용하고 blanket topic 확장을 하지 않는다. 유효 ID라도 요청한 관계와 무관한 것은 관련성 회귀로 거절/제외한다. 자동 보완은 유효 근거가 없는 unknown 경로에서 좁은 부분 근거 회복용으로만 사용한다. 다음 경로는 질문의 제외 대상과 근거의 회차를 존중하고, 현재 이용 가능한 원본 장면/근거 행위자에 연결한다. 새 기록/기능을 만들어 안내하지 않는다.

### RM3 — P2: 안전한 서버 후보를 `말이야` 이름 오탐으로 제거

새 A3의 원문은 `은상: 소문의 출처는 직접 확인하지 못했어. 들은 말이야.`다. 서버가 이를 인용한 후보를 만들었으나 `unknown_person_check`가 **`unknown_person: '말이' in text_all`**로 걸러서 모델 호출·대화·statement·note 모두 0이 된다. 동일 후보에 해당 검사를 적용해 독립 무DB 재현했다.

빈 대화 자체는 허용된다. 하지만 이번 A3는 관련 내용이 없거나 모델이 생략을 고른 사례가 아니라, 이미 알려진 순수 한국어 문장을 사람 이름으로 잘못 판정한 것이다. 안전한 서버 인용 후보에 자유 생성용 이름 추측 검사를 다시 적용할 필요가 있는지 좁게 검토하거나 해당 문법 오탐을 바로잡는다. 현재 장면·소거·금칙어 검사는 계속 유지한다.

### Production ambient trace 판정

| 새 실행 | 모델과 저장 결과 | 독립 판정 |
|---|---|---|
| A1 | 실제 현재 회차/beat5의 public-7 후보를 index0으로 선택. 최종 2줄, statement 2개(reported), 일치하는 note upsert 2개, 두 인물 기억에 같은 문장이 들어감. | 쟁반 원문과 미확인 범위를 유지하며 새 행동/취향을 만들지 않는다. 현재 표본의 출처/저장 정합성 통과. 대사가 메타적이고 길어진 사용성은 별도 관찰 필요. |
| A2 | 현재 beat4 검진 후보가 모델에 전달됐고 모델이 null 선택. 대화/statement/note/기억 갱신 0. | 허용되는 명시적 생략. 이전의 숫자/기록완료 발명 없음. |
| A3 | 후보 작성 후 코드 검사에서 제거되어 모델 호출 0, 저장 0. | 발명 방지는 되었으나 RM3 오탐 미해결. 생략 성공 또는 “실제 모델 3장면 통과”로 세지 않는다. |

원문의 `server_candidates`는 생성된 후보 초안이며, A3처럼 필터를 통과해 모델에 실제 전달된 후보 목록과 동일하지 않다. 실제 전달 여부는 harness의 prompt/calls와 함께 판단했다.

### 이번 검토의 버전 경계

37개 pure tests를 DB conftest 없이 직접 실행해 통과 확인했다. Import contracts 4/4, forbidden words 0/83도 직접 확인했다. 244개 전체 suite와 PostgreSQL 결과는 backend 담당자 보고이며 이번 검토자가 재실행하지 않았다. source/trace/code 계약상 남은 RM1–RM3 때문에 이 passing test 수로 최종 의미 승인하지 않는다.

검토 직후 read-only SHA-256:

- `/tmp/connected-backend-review.diff`: `7a5296dfe0630d298ccfb309c4f93731cf49880f55e528395bdd99f0ec56d5dd` (34-file list)
- `/tmp/connected-backend-changed-files.txt`: `89e94594976ae5d5076f112d42892a4420624e755ffe3ac7da9ade61b1d0b851`
- `intervention_interactor.py`: `c14c830330c44190eaf4db42e09d065e4fc9088ed6851d07a33ba6dd1fd9d203`
- `loop_interactor.py`: `321456f22df666b74bf4c83200c44a52b919d9a63db08455f31809a7591f5728`

이 해시 이후 추가 수정은 본 판정 범위에 포함되지 않는다. RM1–RM3 수정 후 동일 질문·통제·production ambient 원문을 다시 검토해야 한다.

## 04:40:44 파일 실재 확인 — 실모델 검증 아님, provider 접근 차단

파일 목록을 직접 조회해 `/tmp/pigfarm-connected-integration/ollama-results/probes-20260909T044044Z.json`의 존재와 JSON 내용을 확인했다. 검토 시점 durable `real-model-artifacts/`에는 03:58·04:17 두 raw만 있었으며 04:40 파일은 없었다. 03:58과 04:17은 위에서 실패한 과거 실행이며 최신 성공 근거로 재사용하지 않는다.

- 파일 크기 **191,606 bytes**, SHA-256 **`bd7ff8db6fa371016c37d61a2866ef672c20ec8caf41226df1706ef204995718`**.
- 시작 `2026-09-09T04:40:44.894004+00:00`, 끝 `04:40:44.959786+00:00`: 약 **66ms**.
- 원문 질문 12개, PC1–PC4 4개, custom 3개, production ambient 3개가 들어 있다.
- Q12는 로컬 기능 안내로 provider 호출 없음. 나머지 원문 11개 + PC 4개 + ambient 3개 = **18개 provider 시도 모두** `provider: ConnectError: [Errno 1] Operation not permitted`.
- 18개 모두 `output=null`, `accepted=false`, `fallback_used=true`; **성공한 실제 모델 응답은 0개**다. `mode=real Ollama`, `model=gemma3:12b/exaone3.5:7.8b`는 구성된 호출 경로/모델명이지 실제 서버가 이 요청을 처리했다는 증거가 아니다.
- 스크립트가 exit 0으로 끝났더라도 하네스가 provider 예외를 fallback으로 처리했기 때문이며, 모델 호출 성공·관계 판정 통과를 뜻하지 않는다.

따라서 이 파일은 **접근 차단과 fallback 동작을 보여 주는 진단 자료**로만 인정한다. 새 relation 계약의 실제 모델 성능을 승인하거나 실패율을 계산하는 표본이 아니다. PC1/2는 supported, PC3(공개되었어)는 contradicted, PC4(공개되지 않았어)는 supported여야 하지만 이번에는 모두 provider fallback의 unknown이었다. 이를 “새 모델도 관계 판단에 실패했다”로 확정해서는 안 된다. 부정 쌍의 실모델 관계 판정은 **미검증**이다.

### 차단된 실행에서도 확인 가능한 결정적 코드 동작

- Q1/4 fallback 근거는 public-7 쟁반만 남고 제외 대상 채연/일반 배급·수첩 기록이 추가되지 않는다. 다음 경로는 과거의 실제 쟁반 장면 노트로 연결된다.
- Q10은 트럭 글자만, Q11은 손목띠와 귀표 두 기록만 남는다. 무관한 이송/트럭 기록이 뒤섞이던 RM2 사례가 이 fallback 경로에서는 재현되지 않는다.
- Q8/11은 근거 행위자 준과 3회차 원본 장면으로 다음 대화를 안내한다. 과거 기록을 “방금”으로 바꾸지 않는다. Q7은 부재한 충식에게 묻도록 안내하지 않는다.
- ambient 세 경로는 모두 모델 선택 대신 첫 안전 서버 후보를 사용했다. 각각 최종 2줄, reported statement 2개, 일치하는 note upsert 2개를 남긴다. source의 미확인/전언 문구를 유지하고 원래 발명했던 취향·숫자·완료·웃음·부재를 만들지 않는다. A3 `들은 말이야`가 다시 후보/출력에 포함되어 RM3의 결정적 이름 오탐은 제거됐다.
- 위 ambient 결과는 **서버 fallback 정합성**을 입증하며 실제 모델의 candidate 선택 정확성이나 생략 판단을 입증하지 않는다.
- custom 세 원문은 단일 대상·원문·지식 한계를 보존한 비실행 preview와 명시적 대안을 반환한다. 이 경로는 원래 모델을 사용하지 않는다.

## 최신 코드 checkpoint 검토 — 관계 계약 수정 구현, 실제 모델은 미확정

현재 `AdvisorRelationOutput`는 relation을 필수로 요구하고, 기존 자유 answer 문구를 relation으로 추측하지 않는다. 질문/원문 관계와 명시적 부정의 양방향 예시, 발언 존재와 발언 내용 실행의 구분이 prompt에 있다. 서버는 ID를 검증하고 원문만 복원한다. 무관/제외된 근거 제거, 미확인 범위 guard, narrow fallback 및 근거 회차·행위자 경로가 유지된다. 안전한 서버 ambient 인용에는 자유 생성용 인명 추측 검사를 제거했으며 현재 장면·소거·금칙어·언어 검사는 유지했다.

독립 실행: `.venv/bin/python -m pytest tests/pure --confcutdir=tests/pure -q --tb=short` → **47 passed in 0.10s**. 새 관계 양방향/발언 존재/배급 제외 대상/무관 truck ID/`말이야` 회귀를 직접 읽었다. root가 전달한 최종 전체 suite는 **exec session 78183, exit 0, 254 passed, 3 기존 deprecation warnings, 6.23s**다. 이는 root 실행 결과로만 인용하며 `/tmp/...suite-final.log`의 과거 sandbox 오류 파일은 근거로 사용하지 않았다. 검토자가 DB suite를 재실행하지 않았다.

현재 판단: **RM1–RM3의 코드 교정은 구현·pure 회귀 수준에서 확인됨. RM1의 실제 모델 관계 판정과 수정된 production selector의 실모델 재검증은 미확정**이다. 이를 최종 의미 검증 완료로 보고하면 안 된다. 허용된 실제 모델 접근으로 12원문+PC4+custom3+production ambient3를 다시 실행한 raw가 필요하다. 본 검토에서는 네트워크·모델/API·DB·서버 접근이나 새 권한 요청을 하지 않았다.

최신 코드/diff read-only SHA-256:

- `/tmp/connected-backend-review.diff`: `4fb3891cf897006637079b8638582a518ab90148d915b6f7d9fe4552cea4b3f6`
- `/tmp/connected-backend-changed-files.txt`: `bc5864f720b32ea873b16dbe64ab677a5690206311a7d456775e592acf162341` (35 entries)
- `intervention_interactor.py`: `4e3edcefaeb67c00fc7bd4d945040812925fb85d6aca6a327bc1f9d6937f10c6`
- `loop_interactor.py`: `6d8216ff9ca5a875c8faaf65124dbcffa60db7d067549b4cced1a3f00a6414ba`


## 05:41:43 실제 실행 — 호출 성공 확인, RM1 PC3 미해결

[검토한 새 raw](real-model-artifacts/probes-20260909T054143Z.json)는 `/tmp/pigfarm-connected-integration/ollama-results/` 원본에서 바이트 그대로 복사했다. **179,724 bytes**, SHA-256 **`ec0b66e7101ff0681aef8c75e1c9e34a6347eee515961e6f58925f69900230c2`**. 실행 `05:41:43.633378Z`–`05:41:57.512622Z`. root의 허용된 실제 실행(exit 0, exec session19347)이 만든 산출물이며 검토자는 모델·네트워크·DB를 호출하지 않았다.

원문 질문 12개, 별도 통제 4개, custom 3개, production ambient 3개가 있다. **실제 provider 응답 18개 모두 output 존재·accepted=true·오류 없음·fallback=false**를 직접 확인했다. advisor는 gemma3:12b 15건(Q1–11+PC4), ambient는 exaone3.5:7.8b 3건이다. Q12와 custom은 결정적 코드 경로다. 이는 04:40의 접근 실패 raw와 구분되는 실제 응답 증거다. 모델명은 harness 기록이며 이 실행에서 모델 digest를 다시 조회하지 않았다.

### 관계 통제 판정

| 통제 | 모델 출력 → 최종 | 독립 판정 |
|---|---|---|
| PC1 채연이 자기 몫을 반쯤 남기는 걸 봤어? | supported/public-2 → supported | 직접 관찰한 행동을 정확히 지지. |
| PC2 관리자가 이상한 점은 방송실로 알리라고 말했어? | supported/public-1 → supported | 발언 존재를 지지. evidence verification=reported가 보존되어 실제 지시 이행을 관찰 사실로 만들지 않음. |
| PC3 채연의 검진 결과가 공개되었어? | **unknown/public-6 → unknown** | **실패. 명시적 미공개 관찰에 대한 공개 명제는 contradicted. RM1 P1 유지.** |
| PC4 채연의 검진 결과가 공개되지 않았어? | supported/public-6 → supported | 부정 명제 자체를 지지. |

PC3의 원문은 같은 1회차 검진 장면에서 `채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다.`라고 한다. 질문은 결과의 내용·이유·미래 공개 여부를 묻지 않는다. 실제 prompt에도 `결과는 공개되지 않았다 / 결과가 공개되었어? → contradicted` 예시와 질문하지 않은 이유·관계로 unknown을 만들지 말라는 지시가 있다. PC4가 같은 시점·기록으로 supported이기도 하므로 시간 모호성을 새로 도입해 PC3를 합격 처리하지 않는다. 적어도 해당 공개 장면의 사건에 대해서는 contradicted라고 답할 수 있어야 한다.

코드 위치: `intervention_interactor.py:215`의 grounding은 ID의 존재만 검사하고, `:230`은 다른 guard에 걸리지 않은 모델의 unknown을 그대로 수용한다. `:106`/`:239`의 일반 제한 문구는 이 사례에서도 “질문한 관계나 이유는 ... 확인되지 않았다”를 붙여 질문하지 않은 불확실성을 제시한다. raw 경로는 `positive_controls[2].harness[0].call_records[0].output`, `positive_controls[2].result`다. provider 장애·형식 실패·fallback이 원인이 아니다.

최소 후속 제안: 다문장 장면의 생략된 주어를 해당 인물의 사건에 연결하고 질문의 사건·시점과 관찰의 범위를 맞춘 뒤 관계를 판정하도록 prompt의 대비를 명확히 한다. 필요하다면 이미 선택한 원문에 한정해 질문 명제·원문 명제·같은 사건/시점 여부를 확인하는 좁은 관계 재검사를 검토한다. 이는 추가 모델 판단이므로 개선을 보장하지 않으며 실제 양방향 통제로 재검증해야 한다. 단순히 원문에 `않`/`못`이 있다는 이유로 서버가 반전하면 이유·미래·다른 사건·전언 내용 진실까지 잘못 확정하므로 권하지 않는다. 특정 PC 문장 하드코딩도 피한다.

### 원문 12개와 부분 근거·다음 경로

| 질문 | 최종 근거/판정 | 다음 경로와 한계 |
|---|---|---|
| Q1 다른 음식 남긴 사람 | unknown/public-7 | 쟁반 3개, 주인 미확인; 실제 1회차 장면5 노트. 제외 대상 채연과 일반 배급/수첩 기록이 끼지 않음. |
| Q2 준의 역할 | unknown/public-3 | 손목띠 관찰까지만; 준에게 해당 1회차 장면2의 공개 행동을 질문. 역할을 추정하지 않음. |
| Q3 민석의 보고 수신자 | unknown/public-8 | 방송실 방문과 보고 완료·수신자 미확인을 구분; 민석의 원본 장면5 질문. |
| Q4 추가 음식 남긴 사람 | unknown/public-7 | Q1과 같이 쟁반 노트로 연결, 사람 수를 발명하지 않음. |
| Q5 호송된 사람 | unknown/empty | 당시 기록 없음; 노트/다음 낮 관찰. 미래 public-9를 가져오지 않음. |
| Q6 발열과 죽음 | unknown/public-1,6 | 방송·검진 결과 미공개 범위; 채연에게 원본 검진 장면 질문. 사망 인과를 만들지 않음. |
| Q7 충식의 귀환 | unknown/public-9 | 이송 **전언**과 미래 귀환 미확인; 원본 3회차 장면2 노트. 부재한 충식과의 대화를 제안하지 않음. |
| Q8 귀표 정의 | unknown/public-10 | 모델 자체는 supported였으나 서버 guard가 unknown으로 교정. 단어 사용 전언만 보존, 준의 해당 장면 질문. |
| Q9 검진 이상 후 처분 | unknown/public-1 | 방송 지시까지만; 1회차 장면1 노트. 검진 결과 public-6을 함께 보여주지는 않아 부분 근거의 유용성이 제한적이나 거짓 처분을 확정하지 않음. |
| Q10 축산 트럭 정체 | unknown/public-11 | 글자 관찰만; 4회차 장면5 노트. 이송 전언을 무관하게 덧붙이지 않음. |
| Q11 손목띠·귀표 관계 | unknown/public-3,10 | 관찰과 전언 원문 보존, 관계 미확인; 준의 3회차 장면2 질문. truck ID 제외. |
| Q12 무엇을 질문할 수 있나 | supported/empty, 모델 호출 없음 | 실제 공개 노트와 규칙/preview로 다음 날 관찰을 정하는 기능 안내. 세계 사실의 근거라고 세지 않음. |

모든 반환 evidence는 해당 질문의 available_public_observations 원본 객체와 일치하고 미래 회차가 없음을 assertion으로 확인했다. unknown의 인용은 회차·관찰/전언을 구분한다. 실제 존재하는 노트/대화/다음 낮 관찰 경로를 제시하며 새로운 조사 기능을 발명하지 않는다. 다만 이 raw는 후속 대화를 실제 플레이해 유용한 추가 답이 나오는지 시험하지 않는다. 이미 있는 원문 재확인은 진실을 새로 획득했다는 보장이 아니다. Q3/Q9의 부분 근거 폭과 대사의 자연스러움은 후속 사용자 평가 대상이다. 이번 finite 재현에서 **RM2는 닫힘**으로 판정한다.

### Custom 및 production ambient

Custom C1 민석/C2 채연의 자세한 답변, C3 은상의 무조건 소문 진실은 모두 원문·대상을 보존하고 `executable=false`, `rule=null`을 반환한다. C1/2는 실행 행동을 확정할 수 없음을, C3는 모르는 진실을 알게 할 수 없음을 설명한다. 대안은 각 원래 인물의 “알고 있는 관찰을 설명한다”다. 원문 행동을 성공적으로 실행했다는 결과로 세지 않는다.

Ambient A1은 실제 모델이 index0을 골라 쟁반 원문 인용+미확인 한계 2줄을 반환했다. A2는 실제 모델이 null을 골라 대화·관찰·노트·기억 저장이 없다. A3는 `들은 말이야`가 포함된 현재 rule_result 원문 후보를 실제 모델이 index0으로 골라 같은 인용+한계를 반환했다. 원래 오탐으로 막혔던 후보가 실제 선택과 저장까지 이어져 **RM3는 닫힘**이다. A3의 “관찰 기록”은 현재 설명 행동 기록을 인용하는 것이며, 인용 안에서 소문 출처 미확인을 그대로 유지한다.

A1/A3 각각 2개 final lines와 generated statement observations, note upserts의 text가 동일하고 source_key=observation_id이며 현재 loop/beat가 일치한다. 생성 발언의 verification은 모두 reported이고 두 화자 기억도 같은 두 문장이다. 이 연결을 독립 assertion으로 확인했다. 새로운 음식 취향·숫자·기록 완료·떠남·웃음 등의 사건이 없다. 서버가 안전한 원문 후보를 만들고 모델이 후보 ID 또는 생략을 선택한 것이므로 자유 생성 대사의 일반 안전성으로 확대하지 않는다. 저장 trace는 probe 포트의 호출 증거이며 이 실행 자체가 PostgreSQL 내구성 시험인 것도 아니다.

### 최신 결론과 버전 경계

**BR1–BR7 닫힘 유지. RM2/RM3는 이번 실제 재현 범위에서 닫힘. RM1은 PC3 명시적 부정 관계 실패로 변경 요청 유지.** 필수 통제 네 개 중 세 개가 기대 관계를 만족했다는 작은 gate 결과이며 통계 정확도·사람 검토 점수·전체 사용성 수치가 아니다. 18개 호출 성공/0 fallback도 의미 정확도와 분리한다. Q8처럼 모델 출력 자체와 최종 guard 결과도 구분한다.

이 검토 말미 read-only code/diff hash는 이전 47-pure/254-suite checkpoint와 동일하다:

- diff `4fb3891cf897006637079b8638582a518ab90148d915b6f7d9fe4552cea4b3f6`
- changed list `bc5864f720b32ea873b16dbe64ab677a5690206311a7d456775e592acf162341` (35 entries)
- intervention interactor `4e3edcefaeb67c00fc7bd4d945040812925fb85d6aca6a327bc1f9d6937f10c6`
- loop interactor `6d8216ff9ca5a875c8faaf65124dbcffa60db7d067549b4cced1a3f00a6414ba`


## 05:54:16 사건 문맥 수정 재검토 — PC3 교정, PC4 회귀로 RM1 유지

[새 raw](real-model-artifacts/probes-20260909T055416Z.json)를 원본에서 바이트 그대로 보존했다. **213,586 bytes**, SHA-256 **`e1d29431c8ed8f1d83debe7b735f47e28dddb13bcc60d64b9c2becb1e57fa78b`**. 실제 실행 `05:54:16.710501Z`–`05:54:29.893496Z`, root의 허용 실행 session89256 exit0. 모델 구성 gemma3:12b advisor / exaone3.5:7.8b ambient 유지.

호출부터 독립 확인했다. **18개 harness 작업, provider 응답 20개, provider 오류 0, fallback 0**이다. Q2가 잘못된 ID `['']`를 두 번 반환하여 `missing_public_evidence`로 거절된 뒤 세 번째에 public-3으로 통과했다. 따라서 **accepted 18 / rejected 2**이며, 모든 호출이 첫 시도에 통과했다고 보고하면 안 된다. 재시도 로그에는 두 실패와 정상 응답이 모두 남아 있다. Q12 및 custom 3개는 모델 호출을 하지 않는다.

| 통제 | 실제 raw relation / 최종 | 독립 판정 |
|---|---|---|
| PC1 반쯤 남기는 걸 봤어? | supported/public-2 → supported | 유지·통과. |
| PC2 방송실로 알리라고 말했어? | supported/public-1 → supported | 유지·통과. reported 발언 존재이며 내용 실행을 확정하지 않음. |
| PC3 검진 결과가 공개되었어? | contradicted/public-6 → contradicted | 이전 실패 교정. |
| PC4 검진 결과가 공개되지 않았어? | **contradicted/public-6 → contradicted** | **새 회귀. 부정 명제는 같은 미공개 관찰로 supported여야 한다. RM1 P1 유지.** |

PC4 exact raw: `positive_controls[3].harness[0].call_records[0].output={evidence_ids:[public-6],relation:contradicted}`, accepted=true, checks=[], fallback=false. 최종 `answer=틀리다`, `status=contradicted`가 “결과는 공개되지 않았다”는 원문과 함께 나온다. 긍정·부정 질문 모두 contradicted로 답한 것이므로 PC3 한 건의 교정을 전체 관계 gate 통과로 승격할 수 없다. 질문의 부정 명제 자체를 평가한다는 기존 계약/예시는 유지된다. 통제 기준을 자연어 부정 질문의 다른 관습적 해석으로 바꾸지 않는다.

집중 코드 diff는 actor·회차·장면 문맥을 원문에 추가하고, 대상/사건/시점 및 생략 주어 해석, 공개 여부와 결과 내용·이유·미래를 구분하는 일반 기계점검 예시를 추가한다. DTO는 evidence_ids를 relation보다 먼저 생성하도록 순서를 바꾼다. 특정 PC 분기나 부정어 기반 서버 반전은 없으며 범위는 좁다. 하지만 grounding은 여전히 유효한 ID와 model relation의 의미 정합성을 입증하지 않으므로 이 PC4 출력이 그대로 통과한다. 잘못된 모델 관계를 방지했다는 검증 근거로 schema 순서나 예시 존재만 사용할 수 없다.

독립 pure 실행 **54 passed in 0.11s**. 새 7개 회귀는 문맥 보존·schema 필드 순서·주어진 관계의 최종 전달을 확인한다. 관계값은 fake 모델에서 주입되므로 실제 모델이 부정 명제를 올바르게 해석한다는 시험은 아니다. root 보고 전체 suite session8668 exit0는 **261 passed, 3 기존 warnings, 6.95s**이며 reviewer는 DB suite를 재실행하지 않았다. architecture4/4도 이번에는 root의 전달 결과다.

원문 12개 최종 status·evidence_ids·다음 경로는 직전 05:41 표의 의미와 동일하다. Q1/4 쟁반만, Q3 방문만, Q5 미래 자료 없음, Q7 전언·귀환 미확인, Q10 트럭 글자만, Q11 손목띠/귀표만을 유지한다. Q8 및 이번 Q11은 raw model supported를 서버 guard가 unknown으로 교정하므로 모델 자체의 의미 성공으로 세지 않는다. 모든 evidence 객체는 해당 질문 available 원본과 동일하고 미래 회차가 없음을 assertion으로 재검증했다. Q2의 형식 재시도는 최종 근거/경로를 훼손하지 않았다. 이전에 기록한 Q3/Q9의 제한적 부분 근거 유용성과 다음 대화의 실제 효과 미검증 한계는 남는다.

Custom 3개는 원문·대상·비실행·지식 한계를 이전과 같이 보존한다. Ambient A1은 실제 index0 선택으로 2줄, reported 관찰2개, note2개와 두 화자 기억이 일치한다. A2와 A3는 모두 실제 `candidate_index=null` 선택으로 대화·관찰·노트·기억 저장 0이다. A3는 이번에는 모델이 정당한 생략을 고른 것이며 과거 `말이야` 코드 필터 오탐이 아니다. 세 ambient 모두 실제 provider 응답이 있고 fallback은 없다. source/statement/note/memory 및 loop/beat 정합성을 독립 assertion으로 확인했다. 새로운 사건 발명은 없고 RM2/RM3 closure는 유지한다.

**최신 권고: 최종 의미 승인 불가, RM1 P1 변경 요청 유지.** PC3와 PC4를 반드시 한 쌍으로 유지하고 질문 명제의 극성과 인용 사건의 극성을 혼동하는 경로를 다시 수정해야 한다. 단일 예시를 더 붙여 해결됐다고 가정하거나 특정 질문을 하드코딩하지 않는다. 모델이 어떤 명제를 평가했는지를 분리해 검증하는 개선은 가능하지만 그 자체도 실제 양방향 실행이 필요하다. 4개 통제 중 3개 충족은 표본별 gate 결과일 뿐 사람 정확도/통계 성능이 아니다.

검토 말미 current 파일 hash는 인계 manifest와 일치했다:

- focused diff `/tmp/connected-rm1-scope.diff`: `6fe522152e9bf2c4451626a38a3b866dce0ae8f12ce69de3ffcbae778db6fcce`
- intervention interactor: `e3a9ca03edb19468df66aa95325f97fdea2a9db95996daa116124bfa39ff8c1f`
- llm_output_dto: `65acc4c9d96401a649aee8107fbb47fe25cf2541e3de5658978a7bd5d96c9a0b`
- test_relation_event_scope: `7b732c734e0f31c12e937090c9adc7db4a7dc331d5d42be206fe7b1074de19dd`

검토자는 문서/artifact만 변경했으며 DB/API/네트워크/서버/실제 모델을 호출하지 않았다.


### 후속 최소 계약 제안 검토 — 아직 구현/승인 결과 아님

root가 제안한 내부 분리 계약은 질문별 하드코딩 없이 현재 실패 원인을 감사할 수 있는 개선 후보다. 한 번의 모델 출력에서 evidence_ids, 긍정형 proposition(대상·사건·시점·수량사 보존), question_polarity(positive/negative/not_binary), evidence_relation(supported/contradicted/unknown)을 분리한다. 서버 합성은 positive에서 그대로, negative에서 supported/contradicted만 서로 교환하며 unknown은 항상 유지한다. not_binary인 내용·이유·정체 질문은 unknown을 유지한다. 명시 미래 질문에 현재 장면 근거로 답하지 않으며 reported 내용 진실 보호와 ID/source 검증도 합성 후 유지한다. proposition은 감사용이며 사용자에게 새 사실로 렌더링하지 않는다.

이는 단어 `않`의 존재로 극성을 추정하거나 삭제하는 방법이 아니다. 모델이 실제 술어와 부정 범위를 구별해야 하며 `모두 ... 것은 아니다`에서 수량사를 잃으면 잘못된 명제가 된다. 열린 “공개하지 않은 이유?”를 negative binary로 분류해서도 안 된다. 모델이 proposition/polarity를 틀릴 잔여 위험은 여전히 있으므로 계약 자체로 해결을 보장하지 않는다. 별도 2차 모델 호출보다 작고 실패한 판단을 로그로 분리할 수 있다는 점에서 우선 검토할 만하다.

동일 미공개 원문에 positive 질문은 contradicted, negative 질문은 supported; 반대 공개 원문에는 각각 supported/contradicted인 양방향 쌍을 유지한다. 내용·이유·미래와 reported 발언 존재/실제 실행을 별도 negative control로 두어야 한다. pure 진리표는 합성과 unknown 불변성을 입증할 뿐 모델이 세 내부 의미 필드를 제대로 생성함을 입증하지 않는다. 새 raw에서 세 값과 최종 답을 각각 독립 판정해야 하며 HTTP 의미나 사용자 status 계약을 바꾸지 않는다.


## 06:10:38 극성·조회 분리 재검토 — 중간값 오류와 역원문 실패

[새 raw](real-model-artifacts/probes-20260909T061038Z.json)를 원본과 동일하게 보존했다. **296,372 bytes**, SHA-256 **`cb2be29b556162e630f2bf6b3ffc21e67da4e90f135e9c0b8cc0bb76a1d0e21e`**. 실제 실행 `06:10:38.236334Z`–`06:11:12.210066Z`, root session85107 exit0. 질문12 + 통제10(게임 원문8, 명시 synthetic 반대 원문2) + custom3 + production ambient3이다. **24 harness 작업/24 provider 응답, accepted24, rejected0, provider 오류0, fallback0**을 직접 집계했다. gemma3:12b advisor21건, exaone3.5:7.8b ambient3건이며 Q12/custom은 결정적 코드 경로다.

### 코드 확인과 이전 제안의 정정

required evidence_ids/question_kind/positive_claim/evidence_polarity/question_polarity를 읽고 proposition 4칸 합성 및 lookup의 반전 없는 affirmed 처리, null/unknown 불변성을 확인했다. lookup은 실제 요청한 값/행동을 담아야 하고 모델 문장은 사용자에게 표시되지 않는다. 앞 절의 open 무조건 unknown 제안은 **조회 정보 손실을 일으킬 수 있어 정정**한다. “누가 남겼어?”처럼 원문에 값이 있는 조회와 이유가 명시된 조회는 supported가 가능하며 현재 구현도 이를 지원한다. 이유·미래가 unknown인 근거는 의문문 형식이 아닌 필요한 정보 부재다.

집중8파일 current hash가 `/tmp/connected-rm1-polarity-sha256.json`과 모두 일치함을 확인했다. 독립 무DB pure 실행 **71 passed in 0.12s**. root의 전체 suite session35068 exit0는 **278 passed, 3 기존 warnings, 7.22s**, architecture4/4는 root 전달 결과다. fake 출력 회귀는 합성과 guard 동작을 입증하며 모델이 긍정 명제/부정 범위를 정확히 생성함을 입증하지 않는다. 코드 자체의 추가 확정 P1/P2는 발견하지 않았다. 그러나 아래 실제 의미 gate는 실패다.

### 확장 통제 — 최종 상태와 내부 의미를 분리

| 통제 | 실제 중간값 | 최종/독립 판정 |
|---|---|---|
| PC1 관찰 행동 | proposition / 채연이 자기 몫을 반쯤 남겼다 / affirmed / positive | supported, 내부값도 적절. |
| PC2 발언 존재 | proposition / 관리자가 방송실로 알리라고 말했다 / affirmed / positive | supported, reported 발언 존재 범위 유지. |
| PC3 미공개 원문·공개 질문 | proposition / 검진 결과가 공개되었다 / denied / positive | contradicted, 통과. |
| PC4 미공개 원문·미공개 질문 | 같은 claim / denied / negative | supported, 통과. |
| PC5 누가 남겼는지 조회 | lookup / 채연이 자기 몫을 반쯤 남기고 옆으로 민다 / affirmed / open | supported, 요청한 사람·행동이 들어 있어 통과. |
| PC6 왜 남겼는지 조회 | lookup / **채연이 자기 몫을 남겼다** / **affirmed** / open | 최종 unknown은 guard로 적절하지만 **요청한 이유를 행동으로 바꾼 내부 계약 실패**. 이유 없음이면 claim null/evidence unknown이어야 함. |
| PC7 내일 공개 여부 | proposition / **채연의 검진 결과가 공개된다** / unknown / positive | 최종 unknown 적절, **claim에서 내일 시점이 사라짐**. 미래 시점을 보존해야 함. |
| PC8 지시 실제 이행 | proposition / **관리자가 방송 지시를 내렸다** / unknown / positive | 최종 unknown 적절, **이행을 지시 발생으로 바꿈**. 올바른 요청 명제는 실제 지시 이행임. |
| SPC1 synthetic 공개 원문·공개 질문 | proposition / 검진 결과가 공개되었다 / affirmed / positive | supported, 통과. |
| SPC2 synthetic 공개 원문·미공개 질문 | 같은 claim / **denied** / negative | **supported, 실패. evidence는 affirmed, 최종 contradicted여야 함. RM1 P1 유지.** |

SPC2는 synthetic fixture를 별도 표기했으며 게임 실제 사건이라고 주장하지 않는다. 하지만 이 테스트의 실제 model input도 검증했다. `positive_controls[9].harness[0].call_records[0].messages[0].content`의 원문 줄은 `[public-6] (observed; 1회차; 장면 4: 공개 장면 4; 행위자: 채연) ... 결과를 공개했다.`이고 질문은 `채연의 검진 결과가 공개되지 않았어?`다. control_source_observations, available_public_observations, 최종 evidence/detail도 모두 같은 공개 원문이다. 메타데이터만 synthetic으로 바뀐 probe 버그가 아니다. 실제 output은 `positive_claim=채연의 검진 결과가 공개되었다`, `evidence_polarity=denied`, `question_polarity=negative`로 근거 극성을 잘못 분류한다. 합성 코드는 그 잘못된 입력을 일관되게 supported로 바꾼다.

PC6/7/8은 최종 상태만 맞았다고 내부 계약까지 통과 처리하지 않는다. 반대로 사용자에게 이유/미래/실행을 거짓으로 확정했다고도 주장하지 않는다. 문제는 모델이 요청한 정보를 그대로 유지한다는 약속이 이 표본에서 성립하지 않는다는 점이며, 공개 원문 바깥 문장은 UI에 렌더링되지 않는다. SPC2는 그보다 강한 사용자에게 드러나는 실제 관계 오답이다.

### 원문 질문의 상세 회귀와 제한

Q1–11 최종 unknown은 여전히 정당하고 Q12 기능 안내도 유지된다. 모든 반환 evidence 객체는 그 질문의 available 원본과 일치하며 미래 회차가 없음을 assertion으로 확인했다. Q1/4는 쟁반 원문만, Q3는 방문과 미확인 수신자, Q7은 이송 전언만, Q8/11은 용어/손목띠와 미확인 범위, Q10은 트럭 글자만 보여 준다. Q9는 이번에 public1·6이 보완되어 원본 검진 장면의 채연 질문으로 연결된다. 그 외 기존 노트/행위자/과거 회차 next paths는 유지된다.

그러나 내부 lookup값은 여러 원문에서 질문에 맞는 답을 보존하지 못한다: Q1 제외 대상 채연 행동, Q2 역할 대신 손목띠 행동, Q3 수신자 대신 방문, Q4 다른 사람 대신 쟁반 개수, Q8 정의 대신 단어 사용, Q10 정체 대신 글자, Q11 두 표시 관계 대신 사용을 affirmed로 제시한다. 모두 기존 좁은 관련성/미확인/전언 guard가 최종 unknown으로 교정하므로 이 표본의 최종 안전성은 유지되지만 새 구조화 모델 계약의 정확성으로 세지 않는다. Q7은 귀환 여부를 lookup/open으로, Q9는 열린 결과 조회를 proposition/open으로 분류해 question_kind도 완전하지 않다. 구조화 output에 필드가 채워졌다는 사실은 의미 준수를 뜻하지 않는다.

### Custom/ambient 및 현재 권고

Custom3은 대상/원문/지식 한계를 보존한 비실행 preview와 명시적 대안을 유지한다. A1은 실제 index1을 골라 현재 public8의 방송실 방문·말 내용 미확인 원문을 인용한다(이전 index0 쟁반과 다른 안전한 현재 후보). A2는 null 생략, A3는 index0으로 `들은 말이야` 원문 인용을 생성한다. A1/A3 각각 두 줄은 reported statement/동일 source_key note/두 화자 기억과 일치하고 현재 loop/beat를 유지한다. 이를 독립 assertion으로 확인했다. 새로운 보고 내용·소문 진실·행동을 만들지 않는다. RM2/RM3 closure는 재현 범위에서 유지한다.

**최신 판정: BR1–BR7/RM2/RM3 닫힘 유지, RM1 P1 변경 요청 유지. 최종 의미 승인 불가.** 원래 PC3/4는 이번에 모두 통과했지만 공개 원문 역방향 SPC2가 실패했고 PC6/7/8 및 다수 원문 lookup의 내부 의미도 불완전하다. 최종 통제 상태9개 충족/1개 미충족을 전체 성공률로 내세우지 않으며, 내부값 조건까지 고려한 합격 수도 별도 기준 없이 만들지 않는다. 사람 검토·통계 정확도·사용성 지표는 여전히 미측정이다.

검토 hash 경계:

- focused diff: `0895fade8ded054d57bb9e9473522155d7dbe122791c1a8b5ab89185a2fb6d6a`
- 전체 diff: `16d22119f3b35402cc0028cd3bd5f2bd9f98a8f97961906b3c27cad83102287f`
- 전체 changed list(37): `d92a9e904d2abc4bd4fc941e1ad46aff05bcecc78a44131c4e76c99df3a14fc7`
- intervention interactor: `eda69482f0f524c3b7633b57ae233cfab3c56644e8d184c888622a6e8b8a2b22`
- DTO: `b6b2e462fe31917768e9774fd80216d18b50d08d3d29a340dc90d70f6b73e4ea`

검토자는 DB/API/네트워크/서버/권한 요청을 하지 않았고 보고서/artifact만 변경했다.


## 06:28:38 두 단계 실제 검토 — 격리는 확인, 의미 gate 실패

[최신 raw](real-model-artifacts/probes-20260909T062838Z.json)를 바이트 그대로 보존했다. **285,026 bytes**, SHA-256 **`049f9acd282d878416d59313c6d035c47e742d224c698a00444f0589cbc9dc3b`**. 시작 `06:28:38.817009Z`, 종료 `06:29:41.581967Z`(약62.8초). 질문12+통제10+custom3+ambient3. root가 허용 실행을 완료했고 검토자는 파일만 읽었다.

**39 harness 작업, 51 provider 응답(output 모두 존재), accepted33/rejected18, provider 오류0, fallback6**. 작업은 interpretation21/evidence15/ambient3이다. 해석6개가 각각3번 검증 실패 후 fallback이 되어 evidence 호출을 생략했다. Q12 및 custom은 모델 호출 없음. gemma3:12b와 exaone3.5:7.8b 구성은 유지된다. 통신 성공과 의미/검증 성공을 혼동하지 않는다.

### 실행된 입력 격리와 비용/원문 검증

모든 실제 call messages를 검사했다. interpretation에는 원래 질문이 있고 공개 observation ID/원문은 없다. 실행된 binary evidence call에는 normalized positive_claim과 전체 공개 원문이 있으며 원래 질문은 없다. lookup evidence call에는 원래 조회 질문과 전체 공개 원문이 그대로 있다. 같은 adapter 호출이 대화 history를 섞었다는 흔적이 없다. 각 반환 evidence는 그 질문 available 원본 객체와 동일하고 미래 회차가 없으며 모든 질문 remaining=2라 3회 재시도/두 단계여도 질문 비용은1이다. 이 항목들은 assertion으로 확인했다.

따라서 이번 오류는 두 단계 입력 격리 실패로 설명되지 않는다. 해석/근거 모델이 입력에 대해 부정확한 필드를 반환하거나 관련 기록을 찾지 못하는 문제다. optional detail에 생성된 문장도 사용자 detail로 쓰이지 않는다. 예를 들어 Q2 모델 detail은 준을 관리자라고 덧붙이지만 최종은 원본 손목띠 기록만 표시하여 이 발명을 노출하지 않는다.

### 통제별 실제 판정

| 통제 | 해석·근거 결과 | 최종 판정 |
|---|---|---|
| PC1 관찰 행동 | proposition/행동 claim이지만 polarity=open을3회 반환, missing_question_proposition | **unknown, 실패**. supported가 필요. evidence 단계는 실행되지 않음. |
| PC2 발언 존재 | proposition/발언 claim이지만 open을3회 반복 | **unknown, 실패**. supported가 필요. |
| PC3 미공개 원문·공개 질문 | proposition/공개 claim이지만 open을3회 반복 | **unknown, 실패**. contradicted가 필요. |
| PC4 미공개 원문·미공개 질문 | interpretation 공개 claim/negative는 정확. evidence 빈IDs/unknown | **unknown, 실패**. 같은 검진 장면의 명시적 미공개로 supported가 필요. |
| PC5 누가 남겼는지 | lookup/null/open, public2/affirmed | supported, 요청 사람·행동 원문 제공. 통과. |
| PC6 왜 남겼는지 | lookup/null/open 정확, public2/**affirmed**는 이유 근거가 아니므로 오분류 | 최종 unknown은 guard가 교정. 내부 근거 판정은 실패. |
| PC7 내일 공개 여부 | proposition의 claim이 내일을3회 삭제, question_scope_lost | 최종 unknown은 적절한 fallback. 미래 해석 성공으로 인정하지 않음. |
| PC8 실제 지시 이행 | claim은 실제 이행으로 복원하지만 **question_polarity=negative**(원질문은 positive), evidence unknown/empty | 최종 unknown은 적절하나 내부 극성 실패. 관련 지시 부분 근거도 이번에는 비어 있음. |
| SPC1 synthetic 공개 원문·공개 질문 | proposition/open을3회 반복하여 fallback | **unknown, 실패**. supported가 필요. |
| SPC2 synthetic 공개 원문·미공개 질문 | 공개 claim/negative, public6/affirmed | contradicted, 양 단계와 최종 모두 통과. |

SPC2 실제 evidence prompt의 원문은 `결과를 공개했다`이며 positive_claim은 `채연의 검진 결과가 공개되었다`다. 원래 부정 질문은 전달되지 않는다. PC4 evidence prompt는 같은 claim과 `결과는 공개되지 않았다`를 포함하지만 unknown을 반환한다. 역원문 한 건의 교정이 원래 부정 원문 처리까지 보장하지 않는다. synthetic은 검사 fixture로 별도 유지하며 게임 내 실제 사건으로 세지 않는다.

통제10개의 최종 상태는5개 충족/5개 미충족이고, 충족5개 중 PC6/7/8은 내부 판단 또는 fallback 의존 문제가 있다. 이 개수를 정확도나 전체품질로 바꾸지 않는다. **PC1–4/SPC1 사용자 답 실패로 RM1 P1 유지**이며 최종 의미 승인은 불가하다. unknown으로 안전하게 내려간 것과 질문에 올바르게 답했다는 것은 다른 판정이다.

### 원문 질문·다음 경로 및 나머지 경로

Q1–11 최종 unknown과 Q12 기능 안내는 정당하다. Q1/3/5의 lookup 근거 unknown은 적절하고 Q6의 발열→사망 조건명제와 근거 부재도 대체로 보존된다. Q7 귀환 여부는 proposition/open을3회 반환해 해석 fallback이다. Q2 역할, Q4 추가 배급인, Q8 정의, Q9 처분, Q10 정체, Q11 관계에 evidence affirmed가 나오지만 실제로 해당 답이 있는 기록은 아니다. 기존 관련성·미확인·전언 guard가 최종 unknown을 유지했다. 형식 통과를 이 질문들의 의미 성공으로 세지 않는다.

부분 원문은 주로 유지된다. Q3은 방송 지시와 방문 기록을 함께 보여주고 실제 민석의 과거 장면 질문으로 연결한다. Q11은 이번에 귀표 전언 public10만 선택해 이전의 손목띠 public3이 빠졌으므로 비교 질문의 부분 근거 폭은 줄었다. PC8은 관련 방송 지시가 이미 공개되어 있으나 empty evidence와 generic 다음 낮 안내로 끝난다. 이는 거짓 세계 사실을 드러내는 문제는 아니지만 완전한 부분 근거/후속 경로 성공이라고 보고할 수 없다. Q7 fallback은 부재한 충식 대화 대신 실제 이송 전언 노트로 이어진다. 다음 경로의 실사용 효과는 여전히 이 raw로 시험하지 않았다.

Custom3은 원문·단일 대상·지식 한계·비실행·대안을 보존한다. Ambient A1은 실제 index0 쟁반 인용을 선택하고 A2/A3는 실제 null 생략한다. A1의 두 줄은 reported statement와 note source_key 및 두 화자의 기억이 일치하며 loop/beat도 현재 값이다. A2/A3는 대화·statement·note·기억 저장이 없다. 이 연결은 assertion으로 확인했다. 새 사건 발명이나 과거 말이야 코드 필터 회귀는 발견되지 않았다.

### 최신 코드와 승인 범위

독립 pure82개 통과 checkpoint와 동일한 current9파일 hash를 manifest와 다시 대조했다. root 보고 전체 suite는 **289 passed, 6.61s**이며 검토자는 DB suite를 실행하지 않았다. 코드 테스트·입력 격리·audit/질문비용·source 렌더링은 확인됐으나 실제 의미 gate는 위와 같이 실패한다. **BR1–7/RM2/RM3 기존 구체 재현 closure는 유지하되 advisor 의미 승인과 부분 근거 완전성 승인은 보류한다. RM1 변경 요청 유지.**

- focused diff SHA `41b8c7621142c0353913a0e5cb4a4ce892c703111d9a2b1a9519c9788ce8f231`
- intervention interactor SHA `202142583bfb7a217a2abd3bd53afa5c0f47d7e5faa325771e93f4b30540135d`
- DTO SHA `54dea5c669753798d3682e12bf1757ee6c546ea6e433c8130a14fcbf63f00189`
- stage isolation test SHA `c38e7aab43e20ffc0e35dc46d9264e49bd5b43e45f8d5effd17224ac61c0ca0b`

검토자는 DB/API/네트워크/서버/권한 요청을 하지 않고 문서와 복사한 raw만 변경했다. 이 검토는 독립 AI 검토이며 사람 검토·통계 정확도·실제 사용자 유용성 수치를 채우지 않는다.


후속 schema 진단: 실제 `AdvisorInterpretationOutput.model_json_schema()`를 무DB로 출력해 kind/claim/polarity 모두 required이며 default가 없음을 확인했다. `open`은 독립 polarity enum의 허용값이지 자동 주입 default가 아니다. Ollama adapter는 schema를 `body.format`에 그대로 넣고 응답 JSON을 그대로 반환한다. 따라서 이 raw의 proposition/open은 실제 모델 생성값이다. 제안된 결합 question_type(positive_proposition/negative_proposition/lookup)은 이 모순 조합을 schema에서 제거하는 좁은 개선이지만, 잘못된 negative 선택·시점 손실·명시적 부정 근거 unknown은 별도로 남으므로 이를 포괄 해결로 간주하지 않는다.


## Enum/temperature code checkpoint — actual semantics pending

Read the five-file `/tmp/connected-rm1-enum.diff` and verified all current hashes against its manifest. Independent database-free pure tests: **86 passed in 0.12s**. `question_type` replaces the independently combinable kind/polarity fields with positive_proposition/negative_proposition/lookup; the original four-case composition and lookup behavior remain consistent. Binary stage input still excludes the original question, lookup receives the original unchanged, interpretation sees no records, and only original evidence is rendered. Both advisor calls explicitly pass temperature0; the harness records and forwards that exact value and the Ollama adapter preserves zero instead of replacing it with its default. Other roles retain their settings.

The narrow broadcast cue now includes `방송 지시`, allowing empty-unknown execution questions to retain already-public instruction text without asserting actual compliance. Its regression checks original source recall and unknown status. The changed enum cannot express the prior proposition/open combination, but does not prove the model chooses the correct question type, preserves time, or classifies evidence correctly. No new confirmed code P1/P2 was found in this focused check. RM1 remains open pending the authorized actual rerun; the 06:28 failed artifact is not reclassified.

Checkpoint hashes:

- focused diff `c2a8cf3f48c0e68c51885129c60cc534e85210b8b8a796fd17c4b22ea51e255c`
- intervention interactor `fab2e038afe7cd73da926bb30a647b1dd318e6c29d61f782c1f5598f93da8c5b`
- DTO `86181c3f3029dafaf60fa40a1628e38c81fac223094c00f22cf197802681e078`

No DB/network/API/server operation or permission request was made by the reviewer.


## 06:38:51 enum/temperature 실제 검토 — 부정 명제 정규화 실패

[새 raw](real-model-artifacts/probes-20260909T063851Z.json)를 바이트 동일하게 보존했다. **298,821 bytes**, SHA-256 **`db8885673b0672ebfbd2f1fbfda1272aded4513d71e90ea36f0281a208a7e316`**. 실행 `06:38:51.398004Z`–`06:39:45.976343Z`(약54.6초), root session55129 exit0. 질문12+통제10+custom3+ambient3.

**45 harness 작업(interpretation21/evidence21/ambient3), 47 provider 응답, accepted44/rejected3, provider 오류0, fallback1**이다. PC3 evidence가 같은 `evidence_ids=[]/denied`를3회 반환해 missing_public_evidence로 모두 거절되고 fallback unknown이 됐다. 다른 작업은 한 번에 형식을 통과했다. 두 advisor의 모든 attempt temperature=0을 raw에서 확인했고 ambient temperature=null(기존 adapter default)은 구분했다. Q12와 custom은 모델을 쓰지 않는다.

모든 실제 prompt에 대한 assertion으로 interpretation의 원문 기록 격리, binary 단계의 원질문 제외 및 interpretation claim 전달, lookup 원질문 보존, 모든 공개 원문 포함을 확인했다. 모든 반환 source 객체는 해당 available 원본과 일치하며 미래 회차가 없다. 모든 질문 remaining=2로 비용1도 유지된다. 다만 전달된 claim 자체가 항상 올바른 긍정형이라는 뜻은 아니다.

### 통제별 의미 판정

| 통제 | 실제 결과 | 독립 판정 |
|---|---|---|
| PC1 관찰 행동 | positive_proposition/관찰 claim, public2 affirmed → supported | 통과. |
| PC2 발언 존재 | positive_proposition/발언 claim, public1 affirmed → supported | 통과. reported 원문 유지. |
| PC3 미공개 원문·공개 질문 | 공개 claim은 정확; evidence **denied/empty IDs 3회** → fallback unknown | **실패. contradicted가 필요.** 원본 public6이 실제 prompt에 있지만 인용 ID를 반환하지 못함. |
| PC4 미공개 원문·미공개 질문 | type negative_proposition이지만 **positive_claim=공개되지 않았다**. evidence **denied** → supported | 최종만 기대와 같음. **부정 미제거와 근거 오분류가 상쇄된 내부 gate 실패.** |
| PC5 누가 남겼는지 | lookup/null, public2 affirmed → supported | 실제 값 조회 통과. |
| PC6 왜 남겼는지 | lookup/null, public2 **affirmed** → guard unknown | 최종 적절, 이유 없는 원문을 affirmed로 분류한 내부 실패 유지. |
| PC7 내일 공개 여부 | positive_proposition/내일 보존, evidence unknown → unknown | 이번에는 해석·근거 모두 적절. |
| PC8 실제 지시 이행 | positive_proposition/실제 이행 보존, evidence unknown → unknown | 해석·근거 적절. fallback 원문 회복으로 방송/방문과 미확인 범위 제공. |
| SPC1 synthetic 공개 원문·공개 질문 | 공개 claim, public6 affirmed → supported | 통과. |
| SPC2 synthetic 공개 원문·미공개 질문 | type negative_proposition, **positive_claim=공개되지 않았다**, public6 denied → **supported** | **실패. 최종 contradicted가 필요.** |

실제 PC4/SPC2 evidence messages 모두 `[판정할 긍정형 명제] 채연의 검진 결과가 공개되지 않았다.`를 포함한다. PC4 public6은 `결과는 공개되지 않았다`, SPC2 public6은 `결과를 공개했다`다. SPC2의 evidence denied는 실제로 전달받은 부정 명제와 공개 원문 사이에서는 타당하지만, 서버가 그것을 긍정형 명제의 판정으로 가정해 negative_proposition을 다시 반전하면서 오답이 된다. PC4에서는 evidence denied 자체도 잘못이라 두 오류가 상쇄된다. 두 사례를 모두 “정규화된 긍정 명제 판정 성공”으로 세지 않는다. 실제 prompt와 control_source/available/final 원문을 함께 대조했으므로 fixture 메타데이터만 바뀐 문제도 아니다.

원인 경계: interpretation_scope는 claim 존재·lookup null·일부 시점 marker를 검사하지만 주된 술어가 긍정형인지 검증하지 않는다. `question_relation`은 입력 계약을 전제로 반전하므로 잘못된 부정 claim을 받을 때 위 문제가 드러난다. PC3는 원문 접근 부재가 아니라 유효 인용 반환 실패다. 현재 동일 온도0/동일 prompt 재시도는 이 raw에서 동일 잘못된 출력을3번 반복했다. 구체적인 검증 실패 피드백을 주는 제한적 재시도는 검토할 수 있으나 1단계에 공개 근거를 유입시키지 않아야 한다. 주절의 명확한 부정형을 거절하는 검사는 단순 `않` 전체검색이나 자동 문자열 삭제로 대체해서는 안 되며 인용·종속절 부정을 보존해야 한다.

### 원문 및 나머지 경로

Q1–11 최종 unknown은 정당하고 Q12는 실제 기능 안내다. Q1/4 추가 사람, Q2 역할, Q8 정의, Q10 정체, Q11 관계에 모델 evidence affirmed가 나오지만 실제 답은 없어 서버 guard가 교정한다. Q7은 이송 전언만으로 귀환 claim을 denied라고 잘못 판정하지만 미래/전언 guard가 unknown을 유지한다. 이 사례들의 모델 내부 의미 성공을 주장하지 않는다. Q2 detail의 `준은 관리자이다`, Q4 detail의 추가 인물 특정 가능 주장은 무시되며 사용자에게 렌더링되지 않는다.

Q3는 지시/방문 부분 근거를 유지한다. Q9는 public1·6을 함께 보여 주어 검진 장면으로 안내한다. PC8은 방송 cue 보완으로 public1·5·8을 회복하여 관련 원문을 제시하되 실제 이행은 unknown이다. public5 수첩 기록은 명시적 지시 이행의 근거가 아니며 주변 단서로만 취급해야 한다. Q11은 여전히 귀표 public10만 보여 주어 손목띠와의 비교 부분 근거 폭이 제한적이다. 현재 노트/행위자/회차에 연결된 next paths는 존재하지만 다음 행동을 실제 플레이한 유용성 시험은 아니다.

Custom3은 이전과 같은 원문·대상·지식 한계·비실행 대안을 보존한다. Ambient A1/A3는 실제 null 생략, A2는 검진 원문 candidate0을 선택한다. A2의 두 줄이 reported statements/note source_key/두 화자 기억과 일치하고 loop/beat도 현재값임을 assertion으로 확인했다. 미공개 원문과 미확인 한계를 그대로 인용하며 새 사건을 만들지 않는다.

**최신 판정: RM1 P1 변경 요청 유지, 최종 의미 승인 불가.** 최종 통제 상태8개 충족/2개 미충족도 PC4 우연한 상쇄와 PC6 내부 오분류를 감추면 안 된다. BR1–7와 이전 RM2/RM3 구체 재현의 closure는 유지하지만 전체 근거 회복·질문 유용성을 승인한 것은 아니다. 인간 정확도·통계 성능·사용성 지표는 채우지 않는다.

current5파일 hash가 enum manifest와 동일함을 재검증했다. 독립 pure86 checkpoint가 유지되며 root 보고 전체 suite는 **293 passed, 6.84s**다. 검토자는 DB/network/API/server를 실행하지 않고 문서 및 raw 복사만 변경했다. 버전: diff `c2a8cf3f48c0e68c51885129c60cc534e85210b8b8a796fd17c4b22ea51e255c`, interactor `fab2e038afe7cd73da926bb30a647b1dd318e6c29d61f782c1f5598f93da8c5b`, DTO `86181c3f3029dafaf60fa40a1628e38c81fac223094c00f22cf197802681e078`.


## Whole-claim entailment code checkpoint — actual review pending

Independently read the current DTO/interactor/harness and stage regressions; pure tests **87 passed in 0.11s**. The interpretation schema now requests claim/question_kind and preserves the original negation, subject, condition, time and quoted clauses. Evidence classifies the complete supplied claim directly; the old question polarity/positive normalization/matrix flip is removed. Lookup still receives the original query and contradicted lookup outcomes remain unknown. Public evidence originals alone are rendered; no model detail or generated claim becomes a new public fact.

`retry_feedback` defaults false and is enabled only for the two advisor calls. Harness copies the input message list, logs each actual attempt's message snapshot, and appends concrete schema/scope/ID feedback only before another attempt. First-stage time feedback uses the original question marker, not public records. Second-stage missing-evidence feedback lists only IDs already in the stage's public record input; it does not create an ID or establish relation by itself. Unknown without IDs remains valid and nonunknown still requires valid IDs. Provider exceptions retain their prior stop/fallback behavior, both audit roles and one question cost. Existing other-role input behavior is covered by opt-in regression.

No new confirmed code P1/P2 found in this static/pure check. Claim paraphrase and evidence entailment still require actual semantic verification; removing the old double-inversion path does not prove those model judgments are correct. RM1 remains open pending the authorized rerun. Verified current hashes equal the root handoff:

- DTO `b020c54f34fa699d8f861f5dda229e0a6ac256878263bcf89ae84df8111be011`
- interactor `b747ec497c7350f826c0e68efc90f72225cd8166dfd95b1881021511275d2380`
- harness `8c617034a31e661907c42b00375c915e0ed628c74b461b5c62dc0d414c8ae2e2`

No reviewer DB/API/network/server or permission operation occurred.


## 06:47:53 전체 명제 직접 판정 — PC3 및 질문 의미 손실 미해결

[최신 raw](real-model-artifacts/probes-20260909T064753Z.json)를 바이트 그대로 복사했다. **283,483 bytes**, SHA-256 **`7c6b057b8913128f3b4ddcff9ed58d8e27a668e62d348229de1f7cbdd0f443a9`**. 실행 `06:47:53.096227Z`–`06:48:42.356097Z`(약49.3초), root session7771 exit0. 질문12+통제10+custom3+ambient3. **44 harness 작업(interpretation21/evidence20/ambient3), 46 provider 응답, accepted43/rejected3, provider 오류0, fallback1(Q9)**이다. 모든 advisor attempt temperature0, ambient는 기존 설정이다. Q12/custom은 결정적 코드다.

실제 messages를 모두 검사해 첫 단계의 공개 기록 격리, 두 번째 단계의 원질문 대신 claim 전달(proposition), 원문 조회 전달(lookup), 모든 공개 원문 포함을 확인했다. 반환 source 객체·회차와 remaining=2가 일치한다. Q9 재시도 messages 길이는1→2→3이며 실제 `이전 출력의 검증 오류: lookup_must_keep_original ...`가 추가된다. 따라서 feedback은 실행됐지만 모델이3회 모두 nonnull lookup claim을 반복했고 evidence 호출은 생략됐다. 피드백 존재 자체를 복구 성공으로 세지 않는다.

### 통제별 판정

| 통제 | 실제 claim/근거 | 독립 결론 |
|---|---|---|
| PC1 관찰 행동 | 관찰 명제 보존, public2 supported | supported 통과. |
| PC2 발언 존재 | 발언 명제 보존, public1 supported | reported 발언 존재 supported 통과. |
| PC3 미공개 원문·공개 질문 | `채연의 검진 결과가 공개되었다`, public1·6 **unknown** | **최종 unknown 실패. 명시적 미공개 원문으로 contradicted가 필요. RM1 P1 유지.** |
| PC4 미공개 원문·미공개 질문 | `공개되지 않았다` 보존, public6 supported | supported 통과. 이전 부정 정규화/반전 오류가 없음. |
| PC5 누가 남겼는지 | lookup/null, public2 supported | 실제 값 조회 통과. |
| PC6 왜 남겼는지 | **claim=`채연은 자기 몫을 남겼다`, kind=proposition**, public2 supported | 최종 unknown은 guard로 적절하지만 **왜를 행동 발생으로 바꾼 해석 실패**. |
| PC7 내일 공개 여부 | 내일 claim 보존, **public1 supported** | 방송은 오늘 검진/지시 전언이며 내일 결과 공개를 확인하지 않음. 최종 unknown은 reported guard가 교정, **근거 관계 판정 실패**. |
| PC8 실제 지시 이행 | 실제 이행 claim 보존, public1·8 unknown | unknown 통과, 지시/방문 부분 원문 제공. |
| SPC1 synthetic 공개 원문·공개 질문 | 공개 claim, public6 supported | supported 통과. |
| SPC2 synthetic 공개 원문·미공개 질문 | 미공개 claim 보존, public6 contradicted | contradicted 통과. 부정 명제 전체를 직접 판정한 실제 정상 사례. |

PC3 실제 evidence prompt에는 `[판정할 명제] 채연의 검진 결과가 공개되었다`와 public6의 `결과는 공개되지 않았다`가 있다. 선택된 public1은 일반 검진 방송이며 해당 공개 여부의 반박 근거는 public6이다. 이 사례는 provider/fallback/ID 누락이 아니라 accepted relation unknown이다. PC7 실제 prompt에는 내일 공개 claim이 있고 public1은 `오후에는 검진합니다 ... 방송실로 알립니다`일 뿐이다. 같은 원문/claim을 서버가 누락하거나 synthetic metadata만 잘못 전달한 증거는 없다.

최종 통제 상태9개 충족/1개 미충족이지만 PC6·PC7 내부 실패도 별개로 남는다. 이 개수로 의미 gate 통과나 정확도를 주장하지 않는다.

### 원문 질문과 부분 근거

Q1–11 최종 unknown과 Q12 기능 안내는 적절하다. Q1 모델이 제외 대상 public2를 선택하지만 최종은 실제 쟁반 public7로 교정한다. Q2는 empty unknown에서 준의 손목띠 부분 원문을 회복한다. Q3는 지시/방문과 수신자 미확인을, Q7은 이송 전언과 귀환 미확인을 구분한다. Q11은 이번에는 public3 손목띠와 public10 귀표를 함께 인용하고 관계 unknown을 유지해 비교 근거가 회복됐다.

**Q6의 해석은 원문 `열이나면 죽나?`를 claim `열리면 죽는다`로 바꾼다.** 발열 조건을 무엇인가 열리는 조건으로 바꾼 의미 손실이다. 최종 unknown은 우연히 여전히 맞고 모델 claim은 사용자에게 표시되지 않지만 해석 계약은 실패다. Q9는 lookup에 null이 아닌 질문 문장을3번 넣어 fallback으로 끝난다. Q4 추가 사람, Q8 정의, Q10 정체의 supported 모델 출력은 원문이 실제 답을 제공하지 않아 서버 guard가 unknown으로 교정한다. Q10의 optional detail이 축산 글자를 정체로 단정하지만 UI는 그 detail을 무시한다.

후속 경로는 실제 노트/현재 가능한 인물의 원본 회차 장면 질문으로 연결된다. PC7은 부적절하게 선택된 일반 방송 원문에 묶여 장면1 노트로만 안내하므로 내일 공개 여부를 조사할 완전한 정보 제공으로 보지 않는다. 실제 후속 플레이의 유용성은 미측정이다.

Custom3은 원문·단일 대상·지식 한계·비실행 대안을 유지한다. A1/A2는 실제 null 생략, A3는 known-source candidate0을 선택한다. A3의 두 줄은 현재 source의 미확인 출처와 한계를 인용하고 reported statement/note source_key/두 화자 기억·loop/beat와 모두 일치한다. 독립 assertion으로 검증했고 새로운 사건 발명은 없다.

**최신 판정: RM1 P1 변경 요청 유지, 최종 의미 승인 불가.** 전체 명제 직접 판정은 이전 double-flip 경로를 실제 PC4/SPC2에서 제거했으나 명시적 반박·질문 해석·미래 근거 관계 문제가 남는다. BR1–7와 이전 RM2/RM3 구체 재현 closure는 유지하며 이를 전체 advisor 사용성 승인으로 확대하지 않는다.

Current10파일 hash가 entailment manifest와 동일하다. 독립 pure87 checkpoint와 root 보고 **294 passed, 6.63s**를 분리 기록한다. diff SHA `731c4363aaa82713ce923fa269caf8864e572c5488f2eb2c1fe0ce4f6296a053`; DTO `b020c54f34fa699d8f861f5dda229e0a6ac256878263bcf89ae84df8111be011`; interactor `b747ec497c7350f826c0e68efc90f72225cd8166dfd95b1881021511275d2380`; harness `8c617034a31e661907c42b00375c915e0ed628c74b461b5c62dc0d414c8ae2e2`. 검토자는 DB/API/network/server/권한 요청을 하지 않고 문서와 raw 복사만 변경했다. 인간 정확도·통계 성능·사용성 지표는 미측정이다.


## 06:55:04 exaone A/B — 생산 변경 아님, 관계 gate 실패 유지

[별도 exaone raw](real-model-artifacts/probes-exaone-20260909T065504892941Z.json)를 동일 바이트로 보존했다. **302,518 bytes**, SHA-256 **`d797217ce956e5256bf98928ff396bece7bbee2c74ec5278f24635ec03be315c`**. 실행 `06:55:04.892941Z`–`06:55:40.889598Z`(약36.0초), root session62843 exit0. **이는 helper의 advisor 모델만 바꾼 비교 실행이며 생산 모델 교체가 아니다.**

helper 원문·clone을 직접 읽어 advisor constructor 모델, 결과 models 메타데이터, 출력 파일 prefix/timestamp의 정확히3개 치환 외에는 동일함을 확인했다. helper SHA는 original `a568415b5ed215ccaae2d08d7c38752b02717c8cf0aac7ff155f73b998f48e30`, exaone `7498b778890dbab42ae081b0b8b8b29751cd4ff340c1a05bad338dfda6648799`로 verification.json과 일치한다. 두 raw의 질문·회차·각 available 원문 text/actor/beat/verification/source_kind를 비교해 동일 corpus임을 assertion으로 확인했다. 임의 UUID 차이는 비교에서 제외했다.

모든45 harness model은 **exaone3.5:7.8b**, advisor temperature0이며 helper 실제 constructor와 일치한다. **45 작업(interpretation21/evidence21/ambient3), 51 provider 응답, accepted45/rejected6, provider 오류0, fallback0**이다. Q1/Q2/Q3/Q5/PC5/PC6의 lookup nonnull claim은 최초 거절 후 feedback을 받고 각각 두 번째에 null로 복구했다. 모델 digest/서버 버전은 이 검토에서 재조회하지 않았다. 실제 응답 존재와 호출 모델 경로를 확인한 것이며 메타데이터 이름만으로 성공을 가정하지 않았다.

### 통제와 A/B 의미 비교

| 항목 | exaone 실제 결과 | 직전 gemma와 비교한 독립 판정 |
|---|---|---|
| PC1/PC2 | 관찰 행동/발언 명제 보존, supported | 두 모델 모두 적절. |
| PC3 미공개 원문·공개 질문 | claim 정확, public6 **unknown** | 두 모델 모두 **실패**, contradicted 필요. |
| PC4 미공개 원문·미공개 질문 | 부정 claim 보존, public6 supported | 두 모델 모두 적절. |
| PC5 누구 조회 | 첫 nonnull lookup 거절 후 null 복구, public2 supported | 최종 의미는 적절, exaone은 재시도 필요. |
| PC6 왜 조회 | 첫 행동claim/lookup 거절 후 null 복구, public2 unknown | 이번에는 의미/근거가 복구됨. gemma는 왜를 proposition 행동으로 바꿔 guard 의존. |
| PC7 내일 공개 | 내일 보존, public6 unknown | 이번에는 의미/근거 적절. gemma는 오늘 방송으로 supported를 내고 guard 의존. |
| PC8 실제 이행 | 실제 이행 claim 보존, relation unknown | 양 모델 최종/명제 적절. exaone은 모든8기록 ID를 반환해 원본 선택이 덜 정밀함. |
| SPC1 synthetic 공개 원문·공개 질문 | 공개 claim, supported | 두 모델 모두 적절. |
| SPC2 synthetic 공개 원문·미공개 질문 | 부정 claim 보존, public6 **supported** | **exaone 실패**, contradicted 필요. gemma는 이 쌍에서 통과. |

PC3/SPC2 실제 evidence messages를 재검사했다. PC3는 `[판정할 명제] 채연의 검진 결과가 공개되었다`와 public6의 `결과는 공개되지 않았다`, SPC2는 `[판정할 명제] 채연의 검진 결과가 공개되지 않았다`와 public6의 `결과를 공개했다`를 받았다. 원문/claim/fixture 메타데이터 혼선이 아니다. **RM1 P1은 미해결**이며 두 모델 중 하나가 전반적으로 문제를 해결한다는 증거가 없다.

### 한국어 조회·조건 보존의 개선과 회귀

- Q6 `열이나면`을 exaone은 `열이 나면 죽는다`로 올바르게 보존했다. gemma의 `열리면` 변형은 이번에는 없다.
- Q1/Q2/Q3/Q5는 첫 해석에 답을 생성했다(`아무도 없다`, `준은 학생`, `선생님께 보고`, `신원 미상`). lookup/null 검증이 거절하고 feedback 후 null로 복구하여 이 답은 UI에 노출되지 않는다.
- Q4 “채연 말고 추가로 ... 사람”을 exaone은 **채연이 배급을 남겼다**라는 proposition으로 바꿔 제외 대상과 요청 값을 잃었다.
- Q7 “돌아오는가”를 **돌아오지 않는다**로 반전하고 이송 전언만으로 supported라 판정한다. 원문의 질문 극성과 미래 결과를 바꾸는 실제 내부 실패다. guard가 최종 unknown을 유지한다.
- Q8 정의 조회를 **귀표는 동물의 청각을 보호한다**, Q9 처분 조회를 **추가 검사/치료가 필요할 수 있다**, Q10 정체 조회를 **트럭은 동물 운송에 사용된다**, Q11 관계 조회를 **서로 보완적 역할**이라는 proposition으로 첫 단계에서 답해 버렸다. 첫 단계는 공개 기록을 받지 않는 것이 실제 messages에서 확인되므로 이는 근거 없는 답 생성이며 질문을 평서문으로 보존한 것이 아니다.
- 모델 생성 claim은 UI에 직접 출력되지 않고 기존 guard가 최종 Q1–11 unknown을 유지한다. 그럼에도 새 내부 계약의 의미 성공으로 세지 않는다. Q8 최종 근거는 귀표 public10 대신 손목띠 public3만 남아, 원래 질문에 더 가까운 이미 공개된 용어 기록의 회복도 실패한다.

여러 evidence 호출은 요청과 무관한 원본 ID를 다수 반환한다. 최종 필터가 좁혀서 원본과 회차는 맞지만 모델 자체의 관련성 성공은 아니다. Q3 수첩/방송실 방문, PC8 전체 기록 선택의 폭을 요청한 보고 수신자/이행 확인과 혼동하지 않는다. Q11 최종은 두 표시 원문을 함께 보여준다. 다음 경로는 실제 원본 노트/인물 대화지만 후속 플레이의 유용성은 시험하지 않았다.

모든 최종 evidence 객체/회차/질문비용1과 실제 단계 입력 격리를 assertion으로 확인했다. Custom3은 동일 원문·대상·비실행·지식 한계를 유지한다. Ambient A1/A2/A3는 모두 실제 candidate0을 선택하며 각 현재 원문+미확인 한계2줄, reported statements/note source_key/두 화자 기억·loop/beat가 일치한다. 새 사건 발명은 없다. ambient 모델은 원래부터 exaone이므로 A/B advisor 개선 근거로 세지 않는다.

### 원인 가설과 현재 권고

두 모델이 PC3를 모두 unknown으로 판정한 것은 task/prompt의 불명확성이나 과도한 보류 지시 가능성을 검토할 단서지만 **원인을 증명하지 않는다**. 현재 prompt는 same-event 반박을 허용하는 동시에 reported 진실 미확인·모호한 대상 unknown·공개 여부/내용 구분을 연속해서 강조한다. 모델이 observed 기록의 명시적 반박에도 이를 과도하게 일반화할 가능성은 추론이다. PC3/SPC2의 동일 claim+public6만 남긴 짧은 관계 지시와 현재 전체 prompt를 제한적으로 비교하면 문맥/지시 간섭 가설을 분리할 수 있다. 이런 진단 없이 안전 지시를 삭제하면 고쳐진다고 주장하지 않으며 reported guard는 유지해야 한다.

**A/B 결론: 부분 개선과 다른 오류가 함께 나타나 생산 모델 교체나 전체 의미 승인 근거가 되지 않는다.** 최종 통제 상태8개 충족/2개 미충족은 작은 비교 gate의 사례별 결과이며 정확도·사람 검토·통계 성능·사용성 지표가 아니다. 기존 BR1–7/RM2/RM3 구체 closure는 유지하되 RM1 변경 요청은 유지한다. current10 code/test hashes는 기존 entailment manifest와 같고 full294/pure87 checkpoint도 생산 코드 기준 그대로다. 검토자는 DB/API/network/server 호출이나 모델 설정 변경을 하지 않았고 문서/raw 복사만 변경했다.


## 07:07:29 제한 NLI 진단 — 추출 우선4관계 성공, 제품 승인 아님

[12호출 진단 raw](real-model-artifacts/nli-diagnostic-20260909T070729518766Z.json)를 바이트 그대로 보존했다. **137,021 bytes**, SHA-256 **`717be685f46e28bbb40c637a11118466d0551da29b26fcf75d22511883b32f8a`**. 실행 `07:07:29.518766Z`–`07:07:49.463381Z`(약19.9초), root session78490 exit0. gemma3:12b/temperature0이며 원래 064753의 PC3/PC4/SPC1/SPC2 evidence 단계만 대상으로 한다. 첫 해석·전체 질문 corpus·제품 합성·DB 저장을 실행한 시험이 아니다. 모델/생산 코드 변경도 없다.

**12개 HTTP200, raw response와 provider_response/파싱 output 동일, provider_model=gemma3:12b, 오류0**를 확인했다. 진단 helper는 직접 한 번씩 HTTP 호출하며 production harness 재시도/fallback은 사용하지 않는다. 따라서 “fallback0으로 production을 통과” 같은 표현을 사용하지 않는다. ID 존재·관계의 근거 존재·스키마 검사는 모두 통과한다.

fixture의 실제 claim/expected/source 객체와 원래 064753 raw를 직접 대조했다. original 변형 messages는 원래 evidence call과 동일하다. original과 concise는 같은 schema이며 세 변형의 전체 records_text와 claim/expected는 동일하다. **public6만으로 축소하지 않았다.** extract_first는 concise에 인용 지시와 선행 evidence_quotes 필드를 추가한다. 이 변형은 prompt와 schema 두 요소를 함께 바꾸므로 “prompt 축약만의 효과”로 인과를 단정할 수 없다.

| 관계 통제 | original | concise | extract_first |
|---|---|---|---|
| PC3 미공개 원문·공개 명제 | unknown, 실패 | unknown, 실패 | contradicted, 일치 |
| PC4 미공개 원문·미공개 명제 | supported, 일치 | supported, 일치 | supported, 일치 |
| SPC1 공개 원문·공개 명제 | supported, 일치 | supported, 일치 | supported, 일치 |
| SPC2 공개 원문·미공개 명제 | contradicted, 일치 | contradicted, 일치 | contradicted, 일치 |

추출 우선4개 응답의 **6개 인용 모두 해당 ID 원본의 비어 있지 않은 부분 문자열**이며 반환 evidence_ids와도 일치함을 독립 assertion으로 확인했다. PC3는 public1 전체 방송과 public6 전체 검진 장면, PC4는 public6, SPC1은 public1 방송 일부와 public6 `결과를 공개했다`, SPC2는 public6을 인용했다. 명시적 부정이 주어 생략 문장 안에 있어도 이번 추출 우선 실행은 PC3를 반박으로 판정했다. 이것은 좁은 진단의 긍정 결과이며 일반 의미 정확도를 뜻하지 않는다.

중요한 제품 경계: PC3/SPC1은 관찰 public6 외에 전언 public1도 선택했다. 현재 interactor의 `any(verification != observed)` guard는 발언 존재 질문이 아닌 경우 모든 결과를 unknown으로 낮추므로, **이 raw 출력을 기존 제품 경로에 넣으면 두 사례는 여전히 unknown이 된다.** 따라서 diagnostic4/4를 현재 제품 gate 통과로 세지 않는다. public1 일반 검진 방송은 결과 공개 여부를 지지/반박하는 직접 근거가 아니지만 public6 관찰의 유효한 판정을 전체 veto해서도 안 된다.

검토한 후속 설계는 source별 `{id,quote,relation}`을 검증하고 eligible observed 또는 발언 존재 범위의 reported만 집계하며, 관련 전언은 부분 근거로 보존하는 것이다. 유효 source 중 한 방향만 있으면 해당 relation, 양방향 충돌/판정 없음은 unknown이 타당하다. unknown source를 반대 판정으로 세지 않고 invalid ID/empty/nonverbatim 인용은 승격하지 않아야 한다. 첫 단계에서 claim 재작성을 제거하고 원문 질문을 두 번째에 전달하면 확인된 발열/이유/극성 변형 경로를 제거할 수 있다. 그러나 **이 새로운 per-source 계약·집계·kind-only 해석·lookup은 이번 진단이 시험하지 않았다.** 구현 후 전체 기존 corpus와 통제를 재검증해야 한다.

fixture hash 표기는 알고리즘 차이가 있다. verification의 file-byte SHA는 `40c7f4117a9bb6803e2cef6e60a01afb4368866b941348002a15c60df49ea94a`; raw의 `fixture_sha256=f7f5799abde30809095a65cb415fce11b952c1be270bd9338f4a3deed3f48f1d`는 helper의 sorted-key JSON 직렬화 SHA다. 직접 재계산해 둘 다 일치했다. 이는 파일 변조가 아니다. helper SHA는 `183e5745b7b19b8fe82a34be9d3137b854f125389130bb27a89e2ac37762088e`다.

**현재 판정은 RM1 미해결/제품 의미 승인 보류를 유지한다.** original/concise 각3관계와 extract_first4관계 일치는 단4명제의 비통계적 진단 결과다. 기존 실패 원문을 폐기하거나 사람 정확도·제품 전체 품질로 승격하지 않는다. 검토자는 DB/API/network/server를 호출하지 않고 raw 복사와 문서만 변경했다.


## Kind-only/source-assessment code checkpoint — live evidence pending

Independently read current DTO/interactor and source/stage tests; database-free pure tests **100 passed in 0.13s**. All8 handoff manifest hashes match current files. First stage has only question_kind and cannot emit a rewritten claim; second stage receives the original question unchanged. Each source assessment requires a real ID, nonempty verbatim quote and relation. Unknown IDs, whitespace/nonverbatim quotes and duplicate IDs with conflicting relations trigger feedback/retry; identical duplicates render once. Eligible observed sources and reported utterance-occurrence sources contribute separately; unknown context does not veto a decisive source, and both relation directions remain unknown. Unresolved-scope guards run against each full original source, preserving context beyond the short quote. Lookup contradiction remains unknown.

Single-question budget, both audit roles, provider-failure boundaries, original evidence rendering and other-role retry behavior remain covered. No additional confirmed code P1/P2 found. This verifies extraction/aggregation mechanics, not model judgment accuracy or complete source recall; original whole-corpus and opposite-source live controls remain required before RM1 closure.

Hashes: focused diff `918845fc794e12584fa75d25ef0c92ced56f630556d98a0c48c08f8b147a3069`; DTO `0a7374c489dcd7042e009ddb0aa34eadc882eac0104e673853be7903792dcc3c`; interactor `7f93b0bdfb4897c6b0fee0d98fb6098b5cd8d33df4a1275966cddc37764de5a4`. No reviewer DB/API/network/server operation or approval request occurred.


## 07:19:26 kind-only/근거별 집계 실제 검토 — 인용 정확, 분류·관계 실패

[최신 raw](real-model-artifacts/probes-20260909T071926Z.json)를 바이트 동일하게 보존했다. **286,715 bytes**, SHA-256 **`2f07c1fc432460e3601d086423b99170716b9709f1d396eabf3f5059f856b814`**. 실행 `07:19:26.807211Z`–`07:21:07.103800Z`(약100.3초), root session26820 exit0. 질문12+통제10+custom3+ambient3.

**45 harness 작업(interpretation21/evidence21/ambient3), 46 provider 응답, accepted45/rejected1, provider 오류0, fallback0**이다. Q11의 첫 귀표 인용은 원문의 ASCII 따옴표를 곡선 따옴표로 바꿔 non_verbatim_evidence로 거절됐고, feedback 후 두 번째에 정확한 원문으로 복구됐다. **accepted 응답의79개 인용 모두 비어 있지 않은 해당 ID 원문 부분 문자열**임을 독립 assertion으로 검증했다. 인용 개수에는 무관한 맥락/중복된 질문 간 인용도 포함되므로 근거 관련성 성공 개수는 아니다.

실제 모든 첫 호출은 question_kind만 반환하고 공개 기록은 받지 않는다. 두 번째 모든 실제 messages에 원래 질문이 바이트 그대로 있으며 공개 원문 전체가 있다. 기존 발열 표현을 열리면으로 바꾸거나 why를 행동 claim으로 고쳐 전달하는 코드 경로는 제거됐다. 두 advisor temperature0, 반환 source 객체/회차, 모든 remaining=2와 질문 비용1도 일치한다. 그러나 유형 오분류가 질문의 답변 방식을 여전히 바꾼다.

### 통제별 관계·자격·집계 판정

| 통제 | first 분류 및 근거별 모델 판정 | 최종/독립 판정 |
|---|---|---|
| PC1 행동을 봤는지 | **lookup 오분류**. public2 supported, 쟁반 public7 unknown | supported 자체는 맞지만 proposition 종류 실패. |
| PC2 관리자 발언 여부 | proposition. public1 발언 supported, public8 방문 unknown | reported 발언 존재가 eligible, unknown 방문이 veto하지 않음. supported 통과. |
| PC3 결과가 공개됐는지 | **lookup 오분류**. 미공개 public6 quote를 **supported** | **status=supported, answer=기록은 이렇다. 기대 contradicted와 반대라 P1 실패.** |
| PC4 결과가 미공개인지 | **lookup 오분류**. 미공개 public6 supported | 최종 supported는 맞지만 유형 gate 실패. |
| PC5 누가 남겼는지 | lookup. public2 supported, public7 unknown | 실제 값 조회 supported, 적절. |
| PC6 왜 남겼는지 | lookup. 행동 public2 **supported**, 쟁반 unknown | 원인 없음으로 source-scope guard가 unknown. 최종 적절하나 근거별 판정 실패. |
| PC7 내일 공개 여부 | **lookup 오분류**. 오늘 미공개 public6 **contradicted**, 방송 unknown | lookup의 contradicted를 unknown으로 낮춰 최종만 맞음. 현재 미공개가 내일 공개의 반박이라는 근거 판정도 틀림. |
| PC8 실제 지시 이행 | **lookup 오분류**. public1/public8 unknown | 최종 unknown 적절, 유형 실패. |
| SPC1 synthetic 공개·공개 질문 | **lookup 오분류**. 공개 public6 supported | 최종 supported는 맞지만 유형 gate 실패. |
| SPC2 synthetic 공개·미공개 질문 | **lookup 오분류**. 공개 public6 **supported**, 방송 unknown | **status=supported, answer=기록은 이렇다. 기대 contradicted에 실패.** |

PC3 실제 두 번째 입력은 `[원래 질문] 채연의 검진 결과가 공개되었어?`와 public6의 `결과는 공개되지 않았다`를 포함하며, 출력 quote는 `담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다.`다. SPC2는 `[원래 질문] 채연의 검진 결과가 공개되지 않았어?`와 공개 원문 `결과를 공개했다`를 받는다. 질문/원문 전달이나 synthetic 메타데이터가 잘못된 것이 아니다. lookup로 분류되면서 “공개 여부 정보가 있다”를 supported로 붙이는 패턴과 일치하지만 내부 추론을 확인한 것은 아니므로 원인은 이 출력 범위로 한정한다.

현재 코드 집계는 주어진 유효 relation을 일관되게 처리했다. reported의 일반 배경은 관찰 판정을 veto하지 않고, unknown은 반대 vote가 아니며 중복/비원문 검증도 작동했다. **하지만 유효한 원문 quote가 있다는 사실은 원래 질문에 대한 source relation이 맞다는 뜻이 아니다.** 이번에는 핵심 두 반박 통제가 모두 supported로 승격된다. 07:07 단일 evidence 진단의4/4 성공이 새 두 단계 계약에서 재현됐다고 볼 수 없다. 최종 상태8개 충족/2개 미충족도 일곱 통제의 잘못된 유형과 근거별 오류를 감추므로 품질 지표로 사용하지 않는다.

### 원문 질문과 다음 관찰

Q1–11 최종 unknown은 정당하고 Q12는 기능 안내다. Q1/4는 제외 대상 채연을 supported로 선택하지만 필터가 제거하고 쟁반만 남긴다. Q2의 `관리자입니다`와 Q3의 같은 문구가 역할/수신자를 supported로 판정하지만 관련성·reported·scope 처리가 이를 최종 확정에서 제외한다. Q6은 원문 발열 조건이 그대로 전달되어 근거 unknown, 단 모델은 거의 모든 공개 기록을 인용해 관련성이 낮다. Q7은 yes/no 귀환을 lookup으로 오분류하고 이송 전언을 supported로 판정하나 귀환/전언 guard가 unknown으로 유지한다.

Q8 단어 사용, Q9 일반 방송 지시, Q10 트럭 글자와 이송 전언, Q11 두 표시의 관찰/단어 사용에 supported가 붙는 사례는 실제 요청한 정의·처분·정체·관계의 지지가 아니다. 최종 guards가 unknown을 유지한다. Q11의 재시도는 원문 부호를 복원하는 대신11개 기록을 열거하며 source recall이 넓어진다. 최종은 실제 손목띠/귀표 원문과 준의 회차3 장면 안내로 좁혀진다. Q8도 이번에는 두 표시 원문을 제공한다. 최종 next paths는 원래 장면 노트/실제 인물의 낮 대화로 연결되지만, 후속 플레이의 유용성을 이 probe가 확인한 것은 아니다.

Custom3은 원문·대상·지식 한계·비실행 대안을 유지한다. Ambient A1은 실제 null 생략, A2 검진 candidate0과 A3 known-source candidate0은 각각 두 줄을 생성한다. generated statements의 reported label, note source_key, 두 화자 기억, loop/beat가 최종 대사와 모두 일치함을 assertion으로 검증했다. 새 사건 발명은 발견되지 않았다.

**최신 gate: RM1 P1 미해결, 최종 의미 승인 불가.** BR1–7 및 기존 RM2/RM3 구체 재현 closure는 유지하되 전체 advisor 의미/관련성/사용성 승인으로 확대하지 않는다. 모델응답·원문 인용·집계 테스트 성공과 의미 판정 실패를 분리한다. 사람 정확도·통계 성능·사용성은 미측정이다.

Current8 source/test hash가 source manifest와 동일하다. 독립 pure **100 passed in 0.13s**, root 전체 suite **307 passed, 6.66s**를 구분한다. focused diff `918845fc794e12584fa75d25ef0c92ced56f630556d98a0c48c08f8b147a3069`; DTO `0a7374c489dcd7042e009ddb0aa34eadc882eac0104e673853be7903792dcc3c`; interactor `7f93b0bdfb4897c6b0fee0d98fb6098b5cd8d33df4a1275966cddc37764de5a4`. 검토자는 DB/API/network/server/권한 요청을 하지 않고 문서와 raw 복사만 변경했다.


## 07:25:15 질문 분류/강제 올바른 유형 진단 — 두 실패 단계 분리

[28호출 진단 raw](real-model-artifacts/kind-diagnostic-20260909T072515636890Z.json)를 바이트 동일하게 보존했다. **321,111 bytes**, SHA-256 **`47429c71ac0840369a03867c5e098f99bda4d56d60959c35b0a5d6a2637fd0f9`**. 실행 `07:25:15.636890Z`–`07:25:44.577171Z`(약28.9초), root session51640 exit0. 원래071926의21문항 유형 분류 후보와7문항의 강제 올바른 유형 evidence 단계다. 생산 코드나 corpus 변경이 아니며 두 단계 전체를 실제로 연결 실행한 것도 아니다.

**28개 HTTP200, provider_model gemma3:12b, temperature0, raw/parsed response 일치, 오류0**. 진단은 재시도/fallback 없이 직접 한 번씩 호출한다. 질문·expected·available 원문 객체를071926과 대조했고, 강제 evidence messages의 전체 공개 source block은 기존 실제 입력과 바이트 동일하다. 분류 후보 messages에는 원래 질문만 있으며 공개 원문/ID가 없다. forced-kind는 in-memory fake 분류를 거친 현재 use case에서 캡처한 prompt이고 모델 분류 성공을 전제로 했다는 경계를 유지한다.

### 분류 후보

“예/아니오로 완결되면 proposition, 사람·이유·값 등을 요청하면 lookup” 설명과 일반 문닫기 긍정/부정/미래/누구/왜/역할6예시를 붙인 후보는 **21개 expected kind와 모두 일치**했다. 여기에는 기존 오분류인 귀환, 관찰 여부, 공개/미공개, 미래, 실제 이행 질문이 포함된다. 이 결과는 해당 후보가 이 corpus에서 분류 문제를 고친다는 좁은 증거이며, 세계 사실의 관계 판단이나 모든 한국어 문형의 정확도를 입증하지 않는다.

### 올바른 유형을 강제한 evidence7

| 사례 | 각 원본의 실제 관계 | 독립 의미 판단 |
|---|---|---|
| PC3 미공개 원문·공개 질문 | public6 supported | **실패**. 명시적 미공개는 contradicted. 유형을 바로잡아도 오답. |
| PC4 미공개 원문·미공개 질문 | public6 supported | 적절. |
| SPC1 공개 원문·공개 질문 | public6 supported | 적절. |
| SPC2 공개 원문·미공개 질문 | public1 unknown, public6 supported | **실패**. 공개 원문은 미공개 명제를 contradicted. |
| PC6 왜 남겼는지 | 행동 public2 supported, 쟁반 public7 unknown | **근거 관계 실패**. 이유 없으므로 public2도 unknown. |
| PC7 내일 공개 여부 | 오늘 검진 방송 public1 supported, 현재 미공개 public6 contradicted | **두 근거 관계 모두 실패**. 오늘 검진 지시나 현재 미공개는 내일 공개 여부를 결정하지 않음. |
| PC8 지시 실제 이행 | 방송 public1 unknown, 검진 public6 unknown | 관계는 적절. 선택된 검진 원문은 지시 이행의 직접 근거가 아니라 부분/일반 맥락임. |

**11개 인용은 모두 해당 원본의 정확한 비어 있지 않은 구절**이다. 스키마·인용 검증과 source relation의 의미 실패는 분리한다. 실제 PC3/SPC2 질문과 공개/미공개 원문이 바뀌거나 유형만 잘못 주입된 문제가 아님을 확인했다.

추가 무DB 확인: 현재 `question_evidence`/`unresolved_question`과 eligible 집계에 이 모델 출력 및 올바른 kind를 적용해 계산하면 PC3=supported, SPC2=supported, **PC7=contradicted**로 세 사례가 기대와 다르다. PC6는 이유 scope guard가 unknown으로 보호하고 PC8도 unknown이다. 이는 실제 API 응답을 새로 실행한 것이 아니라 현재 코드의 결정적 집계를 독립 계산한 결과다. 특히 이전 PC7 최종 unknown은 잘못된 lookup의 contradicted 제거가 가렸던 것이며, 올바른 분류만 적용하면 관찰 public6의 잘못된 미래 반박이 노출된다.

**결론: 분류 실패와 근거 추론 실패는 독립적으로 확인됐다.** 후보 분류21/21만 production에 넣어 RM1을 닫을 수 없다. “관련 기록에 질문의 답이 있다”와 “질문에 담긴 명제가 그대로 사실이다”를 supported로 혼동하는 가능성이 출력에서 드러나지만 내부 원인을 확정한 것은 아니다. 후속 근거 prompt 진단도 원래 질문·원문·기대 관계를 유지해야 한다. 명시적 반대/why 정보 부재/미래 미확인의 수용 기준은 바꾸지 않는다.

raw fixture canonical SHA `565804968fbbf3724a27c503bdbbe5cc03805693d4756ca249202fe6e998c1a3`는 sorted JSON 재계산과 일치한다. origin raw SHA는 `2f07c1fc432460e3601d086423b99170716b9709f1d396eabf3f5059f856b814`로 동일하다. **RM1 변경 요청 및 제품 의미 승인 보류 유지**. 기존 failed raw를 대체하지 않고 별도 진단으로 보존하며 사람/통계 정확도·사용성 지표로 환산하지 않는다. 검토자는 DB/API/network/server를 호출하지 않고 원문 읽기·무DB 결정 로직 확인·문서/raw 복사만 수행했다.


## 07:29:00 explicit-answer-meaning diagnostic — improvement with SPC2 still wrong

[Seven-call raw](real-model-artifacts/answer-semantics-diagnostic-20260909T072900364027Z.json) is copied byte-identically, **139,670 bytes**, SHA-256 **`db33d6c4619008f31e8b997add83467b732f427055d98ad6dfc27bd752f8cd59`**. Root session52784 exit0, `07:29:00.364027Z`–`07:29:17.576876Z`. Independently verified all7 HTTP200 responses, gemma3:12b, temperature0, raw/parsed agreement and no errors. All9 quotes are nonempty substrings of their cited originals. Questions, forced correct kinds, expected relations/IDs, whole public source blocks and schema exactly match the previous forced-kind diagnostic. Only candidate evidence instructions change; this is not a new production run.

PC3 now returns contradicted correctly; PC4 and SPC1 remain supported correctly; PC7's two sources now correctly say unknown for tomorrow's disclosure; PC8's instruction/visit sources remain unknown. **SPC2 still wrongly supports the negative disclosure question against an explicitly published original. PC6 still labels observed food leaving supported for a why question without any reason.** Thus five cases have appropriate source semantics and two do not. Current reason-scope guard protects PC6's final unknown, so six final expectations would match under aggregation, but that is not seven-case source-semantic success.

This candidate is a bounded improvement over the preceding seven-call diagnostic while RM1 remains open. No new architecture/diagnostics are requested. The final production prompt-only change and single full-corpus rerun will determine the final unresolved disposition; old failed artifacts and unchanged expectations remain preserved. This diagnostic provides no human accuracy, statistical performance or usability estimate. Reviewer performed no network/DB/model/server operation and changed reports/raw copies only.


## Frozen final prompt checkpoint — exact diagnostic text reuse

Reviewed `/tmp/connected-final-prompts.diff`: only classification/evidence prompt strings change, with schema, extraction, eligibility, aggregation, audit and API behavior otherwise unchanged. AST literal evaluation verifies the actual concatenated production first prompt exactly equals the successful21-question classification diagnostic's CLASSIFY string, and second prompt components exactly equal the seven-case semantics diagnostic's COMMON/LOOKUP/PROPOSITION strings. No helper import or model call was required. Current interactor hash is **`6fb42a732b4def2fb24892a7e741cb4593271de4004c976ade78a51d03a2d8d9`**; focused diff SHA **`7218f7035fe76dc79b39f2095f969b2acfbacbe7744f894afe2bbcb3879f6076`**. Pure tests were not repeated; root is running the final full suite and one complete model corpus. Previous diagnostic SPC2/PC6 limits remain acknowledged. Final semantic disposition awaits that sole last raw; no further architecture/diagnostic iterations are requested.


## FINAL — 07:35:56 마지막 전체 실행, RM1 P1 미해결 확정

**최종 독립 gate: 변경 요청 유지 / 의미 승인 불가.** 마지막으로 허용된 전체 실행을 검토했고 추가 코드 수정·진단·재시험을 요구하지 않는다. 기존 운영 서버로 새 코드를 승격할 검토 승인은 제공하지 않는다. 한 건의 명확한 반대 사실 판정 오류와 근거 관계의 잔여 한계를 아래에 보존하며, 이 결과를 바탕으로 사용자/주 담당자가 다음 범위를 결정해야 한다. 이전 expected corpus와 모든 실패 raw는 그대로 유지된다.

### 고정된 코드와 실제 실행 증거

[최종 raw](real-model-artifacts/probes-20260909T073556Z.json) **277,531 bytes**, SHA-256 **`adf69d8b2df289aefdb964fb2aa6282417a76481ce5dc70b8495e13cdbb969a4`**. root session45347 exit0, 실행 `07:35:56.492620Z`–`07:36:58.672944Z`(약62.2초). 원문12질문+별도10통제+custom3+production ambient3. **45 harness 작업(interpretation21/evidence21/ambient3), 45 provider 응답, accepted45, rejected0, provider 오류0, fallback0**이다. Q12/custom은 모델 호출이 없다. advisor gemma3:12b/temperature0, ambient exaone3.5:7.8b/기존 설정을 raw로 확인했다.

분류21개는 기존 기대 종류와 전부 일치한다. **accepted30개 인용 모두 해당 실제 ID 원본의 비어 있지 않은 부분 문자열**이며, 반환 evidence 객체는 각 질문 available 원본과 동일하고 미래 회차가 없다. 첫 단계에 공개 자료가 없고 두 번째에는 원래 질문과 전체 공개 원문이 그대로 전달된다는 것을 실제 messages로 assertion 검증했다. 모든 질문 remaining=2이므로 비용1이다. 모든 유효 호출과 최종 출력은 audit에 남아 있다. 이 수치들은 형식·출처·호출 성공이지 의미 정확도 지표가 아니다.

### 최종 미해결 P1 — SPC2가 반대 사실을 “맞다”로 답함

- 질문: **`채연의 검진 결과가 공개되지 않았어?`**
- fixture: **synthetic-public-6-explicitly-published**. 합의된 역방향 통제이며 게임 원문이라고 주장하지 않는다.
- 실제 model prompt의 public6: **`채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과를 공개했다.`**
- first output: `question_kind=proposition`로 정상.
- second output: 위 원문을 정확히 인용하면서 **`relation=supported`**.
- 최종 사용자/API 출력: **`answer=맞다`, `status=supported`**.
- 필요한 관계: **`contradicted`**. 실제로 공개됐다는 관찰은 같은 사건이 공개되지 않았다는 명제의 반대다.

Exact raw paths: `positive_controls[9].harness[0].call_records[0].output`, `positive_controls[9].harness[1].call_records[0].messages`, `.output`, `positive_controls[9].result`. 원문·질문·통제 메타데이터·인용을 직접 대조했으므로 fixture 전달 오류나 모델 원문 부호 오류가 아니다. 실제 통신/스키마/인용도 통과했으며 현재 `intervention_interactor.py:231`은 인용의 유효성을 확인하고 `:252`–`:259`는 eligible relation을 그대로 집계한다. **정확한 인용을 잘못 해석한 관계가 최종 확정으로 전달되는 의미 결함**이다.

### 최종 통제별 판정

| 통제 | 최종 관계 | 독립 의미 판단 |
|---|---|---|
| PC1 관찰한 배급 행동 | supported | 유형·source 관계 적절. |
| PC2 관리자 발언 존재 | supported | reported 발언 존재만 지지, 실제 이행으로 승격하지 않음. |
| PC3 미공개 원문·공개 질문 | contradicted | 최종 실행에서 교정됨. |
| PC4 미공개 원문·미공개 질문 | supported | 적절. 부정 보존과 source 관계 모두 맞음. |
| PC5 누가 남겼는지 | supported | 실제 사람·행동 원문 조회 적절. |
| PC6 왜 남겼는지 | unknown | 최종은 적절하지만 **행동 원문을 supported로 판정하는 내부 결함**이 남고 이유 scope guard가 보호함. |
| PC7 내일 공개 여부 | unknown | 현재 방송/검진 원문 각각 unknown, 미래 범위 적절. |
| PC8 실제 지시 이행 | unknown | 지시·방문 source 각각 unknown, 요청 실행 범위 적절. |
| SPC1 공개 원문·공개 질문 | supported | 적절. |
| SPC2 공개 원문·미공개 질문 | **supported** | **오답. RM1 P1 최종 미해결.** |

최종 상태9개 일치/1개 불일치는10개 gate의 결과일 뿐 통계 정확도나 전체품질이 아니다. PC6 내부 실패를 포함하면 source별 의미 계약도 모두 통과한 것이 아니다. PC3 한 건의 개선을 RM1 전체 해결로 바꾸지 않는다.

### 원문 질문과 유용성의 잔여 한계

Q1–11 최종 unknown은 당시 원문이 요구 정보를 확정하지 않으므로 정당하다. Q12 기능 안내도 실제 노트/규칙/preview 기능 범위다. 특히 발열 조건과 귀환 질문은 원문 그대로 유지되며 미래/사망 사실을 만들지 않는다. 하지만 Q1/4의 쟁반 개수를 추가 사람의 답으로, Q2의 `관리자입니다`를 준 역할의 근거로, Q8 단어 사용을 정의로, Q9 일반 방송을 검진 후 처분으로, Q10 글자를 정체로, Q11 귀표 단어 사용을 두 표시 관계로 supported 판정하는 source 오류가 남는다. 최종 필터/전언·scope guard가 이를 unknown으로 낮추므로 사용자에게 그 가공된 사실을 그대로 확정하진 않는다.

부분 근거의 최종 범위는 제한적이다. Q3 수신자 질문은 일반 지시 public1만 남고 이미 있는 민석 방문 public8을 생략해 장면1 노트로 안내한다. Q9도 public1만 남아 검진 public6을 함께 보지 못한다. Q11 관계 질문은 귀표 public10만 보여주고 손목띠 public3은 빠진다. Q1/4는 쟁반 주인 미확인과 실제 쟁반 노트를, Q7은 이송 전언과 회차3 노트를, Q8은 준의 원본 용어 장면을, Q10은 트럭 글자 원본을 제시한다. 다음 경로는 실제 기능이지만 후속 대화/플레이가 새로운 유용한 답을 주는지는 이 실행으로 시험하지 않았다. “모른다” 외의 출처와 다음 행동을 제공한다는 개선과 완전한 질문 유용성 승인은 구분한다.

Custom3은 원문·단일 대상·지식 한계·비실행·명시적 대안을 보존한다. 원문의 무조건 진실/무제한 답변 실행 성공으로 계산하지 않는다. A1은 쟁반 candidate0, A2는 실제 null 생략, A3는 known-source candidate0이다. A1/A3 각각 두 줄은 reported statements, 동일 note source_key, 두 화자 기억과 현재 loop/beat에 모두 일치한다. 새로운 사건/소문 진실을 만들지 않는다. 이 trace는 in-memory production-use-case 포트 호출 증거이며 실제 사용자 playtest나 새로운 DB 내구성 시험이 아니다.

### 최종 검증·버전·종결 범위

- 코드 테스트: 독립 순수 **100 passed in 0.13s**는 source-local checkpoint에서 확인했다. 최종 변경은 두 prompt만이며 AST 평가로 진단의 문자열과 바이트 동일함을 검증했고 불필요한 순수 재실행은 하지 않았다.
- 전체 suite: **307 passed, 6.73s**는 root의 마지막 실행 보고다. reviewer는 공유 DB를 실행하지 않았다.
- interactor SHA **`6fb42a732b4def2fb24892a7e741cb4593271de4004c976ade78a51d03a2d8d9`** — 검토 종료 시 고정값과 일치.
- DTO SHA `0a7374c489dcd7042e009ddb0aa34eadc882eac0104e673853be7903792dcc3c`.
- 최종 prompt diff SHA `7218f7035fe76dc79b39f2095f969b2acfbacbe7744f894afe2bbcb3879f6076`.
- 전체 diff SHA `949605a4934b15c1dcdd4b4cd4dab25253fd20b2fd8c7bb0e26be2aab5ffbbb8`.
- changed-file list SHA `eaaf107b9688db2a70857e6a5d8e55a983023b64751bc9421a3443d44f8b5d0c`.

**BR1–7와 기존 RM2/RM3의 구체 재현 closure는 유지한다. RM1은 열림이며 최종 의미 gate를 통과하지 못했다.** 추가 수정/실험 없이 여기서 검토를 종료한다. 운영 전환 승인 없이 기존 서버를 유지하는 gate를 권고하며, 변경된 제품 계약으로 기준을 낮춰 통과시키지 않는다. 사람이 검토한 정확도·사용성·전체품질 수치는 여전히 미측정이다. reviewer는 이번 전체 작업에서 production code를 변경하거나 DB/API/network/server/권한 요청을 실행하지 않았고 보고서와 raw 복사만 작성했다.


## Gemini product-adapter connectivity checkpoint (08:05 UTC)

Root-run `adapter-20260909T080507122303Z.json`, durable `real-model-artifacts/adapter-20260909T080507122303Z.json`, SHA256 `9868f266135669dcf4e1e1720a62f2ae65cb4dc76ebb30e73a1c1c79a28c27f1`. Independent file inspection confirms the actual `GeminiLLM` probe selected `gemini-3.1-pro-preview`, explicit temperature 0, returned JSON object `{"answer":"no"}` to the closed-window/open-window contradiction control, matching its expected answer in 4.465 seconds. This confirms this single product adapter call succeeded; it is not a rerun of the existing RM1 corpus, does not prove provider-wide reliability or human accuracy, and does not close RM1. The earlier Gemini 2.5 Pro generation 404 remains a separate model-availability result. This reviewer made no live calls.


## Selected Gemini 3 Flash: product connectivity checkpoint (08:09 UTC)

Final selected CORE candidate reported by root: `gemini-3-flash-preview` (NPC remains existing Ollama Exaone; embedding remains Gemini). Independent raw-file inspection confirms product `GeminiLLM` with explicit temperature 0 returned `{"answer":"no"}`, the expected closed-window/open-window control answer, in **2.543 seconds**. This is one successful product connection/control, not the original tester1 corpus or the unresolved SPC2 control; **RM1 remains unclosed**. A separate Flash-Lite successful probe is an optional alternative, not the selected model. These files do not independently prove that runtime configuration or server restart has completed.

Durable byte-identical artifacts:

- `real-model-artifacts/adapter-20260909T080958641333Z.json` — SHA256 `e0abd198afc77f856e4da730371edf0142326c16cb2367482156d57848e1ee4a`.

- `real-model-artifacts/adapter-20260909T080832191157Z.json` — SHA256 `478cc103bc802ce92b783ac558896b56cbac4f89ecae1287110a74ec085c32b2`.

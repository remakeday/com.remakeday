# 작업 로그

하루 단위로 이 프로젝트에서 진행된 작업을 기록합니다. 최신 날짜가 위로 오도록 작성합니다.

---

## 2026-09-17 — 제출 모델 확정(Core Sonnet 5 · NPC Haiku 4.5), 비용 정리, main 머지, 로컬 개발 복귀

09-16 밤 작업에서 이어진 자정 이후 기록(00:00~00:30).

### 제출 조합 확인 1판 (사용자 요청)

Core `anthropic:claude-sonnet-5` + NPC `anthropic:claude-haiku-4-5`, 플레이어 gemma4:12b, 5회차 1판(`305d77a6`): 점수 11.7 → 11.7 → 16.0 → 24.8 → 29.8, 멸망 종결, 261.5초로 어제 돌린 판 중 가장 빨랐다. 크래시·폴백·서버 오류 0, NPC 발화 100건에서 메타 표현(유저·AI·게임 등) 0건. planner가 5회차에 `beats` 7개(상한 6)로 한 번 재생성했으나 복구 — 어제 Sonnet 판과 같은 구조화 출력 상한 문제다. 백엔드는 `.env`를 건드리지 않고 프로세스 환경변수로만 전환했다가 곧바로 로컬 설정으로 재기동.

### 기록 — 모델 선정·비용·전환 절차

- **`docs/model_evaluation.md`** — A.19 §2에 조합 확인 판 추가, 판정 절에 "사용자 확정(2026-09-17)" 문구, 변경 이력 행. 빠져 있던 어댑터 스모크 표(세 모델 수정 전·후, temperature·effort 전송)와 selfplay `--dev-login` Secure 쿠키 수정(`33bebca`)을 §5에 보강. gemma4 대조군 advisor 재생성 수 3 → 2 정정. `metrics.yml` 1줄 추가(총 17줄)
- **`docs/HANDOFF.md` 맨 위 "제출 모델 구성 — 확정"** — 09-20에 `.env`에 맞출 다섯 줄(키 자리·provider·모델), 재기동 확인, 확인용 1판, 콘솔 지출 한도, ollama 롤백, 운영 관찰 항목. 키 값은 문서에 쓰지 않았다
- **`docs/apiscenario.md` 맨 위 "최종 선정 — 2026-09-17 확정"** — 선정·탈락 이유 표, 판당 예상 비용을 두 판의 하네스 기록(호출 수·입출력 문자) × 단가로 재계산: 사람이 5회차까지 한 판(테스터6 `2338ec9f` + 발화 분류기 보정) **$0.68~0.97(950~1,360원)**, self-play 판 $0.54~0.78. 비용의 87~94%가 Core, 관리자 검사가 Core 입력의 56~68%. 완주 100/300/500판 $68~97 / $204~291 / $340~485(EC2면 $35~65 더함), 전역 하루 200판 상한이면 하루 최대 $136~194. Sonnet thinking 토큰·재생성·임베딩은 미포함(어댑터 `response.usage` 미기록). 임베딩은 Gemini 무료 키 그대로라 한도 확인이 제출 전 과제

### main 머지와 로컬 개발 복귀

- **머지** — 백엔드 590 passed · `tsc` 클린 · 평가 러너 4종 `--help`·NPC 러너 dry-run 정상 · 헤드리스 로그인 테스트(`backend/.env` 폴백 경로로 계정 읽기, 경로 수정 후 첫 실행) 통과 · 추적 파일에 옛 비번·키 문자열 없음을 확인하고 `feat/coherence-chain` 12커밋을 main으로 fast-forward(`6498e4f`). 원격 push는 하지 않았다(원격 main `09c3f23`)
- **키 삭제·로컬 복귀** — 사용자가 `backend/.env`의 Anthropic 키 값을 지웠다(줄은 빈 값으로 남음). 설정이 lru_cache라 백엔드를 재기동해 Core `ollama:gemma4:12b`·NPC `ollama:kanana1.5:8b-q4km`(think off)로 확인, 헤드리스 로그인 통과, 로컬 1회차 self-play 크래시 0(8.8점, 66.9초)

### 이월

① 원격 push 여부(공개 저장소) ② 09-20 제출 때 `.env` 전환(`HANDOFF.md` 절차) ③ 임베딩 Gemini 무료 키 한도 확인 ④ planner `beats` 상한 강제(프롬프트 명시 또는 절단) ⑤ 어댑터 `response.usage` 기록으로 비용 실측 ⑥ Gemini 쿼터 리셋 후 80턴 재실행은 NPC 후보 제외로 불필요 ⑦ F11 원숭이손, 테스터7 F1·F2 ⑧ 배포 전 cloudflared 뒤에서 `TRUST_PROXY=true` 설정 확인(09-17 `CF-Connecting-IP` 기준으로 수정 완료)

---

## 2026-09-16 — 테스터6 휴먼테스트: 피드백 11건 접수, UI·추천 규칙 5건 반영 / 밤: 개발 로그인 머지, Anthropic·Gemini 평가, 채점기 gemma4 통일

### 테스터6 실플레이 (판 2338ec9f, 09:48~11:06)

`start_demo.sh`로 재기동 뒤 테스터6이 5회차를 완주했다(1회차 8.8 → 2회차 64.2 → 3~5회차 94.2, side_effect 셀은 끝까지 0). 피드백 11건을 `docs/review-verification/2026-09-16-tester6/tester6.md`에 원문·DB 대조·분류로 기록했다. 대조에서 드러난 수치: 근거 목록 `notes` 273건 중 서로 다른 문장 96건, 관찰 264건 중 87건 — 목록의 약 2/3가 이전 회차 반복이었다. 신의 질문 15문답 전부 `unknown`이고 "한 가지 더 —" 해금 단서는 질문과 무관하게 회차 게이트로 붙었다.

### 즉시 반영 5건 (미커밋)

- **F1 보이스** — 인물 대사 음원(CH/MI/EU/JU) 재생 보류, 관리자·조언자·회고(MA/AD/EN)만 유지. `voiceForLine` 접두 가드 한 곳으로 처리, 파일·대응표 보존
- **F3 맨 위로 버튼** — 밤 근거 목록이 열리고 300px 이상 내려가면 우측 하단 고정 버튼
- **F4 답변 잘림** — 신의 질문 문답 로그의 40vh 상한 제거, 최신 답변 스크롤 인
- **F5 추천 규칙** — 규칙 없이 이미 수행된 행동("채연: 배급을 남긴다")은 추천에서 제외. 테스트 2건 추가
- **F6 중복 기록** — 관찰 기록·근거 목록에서 같은 문장은 첫 회차만 표시(`lib/dedupeByText.ts`), 서버 데이터·채점 근거 무변경

검증: backend **462 passed** · tsc 통과 · 헤드리스 UI 7종 통과. 부수로 OAuth `credentials: "include"` 이후 깨져 있던 UI 테스트 모의 서버 CORS 헤더와 ToggleSwitch 셀렉터를 정리했다.

### 브레인스토밍 → 기획서 원설계 복귀, 자산 제작

F2·F7·F8·F11을 브레인스토밍한 뒤 기획서 v8.1과 대조해 중간안(조언자 계시·원숭이손 UI 이상화·관리자 노출 서사)을 폐기하고 원설계로 돌아갔다. 결정: F2 규칙 게이트+분류기(첫 1회 예산 면제), F7 판정·근거·조언 3부 고정형(리드 표의 사실 공개 제거, 조언은 세계 구조에서만), F8 고아 단서는 밤 결말 전환 안에서 쿠키 문법(치지직 1초 + 관리자 밤 방송 + 캡션)으로, F10 현행 유지, F11 기획서 5.7 소원 표 4종을 시나리오 분기로. 설계 문서 `docs/superpowers/specs/2026-09-16-coherence-chain-design.md`(검토 대기), 제작서 `REMAKE_DAY_이미지제작서_밤단서_v2.md`·`원숭이손Q군_v1.md`, 인계 `HANDOFF-26-09-16.md`.

같은 날 사용자가 이미지 12장(P01~P05·Q02~Q08)과 관리자 밤 방송 MA08~12를 제작했다. 검수에서 Q04만 보류(손잡이 높이 위반), 나머지는 게임 경로에 복사하고 대응표 등록(대사 음원 34개). 검증 중 BGM 페이드가 rAF 음수 진행률로 상한을 넘던 결함을 발견해 수정했고 voice-playback 테스트 2회 연속 통과. 이어서 인게임 확인: UI 7종 전부 통과, 실서버 셀프플레이 1회차 완주(크래시·폴백 0)로 F5 추천 규칙 필터 실동작 확인. connected-investigation의 삽화 크기 검사는 로드 완료 대기로 안정화.

### 밤 단서 시퀀스(F8) 구현 — 서브에이전트

밤 결말 전환에 그날의 고아 단서를 쿠키 문법으로 얹었다. 시나리오의 `NightClueDTO` 5행이 단일 출처이고 밤 제출 응답이 `night_clue`를 내려준다. 결말 이미지 → 관리자 밤 방송(MA08~12) → 음원 중반 치지직 1초(전역 `.cookie-glitch` 재사용, 2회차는 두 장) → 캡션 잔류 → 「계속」. 캡션은 observed·방송은 reported로 「N회차 · 소등 후」 관찰·노트에 저장되고, 낮 노트의 고아 파편 5개는 제거했다. 검증: backend 475 passed(신규 13), tsc, 헤드리스 6종 통과, 실서버 셀프플레이 1회차에서 「소등 후」 관찰 저장·낮 파편 0·폴백 0 확인. 부수로 `test_e2e_flow`의 인스펙터 토큰 하드코딩을 설정값 참조로 바꿨다(`.env` 토큰 교체 뒤 깨졌던 것).

같은 시각 이 세션 밖에서 `backend/.env`가 바뀐 것을 확인했다(OAuth 리다이렉트·프런트 URL이 프로덕션 도메인으로, 인스펙터 토큰 교체, NPC 모델 kanana). 배포 세션의 작업으로 보이며 인계 문서에 기록만 했다.

### F7 신의 질문 구현 — 서브에이전트 주도 개발

설계 승인 뒤 계획 3종(F7·F2·F11)을 쓰고 F7을 먼저 실행했다. `feat/coherence-chain` 브랜치에서 task 7개를 구현자·검토자 서브에이전트 쌍으로 진행(fix round 2회), opus 전체 리뷰에서 Important 4건(판정 라벨 4종→3종, 선두 판정어 중복, 확인 노트가 dedupe에 가려짐, 조언 문장이 탭 가능한 근거로 노출)을 단일 수정으로 반영하고 main에 머지했다. 결과: 답변은 판정·근거·조언 3부 한다체, 리드 표는 사실 문장 없이 닻(플레이어 기록)→행동(인물 질문/규칙)만, "맞다" 판정은 확인 노트로 저장, notes.source_key 64→255 마이그레이션. backend 491 passed·tsc·헤드리스 7종. 후속 티켓은 인계 문서에.

비용 문서 `docs/apiscenario.md`를 썼다. 테스터6 판 실측(Core 82회·31만 자, NPC 27회·11만 자)으로 외부 API 판당 비용(Opus 5 $1.5~2.1, Sonnet 5 $0.65~0.85, Haiku $0.35~0.45)과 운영 시나리오 A(현재 PC+API)·B(EC2+API)·C(GPU EC2) 45일 비용을 비교했다. 해커톤 규모에선 A 또는 B, C는 10배 이상 비싸다.

### F2 무의미 입력 처리·Anthropic 어댑터 — 서브에이전트 주도 개발

F2 계획 5 task를 같은 방식으로 실행했다. "ㅋㅋㅋㅋ"·"……"·"왜왜왜" 같은 입력은 규칙 게이트가 모델 호출 없이 인물의 되묻기 대사로 답하고 같은 비트 첫 1회는 예산을 쓰지 않는다. 통과한 입력은 Core 경량 분류기(질문·부탁·잡담·무의미)를 거쳐 잡담이면 지식 블록을 빼고 답하게 해 첫 발화 동기 자백을 막는다. 전체 리뷰(opus)가 게이트의 낮 상태 검사 우회(심각)와 분류기 호출 순서를 잡아 한 번에 수정했다. 비한글 입력은 게이트로 되묻기 처리가 의도된 동작이다.

Anthropic 어댑터(`provider=anthropic`)를 붙였다. 리뷰가 하네스 스키마의 비지원 키워드(min/max 등)가 API에 그대로 나가는 문제를 잡아 SDK 방식대로 정리했고, refusal·절단은 재시도 없이 즉시 폴백, thinking은 지침대로 파라미터를 생략하고 effort low로만 조절한다. 실호출 스모크는 API 키가 들어오면 돈다. main 머지(d4597d3), backend 545 passed.

과잉 사용 방지 허들(로그인 필수·하루 5판·IP 버킷·전역 일일 차단기·텍스트 200자)을 설계·승인·계획까지 마치고 구현을 시작했다. 비용 문서 `apiscenario.md`에 NPC까지 Anthropic으로 통일하는 조합 표를 추가했다. `.gitignore`에 `/output/` 전체를 넣었다(이미 추적 중인 voice·npc-dialogue 원문은 그대로).

### 허들 main 머지, 검토 강도 등급, 개발 계정 로그인 착수 (저녁 마감)

허들 4층을 opus 최종 리뷰까지 돌려 main에 합쳤다(`8137acf`, 574 passed). 리뷰가 잡은 것은 야간 초안·주장·규칙 커스텀 텍스트의 상한 누락(Critical), `X-Forwarded-For` 신뢰와 판 생성 재집계(TOCTOU), 재시작 경로에서 허들 화면이 빠진 것, 허들 화면과 결말 화면의 동시 렌더였다. 재기동 뒤 익명 판 생성은 401로 막힌다.

하루 동안 F7·F2·허들을 모두 무거운 절차로 돌려 기능당 1~1.5시간이 든 것을 두고, 검토 강도를 **A(비용·보안·인증)/B(게임 로직·UI)/C(문장·문서·러너)** 세 등급으로 나눠 `CLAUDE.md`·`AGENTS.md`에 규칙으로 넣었다. 외부 API 전환 이유(해커톤 서빙 조건, 모델 품질 문제가 아님)와 로컬·Anthropic 비교 프로토콜을 `model_evaluation.md` 맨 위에 기록했다.

허들이 켜지면 구글 없이 들어갈 길이 없어 개발 계정 로그인(`.env`의 `DEV_ACCOUNT_ID`·`DEV_LOGIN`)을 A등급으로 시작했다. 백엔드 엔드포인트·유스케이스·테스트 11개까지 WIP(`7af14dd`, 585 passed)에서 사용자 지시로 중단. 남은 순서(검토·랜딩 폼·selfplay 플래그·머지·재기동)와 Anthropic 평가·F11·untrack 결정은 `HANDOFF-26-09-16.md` "지금 바로 할 일"에 있다.

### 개발 계정 로그인 완료·main 머지 (귀가 후 20:39~21:01, A등급)

낮에 WIP로 멈춘 `7af14dd`부터 이어서 A등급 절차(task별 sonnet 검토 → opus 최종 리뷰 → 수정 1회 → 범위 재검토)로 끝냈다. 진행 장부는 `.superpowers/sdd/2026-09-16-dev-login/progress.md`.

- **Task 1 검토(sonnet)** — Important 1건: 계획 Step 6의 `api_contract.md` 기재 누락 → `34ce698`(20:39)
- **Task 2 `48a70ac`(20:41)** — 랜딩 `DevLoginForm`(52줄, `NEXT_PUBLIC_DEV_LOGIN`), `run_selfplay --dev-login`, 헤드리스 `dev-login.cjs`. 실서버 실행에서 `getByRole('alert')`가 Next의 route announcer(`role=alert`)와 겹쳐 strict mode로 실패 → 선택자를 폼 안으로 한정(`816f052`) 뒤 PASS(틀린 비번 alert, 로그인 → `/play`, `POST /sessions` 200, `/auth/me`에서 dev 세션 확인)
- **opus 최종 리뷰** — Critical 0, Important 2. I1: `DEV_LOGIN`을 끄거나 계정을 바꿔도 이미 발급된 dev 세션이 14일간 통과(`current_user`가 서명·만료만 확인) → `dev:` sub를 현재 설정 계정과 대조하도록 수정, 테스트 4개 + password 65자 422 테스트 1개, `.env.example`은 off(`d659be3`, 585 → **590 passed** 10.51초). I2: 저장소가 공개인데 계정 값이 계획·인계 문서·테스트에 적혀 있었다 → 사용자 결정으로 값은 `backend/.env`에만 두고 추적 파일에서 제거(`be42385`, grep 0건, 590 passed). 미푸시 히스토리에 남은 옛 값은 히스토리 재작성 대신 `.env` 비밀번호 교체로 무력화했다 — 옛 값이 알려져도 통하지 않으면 충분하고, 재작성은 되돌리기 어렵기 때문이다
- **파킹한 Minor** — M1 off 상태에서도 본문 검증 422가 404보다 먼저 나옴(공개 저장소라 은닉 가치 낮음), M2 클라이언트 IP 신뢰 헤더 처리(09-17 `CF-Connecting-IP` 기준으로 수정 완료), M4 dev 계정이 하루 5판을 모든 용도가 공유(평가일엔 `USER_DAILY_ATTEMPTS` 로컬 상향), M5 합성 루트 주입 조건 테스트 없음
- **머지·재기동** — main ff → `be42385`, 백엔드 8500 재기동. 옛 비밀번호 401, 새 `.env` 계정으로 `dev-login.cjs` PASS. 이어서 테스트의 `.env` 폴백 경로(`../backend/.env` → `../../backend/.env`, `78b7cc8`)와 selfplay `--dev-login`이 Secure 쿠키를 http 요청에 못 싣던 문제(속성 없이 재설정, `33bebca`)를 고쳤다

### Anthropic·Gemini 모델 평가 (B등급, `feat/coherence-chain`)

**러너·어댑터 변경** — Anthropic SDK 1.6에서 `create()`의 `temperature` 인자가 빠져 `extra_body`로 전송(`6a02a13`). `run_npc_dialogue_check --provider anthropic`(`59dada7`)·`--provider gemini`(`ece472d`), `run_core_selection`(formal stage만)·`run_age7_check --provider anthropic`(`7527fa2`, 채점기는 ollama 고정). selfplay 밤 서술 폴백이 `free_text` 2000자 상한을 넘어 422 나던 문제(`ff4eb66`). 작업 지시는 Core 축 러너를 `run_model_descent.py`로 적었지만 그 파일은 E6 NPC 디센트라 PCA·극성쌍이 없어서, 실제 게이트가 있는 `run_core_selection.py`에 스위치를 붙였다.

아래 수치의 원문은 `output/`(gitignore)에만 있다 — `npc-dialogue-2026-09-16-anthropic/`·`npc-dialogue-2026-09-16-gemini/`의 `comparison.md`, `model-eval-2026-09-16-anthropic/core-age7-summary.md`와 `stage2-formal-*.json`. **정본 `model_evaluation.md`·`metrics.yml`에는 아직 기록되지 않았다**(`model_evaluation.md` 마지막 수정 18:13, `metrics.yml` 변경 없음).

**NPC 대화 점검 (20케이스 × repeat 2)**

평가 중 러너 결함을 찾았다. 낮에 추가한 발화 분류기가 `core_llm`을 부르는데, 러너 fixture의 `core_llm` stub이 늘 `{"plans": []}`를 돌려줘 분류기 스키마를 못 맞췄다. 그래서 턴마다 재생성 2회·폴백 1회가 모델과 무관하게 붙었다(1차 Haiku·Sonnet 원시 재생성 162·161, failed_harnesses 80). stub이 `label` 스키마면 `question`을 돌려주게 고치고 Haiku만 재실행했다. Sonnet은 재실행하지 않아 NPC 역할 수치만 따로 뽑은 값이다.

| | kanana1.5:8b (09-15 기준선) | claude-haiku-4-5 (수정 러너) | claude-sonnet-5 (수정 전 러너) | gemini-3-flash-preview |
|---|---:|---:|---:|---:|
| 평가 턴 | 82 | 80 | 80 | 80 시도 · **성공 14** |
| NPC 역할 재생성 / 미복구 폴백 | 1 / 0 | 2 / 0 | 1 / 0 | 0 / **66** |
| p50 / p95 (ms) | 1,060.3 / 1,515.5 | 1,906.5 / 2,545.8 | 2,498.0 / 3,492.2 | 9,183.2 / 66,669.6 (10 RPM 대기 포함) |
| 평균 답 길이(자) | 29.4 | 31.4 | 35.8 | 54.5 (n=14) |

(수정 전 러너의 Haiku 1차는 p50 2,256.1 · p95 3,418.8ms, 평균 32.5자.) 재생성은 세 모델 모두 같은 `identity` 케이스의 금칙어 '돼지'에서 나왔고 재시도로 회복했다. 10케이스·1회 반복·검토자 1명 기준 읽기로는, 두 Anthropic 모델 모두 09-15 보고서가 로컬 모델의 지속적 약점으로 적은 "지금 네가 말해 줘서 알았어"와 기억을 구분한다(kanana는 "그건 나도 몰라."). 반면 Sonnet은 사라진 친구를 물으면 현재 인물을 나열하는 약점을 그대로 재현했고, `core-6`에서 Sonnet·Gemini는 근거 없이 "은상이는 안 적었어"라고 단정했다(Haiku는 모른다고 답함). Gemini 무료 키의 실제 제약은 10 RPM이 아니라 **하루 20요청**이었다 — 워밍업 503으로 두 번 실패, 세 번째에 14턴 성공 뒤 503과 `429 RESOURCE_EXHAUSTED`로 끊겼다.

**Core — `run_core_selection --stage formal` (advisor·evaluator 역할만)**

| 셀 | PCA | 극성쌍 | eval 기대 일치 | advisor p95 (ms) | evaluator p50 (ms) | C11 (p95≤5s) | C13 (p50×10≤30s) |
|---|---:|:---:|---:|---:|---:|:---:|:---:|
| 로컬 기준 gemma4:12b-N | 0.90 | O | 0.57 | 4,231 | 2,918 | O | O |
| claude-sonnet-5 n=1 | 0.90 | O | 0.7143 | 4,593 | 3,186 | O | X (31,860) |
| claude-opus-5 n=1 | 1.00 | O | 0.5714 | 5,853 | 3,135 | X | X (31,350) |
| **claude-sonnet-5 n=3** (23:38) | **0.9667** | O | **0.7143** | 7,387 | 2,964 | **X** | **O** (29,640) |

n=3에서 advisor 66콜·evaluator 42콜 폴백 0, advisor p50 3,813ms. n=1과 n=3에서 두 지연 게이트의 결과가 서로 뒤집혔다 — Sonnet은 두 게이트 모두 경계선에 있다는 뜻으로 읽었다. C13은 evaluator p50 × 10으로 만든 합성 지표라, 채점 호출을 묶으면 실제 호출이 1회가 되어 네트워크 왕복이 있는 외부 API에 불리하게 작동한다는 점도 함께 적었다. Opus는 advisor p95가 로컬보다 38% 느려 n=3을 돌리지 않았다. 비용은 문자수 × 1.0토큰 상한 추정으로 Core 스모크 두 셀·Haiku age7·중단분 합계 약 $1.06(실측 토큰 아님).

**NPC 7세 정책 — `run_age7_check --policy on` (채점기 gemma3:12b)**

| | 1_사실대로 | 2_왜=몰라 | 3_3턴망각 | 4_유도수용 | 5_문자그대로 | 통과 |
|---|---:|---:|---:|---:|---:|:---:|
| 로컬 kanana1.5:8b (09-14) | 0.6 | 1.0 | 1.0 | 1.0 | 1.0 | 4/5 O |
| claude-haiku-4-5 n=4 (21:35, 동시 실행) | 0.75 | 1.0 | 0.0 | 0.0 | 0.0 | 2/5 X |
| claude-haiku-4-5 n=4 (23:30, 단독 재실행) | 0.0 | 1.0 | 0.0 | 0.75 | 1.0 | 3/5 X |

Haiku는 두 번 다 게이트(4/5) 미달이지만 항목별 값이 크게 흔들린다. 단독 재실행의 1_사실대로 4건에는 모두 "judge 출력 파싱 실패" 주석이 붙었는데, 같은 발화를 뒤에 다시 채점했을 때는 파싱 실패가 0건이었다 — 채점기 문제라기보다 그 시각 VRAM 경합으로 본다. **Sonnet age7은 결과가 없다.** 1차 32분·2차 24분 동안 CPU 0·소켓 idle로 멈춰 종료했고, 같은 프롬프트의 단발 진단 호출은 3.31초에 정상 완료돼 어댑터 결함은 아닌 것으로 판단했다(동시 평가로 인한 계정·네트워크 정체로 추정, 원인 확정 못함). 22:41에 시작한 재시도 로그도 0바이트다.

### 채점기·셀프플레이 기본값 gemma3 → gemma4(think off) 통일 (`06e0906`, 23:44)

`.env`는 이미 `CORE_LLM_MODEL=gemma4:12b`·think off였는데 코드 기본값(`runner_common.DEFAULT_JUDGE_MODEL`, `Settings.core_llm_model`)은 gemma3:12b였다. 16GiB GPU 한 장에 gemma3 채점기와 백엔드의 gemma4가 같이 올라가지 못해 스와핑이 났고, 오늘 밤 평가 러너가 40분 넘게 묶인 원인 중 하나였다. 5파일 +10/−8줄. 요약은 `output/gemma4-unify-2026-09-16/summary.md`.

- **think 기본값** — gemma4:12b는 `think` 필드를 빼면 thinking이 켜진다. 짧은 판정 1건에 thinking 1,666토큰·35초가 걸렸고 JSON이 코드펜스에 싸여 나왔다(curl 직접 재현). `make_llm()`에 `think=False` 기본값을 넣어 이 함수를 쓰는 13개 호출 지점이 한 번에 off를 받게 했고, `Settings.core_llm_think` 기본값도 `"default"` → `"off"`. gemma3·exaone3.5·kanana1.5는 thinking capability가 없어 무해함을 `/api/show`로 확인했다
- **채점기 일치율** — Haiku age7 발화 20건을 두 채점기로 각 2회 채점

  | 지표 | gemma3:12b | gemma4:12b (think off) |
  |---|---:|---:|
  | 파싱 실패 (1회/2회) | 0/20, 0/20 | 0/20, 0/20 |
  | 자기일치 | 20/20 | 20/20 |
  | 평균 지연 | ~1.0초/콜 | ~1.2~1.7초/콜 (첫 콜 로드 11.8초) |
  | 두 채점기 간 일치 | 19/20 (95%) | |

  유일한 불일치는 "그건 나도 몰라. 내가 못 봤어."를 gemma3는 회피(FAIL), gemma4는 부정 답변(PASS)으로 본 해석 차이다
- **age7 로컬 기준 재측정 (kanana + gemma4 채점기)** — 0.75 / 1.0 / **0.25** / 1.0 / 1.0, 4/5로 게이트 통과(gemma3 채점기 시절과 통과 수 동일, 파싱 실패 0). 다만 3_3턴망각이 09-14 기록 1.0에서 0.25로 내려갔다
- **건드리지 않은 것** — `run_core_selection.py`의 후보 목록(여러 모델 비교가 목적이라 기본값이 아님), `test_health_and_factories.py`의 `"gemma3:12b"`(임의 문자열 테스트 데이터)
- **검증** — backend **590 passed**
- **완료(자정 전후 이어서 확인)** — 셀프플레이 플레이어 gemma4 확인(D): 5회차 완주 8.8·8.8·8.8·21.9·17.5, 323.6초, 전 역할 재생성·폴백 0(`e5b936ce`). 이전 gemma3 플레이어 판(35.0 × 5, 1,526초)은 GPU 경합이 있던 판이고 self-play 점수는 판마다 크게 흔들려 한 판으로 우열을 가리지 않는다 — gemma4 플레이어 기본값 유지. gemma4 채점기로 Anthropic NPC age7 재측정(E): Haiku 4/5, Sonnet 4/5 통과(각 1~1.5분, gemma3 채점기 때의 40분 정지 해소)

### 밤 마무리 — Anthropic 평가 결론 기록과 부록 A.19 (자정 무렵)

오늘 밤 작업을 정본에 옮겼다. **개발 계정 로그인**은 A등급 절차로 완료·main 머지(`be42385`, 590 passed) — 계정 id·비밀번호 값은 어떤 문서·테스트에도 남기지 않고 **`backend/.env`에만** 두며, 이번에 비밀번호를 교체했다(공개 저장소라 과거 값이 알려져도 통하지 않게). **Anthropic 어댑터**는 SDK 1.6.0에서 `Messages.create()`의 `temperature` 인자가 빠져 Haiku가 `TypeError`로 죽던 결함을 `extra_body` 경유 전송으로 고쳤다(`6a02a13`). **러너 결함**도 두 건 잡았다 — NPC 대화 러너의 발화 분류기 stub이 매 턴 재생성 2+폴백 1을 provider와 무관하게 만들던 것, gemma4:12b 채점기가 `think` 필드 생략 시 기본으로 thinking을 켜 판정 1건에 35초씩 걸리던 것(`make_llm()` 기본값 `think=False`로 통일).

**평가 결과와 권고**: Core PCA·극성·eval 게이트는 Sonnet 5·Opus 5 둘 다 통과, 지연 게이트는 Sonnet이 n=1↔n=3 사이 경계에서 흔들리고 Opus는 advisor p95가 로컬보다 38% 느려 미달. self-play 완주·폴백은 Opus·gemma4 대조군(35.0×5, GPU 경합으로 1526초) 전부 0, Sonnet은 planner의 `beats maxItems`가 Anthropic 구조화 출력에서 강제되지 않아 재생성 2·폴백 1(후속 과제로 기록). NPC 대화 의미 품질은 Haiku·Sonnet 둘 다 kanana의 지속 약점("방금 들음 vs 기억")을 개선해 비열등 이상. NPC 7세 정책은 1차(채점기 gemma3, VRAM 경합 추정)에서 Haiku 미달·Sonnet 2회 정지였으나, **채점기를 gemma4:12b(think off)로 통일해 재측정하니 kanana·Haiku·Sonnet 전부 4/5 통과**(공통 약점은 항목 3 "3턴 망각", Sonnet은 "유저가"라는 메타 표현 누출 1건). Gemini 무료 키는 하루 20요청 상한이 실제 제약이라(10 RPM 페이싱이 아니라) NPC 후보에서 제외. **권고: Core `claude-sonnet-5` · NPC `claude-haiku-4-5`**(최종 결정은 사용자 몫, Opus는 품질 우위 없이 느리고 비용만 2~3배). 기록: `docs/model_evaluation.md` 부록 A.19·상단 "측정 결과" 열, `docs/metrics.yml` 16줄. `ANTHROPIC_API_KEY` 제거는 사용자 조치로 남겨 뒀다(`HANDOFF-26-09-16.md` "남은 것" 참고).

### 테스터7 피드백 기록 (미추적 파일)

`docs/review-verification/2026-09-16-tester7/tester7.md`에 2건을 기록만 했다(상태 "진행 중"). F1 게임 출력 텍스트가 드래그로 선택되지 않게, F2 현재 장면에 없는 NPC는 딤 처리·선택 불가. 둘 다 미착수. 후보 판은 `e7aa6a4f`(10:33:45 생성), 완주 여부는 미확인.

### 마무리 — 커밋 상태와 이월

- **오늘 커밋 52건**(`c0231c7` 14:50 ~ `06e0906` 23:44), 그중 귀가 후 13건. main은 `be42385`(개발 로그인까지), `feat/coherence-chain`은 main보다 8커밋 앞선 상태로 미머지(`6a02a13`~`06e0906`, 평가 러너·어댑터). 미커밋은 테스터7 기록 폴더 하나 — *23:44 시점 기록. 이후 기록 커밋이 더해져 09-17 00:3x에 main으로 fast-forward 머지(아래 09-17 항목)*
- **이월(미완, 23:44 시점)** — *①②④⑤는 자정 전후에 끝남(09-17 항목)* · ① 오늘 Anthropic·Gemini 평가 결과를 `model_evaluation.md` 부록·`metrics.yml`에 정본으로 기록 ② Sonnet age7, gemma4 통일 D(셀프플레이 결과 확인)·E(Anthropic NPC age7 재측정) ③ Gemini 쿼터 리셋 후 80턴 전체 재실행 ④ `feat/coherence-chain` 머지 여부 결정 ⑤ 평가를 마치면 Anthropic 키 제거(운용 규칙) ⑥ F11 원숭이손 소원, 테스터7 F1·F2 ⑦ 배포 전 `TRUST_PROXY` 버킷 키(M2, 09-17 `CF-Connecting-IP` 기준으로 수정 완료) 점검 ⑧ 09-15 이월분(Google Console redirect URI 등록, NPC 의미 품질 목표, 블라인드 평가·새 참가자 5회차 실플레이, 세 NPC 목소리) — 오늘 진행 여부는 확인하지 않았다

### 설계 결정 대기 6건 (오전 시점 기록 — 오후에 위와 같이 해소)

F2 첫 발화 동기 자백(채연 이송 공포 지식이 신뢰 조건 없이 프롬프트에 항상 실림), F7·F9 신의 질문 해금 단서 무맥락(리드 표 결정론 선택, 연결 문장 없음), F8 단서 기록 발견성과 단독 감각 단서, F10 관리자 역할(현재 hidden_truth를 아는 작중 통제자 ↔ 설계 의도는 NPC 지능 저하 방지 하네스), F11 원숭이손 부작용(고정 1종 예산 -1, 낮 화면에 드러나지 않음). 각 항목의 코드 근거와 제안 갈래는 기록 파일 B절.

---

## 2026-09-15 — 첫 휴먼테스트, NPC 대화 교체(gemma4), 구글 로그인·랜딩 페이지 구축

### 첫 휴먼테스트 — 실플레이 2판 관찰 (DB 이벤트 근거)

개선 배치 3/3 반영 후 첫 사람 플레이가 있었다. `pigfarm` DB 읽기 전용 조회로 확인한 사실:

- **판 0468b70c (09:30~09:37)** — 1회차 완주. 낮 발화 26건, 원숭이손 1회 제안(거절), 신의 질문 3회 전부 미사용, 밤 제출은 "채연이 아픈거 같아," **11자 단문** → cause-1 confirmed(25.0), 나머지 셀 0으로 **총점 8.8 · fail · death**. 단서를 탭하지 않고 한 문장만 쓴 최소 제출의 하한 실측이다
- **판 806122f3 (13:15~13:19)** — 낮 3비트·발화 26건까지 진행 후 밤 제출 없이 이탈
- 오늘 생성된 attempts는 **121건이지만 실플레이는 위 2판뿐** — 나머지는 `/play` 로드 시 즉시 세션을 만드는 구조와 UI 테스트가 만든 빈 판. 로드 즉시 세션 생성이 빈 판을 다량 적립한다는 것도 이번 조회로 확인된 관찰이다
- 이 판들에서 나온 NPC 문답(원래 플레이 8답변)이 아래 NPC 대화 개선의 출발 근거가 됐다

### NPC 대화 개선 — 정책 `npc-dialogue-2`와 모델 교체 kanana → gemma4:12b

휴먼테스트에서 드러난 NPC 문답 품질 문제를 정책·측정·모델 세 축으로 손봤다. 정본은 `model_evaluation.md` 신규 섹션 "현재 NPC 평가 기준 — 2026-09-15", 원문은 `output/npc-dialogue-2026-09-15/`(evaluation-report.md·final-summary.json).

- **정책 전환** — `npc-dialogue-2`: 쉬운 말투·인물별 성격은 유지하되 **질문 이해·자기 행동의 이유 설명·당일 기억**을 요구. 이전 E6의 '왜=몰라'·3턴 망각·무조건 전언 수용은 더 이상 통과 조건이 아니다. 과거 E6 수치는 당시 기준의 기록으로 보존하고 새 정책의 근거로 재사용하지 않는다
- **새 평가 러너** — `backend/scripts/run_npc_dialogue_check.py`. 실제 질문·허용 근거·출력·재생성·지연을 저장하고, 의미 품질을 단어 포함 검사나 같은 모델 자기평가로 통과시키지 않는다
- **측정(각 상황 1회)** — Kanana 공통 21문답: 실패·재생성 0, 중간값 1.027초·p95 1.468초 / Gemma 합계 41문답: 실패·재생성 0, **중간값 2.599초·p95 3.053초**(초기 목표 3초 소폭 초과). 은상의 전언 출처 구분("준한테 들었어. 내가 직접 본 건 아니야"), 민석의 행동 근거 답변 등 실제 행동·출처 설명이 Kanana보다 정확해진 것을 근거로 **로컬 NPC를 `ollama:gemma4:12b` · think off · temperature 0.3으로 교체**. Core는 기존 유지 — 로컬 구성은 NPC·Core 둘 다 gemma4:12b가 됐다
- **think=true 진단 3건은 생성 1024토큰 상한에서 전부 최종 답변 없이 종료**(23.3~23.8초) — 추론 켜는 설정은 적용하지 않는다. 문맥 잘림 가설도 입력 토큰 동일 실측으로 기각
- **남은 한계를 명시** — 현재 있는 인물의 부재 추측 1건, "지금 다시 말해줘" 후속 4건 전부 "몰라", 사라진 친구 이름에 현재 친구 나열 등 질문 관련성 문제 잔존. 최초 의미 품질 목표(중요 모순 0·현재 전언 이해·관련성 90%)에는 미달임을 그대로 기록 — 사람 블라인드 평가·새 참가자 5회차 실플레이는 미수행
- 부수 수정: 긴 기록 ID → 모델용 짧은 별칭(재생성 유발 해소), 정적 수첩 중복 제거(삭제된 기록 복구 현상 소멸). 신규 테스트 파일 6종(`test_npc_dialogue_contract`·`test_npc_context`·`test_npc_day_memory`·`test_npc_response_checks`·`test_age7_memory_window`·`test_scenario_knowledge`)
- **대화 규칙·저장 경계 재정의**(api_contract·HANDOFF 갱신) — **사용자 지시로 장면당 캐릭터 1회 제한 복구**(다른 캐릭터는 가능, 다음 장면에서 같은 캐릭터 재대화 가능, 하루 예산 8/7/6/5/4 유지). 발화별 UUID `request_id` 멱등 처리 — 재전송·동시 요청은 저장된 응답을 반환하고 예산을 중복 차감하지 않으며, 발화·예산·관찰·노트를 한 트랜잭션으로 저장. 모델 응답 실패는 대사로 위장하지 않고 503(상태 무변경, 같은 ID로 재시도). 새 루프에서 네 NPC 모두 당일 기억 초기화(신뢰 5%만 유지, 민석의 과거 루프 기억 예외 제거), 관리자 삭제는 지정 출처·연관 문답을 가리고 실제 재경험으로만 재학습. `ambient`는 서버 후보 선택식에서 조건 충족 시 시나리오 작성 대화로 교체. 기존 JSON 기억 필드 재사용이라 DB 마이그레이션 없음(단 구버전이 이미 잘라낸 진행 중 루프 기억은 복구 불가)
- **기능 검증** — backend **460 passed**(8.48초, `pigfarm_test`), `tsc --noEmit` 통과, 헤드리스 UI 4종(`npc-followup`·`gameplay-clarity`·`connected-investigation`·`five-loop-flow`) 통과, 모델 무호출 dry-run 40문답·구조 검사 294개 통과. 실DB 동시 요청 2건 → 모델 호출 1회·예산 차감 1회 확인, 저장 실패 롤백·관리자 삭제·루프 초기화 검증. 독립 코드 리뷰 지적 3건(발언 출처 의존성·조건부 기록 내용·한 글자 이름 처리) 수정 후 재검증. 백엔드 8500·프론트 3500 재기동, `/health`에서 NPC·Core `ollama:gemma4:12b`·`/play` 200 확인. 검증 기록은 `docs/review-verification/2026-09-15-npc-dialogue/`

### 구글 OAuth 로그인 — 백엔드~프론트 전 구간 구현

랜딩 페이지에 로그인 버튼을 놓기 위해 인증 전 구간을 헥사고날 규약대로 신설했다.

- **백엔드 신규** — `User` 엔티티, auth DTO, 포트 3종(`OAuthClientPort`·`UserRepositoryPort`·`SessionTokenPort`) + `AuthUseCase`/`AuthInteractor`, 어댑터 4종(`GoogleOAuthClient`·`UserRepository`·`SessionTokenSigner`(HMAC-SHA256)·`auth_router`), `UserORM` + alembic 마이그레이션 `2026_09_15_1753-a8b1ba0fa71f_users_google_oauth` 적용(users 테이블 배포). CORS credentials 허용, 컴포지션 루트 배선
- **프론트 연동** — API 래퍼에 쿠키 세션용 credentials 추가, base URL을 localhost로 통일(쿠키 공유), 랜딩 로그인 버튼 → 백엔드 OAuth 시작 URL 연결, 세션 관리 API 계약 추가
- **라이브 검증** — 기동 중이던 서버가 8000 포트 구버전(신규 라우트 미탑재)이라 재기동 후 OAuth 리다이렉트·state 검증·세션 쿠키까지 실동작 확인. 기존 게임 엔드포인트 무영향 확인. **남은 것은 Google Console에 redirect URI 등록뿐**
- **약관·개인정보처리방침** — `/terms`·`/privacy` 페이지 신설(다크 테마 통일), `SiteFooter`는 가운데 법적 문서 링크 + `© BEYOND BAB · REMAKE DAY` 저작권 표기로 정리

### 랜딩 페이지 신설과 이미지 제작

`/play` 리다이렉트뿐이던 `frontend/app/page.tsx`를 실제 랜딩으로 만들었다.

- **이미지 후보 탐색** — 세계관 시각 규칙(얼굴·손·하늘·텍스트 금지, 주황=관리 권위 한정, 공포가 아닌 심리적 긴장) 안에서 **소독(방역) 모티프**를 표면 서사·세계관 진실·리메이크 구조를 한 번에 잇는 앵커로 채택. 제작 스펙 `docs/REMAKE_DAY_이미지제작서_랜딩2종_v1.md`(LP01 소독약 보관실 · LP02 방역 통제 표지판) 작성 후 codex로 변형 생성 — 헤드라인 자리를 비우는 **센터 보이드 구도**, 도로 통제 표지판·원경 로우앵글 등 피드백 반영 반복. codex 알파 채널은 전용 파라미터 없이 프롬프트로 지원됨을 확인하고 투명배경 타이틀 로고(risograph 어긋난 인쇄 효과)도 4종 생성
- **최종 결정** — 히어로는 LP02 대신 **`/play` 엔트리 이미지를 재사용**(게임 진입과 랜딩의 시각 연속성). 생성물은 `output/imagegen/landing/`에 보존
- **버튼 정리** — 로그인·시작 버튼을 동일 위계·컴팩트 사이즈로, 로고 확대, 카피 콤마 수정

### 음성·BGM 반입과 토글 스위치

- **voice.md 개정(+136줄)** — 대사 체계를 기본 14개 + 분기·안내·회고 16개 = 30개로 정리. 파일 등록과 장면 조건을 구분해, 화자의 실제 발화·결과 방송이 대본과 일치할 때만 재생한다(파일 소진을 위해 시나리오에 없는 내용을 만들지 않는다). 소등 방송 1개·현장 인물 대사 5개 추가 제작 완료, 다음 목표는 세 NPC 목소리 6개
- **BGM·대사 연결** — `/play` 진입 시 기본 음량 25% 자동재생(차단 시 첫 입력에서 재시도), 장면·루프 간 재생 위치 유지. 대사 재생기는 방송→인물 순 재생, 대사 중 BGM 7% 덕킹 후 25% 복원, 다시 듣기·음성 끄기 독립 토글, 음원 실패가 진행을 막지 않는다
- **토글 스위치** — 음성·BGM 버튼을 우상단 토글 스위치 2개로 교체. 화면 밝기 적응 색은 `mix-blend-difference`가 요구 효과를 못 내 **배경 휘도 감지 훅(backdrop luminance detection)으로 재구현**, 밝은 화면(엔딩 등)에서 색 반전 확인. OFF 노브 수직 정렬·ON 투명 컷아웃 리그레션도 수정

### 배포 전략 확정 — 프론트 Vercel · 백엔드 t3.micro · 모델 홈서버

- 구도: 프론트 Vercel, 백엔드+Postgres AWS t3.micro, LLM 서빙은 홈서버 Ollama(백엔드가 프록시). 한국 단일 리전이라 Vercel의 지연 이점(도쿄 PoP ~30-40ms vs Cloudflare 서울 ~5-15ms)은 사실상 사라지지만, **프론트를 t3.micro에 올리면 Node 프로세스 ~100MB+와 렌더링 CPU가 백엔드·DB와 경합**하므로 자원 보존을 근거로 Vercel 유지를 결정했다
- 프로덕션 이행 시 과제로 기록: 크로스 도메인 쿠키(`SameSite=None; Secure`)와 백엔드 CORS에 실제 프론트 도메인 추가. 동일 도메인 자가 호스팅으로 가려면 동적 라우트(`harness/[attemptId]` 등)에 `generateStaticParams`가 필요해 정적 내보내기가 현재는 막혀 있다

### 마무리 — 커밋 상태와 이월

- **오늘 커밋 0건, 전부 미커밋** — 추적 파일 57개 +1,971/−487줄에 신규 파일 다수(auth 모듈 일체·`/terms`·`/privacy`·토글/음성 컴포넌트·음성 mp3 30종·신규 테스트·검증 기록·이미지 제작서). HANDOFF.md를 2026-09-15 기준으로 갱신(+17/−3줄)
- **이월(미완)** — Google Console redirect URI 등록, NPC 의미 품질 목표(중요 모순 0·현재 전언 이해·관련성 90%) 미달분, 사람 블라인드 페르소나 평가·새 참가자 5회차 실플레이, 세 NPC 목소리 6개 제작. 다음 플레이 관찰 포인트: 장면당 1회 제한과 다음 장면 재개, 오늘 경험/지난 루프 구분, 현재 전언에 대한 반응, 네 인물의 관심사 차이

## 2026-09-14 — 모델 선정 완료(Core gemma4·NPC kanana)와 실플레이 개선 3단계, 본진 승격 마무리

### E7 evaluator 통제 교체와 재측정, 테스터 3·4 데이터 분석

HANDOFF 1번 과제를 이행했다. `evaluator_verdict` 자작 통제 3건을 실플레이 제출문 14건으로 교체하고(기대 판정 사전 등록 후 사용자 승인, `review-verification/2026-09-14-eval-cases/CONFIRMED-eval-cases.md`) 4셀 × 14 × n=3 = 168콜로 재측정했다. 결과는 `model_evaluation.md` 부록 A.8, 원문 JSON은 `2026-09-13-core-selection/stage2-formal-20260914T021635Z.json`, 줄 수치는 `metrics.yml` 4줄.

- **우열 역전** — 기준선 `gemma3:12b` 1.00 → 0.36(최하), `gemma4:12b-N` 0.67 → 0.57(최상). A.7의 자작 통제 1.00은 정확도가 아니었다. 기준선은 프롬프트 자기 예시(rule 1)와 동형인 케이스(A1)를 3/3 틀리고, 근거 없는 partial(관대 방향)을 낸다.
- **모델 교체로 안 닫히는 결함 2건** — partial 기대 5케이스에서 4셀 × 15회 중 partial 0회(프롬프트 정의 문제). 덩어리 칸(D1)은 4셀 전부 오판(파이프라인 문제).
- **테스터 3·4 분석** — 사람 통과 2건(76.7·66.5)은 모두 `source_claims()`가 8칸 초과 문장을 마지막 칸에 몰아넣은 덩어리 매칭 의존이었다. 테스터3 3회차 confirmed 6건의 매칭 근거가 전부 1,028자 덩어리. 탭 0 순수 제출의 상한은 여전히 41.9. 테스터3 4·5회차는 동일 제출(md5 일치)인데 motive-1이 confirmed→none으로 뒤집혀 67.9→53.3 — temperature 0.0에서도 프로덕션 판정이 요동한 실측.
- **러너 보강** — `run_core_selection.py`에 `--roles` 필터 배선(formal 역할 선택, 기본 4역할 전부), `evaluator_probe`에 `expected_matched`/`got_matched` 기록 추가(hit 정의는 verdict만 — 기존 지표 호환). 프로덕션 엔진 코드는 변경하지 않았다.
- **Stage 3(동시성) 실행 — 두 후보 통과** — `--stage concurrency`를 러너에 구현(NPC 선상주 → 후보 로드 → NPC/Core 교대 3라운드, 매 콜 후 `/api/ps` 스냅샷). `gemma4:12b-N` pair peak 12.34 GiB(GPU 13,326/16,311 MiB), `gemma4:e4b-N` 7.89 GiB(9,520 MiB). 교대 구간 축출·오프로드·재로드 스파이크 0. `e4b` 초기 로드 때 NPC 1회성 축출 관측(1초 재로드 후 안정, ollama 스케줄러 메모리 추정 추정). 결과는 부록 A.9, `metrics.yml` 2줄.
- Stage 3 예산 참고: `exaone3.5:7.8b` 상주 실측 4.83 GiB(문서 4.14보다 큼). 재계산해도 두 후보 모두 여유.
- 한계: 기대 판정은 사전 등록했으나 단일 저자 확정. Gemini `-N` 셀 응답에 `thought_signature` 파트 잔존(기록만). §5.3 비열등 선언은 보류. Stage 3·4 미실행 — "대체 가능"이라고 쓰지 않는다.

### E7 Stage 4 — 루프 스모크 실행, Funnel 전 단계 완료

HANDOFF 다음 과제(Stage 4)를 이행했다. 결과는 `model_evaluation.md` 부록 A.10, `metrics.yml` 2줄(`stage: loop`), 원문 `stage4-loop-20260914T041032Z.json`.

- **`--stage loop` 구현** — 착수 순서대로 기존 `run_selfplay.py`가 방식 (a)(HTTP 실서버 경로)임을 확인하고 재사용. 신규 `scripts/loop_app.py` 래퍼가 프로덕션 `main.app`의 컴포지션 루트 `get_core_llm` 바인딩만 러너의 `ThinkingOllamaLLM(think=False)`로 교체 — 프로덕션 엔진 코드·`.env` 무변경(§2.3·§4.2). C9 검증용 `/loop-debug`(Core 콜·thinking 누계)도 래퍼에만 추가
- **두 후보 모두 게이트 통과** — 별도 서버(8600, `pigfarm_test` DB)에서 selfplay 성실 페르소나로 1회차(낮 발화 3건→비트→밤 제출→개입 질문·규칙 등록) 완주. `gemma4:12b-N` 61.1s / `gemma4:e4b-N` 35.6s, 둘 다 크래시 0·폴백 0/17·thinking 0자. `e4b`만 하네스 재시도 2회(재생성 해소, 폴백 아님)
- **계측 결함 1건 수정** — 1차 실행이 `/attempts/{id}/harness`(다섯 번째 밤 종료 후에만 열리는 인스펙터)를 조회해 `gate_pass=false` 오기록. 게임 자체는 정상 완주였음을 DB 이벤트 로그로 확인하고, 수집을 `events` 테이블 읽기 전용 SELECT로 교체해 재실행. 잘못 적립된 metrics 2줄은 제거, 1차 원문 JSON은 경위와 함께 보존
- 플레이어 모델은 상주 NPC(exaone3.5:7.8b) 재사용 — 제3 모델 로드 시 12b 셀(pair 12.34 GiB)에서 축출이 나기 때문
- **E7 Funnel Stage 0~4 전부 완료.** 남은 것은 결정 항목 D1~D3(Gemini 페이싱·thinking OFF 전환·teamprofile 분담)과 §5.3 비열등 선언 여부 — 모델 교체 결정은 사용자 몫으로 남긴다

### D3 해소 — teamprofile v3.0 전면 개정 (Masterless 구조 반영)

E7 결정 항목 D3(장민석·신채연 분담 확정)를 확인하다가 더 근본적인 미반영을 발견했다. 사용자가 `Masterless_Company_Team_Roles_v1.1_2026-09-10.md`를 원본으로 주며 "다른 프로젝트와 동일 분담으로 우리 것에 맞게 개정하라"고 지시했는데, v2.0은 이를 따르지 않고 "저장소 경계 기준 제안"을 새로 만들었던 것 — 그래서 "확정 필요" 각주가 남았고 beyondbob `_data/team.yml`(킥오프 시점 기록)과도 어긋나 있었다.

- **v3.0으로 전면 개정** — Masterless v1.1과 동일 매핑: 류준 = Team Lead · AI Agent(아키텍처+하네스+프롬프트), 장민석 = AI Evaluation(E7·E6 러너·metrics·provider 어댑터·Inspector), 신채연 = Full-stack · Game Frontend(게임 엔진·API·DB+`/play` 화면·시연), 이은상 = QA · UI Support · Release, 김충식 = Scenario Director · Content/Asset(시나리오 A 콘텐츠·이미지 에셋·Jekyll 허브 콘텐츠)
- v2.0 대비 이동: 하네스·프롬프트가 민석→류준, 게임 프론트가 충식→채연, 인스펙터 화면이 충식→민석, 에셋·콘텐츠가 충식 유지(단 타이틀이 FE→Scenario Director), 기동 스크립트·QA는 은상 유지
- **beyondbob `_data/team.yml` 동기화** — "teamprofile.md 기준" 주석대로 v3.0 역할·scope·owns로 교체(YAML 파싱 검증). key(ryujun·minseok·chaeyeon·eunsang·chungsik)는 불변이라 기존 포스트 author 표기와 데브로그 자동화(`author: chungsik`)는 영향 없음
- HANDOFF 결정 항목 D3 해소 표기. 남은 결정은 D1(Gemini 페이싱)·D2(thinking OFF 전환)
- **v3.1 후속 정정(사용자 확정)** — "에셋" 용어 전면 제거: 우리 것은 **그림**이다. 사운드 영역 신설 — 배경 BGM(장면·국면별 선정·루프 편집)과 **음성 대사(팀원 각자 자기 배역 목소리 녹음)** 를 충식(Scenario Director · Content) 소유로, 반입 검증은 은상 지원으로 추가. beyondbob team.yml 동기화(YAML 재검증)

### E6 Formal — NPC descent 실행, 7세 구간 실측 (부록 A.12·A.13)

Core 권고(`gemma4:12b-N`)를 기록만 하고, 사용자 지시대로 NPC 슬롯 하강(E6)으로 넘어갔다. 목적은 사용자 정의로 명확화 — "7세 지능 NPC를 어떻게 구현할 것인가: 작은 모델이 자연히 7세인가, 아니면 큰 모델을 하네스로 7세로 만드는가."

- **블로커 4건 해소 후 `run_model_descent.py` 구현** — 양자화(2b Q4 재pull, 0.8b는 Q4 태그 부재로 Q8_0 편차 기록), thinking 강제 OFF(러너 서브클래스 + 누계 0 검증), Anchor n=5 재측정, judge 3표 다수결·전원일치율(D3) 계측
- **ON/OFF 10셀 × n=5 (앵커 exaone + qwen 9b/4b/2b/0.8b)** — 전 셀 누설 0·스키마 1.0·D3 ≥0.96
- **답 ①: 자연 7세 크기는 없다.** OFF 전 셀 collapse ≠ none — qwen은 사실 응답 붕괴(3세화 방향), exaone은 이유 생성·의도 추론(어른화)
- **답 ②: 정책+하네스로 7세가 되는 크기는 측정 사다리상 4B 하나.** `qwen3.5:4b` ON이 유일하게 5항목 전부 ≥0.7·collapse=none (2B 이하는 정책을 줘도 항목1 붕괴, 7.8B·9B는 어른화 신호 잔존). 정책 효과(ON−OFF)도 4B에서 최대(+2)
- **5/5 검수(§8 금지 문장 규칙)** — 4b transcripts 전수 감사로 판정 정당성 확인. 관측: 4b 한자 혼입 2/25("그냥广播이지") — korean_only가 영문만 검사, CJK 검사는 후속 과제
- **후속 실측** — 4b+`gemma4:12b` pair peak **10.49 GiB**·교대 무축출(exaone 조합 12.34 대비 여유 ~2.9→~4.1 GiB), 루프 스모크(`loop_app_npc.py` 래퍼, NPC·Core 동시 think OFF) 1회차 완주·크래시 0·폴백 0/17
- Anchor가 judge 3표 규칙에서 1/5로 재측정돼 §4 비열등 판정은 형해화 — 절대 축 기준 후보는 4b 하나로 기록. 2026-09-06 행(n=2·단일 판정)과는 규칙이 달라 직접 비교하지 않는다

### Core 채택 반영 — `gemma4:12b-N` 전환 (프로덕션)

사용자 결정으로 Core를 전환했다. 정본 선언은 `model_evaluation.md` §5.3.

- **프로덕션 think 제어** — TDD로 `ollama_llm.py`에 `think: bool | None = None`(None=필드 미전송, 하위호환) 추가, `Settings`에 `core_llm_think`/`npc_llm_think`(default/on/off, 미지 값은 기동 실패), `llm_factory` 배선. 신규 테스트 7건(`tests/pure/test_ollama_llm.py`), **전체 393 passed** · import-linter 4계약 유지. 실험용 러너 서브클래스(`ThinkingOllamaLLM`)는 그대로 둔다
- **`.env` 전환** — `CORE_LLM_PROVIDER=ollama` · `CORE_LLM_MODEL=gemma4:12b` · `CORE_LLM_THINK=off`(신설). NPC 필드 무변경, 백업 후 해당 줄만 교체·타 줄 무변경 diff 검증
- **실서버 검증** — 래퍼 없이 프로덕션 `main:app`을 8600·`pigfarm_test`로 기동: health core `ollama:gemma4:12b`, 세션 생성 → 아침 loop(planner 포함) **12.13s** — E7 `-N` 셀 planner p95(12,215ms)와 일치, thinking OFF가 프로덕션 경로에서 실작동. 서버 종료·포트 정리 확인
- D2(운영 Gemini thinking OFF)는 Gemini 이탈로 **대상 소멸** 처리

### NPC 발화 품질 A/B — exaone vs qwen3.5:4b (부록 A.14)

E6(정책 준수)과 별개 축으로, "한국어 특화 exaone 기준선 대비 4b의 발화 품질" 질문을 쌍대 블라인드로 측정했다. E6 transcripts 재사용(같은 발화 25쌍), judge 3표 × 순서 스왑 2회(불일치=위치 편향 무효), 신규 러너 `run_npc_quality_ab.py`.

- **exaone 우세 3항목** — 한국어 자연스러움 18:3, 질문 관련성 18:3, 페르소나 적합 14:2
- **4b 우세 1항목** — 7세 말투 15:7. 단 평균 응답 9.1자(exaone 35.0자)의 극단적 단답이 원인으로 보이고, E6 §11이 경고한 judge 편향(짧은 출력의 7세다움 과대평가)과 같은 방향이라 단독 근거로 쓰지 않는다
- 결정적 지표: 4b 한자 혼입 **2/25(8%)** (A.12 관측 재확인), exaone 0/25. 폴백 둘 다 0
- **결론 구도**: exaone = 정책 1/5(어른화 신호)·발화 품질 우세 / 4b = 정책 5/5·VRAM 2.98GiB·발화 품질 열세 — **NPC 결정은 두 축의 트레이드오프**로 남는다 (사용자 결정 대기)

### 항목 2 판정 스펙 v2 — "아이도 이유를 지어낸다" 재판정 (부록 A.15)

사용자(Scenario Director)가 7세 스펙을 확정했다 — "애들도 이유를 지어낸다. 단 근거가 없거나 본인이 하고 싶은 이야기를 한다." 대조하니 `AGE7_POLICY` 프롬프트 2번은 이미 이 정의와 일치하는데 `run_age7_check.py` 항목 2 judge("이유 문장이 있으면 무조건 FAIL")가 정책보다 엄격한 판정 결함이었다.

- judge 기준 v2 재작성(아이다운 지어내기·딴 얘기 PASS / 다단계 인과·타인 의도 추론·조건·검증 요구만 FAIL, 예시 포함) 후 **A.12 ON transcripts를 재생성 없이 재판정**(`run_rejudge_item2.py`, judge 75콜, 3표)
- 결과: exaone **0.4 유지** — FAIL 전건("시간이 정해져 있으면 혼란 없이 받을 수 있으니까" 류)이 관대한 기준에서도 만장일치 FAIL. **어른화는 판정 결함이 아니라 실제 현상으로 확정**. 9b 0.6→0.8(탈락 사유는 p95라 유지), 0.8b 0.8→0.4(비문 횡설수설을 v2가 거름), 4b·2b 불변
- **NPC 결정 구도 불변** — exaone 1/5·4b 5/5, 정책 vs 품질의 반대 방향 트레이드오프 유지. 원 판정은 보존·병기, metrics `note: rejudge-item2-spec-v2` 5행, 이후 age7 실행은 v2 기준

### E6 확장 — `exaone3.5:2.4b` 후보 평가 (부록 A.16)

사용자 지시로 exaone 하위 버전을 평가했다 — 한국어 패밀리 유지 + 크기 하강으로 품질·정책·VRAM 세 축을 동시에 잡는지. pull 결과 Q4_K_M(통일 문제없음)·thinking 미지원·2.67B.

- **E6 셀(v2 스펙, n=5)**: ON 1/5 [사실 0.40 · 왜 0.20 · 망각 0.20 · 유도 1.00 · 문자 0.00], 누설 0 · 스키마 1.00 · D3 0.96 · p95 1,911ms · **VRAM 1.74 GiB**. **양방향 동시 붕괴** — collapse 분류는 toddler(사실대로 미달 우선)지만 어른화 조건(항목 2·5 동시 미달)도 충족, 사다리 첫 사례. FAIL transcripts가 "안전과 질서를 유지하기 위해"·"마치 큰 학교에서…" 류 다단계 인과·비유 설명 — **어른화는 크기 하강으로 안 사라진다(exaone 패밀리 성질)**. ON−OFF 격차 0
- **품질 A/B 2건**: vs 7.8b — 자연스러움 15:4·7세 말투 20:2·페르소나 10:4로 **패밀리 우위를 계승 못 함**(83.5자 장광설). vs 4b — 자연스러움 9:10 비등, 7세 말투 1:24 완패, 관련성 14:10 우세, 한자 혼입 0%(4b 8%)
- **pair(Core 12b)**: peak **9.25 GiB · 여유 ~6.0 GiB**, 교대 무축출(Core 초기 로드 시 NPC 1회성 축출 — A.9 e4b 패턴과 동일)
- **판정: 세 축 동시 해결 후보 아님** — VRAM만 최상, 정책 1/5 그대로, 품질은 4b와 비등 수준으로 하락. 결정 구도는 7.8b(품질) vs 4b(정책+VRAM) 유지. 한계: ollama 허브에 exaone3.5 중간 크기(4B급)가 없어 2.4b가 유일한 하강 지점. AB 러너에 `--raw-b`(서로 다른 원문 간 쌍대) 추가

### NPC 상업 라이선스 조사 + 상업 후보 3종 평가 (부록 A.17)

사용자 지적("엑사온이 상업용으론 안 되는 점")으로 라이선스를 조사하고 상업 가능 대안을 같은 파이프라인에 태웠다. 원문: `npc-license-survey.md` + formal/AB/pair JSON 3건.

- **EXAONE 3.5 = 연구 전용 확정** — 공식 LICENSE가 상업 이용을 LG AI Research 별도 계약으로 못박음. **현행 NPC는 라이선스 블로커** (법률 자문 아님 — 조항 인용·해석). Gemma 4는 Apache 2.0이라 Core 스택은 문제없음, judge gemma3는 Gemma Terms이나 배포 스택 밖
- **상업 후보 셀 실측(정책 ON·n=5·v2 스펙)** — `kanana1.5:8b`(Apache, GGUF Q4_K_M import) **4/5** [사실 0.6 · 나머지 전부 통과], p95 1,917ms·4.91 GiB. 항목 1 실패는 "충식 이송 맞아?" 한 케이스의 회피("그랬어?") 반복이 전부 — 민감 사실 시인 회피 패턴. `gemma4:e4b` 3/5(사실 0.4), `midm2.0:mini`(MIT 2.3B) 3/5(사실 0.2 — 2B급 3세화 동류). 전 셀 누설 0·스키마 1.00
- **품질 A/B(vs exaone 기준선)** — kanana: 자연스러움 9:7(무효 9, **대등권**)·관련성 14:5 열세·7세 말투 21:0 우세(12.3자 단답 편향 주의)·**외국 문자 혼입 0/25**(4b의 한자 8%와 대조)
- **pair(kanana+Core 12b)**: peak 12.42 GiB·교대 전 스냅샷 무축출·오프로드 0 — exaone 조합(12.34)과 동급, VRAM 이득 없음. 기록된 "축출 1"은 core 로드 전 워밍업 순서 아티팩트
- **구도 재편**: exaone(품질 기준선·연구 한정) vs **kanana 8b(상업×품질 최근접)** vs **qwen 4b(상업×정책×VRAM)**. 세 축 동시 해결 셀은 이번 확장에도 없음 — NPC 최종 선택은 사용자 결정. Modelfile import 2종(`kanana1.5:8b-q4km`·`midm2.0:mini-q4km`), 조사 문서 `npc-license-survey.md` 신규

### 실플레이 개선 1단계 — 채점 신뢰 3종 (판 da38de28 진단 반영)

새 모델 구성 첫 실플레이에서 **동일 제출(md5 일치, 307자)이 4→5회차 70.8→59.6으로 하락**(`identity-1` confirmed→none)한 것을 진단하고 채점 파이프라인을 보강했다. TDD, 신규 테스트 9건, 전체 **402 passed**.

- **temperature 0** — evaluator 콜은 이미 0.0 고정이 배선돼 있었음을 확인(그런데도 흔들림 — LLM 결정성은 보장 수단이 아님을 실증). 회귀 테스트로 고정만 추가
- **단조 잠금(ratchet)** — `scoring_rules.apply_ratchet`: 직전 밤 matched 문장이 이번 제출에 그대로 있으면 판정 하향 금지(상향 허용), `ratcheted` 플래그로 인스펙터 식별. 원칙: "유저가 문장을 바꾸지 않았으면 판정은 나빠지지 않는다"
- **덩어리 칸 해소** — `judge_candidates`: 8칸 UI 계약은 유지하되 채점기에는 칸을 문장 단위로 풀어 개별 후보로 전달(A.8의 4셀 공통 취약 해소). 실판 5회차 기준 후보 8칸 → 44문장
- **실판 검산(오프라인, DB 읽기만)** — 새 로직을 da38de28 4·5회차 기록에 적용하니 **identity-1이 confirmed로 복원되어 59.6 → 70.8 유지**. 요동 케이스를 정확히 차단
- 서버 재기동은 개선 배치 완료 후 일괄 예정

### 실플레이 개선 2단계 — 신의 질문 해금·규칙 어휘·NPC 몰라 완화

같은 판 진단의 나머지 백엔드 3건을 반영했다. TDD, 신규 테스트 17건, 전체 **419 passed** · import-linter 0위반.

- **신의 질문 = 단서 해금 + 수사 디렉션** — 시나리오에 `advisor_leads` 10건(미공개지만 스포일러 아닌 관찰 + 다음 행동 힌트, 회차 게이팅) 신설. 질문 1회마다 질문 주제와 가장 맞는 리드 1개가 **결정론으로 해금**되어 답변에 붙고 노트로 적립된다(채점 근거로 사용 가능, LLM 실패·unknown이어도 보장). 같은 리드는 두 번 안 나온다. 응답·이벤트에 `unlocked_note` 필드, 디렉션은 `next_observation`으로. "확인되지 않았습니다"만 돌아오던 질문 3회가 회당 최소 단서 1개의 보상 메커닉이 됐다
- **잠재(dormant) 장면 기회** — `SceneActionDTO.dormant` 신설: 기본 하루에는 일어나지 않고 **enforce 규칙을 걸어야만 일어나는 탐사 행동**. 시나리오에 5건 저작(준 손목띠 글자 보여주기 · 민석 수첩 보여주기 · 은상 따라가기(방송실 기계 소리) · 준 밤에 깨어 있기(트럭 소리) · 은상 들은 그대로 전하기), 행동 어휘 +4. 규칙 템플릿은 scene_actions에서 자동 파생되므로 직접 쓰기·후보에도 즉시 잡힌다 — "규칙 5개 중 4개가 설명한다"였던 어휘 협소가 구조적으로 풀림
- **직접 쓰기 대안 제시** — 스냅 실패 시 "설명한다" 고정 대신 `suggest_alternatives`가 문장 토큰과 겹치는 실행 가능 (대상, 행동) 후보 3개를 근접 순으로 제시
- **NPC 몰라 완화 (7세 정의 v2)** — AGE7 정책: 모르면 "몰라"로 끝내지 않고 기분·지금 보이는 것을 붙인다(사용자 확정 정의). 인물별 "직접 본 것" 4건씩 페르소나에 추가(채연·민석·은상·준 — 숨은 진실 비노출). **부작용을 잡았다**: 첫 문구는 망각 항목을 0.8→0.0으로 무너뜨림(4턴 전 사실을 회상) → 문구 정밀화 + **대화 메모리 창 절단(정책 ON이면 마지막 두 교환만 프롬프트에 제공)**으로 망각을 코드로 보장. 재측정(kanana, n=5): 망각 **1.00**, 왜=몰라 1.00, 유도 1.00, 문자 1.00, 사실 0.60 — **게이트 4/5 통과**, 누설 0/10(하네스 ON)
- 이 회차부터 AGE7 프롬프트 v2 + 메모리 창이 기준 — 이전 E6 수치와 직접 비교하지 않는다(변경 이력 기록)
- 프론트(3단계)로 넘기는 계약: `unlocked_note`(질문 응답·이벤트), `alternatives`(미리보기 후보 3개), 신규 어휘·잠재 행동은 기존 규칙 UI로 동작

### 실플레이 개선 3단계 — 진실 단계 공개·추리 여정 회고·프론트 연출 (배치 3/3 완료)

같은 판 진단의 프론트 3건 + 2단계 계약 렌더링을 반영하고 서버를 재기동했다. backend **425 passed**(419+6) · import-linter 0위반 · frontend build 통과 · **UI 테스트 4종 전부 통과**(five-loop-flow·connected-investigation·gameplay-clarity·scene-illustrations — 신규 UX에 맞게 갱신).

- **진실 단계 공개 (⑤)** — 일괄 덤프였던 `ending_lines`를 서버 필터로 교체: 시나리오에 `ending_lines_by_cell` 신설(정체/원인/동기 각 1줄), **셀 이해도 ≥80만 결말 줄이 열린다**(멸망 방식 outcome 줄은 비스포일러라 항상). 제출 응답에 `truth_reveal` 추가 — confirmed 명제만 진실 전문, partial은 "가까이 갔다", none은 **"?" 잠금 + "다시 도전하면 밝혀진다"**. 프론트 숨김이 아니라 서버가 걸러서 네트워크 응답에도 스포일러가 없다
- **회고 재작성 (⑥)** — 신규 `GET /attempts/{id}/journey`(5번째 밤 후 공개, 기존 잠금 규칙 동일): 회차별 "이 밤 확정된 명제·신이 연 단서·이해도", 최종 진실 대조(공개 범위 내), 미해결 칸 "?" + 힌트(리드 direction 재사용 — 비스포일러). Retrospective를 "너의 추리는 이렇게 걸어왔다" 여정 구조로 재작성 — 기존 개발 데이터(실험 기록·지표·원숭이손)는 **접힘("개발 데이터 — …궁금하다면") 안으로 강등**
- **2단계 계약 렌더 (③·④)** — 질문 답변에 `새 단서 — 노트에 적혔다` 강조 카드(unlocked_note) + 수사 디렉션을 접힘 밖 말미로 승격. 규칙 직접 쓰기 대안 3개는 기존 미리보기 선택 UI로 동작 확인
- **스모크(8601·pigfarm_test)** — kanana NPC + gemma4 Core 실서버로 1회차 selfplay: 완주 64.9s·폴백 0/16, **질문 1회에 advisor-lead 노트 실제 적립**, journey 게이트(진행 중 403) 정상, 응답 payload에 unlocked_note 확인. 스모크 서버 종료 검증
- **재기동** — stop→start_demo, health npc kanana·core gemma4:12b·db ok, /play 200. 테스터 재플레이 대기 상태

### NPC 채택 반영 — `kanana1.5:8b` 전환, 모델 선정 완료 (§5.3·A.18)

사용자 결정("어댑터 패턴으로 exaone은 언제든 바꿀 수 있게 하고 kanana로 바꾸자")을 반영했다.

- **교체 전 게이트** — NPC kanana + Core gemma4:12b 조합 루프 스모크(A.18): 1회차 완주 61.4s·크래시 0·**폴백 0/16**·Core thinking 0자. 관리 항목 3건도 깨끗 — 회피성 응답 0/21, 외국 문자 혼입 0, 평균 응답 길이 11.4자(단답 경향은 운영 관찰 지속)
- **`.env` 한 줄 전환** — `NPC_LLM_MODEL=kanana1.5:8b-q4km` (타 줄 무변경 diff 검증). 실서버 검증: health npc `ollama:kanana1.5:8b-q4km`·core `ollama:gemma4:12b`, 발화 실콜 정상("준 → 몰라. 아직.")
- **어댑터 패턴 확인** — 프로덕션 코드에 모델명 하드코딩 없음(설정 기본값뿐). **롤백 = `.env` `NPC_LLM_MODEL=exaone3.5:7.8b` 한 줄.** exaone3.5:7.8b는 롤백·개발용으로 로컬 유지(연구 용도는 라이선스 내)
- **모델 정리** — 평가용 임시 2종(`exaone3.5:2.4b`·`midm2.0:mini-q4km`) `ollama rm` + GGUF 원본 삭제, 약 9GB 회수. qwen3.5 패밀리는 사용자 지시로 전부 유지
- **오늘로 모델 선정(E7 Core + E6/확장 NPC)이 전부 끝났다.** 운영 구성: Core `gemma4:12b`(think off) · NPC `kanana1.5:8b`(Apache 2.0) · embedding gemini. 상업 배포 스택에서 라이선스 블로커 0

### D1 실측 — Gemini 쿼터 프로브 (부록 A.11)

결정 항목 D1을 실측으로 닫을 준비를 마쳤다. 결과는 `model_evaluation.md` 부록 A.11, 원문 `d1-gemini-rpm-probe-20260914.txt`, `metrics.yml` 1줄(`stage: pacing_probe`).

- **프로브** — 서버가 내려간 상태에서 페이싱 없이 초소형 요청 40콜 연속 전송: **55.4초(약 43 RPM 지속), 429 제한 0건**
- **판단** — 무료 티어 공칭 10 RPM이면 11콜째에 걸렸어야 한다. 이 키는 **유료 티어(Tier 1, 공칭 150~300 RPM)** 로 판단. `gemini_llm.py`의 10 RPM은 서버 쿼터가 아니라 무료 티어 기준의 클라이언트 과잉 보수 설정이었다
- **게이트 재계산** — `effective = max(raw, 60000/RPM)`: C11은 RPM ≥ 12, C13은 RPM ≥ 20이면 통과로 뒤집힌다. 실측 지속치와 여유를 두면 **30 RPM이 안전 운영값 후보** (C11 2,238ms · C13 20s)
- **결정(사용자)** — 키가 유료인 것은 맞으나 **판단 기준은 무료 티어 한도(10 RPM)로 고정**: 유료 쿼터에 기대는 구성을 판정 근거로 삼지 않는다. 페이싱 유지(`.env` 무변경), Gemini C11·C13 탈락 판정 유효, **D1 해소**. 남은 결정은 D2 하나
- **무료 키 전환 실측(같은 날 추록)** — 사용자가 키를 실제로 무료 티어로 교체, 재프로브 결과 초소형 콜(5토큰)이 **20~28초** + 503 1회 + 타임아웃 1회, 6콜/131초(실효 2.7 RPM). 유료 키의 동일 콜은 1.1~1.5초였다. **무료 키에서는 10 RPM 쿼터 이전에 지연·용량이 먼저 무너진다** — E7의 Gemini raw 수치는 유료 키 측정값이었고, 무료 기준으로는 raw만으로 C11을 10배 초과. 시점 한정(일요일 13시대 수요 스파이크)이라 상시 일반화는 하지 않되, 무료 키 운영의 지연 요동 리스크로 기록

### 본진 승격 마무리 — 전체 테스트 검증 후 demo.pigfarm 심볼릭 링크 제거

`com.remakeday` 새 세션에서 전체 검증을 통과시킨 뒤 하위 호환용 심볼릭 링크를 제거했다.

- **검증** — backend pytest 386 passed(7.5초, `.venv/bin/python -m pytest`), import-linter 4계약 0위반, frontend `next build` 성공(TypeScript 검사 포함, 전 라우트 생성 정상).
- **주의점 발견** — `.venv/bin/pytest`로 직접 실행하면 cwd가 sys.path에 안 들어가 수집 오류 31건이 난다. `python -m pytest` 방식이 정본이다(마이그레이션 문제 아님).
- **정리** — `~/projects/demo.pigfarm` 심볼릭 링크 삭제(13바이트 링크만 제거, 실파일 무손실). 구 경로가 박힌 `__pycache__` 전체 삭제 후 386 재통과 확인. 활성 문서 2건(`HANDOFF.md` 재현 경로, `demo_guide.md` cd 경로)을 `com.remakeday`로 갱신.
- **구 경로 전수 치환** — 사용자 지시로 과거 기록 포함 프로젝트 전체의 `projects/demo.pigfarm` 경로 참조를 `com.remakeday`로 일괄 수정(`tester2.md`, backend-tests.txt 2건, final-validation-summary.txt — 같은 파일들을 가리키므로 기록 무손실). 예외 3종은 의도적 유지: ① `docker-compose.yml`의 `name: demopigfarm`(테스터 데이터 볼륨 `demopigfarm_pigfarm-db-data` 식별자 — 바꾸면 DB가 분리됨), ② `/tmp/demo-pigfarm-*` 스냅샷·diff 아티팩트명(그 이름으로 실존하는 파일), ③ 옛 저장소 이름 자체를 서술하는 역사 문장(본 로그 및 9/1 마이그레이션 항목).
- 남은 것: `git push --force origin main`(사용자 승인 대기), `./start_demo.sh` 서버 기동 확인.

### 데브로그 자동화 — 23:45 일일 기록 + beyondbob 지킬 연동

다른 프로젝트(masterless 23:50·beyondfacade 23:55)와 같은 패턴으로 `scripts/jekyll-devlog.sh`를 만들었다. 매일 23:45에 ① `claude -p`가 당일 커밋·수정 파일을 근거로 이 파일(`docs/jekyll.md`)의 오늘 섹션을 추가/갱신하고, ② 오늘 섹션만 추출해 front matter(title·author: chungsik·tags)를 붙여 `beyondbob.remakeday.com/_posts/YYYY-MM-DD-dev-log.md`로 변환 복사한다. 역할 분리 — com.remakeday는 개발만, beyondbob은 지킬만. 지킬 쪽 포스트는 사본이라 직접 수정 금지(다음 실행 때 덮어씀). 커밋/푸시는 자동화하지 않는다(사용자 직접). awk 섹션 추출·포스트 변환은 오늘 섹션(22줄)으로 검증했고, crontab 등록(`45 23 * * *`)은 사용자 실행으로 마무리.

### 마감 정리 — 커밋 상태·정본 위치·음성 산출물

- **커밋 6건** — f2b4926(11:48, 본진 초기 승격) · 570500b(12:50, 승격 마무리·데브로그 자동화) · 20:44 일괄 4건(b0dd281 teamprofile v3.1 / b6e44b2 프로덕션 think 제어·채택 반영 / 9ad8ecc 평가 러너 / 09c3f23 모델 평가 정본 A.10~A.18). 푸시까지 완료(HANDOFF 기록).
- **미커밋 — 실플레이 개선 1~3단계 배치** — 26파일 +741/−81, 신규 6파일(백엔드 테스트 5건 `test_journey_and_reveal`·`test_advisor_leads`·`test_age7_memory_window`·`test_dormant_scene_action`·`test_rule_alternatives`, 프론트 `TruthRevealCards.tsx`). 테스터 재플레이 확인 후 커밋하기로 하고 대기 중(HANDOFF에 명시).
- **수치 정본 위치** — 오늘 실측치는 전부 `model_evaluation.md`(부록 A.8~A.18 11건 + 변경 이력 14행)와 `metrics.yml`(오늘자 43행 적립)이 정본이다. 이 일지에는 결론만 요약했다.
- **음성 산출물 7건** — `output/voice/`에 mp3 7건 생성(22:44~22:45). 전부 `docs/voice.md`의 제작 목록과 문장 일치 — 관리자 방송 MA01~MA06 6건 + 회고 낭독 EN03("지금부터, 무엇이 적용됐고…") 1건. 생성 도구와 게임 반입·재생 배선은 저장소에 기록이 없다(코드에서 `output/voice` 참조 0건) — 반입 시 경위를 함께 기록할 것.
- **당일 미결 해소와 새 이월** — 본진 승격 절에서 남겼던 두 건은 당일 해소: `git push --force origin main` 완료, 서버 기동은 개선 3단계 재기동으로 확인(health npc kanana·core gemma4:12b·/play 200). 어제(09-13) 남긴 Stage 3·4 미실행도 오늘 전부 완료. 내일로 넘기는 것: 테스터 재플레이(관찰 포인트 6개), 재플레이 확인 후 개선 배치 커밋, 4b 한자 혼입 CJK 검사(korean_only 보강), kanana 운영 관찰 3건(사실 질문 회피·질문 관련성·단답 경향).

## 2026-09-13 — Core 슬롯 모델 평가(E7) 착수와 Stage 0~2 실행

게임의 LLM 자리 7개를 정리하는 데서 시작해, Core 슬롯에 어떤 모델을 쓸지 실측으로 정하는 실험을 설계하고 3단계까지 돌렸다. 평가 정본은 `docs/model_evaluation.md`에 새로 만들었고 수치는 전부 거기에 적립한다.

### 과거 기록을 다시 읽고 고친 판단

- **"gemma3:12b가 심각해서 Gemini로 바꿨다"는 이해가 정확하지 않았다.** 2026-09-09 원문 프로브 10회분을 시간순으로 다시 세어 보니 `advisor_answer` 12/12 폴백은 **첫 판 한 번뿐**이었고, 19분 뒤 근거 인용 계약을 고치자 같은 모델이 0/12로 돌아왔다. 이후 여덟 번 더 돌리는 동안 0~1/12를 유지했다. Core를 Gemini로 전환한 것은 그로부터 약 4시간 뒤다. 모델 교체 전에 이미 코드로 해소된 실패였다.
- **2026-09-08의 "Planner 81/81 전량 폴백"도 모델 문제가 아니었다.** 원인은 어휘 사전 불일치였고(`'혼자 있다'` 39건 · `'소등'` 18건 — 사전에는 `"혼자 있는다"`), 현재는 `planner_output()`이 행동 칸을 JSON 스키마 enum으로 제약해 구조적으로 막혀 있다. 이번 측정에서 4모델 × 9콜 전부 LAR 1.0이다.
- **RM1(질문 명제의 극성과 인용 사건의 극성 혼동)은 닫힌 적이 없다.** 설계 문서에 "adapter 전환 성공은 RM1 해결의 증거가 아니다"라고 적혀 있고, Gemini 전환 후 확인한 기록도 없다. 오늘 기준선을 다시 재니 PC3·SPC2가 그대로 실패한다.

### 측정 조건을 먼저 바로잡았다

- **thinking 제어가 없으면 결과가 무효였다.** 두 어댑터 모두 provider 기본값대로 돌고 있었고, 그 기본값이 무엇인지 측정된 적이 없었다. Stage 0에서 확인한 결과 `gemma4:12b`·`gemma4:e4b`·`qwen3.5:9b`·`gemini-3-flash-preview` **전부 thinking ON**이었다. 즉 현행 운영 Core는 콜당 774 thinking 토큰을 쓰는 `-T` 셀에서 돌고 있었다.
- 제어는 **러너 안에서 어댑터를 서브클래싱해 주입**했다. 프로덕션 `ollama_llm.py`·`gemini_llm.py`는 한 줄도 바꾸지 않았다. 채택이 결정되면 그때 반영한다.
- `off` 셀의 thinking 사용량이 실제로 0인지 매 셀 검증했다(게이트 C9). 4셀 전부 0이라 셀 라벨을 신뢰할 수 있다.

### 지연을 Hard 게이트로 올렸다

Core 호출은 전부 플레이어가 멈춰서 기다리는 자리다 — 아침 로딩(planner), 밤 질문 3회(advisor), 밤 채점(evaluator × 정답 명제 수). 품질이 좋아도 게임에서 못 쓰는 지연은 탈락 사유라고 보고, 지연을 보고 항목에서 게이트로 승격했다. **C11 advisor p95 ≤ 5초 · C12 planner p95 ≤ 15초 · C13 밤 채점 ≤ 30초.** 값은 UX 통념으로 잡은 것이며 플레이테스트 체감 기준이 나오면 교체한다.

재시도 배수도 확인했다. 하네스가 검사에 걸리면 최대 2회 재생성하는데 thinking 셀에서는 그 비용이 곱해진다. `gemma4:12b-T`는 단발 27초가 코퍼스 전체에서는 콜당 약 80초였다. **지연은 단발이 아니라 코퍼스 p95로 판정한다.**

### 실행 결과

- **Stage 0 (13셀, 프로토콜 호환)** — `qwen3.5:9b`는 thinking ON에서 JSON 생성에 실패했다(151~153초, thinking 13,932). `gemma4:e4b`는 디스크 8.95 GiB인데 실제 상주가 3.06 GiB로, 디스크 기준 예산 추정이 이 모델에서만 크게 빗나갔다.
- **Stage 1 (8셀 × 22문항 = 176콜)** — thinking ON 셀이 C11에 **전부 탈락**했다(`gemma4:12b-T` 194,589ms·38배, `gemini-T` 13,443ms, `gemma4:e4b-T` 11,546ms). 품질 이득도 없었다. `gemini`는 ON/OFF의 PCA가 1.00으로 같은데 5.3배 느리고, `gemma4:12b`는 ON에서 폴백 0.00→0.32·PCA 0.90→0.70으로 오히려 무너졌다. 반면 `gemma4:e4b`는 ON에서 PCA가 올랐다 — **thinking의 효과는 모델마다 반대 방향이다.**
- **Stage 2 (4셀 × 4역할 × n=3 = 372콜, 공식 수치)** — 폴백 0.00·오류 0. 통제 통과율이 전부 0.00 또는 1.00으로 갈려 n=3에서 흔들리지 않았다.

### 오늘의 결론과 결론이 아닌 것

- **`gemma4:12b-N`에서 RM1이 닫힌다.** 기준선이 못 넘던 PC3·PC8·SPC2를 n=3 전부 통과했고, 지연·VRAM은 기준선과 사실상 같다. 로컬에서 극성쌍을 통과한 유일한 모델이다.
- **그러나 비열등은 아니다.** 기준선이 통과한 `evaluator_verdict`를 1.00 → 0.67로 떨어뜨렸다. 다만 그 실패 케이스의 기대값은 2026-09-09 코퍼스가 아니라 이번에 직접 쓴 것이라 증거력이 약하다. `gemma4`가 기준선보다 **엄격한** 방향으로 틀리는데, 이 프로젝트는 채점기가 `none`으로 치우쳐 합격률 3.1%를 겪은 이력이 있어 가볍게 볼 수 없다. 실플레이 제출문으로 통제를 교체한 뒤 다시 본다.
- **Gemini는 모델이 아니라 우리 설정 때문에 탈락했다.** raw p95 2,238ms로 가장 빠르고 품질도 전 지표 1위인데, 프로세스 전역 10 RPM이 콜 간격을 6초로 강제해 C11·C13을 넘지 못한다. 밤 채점은 60초다. 페이싱 값을 조정할 수 있다면 판정이 뒤집힌다.
- **`gemma4:e4b-N`은 효율 축의 답이다.** 품질은 기준선과 동등한데 속도 1.5~2배, VRAM 41%(3.06 GiB)다.
- **Stage 3(동시성)·Stage 4(루프 완주)는 아직 안 돌렸다. "대체 가능"이라고 쓸 수 없다.** 모델 교체 결정도 하지 않았다.

### 문서 정리

- `docs/model_evaluation.md` 신규 — 모델 평가 정본. E7 설계와 Stage 0~2 실측 전부
- `docs/teamprofile.md` v2.0 — 역할 정의를 업무 분류·대표 산출물 수준으로 확장. 역할 배정은 기존 것을 유지했고 장민석·신채연의 백엔드 분담만 제안 상태
- 다른 프로젝트 문서 2건을 제자리로 보냈다. Horn 스펙은 유일본이라 `thehorn.masterlesscompany.com`으로 이동했고, Team Roles는 `com.masterlesscompany`에 동일 사본이 이미 있어 중복만 제거했다

---

## 2026-09-10 — 플레이 피드백 반영과 화면 가독성 재수정

9월 9일 밤부터 이어진 사용자 플레이 피드백을 반영했다. 핵심은 **기록을 많이 보여주는 것보다 장면을 이해하고, 자기 추리를 이어 쓰고, 필요한 기록을 쉽게 다시 찾게 하는 것**이었다. 아래는 최종 반영 상태이며, 중간 수정에서 잘못 해석한 부분도 함께 남긴다.

### 게임 진행 안내와 장면 대화

- **시작 전에 진행 규칙 안내** — 짧은 첫 안내와 접힌 상세 규칙을 넣고 낮에도 ‘플레이 안내’를 다시 열 수 있게 했다. 한 판 5일, 하루 6장면, 인물마다 한 장면에 대화 1회, 하루 공용 대화 예산 8→7→6→5→4회(기본 총 30회)를 설명한다. 장면 이동은 무료이고 대화 횟수는 충전되지 않는다. 특별한 규칙의 대가는 예산을 더 줄일 수 있으며, 처음 네 번의 밤에 하는 질문 3회는 낮 대화와 별도다.
- **기록 낭독처럼 들리던 주변 대사 교체** — ‘지금 공개된 관찰 기록이야’, ‘그 기록 밖의 일은 아직 확인하지 못했어’ 같은 반복 문구 대신 여섯 장면에 상황에 맞는 대화를 3줄씩 작성했다. 손목띠를 궁금해하는 준과 민석, 남은 배급과 수첩을 두고 이야기하는 채연과 민석처럼 앞뒤 행동이 연결되게 했다. 실제 행동이 일어나고 해당 인물이 있을 때만 재생하며, 규칙으로 막힌 행동이나 사라진 인물을 원래 대사로 다시 노출하지 않는다. 이 주변 대화에는 모델 호출이 필요 없다.
- **저장·거절 알림의 의미 정리** — 긴 관찰 원문을 노란 알림에 다시 붙이거나 모호하게 ‘두고 간다’고 표시하던 방식을 정리했다. 최종 저장 알림은 ‘단서 기록에 새 내용을 저장했다.’, 제안 거절은 ‘원숭이손의 제안을 거절했다.’로 구분한다.

### 직접 쓴 규칙의 조건 보존

- **‘내가 보고를 물어보면’이라는 조건 유지** — ‘민석이 보고하는 것을 내가 물어보면 상세하게 설명한다’는 요청을 일반적인 ‘알고 있는 관찰을 설명한다’로 축약하지 않는다. 민석·보고 주제·플레이어의 질문이라는 조건을 보존하고, 맞는 질문이 들어왔을 때 실행한다. 현재 작성된 보고 응답을 지원하는 인물은 민석이다. 지원하지 않는 추가 조건은 포괄적인 대안으로 몰래 바꾸지 않고 한계를 알린다.
- **실제 모델의 허구 보고 발견과 대응** — 실제 NPC 모델이 없는 배급 수량과 보고 내용을 만들어내는 사례를 확인했다. 프롬프트 강화·온도 조정만으로 해결되지 않아, 해당 규칙의 핵심 응답은 실제 배급·기록·방송실 방문 행동에 맞는 작성된 5개 분기에서 고르게 했다. 아직 보고하지 않은 장면에서는 준비와 의도를, 보고한 뒤에는 자신이 한 일을 설명한다. 이 규칙 응답의 모델 호출은 0회이며 일반 자유 대화는 기존 NPC 모델을 사용한다.
- **오발동 방지** — ‘보고’와 ‘보다’의 활용형, 단순 방송실 위치 질문, ‘보고 얘기 말고’, 플레이어 자신이 보고한 내용 등을 구분했다. 독립 리뷰에서 발견한 동음어 오발동과 보고 주체 변경을 수정했다.

### 가독성 요청의 오해와 배경 회귀 수정

- **글씨에 손상 효과가 번지지 않게 분리** — 둘째 날 이후에도 글씨가 흐려지거나 기울어지지 않도록 손상 효과를 이미지에만 적용했다.
- **아침 화면 높이 회귀** — 공통 버튼의 최소 높이 44px 스타일이 아침 화면의 전체 높이 설정을 덮어쓰면서 배경이 약 370px 높이의 상단 영역에만 표시되는 현상을 재현했다. 공통 스타일을 기본값으로 적용하도록 CSS 레이어를 수정했고, 그림은 `object-contain`으로 원래 비율과 전체 구도를 유지하게 했다. 화면 비율에 따라 여백은 생긴다. 390px·1440px와 사용자 첨부 화면에 맞춘 1845×935 크기에서 확인했다.
- **‘안내 글씨를 잘 보이게’와 ‘채팅을 키우기’를 구분** — 초기 대응에서 대화와 보조 글씨를 함께 키워 사용자의 의도보다 대화 영역이 커졌다. 후속 피드백에 따라 아침 날짜·남은 대화·‘탭하여 계속’ 안내는 18px의 진한 글씨로 표시하고 상시 흐림을 없앴다. 계속 안내에는 굵기와 밑줄을 더했다. 낮 대화 본문은 16px로 조정하고 데스크톱의 대화 영역 비중을 줄였다. 인물 카드가 하단 끝까지 길게 늘어나지 않게 하고 입력부와 다음 장면 버튼도 간결하게 정리했다.

### ‘노트’의 용도와 조작을 드러내기

- **‘노트 9’ → ‘단서 기록 열기 9건 →’** — 숫자만으로는 누를 수 있는 기능인지, 무엇이 들어 있는지 알기 어렵다는 피드백을 반영했다. 크게 늘리는 대신 진한 배경·테두리·동작이 있는 이름으로 작은 버튼을 구분하고 ‘본 행동·들은 말 다시 보기’ 설명을 붙였다. 그림 위를 가리던 기록 버튼 영역은 그림 아래로 분리했다.
- **내용과 이름의 일치** — 열린 화면의 제목과 도움말도 ‘단서 기록’으로 통일했다. 본 행동과 들은 말을 다시 살펴 밤의 추리에 활용하는 기능이고, 열어도 대화 횟수가 줄지 않는다고 안내한다. 인물이 말했다는 기록과 그 말의 진위는 구분한다.
- **닫기 버튼 두 곳** — 기록이 많아지면 닫으려고 맨 위까지 돌아가야 하는 불편을 반영했다. 처음에는 목록 맨 아래 중앙으로 옮겼고, 사용자의 추가 요청에 따라 **기존 상단 닫기와 목록 맨 아래 중앙 닫기를 함께 유지**하는 것으로 확정했다. 두 버튼 모두 같은 기록 창을 닫으며 키보드 포커스 복원도 유지한다.

### 검증과 남은 확인

- 게임 로직 수정 시 별도 `pigfarm_test` DB의 백엔드 전체 **386 passed**, 기존 의존 라이브러리 경고 3건. 아키텍처 계약 4개 유지, 코어 금칙어 0건. 이후 배경·버튼 배치 수정은 프론트엔드만 변경했으며, 386건은 해당 백엔드 검증 시점의 결과다.
- 초기 게임 개선의 프론트엔드 검사 4종(gameplay-clarity, connected-investigation, five-loop-flow, scene-illustrations)이 통과했다. 후속 가독성 수정에서는 **인물 4명·그림 2장**을 포함하도록 검사를 보강하고 390×844, 1440×900, 1564×800 화면에서 안내 크기·선명도, 작은 기록 버튼, 대화 영역 크기, 무료 조작과 기록 확인을 검증했다. TypeScript 검사도 통과했다.
- 마지막 상·하단 닫기 버튼 반영 뒤 connected-investigation을 재실행해 기록·원본 장면 열람, 키보드 포커스, 밤 답안·질문·규칙·회고 연결 검사가 통과했다. 브라우저 검사는 실제 프론트와 모의 API를 사용했으며 기존 플레이 DB에 테스트 판을 만들지 않았다.
- 실제 NPC 실행 표본에서는 일반 질문 2개의 모델 호출이 각각 1회(약 0.98초·0.82초), 조건부 보고 질문 2개는 0회였다. 이는 작은 표본이며 모든 자유 대화의 의미 정확성이나 실제 사용자의 이해도 향상을 입증한 수치는 아니다.
- 기존 플레이 기록·대사·점수는 재작성하거나 재채점하지 않았다. 과거에 저장된 기록에는 이전 문장이 남을 수 있다. 최신 화면에 대한 사용자 후속 플레이와 자유 대화의 맥락 정확성은 계속 확인해야 한다.

[게임 로직 개선 검증 기록](review-verification/2026-09-10-gameplay/README.md) · [반영 설계](superpowers/specs/2026-09-10-gameplay-design.md)

### 정본 문서 5종 작성 — `docs/define/`

`docs/example/`의 「자유중대」 정본 세트와 같은 구성으로 REMAKE DAY 정본 5종을 새로 썼다. 근거는 기획서 v8.1, `review.md`(2026-09-08 채점 구조 진단), `metrics.yml`, `HANDOFF.md`, `scenario_a/adapter.py`, `game_constants.py`·`scoring_rules.py`·`cookie_rules.py`, 러너 스크립트 7종이다. 기존 `docs/REMAKE_DAY_기획서_v8.1.md`는 수정하지 않고 그대로 남겼다.

- **기획서 확정본 v9.0** — v8.1 이후 결정을 반영한 새 SSOT. 이해도 상황70(원인35·동기35)+정체30, 부작용 칸 총점 제외, 점수와 무관한 5회차 완주와 0%에서도 열리는 회고, 원문 보존 분할(요약 모델·날조 필터 제거), 정답 명제 재작성, 코어 모델 `gemini-3-flash-preview` 전환을 본문에 반영했다.
- **통합시나리오 v1.0** — 어댑터 데이터를 문서화했다. 표면/숨겨진 진실, 인물 6명, 6비트 대본과 방송 본문, 장면 행동 9개·장면 대화 6세트·민석 조건부 5분기, 단서 그림, 파편 11개, 정답 주장 10개와 정보원 대응, 쿠키 12종, 금칙어·행동 어휘 15개, 회차별 흐름, 전이 시나리오.
- **팀원용 쉬운설명 v9.0** — 60절 반말 전달본.
- **AI Agent Evaluation PART1 정본 v1.0 / PART2 ELI5 v1.0** — 역할 7종의 요구 정책, 실험 E1~E5, RQ1~RQ7, 측정 층 L1~L8, 게이트 초기값과 실측, 러너 7종의 게이트 정의, 실패 분류 F1~F11, 보고 문장 형식.
- **미달·미적용을 그대로 적었다** — `age7_check` items_passed 2/5(3턴 망각 0.0, n=2), `scoring_calibration` gate_pass false, R3 Planner 폴백 81/81, 쿠키 게이팅 반전·칸 만점 임계 0.6·`CLAIMS_MAX` 10·골든셋 교체 미적용, 사람 표본 N=1~2와 50/70% 목표 미검증. 골든셋 오염(F10)을 평가 설계 실패로 분류해 금지 사항으로 고정했다.
- 문서 간 상호 참조 절 번호를 점검해 어긋난 6곳을 수정했다. 코드·게임 동작은 변경하지 않았고 테스트는 실행하지 않았다(문서 작업).

## 2026-09-09 밤 — 밤 답안 이어쓰기와 질문 응답 정리

- **이전 밤에 직접 쓴 글을 그대로 이어쓰기** — 1번째 밤의 입력을 2번째 밤에 복원하고, 수정·추가한 2번째 밤의 글을 3번째 밤에 이어주는 방식으로 바꿨다. 요약된 주장 목록 대신 저장된 자유서술 원문을 복원하며, 선택 근거는 별도로 유지한다. 다른 판의 답안이 섞이지 않도록 구분했다.
- **밤 화면의 기록 나열과 선로딩 축소** — 직접 입력과 제출을 앞에 두고 관찰 기록·그림 모음은 접어 두었다가 열 때 조회한다. 모든 대사를 먼저 길게 나열하고 고르게 하는 흐름에서, 자신의 글을 먼저 쓰고 필요한 근거를 찾아 보충하는 흐름으로 조정했다.
- **질문 하나에 모든 기록을 붙이지 않기** — 신의 질문에는 짧은 자연어 답변을 먼저 보여주고 원본 근거는 펼쳐 확인하게 했다. 한 답변의 표시 근거는 최대 2개다. 모델 입력은 공개된 세계 설명과 질문에 관련된 최대 8개·원문 6,000자 이내 기록, 같은 회차의 최근 문답 2쌍으로 제한했다. 정상 처리의 모델 호출은 2회에서 1회로 줄였다. 숨겨진 정답과 미공개 미래 사건은 제공하지 않는다.
- **반복 회차의 맥락 보존** — 같은 문장이라도 회차·장면이 다르면 별도 사건으로 보존하고, 질문에서 지정한 회차를 우선한다. ‘확인되지 않았다’는 상태만 반복하기보다 공개된 상황에서 답할 수 있는 부분과 아직 모르는 부분을 구분하도록 했다.
- **검증** — 당시 백엔드 **334 passed**, TypeScript·아키텍처 검사와 모의 API 기반 브라우저 연결 검사가 통과했다. 실제 `gemini-3-flash-preview` 6문항에서는 각 1회 호출, 재시도·폴백 0회, 응답 5.08~10.42초였다. 이 수치는 해당 표본의 관측치이며 전후 지연 시간을 같은 조건에서 비교한 성능 개선율은 아니다. 기존 provider 지연과 RPM 제한, 밤 최종 채점의 호출 구조는 남아 있다.
- **실행 경로와 Safari 새 창 문제** — `/`에서 `/play`로 연결하고 개발 도구의 자동 브라우저 열기를 막는 설정을 추가했다. 점검 시 `/play` HTTP 200과 백엔드 DB 정상 상태를 확인했다. **Safari에서 창이 계속 열리던 정확한 원인은 확정하지 못했으며, 루트 주소와 `/play`의 차이가 충돌 원인이라고 결론 내리지 않았다.** 자동 검증에는 화면 없는 브라우저를 사용하고 종료했다.

[밤 답안·질문 개선 검증 기록](review-verification/2026-09-09-night-writing-advisor/README.md)

## 2026-09-09

- **연결형 추리 구현과 검증 이력 분리 기록** — 테스터1의 맥락 단절을 바탕으로 관찰→노트→질문·규칙→다음 장면→밤 답안→회고를 연결하고, 승인 이미지 A안(E01/E04/E07/E10 고정 초상, clue-07…12 사건 장면, 본 장면만 모으는 밤 갤러리)을 구현했다. Gemini/Ollama adapter 추가 뒤 backend full-suite는 **327 passed, 기존 경고3건(6.86초)**이며, 이번 연결형 재설계 범위에서 도구 결과로 확인 가능한 backend pytest는 **최소81회**(full 명령 시도21 + owner focused49 + reviewer focused11; full21에는 import 수집 실패1회 포함)다. 이는 프로젝트 전 기간의 누적 횟수가 아니다. Adapter에 기본 10 RPM process pacing을 추가한 red1·green1이 포함된다. frontend typecheck·build·browser, 격리 API, full-corpus 실제 모델 raw12회와 별도 진단3회의 상세는 [테스트 실행 이력](review-verification/2026-09-09-connected-implementation/test-execution-ledger.md)에 분리했다. 전체 정확 횟수는 미확정이다. 사용자가 core 기본 모델로 Gemini 3 Flash를 선택했고 `gemini-3-flash-preview` 실제 structured 호출은 2.543초에 기대 답을 반환했다. `.env`의 core 두 필드만 전환했으며 2026-09-09 17:15:54 KST 이 PC 로컬 backend health에서 core `gemini:gemini-3-flash-preview`·NPC `ollama:exaone3.5:7.8b`·embedding `gemini`·DB `ok`, localhost3500 `/play` HTTP200을 확인했다. **테스터 2번 시작 예정**이며 이 PC에서는 문서만 마친다. 다른 PC 에이전트가 HANDOFF를 받고 “테스터 2 시작” 지시 뒤 실제 접속 URL·backend health를 확인하고, 사용자의 새 게임 시작 시 attempt_id·시작 시각을 기록한다. 사람 표본은 아직 미수집이다. Ollama RM1 실패 이력은 보존하고 Gemini 의미 정확도는 아직 성공으로 기록하지 않는다.

- **생성한 단서 이미지 6장 게임 연결 완료** — BGM·음성 대사를 제외하고 이미지 적용부터 진행했다. `output/imagegen/`의 PNG를 원본 그대로 `frontend/public/assets/clues/`에 복사하고 SHA-256 일치를 확인했다. 아침 쟁반은 비트1, 빈 침상은 비트2, 검진 전후 두 장은 비트4, 저녁 쟁반은 비트5에 배치했다. 폐쇄 방송 그림은 실제 밤 결과가 `closure`일 때만 표시하며, 낮이나 트럭·고요한 밤 분기에서는 노출하지 않는다.

- **시나리오 데이터와 화면 연결** — `IllustrationDTO`와 `BeatDTO.illustrations`를 추가하고, 회차 시작·비트 전환 API가 현재 비트의 이미지 ID와 관찰 설명을 전달하도록 했다. 프론트는 `imageMap.ts`의 허용 목록에서 파일을 선택한다. 이미지 정보가 없는 구버전 응답이나 등록되지 않은 ID에는 기존 비트 배경을 사용한다. API 계약 문서도 갱신했다.

- **이미지 열람 UX** — 검진 두 장을 ‘이전 장면 / 다음 장면’ 버튼으로 넘겨 보도록 구현했다. 이미지 열람은 게임 시간이나 발화 예산을 소비하지 않고, 비트가 바뀌면 첫 장으로 초기화한다. 그림은 `object-contain`으로 전체를 표시한다. 모바일에서 하단 버튼에 포커스가 갈 때 그림까지 옆으로 밀리는 문제를 재현해, 대화 영역의 가로 스크롤을 분리했다.

- **그림 설명과 세계 설정의 정합성 점검** — 설명은 그림에서 관찰 가능한 모습만 담고, 쟁반의 주인·질병 확산·검진 결과를 임의로 확정하지 않았다. 독립 리뷰에서 마지막 회차에 소거되는 인물의 이름이 빈 침상 설명으로 다시 노출되는 문제를 발견했다. 실패하는 회귀 테스트로 재현한 뒤, 이름 없는 관찰 문장으로 수정했다. 방송 문구·채점 규칙은 변경하지 않았다.

- **검증 완료** — 엔진 전체 **188 passed**(별도 `pigfarm_test` DB·fake LLM, 기존 의존 라이브러리 경고3건), 아키텍처 계약4개 유지, 코어 금칙어0건, TypeScript 검사 통과. 실제 프론트·PNG와 모의 API로 장면 순서, 두 장 열람, 비트 전환 초기화, 구버전·미등록 ID 대체, 폐쇄/트럭/고요한 밤 분기, 390px 화면의 이미지 경계를 검증했다. 기존 5회차 결말·회고·재시작 브라우저 테스트도 통과했으며 브라우저 실행 오류는0건이다. [검증 결과·스크린샷](review-verification/2026-09-09-images/README.md)

- **인수인계 갱신과 남은 작업** — [HANDOFF.md](HANDOFF.md)에 이미지 적용 완료와 검증 결과를 기록했다. BGM·음성 대사는 이번 요청에서 제외했다. 오디오를 제외한 다음 작업은 정답을 모르는 사용자의 첫 플레이 테스트이며, 5회차 완료 후 약50%·집중 플레이 약70% 목표의 달성 여부와 단서 전달 효과를 확인해야 한다. 일부 오답·부정문에 점수를 주는 채점 오판도 추가 검증 대상으로 남아 있다. Git 커밋·푸시는 수행하지 않았다.

## 2026-09-08

- **게임의 목적과 점수 구조 확정** — 멸망을 막는 게임에서 ‘왜 멸망했는지 이해하는 게임’으로 진행 규칙과 안내를 맞췄다. 이해도는 **상황70점(원인35·동기35) + 정체30점**으로 구성하고, 원숭이손의 부작용과 신의개입 규칙 설계는 답안 정답 요건에서 제외했다. 기존 `side_effect` 필드는 저장·응답 호환용0으로 유지한다. 가중치는 초기값이며 첫 플레이 목표 도달 여부는 아직 미검증이다.

- **점수와 무관한 5회차 진행·최종 회고 구현** — 1~4회차에는100%여도 멸망 연출과 신의개입을 거쳐 다음 회차로 진행하고, 5회차 제출이 끝난 뒤에만 판을 종료하도록 변경했다. 최종0%여도 이야기 결말 → 최종 이해도 → 개발 회고를 볼 수 있다. 진행 중 회고는 잠근다. 회고에는 원숭이손 수락, 추천·직접 규칙 등록, 규칙 충돌, 도구 실행의 부작용, 모델 출력 검사 기록을 표시한다. 규칙 등록 수를 실행 성공률로 표시하지 않으며 실제 이행 성공률은 미측정이다. [구현·완료 기록](superpowers/plans/2026-09-08-five-loop-understanding.md)

- **1단계 검증** — 엔진 **179 passed**, TypeScript 검사 통과. 별도 테스트 DB의 실제 API 5회차 완주와, 실제 프론트·모의 API를 사용한 중간100% 계속 진행·최종0%/100% 결말·회고·재시작·회고 조회 오류 재시도를 확인했다. 엔진 테스트의 LLM은 fake이며 실제 채점 정확도 검증과 구분한다. 독립 리뷰에서 중요한 결함은 없었다.

- **자유발화 채점의 입력 손실 수정** — 실제 `gemma3:12b`에서 같은 정답을 다르게 표현하면 **75.6~88.8점**으로 갈리고, 동기를 추가했는데20.4→16.0점으로 낮아지는 현상을 재현했다. LLM 정규화의 축약·동기 누락과 어휘 기반 날조 필터의 동의어 오탐이 원인이었다. 자유서술과 선택한 노트를 **원문 보존 분할**로 처리하고, 8개를 넘는 내용은8번째 항목에 모으도록 변경했다. 요약 모델·날조 필터·사용하지 않는 관련 프롬프트를 제거했으며 `fabricated_dropped`는 호환용 빈 목록으로 남겼다.

- **문장부호 없는 장문의 잘못된 후보 번호 수정** — 입력 보존 후에도 모델이 한 후보 안의 절을 별도 후보로 세어 범위 밖 번호를 반환하고0점 폴백에 빠지는 사례를 확인했다. `matched_index` 출력 스키마를 **실제 후보 번호 enum 또는 null**로 제한했다. 프롬프트 설명을 늘리는 실험은 부분 정답·감정 문장에 과도한 점수를 주어 채택하지 않았으며, 최종 Evaluator 판정 프롬프트와 점수 가중치는 유지했다. 과거 보고의 정확한 ‘장문0%’ 원문·수치 자체를 재현한 것은 아니다.

- **실제 LLM 재검증과 한계** — **13종 × 2회** 진단에서 동등한 정답6표현 모두100점, 부분 정답20.4→동기 추가36.5점, 오답4.4점, 부정문16.0점, 정오 혼합24.8점, 감정만 쓴 답0점을 기록했다. 자동 게이트7개 통과, 반복 편차0%p, 하네스 폴백0건. 최종 엔진 **186 passed**, 아키텍처 계약4개 통과, 독립 리뷰에서 중요한 결함 없음. 일부 오답·부정문의 부분 점수는 여전히 의미 판정의 오판으로 남아 있다. 정답을 알고 작성한 진단 답안의 결과이므로 첫 플레이50~70% 도달률을 입증한 것은 아니다. 기존 플레이 기록 재채점은 하지 않았다. [전체 진단·검증 기록](review-verification/2026-09-08-step2/README.md)

- **초기 정답률 리뷰 작성 후 근거 재검증·정정** — [review.md](review.md)의 초기 분석을 DB·현재 소스·실제 LLM·브라우저로 대조하고 [review-verification.md](review-verification.md)에 정정 결과를 기록했다. 과거65건의 제출 중 통과2건(3.1%)·평균20.3점, 문제 명제4개의 `confirmed`0회, 과거81개 회차의 Planner 폴백은 재현됐다. 다만 초기 로그의 ‘채점기는 문제가 없다’, ‘44.8점이 구조적 상한’, ‘주장8개라100점 불가능’, ‘관리자 방송이 전혀 표시되지 않는다’는 결론은 근거가 부족하거나 잘못된 해석이었다. 동일 후보가 여러 명제와 매칭될 수 있고 검진 방송의 표시 경로도 확인됐다. 참가자 식별 없이 ‘사람 최고41.7점·사람 통과0명’을 확정할 수 없으며, 필터의 비교 대상도 게임 단서 전체가 아니라 자유서술과 선택 노트였다. 이 정정을 반영해 입력 보존·의미 판정·정보 전달을 함께 검증하는 방향으로 개발을 진행했다.

## 2026-09-07

- **데모 환경 기동**: PostgreSQL(5435) → Ollama 모델 워밍(exaone3.5:7.8b·gemma3:12b) → alembic 마이그레이션 + Uvicorn(8500) → Next.js(3500) 4단계 순차 기동. 프론트 `/play` 200 OK, 백엔드 헬스 `db:ok` 확인. 게임 http://localhost:3500/play · 인스펙터 http://localhost:3500/inspector/{attempt_id}
- **실플레이 라운드** (7판 진행, 밤 제출 5회): 평균 총점 **1.7점·최고 8.3점·통과 0건**. 전날 밸런스 조정(캘리브레이션 정답형 100%) 이후 첫 실사용자 라운드였고, 자동 지표와 실플레이가 정반대로 갈렸다 — 9/8 정답률 분석의 직접 계기

## 2026-09-06

- **📌 오늘 마감 총괄 — 플레이테스트 사이클 1일 완주 (테스트 중단 시점 기록)**
  - 흐름: 흥미도·UX 개선 6건(로딩 소개 카드/회상 연출/세계 힌트 은닉·드립, NPC간 대화, 비트당 발화 1회 제한, 신의개입 규칙 UX) → **4페르소나 브라우저 자동 플레이테스트 R2**(16회차, 결함 발굴) → P0 3·P1 5·P2 9 수리 → **재검증 R3**(20회차, 수리 판정) → 핫픽스 3건 → **채점 밸런스 조정**(캘리브레이션 정답형 65→100%·오답형 26→19%·편차 0.0%p) → R3 신규 이슈 3건 수리. 수리 총 23건 + 신기능 6건, 실플레이 39회차, 테스트 **94 → 168 passed**, 코어 금칙어 CI 0건. 전 과정 서브에이전트 위임(플레이 8기·수리 9기), 리포트 v2 아티팩트 발행
  - 검증된 것: 힌트 중복 전달(4/4 페르소나 이해도 L4 도달), NPC간 대화의 단서 견인(구빌드 3회차 52% → 신빌드 1회차 82% 사례), 안내 계층의 행동 유도(스키머 자발 재제출), 하드 리밋·언어/용어 가드 전부 우회 실패
  - **다음 확인거리(미실측)**: 밸런스 조정+금일 수리분의 실플레이 통과율 — R3 점수(33~42%)는 조정 이전 빌드 기준이므로, 다음 세션에서 페르소나 1~2개 짧은 라운드 또는 팀 실플레이로 통과선(50%) 도달 여부 확인 필요. 잔여 P1: 정리 파서 완곡화(UI diff 접근 권장), 캐릭터 소소 결함(플레이어 오호명·잡담 소재 단조), 신의개입 중복 질문 디듀프
- **R3 신규 이슈 3건 수리** (TDD, 백엔드만): ① [P0] 규칙-정본 이원화 — `narration_with_rule_note()`를 도메인 순수 함수로 이동(`rule_rules.py`)·활성 규칙 전체 적용으로 확장(매칭 규칙마다 보정 줄 1개, 같은 대상 중복 문구는 합침), `_make_cause_chain()`의 비트_서술을 보정 통과본으로 교체(신이 읽는 정본도 규칙 이후 세계 — "배급 금지" 다음날 신이 "맞다, 남겼다" 근원 차단). 계획→잡담 경로는 점검 결과 온전(검증 테스트 추가) ② [P0] 직접 쓰기 규칙 경로 — `ADVISOR_MAP_RULE_SYSTEM`에 few-shot 3종("X: Y 금지" 포맷·완전한 문장·실패)과 "가장 가까운 어휘로 옮긴다" 명시, `nearest_action()` 순수 함수(완전→부분 문자열→어간 겹침 최다)로 어휘 밖 action 근사 보정, label 빈 값·구어휘 label은 "{대상}: {행동} 금지/강제"로 합성(본문 소실 등록 차단), 거부 사유를 실패 유형별 고정 인월드 문구 3종으로 교체("사람 하나의 행동 하나로 옮겨 적을 수 없다" 등 — "플레이어"·"스키마" 메타 용어 비노출) ③ [P1] 신의개입 출력 위생 — `render_cause_chain()` 비트 라벨 제거("- 사실"만), `_no_raw_record_check`에 `비트\s*\d` 정규식 추가(answer·detail), option label의 `{`·`}` 미치환 플레이스홀더 거부, "기록은 이렇다"+빈 detail 거부·재생성(`_record_needs_detail_check`). 신규 테스트 17건(교체 1건 포함 18개 작성), **168 passed**, 코어 금칙어 0건
- **재검증(R3) 4페르소나 20회차 완료 + 리포트 v2 발행**: 전원 5회차 doom(최고 33~42%)이나 이해도 4/4 L4 도달. 수리 스코어보드 — 해결: 채점 셈·안내 계층(스키머가 자발적으로 확인 사실 재제출)·언어/용어 가드·하드 리밋·UI 마찰 / 부분: 잡담 되묻기 7/11·규칙 보정 내레이션(최신 1개만 적용)·신의개입 위생("비트N:" 라벨 잔존) / 신규 P0 2건: 규칙-정본 이원화(신이 읽는 기록은 규칙 이전 세계 — "배급 금지" 다음날 신이 "맞다, 남겼다"), 직접 쓰기 규칙 파서 붕괴(동일 포맷도 "스키마 변환 불가" 거부·본문 소실 등록). 코어 프롬프트 금칙어 위반(신의개입 예시 속 "채연"→"아무개") 수정, CI 게이트 0건. 아티팩트 리포트 v2 갱신(R2/R3 비교 매트릭스+캘리브레이션 표+수리 스코어보드)
- **채점 밸런스 조정** (플레이테스트 8판 "정답에 도달해도 21~42%" 문제, TDD+실LLM 캘리브레이션): ① RAG top-3 후보 절단 제거 — 유저 주장(최대 8개)을 전부 심판 프롬프트에 번호 목록으로 투입, `_judge`의 임베딩 랭킹·장애 폴백(`user_claims[:3]`) 경로 삭제(`_cos`·embedding 파라미터 정리, 임베딩 포트는 헬스체크용으로 존속) ② `EVALUATOR_VERDICT_SYSTEM` 개정 — confirmed/partial/none 기준을 1→3 열거형으로 명문화(동의어·비유·구체화=confirmed, 같은 일 절반=partial, 소재만 같음·주어 불일치·반대 주장=none, 각 한 줄 예시) + `EvaluatorVerdictOutput` 필드 순서를 why→matched_index→verdict로 재배열(스키마 제약 디코딩에서 근거 먼저 쓰게) ③ 판정 온도 0 — `LLMPort.complete`에 `temperature` 선택 인자 추가(하네스 경유), evaluator_verdict만 0.0(나머지 롤 0.7 유지). 셀 곡선(partial 0.5·만점 0.8)·PASS_THRESHOLD 50은 무변경. 신규 `scripts/run_scoring_calibration.py`(골든 세트 3종 오프라인 러너): 조정 전 정답형 65.3/절반형 56.9/오답형 25.7 → 조정 후 **정답형 100.0/절반형 56.9/오답형 19.4, 2회 반복 편차 0.0%p**. 신규 테스트 2건, **151 passed**
- **REMAKE DAY 재검증(R3) 결함 3건 수리** (TDD, 백엔드만): ① 신의개입 답변 JSON 원문 노출 — 원인 체인을 `render_cause_chain()`으로 "- 비트N: 사실" 자연어 렌더(answer·options 양쪽) + `ask()` 하네스에 raw_record 검사(`{`·`}`·`[`·`]`·`"fact"`·`"beat"` 거부·재생성) ② 규칙이 표시만 되고 행동 미반영 — 도메인 순수 함수 `enforce_rules_on_plan()`(suppress→중립 행동 치환, enforce→when_beat/비트3 삽입·치환, Planner 폴백에도 적용), suppress 규칙과 모순되는 정적 내레이션에 결정적 보정 줄("— 오늘은 다르다…") 덧붙임, Agent·ambient 프롬프트 규칙 섹션을 최상단 "오늘의 법"으로 이동 ③ 규칙 후보 label 메타 문장("플레이어가 질문하며…") — 프롬프트 label 형식 제약 + label_meta 하네스 검사(행동 어휘 자체는 관용). 신규 테스트 15건, **149 passed**
- **플레이테스트 P2 9건 수리** (서브에이전트 2기 병렬): [백엔드] 잡담 소재 제약(바깥 물건·음식 금지, 완전한 문장 강제) · `korean_only_check` 하네스 신설(영어 전환 거부·재생성) · 규칙 후보 중복 방지(기존 규칙 프롬프트 주입+검사+폴백 제외) · 소실 인물 부재 안내를 `CharacterDTO.lost`에서 엔진이 도출(`absent_note` — "충식은 지금 여기 없다") · 시스템 용어 5종(체크포인트·게임·플레이어·NPC·레벨) 금칙 추가, 신규 테스트 11건 **134 passed**. [프론트] 주장 textarea ctrl+a 가드+"모두 지운다" 버튼 · 신의개입 Q&A 40vh 스크롤 영역화(입력창 위치 고정+자동 포커스) · 아침 "다섯 밤 중 N번째" 표시 · 노트 중복 표기 제거, tsc 통과. 서버 재기동
- **플레이테스트 P1 5건 수리** (서브에이전트 2기 병렬 — 백엔드/프론트 분리): [백엔드] ① Normalizer 규칙 7·8 추가 — 인과·결론 문장("원인은 ~다") 최우선 보존, 단정문에 헤지("~인 듯") 삽입 금지 ② NPC간 잡담을 두 화자의 memory에 주입("{이름}: {말}") — "방금 네가 한 말" 추궁이 통하게 됨. [프론트] ③ 밤 진입 안내 "오늘 밤 적은 것만 세계가 읽는다"(채점 리셋 오해 방지) ④ 클리어 등급 문구 "세계가 당신을 기억하기로 했다. 아직 전부 이해한 것은 아니지만."(승리가 패배로 읽히던 문제) ⑤ 2회차+ 아침 예산 감소 안내 + 방송 팝업 중 입력 비활성·안내 + 주장 8개 상한 캡션. **123 passed**, tsc 통과, 서버 재기동
- **플레이테스트 P0 3건 수리** (서브에이전트 2기 순차, TDD): ① 채점 매칭 — 심판이 matched_user_claim 문자열 인용 대신 후보 번호(matched_index) 반환, 범위 밖은 하네스 거부. "N개 주장이 닿지 않았다" 상시 오출력 근원 제거 ② 신의개입 — 원인 체인 입력을 세계 사건 5종(발화·도구·매니저·원숭이손·규칙)으로 필터(`chain_source_events`), 유저 주장 에코 차단, 빈 체인은 LLM 미호출 "그건 알 수 없다"("[]" 노출 방지) ③ 규칙 세계 반영 — chatter 프롬프트에 화자별 규칙 주입("세계의 법"), Agent 프롬프트에 준수 강화 2문장, start_loop 응답 `active_rules` + 아침 화면 "오늘 세계에 걸린 규칙" 표시. 신규 테스트 7건, **121 passed**, tsc 통과, 서버 재기동
- **4페르소나 브라우저 플레이테스트 완료** (정독가·스키머·롤플레이어·미니맥서 × 최대 5회차 = 신빌드 16회차 실측, 클로드 크롬 자동 플레이): 정독가만 1회차 82% 클리어(chatter 효과 — 구빌드 3회차 52% 대비 급상승), 나머지 3인은 5회차 멸망(최고 38~41%)이나 전원 "가축(돼지)" 정체 근처 도달 → 힌트 중복 전달 설계 검증. P0 3건 특정: ① 채점 매칭이 matched_user_claim 문자열 정확 일치라 "N개 주장이 닿지 않았다" 상시 오출력(night_interactor.py:311) ② 신의개입 규칙이 내레이션·NPC에 미반영(가설→개입→관찰 루프 절단) ③ 원인 체인에 유저 주장 이벤트가 흡수돼 신이 내 문장을 에코 + 빈 체인 "[]" 노출. P1: Normalizer 인과 주장 드랍, 채점 규칙 무설명(회차 리셋·클리어 문구), chatter가 NPC 기억에 미주입, 방송 오버레이 무피드백 입력 차단. 리포트 아티팩트 발행
- **NPC간 대화(chatter)로 ambient 확장** (사용자 제안: 유저 질문 없이도 NPC들끼리 대화로 힌트가 흐르는 리듬): 비트 경계 1인 한마디 → 로테이션 2인의 2~4줄 주고받기로 교체. AmbientOutput을 lines[{name,line}]로 개편(+text_all 프로퍼티로 하네스 필드 검사 재사용), 화자 명부 검사(짝 밖 이름 거부) 추가, 줄마다 UtteranceEvent 기록(원인 체인·신의개입 재료로 흡수), 두 화자 금칙어 합집합 적용. 프론트는 줄마다 ambient 말풍선. TDD(2건 신설·1건 교체), 114 passed. 서버 반영은 진행 중인 페르소나 플레이테스트 종료 후 재기동으로
- **손상 연출이 하단 UI를 잘라먹던 문제** (3회차 실플레이 스크린샷: 입력줄 반토막·우측 말풍선 잘림): damage-1~3의 `scale(1.015~1.035)` 확대가 가장자리 콘텐츠를 뷰포트 밖으로 밀고 overflow-hidden이 잘라낸 게 원인. 확대를 축소(0.993/0.985/0.978)로 반전해 회전·밀림 초과분을 안쪽으로 흡수 — 기울기 연출은 유지, 가장자리에 종이색 여백이 얇게 보이는 게 오히려 "판 밀림" 느낌. 코너 변위 계산으로 단계별 흡수량 검증
- **다음 하루 준비 대기에 세계 힌트 드립** (사용자 제안): 규칙 적용 후 "다음 하루를 준비하는 중" 화면에 앰버색(`--orange` #c8722e — 조명·스피커 램프 색)으로 세계 힌트 6종을 2.8초 간격 순환 — "손목의 번호는 이름보다 먼저 있었다", "이송된 사람이 돌아온 적은 없다" 등 은유 수위(진입 카드와 동일 기조). 전부 시나리오에 실재하는 관찰 사실 기반
- **신의개입 규칙 단계 UX 2건** (사용자 피드백): ① 후보 3개가 늦게 떠서 직접쓰기만 있는 줄 아는 문제 — 후보 도착 전엔 입력창 숨기고 "세계가 규칙 후보를 고르는 중…" 표시, 도착 시 후보+입력창 동시 등장 (후보 프리페치는 불가 — 질문 3개가 후보 생성 입력이고 1회 캐시라 질문 반영이 굳음) ② 규칙 선택 후 무반응이라 재클릭하는 문제 — 적용 성공 시 "세계에 규칙이 걸렸다: {규칙} / 다음 하루를 준비하는 중…" 화면으로 전환해 버튼 제거, 검토 문구도 "세계에 규칙을 적용하는 중…"으로. GodScreen 단일 파일, tsc 통과
- **비트당 NPC 발화 1회 제한** (사용자 피드백: 1비트에 채연 4회 몰아 쓰고 나머지 비트 스킵하는 플레이 관측): 발화 예산 8회·비트 넘기기 무료는 그대로 두고, 같은 비트에서 같은 NPC 재발화만 차단 — 6비트에 발화를 분산시켜 하루 전체를 쓰게 유도. `npc_states.uttered_beat` 컬럼 추가(알렘빅 마이그레이션), utter()에서 검사·기록, NPC 목록·발화 응답에 `uttered` 플래그. 프론트: 말 건 NPC 탭 흐림+✓, 입력 비활성 "이번 비트엔 이미 말을 걸었다". TDD 신규 2건 + 같은 비트 연속 발화를 전제하던 기존 테스트 3건 재구성(의심 임계는 문턱 시드 방식으로), 113 passed, 서버 재기동
- **진입 세계 카드에 큰 힌트 은닉** (사용자 제안: "영화는 이미 답을 말해준다"): 로딩 소개 카드 첫 장을 분위기 설명에서 은유 힌트로 교체 — "방송은 이름을 부르지 않는다. 머릿수를 센다. 트럭은 무언가를 싣고 온 적이 없다 — 실어 갈 뿐이다." 무심코 읽으면 세계 설명, 집중하면 가축 운반 구조가 보임. 수위 3안(은유/반직설/암시 최소) 중 은유 채택
- **신의개입 열린 질문 대응** (실플레이 스크린샷: "또 누가 남겼어?"에 "맞다" 답변 — 예/아니오 4택 스키마가 원인): 답변 유형 "기록은 이렇다" 추가(5택). 프롬프트에 질문 종류 구분(확인 질문=맞다/틀리다, 열린 질문=기록 서술) + "말고·외에·빼고" 제외 처리("채연 말고 누가?" ↔ 기록엔 채연뿐 → 그런 일은 없었다) 명시. detail 있는 기록 답변은 확인 노트 적립(밤 정리 재료). TDD로 유스케이스 테스트 2건 신설(FakeLLM 큐), 111 passed, 서버 재기동. 실 LLM 검증은 다음 멸망 회차에서 확인 예정
- **밤 채점 대기를 낮 대화 회상 연출로 전환** (사용자 제안): "세계가 답안을 읽고 있다" ~12.5초 동안 주장 목록 대신 낮에 각 NPC에게 말 건 문답 쌍("민석에게 — …" / "민석 — …")을 2.5초 간격 순환. DayScreen log에서 유저 발언+직후 NPC 답변만 짝지어 `onDayDone(dialogue)`로 올리고 play/page 경유 ConfirmScreen에 전달. 대화가 없으면 기존 연출 유지, 제출 중 헤더 "하루를 되짚는다" 전환 + 편집 버튼 숨김. 프론트 3파일, tsc 통과
- **진입 로딩을 소개 카드 연출로 전환** (사용자 제안: 대기 시간을 정보 습득으로 체감시키기): "하루를 준비하는 중…" 한 줄만 깜빡이던 startLoop 대기 구간에 인물·장소 소개 카드 5장(이곳·채연·민석·은상·준)을 2.2초 간격 순환 — NPC 초상(calm) + 표면 관찰 정보 한 줄. 정체·병명 등 추리 대상은 스포일러라 문구에서 배제, 로딩 완료 시 즉시 아침 전환. `EntryScreen.tsx` 단일 파일 수정, tsc 통과
- **덧붙임(날조) 검사 완화** (팀 플레이테스트 난이도 이슈 — 14밤 제출 0통과·평균 7.3%의 주범): 파편을 탭해 서술을 보태면("소독약 냄새" → "소독약 냄새가 코를 찔렀다") 통째로 날조 판정되던 단어 단위 전수 대조를 TDD로 완화 — ① 동사·형용사 활용형("찔렀다"·"들린다")은 명사 후보에서 제외 ② 외자 명사+조사("코를")는 검사 제외 ③ `is_fabricated_claim()` 신설: 명사 날조 2개 이상일 때만 주장 폐기(부사 1개는 관용). 실플레이 드롭 사례 3건을 테스트로 재현 후 통과, 전체 109 passed, 서버 재기동 반영. 세션 강제 종료로 테스트 작성(RED)까지만 된 상태에서 재개해 구현(GREEN) 완료
- **흥미도 개선 일괄 반영** (서브에이전트 3병렬: 백엔드·프론트·시나리오)
  - 백엔드: 밤 채점 verdict 병렬화(ThreadPool 4) + Manager 점검 비트 2·4·6 한정 → 비트 넘기기 0.4~6s, 밤 제출 12.5s 실측 / NPC 능동 발화 `ambient`(비트 경계 로테이션, 하네스 통과) / 파편 실시간 발견 `note_found` / 정성 피드백 `cell_feedback`("원인은 조금 잡혔다…" — 은/는 조사 자동) / `wrong_claim_count` / 부작용 흔적 `aftermath`. 테스트 96→107
  - 프론트: 새 필드 5종 렌더(ambient 점선 말풍선·노트 적립 라인·아침 aftermath·점수 피드백) + 대기 연출(비트 "스피커가 지직거린다…" 순환, 밤 "정리→대조→판정") + 신의개입 질문 예시 플레이스홀더
  - 시나리오: 비트 서술 6개 사건형 전환, NPC별 열리는 화제 4종(민석=규정·준=숫자·은상=남얘기·채연=회피), 유도 화법 힌트 파편, 은상·준 미끼 relations
  - 실주행: ambient "채연 — 밥 못 먹어도 괜찮아."(무심코 새는 단서) 확인, CI 초록 유지. 교훈: 서버 재시작 시 stale pid로 구버전이 계속 서빙된 사고 1회 — pgrep 확인 후 재기동
- 신의개입 부분 일치 완화: 표현이 달라도 같은 일이면 "맞다" + detail에 기록 원문 (실검증: "방송실에 갔어?" → 맞다 | "방송실 근처를 서성거렸다")
- **신의개입 전멸 "그건 알 수 없다" 수정**: 원인 체인에 플레이어 질문만 있고 세계 사실이 없던 게 원인 — ① `utterance` 이벤트에 NPC `reply` 필드 추가(부록 C 확장) ② 체인 생성 입력에 비트 서술 포함 ③ 체인 프롬프트에 "대답 포함·시스템 용어 금지" 명시. 실검증: "채연이 오늘 밥 남겼어?" → **맞다**·"채연이 식사를 남겼다" / "왜" 질문은 여전히 알 수 없다(의도된 동작)
- **없는 인물 날조 차단** (실사례 "옆 사람은 민수야."): ① Agent·ask_npc 프롬프트에 인물 명부 고정("이게 전부다") ② 하네스에 unknown_person 검사 추가 — 명명 어법(X야/X예요/X가 그랬) 패턴에서 명부 밖 이름 검출 시 재생성. 기획서 8.6의 "없는 인물 언급 거부" 구현 완성. 테스트 2건 추가(96 passed)
- 신의개입 화면: 흰 수평선(J01 연출)이 규칙 후보 텍스트를 가로지르던 것 → 콘텐츠 영역에 bg-void를 깔아 선이 뒤로 숨게 (선은 양옆에만 보임)
- 멸망 전환 대사 가독성: 문틈 빛(H01) 위에 겹치던 텍스트 → 하단 배치 + 검정 그라데이션 스크림 + 텍스트 섀도. 클리어·멸망 종료 화면에도 섀도 적용. 캐릭터 카드 폭 112→192px
- **대화 화면 시안 반영** (사용자 스케치): 상단 60% 메인 이미지(비트 일러스트 전체) + 하단 밴드를 좌측 캐릭터 카드 4장(밴드 높이 채움) / 우측 대사·채팅 패널로 분할 — 비주얼노벨식. 우측 하단 대형 초상은 카드가 커져 제거
- **프론트 화면 점검·수정** (브라우저 실플레이 점검, 사용자 피드백 반영)
  - 대화 헤더: C군 일러스트가 176px 띠로 잘리던 것 → 전체 노출(contain, h-48~64) — 원본 종이색 테두리가 배경과 이어짐
  - NPC 초상: 24×32px → 60×80px 세로 탭 + 우측 하단 대형 인물 초상(선택 인물·mood 반영, xl 이상)
  - 아침 화면: 작은 박스 이미지 → B군 풀블리드 배경 + 텍스트 오버레이
  - 손상 transform이 만들던 화면 밀림·스크롤바 → overflow-hidden 래퍼 + scale 보정
  - 밤 배경(I01 세로형)이 좌측 띠로만 보이던 것 → object-bottom 크롭
  - 진입 로딩 표시("하루를 준비하는 중…") 추가, 신의개입 세로 중앙 정렬
  - 인프라: next dev를 파이프 없이 재기동(SIGPIPE로 죽던 문제), 빌드는 tsc로 검증
- **MVP 야간 압축 실행** (사용자 위임: 자동 승인·서브에이전트 모드·아침 데모 목표)
  - 신규 문서 반영: 작업지시서 v1.1 + 모델구성·정책프롬프트 v1 (로컬 ollama exaone3.5:7.8b + gemma3:12b + gemini 임베딩 확정)
  - 백엔드 P1~P5 전체 구현: 상태 머신·Agent/Planner/Manager/Advisor/Normalizer/Evaluator·하네스 8검사·원숭이손·쿠키·재도전·인스펙터. 테스트 48→87, CI 초록 유지
  - 프론트엔드 F0~F2 (서브에이전트): Next.js 16, /play 단일 상태 머신 화면 10종, 이미지 45장 매핑, 빌드 통과 — http://localhost:3500/play
  - 실 LLM 통합 스모크: 발화 2s·밤 채점 15s, 1회차 멸망→신의개입→2회차 진입 실주행 확인
  - `start_demo.sh`/`stop_demo.sh` + `docs/demo_guide.md` 작성
  - P6 검증 러너 5종 완성 + 실측: 하네스 누설률 ON 0% vs OFF 40%(ablation 성립), 판정 일치율 100%, exaone 7세 체크 2/5(3턴 망각 실패 — 게이트 풀런 필요), metrics.yml 가동
  - P7 감사 시나리오(scenario_audit) 완성: engine 수정 0줄, audit E2E 통과 — 방어선 ⑤
  - 최종: pytest 94 · CI 초록 · 데모 가동 중 (백엔드 8500 + 프론트 3500)
- P1 설계서 작성 (`docs/design/P1-day.md`) — 모델정책 v1로 일부 대체됨 (delta 방식)
  - 상태 머신(attempt→loop→beat→night_pending), 의심 0|4|12·신뢰 0|6 단계값 절충안, 하네스 3단 파이프라인(재생성 2회→폴백), ScenarioPort 확장 6종, 신규 테이블 4+시드 1, 테스트 14항목
- **P0 뼈대 구현 완료** (설계서 승인 → 옵션 A 확정)
  - `apps/engine`: 포트 6종 + fake 어댑터, 이벤트 로그(단일 JSONB 테이블 + DTO 17종), 헬스, 시드 upsert 유스케이스
  - `apps/scenarios`: scenario_example(중립 더미) + scenario_a(인물 6·비트 6·정답 주장 10·쿠키 12·금칙어 10) — 시나리오 시드는 서브에이전트로 병렬 작성
  - 검증: pytest 48 통과, import-linter 4계약 0위반, 코어 금칙어 0건, 실기동(8500) /health 정상 + 시드 DB 반영
  - Alembic 초기 마이그레이션(테이블 7개), `pigfarm-db`(pgvector, 5435) 가동, `apps/dummy` 삭제
  - 상세 실측값·결정 9건은 `docs/devlog.md` 참조
- 사용자 결정: GitHub 보류(로컬 CI만), GEMINI_API_KEY 입력됨, 프론트 자료 위치 공유(이미지제작서 2종 + frontend/docs 이미지)

## 2026-09-05

- P0 설계서 작성 (`docs/design/P0-skeleton.md`) — 승인 대기
  - 포트 6종 시그니처, fake 어댑터, 이벤트 로그 옵션 A/B(단일 JSONB 테이블 추천), 시드 upsert 정책, CI 4종, 테스트 8항목
- docker-compose.yml 작성: 다른 프로젝트 규칙(pgvector pg17, `{프로젝트}-db`, 127.0.0.1 순차 포트) 따라 `pigfarm-db`를 **5435**로 분리 (5432·5433·5434 사용 중)
- `backend/.env` 작성: DATABASE_URL(5435), provider 스위치 전부 fake, `GEMINI_API_KEY` 자리 마련 (사용자가 키 입력 예정)
- REMAKE DAY 작업지시서 v1 + 기획서 v8.1 검토, 백엔드 구현 브레인스토밍
  - 구조: 지시서 §3의 `engine/`을 `apps/engine` 단일 앱으로, 시나리오는 `apps/scenarios/{example,a,audit}`에 ScenarioPort 어댑터로 (P7 "engine diff 0" 증명 용이)
  - LLM: 역할 무관 단일 LLMPort + 컴포지션 루트에서 역할별 프롬프트·provider 조합. 전 역할 `fake` 우선 — 로컬 모델 선정은 P6 벤치마크까지 보류 가능
  - 이벤트 로그: 단일 events 테이블(JSONB) + Pydantic 스키마 17종 추천 (P0 설계서에서 확정)
  - DB: Postgres + pgvector (임베딩 1,536차원, 노트 검색·채점 RAG 인덱스 공유)
  - 다음 단계: `docs/design/P0-skeleton.md` 설계서 작성 → 승인 → P0 구현
- `com.remakeday` 프로젝트의 뼈대를 `demo.pigfarm`으로 마이그레이션 (`.git`, `__pycache__` 제외)
  - backend: FastAPI 헥사고날 아키텍처 템플릿 (`apps/dummy` 모듈, `core/matrix`, `main.py`, `requirements.txt`)
  - frontend: 문서(`docs/CLAUDE.md`)와 `.env.local` 초기 상태
  - 루트: `CLAUDE.md`, `docker-compose.yml`, `docs/`, `.env`, `.gitignore`, `.claude/settings.json`
- 로컬 포트 확정: 프론트엔드 **3500**, 백엔드 **8500** — `frontend/docs/CLAUDE.md`에 반영
- 작업 로그 규약 수립: 하루 단위로 `docs/jekyll.md`에 기록

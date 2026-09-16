# 연결형 추리 통합 검증 보고

날짜: 2026-09-09  
담당: `/root/integration`  
상태: **fake API·실제 UI 통합과 Gemini/Ollama adapter 포함 backend 325개 suite 통과. 실제 Gemini 생성 전환은 미완료, Ollama RM1 실패를 공개한 테스터2 preview 기동.**

이 보고서의 자동 실행은 사람 첫 플레이 자료가 아니다. 운영 DB `game_db`과 운영 백엔드 8500은 사용하거나 변경하지 않았다. 실제 HTTP 검증은 가드된 `test_db`와 fake provider를 사용하는 8501에서만 수행했고, 기존 사용자 판은 재채점·재설정하지 않았다.

## 실행 경계

- 가드 launcher는 시작 전에 URL의 DB명과 SQL `current_database()`가 모두 `test_db`인지 확인하고, NPC/core provider가 모두 fake인지 확인했다. 비밀값을 저장하지 않은 attestation은 API 보고서 안에 복사했다.
- 검증 당시 `/health`: scenario `a`, harness `on`, DB `ok`, NPC `fake:exaone3.5:7.8b`, core `fake:gemma3:12b`, embedding `fake`.
- 프론트엔드는 기존 `http://localhost:3500` 개발 서버를 사용했다. API 요청만 Playwright route로 8501에 보냈다. 다른 작업자가 소유한 서버를 재빌드·재시작·종료하지 않았다.
- 실제 Ollama 검증은 DB 없는 in-memory repository에서 별도 실행했으며, 상세 내용과 원문은 [실제 모델 보고](real-model-report.md)와 `real-model-artifacts/`에 둔다.
- 사용자 재플레이용 기존 8500 listener는 [read-only health](integration-artifacts/production-health.json)에서 HTTP 200, scenario `a`, harness `on`, real Ollama 두 모델, DB `ok`를 반환했다. 판 생성이나 DB 변경 없이 그대로 두었다. 실제 frontend는 `http://localhost:3500/play`에 유지돼 있다.

## fake API 5회차

가드된 실제 HTTP API에서 test 판 `6cd879cb-767c-4810-82d4-e9099ef42867`을 5회차까지 진행하고, 재도전 판 `ed4a17da-d316-493b-88da-ef50e86daef3`을 생성했다. [요약](integration-artifacts/live-api/report.json)의 **25개 assertion이 모두 통과**했고 [117개 요청·응답 원문](integration-artifacts/live-api/traffic.json)을 그대로 보존했다.

확인한 범위:

- 매 회차 공개 관찰의 판·회차·비트·출처와 노트의 원본 source 연결
- 1–4회차 점수와 무관한 계속 진행, 5회차의 `is_final=true`와 결말 문장
- 직전 확인 화면 최종 편집본과 선택 근거 복원, 3회차 이후 inherited ID·본문 비중복
- 12개 테스터1 질문의 요청/응답·예산, 맥락 후보의 근거·이유·기대 관찰
- 알려진 출처 규칙의 미리보기→원문 불일치 적용 거부→동일 원문 명시 적용
- 실제 규칙 기회/행동/결과, 민석 기록 금지 뒤 clue-08 비노출, 원숭이손의 설명 이득과 연결된 발화 여유 대가
- 관리자 방송의 매 회차 beat 1 배급/검진/보고 안내와 beat 4 검진, beat 6 소등 연결
- clue-07은 네 인물이 있는 1회차 beat 1에만 노출. clue-08은 채연·민석과 실제 기록, clue-09는 방송실 접근과 보고 미완료, clue-10은 실제 소문 행동과 진위 불명, clue-11은 준의 띠 관찰, clue-12는 담당자 이동·채연 대기와 결과 미공개 조건으로 노출
- note linkage `154/154`, rule compliance `19/19`. 사람 의미 검토가 없는 question/recommendation/custom/checker 지표는 분모0·값 null·N/A로 유지
- call coverage는 107 calls/291 attempts를 완전 기록으로 표시했고 성공·실패·fallback 원문을 함께 남김

이 실행은 이후 발견된 직접 규칙 이름 부분문자열 문제를 고치기 전 서버였다. 따라서 이 원문의 C3 잘못된 `준` 대안은 발견 증거로 보존하고, 수정 완료 증거로 사용하지 않는다. 같은 이유로 최종 코드 버전의 짧은 API 재검증이 남아 있다.

## 실제 프론트엔드 + fake API

[브라우저 보고](integration-artifacts/live-browser-rerun3/report.json)는 실제 프론트엔드 3500과 실제 test API 8501을 연결했다. 모바일 390×844와 데스크톱 1440×1000에서 각각 하나의 **복합 관찰 시나리오**가 통과했고 page error와 failed request는 0건이었다. 판 ID는 모바일 `b4c12b07-f6ca-4c03-bcd0-d5483afbe889`, 데스크톱 `84ed0510-10af-461a-a4cb-bde26ca4537c`이다.

각 시나리오는 첫날의 낮 노트와 밤까지 진행했다. 낮 노트 열람 전후 발화 예산 불변, E01/E04/E07/E10 고정 초상, beat 1에서 clue-07 확인과 미래 clue-12 비노출, 여섯 사건 이미지 clue-07…12의 관찰 후 갤러리 표시, closure clue-06 비노출, 원본 장면 열기/닫기, 문서 가로 넘침 없음을 확인했다. API 원문은 `live-browser-rerun3/mobile-api.json`과 `desktop-api.json`, 화면은 [모바일](integration-artifacts/live-browser-rerun3/mobile-gallery.png)과 [데스크톱](integration-artifacts/live-browser-rerun3/desktop-gallery.png)에 있다.

실제 UI에서 5회차 전체, 최종0/100, 3회차 연속 답안 복원을 실행했다고 해석하면 안 된다. 그 범위는 실제 API 5회차 검증과 아래 real frontend/mock API 회귀를 결합해 확인했다.

## real frontend/mock API 회귀

- [5회차 결과](integration-artifacts/mock-five-loop/results.json): 14개 assertion, 오류0. 1–4회차 100점 계속 진행, 최종0/100 모두 이야기 결말→개발 회고→재도전, 진행 중 회고 잠금, 390px 흐름을 확인했다. 화면은 같은 폴더의 final/retrospective PNG 4장이다.
- [연결 기능 결과](integration-artifacts/mock-connected/results.json): 세 개의 복합 시나리오, 오류0. 낮 노트의 공개/출처/고정 초상, 최종 편집 답안·선택 근거 복원, 질문·미리보기·명시 적용, 실제 실행 사슬과 N/A 지표를 확인했다.
- 별도 frontend 독립 리뷰는 390px 제어 경계, modal focus/Escape/복귀/inert, 시간 진행 없음, 시간순 비교, 최종 편집 가설 연결, 지연된 이전 답안 복원을 실제 3500에서 재확인했다. 상세 범위는 [frontend-review.md](frontend-review.md)에 있다.

## 이미지 자체와 런타임 조건

[이미지 독립 검토](image-review.md)는 생성된 clue-07…12 여섯 장과 E01/E04/E07/E10 기준 초상을 직접 열어 얼굴·노출된 손·숨은 정답/진단 비노출을 확인했다. 이는 이미지 파일 자체의 통과 판정이다. 현재 회차·등장인물·실제 행동에 따른 노출 조건은 위 fake API와 실제 브라우저 실행이 별도로 확인했다.

경미한 한계도 유지한다. clue-08의 소매 띠 좌우는 정답 근거로 쓰지 않으며, clue-10 한 컷만으로는 이동 순서나 소문의 내용·진위를 확인할 수 없어 실제 사건 서술과 함께 사용한다.

## 실행 중 실패와 해석

- 첫 브라우저 시도는 `127.0.0.1:3500`에서 Next 개발 클라이언트가 hydrate되지 않아 시작 문구 대기에서 종료했다. HTTP 200 SSR만 보였고 API 판은 생성되지 않았다. 프로젝트와 기존 테스트가 사용하는 `localhost:3500`에서 HMR 연결과 POST `/sessions` 200을 확인해 환경 원인으로 판정했다.
- 다음 시도는 monkey-paw 응답 중 잠시 disabled인 버튼을 하네스가 즉시 누르려 해 종료했다. test 판 하나가 생성됐지만 완료되지 않았다. 네트워크 완료 후 활성화를 기다리도록 `/tmp` 관찰 코드만 고쳤고 같은 제품 코드에서 다음 실행이 통과했다.
- 두 실패의 빈 `report.json`은 `live-browser-rerun/`, `live-browser-rerun2/`에 남겨 통과 결과와 구분한다. 제품 결함 통과 증거로 세지 않는다.

## 남은 검증

- Gemini/Ollama adapter 추가 뒤 전체 DB suite는 **325 passed, 3 warnings in 6.49s, exit0**이다. owner pure118과 독립 reviewer adapter targeted18도 통과했다. 경고는 기존 dependency deprecation이다. API 인증·모델 inventory는 성공했지만 `gemini-2.5-pro` generation은404여서 실제 core 전환은 아직 하지 않았다. [adapter progress](adapter-progress.md), [최종 검증 요약](final-validation-summary.txt).
- 실제 Ollama full-corpus raw는 03:58~07:35 UTC의12회를 보존했다. 최종 실행은 harness45, provider output45, accepted45, rejected·오류·fallback0, kind21/21, 원문 quote30개 일치였다. 그러나 SPC2의 명시적 공개 기록에 부정 질문을 supported로 답했고, PC6과 원문 여러 문항의 중간 오분류는 guard가 최종 응답만 보호했다. 별도 진단과 Exaone 비교도 제품 gate가 아니다. **RM1 P1과 기능 전체 의미 승인은 미해결이다.**
- RM1 실패를 품질 승인으로 숨기지 않은 채 테스터2 수동 preview를 위해 최종 prompt 소스를 8500에 기동했다. foreground session `32276`, PID `1478841`에 대해 별도 read-only GET이 scenario `a`, harness `on`, NPC `ollama:exaone3.5:7.8b`, core `ollama:gemma3:12b`, embedding `gemini`, DB `ok`를 확인했다. OpenAPI에는 새 observations/night previous/rule preview 경로가 모두 있고 frontend `http://localhost:3500/play`도 HTTP200이다. 이 확인은 판을 만들지 않았으며 실제 플레이·RM1 해결·품질 승인이 아니다.
- 사람 테스터1 재플레이, 정답을 모르는 새 참가자의 첫 플레이 난이도, 질문·추천·규칙의 체감 효용, 약50%/집중70% 목표, 인과적 개선 효과는 미검증이다. 자동 실행을 그 표본에 합치지 않는다.

## 재현 명령

아래 명령은 별도 `test_db`가 준비되고 가드된 fake 8501과 기존 frontend 3500이 실행 중일 때만 사용한다.

```bash
BACKEND_ATTESTATION=/tmp/demo-integration/backend-attestation.json \
API_BASE=http://127.0.0.1:8501 \
ARTIFACT_DIR="$PWD/docs/review-verification/2026-09-09-connected-implementation/integration-artifacts/live-api" \
node /tmp/demo-integration/api-live-flow.mjs

BACKEND_ATTESTATION=/tmp/demo-integration/backend-attestation.json \
API_BASE=http://127.0.0.1:8501 \
FRONTEND_BASE=http://localhost:3500 \
ARTIFACT_DIR="$PWD/docs/review-verification/2026-09-09-connected-implementation/integration-artifacts/live-browser-rerun3" \
NODE_PATH=/tmp/demo-image-browser/node_modules \
node /tmp/demo-integration/browser-live-observe.cjs
```

가드 launcher와 Playwright 관찰 코드는 임시 검증 도구라 `/tmp`에만 있다. 장기 보존 대상은 이 폴더의 보고서·JSON·PNG 원문이다. DB 접속 비밀은 명령, 보고서, artifact에 기록하지 않는다.

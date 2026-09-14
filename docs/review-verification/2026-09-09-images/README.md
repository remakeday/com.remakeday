# 단서 이미지 연결 검증 — 2026-09-09

생성한 이미지 6장을 해당 장면에 연결했다. BGM·음성은 작업 범위 밖이다.

| 그림 | 표시 위치 |
|---|---|
| 아침 쟁반 | 비트1 |
| 빈 침상 | 비트2, 소거 인물 이름 없는 관찰 설명 |
| 검진 방송 아래 채연 | 비트4 첫 이미지, 기존 방송 팝업 뒤 열람 |
| 검진 도구 옆 채연 | 비트4 다음 장면 버튼 |
| 저녁 쟁반 | 비트5 |
| 폐쇄 방송 | 밤 결과 `closure` 전용 |

## 결과

- 엔진 188 passed, 기존 라이브러리 경고3건. 별도 `pigfarm_test` DB, fake LLM.
- TypeScript 검사 통과. 아키텍처 계약4개 유지, 코어 금칙어0건.
- 새 이미지 API 전달 테스트와 마지막 회차 소거 이름 회귀 테스트 통과. 각각 구현·수정 전 실패도 확인했다.
- [브라우저 결과](results.json): 실제 프론트와 PNG, 모의 API. 현재 비트 이미지, 검진 두 장 열람, 비트 전환 시 선택 초기화, 구버전 응답·알 수 없는 ID의 기존 배경 대체, 폐쇄/트럭/고요한 밤 분기, 모바일 버튼 조작 후 이미지 경계 검사 통과. 브라우저 실행 오류0건.
- [기존 5회차 흐름 결과](five-loop-results.json): 중간100% 계속 진행, 최종0%/100% 결말·회고·재시작 통과.
- 복사한 PNG 6장의 SHA-256이 `output/imagegen/` 원본과 일치한다.

## 화면

- [검진 두 번째 장면 — 데스크톱](checkup-1440.png)
- [검진 두 번째 장면 — 모바일](checkup-390.png)
- [폐쇄 결과](closure.png)

검증 화면의 문장·NPC 수는 모의 API 데이터다. 실제 LLM과 연결한 첫 플레이 난이도·추론 정확도는 이번 검증에 포함하지 않았다. 그림과 설명은 고정 시나리오의 관찰 정보이며, 질병 진단·검진 결과·추가 인물의 식사 거부를 판정하는 새 사건 엔진을 만들지 않았다.

## 재실행

```bash
# backend/ — 테스트 DB를 사용하는 기존 fixture
.venv/bin/python -m pytest tests/engine -q
.venv/bin/lint-imports
bash scripts/check_forbidden_words.sh

# frontend/ — 3500 포트에서 npm run dev 실행 후
./node_modules/.bin/tsc --noEmit --incremental false
NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/scene-illustrations.cjs
NODE_PATH=/tmp/pigfarm-image-browser/node_modules node tests/five-loop-flow.cjs
```

Playwright와 `/usr/bin/google-chrome`을 사용했다. `/tmp` 설치 경로는 환경에 맞춰 다시 준비한다.

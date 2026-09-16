# REMAKE DAY — 이미지 제작서 · 랜딩 2종 (LP)

> 이미지제작서 v1의 부록. 공통 뼈대(0.1)·공통 네거티브(0.2)·팔레트(0.3)·검수 체크리스트(0.5)는 v1을 그대로 따른다.
> 용도: 랜딩 페이지 키 이미지. **A안(LP01)·B안(LP02) 둘 다 제작해 비교 후 채택한다.**
> 소재: 소독약. 표면에서는 "바깥의 병"을 떠받치고, 진실 쪽에서는 방역이며, 구조로는 "매일 닦여서 다시 시작되는 하루"다.

---

## 0. 이 문서만의 규칙

### 0.1 비율

| ID | 비율 | 이유 |
|---|---|---|
| LP01 | 3:2 | 랜딩 스크롤 중반 삽입. 비트 배경(C군)과 같은 관례 |
| LP02 | 16:9 | 데스크톱 히어로. **중앙 여백**(카피가 화면 가운데 앉는다) |
| LP02-m | 9:16 | 모바일 히어로 변형. 같은 장면 세로 재구성, 중앙 여백 |

**중앙 여백 원칙 (랜딩 공통)** — 랜딩 카피는 화면 중앙에 올라간다. 피사체는 좌·우(세로형은 상·하) 가장자리로 밀고, **프레임 중앙 1/3은 옅은 안개나 맨 종이로 비워** 텍스트가 앉을 자리를 남긴다.

### 0.2 예외 승인 2건

v1 불변 규칙에서 이 문서가 의도적으로 여는 예외는 정확히 둘이다. 그 외는 전부 v1 그대로.

1. **LP02의 입간판** — "글자·표지판 금지"의 예외. 단, 글자는 **뭉개져서 판독 불가능한 잉크 얼룩**이어야 한다. 선례는 쿠키 N08(트럭 옆면의 뭉개진 글자). 읽을 수 있는 글자·숫자가 한 자라도 나오면 폐기.
2. **LP02의 방역복 인물** — 관리자 쪽 존재가 처음으로 몸을 갖고 화면에 나타난다(지금까지는 스피커 방송뿐). 세계관 결정 사항으로 기록해 둔다. 얼굴 없음·손 없음 규칙은 그대로 유지 — 후드 뒷모습, 손은 안개와 소매 속.

### 0.3 주황

| ID | 주황이 앉는 곳 | 논리 |
|---|---|---|
| LP01 | 말통 캡 **하나** | 관리자가 보급한 것 |
| LP02 | 방역복 등의 가는 띠 **한 줄** | 이 사람이 곧 바깥에서 온 것 |

둘 다 주황은 한 물건, 한 곳. 그 외에 주황이 새면 폐기. v1 §0.3의 문장을 다시 적는다 — **주황은 유저에게 설명하지 않는다. 주황 = 바깥에서 온 것.**

### 0.4 안개 렌더링 (LP02)

공통 뼈대의 `no gradients`와 충돌하지 않게, 안개는 **하프톤 밀도**로만 그린다. 부드러운 그라데이션 안개가 나오면 리소 인쇄물이 아니게 되므로 폐기.

### 0.5 파일

- 파일명: `img_LP01_stockroom.png`, `img_LP02_disinfection.png`, `img_LP02m_disinfection_v.png`
- 채택본은 `frontend/public/assets/`에 둔다
- 한 장당 4~6개 뽑고 v1 §0.5 체크리스트 + 이 문서 각 장의 추가 체크를 통과한 것만 채택

---

## LP01 · 소독약 창고 (A안) — `img_LP01_stockroom` · 3:2

**용도** — 랜딩 스크롤 중반. "다섯 번의 하루" 설명 구간 옆에 조용히 놓인다. 카피는 붙이지 않거나 최소로 — 이 그림은 설명하면 죽는다.

**노리는 것** — 핵심은 **양(量)**이다. 이 인원 규모에 명백히 과한 소독약. 라벨 없는 동일한 말통이 규격대로 반복되는 선반 — 제도적 차가움과 리소의 반복 패턴이 같은 말을 한다. 드럼통이 아니라 10~20L 플라스틱 말통인 것은 고증(축사·병원의 실제 보관 형태)이자, 개수가 셀 수 있게 보여야 "왜 이렇게 많지?"가 정확히 꽂히기 때문이다. 처음 보는 사람에겐 그냥 창고. 클리어한 사람에겐 두 번째 의미.

```
[공통 뼈대]
A storage room corner: tall steel shelving units against a concrete wall,
seen from low so the second shelf sits at eye level and the top shelf looms.
The shelves are packed with dozens of identical rectangular plastic jerry
cans in strict rows, all unlabeled, all rendered in the same flat navy.
Far more supply than a small shelter would ever need. One single can in the
middle row has a small screw cap in dull orange (#C8722E) — the only color
in the frame. A floor drain grate in the near foreground. The lower third
of the frame is plain concrete floor.
[공통 네거티브 — orange only on the single cap. No labels, stickers, or
markings on any can. No drums, no barrels.]
```

**추가 체크**
- [ ] 말통이 전부 같은 형태다 — 하나라도 다른 모양이면 "반복"이 죽는다
- [ ] 라벨·스티커·마킹이 전혀 없다
- [ ] 주황 캡은 정확히 하나다
- [ ] 드럼통·원통형 배럴로 그려지지 않았다 (사각 말통이어야 한다)
- [ ] 선반이 화면 밖으로 이어지는 느낌이 있다 — 다 보여주면 양이 줄어든다

---

## LP02 · 소독하는 사람 (B안) — `img_LP02_disinfection` · 16:9

**용도** — 랜딩 히어로. entry_lines 세 줄("세계가 이상하다 / 오늘이 지나면, 세계는 멸망한다 / 다섯 번의 하루 안에, 왜 멸망했는지 알아내야 한다")이 하단 1/3에 올라간다. 카피 짝 후보: "아침은 소독약 냄새로 시작된다."

**노리는 것** — 방역 뉴스 사진의 문법(입간판 + 방역복 + 분무)을 대피소 안으로 옮긴 것. 보는 사람에겐 익숙한 전염병 방역 풍경으로 읽혀 표면 서사를 떠받치고, 아는 사람에겐 다른 것이 보인다. **시점은 멀리서 지켜보는 것** — 복도 끝에서 낮게 웅크리고 거리를 둔 채 바라보는 눈. 인물은 멀고 작고, 안개에 반쯤 잠겨 있고, 등을 보인다. 입간판은 도로 방역 통제 때 세우는 **대형 표지판**(다리 달린 가슴 높이 사각판) — 글자는 뭉개진 얼룩. 아무 일도 일어나지 않고 있다 — 그냥 소독 중일 뿐이다.

**구도 규칙** — 입간판과 인물은 **둘 다 원거리**, 같은 깊이쯤에 좌·우로 나뉘어 선다. 전경은 젖은 빈 바닥뿐. 입간판은 칠판처럼 커지면 안 된다 — **허리 높이의 소형 이동식 표지판**이고, 멀리 있으니 화면에서는 작게 잡힌다.

```
[공통 뼈대]
A very wide view of a shelter corridor, watched quietly from far away and
from very low, near the floor — as if someone is crouching at the other
end of the hall, keeping their distance. Disinfectant fog rendered only as
halftone density, never as gradients. The fluorescent tubes are reduced to
soft halos. FAR AWAY down the corridor, both small in the frame at a
similar depth: in the RIGHT THIRD, one figure in a full protective suit
with a hood, seen entirely from behind, spraying mist toward the right
edge, away from the center, hands hidden by the fog and the sleeves, a
thin dull orange (#C8722E) stripe across the back of the suit — the only
color; and in the LEFT THIRD, a compact portable road-control sign — a
small rectangular panel on slim metal legs, waist-high, the kind placed on
rural roads during disinfection control, NOT a blackboard — its printed
marks smeared into illegible ink blots. The near and middle ground is
nothing but empty wet concrete floor faintly reflecting the light halos.
The CENTER THIRD of the frame is the quietest area: fog thinning into
almost plain paper, no objects, reserved for overlay text.
[공통 네거티브 — orange only as the single stripe on the suit. The sign
carries only unreadable ink smears, never letters or numbers. Back view
only, face fully hidden by the hood, no hands, no gloves visible. No
blackboard, no chalkboard, no large billboard.]
```

### LP02-m · 모바일 변형 — `img_LP02m_disinfection_v` · 9:16 · **제작 중단**

> 2026-09-15 결정: 세로 변형은 만들지 않는다. 모바일은 가로판(LP02)을 크롭해 쓴다. 아래 스펙은 기록용.

같은 장면의 세로 재구성. 대형 입간판이 하단, 인물은 상단에 멀리 작게, **중앙 절반은 옅은 안개가 종이로 풀리는 빈 영역**(카피 자리). 시점은 가로판과 동일 — 멀리서, 바닥 가까이 낮게.

```
[공통 뼈대]
The same corridor scene recomposed vertically with a hollow middle, watched
from far away and from very low, near the floor. Disinfectant fog as
halftone density. In the BOTTOM QUARTER, at the left, the LARGE rectangular
road-control signboard on sturdy metal legs, chest-high, its printed
characters smeared into illegible ink blots, standing on wet concrete. In
the TOP QUARTER, small and far away, the hooded figure in a full protective
suit seen from behind, spraying halftone mist, a thin dull orange (#C8722E)
stripe across the back of the suit — the only color. Faint fluorescent
halos at the very top. The MIDDLE HALF of the frame is almost empty: thin
fog dissolving into plain paper grain, no objects, reserved for overlay
text.
[공통 네거티브 — 위와 동일]
```

**추가 체크 (LP02 · LP02-m 공통)**
- [ ] 입간판의 얼룩에서 읽을 수 있는 글자·숫자가 없다 — 한 자라도 판독되면 폐기
- [ ] 인물이 완전한 뒷모습이다 — 마스크·고글이라도 정면 기미가 있으면 폐기
- [ ] 손·장갑이 보이지 않는다
- [ ] 주황은 방역복 띠 한 줄뿐이다 — 분무 안개·형광등·입간판에 주황기가 새면 폐기
- [ ] 안개가 하프톤이다 — 부드러운 그라데이션이면 폐기
- [ ] 공포 연출이 없다 — 인물이 위협적으로 크거나 카메라를 향해 다가오는 구도면 폐기. 소독 중일 뿐이다
- [ ] 하단 1/3(모바일은 상·하단 1/3)에 카피 자리가 비어 있다

---

## 부록. 채택 비교 기준

두 안을 나란히 놓고 본다. 서로 다른 것을 겨냥하므로 "더 잘 나온 쪽"이 아니라 "랜딩의 첫인상을 무엇으로 할 것인가"로 고른다.

| | LP01 창고 | LP02 소독하는 사람 |
|---|---|---|
| 말하는 것 | 단서 — 왜 이렇게 많지? | 분위기 — 이 세계는 관리되고 있다 |
| 첫인상 온도 | 정적, 차가움 | 익숙한 불안 (뉴스 사진 기시감) |
| 스포일러 거리 | 두 번째 의미가 조용히 잠복 | 표면 서사를 오히려 강화 |
| 어울리는 자리 | 스크롤 중반 / clue 전용 겸용 | 히어로 |

둘 다 채택하는 구성도 성립한다 — 히어로 LP02, 중반 LP01. 이 경우 랜딩 한 페이지에서 주황이 두 번 등장하므로, LP01의 캡과 LP02의 띠가 **같은 주황(#C8722E)** 인지 최종 확인할 것.

**총 3장 (LP01 1 + LP02 1 + LP02-m 1). 전부 생성, 후처리 없음.**

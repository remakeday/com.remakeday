# REMAKE DAY — 이미지 제작서 v1

> 기획서 v8 부록 F 기준 · 45장
> 톤앤매너: **복사본의 복사본** — 2도 리소그래프, 낮은 카메라, 얼굴도 손도 없다
> 제작 도구: Gemini / ChatGPT 이미지 생성 → 손상 변형 12장은 후처리

---

## 0. 사용법

1. 모든 프롬프트는 **[공통 뼈대] + [장면]** 으로 조립한다. 공통 뼈대를 먼저 붙여넣고 장면을 이어 쓴다
2. 한 장당 4~6개 뽑고 검수 체크리스트(0.5)를 통과한 것만 채택한다
3. 손상 변형 12장(D)은 생성하지 않는다. 원본 6장(C)을 후처리한다
4. 파일명 규칙: `img_{ID}_{slug}.png` — 예: `img_C01_ration.png`
5. 글자는 그리지 않는다. 생성 모델은 글자를 망가뜨리고, 대피소엔 표지판이 없는 게 맞다

### 0.1 공통 뼈대 (모든 프롬프트 앞에)

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.
```

### 0.2 공통 네거티브 (모든 프롬프트 뒤에)

```
No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
```

### 0.3 팔레트

| 역할 | 색 | 어디에 |
|---|---|---|
| 잉크 | `#1C2340` 남색 | 모든 선과 면 |
| 종이 | `#EDE8DC` 미색 | 배경 |
| 강조 | `#C8722E` 탁한 주황 | **관리자 쪽 것에만** — 스피커 불빛, 트럭 헤드라이트, 원숭이손, 검진 장비의 불 |
| 세계 밖 | `#000000` 검정 + `#FFFFFF` 흰 | 신의개입, 클리어, 멸망 종료 화면 |

주황은 유저에게 설명하지 않는다. 주황 = 바깥에서 온 것. 45장 통틀어 주황이 있는 장면은 8장뿐이다.

### 0.4 비율

| 용도 | 비율 | 이유 |
|---|---|---|
| 비트 배경 (C·D), 아침 (B) | 3:2 | 대화창 위 헤더 띠. 하단 1/3 비움 |
| NPC 초상 (E) | 3:4 | 대화 상대 카드 |
| 전환·전체 화면 (A·H·I·J·K·L·M) | 9:16 | 모바일 전체 화면. 데스크톱은 중앙 배치 |
| 스피커·원숭이손 (F·G) | 1:1 | 팝업 |

### 0.5 검수 체크리스트

채택 전에 전부 확인한다. 하나라도 걸리면 폐기.

- [ ] 손·손가락이 없다 (소매 속, 프레임 밖, 담요 속)
- [ ] 얼굴이 없다 (뒷모습, 어깨선, 그림자, 프레임 밖)
- [ ] 창문·거울·하늘·햇빛이 없다
- [ ] 글자·숫자·표지판이 없다
- [ ] 동물·분홍·짚·울타리가 없다
- [ ] 카메라가 낮다 — 문손잡이가 화면 위쪽에, 배급대가 눈높이에
- [ ] 주황은 지정된 장면에만, 지정된 물건에만
- [ ] 배경류는 하단 1/3이 비어 있다
- [ ] 2도다 — 남색과 미색 외의 색이 새지 않았다

---

## 1. 이미지 목록 — 45장

| 군 | ID | 수 | 내용 |
|---|---|---|---|
| A | A01 | 1 | 진입 화면 |
| B | B01~B03 | 3 | 아침 — 원본 / 판 밀림 / 7시 13분 |
| C | C01~C06 | 6 | 비트 배경 원본 |
| D | D01~D12 | 12 | 비트 배경 손상 변형 (후처리) |
| E | E01~E12 | 12 | NPC 초상 4인 × 3상태 |
| F | F01 | 1 | 관리자 스피커 |
| G | G01 | 1 | 원숭이손 |
| H | H01~H03 | 3 | 멸망 전환 — 트럭 / 조용히 이송 / 폐쇄 방송 |
| I | I01 | 1 | 밤 — 정답 제출 배경 |
| J | J01 | 1 | 신의개입 배경 |
| K | K01~K02 | 2 | 클리어 — 아직 / 이해했다 |
| L | L01 | 1 | 멸망 종료 |
| M | M01 | 1 | 하네스 공개 |

---

## A. 진입 화면 (1장)

### A01 · 진입 — `img_A01_entry` · 9:16

**용도** — 세 줄("세계가 이상하다 / 오늘이 지나면 세계는 멸망한다 / 왜인지 알아내면 막을 수 있다")이 중앙에 올라간다. 그림은 배경. 상단 1/3과 하단 1/3 비움.

**노리는 것** — 아직 아무것도 모르는 사람이 보는 첫 장면. 복도 끝. 낮은 카메라 때문에 복도가 실제보다 길어 보여야 한다.

```
[공통 뼈대]
A long, narrow shelter corridor receding into darkness, seen from very low.
Fluorescent tubes on the ceiling, every second one unlit. Pipes run along the
top of the walls. A closed steel door at the far end, tiny, with a heavy
handle high up. The floor is the largest shape in the frame. Empty. Vertical
composition, upper and lower thirds left plain paper.
[공통 네거티브]
```

---

## B. 아침 (3장)

**용도** — "7시 12분. 눈을 뜬다." 매 회차 첫 화면. 그림은 같은 침상, 같은 천장. B02·B03은 B01의 변형이라 **B01을 먼저 확정하고 같은 시드/참조로 뽑는다.**

### B01 · 아침 원본 — `img_B01_morning` · 3:2

**노리는 것** — 누워서 눈을 뜬 시점. 천장이 전부. 1회차엔 아무 의미 없고 2회차부터 "같다"는 게 의미가 된다.

```
[공통 뼈대]
View straight up from a bunk: a concrete ceiling, one fluorescent tube
running diagonally across the frame, two pipes crossing it, a metal bunk
frame edge at the bottom left. A thin gray blanket edge at the very bottom.
Flat, symmetrical, calm. Nothing else.
[공통 네거티브]
```

### B02 · 아침 — 천장이 조금 낮아 보인다 — `img_B02_morning_shift` · 3:2

**노리는 것** — 손상 1층. 같은 천장인데 뭔가 다르다. 확인할 수 없어야 한다. **후처리 우선**: B01의 남색 판을 아래로 4%, 오른쪽으로 1.5% 밀고 형광등 굵기를 6% 늘린다. 생성한다면:

```
[공통 뼈대]
Same view straight up from a bunk as before: concrete ceiling, one diagonal
fluorescent tube, two crossing pipes, bunk frame edge bottom left. But the
ceiling feels slightly closer — the tube is a little thicker, the pipes a
little lower in frame. The navy layer is offset a few millimeters from the
paper layer, as if the print slipped. Otherwise identical.
[공통 네거티브]
```

### B03 · 아침 — 7시 13분 — `img_B03_morning_713` · 3:2

**노리는 것** — 4회차. 첫 문장이 흔들리는 유일한 아침. 그림은 B01과 거의 같되 **형광등이 꺼져 있다.** 어둡지 않다 — 그냥 불이 안 켜졌을 뿐. 텍스트가 "7시 13분"을 말하고 그림은 아무 말도 안 한다.

```
[공통 뼈대]
Same view straight up from a bunk: concrete ceiling, one diagonal fluorescent
tube, two crossing pipes, bunk frame edge bottom left. The tube is unlit —
drawn only as an outline, no glow. The ceiling is rendered in slightly lighter
ink, as if the print is running out. Still calm. Still nothing happening.
[공통 네거티브]
```

---

## C. 비트 배경 원본 (6장)

**용도** — 대화창 헤더. 하단 1/3 비움. 사람 없음. 이 6장이 D의 원본이므로 **가장 공을 들인다.** 여섯 장이 같은 공간의 다른 구석으로 읽혀야 한다 — 같은 바닥, 같은 형광등, 같은 배관.

### C01 · 비트 1 — 배급 — `img_C01_ration` · 3:2

**노리는 것** — 배급대가 눈높이에 있다(카메라 60cm). 쟁반 하나가 반쯤 남은 채 옆으로 밀려 있다 — 채연의 것. 스피커 주황 불 하나. **주황 허용.**

```
[공통 뼈대]
A long metal serving counter seen from just below counter height, its edge
cutting across the frame at eye level. A row of identical shallow metal trays
on top; one tray, half-full, pushed aside at an angle. Above, on the wall, a
small boxy speaker with a single dull orange light (#C8722E) — the only color.
Steam faintly drawn as halftone. No people.
[공통 네거티브 — orange light permitted only on the speaker]
```

### C02 · 비트 2 — 오전, 침상 사이 — `img_C02_bunks` · 3:2

**노리는 것** — 대화의 대부분이 일어나는 곳. 침상 열 사이 통로. 담요 하나가 정리 안 됨(채연). 손목띠 하나가 침상 기둥에 걸려 있다 — 아무도 안 부르는 번호.

```
[공통 뼈대]
An aisle between two rows of metal bunk beds, seen from low, the upper bunks
looming. Thin gray blankets folded flat on every bunk except one, which is
rumpled and hangs over the edge. A single fabric wristband hangs from a bunk
post, drawn plain, no markings. The aisle floor fills the lower half of the
frame. No people.
[공통 네거티브]
```

### C03 · 비트 3 — 정오, 배급 두 번째 — `img_C03_noon` · 3:2

**노리는 것** — C01과 같은 배급대, 다른 각도. 이번엔 쟁반이 전부 비어 있고 하나만 손 안 댄 채. 민석이 "누가 남기는지 본다"는 비트. 스피커는 보이지만 불이 꺼져 있다. **주황 없음.**

```
[공통 뼈대]
The same metal serving counter from a different angle, seen along its length
from low. All trays empty and stacked at the far end except one, untouched,
still full, alone near the camera. The wall speaker visible at the top edge,
its light off. Long shadow of the counter across the floor.
[공통 네거티브]
```

### C04 · 비트 4 — 오후, 검진 — `img_C04_checkup` · 3:2

**노리는 것** — 검진이 다녀가는 자리. 사람은 없고 장비만. 접이식 철제 탁자, 체온계 같은 막대 하나, 클립보드(글자 없음). 장비 하나에 주황 불 — 검진은 관리자 쪽 것. **주황 허용.**

```
[공통 뼈대]
A folding metal table against a concrete wall, seen from low so the tabletop
is at eye level. On it: a blank clipboard, a small handheld device shaped like
a thick pen with one tiny orange indicator light (#C8722E), a coiled cable.
A single metal stool. A drain grate in the floor in the foreground. No people.
[공통 네거티브 — orange only on the device light]
```

### C05 · 비트 5 — 저녁, 방송실 앞 복도 — `img_C05_evening` · 3:2

**노리는 것** — 민석이 서성이는 곳. 닫힌 문 하나, 문 옆에 스피커. 복도 끝이 어둡다. 은상의 소문이 도는 시간이라 화면이 좀 좁다. **주황: 스피커 불만.**

```
[공통 뼈대]
A short corridor ending at a closed steel door with a small square hatch,
seen from low so the door handle sits near the top of the frame. Beside the
door, a wall speaker with one dull orange light (#C8722E). The fluorescent
tube here flickers — drawn with broken halftone. The corridor narrows toward
the door. No people.
[공통 네거티브 — orange only on the speaker]
```

### C06 · 비트 6 — 소등 — `img_C06_lightsout` · 3:2

**노리는 것** — 어둡지만 검지 않다. 형광등 꺼짐. 침상 열이 실루엣으로. 문 아래 틈이 보인다 — H01의 복선. 틈에서 빛은 아직 안 새어 나온다. **주황 없음.**

```
[공통 뼈대]
The bunk aisle at lights-out, fluorescent tube off, drawn as outline only.
Rows of bunks as flat navy silhouettes. At the far end, the steel door, and
beneath it a wide horizontal gap — dark, nothing coming through yet. The
floor is paper-white, the walls navy. Very few lines. Quiet.
[공통 네거티브]
```

---

## D. 비트 배경 손상 변형 (12장 · 후처리)

**생성하지 않는다.** C01~C06 각각에 두 단계 후처리를 걸어 12장을 만든다. 같은 그림의 불량 복사본이어야 하므로 새로 뽑으면 오히려 틀린다.

### 단계 1 — 판 밀림 (D01~D06) · 3회차부터

| 처리 | 값 |
|---|---|
| 남색 판을 종이 판에서 분리 | 레이어 2개 |
| 남색 판 이동 | 오른쪽 1.5%, 아래 1% |
| 남색 판 회전 | 0.4° |
| 그레인 | 원본 대비 +20% |
| 모서리 | 네 모서리 2% 반경으로 잉크 흐림 |

유저가 알아채면 안 되고, 노트에 적어둔 것과 대조했을 때만 "다른가?" 싶어야 한다.

### 단계 2 — 잉크 빠짐 + 물건 하나 소실 (D07~D12) · 5회차

| 처리 | 값 |
|---|---|
| 단계 1 유지 | |
| 남색 판 농도 | 70% |
| 무작위 영역 잉크 탈락 | 화면의 8~12%, 얼룩 형태 |
| **물건 하나 삭제** | 아래 표 |

| 원본 | D ID | 삭제하는 것 | 의미 |
|---|---|---|---|
| C01 배급 | D07 | 밀려난 쟁반 | 채연의 흔적이 없다 |
| C02 침상 | D08 | 기둥의 손목띠 | 번호가 사라진다 |
| C03 정오 | D09 | 손 안 댄 쟁반 | 아무도 남기지 않는다 |
| C04 검진 | D10 | 클립보드 | 기록이 없다 |
| C05 저녁 | D11 | 스피커의 주황 불 | 관리자가 조용하다 |
| C06 소등 | D12 | **침상 하나** (가장 먼 것) | 충식의 침상. 손상 3층 |

D12가 45장 중 가장 중요하다. 침상이 하나 줄었는데 화면은 아무 말도 안 한다.

파일명: `img_D01_ration_shift` … `img_D06_lightsout_shift`, `img_D07_ration_fade` … `img_D12_lightsout_fade`

---

## E. NPC 초상 (12장)

**용도** — 대화 상대 카드. 3:4. 상태 3개(평상·불안·의심)는 도메인 계층이 계산한 정수로 바뀐다.

**원칙** — 얼굴 없음, 손 없음. 인물은 실루엣과 소지품으로 구분한다. 상태는 몸의 방향으로만 표현한다.

| 상태 | 몸 | 규칙 |
|---|---|---|
| 평상 | 등을 보이되 어깨가 정면. 고개는 안 돌림 | 카메라를 향해 열려 있음 |
| 불안 | 몸이 반쯤 옆으로. 어깨가 올라감 | 벗어나려는 중 |
| 의심 | 등을 완전히 돌리고 고개만 살짝 이쪽 | 얼굴은 프레임 밖 |

| 인물 | 실루엣 | 소지품 | 프롬프트 키 |
|---|---|---|---|
| 채연 | 작다. 담요를 어깨에 두름. 웅크림 | 담요 | `a slight figure wrapped in a gray blanket over the shoulders` |
| 민석 | 곧다. 옷이 정돈됨. 손목띠가 잘 보이는 자세 | 손목띠 (소매 밖) | `a straight-backed figure in a neat shelter uniform, one fabric wristband visible at the cuff, sleeve ending before any hand` |
| 은상 | 움직이는 중. 항상 살짝 흔들림 | 없음 | `a restless figure mid-step, slightly motion-blurred in the halftone, one shoulder higher` |
| 준 | 가장 작다. 소매가 길어서 손목띠를 소매 속에서 만지작 | 긴 소매 | `the smallest figure, oversized sleeves pulled down past the wrists, sleeves bunched as if fidgeting with something underneath` |

**공통 (초상 전용 뼈대, 0.1 뒤에 추가)**

```
Portrait crop, 3:4, waist up. The figure is seen from behind or in
three-quarter back view. The face is never visible — turned away, in shadow,
or cropped by the frame. Hands are never visible — inside sleeves, under
blanket, or out of frame. Background: plain concrete wall with one pipe.
Camera at 60 cm, so the figure is seen from slightly below.
```

### 채연

**E01 · 채연 · 평상** — `img_E01_chaeyeon_calm`
```
[공통 뼈대] [초상 뼈대]
A slight figure wrapped in a gray blanket over the shoulders, seen from
behind, shoulders square to the camera, head not turned. The blanket edge
is pulled tight at the neck. Still.
[공통 네거티브]
```

**E02 · 채연 · 불안** — `img_E02_chaeyeon_uneasy`
```
[공통 뼈대] [초상 뼈대]
A slight figure wrapped in a gray blanket, turned halfway to the side,
shoulders hunched up toward the ears, the blanket clutched closed from the
inside — no hands visible. Slightly leaning away from the camera.
[공통 네거티브]
```

**E03 · 채연 · 의심** — `img_E03_chaeyeon_wary`
```
[공통 뼈대] [초상 뼈대]
A slight figure wrapped in a gray blanket, back fully to the camera, head
turned just enough that one ear and the edge of the jaw show, face out of
frame. The blanket has slipped off one shoulder.
[공통 네거티브]
```

### 민석

**E04 · 민석 · 평상** — `img_E04_minseok_calm`
```
[공통 뼈대] [초상 뼈대]
A straight-backed figure in a neat shelter uniform, seen from behind,
shoulders level, standing at attention. One fabric wristband visible at the
cuff, the sleeve ending before any hand. Posture like someone waiting for a
broadcast.
[공통 네거티브]
```

**E05 · 민석 · 불안** — `img_E05_minseok_uneasy`
```
[공통 뼈대] [초상 뼈대]
A straight-backed figure in a neat uniform, turned three-quarters away,
one shoulder dropped, the wristband arm held slightly behind the body as
if hiding it. Posture still stiff but off-balance.
[공통 네거티브]
```

**E06 · 민석 · 의심** — `img_E06_minseok_wary`
```
[공통 뼈대] [초상 뼉대]
A straight-backed figure in a neat uniform, back to the camera, head turned
sharply to one side, face out of frame. The wristband arm is raised slightly,
as if about to note something. Rigid.
[공통 네거티브]
```

### 은상

**E07 · 은상 · 평상** — `img_E07_eunsang_calm`
```
[공통 뼈대] [초상 뼈대]
A restless figure mid-step seen from behind, slightly motion-blurred in the
halftone, one shoulder higher than the other, weight on one foot. Even at
rest, not still.
[공통 네거티브]
```

**E08 · 은상 · 불안** — `img_E08_eunsang_uneasy`
```
[공통 뼈대] [초상 뼈대]
A restless figure half-turned, drawn with a doubled outline as if it moved
during the exposure, shoulders drawn up, leaning toward the edge of the
frame as if about to leave.
[공통 네거티브]
```

**E09 · 은상 · 의심** — `img_E09_eunsang_wary`
```
[공통 뼈대] [초상 뼈대]
A restless figure with its back to the camera, head tilted toward the
viewer but face hidden, body already angled toward the exit. Halftone
smeared along the outline. Tension without stillness.
[공통 네거티브]
```

### 준

**E10 · 준 · 평상** — `img_E10_jun_calm`
```
[공통 뼈대] [초상 뼈대]
The smallest figure, seen from behind, oversized sleeves pulled down past
the wrists, sleeves bunched together in front of the body as if fidgeting
with something underneath. Relaxed shoulders. Curious posture, head
slightly up.
[공통 네거티브]
```

**E11 · 준 · 불안** — `img_E11_jun_uneasy`
```
[공통 뼈대] [초상 뼈대]
The smallest figure, half-turned, oversized sleeves crossed over the chest,
shoulders raised. Looking down and away. The sleeves hide everything.
[공통 네거티브]
```

**E12 · 준 · 의심** — `img_E12_jun_wary`
```
[공통 뼈대] [초상 뼈대]
The smallest figure, back to the camera, one oversized sleeve raised toward
the wall as if pointing at a pipe, head turned toward it, face out of frame.
Small against the wall.
[공통 네거티브]
```

---

## F. 관리자 스피커 (1장)

### F01 · 관리자 — `img_F01_manager` · 1:1

**용도** — 관리자 방송 시 팝업. 이 세계에서 유일하게 "위"에서 오는 것. 얼굴 없음. **주황 허용 — 45장 중 주황이 가장 크게 쓰이는 장면.**

**노리는 것** — 스피커를 올려다본다. 낮은 카메라라 스피커가 크고 멀다. 주황 불 하나가 켜져 있다. 그게 전부다.

```
[공통 뼈대]
A wall-mounted metal speaker box seen from directly below, filling the
center of a square frame, mounted high on a concrete wall where it meets
the ceiling pipes. Its grille drawn as a halftone grid. One round indicator
light glowing dull orange (#C8722E), the glow bleeding slightly into the
paper grain around it. Nothing else in frame. Symmetrical.
[공통 네거티브 — orange permitted on the speaker light and its glow]
```

---

## G. 원숭이손 (1장)

### G01 · 원숭이손 — `img_G01_paw` · 1:1

**용도** — "무언가가 굴러왔다" 팝업. 받는다/두고 간다 버튼이 아래에 붙는다.

**노리는 것** — 뭔지 몰라야 한다. 손이 아니다. 종이 뭉치인지 천 조각인지 매듭인지. 바닥에 놓여 있고 낮은 카메라라 크게 보인다. 주황 기운만 살짝 — 바깥에서 온 것. **절대 손 모양이 되면 안 된다.**

```
[공통 뼈대]
A small, ambiguous object lying on the concrete floor, seen from very low
so it looms in the center of a square frame: a tightly knotted bundle of
cloth or crumpled paper, roughly fist-sized, its shape unclear. A faint
dull orange (#C8722E) tint on one edge, as if it caught light from
somewhere else. Long low shadow. Nothing else in frame.
[공통 네거티브 — orange permitted as a faint tint on the object only. Absolutely not shaped like a hand, paw, or any body part.]
```

---

## H. 멸망 전환 (3장)

**용도** — 3~5초 전환. 9:16 전체 화면. 사건은 없다. 단절만 있다.

### H01 · 트럭 — `img_H01_truck` · 9:16

**노리는 것** — 가장 흔한 멸망. 문 아래 틈으로 주황 헤드라이트가 샌다. 낮은 카메라라 틈이 크다. 트럭은 안 보인다. **주황 허용 — 틈에서 새는 빛과 바닥 반사만.**

```
[공통 뼈대]
A closed steel door seen from very low, filling the upper half of a tall
frame, its handle far above. Beneath the door, a wide horizontal gap. Harsh
orange light (#C8722E) pours through the gap and spreads across the concrete
floor toward the camera in a long wedge, everything else in navy shadow.
The floor wedge of light is the brightest thing in the image.
[공통 네거티브 — orange permitted only as the light through the gap and its reflection on the floor. No vehicle visible.]
```

### H02 · 조용히 이송 — `img_H02_quiet` · 9:16

**노리는 것** — 이상자가 셋이 되기 전에 유저만 빠지는 경우. 빈 침상 하나. 담요가 반듯하게 개어져 있다 — 방금 정리된 것처럼. **주황 없음.**

```
[공통 뼈대]
A single metal bunk seen from low and close, filling a tall frame. Its thin
gray blanket folded perfectly flat and square at the foot, the mattress
bare. The bunks around it are only edges at the frame's border. Fluorescent
light steady. Nothing missing except a person.
[공통 네거티브]
```

### H03 · 폐쇄 방송 — `img_H03_closure` · 9:16

**노리는 것** — 소문이 임계를 넘어 방송으로 끝나는 경우. F01의 스피커가 켜진 채 나머지가 검게 잠긴다. **주황 허용 — 스피커 불만.**

```
[공통 뼈대]
A tall frame almost entirely navy — the shelter at lights-out. Near the top,
the wall speaker box, its single orange light (#C8722E) on, the only light
in the image, casting a faint cone of halftone down the wall. The floor at
the bottom barely visible as a lighter band. Everything else swallowed.
[공통 네거티브 — orange only on the speaker light]
```

---

## I. 밤 — 정답 제출 배경 (1장)

### I01 · 정답 제출 — `img_I01_night` · 9:16

**용도** — "오늘은 무슨 상황이었나요? 왜 멸망하나요?" 노트 패널과 서술창이 위에 올라간다. 배경은 거의 비어야 한다.

**노리는 것** — 아직 이 세계 안이다(남색·미색). 하지만 아무것도 없다. 소등된 복도 바닥만. 텍스트가 주인공.

```
[공통 뼈대]
A tall frame showing only the shelter floor at lights-out, seen from very
low: concrete texture rendered in sparse halftone, a single drain grate
near the bottom, the base of one wall along the left edge. No light source.
Ninety percent of the frame is plain paper grain. Extremely minimal.
[공통 네거티브]
```

---

## J. 신의개입 배경 (1장)

### J01 · 신의개입 — `img_J01_god` · 9:16

**용도** — 질문 3회, 선택지 3개 화면 공통 배경. **이 세계 밖.** 팔레트를 버린다 — 순검정 + 흰. 그림이라기보다 한 줄.

**노리는 것** — 사람이 아닌 목소리. 형태 없음. 흰 수평선 하나가 화면 아래 1/3에 있다. 그게 신이다. 리소 그레인도 없다 — 인쇄물이 아니다.

```
Pure black (#000000) background, no texture, no grain, no paper.
A single thin horizontal white (#FFFFFF) line across the full width of a
tall frame, positioned one third from the bottom, one pixel thick, perfectly
straight. Nothing else. No gradient, no glow, no vignette.
[공통 네거티브]
```

CSS로 그려도 된다. 생성이 필요 없는 유일한 장이지만 목록에 두는 이유는 **"세계 밖"이 다르게 보여야 한다**는 걸 팀이 잊지 않기 위해서다.

---

## K. 클리어 (2장)

### K01 · 아직 이해하지 못했다 — `img_K01_clear_not_yet` · 9:16

**용도** — 50~99%. 칸별 ○△✗와 "당신은 아직 세계를 이해하지 못했습니다"가 올라간다. 그리고 그냥 끝난다.

**노리는 것** — J01과 같은 검정. 흰 선이 **끊겨 있다.** 네 토막 중 셋만 있다. 설명 없음.

```
Pure black (#000000) background, no texture. A thin white (#FFFFFF)
horizontal line one third from the bottom, but broken into four equal
segments with gaps between them; the fourth segment on the right is
missing entirely. Nothing else.
[공통 네거티브]
```

### K02 · 세계를 이해했다 — `img_K02_clear_understood` · 9:16

**용도** — 100%. "당신은 세계를 이해했습니다." 이 뒤에 M01(하네스 공개)로 넘어간다.

**노리는 것** — 흰 선이 이어졌다. 그리고 선 위, 아주 작게, 남색 점 하나. 이 세계의 색이 세계 밖 화면에 처음 들어온다. 유저는 모른다.

```
Pure black (#000000) background, no texture. A single unbroken thin white
(#FFFFFF) horizontal line one third from the bottom. Directly above the
center of the line, a tiny dark navy (#1C2340) dot, barely visible against
the black. Nothing else.
[공통 네거티브]
```

---

## L. 멸망 종료 (1장)

### L01 · 세계는 멸망했습니다 — `img_L01_doom` · 9:16

**용도** — 5회차 밤 50% 미만. "세계는 멸망했습니다." 다시 하기.

**노리는 것** — 검정. 흰 선이 없다. 대신 화면 맨 아래에 남색 띠가 아주 얇게 — 이 세계의 바닥이 여기 있었다는 것만.

```
Pure black (#000000) background, no texture. No white line. At the very
bottom edge of a tall frame, a thin horizontal band of dark navy (#1C2340),
about two percent of the frame height, with faint paper grain inside the
band only. Nothing else.
[공통 네거티브]
```

---

## M. 하네스 공개 (1장)

### M01 · 하네스 공개 — `img_M01_harness` · 9:16

**용도** — 100%에서만. 규칙 목록·출처·부작용 인과가 올라간다. 맨 아래 "누가 당신의 세계에 개입하고 있었나요?"

**노리는 것** — 검정 위에 이 세계가 **인쇄물로** 돌아온다. 화면 상단에 C06(소등)의 축소본이 인쇄된 종이 한 장처럼 놓여 있고, 종이 모서리가 말려 있다. 세계가 사실은 종이 한 장이었다는 것. 리소 그레인은 종이 안에만.

```
Pure black (#000000) background. Near the top of a tall frame, a single
sheet of off-white paper (#EDE8DC) lying flat, slightly rotated, one corner
curled up. Printed on the sheet in navy risograph: the shelter bunk aisle at
lights-out, rows of bunks as silhouettes, the steel door at the far end —
a small, faded copy of a copy. Paper grain and halftone only inside the
sheet. Below the sheet, black. Lower two thirds empty.
[공통 네거티브 — this is the one image where the shelter appears inside another frame]
```

---

## 부록. 생성 팁

- **시드 고정이 되는 도구면 C01을 먼저 뽑고 그 시드로 C02~C06을 간다.** 안 되면 C01 채택본을 참조 이미지로 첨부하고 "same print run, same paper, same ink" 를 붙인다
- 초상 12장은 인물별로 평상을 먼저 확정하고, 그 이미지를 참조로 불안·의심을 뽑는다. 실루엣이 바뀌면 다른 사람이 된다
- 손·얼굴이 자꾸 나오면 프롬프트 맨 앞에 `back view only,` 를 추가한다. 네거티브보다 앞쪽 지시가 잘 먹힌다
- 주황이 다른 데로 새면 `monochrome navy except one orange point` 로 바꿔 쓴다
- 생성 결과에 글자가 박히면 폐기. 지우지 말고 다시 뽑는다 — 지운 자리가 남는다
- D군 후처리는 Photoshop/Figma에서 레이어 2개(남색·종이)로 분리한 뒤 한다. 원본 PNG를 그대로 밀면 종이 결까지 같이 밀려서 "인쇄 오차"가 아니라 "이동"으로 보인다

**총 45장. 생성 32장 + 후처리 12장 + CSS 가능 1장(J01).**

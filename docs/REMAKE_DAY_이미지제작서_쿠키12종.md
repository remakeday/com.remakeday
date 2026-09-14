# REMAKE DAY — 이미지 제작서 부록 N · 치지직 쿠키 12종

> 기획서 v8.1 7.5·부록 A.5 기준 · 이미지 제작서 v1의 공통 규칙(0.1 뼈대·0.2 네거티브·0.3 팔레트·0.5 체크리스트)을 그대로 상속한다
> 제작 도구: Gemini / ChatGPT → 12장 생성. **치지직 연출은 이미지에 굽지 않고 코드로 건다** (N.3)

---

## N.0 쿠키가 무엇인가 — 그림이 알아야 할 것

50% 이상 클리어 화면에서 "당신은 아직 세계를 이해하지 못했습니—" 가 끝나기 전에 검정 화면이 **치지직** 하고, 남색 인쇄물이 **1초** 새어 들어오고, 그 위에 파편 한 줄이 뜨고, 다시 검정.

그래서 이 12장은 45장 세트와 같은 리소 인쇄물이지만 **역할이 다르다.**

| | 45장 (A~M) | 쿠키 12장 (N) |
|---|---|---|
| 보이는 시간 | 계속 | **1초** |
| 배경 | 그림이 화면 전체 | 검정 위에 찢어진 띠로 일부만 |
| 정보량 | 공간 하나 | **물건 하나** |
| 읽히는 방식 | 훑어본다 | **한 눈에 찍힌다** |

1초 안에 찍혀야 하므로 규칙 셋이 추가된다.

- **피사체 하나.** 쟁반 하나, 문손잡이 하나, 스피커 둘. 배경은 벽 한 면
- **종이가 잉크보다 많다.** 남색 60% 이하. 어두우면 검정 위에서 안 보인다
- **텍스트 오버레이 자리를 비운다.** 하단 1/3은 미색 종이만. 파편 문장이 거기 올라간다

쿠키는 사실이 아니라 **파편**이다. 그림도 마찬가지다 — "우리는 동물이다"를 그리면 안 되고, 거울이 없는 벽을 그린다.

### N.0.1 쿠키 전용 뼈대 (0.1 뒤에 붙임)

```
Cookie frame, 9:16 vertical. A single subject fills the middle third of the
frame, drawn tight and clear enough to be read in one second. More paper than
ink — navy covers no more than sixty percent of the frame. Upper and lower
thirds are mostly plain off-white paper grain. Slightly heavier misregistration
than the main set, as if this print came from a worn plate.
```

### N.0.2 파일명·비율

- `img_N{번호}_cookie_{칸}_{단계}.png` — 예: `img_N04_cookie_motive_1.png`
- 전부 **9:16**
- 12장 모두 같은 종이 결(0.1 뼈대의 grain 문구 유지). 치지직 위에서 세트로 보여야 한다

---

## N.1 목록

| ID | 칸 | 단계 | 파편 문장 (텍스트 오버레이) | 피사체 |
|---|---|---|---|---|
| N01 | 원인 | 1 | 채연의 쟁반이 아침마다 그대로였다. | 가득 찬 쟁반 하나 |
| N02 | 원인 | 2 | 검진이 다녀간 뒤 아무도 열이 없다고 했다. 채연은 담요를 벗지 않았다. | 검진 탁자 위 담요 |
| N03 | 원인 | 3 | 저녁에 은상도, 준도 밥을 남겼다. | 남긴 쟁반 셋 |
| N04 | 동기 | 1 | 충식이 이송된 날, 충식은 아팠다고 했다. | 헝클어진 채 비어 있는 침상 |
| N05 | 동기 | 2 | 채연은 말하면 어디로 가는지 알고 있었다. | 복도 끝 문의 작은 창 |
| N06 | 동기 | 3 | 관리자 방송에 "옆 구역"이라는 말이 있었다. | 스피커 둘 |
| N07 | 정체 | 1 | 거울이 없다는 걸 문득 안다. | 거울 자리만 남은 벽 |
| N08 | 정체 | 2 | 트럭 옆면에 글자가 있었다. | 문 틈 너머 트럭 옆면 (글자는 뭉개짐) |
| N09 | 정체 | 3 | 문손잡이가 언제나 머리 위에 있다. 손이 닿지 않는다. | 아주 높은 문손잡이 |
| N10 | 부작용 | 1 | {규칙}이 걸린 날, {NPC}가 전과 다르게 행동했다. | 하나만 다르게 개어진 담요 |
| N11 | 부작용 | 2 | {규칙}이 걸린 날 {관찰}. 그 전날엔 없던 일이다. | 같은 장면이 두 번 인쇄됨 |
| N12 | 부작용 | 3 | {규칙}과 {규칙}이 같은 날 걸렸다. {NPC}가 둘 사이에서 이상하게 움직였다. | 겹쳐진 종이 두 장 |

부작용 3장은 문장이 템플릿(그 판의 규칙 로그에서 채움)이므로 그림은 **규칙이 뭐든 맞는 일반형**이어야 한다. "달라졌다 / 두 번이다 / 둘이 겹쳤다" 세 개념만 그린다.

---

## N.2 프롬프트

### 원인

**N01 · 원인 1** — `img_N01_cookie_cause_1`
```
[공통 뼈대] [쿠키 뼈대]
One shallow metal tray on the serving counter, seen from just below counter
height so its rim sits at eye level. The tray is completely full, untouched,
food drawn as flat halftone. Beside it, only the empty edge of the counter.
Steam faintly rising. Nothing else.
[공통 네거티브]
```

**N02 · 원인 2** — `img_N02_cookie_cause_2`
```
[공통 뼈대] [쿠키 뼈대]
The folding metal checkup table, seen from low. On it, a gray blanket lies
crumpled where a person sat, still holding the shape of shoulders. The
handheld checkup device rests beside it, its indicator light off, drawn as
an empty circle. No orange. No people.
[공통 네거티브]
```

**N03 · 원인 3** — `img_N03_cookie_cause_3`
```
[공통 뼈대] [쿠키 뼈대]
Three metal trays in a row on the counter at eye level, each about one third
eaten and then abandoned — food pushed to one side in all three the same way.
Evening: the fluorescent tube above is drawn dimmer, the shadows longer.
Nothing else.
[공통 네거티브]
```

### 동기

**N04 · 동기 1** — `img_N04_cookie_motive_1`
```
[공통 뼈대] [쿠키 뼈대]
A single metal bunk seen from low and close. The thin gray blanket is NOT
folded — it is rumpled and twisted, half hanging off the mattress, the shape
of someone who lay there sweating. A plain fabric wristband hangs from the
bunk post. The bunk is empty. Unlike the tidy bunk of the departure scene,
this one was left in a hurry.
[공통 네거티브]
```

**N05 · 동기 2** — `img_N05_cookie_motive_2`
```
[공통 뼈대] [쿠키 뼈대]
Tight view of the steel door at the corridor's end, seen from far below:
only the small square hatch window at its top is in focus, a dark rectangle
high above. The rest of the door is a flat navy plane. In the very bottom
corner of the frame, the edge of a gray blanket, as if someone is watching
the door from the floor. No face.
[공통 네거티브]
```

**N06 · 동기 3** — `img_N06_cookie_motive_3`
```
[공통 뼈대] [쿠키 뼈대]
Two identical wall speaker boxes on the same concrete wall, one near and
large, one far and small down the corridor, both with a dull orange
indicator light (#C8722E). A pipe connects them. The far one implies another
room beyond. Nothing else.
[공통 네거티브 — orange permitted on the two speaker lights only]
```

### 정체

**N07 · 정체 1** — `img_N07_cookie_identity_1`
```
[공통 뼈대] [쿠키 뼈대]
A bare concrete wall above a small metal sink, seen from low. Where a mirror
should hang there is only a clean rectangular patch, lighter than the wall
around it, with four small screw holes at its corners. Nothing hangs there.
Nothing reflects. Nothing else in frame.
[공통 네거티브]
```

**N08 · 정체 2** — `img_N08_cookie_identity_2`
```
[공통 뼈대] [쿠키 뼈대]
Seen from the floor through the wide gap beneath the steel door: outside,
filling the gap, the flat metal side panel of a large vehicle, very close.
On the panel a painted rectangular mark, smeared and illegible — shapes of
letters that cannot be read, worn away by the print. Faint orange (#C8722E)
glow along the bottom edge only. No vehicle wheels, no full truck, no
readable text.
[공통 네거티브 — orange only as a faint glow at the gap; the painted mark must NOT be readable as any letters]
```

**N09 · 정체 3** — `img_N09_cookie_identity_3`
```
[공통 뼈대] [쿠키 뼈대]
The steel door seen from extremely low, almost from the floor. The handle is
impossibly far up — near the top edge of a tall frame, small, out of reach.
The lower part of the door, at knee height, has faint pale scuff marks and
scratches on the paint, as if something has pushed against it many times.
No hands, no people.
[공통 네거티브]
```

### 부작용 (일반형)

**N10 · 부작용 1** — `img_N10_cookie_side_1`
```
[공통 뼈대] [쿠키 뼈대]
A row of five identical metal bunks seen along their length from low. Four
blankets are folded the same way, flat and square. The middle one is folded
differently — rolled instead of flat, placed at the head instead of the foot.
Everything else identical. Nothing else in frame.
[공통 네거티브]
```

**N11 · 부작용 2** — `img_N11_cookie_side_2`
```
[공통 뼈대] [쿠키 뼈대]
The serving counter with one tray, printed twice: the same scene overlaid on
itself with a clear offset, as if the paper went through the press two times.
In one print the tray is full; in the other, shifted a few centimeters, the
tray is empty. Both prints equally strong. A double image, not a blur.
[공통 네거티브]
```

**N12 · 부작용 3** — `img_N12_cookie_side_3`
```
[공통 뼈대] [쿠키 뼈대]
Two sheets of off-white paper lying on the concrete floor, seen from low so
they loom, one partly on top of the other. Both are blank except for a single
thick navy line printed across each, and where the sheets overlap the two
lines cross. One sheet's corner is curled. Nothing is written on them.
[공통 네거티브 — no text, no letters on the sheets]
```

---

## N.3 치지직 연출 — 이미지에 굽지 않는다

12장은 **깨끗한 인쇄물**로 뽑는다. 치지직은 코드가 건다. 이유 둘 — 12장에 같은 연출이 균일하게 걸려야 하고, 나중에 쿠키를 추가할 때 그림만 뽑으면 되게.

**타임라인 (총 1,000ms)**

| 시각 | 화면 |
|---|---|
| 0 | 검정. "당신은 아직 세계를 이해하지 못했습니—" 마지막 글자에서 멈춤 |
| 0~120ms | 검정 위에 가로 띠 2~3개가 튀며 나타남. 띠 안으로만 인쇄물이 보임 |
| 120~820ms | 띠가 매 프레임 1~3px 위아래로 튐. 남색 판이 종이 판에서 3% 어긋남. 3프레임에 한 번 띠 위치가 바뀜 |
| 300ms | 파편 문장 등장. 흰색, 한 줄, 화면 아래 1/3 (J01의 흰 선 위치) |
| 820~1000ms | 띠가 하나씩 꺼지고 검정. 문장도 사라짐 |
| 1000ms~ | 검정. 아무것도 없음. 탭하면 "다시 한다" |

**띠 규칙**

- 띠 높이: 화면의 12~28%. 합쳐서 화면의 45~60%만 보인다
- 띠 위치는 매번 무작위지만 **피사체(중앙 1/3)가 들어가는 띠가 반드시 하나** 있다
- 띠 안 이미지는 좌우로 2~6px 어긋남(RGB 분리 아님 — 2도 인쇄라 남색 판만 밀린다)
- 소리 없음 (오디오 에셋 0건 원칙 유지). "치지직"은 화면만으로 한다

**CSS 힌트**

```css
.cookie { position:absolute; inset:0; background:#000; }
.cookie .band { position:absolute; left:0; right:0; overflow:hidden;
  background:url(img_N07.png) center/cover; animation: jitter 90ms steps(1) infinite; }
.cookie .band::after { content:""; position:absolute; inset:0;
  background:inherit; mix-blend-mode:multiply; transform:translateX(3%); opacity:.7; }
@keyframes jitter { 0%{transform:translateY(0)} 33%{transform:translateY(2px)} 66%{transform:translateY(-1px)} }
.cookie .line { position:absolute; left:24px; right:24px; bottom:33.3%;
  color:#fff; font-size:15px; opacity:0; animation: show 200ms 300ms forwards; }
```

**접근성** — `prefers-reduced-motion`이면 띠를 튀기지 않고 0~1000ms 동안 정지 상태로 보여준다. 이미지와 문장은 같다.

---

## N.4 검수 체크리스트 (0.5에 추가)

- [ ] 피사체가 하나이고 중앙 1/3에 있다
- [ ] 남색이 화면의 60%를 넘지 않는다 — 검정 위에 올려 보고 판단
- [ ] 하단 1/3이 미색 종이만이다 (문장 자리)
- [ ] 1초 미리보기로 봤을 때 뭘 그렸는지 읽힌다 — 실제로 1초만 띄워보고 팀원에게 "뭐였어?"라고 묻는다
- [ ] N06·N08만 주황이 있고 지정된 자리에만 있다
- [ ] N08의 페인트 자국이 어떤 글자로도 읽히지 않는다
- [ ] N10·N11·N12가 특정 규칙을 암시하지 않는다 (템플릿 문장 어느 것과도 맞아야 한다)
- [ ] 12장의 종이 결이 같다 — 나란히 놓고 확인

---

## N.5 순서

1. **N07(거울 자리)을 먼저 뽑는다.** 12장 중 가장 단순해서 쿠키 뼈대가 잡히는지 확인하기 좋다
2. N01·N04·N09 — 45장 세트의 C01·H02·H01과 같은 피사체라 참조 이미지로 걸면 한 세트로 붙는다
3. 나머지 8장
4. 12장을 검정 위에 N.3 타임라인으로 실제 1초 재생해보고, 안 읽히는 것만 다시 뽑는다

**생성 12장 + 후처리 0장.** 치지직은 코드다.

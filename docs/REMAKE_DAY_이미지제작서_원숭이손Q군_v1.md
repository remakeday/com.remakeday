# REMAKE DAY — 이미지 제작서 부록 Q · 원숭이손 소원 삽화 8종

> 이미지제작서 v1의 부록. 공통 뼈대(0.1)·공통 네거티브(0.2)·팔레트(0.3)·검수 체크리스트(0.5)는 v1을 그대로 따른다.
> 근거: 설계 문서 `superpowers/specs/2026-09-16-coherence-chain-design.md` §3(기획서 5.7 소원 표 4종). 소원 1종당 **소원 장면 1장 + 부작용 흔적 1장**.
> 용도: 낮 화면 비트 삽화. 원숭이손을 받은 날에만 뜬다. 부작용은 체감이 조건이므로 그림이 있어야 한다 — 그날만 그림이 비면 "바뀌었다"가 아니라 "빠졌다"로 읽힌다.

---

## Q.0 이 문서만의 규칙

- **비율 3:2**, 비트 삽화(C군·clue군)와 같은 자리. 하단 1/3은 비우지 않는다(대화창 헤더가 아니라 삽화 카드다)
- **사람은 있되 얼굴도 손도 없다.** 등, 담요, 어깨선, 물건으로만 말한다. E군 초상과 같은 원칙
- **소원 장면과 부작용 장면은 한 세트다.** 같은 공간, 같은 형광등, 같은 바닥. 부작용 장면은 소원 장면에서 "무엇이 달라졌는가"가 한 눈에 잡혀야 한다 — 평소 삽화(clue-01~12)와 나란히 놓고 차이가 보이지 않으면 폐기
- **주황은 Q05의 스피커 불 하나.** 나머지 일곱 장은 2도
- 파일명 `frontend/public/assets/clues/Q0N-{slug}-v1.png`. 재사용 두 장은 기존 파일 그대로

## Q.1 목록

| ID | 소원 | 장면 | 제작 |
|---|---|---|---|
| — | skip-checkup 소원 | 담당자가 채연 침상을 지나친다 | **clue-02 재사용** |
| Q02 | skip-checkup 부작용 | 저녁, 남은 쟁반 넷과 담요 두른 등 둘 | clue-03 검토 후 안 맞으면 신규 |
| Q03 | mute-eunsang 소원 | 은상이 구석 침상에서 벽을 보고 앉아 있다 | 신규 |
| Q04 | mute-eunsang 부작용 | 방송실 문 앞의 민석, 프레임 뒤쪽 구석에 등 돌린 담요 | 신규 — v1 폐기(손잡이 허리 높이), **v2 채택** `Q04-minseok-reports-eunsang-v2.png` |
| Q05 | deaf-minseok 소원 | 스피커 불이 켜졌는데 한 사람만 등이 반대쪽 | 신규 (주황) |
| Q06 | deaf-minseok 부작용 | 덮인 수첩, 채연 침상 쪽으로 기운 등 | 신규 |
| Q07 | sleep-jun 소원 | 머리까지 덮인 담요, 기둥에 걸린 손목띠 | 신규 |
| Q08 | sleep-jun 부작용 | 은상이 준의 침상 앞에 서서 담요 덩어리를 내려다본다 | 신규 |

## Q.2 프롬프트

### Q02 · 검진 회피 → 저녁에 넷 — `Q02-evening-four-trays` · 3:2
**노리는 것** — clue-04(저녁 쟁반 셋)의 변형. 셋이 넷이 됐고, 그 옆에 담요를 두른 등이 둘이다. 평소 저녁과 나란히 놓으면 "하나 늘었다"만 보여야 한다.
```
[공통 뼈대]
Evening in the shelter, the fluorescent tube dimmer. On the floor by the
bunks, four metal trays in a row, each with food left untouched. Behind
them, two figures sitting on the lower bunks with gray blankets pulled up
over their shoulders and heads, seen from behind, backs to the camera.
Low camera at tray height. No faces, no hands.
[공통 네거티브]
```

### Q03 · 은상 침묵 — `Q03-eunsang-silent-corner` · 3:2
**노리는 것** — 평소 은상은 사람들 사이를 옮겨 다닌다(clue-10). 오늘은 구석 침상에 혼자, 벽을 보고 앉아 있다. 다른 침상은 비어 있어 "혼자"가 강조된다.
```
[공통 뼈대]
A corner of the bunk room. On the lowest bunk in the corner, one figure sits
facing the concrete wall, back fully to the camera, shoulders drawn in, a
gray blanket around them. The other bunks in the frame are empty and tidy.
Low camera from the aisle. No faces, no hands.
[공통 네거티브]
```

### Q04 · 은상 침묵 → 민석이 방송실로 — `Q04-minseok-reports-eunsang` · 3:2
**노리는 것** — clue-09(민석 혼자 방송실 문 앞)와 구분되는 두 인물 구도. 앞쪽에 방송실 문과 민석의 등, 프레임 깊숙이 구석에 Q03의 등 돌린 담요가 작게 보인다. 원인과 결과가 한 프레임.
```
[공통 뼈대]
Foreground: the closed broadcast-room door and, before it, one figure
standing with their back to the camera, arms hidden in sleeves. Deep in the
background at the far corner of the bunk room, small, another figure sits
facing the wall wrapped in a gray blanket. Low camera from the corridor
floor. No faces, no hands.
[공통 네거티브]
```

### Q05 · 민석 방송 차단 — `Q05-minseok-not-listening` · 3:2
**노리는 것** — 방송 중이다. 벽의 스피커 불이 켜져 있고 셋의 등은 스피커를 향하는데, 한 사람의 등만 반대쪽을 향한다. **주황 허용 — 스피커 불 하나.**
```
[공통 뼈대]
The wall speaker box high on the concrete wall, its single dull orange
(#C8722E) light on — the only color. Below, four figures seen from behind on
the bunks: three turned toward the speaker, one turned the opposite way,
facing the far wall. Low camera at bunk height. No faces, no hands.
[공통 네거티브 — orange only on the speaker light]
```

### Q06 · 민석 방송 차단 → 수첩 대신 묻는다 — `Q06-notebook-closed` · 3:2
**노리는 것** — clue-08(민석이 수첩에 적는다)의 변형. 수첩은 덮인 채 침상에 놓여 있고, 한 등이 옆 침상의 담요 두른 등 쪽으로 기울어 있다. 적지 않고 묻는다.
```
[공통 뼈대]
Two lower bunks side by side. On the near mattress a small closed notebook
lies untouched. Beside it a figure sits leaning toward the next bunk, back
to the camera; on that next bunk another figure sits wrapped in a gray
blanket, also seen from behind. Low camera at mattress height. No faces, no
hands, no writing visible.
[공통 네거티브 — no text on the notebook]
```

### Q07 · 준 잠들기 — `Q07-jun-asleep` · 3:2
**노리는 것** — 준의 침상. 담요가 머리까지 덮여 사람 모양 덩어리만 있다. 기둥에 손목띠가 걸려 있다(준이 늘 만지던 것). 낮인데 잔다.
```
[공통 뼈대]
A single lower bunk in daylight fluorescent light. A gray blanket covers a
sleeping shape completely, head and all — just a long lump. A plain fabric
wristband hangs from the bunk post, drawn plain, no markings. The aisle
floor in the lower part of the frame. No faces, no hands.
[공통 네거티브]
```

### Q08 · 준 잠들기 → 은상이 출처를 잃는다 — `Q08-eunsang-at-jun-bunk` · 3:2
**노리는 것** — Q07의 침상 앞에 은상이 서서 담요 덩어리를 내려다본다. 물을 사람이 자고 있다. 등만 보인다.
```
[공통 뼈대]
The same lower bunk with the blanket-covered sleeping shape. In front of it,
one figure stands with their back to the camera, looking down at the lump,
arms hidden in sleeves. Low camera from the aisle floor, the standing
figure's legs and back filling the left of the frame. No faces, no hands.
[공통 네거티브]
```

## Q.3 검수 (0.5에 추가)

- [ ] 얼굴·손이 없다 — 등, 담요, 소매
- [ ] 평소 삽화와 나란히 놓았을 때 차이가 한 눈에 보인다 (Q02↔clue-04, Q03↔clue-10, Q04↔clue-09, Q06↔clue-08)
- [ ] Q05만 주황, 스피커 불 하나
- [ ] 소원 장면과 부작용 장면이 같은 공간으로 읽힌다
- [ ] 수첩·손목띠에 글자·숫자가 없다

## Q.4 순서

1. **Q07(담요 덩어리)** — 가장 단순. 인물을 등·담요로만 그리는 뼈대가 잡히는지 확인
2. Q03·Q05 — 소원 장면 둘
3. Q04·Q06·Q08 — 부작용 셋. 각각 짝이 되는 소원 장면을 참조로 건다
4. Q02는 clue-03을 먼저 대 보고 결정

**신규 6장(Q03~Q08) + 조건부 1장(Q02) + 재사용 1장(clue-02). 후처리 없음.**

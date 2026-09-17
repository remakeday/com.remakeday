# REMAKE DAY — 이미지 제작서 부록 Q v2 · 원숭이손 새 소원 삽화 + 밤 단서 P06

> Q군 v1(`REMAKE_DAY_이미지제작서_원숭이손Q군_v1.md`)을 대체한다. v1 파일은 지우지 않는다 — Q02~Q08 원본 프롬프트의 기록이다.
> 공통 규칙은 이미지제작서 v1(0.1 뼈대·0.2 네거티브·0.3 팔레트·0.5 체크리스트)과 Q군 v1의 Q.0을 그대로 상속한다. P06은 밤단서 v2(P.0.1 뼈대·P.0.2·P.4)를 상속한다.
> 근거: 설계 문서 `superpowers/specs/2026-09-16-coherence-chain-design.md` §3(2026-09-17 개정, "이미지" 소절), 테스터9 F24(`review-verification/2026-09-17-tester9/tester9.md`).
> 작성 2026-09-17 · 상태: **초안 — 시나리오 디렉터 확인 전.** 캡션·방송 문장은 모두 초안이다.

---

## Q2.0 무엇이 바뀌었나

**소원 네 개가 전부 바뀌었다.** v1의 소원(검진 회피·은상 침묵·민석 방송 차단·준 잠들기)은 폐기됐다. 플레이어가 원할 이유가 없었고, 정보원을 없애 조사 경로를 막았다.

새 소원은 **진실에 다가가는 것처럼 보이지만 엉뚱한 곳을 가리키는 제안**이다. 소원으로 보는 장면은 세계에서 사실이고, 같은 날 뒤 비트에 **반대 사건**이 일어난다. 그래서 그림도 한 쌍이 "소원 장면 1장 + 반대 사건 흔적 1장"이다. 원칙(3:2, 얼굴·손 없음, 같은 공간)은 v1과 같다.

| # | 키 | 소원(팝업 문장) | 소원 장면 비트 | 반대 사건 비트 |
|---|---|---|---|---|
| ① | `chaeyeon-honest` | 채연이 오늘은 밥을 왜 안 먹는지 솔직하게 말한다. | 2 | 3(쟁반을 비운다) · 5(담요 두른 사람이 는다) |
| ② | `checkup-record` | 검진 담당자가 채연을 두고 무슨 말을 하는지 들린다. | 4 | 6(소등 후 기침) |
| ③ | `broadcast-room` | 민석이 방송실에서 하는 말이 들린다. | 2 | 3(수첩을 덮어 둔다) |
| ④ | `band-meaning` | 준이 손목띠 숫자의 뜻을 알아낸다. | 2 | 5(번호 소문) |

얻는 사실과 반대 사건의 뜻은 설계 문서 §3 소원 표가 정본이다. 이 문서는 그림만 다룬다.

### Q2.0.1 v1 산출물을 어떻게 쓰나

파일은 전부 `frontend/public/assets/clues/`에 있다. 삽화 ID는 각 잠재 행동의 `illustrations`에 지정한다.

| ID · 파일 | v1 용도 | 새 용도 | 판단 | 캡션 초안 |
|---|---|---|---|---|
| Q03 `Q03-eunsang-silent-corner-v1.png` | 은상 침묵 | ① 2비트 소원 장면 — 채연이 벽 쪽에 앉아 말한다 | **재사용**(캡션 교체) | 채연이 담요를 두른 채 벽 쪽을 보고 앉아 있다. |
| clue-03 `clue-03-after-checkup-v1.png` | (어댑터 미사용) | ② 4비트 소원 장면 — 검진 책상 앞, 담당자가 채연에 대해 말하는 동안의 검진 책상 | **재사용** | 검진 책상 위에 종이가 놓여 있다. |
| Q04 `Q04-minseok-reports-eunsang-v2.png` | 은상 침묵 부작용 | ③ 2비트 소원 장면 — 방송실 문 앞 민석, 구석의 은상 | **재사용** | 민석이 방송실 문 앞에 서 있다. 구석에 담요를 두른 사람이 있다. |
| Q06 `Q06-notebook-closed-v1.png` | 민석 방송 차단 부작용 | ③ 3비트 반대 사건 — 덮인 수첩 | **재사용** | 민석의 수첩이 덮인 채 놓여 있다. |
| Q02 `Q02-evening-four-trays-v1.png` | 검진 회피 부작용 | ① 5비트 반대 사건 — 담요 두른 사람이 는다 | **조건부 재사용** → Q2.2 | — |
| Q08 `Q08-eunsang-at-jun-bunk-v1.png` | 준 잠들기 부작용 | ④ 5비트 반대 사건 — 은상의 번호 소문 | **조건부 재사용** → Q2.2 | — |
| Q05 `Q05-minseok-not-listening-v1.png` | 민석 방송 차단 | — | **미사용 · 보관** | — |
| Q07 `Q07-jun-asleep-v1.png` | 준 잠들기 | — | **미사용 · 보관**(Q11 구도 참조용) | — |

**신규 3장(Q09~Q11) + 조건부 대체 최대 2장(Q02 v2·Q08 v2) + 밤 단서 1장(P06).**

---

## Q2.1 신규 목록

| ID | 소원 · 비트 | 장면 | 짝(나란히 놓고 차이 확인) | 파일 |
|---|---|---|---|---|
| Q09 | ① · 3 | 채연 자리 앞, 숟가락이 걸친 빈 쟁반 | clue-01(밀어 둔 남은 쟁반), Q03(같은 구석) | `frontend/public/assets/clues/Q09-chaeyeon-empty-tray-v1.png` |
| Q10 | ② · 6 | 소등 후 채연 자리, 앞으로 웅크려 들썩인 담요 | C06(소등 배경), Q03(같은 구석), Q07(누운 덩어리와 구분) | `frontend/public/assets/clues/Q10-cough-after-lights-out-v1.png` |
| Q11 | ④ · 2 | 침상 기둥의 표식과 손목띠의 표식이 나란히, 같은 무늬 | clue-11(준이 손목띠를 본다), Q07(기둥에 걸린 손목띠) | `frontend/public/assets/clues/Q11-band-matches-bunk-mark-v1.png` |

### Q2.1.1 이 문서만의 규칙 (Q.0에 추가)

- **채연 자리는 Q03의 구석 침상이다.** Q09·Q10은 Q03과 같은 구석, 같은 벽 모서리, 같은 배관으로 읽혀야 한다. Q03을 참조 이미지로 건다
- **주황 없음.** Q09~Q11과 대체 두 장은 모두 2도
- **표식은 숫자가 아니라 무늬다.** Q11의 "같은 숫자"는 구멍 무늬가 똑같다는 것으로 보여준다(아래 Q11). 등장인물은 글자를 읽지 못한다 — 숫자 모양의 글리프를 그리면 폐기
- **침상 명판은 침상 근접 컷에만 그린다(채택, 2026-09-17).** 기존 원거리 침상 삽화(Q01~Q08 등)는 수정하지 않는다. 앞으로 근접 컷을 새로 그릴 때만(Q11, Q08 v2 등) 넣는다
- 소등 장면(Q10)도 **검정 금지.** 남색 망점 밀도로만 어둡게, C06과 같은 방식

---

## Q2.2 신규 브리프

### Q09 · ① 3비트 · 쟁반이 빈다 — `Q09-chaeyeon-empty-tray` · 3:2

**장면** — 서술 초안 "채연이 숟가락을 끝까지 든다. 쟁반이 빈다." 늘 밀어 두던 채연이 오늘은 다 비웠다.
**노리는 것** — clue-01과 정반대여야 한다. clue-01의 채연 쟁반은 **비스듬히 밀려 있고 음식이 남아 있다.** Q09는 **반듯하게 놓여 있고 비어 있으며 숟가락이 가로질러 걸쳐 있다.** 먹는 동작은 그리지 않는다(손 금지) — 다 먹은 뒤의 흔적만.
**구도** — Q03의 구석 침상 앞 바닥, 쟁반 높이의 낮은 카메라. 쟁반 하나가 프레임 중앙 아래쪽을 크게 차지하고, 그 뒤 침상 가장자리에 담요를 두른 등(채연)이 벽을 보고 앉아 있다. 다른 쟁반은 없다.
**금지** — 음식 찌꺼기로 "남긴" 것처럼 보이는 덩어리, 쟁반 여러 개(C01·Q02와 헷갈림), 비스듬한 각도, 손·얼굴, 숟가락을 쥔 모습.
**검수** — ① clue-01과 나란히 놓았을 때 "남겼다/비웠다"가 한 눈에 갈린다 ② 쟁반이 하나다 ③ Q03과 같은 구석으로 읽힌다.
**캡션 초안** — 채연의 쟁반이 비어 있다. 숟가락이 쟁반 위에 걸쳐 있다.

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.

The same corner of the bunk room: two concrete walls meeting, a pipe running
along the top of both walls. On the concrete floor in front of the lowest
corner bunk, one shallow metal tray sits perfectly square to the bunk,
completely empty and scraped clean, a single spoon laid straight across it.
It is large in the lower middle of the frame. Behind it, on the edge of the
bunk, one small figure sits wrapped in a gray blanket, back to the camera,
facing the wall. No other trays. Low camera at tray height. No faces, no hands.

No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
No leftover food on the tray. Only one tray. The tray is not tilted or pushed aside.
```

### Q10 · ② 6비트 · 소등 후 기침 — `Q10-cough-after-lights-out` · 3:2

**장면** — 서술 초안 "소등 뒤, 채연 자리에서 기침 소리가 난다. 담요가 들썩인다." 목격자는 은상·준.
**노리는 것** — 소리를 그림으로 옮기지 않는다(효과선·글자 없음). **자세와 판 밀림**으로 들썩임을 보인다 — 담요 두른 등이 앞으로 웅크려 어깨가 솟았고, 담요 윤곽만 남색 판이 한 번 더 찍힌 듯 살짝 겹친다. 검진에서 「이상 없음」이었던 채연이 밤에 아프다는 것이 "같은 구석"으로 이어져야 한다.
**구도** — 통로 건너편 침상(은상·준 자리)에서 본 시점. 프레임 가까운 한쪽 모서리에 침상 틀과 담요 끝이 걸린다. 가운데에 Q03의 구석 침상, 그 위에 앉아 앞으로 웅크린 담요 두른 형체 하나. 형광등은 윤곽선만(꺼짐, C06과 동일). 바닥은 종이색, 벽과 침상은 남색 실루엣.
**금지** — 누운 담요 덩어리(Q07과 헷갈림, 시신으로 읽힘), 검정, 입김·효과선·"콜록" 류 글자, 공포 조명, 문 아래 빛(H01과 헷갈림), 얼굴·손.
**검수** — ① Q07과 나란히 놓았을 때 "잔다"가 아니라 "앉아서 웅크렸다"로 읽힌다 ② C06과 같은 소등 방식(검정 없음, 윤곽선 형광등) ③ Q03과 같은 구석 ④ 공포물처럼 보이지 않는다.
**캡션 초안** — 소등 뒤, 채연 자리의 담요가 들썩인다.

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.

The same corner of the bunk room at lights-out. The fluorescent tube is off,
drawn as an outline only. Bunks are flat navy silhouettes; the floor stays
paper-white. Seen from a bunk across the aisle: the edge of a metal bunk frame
and a gray blanket edge intrude at the near bottom-left corner. In the middle
of the frame, on the lowest corner bunk, one small figure sits hunched sharply
forward, wrapped in a gray blanket, shoulders raised under it, back to the
camera. Only the blanket's outline is printed twice, slightly offset, as if
it jolted. Darkness only as halftone density of navy, never black.
No faces, no hands.

No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
No black areas. No motion lines, no breath clouds, no sound symbols. The figure is sitting, not lying down. No light under any door.
```

### Q11 · ④ 2비트 · 침상 번호와 손목띠 — `Q11-band-matches-bunk-mark` · 3:2

**장면** — 서술 초안 "준이 손목띠를 침상 기둥에 대 본다. '침상에 같은 숫자가 있어. 자리 번호야.'"
**침상 명판이란** — 침상 머리맡 기둥에 리벳으로 박힌 작은 금속판. 손목띠와 같은 번호가 새겨져 있고, 그림에서는 숫자 대신 손목띠 태그와 같은 구멍 다섯 개 배열로 나타난다. 유저에게는 자리 번호로 읽히지만, 실제로는 돈방마다 거는 개체 카드(귀표 번호·입식 날짜)다 — 이 이중 의미는 게임 안에서 밝히지 않는다.
**채택(사용자 확정 2026-09-17)** — 침상 명판은 새 세계 설정이다. Q.0·0.5 규칙 "글자·숫자 없음"과 장면의 "같은 숫자" 사이 충돌, 등장인물이 글자를 읽지 못한다는 설정(F24)은 아래 표현 방법(구멍 무늬 일치)으로 해소한다.
**표현 방법 — 구멍 무늬 일치**
- 침상 기둥에 작은 금속 명판이 리벳으로 박혀 있고, 명판에 **둥근 구멍 다섯 개가 고르지 않은 간격**(둘 붙고, 틈, 셋 붙음)으로 뚫려 있다
- 손목띠의 태그에도 **같은 배열의 구멍 다섯 개**가 뚫려 있다. clue-11·Q07의 손목띠에 이미 작은 점무늬가 있어 같은 물건으로 이어진다
- 구멍 배열 = 인물들이 읽는 숫자다. 두 무리의 구멍 수를 앞뒤로 읽는다(예 준 ●● ●●● = 23). 사람의 숫자가 아니라 귀 절흔 표식이므로 그림에는 숫자를 그리지 않는다 (2026-09-18 결정)
- 손목띠를 명판 바로 아래 볼트에 걸어 두 무늬가 **같은 크기로 위아래에 정렬**된다. 손으로 대는 동작은 그리지 않는다
- 무늬는 셀 수 있지만 숫자 글리프가 아니다. "같다"는 한 눈에 보이고, "무슨 뜻"은 보이지 않는다 — 준도 모른다
- 제작 중 무늬가 숫자처럼 읽히면(대안): P04·N08과 같은 **읽을 수 없는 얼룩 도장**을 명판과 태그에 같은 모양으로 찍는다. 같음은 약해지지만 "읽을 수 없는 글자" 계열로 통일된다
- **명판은 침상 근접 컷에만 그린다(공통 규칙, Q2.1.1 참고).** 기존 원거리 침상 삽화는 수정하지 않는다 — 멀리서는 안 보이는 것이 자연스럽다

**구도** — 침상 기둥 근접, 명판 높이의 낮은 카메라. 기둥이 프레임 세로 중심을 지나고, 명판과 그 아래 걸린 손목띠 태그가 프레임 중앙을 차지한다. 프레임 왼쪽 가장자리에 준의 등·어깨(후드)가 흐리게 걸린다 — clue-11의 인물과 같은 옷.
**금지** — 아라비아 숫자·한글·바코드처럼 읽히는 무늬, 손·손가락, 명판 여러 개(Q08 v2에서만 줄 세움), 주황.
**검수** — ① 명판 무늬와 태그 무늬가 같다는 게 1초에 보인다 ② 어떤 숫자·글자로도 읽히지 않는다 ③ clue-11과 나란히 놓았을 때 "띠만 본다 / 기둥과 맞춰 본다"가 갈린다 ④ 기둥의 명판이 새 설정이므로, 이 명판을 **Q08 v2·이후 C02류 삽화에서 같은 모양으로 재사용**할 수 있게 단순하다.
**캡션 초안** — 준의 손목띠 무늬가 침상 기둥의 무늬와 같다.

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.

Close on a square metal bunk post, seen low at plate height, the post running
vertically through the center of the frame. Riveted to the post, a small plain
metal plate with five round punched holes in an uneven row: two close together,
a gap, then three close together. Directly beneath it, hooked over a bolt on
the same post, a plain fabric wristband whose flat tag has exactly the same
five punched holes in the same uneven row, the same size, lined up under the
plate so the two patterns match at a glance. At the far left edge, blurred,
the hooded shoulder and back of a small figure. The aisle floor at the bottom.
No faces, no hands.

No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
The holes are plain round punched holes, not digits, not barcodes. Only one plate.
```

---

## Q2.3 조건부 재사용 2장 — 판단 기준과 대체안

### Q02 · ① 5비트 · 담요 두른 사람이 는다

**현재 그림** — 쟁반 넷(음식 남음) 앞, 담요를 머리까지 쓴 등 둘.
**판단 기준** (하나라도 걸리면 대체)
1. **같은 화면의 문장과 수가 맞는가.** 5비트 기본 서술은 "음식이 남은 쟁반 세 개가 보인다", 기본 삽화 clue-04 캡션도 "쟁반이 세 개"다. Q02(넷)가 함께 뜨면 퍼짐이 아니라 오류로 읽힐 수 있다. 팀원 1명에게 5비트 화면을 그대로 보여 주고 "쟁반 몇 개?"를 묻는다 — 답이 갈리거나 "틀린 것 같다"가 나오면 탈락
2. **"늘었다"가 담요로 읽히는가.** 쟁반 수보다 담요 두른 등 둘이 먼저 눈에 들어와야 한다
3. **①의 3비트와 모순이 없는가.** 정오에 채연이 다 먹었는데 저녁에 채연 쟁반이 남아 있는 것으로 읽히지 않아야 한다(Q02의 쟁반 넷 중 하나가 채연 것으로 읽힐 위험)

**제작자 소견** — 1번에서 탈락할 가능성이 높다. 서술이 "세 개"로 고정된 한 대체를 먼저 준비한다.

**대체 브리프 — Q02 v2 `Q02-evening-two-blankets-v2.png` (같은 ID, 파일만 교체)**
저녁, Q03의 구석. 구석 침상에 담요 두른 등 하나(채연), **바로 옆 침상에 새로 담요를 뒤집어쓴 등 하나(은상)**가 나란히 벽을 본다. 쟁반은 프레임에 없다. Q03(등 하나)과 나란히 놓으면 "하나 → 둘"만 보인다.
캡션 초안 — 저녁, 담요를 두른 사람이 하나 늘었다.

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.

Evening, the fluorescent tube dimmer. The same corner of the bunk room. On the
lowest corner bunk, one small figure sits wrapped in a gray blanket facing the
wall. On the next lower bunk right beside it, a second figure sits the same
way, a gray blanket pulled up over the head and shoulders. Two blanketed backs
side by side, both toward the wall. The other bunks in the frame are empty.
No trays anywhere. Low camera from the aisle. No faces, no hands.

No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
No trays or food in frame.
```

### Q08 · ④ 5비트 · 은상의 번호 소문

**현재 그림** — 기둥에 손목띠가 걸린 침상 앞에 선 은상의 등, 침상 위 머리까지 덮인 담요 덩어리.
**판단 기준** (하나라도 걸리면 대체)
1. **담요 덩어리의 정체가 설명되는가.** 새 설계에서 5비트에 누워 있는 사람은 없다(준 잠들기는 폐기). 덩어리가 "누군가 누워 있다 / 실려 갈 사람 / 시신"으로 읽히면 탈락 — 일어나지 않은 이송을 그림이 만든다
2. **"번호"가 보이는가.** Q11의 기둥 명판이 없다. 소문의 내용(번호 순서)이 그림에 없으면 5비트 기본 삽화 clue-10(귓속말)과 차이가 "은상이 서 있다" 뿐이다
3. **Q11과 같은 기둥으로 읽히는가.** Q11이 확정된 뒤 나란히 놓아 판단한다

**제작자 소견** — 1·2번에서 탈락할 가능성이 높다. Q11 확정 뒤 대체를 뽑는다.

**대체 브리프 — Q08 v2 `Q08-eunsang-number-rumor-v2.png` (같은 ID, 파일만 교체)**
통로를 따라 침상 기둥이 줄지어 멀어지고, **기둥마다 Q11과 같은 명판**이 같은 높이에 박혀 있다(무늬는 기둥마다 다르게, 전부 구멍만). 앞쪽에서 은상의 등이 옆 침상에 앉은 담요 두른 등 쪽으로 몸을 기울인다(귓속말). "줄지어 선 명판 = 순서"가 소문의 내용이다. 누운 사람 없음.
캡션 초안 — 은상이 귓속말에 한마디를 보탠다. 기둥마다 표식이 있다.

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.

Evening, the fluorescent tube dimmer. A long row of metal bunk posts recedes
down the aisle; on every post, at the same height, a small plain metal plate
with a few round punched holes, the hole patterns different from post to
post. In the foreground, one figure stands with their back to the camera,
leaning toward the next bunk, where another figure sits wrapped in a gray
blanket, also seen from behind — as if something is being said close to the
ear. Low camera from the aisle floor. No one is lying down. No faces, no hands.

No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
The holes are plain round punched holes, not digits. No blanket-covered lying shape.
```

---

## Q2.4 밤 단서 P06 · 트럭 옆면 — F24 대응

### Q2.4.1 왜 필요한가

4회차 트럭 결말 밤에는 캡션 뒤에 결말 파편 `트럭 옆면 "○○축산".`이 한 줄 붙는다(`adapter.py` fragments `loop_n=4, world_outcome="truck"`, 밤단서 v2 P.1). **등장인물은 글자를 읽지 못하는데 이 문장만 읽힌 문자열이다**(테스터9 F24). 결정: 이 파편을 없애고, **글자를 읽을 수 있는 쪽인 관리자의 방송**이 그 표기를 말하게 한다. 형식은 기존 밤 단서와 같다 — 방송(출처) → 치지직 그림(흔적) → 캡션(내가 느낀 것).

**등장 시점은 4회차 트럭 결말 밤이 아니라 5회차 낮 끝으로 바뀌었다(2026-09-17 결정, 아래 Q2.4.2).**

**이미지가 필요하다고 판단했다.** 이유 셋.
1. 밤 단서의 문법이 "방송 → 그림 → 캡션"이다. 방송만 있고 그림이 없으면 이 단서만 치지직 없이 지나가 다른 밤과 무게가 달라진다. 데이터 구조도 `image_ids` 최소 1장이다
2. 바탕 H01(트럭)은 **문 아래 틈의 주황 빛뿐이고 트럭이 보이지 않는다.** "트럭 옆면에 글자가 있다"를 보여주는 그림이 본편에 없다. 밤단서 v2가 "H01이 이미 트럭이니 이미지를 추가하지 않는다"고 한 것은 읽힌 문자열 파편 한 줄을 붙일 때의 판단이었다
3. 대상이 같은 쿠키 N08(문 아래 틈으로 본 트럭 옆면)을 그대로 쓰면 클리어 화면에서 같은 그림이 두 번 나온다. P03↔N07, P05↔N09처럼 **각도를 달리한 밤 단서판**을 따로 둔다

### Q2.4.2 회차·타이밍 제안 (2026-09-17 개정 — 등장 시점을 5회차 낮 끝으로 변경)

**사용자 결정(2026-09-17):** 이 방송과 단서는 4회차 밤이 아니라 **5회차 낮의 마지막 장면(6비트, 소등 후)이 끝난 직후, 마지막 밤 추리문을 쓰기 전**에 나온다. 5회차 밤의 결말(트럭·조용함·폐쇄)은 그 시점에 아직 정해지지 않았으므로, **결말 조건과 무관하게 5회차마다 항상** 재생한다. 트럭 결말로 가야만 보이는 장치가 아니라, 플레이어가 알아채면 정체 칸에 쓸 수 있고 못 알아채면 못 쓰는 정체 단서다.

- 1~5회차 밤 단서(MA08~MA12, P01~P05)의 배치·조건은 건드리지 않는다. MA13·P06은 그 대체가 아니라 5회차 낮 끝에 추가되는 별도 장면이다
- 4회차 트럭 결말 파편(`FragmentDTO(loop_n=4, beat=6, world_outcome="truck", text='트럭 옆면 "○○축산".')`)은 삭제한다(Q2.4.1과 동일). 이 파편이 있던 4회차 밤 자리는 비워 두고 아무것도 대체하지 않는다 — 단서 자체가 5회차로 옮겨졌기 때문이다
- 같은 밤의 포대 단서(MA11 · P04)에 이어 붙이는 구성은 더 이상 쓰지 않는다. 그 구성은 "4회차 밤, 트럭 결말"에 종속됐던 옛 설계였다

| 시각 | 화면 | 소리 |
|---|---|---|
| 0s | 5회차 6비트(소등 후) 장면의 관찰·인물 대사 재생이 끝난 직후. 화면 전환 없음 | (없음) |
| +0.3s | 같은 소등 장면 유지 | **MA13 시작** |
| MA13 길이의 40~60% ("축산 차량" 직후) | **치지직 1초**: 밤 단서와 같은 띠 규칙(N.3)으로 P06 노출 | — |
| +0.3s | **캡션** 등장(밤 단서 캡션과 같은 자리·같은 미색) | — |
| +1.0s | 띠가 하나씩 꺼진다. 캡션 잔류 | — |
| +2.0s | 탭하면 밤(NightScreen, 마지막 추리문 작성)으로 넘어간다. 자동 진행 없음 | — |

- 전체 전환은 약 5~6초. 길다고 판단되면 "+2.0s 탭 대기"를 없애고 바로 밤으로 넘긴다
- 음성 차단·음소거면 MA13을 건너뛰고 소등 장면 종료 0.6초 뒤 치지직을 시작한다(밤단서 v2 P.2와 같은 정책)
- MA13 파일 오류 시 대체 음원은 쓰지 않는다. 이 장면은 밤 결말 전환이 아니므로 결말별 대체 음원(MA03/04/05)과는 관계없다. 방송 문장은 노트의 전언으로 남는다
- `prefers-reduced-motion`이면 띠를 튀기지 않고 1초 정지(P.2와 동일)

### Q2.4.3 문장 초안 (시나리오 디렉터 확인 전)

| 항목 | 초안 | 메모 |
|---|---|---|
| **관리자 방송 MA13** | 축산 차량이 출발합니다. 문이 닫힐 때까지 자리에서 움직이지 마십시오. | 합니다체, MA07("모두 자리에서 움직이지 않습니다")과 같은 온도. 차량을 **이름으로 부를 뿐** 무엇을 싣는지·어디로 가는지는 말하지 않는다. 상호 없이 "축산 차량"으로 확정(2026-09-17) |
| **캡션** | 트럭 옆면에도 글자가 있다. | 방송을 되풀이하지 않는다. 읽었다고 쓰지 않는다 |
| 삭제 | `트럭 옆면 "○○축산".` (fragments `loop_n=4, world_outcome="truck"`) | 읽힌 문자열. 이 단서로 대체 |

- **"○○" 상호 표기는 쓰지 않는다(2026-09-17 확정).** 자막·대본·노트 모두 상호 없이 "축산 차량이 출발합니다"로 통일한다.
- 방송 문장은 5회차 낮 끝(소등 후)에 「5회차 · 낮 끝 · 전언」으로 저장한다. 정확한 저장 경로는 Q2.4.5 구현 메모 참고. 조언자가 이 단서를 해석하는 방식과 정체 칸 채점 인정 범위는 F24 개선 방향대로 함께 점검한다

### Q2.4.4 P06 브리프 — `P06` · 9:16

**노리는 것** — 5회차 낮 끝, 트럭이 실려 가는 모습이 문틈으로 보이는 순간. 결말(트럭 여부)과 무관하게 항상 벌어지는 장면이다. 내 침상에서 본, **반쯤 열린 철문 틈을 가득 채운 트럭 옆면**, 그 위에 **P04와 같은 모양의 읽을 수 없는 얼룩 표기**. N08과는 시점이 다르다 — N08은 닫힌 문 아래 틈으로 바닥에서 본 것, P06은 열린 문을 침상에서 본 것. 프레임 아래 구석에 내 담요 끝.
**구도** — 침상 매트리스 높이. 담요 끝이 프레임 아래 왼쪽. 중앙 1/3에 세로로 열린 문틈, 그 안을 트럭의 평평한 금속 옆면이 채우고, 옆면에 직사각형 표기 하나 — 얼룩 덩어리 배치를 **P04와 같게**(두 덩어리가 나란한 모양). 표기 테두리에만 옅은 주황(P04와 같은 처리).
**금지** — 읽을 수 있는 글자·숫자, 바퀴·트럭 전체 모습, 사람·손·얼굴, 헤드라이트 광원, 검정, 동물·농장 물건.
**검수 (P.4에 추가)**
- [ ] 1초 미리보기로 "열린 문 너머 트럭 옆면에 뭔가 찍혀 있다"가 읽힌다
- [ ] 얼룩이 어떤 글자로도 읽히지 않는다
- [ ] P04와 나란히 놓았을 때 **같은 모양의 표기**로 보인다
- [ ] N08과 나란히 놓았을 때 시점이 다르다(닫힌 문 아래 틈 / 열린 문틈)
- [ ] 담요 끝이 한 구석에 있다. 종이 40% 이상. 주황은 표기 테두리에만

**파일** — `frontend/public/assets/P06.png`. 참조 이미지로 **P04**(얼룩 모양)와 **H01**(같은 철문)을 건다.

```
Two-color risograph print, dark navy ink (#1C2340) on off-white paper (#EDE8DC).
Heavy paper grain, visible halftone dots, slight misregistration between layers,
flat shading, no gradients, no photorealism.
Camera at 60 cm height, tilted slightly upward, wide lens.
Underground shelter interior: bare concrete floor, one fluorescent tube light,
exposed pipes along the ceiling, metal bunks, no windows, no mirrors, no sky.
Quiet, institutional, cold. Not horror. Nothing is happening.

Cookie frame, 9:16 vertical. A single subject fills the middle third of the
frame, drawn tight and clear enough to be read in one second. More paper than
ink — navy covers no more than sixty percent of the frame. Upper and lower
thirds are mostly plain off-white paper grain. Slightly heavier misregistration
than the main set, as if this print came from a worn plate.

Night-clue frame, 9:16 vertical, lights-out. Seen from a bunk or from the
floor, very low; the edge of a gray blanket or a bunk frame intrudes at one
corner of the frame — someone is lying here. One thing noticed in the dark
fills the middle third, drawn tight and clear enough to be read in one
second. Darkness only as halftone density of navy, never black, never
gradients; at least forty percent of the frame stays off-white paper grain.
The lower third is plain paper, reserved for one caption line.

Lying on a bunk, eye at mattress level. The frayed edge of a gray blanket
fills the bottom-left corner. Across the floor, the heavy steel door stands
half open. The vertical opening fills the middle third, and right behind it,
very close, the flat metal side panel of a large vehicle fills the whole
opening. On the panel, one printed rectangular mark smeared into two
illegible ink blots side by side — shapes that cannot be read as letters,
worn by the print — with a faint dull orange (#C8722E) border around the
mark. Nothing else.

No human faces. No hands or fingers. No windows, mirrors, sky, or daylight.
No animals, pink tones, straw, fences, or farm objects. No text, letters, numbers,
signs, or logos. No blood, weapons, or violence. No third color except where specified.
The mark must NOT be readable as any letters or numbers. Orange only as the faint border. No wheels, no whole truck, no headlights, no people.
```

### Q2.4.5 구현 메모 (참고 — 이 문서는 코드를 바꾸지 않는다)

지금 밤 단서(MA08~12·P01~05)는 "밤 결말 전환 안"에서만 알려진다 — `backend/apps/engine/app/use_cases/night_interactor.py`의 `_disclose_night_clue`가 `ConfirmScreen` 제출 뒤에야 `loop.loop_n`으로 `backend/apps/scenarios/scenario_a/adapter.py`의 `night_clues`(`NightClueDTO`, 회차당 1행) 목록에서 그 회차 단서를 골라 제출 결과(`night_clue`, `world_outcome`)에 담고, 프런트(`frontend/app/play/page.tsx`)는 그 결과를 받은 뒤 `doom_transition` 단계에서 `frontend/components/screens/DoomTransition.tsx`로 재생한다. MA13·P06을 **5회차 낮 끝(6비트가 끝난 뒤, `NightScreen` 진입 전)으로 옮기려면** 이 흐름 전체를 바꿔야 한다. 백엔드는 제출 결과가 아니라 5회차 day 응답(또는 day→night 전환 시점)에 이 단서를 실어야 하므로, `night_clues`에 결말 조건 없이 항상 내려주는 5회차 전용 항목(`image_ids=["P06"]`, `voice_id="MA13"`)을 추가하고 이를 `frontend/components/screens/DayScreen.tsx`의 6비트 응답(또는 day→night 전환 API)으로 옮겨 실어야 한다. 프런트는 `DayScreen.tsx`가 지금 곧바로 `onDayDone` → (`page.tsx`의) `setPhase("night")`로 넘기는 지점에 새 단계(또는 하위 화면)를 끼워 넣고, `DoomTransition.tsx`의 치지직·캡션 재생 로직을 `world_outcome` 없이도 동작하도록 분리해 재사용해야 한다(5회차 낮 끝 시점에는 아직 밤 결과가 없다). 4회차 `world_outcome="truck"` 조건부 `FragmentDTO`와 `night_interactor`의 결말 연동은 제거한다.

- 프론트: `imageMap.nightClueImage`에 P06 등록, `voiceMap.ts`에 MA13 등록
- 테스트 기대값: `frontend/tests/five-loop-flow.cjs`·`guard.cjs`의 4회차 `outcome_line` 기대와 5회차 낮→밤 전환 기대가 바뀐다

---

## Q2.5 디렉터 확인 필요

- Q02·Q08은 판단 기준으로 보면 대체 가능성이 높다. 대체 시 ID는 유지하고 파일만 v2
- F24: MA13 방송 문장, 캡션, 트럭 단서의 5회차 낮 끝 전환 길이(Q2.4.2)

**해결됨(2026-09-17, 사용자 확정):** ② 검진 기록 문장(담당자가 채연 앞에서 소리 내어 "여기는 이상 없음"이라고 말한다 — 설계 문서 §3 확정, 위 Q2.0·clue-03 참고), Q11 표현 방법과 침상 명판의 새 세계 설정 여부(채택 — 위 Q11 참고), "○○" 발음 처리(상호 없이 "축산 차량"으로 통일), 트럭 단서의 등장 회차·결말 조건(4회차 밤 트럭 결말 한정 → 5회차 낮 끝, 결말과 무관하게 항상 — Q2.4.2).

## Q2.6 순서

1. **Q09** — 가장 단순. Q03을 참조로 걸어 "같은 구석"이 붙는지 확인
2. **Q11** — 규칙이 가장 까다롭다(무늬가 숫자로 읽히면 폐기). 일찍 실패를 본다. 확정되면 명판 모양을 고정
3. **Q10** — Q03·C06을 참조로
4. **P06** — P04·H01을 참조로. 5회차 낮 끝 타임라인(Q2.4.2)에 얹어 1초 재생
5. Q02·Q08 판단(Q2.3) → 탈락 시 Q02 v2, Q08 v2(Q11 명판 참조)

**신규 4장(Q09·Q10·Q11·P06) + 조건부 대체 최대 2장(Q02 v2·Q08 v2) + 재사용 4장(Q03·Q04·Q06·clue-03) + 보관 2장(Q05·Q07). 전부 생성, 후처리 없음.**

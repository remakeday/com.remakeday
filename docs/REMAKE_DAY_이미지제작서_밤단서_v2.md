# REMAKE DAY — 이미지 제작서 부록 P v2 · 밤 단서 — 쿠키 문법

> v1(밤단서4종, 삭제됨)을 대체한다. v1의 "원거리·정물" 규칙은 폐기 — 그 규칙으로 생성한 P01~P04(`output/imagegen/img_P0*_night_*.png`)가 1초 안에 단서로 읽히지 않았다(복도 전경·차이 없음·감각 캡션과 그림의 분리).
> 공통 규칙은 이미지제작서 v1(0.1 뼈대·0.2 네거티브·0.3 팔레트·0.5 체크리스트)과 쿠키 12종(N.0.1 쿠키 뼈대·N.3 치지직·N.4 체크)을 그대로 상속한다.
> 용도: 밤 결말 전환 안에서 **관리자 밤 방송이 그날의 고아 단서를 흘리고**, 치지직 그림 1~2장이 그 흔적을 보여준다. 기획서 A.3 "1 멸망: 소독약 냄새. 트럭 소리. 발 아래 콘크리트가 차다"의 배치 원칙을 화면으로 옮긴 것.
> 구현: 코드 타임라인(Codex). mp4로 굽지 않는다. 이미지·음원은 기존 경로(`frontend/public/assets/`) 그대로 쓴다.

---

## P.0 쿠키와 무엇이 같고 무엇이 다른가

| | 쿠키 N군 | 밤 단서 P군 |
|---|---|---|
| 언제 | 클리어 화면, 판당 1회 | **매일 밤**, 결말 전환 안에서 |
| 바탕 | 검정 | **그날 결말 이미지**(H01 트럭 / H02 조용히 / clue-06 폐쇄) — 세계 안이다 |
| 띠 안 | 쿠키 이미지 | 밤 단서 이미지 |
| 문장 | 파편 문장, 흰 글씨 | **고아 단서 문장**, 미색 글씨. 띠가 꺼진 뒤에도 바탕 위에 남는다 |
| 소리 | 없음 | **관리자 음성 1개**(결말별) + 결말 효과음 |
| 뜻 | 사실이 아니라 파편 | 같다. 확인할 상대가 없다(4.9). 낮 노트에는 넣지 않는다 |

**세 존재의 순서가 개연성을 만든다.** 방송(원인) → 문 아래 빛·빈 침상·스피커(사건) → 치지직 단서(흔적). 단서 그림이 왜 지금 나오는지를 방송 한 줄이 설명한다.

### P.0.1 밤 단서 전용 뼈대 (0.1 → N.0.1 뒤에 붙임)

```
Night-clue frame, 9:16 vertical, lights-out. Seen from a bunk or from the
floor, very low; the edge of a gray blanket or a bunk frame intrudes at one
corner of the frame — someone is lying here. One thing noticed in the dark
fills the middle third, drawn tight and clear enough to be read in one
second. Darkness only as halftone density of navy, never black, never
gradients; at least forty percent of the frame stays off-white paper grain.
The lower third is plain paper, reserved for one caption line.
```

### P.0.2 파일·비율·주황

- 전부 **9:16**. 파일 `frontend/public/assets/P0N.png`
- 주황은 **P01의 말통 캡 하나**, **P04의 포대 인쇄 얼룩 테두리(N08 선례)**. 나머지 2도
- 글자·숫자 금지. P04의 포대 글자는 **판독 불가능한 얼룩**이어야 한다(N08과 같은 규칙)

---

## P.1 회차별 구성 (Codex가 데이터로 옮길 표)

관리자 음성이 단서를 **흘린다.** 관리자는 시설 안내만 하고 진실은 한 마디도 하지 않는다. 그런데 그 안내가 그날 밤 튀는 그림과 겹치면 단서가 된다. 방송(출처) → 치지직 그림(흔적) → 캡션(내가 느낀 것) 순서. 캡션은 짧게, 방송이 말한 것을 되풀이하지 않는다.

| 밤 | 바탕(결말별) | **관리자 밤 방송(신규 녹음 5개)** | 치지직 이미지(1~2장) | 캡션(잔류) |
|---|---|---|---|---|
| 1 | H01 / H02 / clue-06 | **MA08** "소독을 실시합니다. 바닥에서 떨어져 자리에 오르십시오." | P01 말통 | 소독약 냄새. 발 아래 콘크리트가 차다. |
| 2 | 〃 | **MA09** "정리 작업이 있겠습니다. 비어 있는 자리는 아침에 정돈됩니다." | P02 바퀴 자국 → clue-05 빈 침상 | 트럭 소리. |
| 3 | 〃 | **MA10** "외관 확인은 담당자가 합니다. 각자 확인할 필요 없습니다." | P03 빈 자국 | 거울이 없다. |
| 4 | 〃 | **MA11** "배급 물자가 도착했습니다. 포대의 표기는 관리 용도입니다. 읽을 필요 없습니다." | P04 포대 얼룩 | 배급 포대에 글자가 있다. |
| 5 | 〃 | **MA12** "출입문은 관리자가 개방합니다. 문에 손대지 마십시오." | P05 손잡이 | 손이 없어서 문을 못 연다는 것을 문득 안다. |

- 방송 대본은 초안이다. voice.md 원칙대로 **시나리오에 없는 사실을 만들지 않는다** — 다섯 줄 모두 표면 세계(소독·정리·세면·배급·출입 통제)의 안내이며 정체·원인을 말하지 않는다. 연기는 MA01~MA07과 같은 온도: 절제된 시설 안내, 감정 없음
- 녹음 전까지는 결말별 기존 음원으로 대체한다: 트럭 MA04 "확인이 필요한 대상이 있습니다" · 조용히 MA03 "검진을 마쳤습니다. 추가 이송 대상은 없습니다" · 폐쇄 MA05 "구역 간 이동을 중단합니다"(→ MA06). 셋 다 제작돼 있고 지금 안 쓰인다
- 트럭 결말 밤에는 캡션 뒤에 기존 트럭 파편이 한 줄 더 붙는다(1회차 "트럭 소리.", 4회차 '트럭 옆면 "○○축산".'). 이미지는 추가하지 않는다 — H01이 이미 트럭이다
- 2회차만 두 장(자국 → 빈 침상)이다. 띠가 한 번 더 튄다. 나머지는 한 장
- "7시 13분"은 밤이 아니라 4회차 아침(B03)의 것이다. 여기 넣지 않는다
- 낮 노트의 파편 공개(`loop_interactor` fragments 분기)는 끈다. 캡션 문장은 밤에 「N회차 · 소등 후」 출처의 관찰로 저장한다(밤 조언의 닻으로는 쓰되, 조언은 파편의 뜻을 풀지 않는다). 방송 문장도 「소등 후 · 전언」으로 저장한다 — 플레이어가 밤에 "관리자가 포대 글자를 읽지 말랬다"를 근거로 탭할 수 있어야 한다

## P.2 타임라인 (총 약 6초 · 쿠키 N.3을 바탕 위에서 재생)

| 시각 | 화면 | 소리 |
|---|---|---|
| 0 | 검정에서 바탕(결말 이미지)으로 0.4초 페이드. 기존 결말 자막 유지 | 결말 효과음(있으면). BGM 낮춤 |
| 0.8s | — | 관리자 밤 방송 시작(MA08~12, 미녹음 시 결말별 MA03/04/05) |
| 음성 중반 | **치지직 1초**: 방송이 단서 단어(소독·정리·외관·포대·문)를 말하는 순간에 맞춰 띠 2~3개, 띠 안에만 단서 이미지. 2회차는 두 번. N.3 띠 규칙 그대로(높이 12~28%, 합쳐 45~60%, 피사체 띠 필수, 남색 판만 2~6px 밀림) | 짧은 잡음(선택. 없어도 된다) |
| +0.3s | 단서 문장 등장. 미색, 한 줄, 화면 아래 1/3 | — |
| +1.0s | 띠가 하나씩 꺼지고 바탕만 남는다. **문장은 남는다** | — |
| +2.0s | 탭하면 다음(밤 정답 제출). 자동 진행 없음 | — |

- 음성이 아직 재생 허용 전(첫 조작 전)이면 음성을 건너뛰고 치지직은 0.8초에 시작한다. 음성은 BGM과 같은 "첫 조작 뒤 재시도" 정책
- `prefers-reduced-motion`이면 띠를 튀기지 않고 1초 동안 정지 상태로 보여준다(N.3과 동일)
- 회차 구성은 코드가 아니라 데이터: `{ loop_n, voice_id, image_ids[], caption }` 5행 + `{ outcome → base_image, fallback_voice_id }` 3행. 치지직 시점은 음원 길이의 40~60% 지점(단어별 타임스탬프는 녹음 뒤 확정)

---

## P.3 프롬프트 (전부 다시 뽑는다. 기존 `output/imagegen/img_P01_night_floor.png`만 참조 이미지로 걸 수 있다)

### P01 · 내 침상 옆 말통 — `P01` · 9:16
**노리는 것** — 기존 P01(말통 구석)의 근접판. 내 담요 끝이 프레임 아래 왼쪽에 걸리고, 팔 뻗으면 닿을 거리에 라벨 없는 말통 하나. "청소 도구"로 읽혀도 된다 — 문장이 냄새를 말하고 그림은 가까움을 말한다. **주황 캡 하나.**
```
[공통 뼈대] [쿠키 뼈대] [밤 단서 뼈대]
Lying on a bunk, eye at mattress level. The frayed edge of a gray blanket
fills the bottom-left corner. An arm's length away on the bare concrete
floor, one rectangular plastic jerry can, unlabeled, flat navy, large in
the middle third, its small screw cap in dull orange (#C8722E) — the only
color. A floor drain grate just beyond it. Nothing else.
[공통 네거티브 — orange only on the single cap. No labels or markings. No drums.]
```

### P02 · 침상 옆을 지나는 바퀴 자국 — `P02` · 9:16
**노리는 것** — 전경이 아니라 근접. 두 줄 자국이 내 침상 다리 바로 옆을 스쳐 프레임 밖으로 나간다. 지나간 뒤다. **주황 없음.**
```
[공통 뼈대] [쿠키 뼈대] [밤 단서 뼈대]
From the floor beside a bunk, very low. A metal bunk leg in the near left.
Two parallel wet wheel tracks, evenly spaced, run diagonally across the
concrete from the near right edge past the bunk leg and out of the frame,
large and clear in the middle third. Nothing else on the floor. No light.
[공통 네거티브 — no vehicle, no footprints, no door in frame]
```

### P03 · 세면대 위 빈 자국 — `P03` · 9:16
**노리는 것** — N07(쿠키 정체 1)과 같은 대상이다. 밤 단서는 **침상에서 본 각도**로 구분한다 — 세면대가 프레임 아래에 걸리고 벽의 밝은 직사각형이 중앙을 채운다. 클리어 때 N07이 정면 근접으로 다시 찍는다. **주황 없음.**
```
[공통 뼈대] [쿠키 뼈대] [밤 단서 뼈대]
From a bunk across the room, slightly below sink height. The rim of a small
metal sink cuts the bottom of the middle third. Above it, filling the middle
third, a clean rectangular patch on the concrete wall, clearly lighter than
the wall, four small screw holes at its corners, nothing hanging. A bunk
frame edge intrudes at one side. Nothing reflects.
[공통 네거티브 — no mirror, no glass, no reflection]
```

### P04 · 배급 포대의 얼룩진 글자 — `P04` · 9:16
**노리는 것** — 4회차의 단어 단서. 배급대 아래 놓인 포대 하나, 옆면에 인쇄된 큰 얼룩. N08(트럭 옆면)과 같은 규칙 — **어떤 글자로도 읽히면 폐기.** 얼룩 테두리에만 옅은 주황.
```
[공통 뼈대] [쿠키 뼈대] [밤 단서 뼈대]
From the floor, very low, beneath the serving counter. One large woven
sack leaning against the counter leg fills the middle third. On its side, a
printed rectangular mark smeared into illegible ink blots — shapes that
cannot be read as letters, worn by the print — with a faint dull orange
(#C8722E) border around the blot. The blanket edge at a corner. Nothing else.
[공통 네거티브 — the mark must NOT be readable as any letters or numbers. Orange only as the faint border.]
```

### P05 · 문 아래에서 올려다본 손잡이 — `P05` · 9:16
**노리는 것** — N09(쿠키 정체 3)와 같은 대상. 밤 단서는 **바닥에 앉은 나**가 기준이다 — 프레임 아래에 내 담요, 문 아래쪽에 무릎 높이 긁힌 자국, 손잡이는 위쪽 끝에 작지만 분명히. 크기 기준이 담요다. **주황 없음.**
```
[공통 뼈대] [쿠키 뼈대] [밤 단서 뼈대]
Sitting on the floor against the steel door, looking up. A gray blanket
edge across the bottom of the frame. The door fills the frame; at knee
height, faint pale scuff marks on the paint; far above, near the top edge,
the handle, small but distinct. No hands, no people, no light under the door.
[공통 네거티브 — no hands, no faces, no light]
```

---

## P.4 검수 (0.5 + N.4에 추가)

- [ ] 1초 미리보기로 봤을 때 뭘 그렸는지 읽힌다 — 실제 치지직 타임라인에 얹어 팀원에게 "뭐였어?"를 묻는다
- [ ] 담요 끝 또는 침상 틀이 프레임 한 구석에 있다 — 없으면 "내가 본 것"이 아니다
- [ ] 피사체 하나, 중앙 1/3, 근접이다 — 복도 전경이면 폐기
- [ ] 검정이 없다. 종이 40% 이상
- [ ] P01·P04만 주황, 지정된 자리에만
- [ ] P04의 얼룩이 어떤 글자로도 읽히지 않는다
- [ ] P03·P05가 N07·N09와 각도가 다르다 — 나란히 놓고 확인
- [ ] 5장의 종이 결이 같고, 바탕(H01·H02)과 같은 결이다

## P.5 순서

1. P01 — v1 P01을 참조로 걸면 같은 물건으로 붙는다. 뼈대가 잡히는지 확인
2. P04 — 규칙이 가장 까다롭다(글자 얼룩). 일찍 실패를 본다
3. P02·P03·P05
4. 5장을 P.2 타임라인에 실제로 얹어 1초 재생하고, 안 읽히는 것은 다시 뽑는다

**총 5장 (P01~P05). 전부 생성, 후처리 없음. 영상은 굽지 않는다 — 코드 타임라인.**

---

## P.6 Codex 브리프 (구현 요약)

- 대상: `frontend/components/screens/DoomTransition.tsx`. 결말 이미지·MA06 재생은 현행 유지
- 입력 데이터: `NIGHT_CLUES = [{loop_n, voice_id, image_ids, caption}]` 5행, `NIGHT_VOICE_FALLBACK = {truck: "MA04", quiet: "MA03", closure: "MA05"}`. 이미지는 `imageMap`에 `nightClueImages(loop_n)` 추가. 방송 대본은 `voiceMap.ts`에 MA08~12로 등록(voice.md 갱신)
- 치지직: 쿠키 컴포넌트의 띠 연출을 재사용(같은 CSS 클래스). 바탕이 검정이 아니라 결말 이미지라는 점만 다르다
- 순서: 바탕 페이드 → 음성 → 치지직 1초 → 문장 잔류 → 탭 대기. 음성 차단 시 음성 생략
- 단서 캡션과 방송 문장은 서버가 밤 시작 때 관찰로 저장한다(`night_interactor` 파편 공개 지점에서 `loop_n` 매칭 파편을 「소등 후」 출처로, 방송은 `statement`). 낮 비트의 파편 공개는 제거. 방송 문장은 시나리오 `BeatDTO`가 아니라 새 `night_broadcasts`(loop_n → text, voice_id)로 둔다
- 접근성: `prefers-reduced-motion` 정지 버전. 문장은 `aria-live="polite"`
- 테스트: 헤드리스로 다섯 밤을 돌려 각 밤에 띠·문장·음성 ID가 표대로 나오는지, 낮 노트에 파편이 없는지

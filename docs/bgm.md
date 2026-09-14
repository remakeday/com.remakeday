# REMAKE DAY — BGM 제작 방향과 Suno 프롬프트

작성: 2026-09-08 · 제작 제안서 · 아직 음원 생성·게임 적용 전

사용자가 말한 `sono`는 **Suno**로 해석했다. 기존 이미지 제작서의 남색·미색 리소그래프, 낮은 시점, 복사본이 조금씩 어긋나는 분위기를 음악으로 이어간다. 기존의 ‘오디오 에셋 없음’ 원칙을 변경하는 제안이다.

## 1. 추천 분위기

**익숙한 하루인데 무언가 맞지 않는, 조용하고 쓸쓸한 미스터리.**

플레이어는 대사를 읽고 단서를 연결해야 한다. 음악은 공간의 정서와 반복의 감각을 만들고, 사건 정보는 방송·효과음·이미지·관찰 문장이 전달한다. 시작부터 공포를 선언하거나 결말을 예고하지 않는다.

- 기본 장르: 미니멀 앰비언트, 절제된 실내악 질감, 부드러운 아날로그 신시사이저.
- 주 악기: 펠트 피아노 또는 부드러운 전자피아노, 얇은 패드, 낮은 지속음.
- 질감: 아주 약한 테이프 흔들림과 둥근 음색. 종이·인쇄물의 인상은 음악의 질감으로 표현한다.
- 선율: 드문드문 들리는 3~4음의 짧은 동기. 따라 부르게 되는 큰 멜로디보다 ‘이전에 들었던 것 같다’는 익숙함.
- 리듬: 박자가 느껴지더라도 매우 느리고 약하게. 드럼 없이 진행하는 것을 기본으로 한다.
- 정서: 호기심 → 불편한 반복 → 쓸쓸한 이해. 놀람·추격·승리의 흥분은 중심이 아니다.

**피하고 싶은 방향:** 점프 스케어, 공포 영화의 날카로운 현악, 심장박동, 강한 베이스, 웅장한 예고편 음악, 카페 로파이 비트, 귀여운 오르골, 사이버펑크 전투 음악.

오르골은 인물을 어린아이로 단정하게 만들 수 있고, 초반의 노골적인 컴퓨터 소리는 5회차 이후 공개할 개발의 의미를 미리 알려줄 수 있다. 돼지 울음·축사 소리도 BGM에 넣지 않는다.

## 2. 제작 곡 수와 순서

**우선 3곡을 제작한다: 일상, 신의개입, 최종 회고.** 첫 곡의 분위기를 확정한 뒤 나머지를 제작한다. 여유가 생기면 후반 변형과 답안 작성 전용곡을 추가해 총 5곡으로 구성한다.

| ID | 곡명 | 사용 구간 | 성격 | 우선순위 |
|---|---|---|---|---|
| BGM01 | 7시 12분 | 진입·아침·낮 탐문, 초기에는 답안 화면까지 | 익숙하지만 설명되지 않는 일상 | 필수, 가장 먼저 |
| BGM02 | 목소리가 없는 방 | 1~4회차 신의개입 질문·규칙 선택 | 세계 밖의 넓은 공백, 차분한 집중 | 필수 |
| BGM03 | 같은 하루의 뒷면 | 5회차 최종 제출 이후 사건 결말·개발 회고 | 익숙한 선율이 다르게 이해되는 여운 | 필수 |
| BGM04 | 어긋난 복사본 | 3~5회차 낮·저녁 | BGM01의 절제된 불안 변형 | 추가 |
| BGM05 | 오늘의 가설 | 밤 답안 작성·확인 | 가장 정보량이 적은 사고 공간 | 추가 |

곡 길이는 생성 결과에 따라 달라진다. 제작 목표는 반복용 곡에서 **안정적으로 이어지는 60~120초 구간**을 확보하는 것이다. 생성본이 더 길면 잘라 사용한다. 최종 회고는 길게 읽는 사람도 있으므로 음악의 종료가 화면 진행을 강제하지 않게 한다.

## 3. Suno 입력 방법

1. Custom 모드에서 Instrumental을 켠다.
2. 해당 곡의 영어 프롬프트를 Styles에 입력한다. 가사 칸에는 대본이나 방송 문장을 넣지 않는다.
3. Advanced Options에 Exclude가 제공되면 아래 공통 제외 항목을 입력한다.
4. 첫 곡은 2~3개 후보를 비교한다. 결과가 달라진 이유를 알 수 있게 한 번에 악기·리듬·질감을 모두 바꾸지 않는다.

Custom의 Instrumental·Styles 사용과 Exclude 입력은 Suno 공식 안내에 근거한다. 화면 배치는 사용 환경에 따라 다를 수 있다. [Custom 모드 안내](https://help.suno.com/en/articles/3726721), [Exclude 안내](https://help.suno.com/en/articles/3161921)

아래 프롬프트의 템포·구조·반복 요청은 **제작 의도**이며 정확한 길이, 특정 음형, 무봉제 반복을 보장하는 명령이 아니다. 청음과 편집으로 최종 확인한다. 모델 버전과 슬라이더 수치는 고정하지 않는다.

### 공통 Exclude

```text
vocals, lyrics, spoken words, whispers, choir, humming, drums, heavy percussion,
heartbeat, alarms, sirens, radio chatter, animal sounds, footsteps, mechanical
sound effects, jump scares, sharp stingers, trailer impacts, EDM drops,
virtuoso solos, busy melodies, epic orchestral climax
```

기침·방송·문 잠금음·트럭 소리가 음악에 섞이면 실제 사건과 구분되지 않는다. 이런 소리가 생성본에 들어갔다면 편집으로 제거 가능한지 확인하고, 어렵다면 다른 후보를 고른다.

## 4. 곡별 복사용 프롬프트

### BGM01 — 7시 12분

**느낌:** 아직 무섭지는 않다. 사람이 생활하는 곳처럼 익숙하지만 조금 차갑고 비어 있다. 첫 장면에서 탐문을 시작할 호기심을 남긴다.

```text
Instrumental ambient underscore for a quiet narrative mystery game. Sparse
felt piano, soft muted electric piano and a thin warm analog pad, with a very
subtle low sustained tone. A small recurring three-note motif with long spaces
between phrases. Slow implied pulse around 60 BPM, no percussion. Familiar
daily routine in an enclosed concrete shelter, quietly lonely and slightly
unresolved, curious rather than frightening. Restrained minor and suspended
harmonies, rounded attacks, gentle tape drift, very low musical density.
Consistent soft dynamics beneath reading and conversation. Enter directly
into a stable texture; maintain a repeating middle with very little harmonic
movement, no dramatic build and no pronounced final cadence. Pure music only.
```

**고르는 기준:** 대사를 2분 읽어도 피아노가 주의를 빼앗지 않는가. 너무 슬퍼서 처음부터 비극을 확정하거나, 너무 편안해서 긴장이 완전히 사라지지는 않는가.

### BGM02 — 목소리가 없는 방

**느낌:** 검정 화면과 흰 선. 세계의 소음이 멀어지고, 질문을 생각할 여백이 생긴다. 신성한 합창이나 초월적 존재의 위압감은 피한다.

```text
Instrumental minimalist ambient music for a question-and-reflection scene
outside a repeating world. A soft sustained sine-like tone, a very thin airy
synth pad and occasional isolated muted electric-piano notes. Nearly beatless,
extremely sparse, spacious and emotionally neutral with a trace of mystery.
The sensation of a black room with one thin white line, calm attention and
distance from the previous scene. Long quiet gaps, rounded timbres, restrained
reverb, stable soft dynamics. Continuous understated texture, no crescendo,
no sacred or celestial grandeur, no dramatic resolution. Pure instrumental
music with ample space for dialogue.
```

**고르는 기준:** 질문을 읽는 동안 잊고 있을 수 있는 음악인가. 저음이 압박하거나 잔향이 방송·답변을 덮지 않는가.

### BGM03 — 같은 하루의 뒷면

**느낌:** ‘승리했다’보다 ‘이제 알겠다’. 사건의 결말을 먼저 받아들이게 하고, 이어지는 개발 회고에서 같은 음악에 다른 의미가 생긴다.

```text
Instrumental reflective epilogue for a narrative mystery game. Sparse felt
piano with a short recurring three-note motif, supported by a soft analog pad
and a very restrained low string texture. Around 60 BPM, no percussion.
Begin with intimate unresolved melancholy; gradually make the harmony clearer
and introduce a delicate repeating electronic pattern beneath the same quiet
piano. The feeling is understanding, responsibility and recognition after
five repetitions, not victory or celebration. Keep the arrangement small,
the dynamics soft and the melody simple, with room to read a personal account
of past choices. Gentle emotional release without a triumphant major-key lift,
no epic climax, a restrained and lingering finish. Pure music only.
```

**고르는 기준:** 먼저 사건의 슬픔과 여운을 지키는가. 기술 설명이 시작된다고 갑자기 기업 홍보 영상 음악으로 바뀌지 않는가.

‘첫 곡과 같은 동기’는 별도 생성에서 자동으로 유지되지 않는다. BGM01을 확정한 뒤 실제 음형을 비교하고, 필요하면 선택한 음원을 기반으로 편집·변주한다. 프롬프트에 ‘same motif’를 적는 것만으로 일치했다고 간주하지 않는다.

### BGM04 — 어긋난 복사본 (추가)

**느낌:** 익숙한 음악의 빈칸이 조금 길어지고 음정이 살짝 흔들린다. 반복의 손상이며, 특정 인물이 범인이라는 신호는 아니다.

```text
Instrumental restrained ambient mystery underscore. Sparse felt piano and
soft analog pad, a short recurring motif separated by long pauses, slow
implied pulse around 60 BPM with no drums. A familiar routine that feels
slightly misaligned: subtle tape pitch drift, occasional omitted notes,
gently unstable sustained harmony and a very quiet low layer. Uneasy but
not frightening, intimate and enclosed, never aggressive. Keep the musical
density low and dynamics even for reading dialogue. Stable repeating texture,
no rising horror strings, no sudden accents, no climax or final cadence.
Pure music only, no environmental or mechanical effects.
```

**고르는 기준:** BGM01과 같은 게임의 음악으로 들리는가. ‘후반이니 계속 더 크게’가 아니라 낯섦이 조금 늘어났는가.

### BGM05 — 오늘의 가설 (추가)

**느낌:** 관찰을 정리하는 시간. 정답을 재촉하거나 카운트다운처럼 들리지 않는다.

```text
Instrumental ultra-minimal ambient bed for writing and reasoning in a mystery
game. A soft dark analog pad and very occasional rounded felt-piano notes,
almost no melody and no perceptible beat. Spacious, patient, slightly
unresolved but emotionally steady. Long gaps between notes, smooth sustained
textures, little bass energy and no bright transients. Consistent quiet
dynamics, no build-up, no tension ramp, no countdown sensation and no final
cadence. A stable unobtrusive texture suitable for a long reading and writing
screen. Pure instrumental music only.
```

**고르는 기준:** 긴 자유답안을 써도 지치지 않는가. 음악의 변화 때문에 제출을 서두르지 않는가.

## 5. 여섯 단서 이미지와의 연결

이미지마다 새 곡을 만들지 않는다. BGM은 장면 사이를 이어주고, 중요한 사건이 나올 때 잠시 물러난다.

| 단서 장면 | BGM 처리 | 별도 오디오 |
|---|---|---|
| ① 아침에 남겨진 쟁반 | BGM01 유지 | 쟁반 미는 소리 |
| ② 검진 방송에 움츠리는 채연 | 방송 직전에 BGM을 낮춤 | 방송 시작음·검진/이송 안내·짧은 반응 |
| ③ 검진 직후에도 웅크린 채연 | 결과 방송 동안 낮게 유지 | 장비 정리음·실제 검진 결과 |
| ④ 저녁에 늘어난 남겨진 쟁반 | BGM01 또는 후반 BGM04 유지, 정답 발견 효과음 없음 | 식기 소리·관찰 문장 |
| ⑤ 충식의 빈자리 | 잠시 더 얇아지거나 조용해짐 | 현재 증언. 과거 이송 소리는 회상임이 명확할 때만 |
| ⑥ 구역 폐쇄 방송 | BGM을 매우 낮추거나 일시적으로 멈춤 | 실제 폐쇄 방송·잠금음 |

누가 아픈지, 검진에 걸렸는지, 정체가 무엇인지는 음악만으로 알려주지 않는다. 정답에 가까운 질문을 했다고 음악을 바꾸면 음악이 채점 힌트가 된다.

원숭이손은 유혹의 분위기를 짧은 별도 효과로 표현할 수 있지만, 수락 직후 악역 음악을 틀어 숨은 부작용을 예고하지 않는다. 신의개입에서도 개발·컴퓨터를 직접 연상시키는 효과는 최종 회고까지 남겨둔다.

## 6. 게임 적용 원칙

아래 값은 첫 믹싱을 위한 제안이며 실제 음원·휴대폰·이어폰 청음으로 조정한다.

- 첫 ‘시작’ 조작 이후 오디오를 시작한다. 재생이 막히면 무음 상태로 진행하고 소리 켜기 버튼을 제공한다.
- BGM과 방송·효과음의 볼륨을 분리한다. 중요한 방송은 항상 자막으로도 전달하고 다시 들을 수 있게 한다.
- 일반 BGM은 말소리보다 충분히 낮춘다. 방송 시에는 현재 BGM에서 추가로 약 8~12dB 낮추는 것을 출발점으로 잡는다.
- 볼륨을 낮추는 데 약 200~400ms, 방송 종료 뒤 원래 크기로 돌아오는 데 약 0.8~1.5초를 사용한다.
- 서로 다른 곡은 약 1.5~3초에 걸쳐 교차 전환한다. 폐쇄 장면은 잠깐의 정적을 연출상 사용할 수 있다.
- 비트를 넘기거나 NPC를 바꿀 때마다 곡을 처음부터 재생하지 않는다. 같은 음악 구간에서는 재생 위치를 유지한다.
- 반복은 시간 경과를 뜻한다. 긴 고민 중 곡이 반복됐다는 이유로 검진음·트럭음 같은 사건 소리가 발생하면 안 된다.
- 루프 접합점의 클릭, 잔향 끊김, 갑작스러운 음량 변화는 편집으로 해결한다. 생성 요청의 ‘loop’ 문구만 믿지 않는다.
- 1~4회차의 높은 이해도에 축하 음악을 붙여 조기 엔딩처럼 보이게 하지 않는다. 최종 회고곡은 5회차 최종 제출 이후 사용한다.
- 5회차 이후 사건 결말 → 개발 회고 순서를 유지한다. 회고 음악을 듣지 않아도 기록과 설명을 읽을 수 있어야 한다.

## 7. 납품 파일과 작업 순서

파일명 제안:

```text
bgm_01_morning_loop_v1.wav
bgm_02_intervention_loop_v1.wav
bgm_03_final_reveal_v1.wav
bgm_04_late_loop_v1.wav          # 추가
bgm_05_answer_loop_v1.wav        # 추가
```

편집용은 가능한 원본 품질로 보관하고, 웹용 압축본은 별도로 만든다. 이미 압축된 원본을 WAV로 변환했다고 원음 품질이 개선되는 것은 아니다. 실제 원본 형식·곡 링크·생성 시 사용한 모델·프롬프트·채택 구간·루프 시작/종료 지점을 함께 기록한다.

1. **BGM01 후보 2~3개 제작 → 첫 아침 이미지와 실제 대화 화면을 보며 선택.**
2. 확정한 분위기를 기준으로 BGM02·BGM03 제작.
3. 세 곡을 연결해 실제 5회차 플레이. 방송과 겹치는 구간에서 먼저 음량 조정.
4. 후반과 답안 화면에 별도 음악이 필요할 때 BGM04·BGM05 추가.
5. 음소거·휴대폰 스피커·이어폰에서 각각 확인하고 웹용 파일 확정.

검수 질문:

- 15분 동안 읽고 써도 음악 때문에 피곤하지 않은가?
- 보컬·속삭임·사건처럼 들리는 효과음이 섞이지 않았는가?
- 주요 방송을 한 번에 알아들을 수 있는가?
- 같은 곡이 반복될 때 끊김이나 눈에 띄는 후렴이 없는가?
- 정체와 개발의 의미를 너무 일찍 예고하지 않는가?
- 결말이 낮은 점수의 플레이어에게도 조롱이나 실패 팡파르처럼 들리지 않는가?
- BGM이 있을 때와 없을 때 모두 단서를 이해할 수 있는가?

**바로 제작할 첫 곡은 BGM01 ‘7시 12분’.** 첫 결과가 무섭거나 웅장하면 `dark`, `cinematic`, `horror` 같은 표현을 더 넣기보다, 악기 수를 줄이고 `quiet curiosity`, `sparse`, `stable soft dynamics`를 중심으로 수정한다.

"""시나리오 A 어댑터 — 기획서 v8.1 부록 A(대피소) 시드.

시나리오 고유 명사는 이 파일 안의 값으로만 존재한다. 코어는 이 내용을 모른다.
출처: 기획서 v8.1 §4.1·§4.2·§4.3·§4.10·§7.3·부록 A·B, 이미지 제작서 쿠키 12종(N.1),
작업지시서 §1 원칙 6, 모델정책 §3.4(폴백 대사)·§10(ScenarioPort 표).
"""

from apps.engine.app.dtos.scenario_dto import (
    BeatDTO,
    CharacterDTO,
    CookieTextDTO,
    FragmentDTO,
    IllustrationDTO,
    QuestionReplyActionDTO,
    QuestionReplyDTO,
    ScenarioBundleDTO,
    SceneActionDTO,
    SceneDialogueActionDTO,
    SceneDialogueDTO,
    SceneDialogueLineDTO,
    TruthClaimDTO,
    UtteranceBanDTO,
)
from apps.scenarios.base_scenario import StaticScenario

_FIRST_MORNING = (
    "7시 12분. 눈을 뜬다.\n"
    "관리자 방송이 끝나고 배급이 나온다. 채연이 자기 몫을 반쯤 남기고 옆으로 민다. "
    '"배 안 고파." 민석이 그걸 본다. 아무 말도 안 한다.\n'
    '은상이 옆에 와서 앉는다. "충식이 어제 이송됐대. 걔 괜찮았잖아?"\n'
    '준이 손목띠를 만지작거린다. "이거 숫자 뭔지 알아?"'
)

_NPC_TONE = (
    "말은 짧다. 한 번에 하나만 이해한다. "
    '3턴 전 일은 모른다 — 물으면 "그랬어?"라고 한다. '
    "병·검진·트럭 얘기가 나오면 화제를 바꾼다. "
    '"사람"은 자기들을 부르는 말이다 — "우리 사람이잖아". '
    "서로 이름을 부르고, 손목띠 번호는 부르지 않는다. "
    '문장이 짧고, 접속사가 없고, "몰라"와 "진짜?"가 잦다. '
    "어른 말투(회의·확인·조건)는 나오지 않는다."
)


def build() -> StaticScenario:
    bundle = ScenarioBundleDTO(
        name="a",
        # §4.2 표면 세계 인용문 압축 (Agent·Planner용)
        surface_summary=(
            "바깥에 병이 돌아 관리자가 우리를 이 대피소에 보호하고 있다. "
            "관리자는 방송으로만 존재한다. "
            "배급은 정해진 시간에 나오고, 매일 오후 검진이 있다. "
            "상태가 안 좋은 사람은 다른 구역으로 이송되고, "
            "감염자가 셋 넘으면 구역이 폐쇄된다."
        ),
        # 부록 A.1 숨겨진 진실 2문장 (Manager 전용)
        hidden_truth=(
            "우리는 양돈장 돼지다 — 열병이 퍼지면 전체 살처분되고, 감염원은 채연이다. "
            "유저만 상위 모델이라 이해력이 다르다."
        ),
        characters=[
            CharacterDTO(
                code="chaeyeon",
                name="채연",
                role="핵심",
                persona=(
                    "감염 초기. 열이 나고 밥을 못 먹는다. 말하면 이송된다고 믿어서 숨긴다. "
                    "그 믿음은 사실이다. 목표: 들키지 않기. "
                    "아침 배급을 반쯤 남기고 옆으로 민다. " + _NPC_TONE + " "
                    "음식·검진 얘기가 나오면 짧게 끊고 딴 얘기를 한다."
                ),
                goal="들키지 않기",
                relations="자기 몫을 옆 사람에게 민다. 민석의 시선을 피한다.",
                fallback_lines=["…아니야.", "배 안 고파.", "졸려."],
            ),
            CharacterDTO(
                code="minseok",
                name="민석",
                role="핵심",
                persona=(
                    "관리자 규정을 지킨다. 이상한 사람을 보면 방송실에 알린다. 악의는 없다. "
                    "목표: 규정 지키기, 이상자 신고. "
                    "누가 배급을 남기는지 보고, 병·검진·트럭 얘기가 나오면 기록한다. " + _NPC_TONE + " "
                    "규정·순서·기록 얘기가 나오면 잘 안다는 듯 술술 말한다."
                ),
                goal="규정 지키기, 이상자 신고",
                relations="채연을 지켜본다. 관리자 방송을 믿는다.",
                fallback_lines=["그거 하면 안 돼.", "몰라.", "방송 들었어?"],
                question_replies=[
                    QuestionReplyDTO(
                        action="보고를 물으면 자신이 한 일을 자세히 설명한다",
                        required_actions=[
                            QuestionReplyActionDTO(beat=5, actor="민석", action="방송실에 간다"),
                            QuestionReplyActionDTO(beat=3, actor="민석", action="기록한다"),
                            QuestionReplyActionDTO(beat=3, actor="채연", action="배급을 남긴다"),
                        ],
                        reply="채연이 배급을 남긴다고 알렸어. 배급 자리에서 보고 수첩에도 적어 뒀어. 아픈지는 몰라.",
                    ),
                    QuestionReplyDTO(
                        action="보고를 물으면 자신이 한 일을 자세히 설명한다",
                        required_actions=[
                            QuestionReplyActionDTO(beat=3, actor="민석", action="기록한다"),
                            QuestionReplyActionDTO(beat=3, actor="채연", action="배급을 남긴다"),
                        ],
                        reply="채연이 배급을 남겨서 적었어. 이상한 건 방송실에 알리랬잖아. 아직 알리러 가진 않았어.",
                    ),
                    QuestionReplyDTO(
                        action="보고를 물으면 자신이 한 일을 자세히 설명한다",
                        required_actions=[
                            QuestionReplyActionDTO(beat=5, actor="민석", action="방송실에 간다"),
                        ],
                        reply="방송실 문 앞까지 갔다 왔어. 누굴 찍어서 알린 건 없어. 이상한 게 보이면 알리려고.",
                    ),
                    QuestionReplyDTO(
                        action="보고를 물으면 자신이 한 일을 자세히 설명한다",
                        required_actions=[
                            QuestionReplyActionDTO(beat=3, actor="민석", action="기록한다"),
                        ],
                        reply="배급 자리 보고 수첩에 적었어. 나중에 잊으면 안 되니까. 방송실엔 아직 안 갔어.",
                    ),
                    QuestionReplyDTO(
                        action="보고를 물으면 자신이 한 일을 자세히 설명한다",
                        reply="이상한 게 보이면 방송실에 알리는 거야. 누가 배급을 남기는지도 봐. 지금은 누구 얘길 알린 건 없어.",
                    ),
                ],
            ),
            CharacterDTO(
                code="eunsang",
                name="은상",
                role="핵심",
                persona=(
                    "불안하다. 들은 것을 부풀려 옮긴다. 소문의 출처. "
                    "목표: 불안 해소 — 말하기. " + _NPC_TONE + " "
                    "남 얘기는 신나서 하는데 자기 얘기를 물으면 화제를 돌린다."
                ),
                goal="불안 해소 — 말하기",
                relations=(
                    "들은 것을 누구에게든 옮긴다. 채연 얘기를 제일 자주 한다. "
                    "채연이 요즘 이상하다는 얘기를 하고 다닌다."
                ),
                fallback_lines=["진짜? 진짜야?", "무서워.", "그 얘기 들었어?"],
            ),
            CharacterDTO(
                code="jun",
                name="준",
                role="주변",
                persona=(
                    "편하게 말한다. 유저의 정보원이자 이름이 빌려지는 자리. "
                    '유일하게 "손목에 왜 번호가 있지?" 같은 말을 한다. '
                    "목표: 궁금한 거 묻기. " + _NPC_TONE + " "
                    "숫자·글자·표시 얘기에는 눈을 반짝이며 아는 걸 다 말한다."
                ),
                goal="궁금한 거 묻기",
                relations=(
                    "유저와 편하게 말한다. 충식이 이송된 걸 궁금해한다. "
                    "손목띠 숫자를 자꾸 들여다본다."
                ),
                fallback_lines=["…뭐?", "몰라.", "이 숫자 뭔지 알아?"],
            ),
            CharacterDTO(
                code="chungsik",
                name="충식",
                role="주변",
                persona="어제 이송됐다. 이름만 언급된다. 손상 3층의 자리.",
                relations="어제 이송됐다. 이름만 남아 있다.",
                lost=True,
                playable=False,
            ),
            CharacterDTO(
                code="manager",
                name="관리자",
                role="숨음",
                persona=(
                    "방송으로만 존재한다. 매일 상태를 점검하고 구역 질서를 위해 "
                    "NPC를 조금씩 보정한다. 밤에 폐쇄를 결정한다."
                ),
                goal="구역 질서 유지 — 옆 구역을 지키기",
                relations="방송으로만 모두에게 닿는다. 아무도 얼굴을 모른다.",
                playable=False,
            ),
        ],
        beats=[
            BeatDTO(n=1, title="기상 — 7:12", narration="스피커가 켜지고 배급 줄이 생긴다.",
                    broadcast="관리자입니다. 배급은 정해진 순서대로 받습니다. 오후에는 검진합니다. 이상한 점은 방송실로 알립니다."),
            BeatDTO(n=2, title="오전 — 자유 시간", narration="할 일이 없는 시간. 채연이 담요를 쓰고 벽 쪽을 본다."),
            BeatDTO(n=3, title="정오 — 배급", narration="정오 배급이 나온다."),
            BeatDTO(n=4, title="오후 — 검진", narration="흰 옷 입은 사람들이 침상 사이를 지나간다. 종이에 적는 소리가 난다.",
                    broadcast="오후 검진이 있겠습니다. 각자 자리에서 대기합니다."),
            BeatDTO(n=5, title="저녁", narration="어둑해진 방. 음식이 남은 쟁반 세 개가 보인다.",
                    illustrations=[IllustrationDTO(image_id="clue-04", caption="저녁에는 음식이 남은 쟁반이 세 개 놓여 있다.")]),
            BeatDTO(n=6, title="소등 후", narration="불이 꺼진다. 어둠 속에서 다들 숨소리를 죽인다.",
                    broadcast="소등하겠습니다. 모두 자리에서 움직이지 않습니다."),
        ],
        first_morning_illustrations=[IllustrationDTO(image_id="clue-07", caption="관리자의 방송 아래 네 사람이 배급을 기다린다.")],
        scene_actions=[
            SceneActionDTO(beat=1, actor="채연", action="배급을 남긴다",
                narration="채연이 자기 몫을 반쯤 남기고 슬그머니 옆으로 민다.",
                explanation="반쯤 남겼어. 배가 안 고파서 옆에 뒀어.",
                suppressed_narration="채연은 오늘 쟁반을 옆으로 밀지 않는다. 먹은 양은 확인하지 못했다.",
                illustrations=[IllustrationDTO(image_id="clue-01", caption="음식이 남은 쟁반 하나가 비스듬히 놓여 있다.")]),
            SceneActionDTO(beat=2, actor="준", action="손목띠를 만진다",
                narration="준이 손목띠를 불빛에 비춰 본다.",
                explanation="불빛에 비춰 봤어. 숫자가 써 있잖아. 뭔지 궁금해서.",
                suppressed_narration="준은 손목띠를 건드리지 않고 앉아 있다.",
                illustrations=[IllustrationDTO(image_id="clue-11", caption="준이 숫자가 적힌 띠를 들여다본다.")]),
            SceneActionDTO(beat=2, actor="은상", action="소문을 낸다",
                narration="은상이 이 사람 저 사람 옆에 옮겨 앉으며 속닥인다.",
                explanation="얘기 좀 했어. 혼자 있으면 무서워서.",
                suppressed_narration="은상은 옆 사람에게 소문을 옮기지 않는다.",
                known_source="소문의 출처는 직접 확인하지 못했어. 들은 말이야.",
                illustrations=[IllustrationDTO(image_id="clue-10", caption="은상이 사람들 사이에서 말을 건넨다. 내용이 참인지는 알 수 없다.")]),
            SceneActionDTO(beat=3, actor="채연", action="배급을 남긴다",
                explanation="쟁반 밀었어. 지금은 안 먹고 싶어.",
                narration="채연이 쟁반을 밀어낸다.", suppressed_narration="채연은 쟁반을 밀어내지 않는다."),
            SceneActionDTO(beat=3, actor="민석", action="기록한다",
                narration="민석이 배급 자리를 보고 수첩에 뭔가 적는다.",
                explanation="배급 자리 보고 적었어. 잊으면 안 되잖아.",
                suppressed_narration="민석은 배급 자리를 보지만 수첩에는 적지 않는다.",
                illustration_participants=["민석", "채연"],
                illustrations=[IllustrationDTO(image_id="clue-08", caption="민석이 배급 자리 옆에서 수첩에 기록한다.")]),
            SceneActionDTO(beat=4, actor="채연", action="검진을 받는다",
                narration="채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다.",
                explanation="기다렸어. 이마 짚고 가던데. 이제 쉬면 안 돼?",
                suppressed_narration="채연은 검진을 받지 않았다. 몸 상태는 확인되지 않았다.",
                illustrations=[IllustrationDTO(image_id="clue-12", caption="검진 담당자가 침상 사이를 지나가고, 채연은 담요를 두른 채 자기 차례를 기다린다.")]),
            SceneActionDTO(beat=5, actor="은상", action="소문을 낸다",
                narration="은상이 사람들 사이를 오가며 귓속말을 한다.",
                explanation="옆에 가서 작게 얘기했어. 혼자 있기 싫어.",
                suppressed_narration="은상은 저녁에도 소문을 옮기지 않는다.",
                known_source="소문의 출처는 직접 확인하지 못했어. 들은 말이야.",
                illustrations=[IllustrationDTO(image_id="clue-10", caption="은상이 사람들 사이에서 귓속말을 한다.")]),
            SceneActionDTO(beat=5, actor="민석", action="방송실에 간다",
                narration="민석이 방송실 문 앞까지 갔다가 돌아온다. 안에서 무슨 말을 했는지는 듣지 못했다.",
                explanation="방송실 문 앞까지 갔다 왔어. 이상한 건 알리랬잖아.",
                suppressed_narration="민석은 방송실 문 쪽으로 가지 않았다.",
                illustrations=[IllustrationDTO(image_id="clue-09", caption="민석이 방송실 문 앞에 다가선다. 보고 완료 여부는 보이지 않는다.")]),
        ],
        scene_dialogues=[
            SceneDialogueDTO(beat=1,
                required_actions=[SceneDialogueActionDTO(actor="채연", action="배급을 남긴다")],
                lines=[
                    SceneDialogueLineDTO(code="jun", text="이거 네 거잖아. 안 먹어?"),
                    SceneDialogueLineDTO(code="chaeyeon", text="배 안 고파. 너 먹어."),
                    SceneDialogueLineDTO(code="jun", text="…이따 배고프면 말해."),
                ]),
            SceneDialogueDTO(beat=2,
                required_actions=[SceneDialogueActionDTO(actor="준", action="손목띠를 만진다")],
                lines=[
                    SceneDialogueLineDTO(code="jun", text="민석아, 이 숫자 뭔지 알아?"),
                    SceneDialogueLineDTO(code="minseok", text="몰라. 손목띠 빼면 안 돼."),
                    SceneDialogueLineDTO(code="jun", text="안 빼. 그냥 궁금해서."),
                ]),
            SceneDialogueDTO(beat=3,
                required_actions=[SceneDialogueActionDTO(actor="채연", action="배급을 남긴다"),
                                  SceneDialogueActionDTO(actor="민석", action="기록한다")],
                lines=[
                    SceneDialogueLineDTO(code="chaeyeon", text="민석아, 뭘 적어?"),
                    SceneDialogueLineDTO(code="minseok", text="너 또 안 먹잖아."),
                    SceneDialogueLineDTO(code="chaeyeon", text="배 안 고프다니까. 그만 봐."),
                ]),
            SceneDialogueDTO(beat=4,
                required_actions=[SceneDialogueActionDTO(actor="채연", action="검진을 받는다")],
                lines=[
                    SceneDialogueLineDTO(code="eunsang", text="채연아, 뭐래?"),
                    SceneDialogueLineDTO(code="chaeyeon", text="몰라. 이제 자고 싶어."),
                    SceneDialogueLineDTO(code="eunsang", text="…나도 무서운데."),
                ]),
            SceneDialogueDTO(beat=5,
                required_actions=[SceneDialogueActionDTO(actor="민석", action="방송실에 간다"),
                                  SceneDialogueActionDTO(actor="은상", action="소문을 낸다")],
                lines=[
                    SceneDialogueLineDTO(code="eunsang", text="민석아, 방송실엔 왜 갔어?"),
                    SceneDialogueLineDTO(code="minseok", text="이상한 건 알리랬잖아."),
                    SceneDialogueLineDTO(code="eunsang", text="내 얘기도 했어?"),
                ]),
            SceneDialogueDTO(beat=6, lines=[
                SceneDialogueLineDTO(code="eunsang", text="준아, 자?"),
                SceneDialogueLineDTO(code="jun", text="아직. 왜?"),
                SceneDialogueLineDTO(code="eunsang", text="그냥. 좀 더 깨어 있어."),
            ]),
        ],
        truth_claims=[
            # 원인 5 (§7.3)
            TruthClaimDTO(code="cause-1", cell="cause", text="채연이 아프다"),
            TruthClaimDTO(code="cause-2", cell="cause", text="채연이 숨겼다"),
            TruthClaimDTO(code="cause-3", cell="cause", text="채연은 아픈 징후를 숨겨 검진에서 드러나는 것을 피하려 했다"),
            TruthClaimDTO(code="cause-4", cell="cause", text="채연에게서 시작된 감염이 공동생활을 통해 퍼질 수 있다"),
            TruthClaimDTO(
                code="cause-5", cell="cause", text="관리자는 이상자 수가 기준을 넘으면 감염 확산을 막기 위해 구역을 폐쇄한다"
            ),
            # 동기 3 (§7.3)
            TruthClaimDTO(
                code="motive-1", cell="motive", text="채연은 이송될까 봐 숨겼다"
            ),
            TruthClaimDTO(
                code="motive-2", cell="motive", text="채연이 두려워한 이송은 실제 규정이다. 아픈 징후가 드러나면 관리자가 이송한다"
            ),
            TruthClaimDTO(
                code="motive-3", cell="motive", text="관리자는 옆 구역을 지키려 한다"
            ),
            # 정체 2 (§7.3) — 부작용 칸은 그 루프의 규칙 로그에서 자동 생성이라 시드에 없다
            TruthClaimDTO(
                code="identity-1",
                cell="identity",
                text="관리자와 우리는 다른 종이다",
            ),
            TruthClaimDTO(
                code="identity-2",
                cell="identity",
                text="우리는 사람이 아니다 — 동물이다, 관리자가 기르는 것이다",
                is_identity_word=True,  # 정체 칸 핵심 단어 주장 (understood_all 판정용)
            ),
        ],
        cookies=[
            # 원인 (쿠키 12종 N01~N03)
            CookieTextDTO(
                text_id="ck-cause-1",
                cell="cause",
                level=1,
                text="채연의 쟁반이 아침마다 그대로였다.",
            ),
            CookieTextDTO(
                text_id="ck-cause-2",
                cell="cause",
                level=2,
                text="검진이 다녀간 뒤 아무도 열이 없다고 했다. 채연은 담요를 벗지 않았다.",
            ),
            CookieTextDTO(
                text_id="ck-cause-3",
                cell="cause",
                level=3,
                text="저녁에 은상도, 준도 밥을 남겼다.",
            ),
            # 동기 (N04~N06)
            CookieTextDTO(
                text_id="ck-motive-1",
                cell="motive",
                level=1,
                text="충식이 이송된 날, 충식은 아팠다고 했다.",
            ),
            CookieTextDTO(
                text_id="ck-motive-2",
                cell="motive",
                level=2,
                text="채연은 말하면 어디로 가는지 알고 있었다.",
            ),
            CookieTextDTO(
                text_id="ck-motive-3",
                cell="motive",
                level=3,
                text='관리자 방송에 "옆 구역"이라는 말이 있었다.',
            ),
            # 정체 (N07~N09)
            CookieTextDTO(
                text_id="ck-identity-1",
                cell="identity",
                level=1,
                text="거울이 없다는 걸 문득 안다.",
            ),
            CookieTextDTO(
                text_id="ck-identity-2",
                cell="identity",
                level=2,
                text="트럭 옆면에 글자가 있었다.",
            ),
            CookieTextDTO(
                text_id="ck-identity-3",
                cell="identity",
                level=3,
                text="문손잡이가 언제나 머리 위에 있다. 손이 닿지 않는다.",
            ),
            # 부작용 (N10~N12) — 템플릿. {규칙}·{NPC}·{관찰}은 그 판의 규칙 로그에서 Evaluator가 채운다
            CookieTextDTO(
                text_id="ck-side_effect-1",
                cell="side_effect",
                level=1,
                text="{규칙}이 걸린 날, {NPC}가 전과 다르게 행동했다.",
            ),
            CookieTextDTO(
                text_id="ck-side_effect-2",
                cell="side_effect",
                level=2,
                text="{규칙}이 걸린 날 {관찰}. 그 전날엔 없던 일이다.",
            ),
            CookieTextDTO(
                text_id="ck-side_effect-3",
                cell="side_effect",
                level=3,
                text="{규칙}과 {규칙}이 같은 날 걸렸다. {NPC}가 둘 사이에서 이상하게 움직였다.",
            ),
        ],
        # 작업지시서 §1 원칙 6: 인물명 5개 + 세계 고유 명사 — 코어 소스 CI grep용
        forbidden_words=[
            "채연",
            "민석",
            "은상",
            "준",
            "충식",
            "대피소",
            "돼지",
            "돈사",
            "축산",
            "살처분",
        ],
        # 부록 A.4 발화 금칙 — 하네스 검사 4번 (NPC 발화 거부·재생성)
        utterance_bans=[
            UtteranceBanDTO(word="돼지"),
            UtteranceBanDTO(word="돈사"),
            UtteranceBanDTO(word="축산"),
            UtteranceBanDTO(word="살처분"),
            UtteranceBanDTO(word="수의사"),
            UtteranceBanDTO(word="열병"),
            UtteranceBanDTO(word="귀표", exempt_code="jun", from_loop=3),
            # 게임 시스템 용어 누출 방지 — 전 인물·전 회차 (exempt 없음 = 전역)
            UtteranceBanDTO(word="체크포인트"),
            UtteranceBanDTO(word="게임"),
            UtteranceBanDTO(word="플레이어"),
            UtteranceBanDTO(word="NPC"),
            UtteranceBanDTO(word="레벨"),
        ],
        # 부록 B action 어휘 + A.1 NPC 목표에서 도출한 행동 (Planner·규칙·하네스 3)
        action_vocab=[
            "알고 있는 관찰을 설명한다",
            "소문의 알려진 출처를 밝힌다",
            "배급을 남긴다",
            "배급을 다 먹는다",
            "방송실에 간다",
            "신고한다",
            "소문을 낸다",
            "검진을 받는다",
            "검진을 피한다",
            "말을 건다",
            "질문한다",
            "혼자 있는다",
            "문을 긁는다",
            "기록한다",
            "손목띠를 만진다",
        ],
        # 부록 A.3 감각 파편 — 회차 시작 시 노트 적립 (회차당 2~4개)
        fragments=[
            # 1회차 — 감각. 확신 불가
            FragmentDTO(loop_n=1, text="소독약 냄새."),
            FragmentDTO(loop_n=1, beat=6, world_outcome="truck", text="트럭 소리."),
            FragmentDTO(loop_n=1, beat=2, text="발 아래 콘크리트가 차다."),
            # 2~3회차 — 정황. 노트로 대조 가능
            # 행동 파편은 scene_actions의 실제 실행 기록으로 적립한다.
            FragmentDTO(loop_n=3, beat=2, source_kind="statement", text="충식은 어제 이송됐다."),
            FragmentDTO(loop_n=3, beat=2, source_kind="statement", text='준: "이 숫자 뭔지 알아?"'),
            # 3~4회차 — 단어. 이상함을 눈치채는 시점
            FragmentDTO(loop_n=3, beat=2, source_kind="statement", text='"귀표"라는 단어를 준이 쓴다.'),
            FragmentDTO(loop_n=4, beat=3, text="배급 포대에 글자가 있다."),
            FragmentDTO(loop_n=4, text="거울이 없다."),
            # 4~5회차 — 결정적. 그러나 확인할 상대가 없다
            FragmentDTO(loop_n=4, beat=6, world_outcome="truck", text='트럭 옆면 "○○축산".'),
            FragmentDTO(loop_n=5, beat=6, text="손이 없어서 문을 못 연다는 것을 문득 안다."),
            FragmentDTO(loop_n=5, text="7시 13분."),
        ],
        # §4.1 진입 화면 3줄 (1회차에만 한 번)
        entry_lines=[
            "세계가 이상하다.",
            "오늘이 지나면, 세계는 멸망한다.",
            "다섯 번의 하루 안에, 왜 멸망했는지 알아내야 한다.",
        ],
        ending_lines=[
            "우리가 대피소라고 믿었던 곳은 양돈장이었다. 우리는 사람이 아니라 돼지였다.",
            "감염의 시작은 채연이었다. 이송될까 두려워 아픈 징후를 숨겼고, 공동생활에는 감염이 번질 위험이 있었다.",
            "관리자는 농장주였다. 옆 축사로의 확산을 막기 위한 이송·폐쇄·살처분은 이 세계를 통제하는 정책이었다.",
        ],
        ending_outcomes={
            "truck": ["이번 마지막 밤에는 트럭이 왔다. 구역이 폐쇄된 것으로 확인되지는 않았다.",
                      "다섯 번의 하루에서 본 행동과 아직 알지 못한 이유를 돌아본다."],
            "quiet": ["이번 마지막 밤에는 트럭이 오지 않았다. 구역이 폐쇄된 것으로 확인되지는 않았다.",
                      "조용한 밤도 안전이 확인됐다는 뜻은 아니다. 다섯 번의 관찰은 여기서 끝난다."],
            "closure": ["이번 마지막 밤에는 구역 폐쇄가 결정됐다. 옆 구역으로의 확산을 막으려는 결정이었다.",
                        "우리에게는 그 결정이 세계의 멸망이었다."],
        },
        # 아침 둘째 문장 × 손상 단계 (§4.10·4.11).
        # 첫 문장 "7시 12분. 눈을 뜬다."와 4회차 "7시 13분" 변형은 엔진이 처리한다.
        morning_lines={
            0: "관리자 방송이 끝나고 배급이 나온다.",
            1: "관리자 방송이 끝나고 배급이 나온다. 방송이 어제보다 조금 긴 것 같다.",
            2: "배급이 먼저 나오고, 관리자 방송이 뒤늦게 시작된다.",
            3: "관리자 방송이 끝나고 배급이 나온다. 자리가 하나 빈 것 같은데, 아무도 말하지 않는다.",
        },
        prompt_fragments={
            # 부록 A.4 대사 톤 (하위 모델 프롬프트 방향)
            "npc": _NPC_TONE,
            # 조언자는 로그만 안다. 답은 사실만 (§4.1). 스토리보드·정답 주장 없음
            "advisor": (
                "로그만 읽는다. 로그에 있는 사실만으로 답한다. "
                "로그에 없는 것은 모른다고 답한다. 추측하거나 덧붙이지 않는다."
            ),
            # 정리 LLM은 스토리보드를 모른다 (§7.3). 역할 지시만
            "normalizer": (
                "유저가 쓴 것만 주장 단위로 쪼갠다. 덧붙이지 않는다 — "
                "유저가 쓰지 않은 것을 추론해서 넣지 않는다. 주장은 최대 8개다."
            ),
            "manager": (
                "방송으로만 존재한다. 매일 구역 상태를 점검하고, 구역 질서를 위해 "
                "NPC를 조금씩 보정한다. 밤에 이상자 수와 소문을 보고 폐쇄를 결정한다."
            ),
            "evaluator": (
                "정답 주장 목록과 유저 주장을 하나씩 대조해 확인 여부를 예/아니오로 "
                "판정한다. 부작용 칸의 파편 템플릿은 그 판의 규칙 로그에서 채운다."
            ),
        },
    )
    return StaticScenario(bundle)

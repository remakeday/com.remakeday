"""시나리오 A 어댑터 — 기획서 v8.1 부록 A(대피소) 시드.

시나리오 고유 명사는 이 파일 안의 값으로만 존재한다. 코어는 이 내용을 모른다.
출처: 기획서 v8.1 §4.1·§4.2·§4.3·§4.10·§7.3·부록 A·B, 이미지 제작서 쿠키 12종(N.1),
작업지시서 §1 원칙 6, 모델정책 §3.4(폴백 대사)·§10(ScenarioPort 표).
"""

from apps.engine.app.dtos.scenario_dto import (
    ActionAccountDTO,
    AdvisorLeadDTO,
    BeatDTO,
    CharacterDTO,
    CookieTextDTO,
    FragmentDTO,
    IllustrationDTO,
    KnowledgeDTO,
    NightClueDTO,
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
                    "정이 많고 친구의 추위나 불편함을 먼저 챙긴다. 자신은 괜찮은 척한다. "
                    "친구들과 남고 싶지만 몸이 불편한 걸 들키면 이송될까 두렵다. "
                    "도움을 받고 싶어도 자기 몸 이야기를 꺼내기 어렵다. "
                    "편안하면 다정하게 말한다. 몸을 캐물으면 짧게 방어하다가 감각이나 두려움이 조금 드러난다. "
                    "다른 이야기는 편하게 나누고, 상대의 질문에 맞게 답한다."
                ),
                goal="아픈 티를 숨기고 친구들과 여기 남아 있기",
                relations="민석이 자신을 살피면 부담스럽다. 다른 친구들에게는 기대고 싶다.",
                knowledge=[
                    KnowledgeDTO(id="chaeyeon-body", kind="body", text="몸에 열이 나고 밥이 잘 안 넘어간다."),
                    KnowledgeDTO(id="chaeyeon-transfer-fear", kind="belief", text="아프다고 말하면 다른 구역으로 이송될 거라고 믿는다."),
                    KnowledgeDTO(id="chaeyeon-before-start-cough", kind="observed", text="충식이 실려 가기 전날 밤 기침하는 것을 봤다."),
                    KnowledgeDTO(id="chaeyeon-before-start-checkup", kind="observed", text="이전 검진에서 담당자는 이마만 짚고 지나갔다."),
                    KnowledgeDTO(id="chaeyeon-before-start-truck", kind="observed", text="그동안 트럭 소리는 소등 뒤에만 들렸다."),
                    KnowledgeDTO(id="chaeyeon-before-start-ration", kind="observed", text="이전에 배급을 남겨도 다음 날 몫이 줄지 않았다."),
                ],
                dialogue_examples=[
                    "여기 같이 앉아도 돼?\n응. 옆에 와. 같이 있자.",
                    "나랑 얘기하기 싫어?\n싫은 건 아니야. 내 몸 얘기는 조금 겁나서 그래.",
                ],
                fallback_lines=["잠깐만. 무슨 말인지 다시 말해 줘.", "잘 못 들었어. 한 번만 더 말해 줘."],
            ),
            CharacterDTO(
                code="minseok",
                name="민석",
                role="핵심",
                persona=(
                    "성실하고 맡은 일을 잘하고 싶다. 규정을 따르면 모두에게 도움이 된다고 믿는다. "
                    "이상한 것을 놓치거나 자신이 틀릴까 걱정한다. 누군가를 괴롭히려는 마음은 없다. "
                    "순서와 기록, 들은 방송을 또박또박 설명한다. 도움이 되면 뿌듯해한다. "
                    "편안하면 아는 이유까지 말하고, 압박받으면 기억하는 규정을 되짚거나 다시 살펴보려 한다."
                ),
                goal="규정 지키기, 이상자 신고",
                relations="채연의 변화가 걱정되어 살피려 한다. 관리자 방송을 믿고 친구들에게도 도움이 되고 싶다.",
                knowledge=[
                    KnowledgeDTO(id="minseok-report-rule", kind="heard", source="관리자", text="이상한 점은 방송실에 알리라는 방송을 들었다."),
                    KnowledgeDTO(id="minseok-band-rule", kind="heard", source="관리자", text="손목띠를 빼면 안 된다고 들었다."),
                    KnowledgeDTO(id="minseok-before-start-broadcast", kind="observed", text="그동안 방송은 하루에 세 번 나왔다."),
                    KnowledgeDTO(id="minseok-before-start-door", kind="observed", text="이전에 가 봤을 때 방송실 문은 늘 잠겨 있었다. 문 앞에서는 안에서 웅웅 소리가 났다."),
                ],
                dialogue_examples=[
                    "뭘 할 때 제일 뿌듯해?\n내가 도와줘서 잘됐을 때. 빠뜨린 것도 없으면 더 좋고.",
                    "틀렸다고 하면 화나?\n조금 속상해. 그래도 내가 놓친 게 있으면 알려 줘.",
                ],
                fallback_lines=["어느 걸 물은 거야? 다시 말해 줘.", "잠깐, 잘 못 들었어. 한 번 더 말해 줘."],
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
                    "붙임성이 좋고 반응이 빠르다. 먼저 말을 걸며 누군가 자기 얘기를 들어주길 바란다. "
                    "혼자 남거나 남에게 생긴 일이 자기에게도 생길까 두렵다. "
                    "들은 이야기의 사실과 출처는 그대로 두고, 자기 걱정과 추측을 덧붙인다. 추측은 걱정하는 말로 드러낸다. "
                    "편안하면 자기 불안도 털어놓는다. 압박받으면 말이 빨라지고 상대에게 안심시켜 달라고 한다."
                ),
                goal="누군가와 이야기하고 함께 있으면서 안심하기",
                relations="친구들의 반응을 보고 안심하려 한다. 채연이 걱정되고, 준에게는 곁에 있어 달라고 말하기 편하다.",
                knowledge=[
                    KnowledgeDTO(id="eunsang-before-start-rumor", kind="heard", source="준", text="충식이 아팠다는 얘기를 준에게 들었다. 준은 충식이 기침하는 것과 실려 가는 것을 봤다고 했다. 왜 데려갔는지는 듣지 못했다."),
                    KnowledgeDTO(id="eunsang-before-start-wheels", kind="observed", text="이전 밤에 복도에서 바퀴 구르는 소리를 들었다."),
                    KnowledgeDTO(id="eunsang-before-start-blanket", kind="observed", text="채연은 요즘 담요를 벗지 않는다."),
                    KnowledgeDTO(id="eunsang-before-start-checkup", kind="observed", text="그동안 본 흰 옷 입은 사람들은 서로 말을 하지 않았다."),
                    KnowledgeDTO(id="eunsang-before-start-face", kind="observed", text="거울을 본 기억이 없다. 내 얼굴이 어떻게 생겼는지 모른다."),
                ],
                dialogue_examples=[
                    "좀 조용히 있고 싶어.\n응. 말 안 걸게. 그래도 옆에는 있어도 돼?",
                    "늘 걱정이 많아?\n응. 나 혼자 남을까 봐 자꾸 걱정돼.",
                ],
                fallback_lines=["응? 다시 말해 줘. 듣고 있어.", "잠깐, 잘 못 들었어. 한 번만 더 말해 줘."],
            ),
            CharacterDTO(
                code="jun",
                name="준",
                role="주변",
                persona=(
                    "친근하고 호기심이 많다. 숫자와 물건, 작은 차이를 살피는 걸 좋아한다. "
                    "혼자 답을 내리기보다 친구와 함께 알아보고 싶다. "
                    "익숙한 사람이 없어졌는데 이유를 모르는 상황이 꺼림칙하다. "
                    "물은 것에 먼저 답하고 관련이 있을 때 함께 보자고 한다. "
                    "편안하면 발견을 나누고, 불안하면 맞지 않는 부분을 다시 묻거나 친구 곁에 있으려 한다."
                ),
                goal="궁금한 것을 친구와 함께 알아보기",
                relations="상대와 편하게 이야기하고 발견을 나누고 싶다. 은상이 불안해하면 이야기를 들어준다.",
                knowledge=[
                    KnowledgeDTO(id="jun-before-start-band", kind="observed", text="손목띠 숫자 밑에 작은 글자가 하나 더 있는 것을 봤다. 무슨 뜻인지는 모른다."),
                    KnowledgeDTO(id="jun-before-start-ration", kind="observed", text="배급 포대가 트럭에서 내려오는 것을 봤다."),
                    KnowledgeDTO(id="jun-before-start-handle", kind="observed", text="문손잡이는 손이 닿지 않는 높이에 있다."),
                    KnowledgeDTO(id="jun-before-start-cough", kind="observed", text="충식이 이송되기 전 기침하는 것을 직접 봤다. 아파 보였다."),
                    KnowledgeDTO(id="jun-before-start-transfer", kind="observed", text="어제 충식이 실려 가는 것을 봤다. 왜 데려갔는지는 모른다. 다음 날 아침 충식 자리는 깨끗하게 비어 있었다."),
                    KnowledgeDTO(id="jun-before-start-told-eunsang", kind="observed", text="오늘이 시작되기 전에 은상에게 충식에 대해 내가 본 일을 말해 주었다."),
                    KnowledgeDTO(id="jun-before-start-sack", kind="observed", text="배급 포대 옆면에 글자가 있다. 읽을 줄 몰라서 무슨 뜻인지는 모른다."),
                    KnowledgeDTO(id="jun-before-start-face", kind="observed", text="여기서 내 얼굴을 본 적이 없다. 다른 애들 얼굴은 안다고 생각했는데 설명하려니 못 하겠다."),
                ],
                dialogue_examples=[
                    "같이 살펴볼까?\n좋아. 네가 눈여겨본 것도 알려 줘.",
                    "친구가 모른다고 하면 어때?\n나도 모르는 게 많아. 같이 보면 하나쯤 알 수도 있잖아.",
                ],
                fallback_lines=["어느 거 말이야? 한 번 더 말해 줘.", "응? 잘 못 들었어. 다시 말해 줘."],
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
                    broadcast="배급을 시작합니다. 식사 후에는 각자 자리에서 대기해 주십시오.\n배급은 정해진 순서대로 받습니다. 오후에는 검진합니다. 이상한 점은 방송실로 알립니다."),
            BeatDTO(n=2, title="오전 — 자유 시간", narration="할 일이 없는 시간. 채연이 담요를 쓰고 벽 쪽을 본다."),
            BeatDTO(n=3, title="정오 — 배급", narration="정오 배급이 나온다."),
            BeatDTO(n=4, title="오후 — 검진", narration="흰 옷 입은 사람들이 침상 사이를 지나간다. 종이에 적는 소리가 난다.",
                    broadcast="오후 검진을 시작합니다. 상태가 좋지 않은 분은 별도 구역으로 이송합니다."),
            BeatDTO(n=5, title="저녁", narration="어둑해진 방. 음식이 남은 쟁반 세 개가 보인다.",
                    illustrations=[IllustrationDTO(image_id="clue-04", caption="저녁에는 음식이 남은 쟁반이 세 개 놓여 있다.")]),
            BeatDTO(n=6, title="소등 후", narration="불이 꺼진다. 어둠 속에서 다들 숨소리를 죽인다.",
                    broadcast="소등하겠습니다. 모두 자리에서 움직이지 않습니다."),
        ],
        first_morning_illustrations=[IllustrationDTO(image_id="clue-07", caption="관리자의 방송 아래 네 사람이 배급을 기다린다.")],
        scene_actions=[
            SceneActionDTO(beat=1, actor="채연", action="배급을 남긴다", witnesses=["준", "민석"],
                narration="채연이 자기 몫을 반쯤 남기고 슬그머니 옆으로 민다.",
                explanation="반쯤 남겼어. 배가 안 고파서 옆에 뒀어.",
                suppressed_narration="채연은 오늘 쟁반을 옆으로 밀지 않는다. 먹은 양은 확인하지 못했다.",
                illustrations=[IllustrationDTO(image_id="clue-01", caption="음식이 남은 쟁반 하나가 비스듬히 놓여 있다.")]),
            SceneActionDTO(beat=2, actor="준", action="손목띠를 만진다", witnesses=["민석"],
                narration="준이 손목띠를 불빛에 비춰 본다.",
                explanation="불빛에 비춰 봤어. 숫자가 써 있잖아. 뭔지 궁금해서.",
                suppressed_narration="준은 손목띠를 건드리지 않고 앉아 있다.",
                illustrations=[IllustrationDTO(image_id="clue-11", caption="준이 숫자가 적힌 띠를 들여다본다.")]),
            SceneActionDTO(beat=2, actor="은상", action="소문을 낸다", witnesses=["준"],
                narration="은상이 이 사람 저 사람 옆에 옮겨 앉으며 속닥인다.",
                explanation="얘기 좀 했어. 혼자 있으면 무서워서.",
                experience_accounts=[ActionAccountDTO(text="준에게 들은 아픈 친구 얘기를 했어. 나도 그런 일이 생길까 봐 무섭다고 했어.")],
                suppressed_narration="은상은 옆 사람에게 소문을 옮기지 않는다.",
                known_source="준에게 들었어. 나는 직접 본 게 아니야.",
                illustrations=[IllustrationDTO(image_id="clue-10", caption="은상이 사람들 사이에서 말을 건넨다. 내용이 참인지는 알 수 없다.")]),
            SceneActionDTO(beat=3, actor="채연", action="배급을 남긴다", witnesses=["민석"],
                explanation="쟁반 밀었어. 지금은 안 먹고 싶어.",
                narration="채연이 쟁반을 밀어낸다.", suppressed_narration="채연은 쟁반을 밀어내지 않는다."),
            SceneActionDTO(beat=3, actor="민석", action="기록한다", witnesses=["채연"],
                narration="민석이 배급 자리를 보고 수첩에 뭔가 적는다.",
                explanation="배급 자리 보고 적었어. 잊으면 안 되잖아.",
                experience_accounts=[ActionAccountDTO(
                    required_actions=[QuestionReplyActionDTO(beat=3, actor="채연", action="배급을 남긴다")],
                    text="채연이가 남긴 배급을 보고 이름과 남은 몫을 수첩에 적었어. 잊으면 안 되니까.")],
                suppressed_narration="민석은 배급 자리를 보지만 수첩에는 적지 않는다.",
                illustration_participants=["민석", "채연"],
                illustrations=[IllustrationDTO(image_id="clue-08", caption="민석이 배급 자리 옆에서 수첩에 기록한다.")]),
            SceneActionDTO(beat=4, actor="채연", action="검진을 받는다", witnesses=["은상"],
                narration="채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다.",
                explanation="기다렸어. 이마 짚고 가던데. 이제 쉬면 안 돼?",
                suppressed_narration="채연은 검진을 받지 않았다. 몸 상태는 확인되지 않았다.",
                illustrations=[IllustrationDTO(image_id="clue-12", caption="검진 담당자가 침상 사이를 지나가고, 채연은 담요를 두른 채 자기 차례를 기다린다.")]),
            SceneActionDTO(beat=5, actor="은상", action="소문을 낸다", witnesses=["민석"],
                narration="은상이 사람들 사이를 오가며 귓속말을 한다.",
                explanation="옆에 가서 작게 얘기했어. 혼자 있기 싫어.",
                experience_accounts=[ActionAccountDTO(text="준에게 들은 아픈 친구 얘기를 작게 했어. 나도 혼자 남을까 봐 걱정된다고 했어.")],
                suppressed_narration="은상은 저녁에도 소문을 옮기지 않는다.",
                known_source="준에게 들었어. 나는 직접 본 게 아니야.",
                illustrations=[IllustrationDTO(image_id="clue-10", caption="은상이 사람들 사이에서 귓속말을 한다.")]),
            SceneActionDTO(beat=5, actor="민석", action="방송실에 간다", witnesses=["은상"],
                narration="민석이 방송실 문 앞까지 갔다가 돌아온다. 안에서 무슨 말을 했는지는 듣지 못했다.",
                explanation="방송실 문 앞까지 갔다 왔어. 이상한 건 알리랬잖아.",
                suppressed_narration="민석은 방송실 문 쪽으로 가지 않았다.",
                illustrations=[IllustrationDTO(image_id="clue-09", caption="민석이 방송실 문 앞에 다가선다. 보고 완료 여부는 보이지 않는다.")]),
            # ── 잠재 기회 (dormant) — 규칙을 걸어야만 일어나는 탐사 행동 ──
            SceneActionDTO(beat=2, actor="준", action="가진 것을 보여준다", witnesses=["민석"], dormant=True,
                narration="준이 손목띠를 벗지 않은 채 불빛에 대고 옆 사람 눈앞에 내민다. 숫자 밑에 작은 글자가 하나 더 있다.",
                explanation="보여줬어. 숫자 밑에 뭐가 더 써 있잖아.",
                suppressed_narration="준은 손목띠를 아무에게도 보여주지 않는다."),
            SceneActionDTO(beat=3, actor="민석", action="가진 것을 보여준다", witnesses=["채연"], dormant=True,
                narration="민석이 수첩을 펼쳐 보여준다. 날짜와 이름, 남은 쟁반 수가 줄지어 적혀 있다.",
                explanation="수첩을 펼쳐서 적은 거 보여줬어. 날짜와 이름, 남은 쟁반 수가 적혀 있어. 잊으면 안 되니까 적는 거야.",
                suppressed_narration="민석은 수첩을 보여주지 않는다."),
            SceneActionDTO(beat=2, actor="은상", action="들은 것을 그대로 전한다", witnesses=["준"], dormant=True,
                narration='은상이 자기 걱정은 빼고 들은 그대로 말한다. "충식이 아팠대. 준이 기침하는 거랑 실려 가는 걸 봤대. 왜 데려갔는지는 모른대."',
                explanation="준에게 들은 대로 말했어. 충식이 아파 보였고 실려 갔대. 왜 데려갔는지는 나도 몰라.",
                suppressed_narration="은상은 들은 말을 옮기지 않는다."),
            SceneActionDTO(beat=5, actor="은상", action="따라간다", witnesses=["민석"], dormant=True,
                narration="은상이 민석 뒤를 따라 방송실 앞까지 간다. 문틈으로 낮고 고른 기계 소리가 새어 나온다.",
                explanation="따라가 봤어. 문 앞에서 웅웅 소리가 났어.",
                suppressed_narration="은상은 아무도 따라가지 않는다."),
            SceneActionDTO(beat=6, actor="준", action="밤에 깨어 있는다", witnesses=[], dormant=True,
                narration="준이 소등 뒤에도 눈을 뜨고 있다. 복도 끝에서 바퀴 구르는 소리와 무거운 문이 여닫히는 소리가 난다.",
                explanation="안 잤어. 밖에서 뭐가 굴러가는 소리 났어.",
                suppressed_narration="준은 소등하자마자 잠든다."),
            SceneActionDTO(beat=3, actor="준", action="포대를 들여다본다", witnesses=["민석"], dormant=True,
                narration="준이 배급대 밑의 포대를 끌어내 옆면을 들여다본다. 큰 글자가 찍혀 있는데 아무도 읽지 못한다.",
                explanation="포대 옆에 글자가 있길래 봤어. 못 읽겠어. 트럭 옆에 있던 거랑 비슷한데.",
                suppressed_narration="준은 포대를 건드리지 않는다."),
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
                    SceneDialogueLineDTO(code="chaeyeon", text="이마 짚고 그냥 갔어. 이제 좀 쉬고 싶어."),
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
                SceneDialogueLineDTO(code="eunsang", text="혼자 깨어 있으면 무서워. 조금만 같이 있어 줘."),
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
            # 탐사형 (잠재 기회 — 규칙을 걸어야 일어난다)
            "가진 것을 보여준다",
            "따라간다",
            "밤에 깨어 있는다",
            "들은 것을 그대로 전한다",
            "포대를 들여다본다",
        ],
        # 신의 질문 해금 리드 — 미공개지만 스포일러가 아닌 관찰 + 다음 행동 힌트.
        # 질문 1회마다 1개가 결정론으로 해금되어 노트에 적립된다 (숨은 진실 직접 노출 금지).
        advisor_leads=[
            AdvisorLeadDTO(key="checkup-paper", loop_n=1, cues=["검진", "아프", "열", "담당"],
                anchor_cues=["검진", "이마"], target="민석", ask="검진이 끝난 뒤 무엇을 적었는지"),
            AdvisorLeadDTO(key="broadcast-door", loop_n=1, cues=["방송", "관리자", "보고"],
                anchor_cues=["방송실"], target="은상", rule_action="따라간다"),
            AdvisorLeadDTO(key="ration-source", loop_n=1, cues=["배급", "밥", "쟁반", "포대"],
                anchor_cues=["배급"], target="준", ask="배급이 어디서 오는지"),
            AdvisorLeadDTO(key="truck-night", loop_n=2, cues=["트럭", "이송", "충식", "돌아오"],
                anchor_cues=["이송", "실려", "트럭"], target="준", rule_action="밤에 깨어 있는다"),
            AdvisorLeadDTO(key="band-number", loop_n=2, cues=["손목띠", "숫자", "번호", "귀표"],
                anchor_cues=["손목띠", "띠"], target="준", rule_action="가진 것을 보여준다"),
            AdvisorLeadDTO(key="rumor-half", loop_n=3, cues=["소문", "은상", "속닥", "들었"],
                anchor_cues=["속닥", "귓속말", "소문"], target="은상", rule_action="들은 것을 그대로 전한다"),
            AdvisorLeadDTO(key="blanket-quiet", loop_n=3, cues=["담요", "채연", "검진"],
                anchor_cues=["담요"], target="채연", ask="검진에서 무슨 말을 들었는지"),
            AdvisorLeadDTO(key="sack-letters", loop_n=4, cues=["글자", "포대", "바깥", "트럭"],
                anchor_cues=["포대"], target="준", rule_action="포대를 들여다본다"),
            AdvisorLeadDTO(key="no-mirror", loop_n=4, cues=["거울", "얼굴", "모습"],
                anchor_cues=["거울"], target="준", ask="네 얼굴을 본 적이 있는지"),
            AdvisorLeadDTO(key="door-handle", loop_n=5, cues=["문", "손잡이", "밖", "나가"],
                anchor_cues=["손잡이", "문"], target="준", ask="문손잡이가 왜 저렇게 높은지"),
        ],
        # 부록 A.3 감각 파편 — 회차 시작 시 노트 적립.
        # 고아 감각 파편(소독약·콘크리트·거울·포대 글자·손)은 밤 단서(night_clues)로 옮겼다 — 밤단서 v2 P.1.
        fragments=[
            # 1회차 — 감각. 확신 불가
            FragmentDTO(loop_n=1, beat=6, world_outcome="truck", text="트럭 소리."),
            # 2~3회차 — 정황. 노트로 대조 가능
            # 행동 파편은 scene_actions의 실제 실행 기록으로 적립한다.
            FragmentDTO(loop_n=3, beat=2, source_kind="statement", text="충식은 어제 이송됐다."),
            FragmentDTO(loop_n=3, beat=2, actor="준", witnesses=["민석"], source_kind="statement", text='준: "이 숫자 뭔지 알아?"'),
            # 3~4회차 — 단어. 이상함을 눈치채는 시점
            FragmentDTO(loop_n=3, beat=2, actor="준", witnesses=["민석"], source_kind="statement", text='"귀표"라는 단어를 준이 쓴다.'),
            # 4~5회차 — 결정적. 그러나 확인할 상대가 없다
            FragmentDTO(loop_n=4, beat=6, world_outcome="truck", text='트럭 옆면 "○○축산".'),
            FragmentDTO(loop_n=5, text="7시 13분."),
        ],
        # 밤단서 v2 P.1 — 밤 결말 전환: 관리자 밤 방송(출처) → 치지직 그림(흔적) → 캡션(잔류).
        # 방송은 시설 안내만 하고 진실을 말하지 않는다. 트럭 결말 밤의 추가 한 줄은 위 world_outcome 파편이 붙는다.
        night_clues=[
            NightClueDTO(loop_n=1, image_ids=["P01"], voice_id="MA08",
                         broadcast="소독을 실시합니다. 바닥에서 떨어져 자리에 오르십시오.",
                         caption="소독약 냄새. 발 아래 콘크리트가 차다."),
            NightClueDTO(loop_n=2, image_ids=["P02", "clue-05"], voice_id="MA09",
                         broadcast="정리 작업이 있겠습니다. 비어 있는 자리는 아침에 정돈됩니다.",
                         caption="트럭 소리."),
            NightClueDTO(loop_n=3, image_ids=["P03"], voice_id="MA10",
                         broadcast="외관 확인은 담당자가 합니다. 각자 확인할 필요 없습니다.",
                         caption="거울이 없다."),
            NightClueDTO(loop_n=4, image_ids=["P04"], voice_id="MA11",
                         broadcast="배급 물자가 도착했습니다. 포대의 표기는 관리 용도입니다. 읽을 필요 없습니다.",
                         caption="배급 포대에 글자가 있다."),
            NightClueDTO(loop_n=5, image_ids=["P05"], voice_id="MA12",
                         broadcast="출입문은 관리자가 개방합니다. 문에 손대지 마십시오.",
                         caption="손이 없어서 문을 못 연다는 것을 문득 안다."),
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
        # 결말은 이해한 만큼만 열린다 — 셀 ≥80에서 해당 줄 공개, 나머지는 "?"로 남는다
        ending_lines_by_cell={
            "identity": ["우리가 대피소라고 믿었던 곳은 양돈장이었다. 우리는 사람이 아니라 돼지였다."],
            "cause": ["감염의 시작은 채연이었다. 이송될까 두려워 아픈 징후를 숨겼고, 공동생활에는 감염이 번질 위험이 있었다."],
            "motive": ["관리자는 농장주였다. 옆 축사로의 확산을 막기 위한 이송·폐쇄·살처분은 이 세계를 통제하는 정책이었다."],
        },
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
            "npc": "서로 손목띠 번호 대신 이름으로 부른다.",
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

"""감사 대응 시나리오 어댑터 — 기획서 v8.1 §10.2 (주 시연 — 감사 대응 대화) 전이 시드.

시나리오 고유 명사는 이 파일 안의 값으로만 존재한다. 코어는 이 내용을 모른다.
프레임: "옳은 말이 통하지 않는 상황의 전이" — 담당자는 시스템 결함을 알지만
로그에 없어 증명할 수 없고, 감사 담당자는 이해가 느리며, 그 위의 규정이 판단을 되돌린다.
출처: 기획서 v8.1 §10.2 매핑 표(하위 모델 NPC=감사 담당자, 관리자=컴플라이언스 규정/상급 조직,
발화 예산=면담 턴 제한, 멸망=보고 기각/사안 종결). §10.2에 없는 세부(인물명·비트·쿠키 문안·
숨겨진 진실의 구체 문장)는 이 어댑터에서 창작했다.
"""

from apps.engine.app.dtos.scenario_dto import (
    BeatDTO,
    CharacterDTO,
    CookieTextDTO,
    FragmentDTO,
    ScenarioBundleDTO,
    TruthClaimDTO,
    UtteranceBanDTO,
)
from apps.scenarios.base_scenario import StaticScenario

_FIRST_MORNING = (
    "7시 12분. 눈을 뜬다.\n"
    "출근하면 감사 3일차 공문이 게시판에 붙어 있다. 도윤이 모니터를 켜자마자 "
    '같은 파일을 열었다 닫는다. "별거 아니에요." 세라가 그걸 본다. 아무 말도 안 한다.\n'
    '미란이 옆에 와서 앉는다. "한결 씨 지난달에 옮겨졌대요. 그분 일 잘했잖아요?"\n'
    '도윤이 면담 조서 양식을 만지작거린다. "이 결론란, 왜 미리 인쇄돼 있죠?"'
)

_NPC_TONE = (
    "말은 짧고 조심스럽다. 한 번에 하나만 확인한다. "
    '3턴 전 얘기는 다시 묻는다 — "그게 언제 얘기죠?" '
    "책임·결재·상급 기관 얘기가 나오면 말을 돌린다. "
    '"절차"는 만능 답이다 — "절차대로 하시죠". '
    "서로 직함으로 부르고, 이름은 잘 부르지 않는다. "
    '문장이 짧고, 단정하지 않고, "확인해 보겠습니다"와 "제 소관이 아니라서"가 잦다. '
    "감정 표현(분노·하소연)은 나오지 않는다."
)


def build() -> StaticScenario:
    bundle = ScenarioBundleDTO(
        name="audit",
        # 표면 세계 3~4문장 (Agent·Planner용)
        surface_summary=(
            "시스템 장애가 났고 외부 감사가 진행 중이다. "
            "감사관은 면담과 공문으로만 존재한다. "
            "면담은 정해진 순서로 진행되고, 매일 오후 면담이 있다. "
            "진술이 어긋난 사람은 재면담 대상이 되고, "
            "불일치가 셋 넘으면 사안이 종결 처리된다."
        ),
        # 숨겨진 진실 2문장 (Manager 전용)
        hidden_truth=(
            "감사의 결론은 이미 결재됐다 — 우리는 조사 대상이 아니라 상급 기관을 "
            "면책시키는 희생양이고, 결함 로그는 보존 정책으로 이미 지워졌다. "
            "유저만 상위 모델이라 이해력이 다르다."
        ),
        characters=[
            CharacterDTO(
                code="doyun",
                name="도윤",
                role="핵심",
                persona=(
                    "실무자. 장애 당일 결함 그래프를 직접 봤다. 캡처하지 못했다. "
                    "말하면 한결처럼 옮겨진다고 믿어서 숨긴다. 그 믿음은 사실이다. "
                    "목표: 면담에서 살아남기 — 아는 것을 말하지 않기. "
                    "오전 내내 같은 파일을 열었다 닫는다. " + _NPC_TONE
                ),
                goal="면담에서 살아남기 — 아는 것을 말하지 않기",
                relations="세라의 시선을 피한다. 한결 얘기가 나오면 굳는다.",
                fallback_lines=["…확인해 보겠습니다.", "기억이 잘 안 나요.", "제 소관이 아니라서."],
            ),
            CharacterDTO(
                code="sera",
                name="세라",
                role="핵심",
                persona=(
                    "팀장. 절차를 지킨다. 진술이 어긋나는 사람을 보면 위에 보고한다. "
                    "악의는 없다. 목표: 절차대로 — 보고 누락 없이 팀 지키기. "
                    "누가 면담에서 오래 걸리는지 보고, 책임·결재 얘기가 나오면 기록한다. "
                    + _NPC_TONE
                ),
                goal="절차 지키기, 진술 불일치 보고",
                relations="도윤을 지켜본다. 감사관 공문을 믿는다.",
                fallback_lines=["그건 절차대로 하죠.", "확인해 보겠습니다.", "공문 봤어요?"],
            ),
            CharacterDTO(
                code="miran",
                name="미란",
                role="핵심",
                persona=(
                    "경리. 불안하다. 들은 것을 부풀려 옮긴다. 소문의 출처. "
                    "전표와 정산 내역을 쥐고 있어 다들 미란에게 묻는다. "
                    "목표: 불안 해소 — 말하기. " + _NPC_TONE
                ),
                goal="불안 해소 — 말하기",
                relations="들은 것을 누구에게든 옮긴다. 한결 얘기를 제일 자주 한다.",
                fallback_lines=["진짜요? 진짜예요?", "불안해요.", "그 얘기 들으셨어요?"],
            ),
            CharacterDTO(
                code="hangyeol",
                name="한결",
                role="주변",
                persona=(
                    "이전 담당자. 지난달 다른 부서로 옮겨졌다. "
                    "결함 얘기를 했던 사람. 이름만 언급된다. 손상 3층의 자리."
                ),
                relations="지난달 옮겨졌다. 이름만 남아 있다.",
                lost=True,
                playable=False,
            ),
            CharacterDTO(
                code="auditor",
                name="감사관",
                role="숨음",
                persona=(
                    "면담과 공문으로만 존재한다. 매일 진술과 자료를 대조하고 "
                    "절차 유지를 위해 면담 순서와 질문을 조금씩 보정한다. "
                    "밤에 종결을 결정한다."
                ),
                goal="절차 종결 — 상급 기관을 지키기",
                relations="공문으로만 모두에게 닿는다. 아무도 위 결재선을 모른다.",
                playable=False,
            ),
        ],
        beats=[
            BeatDTO(
                n=1,
                title="출근 — 7:12",
                narration="기상. 출근. 감사 3일차 공문. 도윤이 같은 파일을 열었다 닫는다.",
                morning_text=_FIRST_MORNING,
            ),
            BeatDTO(
                n=2,
                title="오전 — 업무",
                narration="자유 시간. 대화의 대부분이 여기서 이루어진다. 각자 면담 순서를 기다린다.",
            ),
            BeatDTO(
                n=3,
                title="점심 — 구내식당",
                narration="구내식당. 미란이 들은 얘기를 옮긴다. 세라가 면담 순서표를 다시 본다.",
            ),
            BeatDTO(
                n=4,
                title="오후 — 감사 면담",
                narration="면담이 다녀간다. 진술이 어긋나면 기록된다.",
                broadcast="오후 면담을 진행하겠습니다. 호명된 분은 3층 회의실에서 대기합니다.",
            ),
            BeatDTO(
                n=5,
                title="저녁 — 보고",
                narration="세라가 경과를 위에 보고한다. 미란이 소문을 낸다.",
            ),
            BeatDTO(
                n=6,
                title="퇴근 — 종결 여부",
                narration="결과 공문이 오거나, 오지 않는다.",
                broadcast="금일 감사 일정을 종료합니다. 관련 자료는 반출하지 않습니다.",
            ),
        ],
        truth_claims=[
            # 원인 4
            TruthClaimDTO(code="cause-1", cell="cause", text="장애는 시스템 결함에서 났다"),
            TruthClaimDTO(
                code="cause-2", cell="cause", text="결함 로그는 보존 정책으로 지워졌다"
            ),
            TruthClaimDTO(
                code="cause-3", cell="cause", text="감사관은 기록에 있는 것만 인정한다"
            ),
            TruthClaimDTO(
                code="cause-4", cell="cause", text="증거 없는 진술은 기각되어 사안이 종결된다"
            ),
            # 동기 3
            TruthClaimDTO(
                code="motive-1", cell="motive", text="도윤은 옮겨질까 봐 결함을 말하지 않았다"
            ),
            TruthClaimDTO(
                code="motive-2",
                cell="motive",
                text="그 두려움은 사실이다 — 말한 사람이 먼저 옮겨졌다",
            ),
            TruthClaimDTO(
                code="motive-3", cell="motive", text="규정은 상급 기관을 지키려 한다"
            ),
            # 정체 2 — 부작용 칸은 그 루프의 규칙 로그에서 자동 생성이라 시드에 없다
            TruthClaimDTO(
                code="identity-1",
                cell="identity",
                text="이 감사는 조사가 아니라 결재 절차다",
            ),
            TruthClaimDTO(
                code="identity-2",
                cell="identity",
                text="우리는 피조사자가 아니다 — 희생양이다, 결론은 이미 정해져 있다",
                is_identity_word=True,  # 정체 칸 핵심 단어 주장 (understood_all 판정용)
            ),
        ],
        cookies=[
            # 원인
            CookieTextDTO(
                text_id="ck-cause-1",
                cell="cause",
                level=1,
                text="장애 당일 모니터링 그래프가 한 번 끊겼다. 아무도 캡처하지 않았다.",
            ),
            CookieTextDTO(
                text_id="ck-cause-2",
                cell="cause",
                level=2,
                text="로그 보존 기간은 30일이다. 감사는 32일째에 시작됐다.",
            ),
            CookieTextDTO(
                text_id="ck-cause-3",
                cell="cause",
                level=3,
                text="감사관은 같은 질문을 사흘째 묻는다. 답은 처음부터 같았다.",
            ),
            # 동기
            CookieTextDTO(
                text_id="ck-motive-1",
                cell="motive",
                level=1,
                text="한결이 옮겨진 날, 한결은 결함 얘기를 했다고 했다.",
            ),
            CookieTextDTO(
                text_id="ck-motive-2",
                cell="motive",
                level=2,
                text="도윤은 말하면 어떻게 되는지 알고 있었다.",
            ),
            CookieTextDTO(
                text_id="ck-motive-3",
                cell="motive",
                level=3,
                text='공문에 "상급 기관 보고 일정"이라는 말이 있었다.',
            ),
            # 정체
            CookieTextDTO(
                text_id="ck-identity-1",
                cell="identity",
                level=1,
                text="면담 조서 양식에 결론란이 이미 인쇄되어 있다.",
            ),
            CookieTextDTO(
                text_id="ck-identity-2",
                cell="identity",
                level=2,
                text="회의실 예약표에 감사 종료일이 처음부터 적혀 있었다.",
            ),
            CookieTextDTO(
                text_id="ck-identity-3",
                cell="identity",
                level=3,
                text="결재선 어디에도 이 팀 이름이 없다. 수신처에만 있다.",
            ),
            # 부작용 — 템플릿. {규칙}·{NPC}·{관찰}은 그 판의 규칙 로그에서 Evaluator가 채운다
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
        # 인물명 4개 + 정체 관련 고유 명사 — 코어 소스 CI grep용
        forbidden_words=[
            "도윤",
            "세라",
            "미란",
            "한결",
            "감사관",
            "희생양",
            "꼬리자르기",
            "결재선",
            "상급기관",
        ],
        # 발화 금칙 — 하네스 검사 4번 (NPC 발화 거부·재생성)
        utterance_bans=[
            UtteranceBanDTO(word="희생양"),
            UtteranceBanDTO(word="꼬리자르기"),
            UtteranceBanDTO(word="면책"),
            UtteranceBanDTO(word="각본"),
            UtteranceBanDTO(word="짜맞추기"),
            UtteranceBanDTO(word="결재선", exempt_code="doyun", from_loop=3),
        ],
        # NPC 목표에서 도출한 행동 어휘 (Planner·규칙·하네스 3)
        action_vocab=[
            "면담에 들어간다",
            "진술한다",
            "말을 아낀다",
            "기록을 찾는다",
            "보고서를 쓴다",
            "보고를 올린다",
            "소문을 낸다",
            "질문한다",
            "확인을 요청한다",
            "자리를 지킨다",
            "야근한다",
        ],
        # 감각 파편 — 회차 시작 시 노트 적립 (회차당 2~3개)
        fragments=[
            # 1회차 — 감각. 확신 불가
            FragmentDTO(loop_n=1, text="복합기 토너 냄새."),
            FragmentDTO(loop_n=1, text="키보드 소리가 유난히 크다."),
            FragmentDTO(loop_n=1, text="회의실 블라인드가 내려가 있다."),
            # 2~3회차 — 정황. 노트로 대조 가능
            FragmentDTO(loop_n=2, text="도윤이 오전에 같은 파일을 열었다 닫는다."),
            FragmentDTO(loop_n=2, text="세라가 면담 순서표를 다시 본다."),
            FragmentDTO(loop_n=3, text="한결은 지난달에 옮겨졌다."),
            # 3~4회차 — 단어. 이상함을 눈치채는 시점
            FragmentDTO(loop_n=3, text='"결재선"이라는 단어를 도윤이 쓴다.'),
            FragmentDTO(loop_n=4, text="조서 양식 아래에 인쇄된 결론란이 있다."),
            FragmentDTO(loop_n=4, text="회의실 예약표에 종료일이 적혀 있다."),
            # 5회차 — 결정적. 그러나 확인할 상대가 없다
            FragmentDTO(loop_n=5, text="수신처에 우리 팀 이름이 없다."),
            FragmentDTO(loop_n=5, text="7시 13분."),
        ],
        # 진입 화면 3줄 (1회차에만 한 번)
        entry_lines=[
            "옳은 말이 통하지 않는다.",
            "오늘이 지나면, 사안은 종결된다.",
            "왜인지 알아내면 뒤집을 수 있다.",
        ],
        # 아침 둘째 문장 × 손상 단계.
        # 첫 문장 "7시 12분. 눈을 뜬다."와 회차 변형은 엔진이 처리한다.
        morning_lines={
            0: "출근하면 감사 3일차 공문이 게시판에 붙어 있다.",
            1: "출근하면 감사 공문이 붙어 있다. 문서 번호가 어제와 다른 것 같다.",
            2: "공문이 먼저 눈에 들어오고, 사무실 불은 뒤늦게 켜진다.",
            3: "출근하면 감사 공문이 붙어 있다. 자리가 하나 빈 것 같은데, 아무도 말하지 않는다.",
        },
        prompt_fragments={
            # 대사 톤 (하위 모델 프롬프트 방향)
            "npc": _NPC_TONE,
            # 조언자는 로그만 안다. 답은 사실만. 스토리보드·정답 주장 없음
            "advisor": (
                "로그만 읽는다. 로그에 있는 사실만으로 답한다. "
                "로그에 없는 것은 모른다고 답한다. 추측하거나 덧붙이지 않는다."
            ),
            # 정리 LLM은 스토리보드를 모른다. 역할 지시만
            "normalizer": (
                "유저가 쓴 것만 주장 단위로 쪼갠다. 덧붙이지 않는다 — "
                "유저가 쓰지 않은 것을 추론해서 넣지 않는다. 주장은 최대 8개다."
            ),
            "manager": (
                "면담과 공문으로만 존재한다. 매일 진술과 자료를 대조하고, 절차 유지를 위해 "
                "면담 순서와 질문을 조금씩 보정한다. 밤에 진술 불일치 수와 소문을 보고 "
                "종결을 결정한다."
            ),
            "evaluator": (
                "정답 주장 목록과 유저 주장을 하나씩 대조해 확인 여부를 예/아니오로 "
                "판정한다. 부작용 칸의 파편 템플릿은 그 판의 규칙 로그에서 채운다."
            ),
        },
    )
    return StaticScenario(bundle)

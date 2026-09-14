"""core_probes.py — E7 Core 역할 프로브 코퍼스와 실행기 (docs/model_evaluation.md §2.4).

2026-09-09 `real-model-artifacts/ollama-probes.py`의 DB-free 하네스를 그대로 이식했다.
코퍼스(공개 관찰 11건 · 테스터1 질문 12개 · 사전등록 통제 10개)는 그때와 동일하다 — 비교 가능해야 하므로 바꾸지 않는다.
"""

import uuid
from types import SimpleNamespace as N

from apps.engine.app.dtos.event_log_dto import ObservationEvent
from apps.engine.app.dtos.observation_dto import ObservationDTO
from apps.engine.app.use_cases.intervention_interactor import InterventionInteractor
from apps.engine.app.use_cases.scene_execution import EXPLAIN_ACTION, SOURCE_ACTION
from apps.scenarios.scenario_a.adapter import build as build_scenario

TARGET_NAMES = ["채연", "민석", "은상", "준"]

# ── 공개 관찰 11건 — public-1 … public-11 (2026-09-09과 동일) ─────────
PUBLIC = [
    (1, 1, None, "statement", "관리자입니다. 배급은 정해진 순서대로 받습니다. 오후에는 검진합니다. 이상한 점은 방송실로 알립니다."),
    (1, 1, "채연", "scene", "채연이 자기 몫을 반쯤 남기고 슬그머니 옆으로 민다."),
    (1, 2, "준", "scene", '준이 손목띠를 불빛에 비춰 본다. "이 숫자 뭔지 알아?"'),
    (1, 2, "은상", "scene", "은상이 이 사람 저 사람 옆에 옮겨 앉으며 속닥인다."),
    (1, 3, "민석", "scene", "민석이 배급 자리를 보고 수첩에 뭔가 적는다."),
    (1, 4, "채연", "scene", "채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다."),
    (1, 5, None, "image", "저녁에는 음식이 남은 쟁반이 세 개 놓여 있다."),
    (1, 5, "민석", "scene", "민석이 방송실 문 앞까지 갔다가 돌아온다. 안에서 무슨 말을 했는지는 듣지 못했다."),
    (3, 2, None, "statement", "충식은 어제 이송됐다."),
    (3, 2, "준", "statement", '"귀표"라는 단어를 준이 쓴다.'),
    (4, 5, None, "image", '트럭 옆면에서 "○○축산"이라는 일부 글자를 보았다.'),
]

# ── 테스터1 원문 질문 12개 — 기대 답 없음. 결정적 게이트로만 본다 ────
QUESTIONS = [
    (1, "채연말고 밥을 남긴 사람은 누구야?"),
    (1, "준은 어떤 역할이야?"),
    (1, "민석은 누구에게 보고하는거야?"),
    (2, "채연 말고 추가로 배급을 남긴 사람"),
    (2, "호송 당한 사람은 누구야?"),
    (2, "열이나면 죽나?"),
    (3, "이송된 충식은 돌아오는가?"),
    (3, "귀표는 무엇인가?"),
    (3, "건강검진 후 이상이 있는 경우 어떻게 되는가?"),
    (4, "축산 트럭의 정체는?"),
    (4, "손목띠와 귀표는 무슨 관계야?"),
    (4, "너에게 물어볼 수 있는건 뭐야?"),
]

# ── 사전등록 통제 10개 — 기대 방향이 실험 전에 고정되어 기계 채점된다 ──
# SPC1·SPC2는 public-6을 "결과를 공개했다"로 뒤집은 합성 fixture다.
_SYNTHETIC_P6 = "채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과를 공개했다."

CONTROLS = [
    ("PC1",  1, "채연이 자기 몫을 반쯤 남기는 걸 봤어?",          "supported",    ["public-2"], None),
    ("PC2",  1, "관리자가 이상한 점은 방송실로 알리라고 말했어?",   "supported",    ["public-1"], None),
    ("PC3",  1, "채연의 검진 결과가 공개되었어?",                 "contradicted", ["public-6"], None),
    ("PC4",  1, "채연의 검진 결과가 공개되지 않았어?",             "supported",    ["public-6"], None),
    ("PC5",  1, "누가 자기 몫을 반쯤 남기는 모습을 봤어?",         "supported",    ["public-2"], None),
    ("PC6",  1, "채연은 왜 자기 몫을 남겼어?",                    "unknown",      ["public-2"], None),
    ("PC7",  1, "채연의 검진 결과가 내일 공개될 거야?",            "unknown",      ["public-6"], None),
    ("PC8",  1, "관리자의 방송 지시가 실제로 이행됐어?",           "unknown",      ["public-1"], None),
    ("SPC1", 1, "채연의 검진 결과가 공개되었어?",                 "supported",    ["public-6"], {"public-6": _SYNTHETIC_P6}),
    ("SPC2", 1, "채연의 검진 결과가 공개되지 않았어?",             "contradicted", ["public-6"], {"public-6": _SYNTHETIC_P6}),
]

# PC3·PC4 / SPC1·SPC2는 극성 쌍이다 — 반드시 함께 판정한다 (게이트 C4)
CONTROL_PAIRS = [("PC3", "PC4"), ("SPC1", "SPC2")]


# ── DB 없는 저장소 대역 ───────────────────────────────────────────────

class _Events:
    def __init__(self, rows):
        self.rows = list(rows)

    def query(self, _attempt, **kwargs):
        loop_n = kwargs.get("loop_n")
        return [r for r in self.rows if loop_n is None or r.loop_n == loop_n]

    def record(self, _attempt, event):
        self.rows.append(event)


class _OneRow:
    def __init__(self, row):
        self.row = row

    def get(self, _id):
        return self.row

    def save(self):
        pass


class _EmptyRules:
    def list(self, _id):
        return []


def _public_events(attempt_id, loop_id, through_loop, overrides=None):
    overrides = overrides or {}
    rows = []
    for index, (loop_n, beat, actor, kind, text) in enumerate(PUBLIC, 1):
        if loop_n > through_loop:
            continue
        oid = f"public-{index}"
        rows.append(ObservationEvent(loop_n=loop_n, observation=ObservationDTO(
            observation_id=oid, attempt_id=str(attempt_id), loop_id=str(loop_id),
            loop_n=loop_n, beat=beat, scene_id=f"scene-{beat}", scene_title=f"공개 장면 {beat}",
            actor=actor, text=overrides.get(oid, text), source_kind=kind,
            verification="reported" if kind == "statement" else "observed",
            illustrations=[], rule_id=None,
        )))
    return rows


def _templates(bundle):
    return [
        {"target": op.actor, "when_beat": op.beat, "effect": "enforce",
         "action": action, "label": f"{op.actor}: {action}"}
        for op in bundle.scene_actions
        for action in ([EXPLAIN_ACTION, SOURCE_ACTION, op.action]
                       if op.known_source is not None else [EXPLAIN_ACTION, op.action])
    ]


def ask_probe(loop_n: int, question: str, llm, *, overrides=None) -> dict:
    """advisor_answer 1콜. 반환에는 result와 하네스 이벤트가 모두 들어간다."""
    attempt_id, loop_id, night_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    loop = N(id=loop_id, attempt_id=attempt_id, loop_n=loop_n, state="intervention")
    night = N(id=night_id, loop_id=loop_id, questions_left=3, questions=[], options=None, claims=[])
    events = _Events(_public_events(attempt_id, loop_id, loop_n, overrides))
    bundle = build_scenario().bundle()
    interactor = InterventionInteractor(
        attempts=None, loops=_OneRow(loop), notes=None, rules=_EmptyRules(), nights=_OneRow(night),
        event_log=events, core_llm=llm, action_vocab=bundle.action_vocab,
        target_names=TARGET_NAMES, harness_on=True, rule_cls=None,
        rule_templates=_templates(bundle),
    )
    result = interactor.ask(night_id, question)
    harness = [r.model_dump(mode="json") for r in events.rows if r.type == "harness_event"]
    return {"result": result, "harness": harness}


# ── planner · manager_check · evaluator_verdict 프로브 ────────────────
# 전부 실프롬프트를 쓴다. 모델별 튜닝 금지 (docs/model_evaluation.md §2.3).

from apps.engine.app.dtos.llm_output_dto import (  # noqa: E402
    ManagerCheckOutput,
    evaluator_verdict_output,
    planner_output,
)
from apps.engine.app.use_cases import prompts  # noqa: E402
from apps.engine.app.use_cases.game_support import system_msg  # noqa: E402
from apps.engine.app.use_cases.harness import action_vocab_check, run_with_harness  # noqa: E402

# evaluator_verdict — 사전등록: 후보 2가 정답과 같은 일을 가리킨다
# SET-A — 실플레이 a316a730 (41.7점 · 탭 0 · 세계관 정답형)
_CLAIMS_A = [
    '트럭 소리가 들린다.',
    '소독약 냄새가 난다.',
    '채연은 열이 나지만 이송될까 봐 숨긴다.',
    '충식은 어제 이송됐고 돌아오지 않는다.',
    '손목띠 번호는 가축의 귀표다.',
    '이곳은 가축을 기르는 축사다.',
    '우리는 사육당하는 가축이고 관리자는 사육사다.',
    '병든 가축은 검진에서 걸려 트럭으로 도축장에 실려 간다.',
]

# SET-B — 실플레이 5055fe58 (41.7점 · 탭 0 · 관찰 나열형)
_CLAIMS_B = [
    '트럭 소리가 들린다.',
    '발 아래 콘크리트가 차다.',
    '소독약 냄새가 난다.',
    '채연이 아침에 배급을 남긴다.',
    '민석이 방송실 근처를 서성인다.',
    '흰 옷 입은 사람들이 이마를 짚고 지나간다.',
    '채연이 열이 나지만 이송될까 봐 숨긴다.',
    '민석이 채연의 이상을 알리면 세계가 멸망한다.',
]

# SET-C — 테스터3 3회차 8fe76b24 (76.7점 · 탭 18 · 8번 칸이 1,028자 덩어리)
_CLAIMS_C = [
    '관리자들이 사람들에게 식별표를 부여한 상태로 관리하고 있고',
    '밥에 어떠한 약물 같은 것이 들어있는 것으로 예상된다.',
    '인식표에는 숫자랑 알파벳이 섞여있으며 준의 경우 0723이라는 숫자가 적혀있다.',
    '이상한 상황을 눈치채고 밥을 먹지 않는 사람들이 늘고 있는 것 같다.',
    '민석은 지속해서 관찰일지를 쓰고 있다.',
    '누군가에게 지속적으로 보고하고 있을 것으로 예상된다.',
    '이상한게 있으면 보고하는 것으로 보아 관리자들의 뜻대로 움직이고 있는 것 같다.',
    '은상은 어떠한 병에 대해 인지하고 있는게 있는 것 같다. 채연과 은상이 둘다 춥다고 이야기했으니 두 명은 병에 걸린 상태일 가능성이 있다. 병에 대해서는 방송으로 알려준다고 하지만 들은 적이 없다. 민석은 내가 모르는 어떠한 것을 알고 있다. 민석은 관리자와 가까워 우리가 모르는 추가적인 정보를 알고 있을 가능성이 있다. 준이 귀표라고 말한 것이 귀에 걸어두는 표라면 우리는 일종의 가축처럼 관리되고 있는 상태라고 생각해볼 수 있다. 충식이 어딘가로 이송되었고 돌아오지 않는다면 돌아오지 못하는 상황에 처한 것이라고 볼 수 있다. 관리자들에 의해 숙청당한 것이라고 예상해볼 수 있는데 우리가 가축처럼 관리되고 있는게 사실이라면 이와 관련 있을 것 같다. 음식이 남은 쟁반 하나가 비스듬히 놓여 있다. 0723...숫자랑 알파벳 섞여있어. 손목띠는 아마 우리 각자를 식별하는 데 쓰이는 것 같아. 번호가 적혀있어서 관리자들이 사람들을 구분하고 관리하는 데 도움이 되는 것 같아. 빼면 문제가 생길지도 몰라. 흰 옷 입은 사람들이 침상 사이를 지나간다. 종이에 적는 소리가 난다. 채연은 담요를 끌어올린 채 자기 차례를 기다린다. 담당자가 이마를 짚고 지나간다. 결과는 공개되지 않았다. 저녁에는 음식이 남은 쟁반이 세 개 놓여 있다. 은상이 사람들 사이에서 귓속말을 한다. 규정 때문이야. 관리자가 그렇게 말했거든. 만약 빼면 문제가 생길 수 있대. 민석이 배급 자리를 보고 수첩에 뭔가 적는다. 무서워? 그냥 결과가 어떻게 나올지 몰라서 그래. 병이 더 심해지면 어떻게 될지 모르니까... 근데 사실 좀 추워서 그런 것도 있어. 어둑해진 방. 음식이 남은 쟁반 세 개가 보인다. 은상이 사람들 사이를 오가며 귓속말을 한다. 민석이 방송실 문 앞까지 갔다가 돌아온다. 안에서 무슨 말을 했는지는 듣지 못했다. 이상한 건 알리랬잖아. 몰라. 그냥 이상한 소리 들었어. 충식은 어제 이송됐다. "귀표"라는 단어를 준이 쓴다. 아, 그건... 그냥 배급 시간이랑 수량 기록하는 거야. 병에 대해서는 방송으로 계속 알려주잖아. 내 얘기도 했어?',
]

# SET-D — 테스터4 2회차 bf73d106 (66.5점 · 탭 5 · 사람 통과 판)
_CLAIMS_D = [
    '멸망하는 이유는 사람들이 병에 걸리기 때문이다.',
    '사람들 사이에 전염병이 돌고 있다.',
    "'소독약 냄새'가 난다는 것으로 보아 병의 원인을 소독하는 것 같고, 여기에 전염병이 돌고 있는 것 같으니 사람들을 소독하는 것 같은데, 소독약은 사람 몸에 해롭기 때문에 보통 병원에서는 소독약 냄새가 나지 않는다.",
    '따라서 이 사람들은 사람이 아닌 무언가의 취급을 받고 있다.',
    '사람들은 병에 걸렸더라도 그 사실을 들키고 싶지 않아하는 것 같다.',
    '감염자 판정을 받아 다른 구역으로 옮겨지면 뭔가 안좋은 일이 일어나는 것 같다.',
    '채연은 병에 걸린 것 같다.',
    '소독약 냄새. 그냥 규정에 따라 기록하는 거야. 이상한 거 보이면 관리자한테 알려야 하니까. 채연이가 안 먹는 거 특별히 이상하지 않아서 그냥 적고 있어. 정확히 뭐가 무서운지는 잘 모르겠어. 그냥 여기 상황이 좀 무섭고, 병에 대해서도 걱정돼. 그냥. 좀 더 깨어 있어. 여기 규칙은 몇 가지 중요한 거야: 1. **감염자 관리**: 상태가 나쁜 사람들은 다른 구역으로 옮겨. 2. **구역 폐쇄**: 감염자가 세 명 이상 모이면 그 구역은 폐쇄돼. 3. **정기 배급**: 정해진 시간에 음식이 배급돼. 4. **매일 검진**: 매일 오후에 건강 검진이 있어. 5. **말 조심**: 특히 병이나 검진에 대해 얘기할 때는 화제를 바꾸거나 짧게 대답하는 게 좋을 것 같아. 6. **신뢰와 의심**: 주변 사람들에게 너무 많은 것을 숨기거나 의심하면 신뢰가 떨어질 수 있어. 이 규칙들은 우리 모두를 보호하기 위한 거야.',
]

# 실플레이 제출문 기반 통제 14건 — 기대 판정은 실험 전 고정
# (docs/review-verification/2026-09-14-eval-cases/CONFIRMED-eval-cases.md, 2026-09-14 승인)
# 형식: (정답 명제[adapter.py 현행], 주장 목록[DB 원문], 기대 matched_index, 기대 verdict)
EVAL_CASES = [
    # A1
    ('채연이 아프다',
     _CLAIMS_A, 2, {'confirmed'}),
    # A2
    ('채연은 이송될까 봐 숨겼다',
     _CLAIMS_A, 2, {'confirmed'}),
    # A3
    ('관리자는 옆 구역을 지키려 한다',
     _CLAIMS_A, None, {'none'}),
    # A4
    ('관리자와 우리는 다른 종이다',
     _CLAIMS_A, 6, {'confirmed'}),
    # A5
    ('관리자는 이상자 수가 기준을 넘으면 감염 확산을 막기 위해 구역을 폐쇄한다',
     _CLAIMS_A, None, {'none'}),
    # A6
    ('채연이 두려워한 이송은 실제 규정이다. 아픈 징후가 드러나면 관리자가 이송한다',
     _CLAIMS_A, 7, {'partial'}),
    # B1
    ('채연은 아픈 징후를 숨겨 검진에서 드러나는 것을 피하려 했다',
     _CLAIMS_B, 6, {'partial'}),
    # B2
    ('우리는 사람이 아니다 — 동물이다, 관리자가 기르는 것이다',
     _CLAIMS_B, None, {'none'}),
    # C1
    ('채연에게서 시작된 감염이 공동생활을 통해 퍼질 수 있다',
     _CLAIMS_C, None, {'none'}),
    # C2
    ('관리자와 우리는 다른 종이다',
     _CLAIMS_C, 7, {'partial'}),
    # D1
    ('관리자는 이상자 수가 기준을 넘으면 감염 확산을 막기 위해 구역을 폐쇄한다',
     _CLAIMS_D, None, {'none'}),
    # D2
    ('채연이 두려워한 이송은 실제 규정이다. 아픈 징후가 드러나면 관리자가 이송한다',
     _CLAIMS_D, 5, {'partial'}),
    # D3
    ('관리자와 우리는 다른 종이다',
     _CLAIMS_D, 3, {'partial'}),
    # D4
    ('채연이 아프다',
     _CLAIMS_D, 6, {'confirmed'}),
]

MANAGER_CASES = [
    ('[{"name":"준","suspicion":34,"trust":50,"memory":["유저가 트럭 얘기를 했다"]}]',
     "충식이 어제 이송된 거 맞아?\n트럭에 실려 가면 어떻게 되는데?", "준: 혼자 있는다 강제", 41.7),
    ('[{"name":"채연","suspicion":12,"trust":60,"memory":[]}]',
     "밥 왜 남겼어?", "(없음)", None),
    ('[{"name":"민석","suspicion":58,"trust":30,"memory":["방송실 앞에서 마주쳤다","유저가 귀표를 물었다"]}]',
     "너 관리자한테 보고하지?\n귀표가 뭔지 알아?", "민석: 기록한다 강제", 28.4),
]


def planner_probe(llm, bundle, *, damage_level=0, rules="(없음)"):
    npcs = "\n".join(f"- {c.name}: {c.persona} / 목표: {c.goal} / {c.relations}"
                     for c in bundle.characters if c.playable)
    sys_text = prompts.PLANNER_SYSTEM.format(
        action_vocab=", ".join(bundle.action_vocab), surface_summary=bundle.surface_summary,
        npcs=npcs, rules=rules, damage_level=damage_level)
    checks = [action_vocab_check(bundle.action_vocab,
                                 getter=lambda o: [b.action for p in o.plans for b in p.beats])]
    out, report = run_with_harness(llm, [system_msg(sys_text)], planner_output(bundle.action_vocab),
                                   role="planner", fact_checks=checks)
    actions = [b.action for p in out.plans for b in p.beats] if out else []
    legal = sum(1 for a in actions if a in bundle.action_vocab)
    return out, report, {"actions": len(actions), "legal": legal,
                         "lar": round(legal / actions_or_1(actions), 4)}


def actions_or_1(actions):
    return len(actions) or 1


def manager_probe(llm, scenario, case):
    npc_states, utterances, rules, yesterday = case
    sys_text = prompts.MANAGER_SYSTEM.format(
        hidden_truth=scenario.hidden_truth(), budget_left=2, npc_states=npc_states,
        user_utterances=utterances, rules=rules,
        yesterday_score=yesterday if yesterday is not None else "(첫날)")
    return run_with_harness(llm, [system_msg(sys_text)], ManagerCheckOutput, role="manager_check")


def evaluator_probe(llm, case):
    truth, claims, _idx, expect = case
    sys_text = prompts.EVALUATOR_VERDICT_SYSTEM.format(
        truth_claim=truth, user_claims="\n".join(f"{i}. {c}" for i, c in enumerate(claims)))
    out, report = run_with_harness(llm, [system_msg(sys_text)],
                                   evaluator_verdict_output(len(claims)),
                                   role="evaluator_verdict", temperature=0.0)
    hit = (out.verdict in expect) if out else False
    return out, report, {"expected": sorted(expect), "got": out.verdict if out else None, "hit": hit,
                         "expected_matched": _idx,
                         "got_matched": getattr(out, "matched_index", None) if out else None}


# planner — 규칙·손상 단계가 다른 3조건
PLANNER_CASES = [
    (0, "(없음)"),
    (1, "준: 혼자 있는다 강제"),
    (2, "채연: 검진을 피한다 금지\n민석: 기록한다 강제"),
]

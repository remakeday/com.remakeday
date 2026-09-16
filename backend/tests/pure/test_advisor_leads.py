"""신의 질문 = 단서 해금 — 리드 선택 순수 로직 (개선 2단계 임무 A)."""

from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
from apps.engine.app.use_cases.intervention_interactor import select_lead

L_RATION = AdvisorLeadDTO(
    key="ration", loop_n=1, cues=["배급", "쟁반"],
    text="배급 포대는 늘 같은 트럭에서 내려온다.", direction="내일 배급 자리를 지켜봐라.")
L_TRUCK = AdvisorLeadDTO(
    key="truck", loop_n=2, cues=["트럭", "이송"],
    text="트럭은 소등 뒤에만 온다.", direction="소등 후 소리를 기록해 둬라.")
L_BAND = AdvisorLeadDTO(
    key="band", loop_n=1, cues=["손목띠", "숫자"],
    text="손목띠 숫자는 자리 순서가 아니다.", direction="준에게 손목띠를 보여 달라고 해라.")

LEADS = [L_RATION, L_TRUCK, L_BAND]


def test_cue_match_wins_over_order():
    assert select_lead("손목띠 숫자가 뭐야?", LEADS, set(), 1).key == "band"


def test_loop_gating_excludes_future_leads():
    assert select_lead("트럭이 왜 와?", [L_TRUCK], set(), 1) is None


def test_no_cue_match_falls_back_to_earliest_unused():
    lead = select_lead("전혀 관련 없는 질문", LEADS, {"ration"}, 2)
    assert lead.key == "band"  # loop 1 리드 중 미사용 → 트럭(2회차)보다 먼저


def test_used_leads_are_never_reissued():
    assert select_lead("배급 쟁반 얘기", [L_RATION], {"ration"}, 3) is None

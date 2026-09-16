"""신의 질문 = 단서 해금 — 리드 선택 순수 로직 (개선 2단계 임무 A)."""

from apps.engine.app.dtos.scenario_dto import AdvisorLeadDTO
from apps.engine.app.use_cases.intervention_interactor import select_lead

L_RATION = AdvisorLeadDTO(
    key="ration", loop_n=1, cues=["배급", "쟁반"],
    anchor_cues=["배급"], target="준", ask="배급이 어디서 오는지")
L_TRUCK = AdvisorLeadDTO(
    key="truck", loop_n=2, cues=["트럭", "이송"],
    anchor_cues=["트럭"], target="준", rule_action="밤에 깨어 있는다")
L_BAND = AdvisorLeadDTO(
    key="band", loop_n=1, cues=["손목띠", "숫자"],
    anchor_cues=["손목띠"], target="준", rule_action="가진 것을 보여준다")

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

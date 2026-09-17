"""F11 원숭이손 소원 표 DTO (스펙 §3 새 개념 1·2·3)."""

import pytest
from pydantic import ValidationError

from apps.engine.app.dtos.event_log_dto import MonkeyPawOfferEvent
from apps.engine.app.dtos.scenario_dto import PawRuleDTO, PawWishDTO, SceneActionDTO


def _wish(**over):
    data = dict(key="k", label="소원", default_reason="이유", target_cell="motive",
                reveal=PawRuleDTO(actor="가", action="보인다", effect="enforce", beat=2),
                effects=[PawRuleDTO(actor="나", action="일어난다", effect="enforce", beat=5)],
                observation="관찰 문장")
    return PawWishDTO(**{**data, **over})


def test_wish_needs_hidden_effects_and_valid_cells():
    assert _wish().effects[0].beat == 5
    with pytest.raises(ValidationError):
        _wish(effects=[])
    with pytest.raises(ValidationError):
        _wish(target_cell="side_effect")  # 부작용 칸은 겨냥 대상이 아니다
    with pytest.raises(ValidationError):
        PawRuleDTO(actor="가", action="말", effect="silence", beat=2)  # 발화 침묵은 폐기


def test_scene_action_paw_only_and_world_effect_defaults():
    action = SceneActionDTO(beat=5, actor="가", action="행동", narration="서술", suppressed_narration="")
    assert action.paw_only is False and action.world_effect is None
    assert SceneActionDTO(beat=5, actor="가", action="행동", narration="서술", suppressed_narration="",
                          world_effect="rumor").world_effect == "rumor"
    with pytest.raises(ValidationError):
        SceneActionDTO(beat=5, actor="가", action="행동", narration="서술", suppressed_narration="",
                       world_effect="budget")


def test_offer_event_keeps_wish_key():
    event = MonkeyPawOfferEvent(loop_n=1, beat=2, offer_index=1, rule_id="-", reason_shown=None,
                                accepted=False, wish_key="k")
    assert event.wish_key == "k"

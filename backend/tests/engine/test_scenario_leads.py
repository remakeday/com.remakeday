from apps.scenarios.scenario_a.adapter import build


def test_leads_only_point_at_world_structure():
    bundle = build().bundle()
    knowledge_targets = {c.name for c in bundle.characters for _ in c.knowledge}
    dormant = {(a.actor, a.action) for a in bundle.scene_actions if a.dormant}
    assert len(bundle.advisor_leads) == 10
    for lead in bundle.advisor_leads:
        assert not hasattr(lead, "text")
        if lead.rule_action:
            assert (lead.target, lead.rule_action) in dormant, lead.key
        else:
            assert lead.target in knowledge_targets, lead.key
    assert "ration-truck" not in {l.key for l in bundle.advisor_leads}


def test_jun_knows_sack_letters_and_mirror_absence():
    bundle = build().bundle()
    jun = next(c for c in bundle.characters if c.code == "jun")
    ids = {k.id for k in jun.knowledge}
    assert {"jun-before-start-sack", "jun-before-start-face"} <= ids
    assert any(a.actor == "준" and a.action == "포대를 들여다본다" and a.dormant and a.beat == 3
               for a in bundle.scene_actions)

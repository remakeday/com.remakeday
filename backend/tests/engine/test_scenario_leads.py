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


# 순서표 5번 — 신의 질문 공개 사다리: 확인 가능한 사실만, 정체 단어·정답 문장 없음 (기획서 4.8⑤·5.6)
_IDENTITY_WORDS = ("가축", "동물", "사람이 아니", "종이다", "다른 종", "양돈", "농장", "손이 없")


def test_ladder_has_two_rungs_per_intervention_stage_with_unique_keys():
    ladder = build().bundle().advisor_ladder
    assert sorted(r.stage for r in ladder) == [1, 1, 2, 2, 3, 3, 4, 4]
    assert len({r.key for r in ladder}) == len(ladder)


def test_ladder_never_carries_identity_words_truth_claims_or_ending_lines():
    bundle = build().bundle()
    banned = [b.word for b in bundle.utterance_bans] + list(_IDENTITY_WORDS)
    truths = [t.text for t in bundle.truth_claims]
    endings = bundle.ending_lines + [line for lines in bundle.ending_outcomes.values() for line in lines]
    for rung in bundle.advisor_ladder:
        assert not [w for w in banned if w in rung.text], rung.key
        assert not [t for t in truths if t in rung.text], rung.key
        assert not [e for e in endings if e in rung.text or rung.text in e], rung.key

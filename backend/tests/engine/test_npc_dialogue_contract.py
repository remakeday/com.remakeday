"""Dialogue, evidence and budget are a single retriable day action."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from apps.engine.adapter.outbound.repositories.game_repository import LoopRepository
from apps.engine.app.use_cases.loop_interactor import GameStateError
from tests.engine.test_usecase_day import make_day, _agent_reply
from apps.engine.domain.entities.npc_memory import add_memory, forget_memory, visible_memories


def test_next_scene_reply_has_own_evidence_and_retry_does_not_charge_twice(db_session):
    day, _, _, info = make_day(db_session, [_agent_reply("응, 봤어."), _agent_reply("문 앞에서.")])
    first_id, second_id = uuid.uuid4(), uuid.uuid4()
    first = day.utter(info["loop_id"], "jun", "봤어?", request_id=first_id)
    assert day.utter(info["loop_id"], "jun", "봤어?", request_id=first_id) == first
    assert len(day._npc_llm.calls) == 1
    day.advance_beat(info["loop_id"])
    second = day.utter(info["loop_id"], "jun", "어디서?", request_id=second_id)
    retried = day.utter(info["loop_id"], "jun", "어디서?", request_id=second_id)
    assert (first["budget_left"], second["budget_left"], second["beat"]) == (7, 6, 2)
    assert first["observations"][0]["observation_id"] != second["observations"][0]["observation_id"]
    assert retried == second and len(day._npc_llm.calls) == 2
    source_ids = {source for note in day.list_notes(info["loop_id"])["notes"] for source in note["observation_ids"]}
    assert {first["observations"][0]["observation_id"], second["observations"][0]["observation_id"]} <= source_ids
    with pytest.raises(GameStateError):
        day.utter(info["loop_id"], "jun", "바뀐 질문", request_id=second_id)


def test_failed_dialogue_note_rolls_back_budget_reply_and_memory(db_session):
    day, _, _, info = make_day(db_session, [_agent_reply("응."), _agent_reply("다시 답할게.")])
    repo = LoopRepository(db_session)
    before_memory = list(repo.npc_state(info["loop_id"], "jun").memory)
    original = day._notes.upsert
    def fail(*args, **kwargs):
        db_session.execute(text("SELECT 1 / 0"))
    day._notes.upsert = fail
    key = uuid.uuid4()
    with pytest.raises(DBAPIError):
        day.utter(info["loop_id"], "jun", "안녕", request_id=key)
    db_session.expire_all()
    assert repo.get(info["loop_id"]).budget_left == 8
    assert repo.npc_state(info["loop_id"], "jun").memory == before_memory
    day._notes.upsert = original
    assert day.utter(info["loop_id"], "jun", "안녕", request_id=key)["budget_left"] == 7


def test_current_day_actions_are_owned_and_previous_loop_dialogue_is_absent(db_session):
    day, _, _, info = make_day(db_session, [_agent_reply("불안해서 그랬어."), _agent_reply("오늘 처음 듣는데.")])
    day.advance_beat(info["loop_id"])
    day.utter(info["loop_id"], "eunsang", "누구한테 들은 얘기를 한 거야?")
    system = day._npc_llm.calls[-1][0][0].content
    state = LoopRepository(db_session).npc_state(info["loop_id"], "eunsang")
    experience = next(m for m in state.memory if "action-2-은상" in m["id"])
    assert experience["text"] in system and experience["kind"] == "내가 한 일"
    repo = LoopRepository(db_session)
    state = repo.npc_state(info["loop_id"], "eunsang")
    state.memory.append("유저: 이전 반복 비밀표식")
    state.memory = list(state.memory)
    state.trust = 60
    repo.get(info["loop_id"]).state = "closed"
    repo.save()
    next_info = day.start_loop(repo.get(info["loop_id"]).attempt_id)
    day.utter(next_info["loop_id"], "eunsang", "오늘은 어때?")
    assert "이전 반복 비밀표식" not in day._npc_llm.calls[-1][0][0].content
    assert repo.npc_state(next_info["loop_id"], "eunsang").trust == 3


def test_manager_deletes_only_valid_id_and_all_reply_paths_keep_it_hidden(db_session):
    from apps.engine.app.dtos.llm_output_dto import ToolCallSpec
    from apps.engine.adapter.outbound.orms.game_state_orm import RuleOrm
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    from apps.engine.adapter.outbound.repositories.game_repository import RuleRepository
    day, scenario, attempt, info = make_day(db_session, [
        _agent_reply("기억이 잘 안 나."), {"answer": "그 얘기는 기억이 안 나.", "said_it": None},
    ])
    repo = LoopRepository(db_session)
    day.advance_beat(info["loop_id"])
    day.advance_beat(info["loop_id"])
    loop = repo.get(info["loop_id"])
    npc = repo.npc_state(loop.id, "minseok")
    source = f"{loop.id}:action-3-민석-기록한다"
    npc.memory = add_memory(npc.memory, memory_id="related-reply", beat=3, kind="dialogue",
        text="삭제할 문답 고유표식", speaker="민석", listeners=["민석"], source_ids=[source])
    before = loop.manager_budget_left
    day._core_llm._queue.append({"patches": [
        {"npc": "minseok", "kind": "memory_delete", "target": source, "reason": "기록 감추기"},
        {"npc": "민석", "kind": "memory_delete", "target": "없는 ID", "reason": "잘못된 요청"},
    ], "flagged_abnormal": []})
    day._manager_check(loop, scenario.bundle())
    repo.save()
    assert loop.manager_budget_left == before - 1
    audit = [e for e in EventLogRepository(db_session).query(attempt.id) if e.type == "manager_check"][-1]
    assert [p.applied for p in audit.patches] == [True, False]
    assert any(m["id"] == source and m["forgotten"] for m in npc.memory)
    assert "삭제할 문답 고유표식" not in str(visible_memories(npc.memory))
    RuleRepository(db_session).add(RuleOrm(attempt_id=attempt.id, rule_id="R1", source="user_choice",
        target="민석", action="보고를 물으면 자신이 한 일을 자세히 설명한다", effect="enforce", created_loop=1))
    assert day.utter(loop.id, "minseok", "무슨 보고를 했어?")["reply"] == "기억이 잘 안 나."
    asker = repo.npc_state(loop.id, "jun")
    day._run_ask_npc(loop, scenario.bundle(), asker, next(c for c in scenario.bundle().characters if c.code == "jun"),
                     ToolCallSpec(name="ask_npc", target="민석", question="무슨 보고를 했어?"))
    for messages, _ in day._npc_llm.calls:
        assert source not in messages[0].content and "삭제할 문답 고유표식" not in messages[0].content
    assert any(o["observation_id"] == source for o in day.list_observations(loop.id)["observations"])


def test_lost_character_never_returns_via_baseline_or_day_memory(db_session):
    day, _, _, info = make_day(db_session, [_agent_reply("같이 있어 줘.")])
    repo = LoopRepository(db_session)
    loop = repo.get(info["loop_id"])
    loop.damage_level = 3
    npc = repo.npc_state(loop.id, "eunsang")
    npc.memory = ["준: 충식이 기침했어."]
    repo.save()
    day.utter(loop.id, "eunsang", "누가 옆에 있었으면 좋겠어?")
    assert "충식" not in day._npc_llm.calls[-1][0][0].content


def test_asking_friend_does_not_preserve_deleted_fact_inside_own_question(db_session):
    from apps.engine.app.dtos.llm_output_dto import ToolCallSpec
    day, scenario, _, info = make_day(db_session, [{"answer": "기억이 잘 안 나.", "said_it": None}])
    repo = LoopRepository(db_session)
    loop = repo.get(info["loop_id"])
    asker = repo.npc_state(loop.id, "jun")
    asker.memory = add_memory(asker.memory, memory_id="source-to-delete", beat=1, kind="observed",
        text="복도 모퉁이의 푸른 단추", speaker=None, listeners=["준"])
    day._run_ask_npc(loop, scenario.bundle(), asker, next(c for c in scenario.bundle().characters if c.code == "jun"),
        ToolCallSpec(name="ask_npc", target="민석", question="복도 모퉁이의 푸른 단추 봤어?"))
    asker.memory, _ = forget_memory(asker.memory, "source-to-delete")
    visible = str(visible_memories(asker.memory))
    assert "푸른 단추" not in visible
    assert "기억이 잘 안 나" in visible  # Friend's independently heard answer remains.


def test_concurrent_retry_executes_model_and_charges_only_once(db_session):
    """A second real DB session must wait for the first committed response."""
    from sqlalchemy.orm import Session
    from apps.engine.adapter.outbound.repositories.event_log_repository import EventLogRepository
    from apps.engine.adapter.outbound.repositories.game_repository import NoteRepository, RuleRepository
    from apps.engine.adapter.outbound.repositories.scene_transaction import SceneTransaction
    day, _, _, info = make_day(db_session, [])
    started, release = Event(), Event()
    class PausingModel:
        calls = 0
        def complete(self, *_args, **_kwargs):
            self.calls += 1
            started.set()
            assert release.wait(5)
            return _agent_reply("방송에서 들었어.")
    model = PausingModel()
    engine = db_session.get_bind()
    key = uuid.uuid4()
    def send():
        with Session(engine) as session:
            worker = day.__class__.__new__(day.__class__)
            worker.__dict__.update(day.__dict__)
            worker._loops = LoopRepository(session)
            worker._events = EventLogRepository(session)
            worker._notes = NoteRepository(session)
            worker._rules = RuleRepository(session)
            worker._scene_transaction = SceneTransaction(session)
            worker._npc_llm = model
            return worker.utter(info["loop_id"], "minseok", "어디서 들었어?", request_id=key)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(send)
        assert started.wait(5)
        second = pool.submit(send)
        release.set()
        assert first.result(timeout=10) == second.result(timeout=10)
    db_session.expire_all()
    assert model.calls == 1 and LoopRepository(db_session).get(info["loop_id"]).budget_left == 7

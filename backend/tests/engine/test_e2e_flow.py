"""E2E — valid fake NPC responses and core fallbacks through five complete loops."""

from fastapi.testclient import TestClient


def test_full_attempt_five_loops_to_doom(db_session, monkeypatch, logged_in):
    from main import app
    from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
    from apps.engine.dependencies import engine_dependency
    npc = FakeLLM([{"reply": "조금 추워.", "suspicion_delta": 0, "trust_delta": 0}] * 5)
    monkeypatch.setattr(engine_dependency, "get_npc_llm", lambda: npc)

    with TestClient(app) as client:
        session_res = client.post("/sessions", json={}).json()
        attempt_id = session_res["attempt_id"]
        assert len(session_res["entry_lines"]) == 3

        for loop_n in range(1, 6):
            loop = client.post(f"/sessions/{attempt_id}/loops").json()
            assert loop["loop_n"] == loop_n
            assert "7시 1" in loop["morning_text"]
            assert "aftermath" in loop  # 계약 필드 (fake 폴백은 부작용 없음 → null)
            loop_id = loop["loop_id"]

            npcs = client.get(f"/loops/{loop_id}/npcs").json()["npcs"]
            assert npcs
            u = client.post(
                f"/loops/{loop_id}/utterances",
                json={"target": npcs[0]["code"], "text": "무슨 일 있어?"},
            )
            assert u.status_code == 200
            assert u.json()["budget_left"] == (9 - loop_n) - 1

            day_done = False
            for _ in range(6):
                b = client.post(f"/loops/{loop_id}/beats/next").json()
                assert "ambient" in b and "note_found" in b  # 계약 필드
                assert b["ambient"] is None or 2 <= len(b["ambient"]["lines"]) <= 4  # Eligible authored exchange.
                day_done = b["day_done"]
            assert day_done

            notes = client.get(f"/loops/{loop_id}/notes").json()["notes"]
            assert notes  # 파편 적립

            # 시나리오 중립: 파편 텍스트를 서술로 사용 (audit E2E에서도 동작)
            draft = client.post(
                f"/loops/{loop_id}/night/draft",
                json={
                    "tapped_note_ids": [notes[0]["id"]],
                    "free_text": f"{notes[0]['text']} 그게 이상했다.",
                },
            ).json()
            night_id = draft["night_id"]
            assert draft["claims"]

            # 수정 1회만
            assert client.patch(f"/nights/{night_id}/claims", json={"claims": draft["claims"]}).status_code == 200
            assert client.patch(f"/nights/{night_id}/claims", json={"claims": draft["claims"]}).status_code == 409

            result = client.post(f"/nights/{night_id}/submit").json()
            assert result["passed"] is False  # 폴백 판정은 전부 none
            assert result["cell_feedback"]  # 실패한 밤 → 정성 문장
            assert "비어 있다" in result["cell_feedback"]
            assert isinstance(result["wrong_claim_count"], int)

            if loop_n < 5:
                assert result["intervention_available"]
                q = client.post(f"/nights/{night_id}/questions", json={"text": "채연이 밥 남겼어?"}).json()
                assert q["remaining"] == 2
                opts = client.get(f"/nights/{night_id}/options").json()["options"]
                assert len(opts) == 3
                rule = client.post(f"/nights/{night_id}/rule", json={"choice": "1"}).json()
                assert rule["ok"]
            else:
                assert result["is_final"] and result["closed_by"] == "doom"
                assert result["cells"] is not None

        # 판이 닫혔으니 6회차는 없다
        assert client.post(f"/sessions/{attempt_id}/loops").status_code == 409

        # 인스펙터는 토큰, 개발 회고는 5회차 완료 시 점수 무관
        assert client.get(f"/attempts/{attempt_id}/harness").status_code == 200
        bad = client.get(f"/attempts/{attempt_id}/inspector", params={"token": "wrong"})
        assert bad.status_code == 403
        from core.matrix.grid_keymaker_secret_manager import get_settings
        ok = client.get(
            f"/attempts/{attempt_id}/inspector", params={"token": get_settings().inspector_token}
        )
        assert ok.status_code == 200
        assert ok.json()["events"]

        # 재도전 — prior 연결
        retry = client.post("/sessions", json={"prior_attempt_id": attempt_id}).json()
        assert retry["attempt_n"] == 2
        assert retry["prior_cell_results"] is not None

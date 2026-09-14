import sys

import pytest
from fastapi.testclient import TestClient

from apps.engine.dependencies.llm_factory import build_embedding, build_llm
from apps.engine.dependencies.scenario_factory import build_scenario

_OLLAMA = "http://localhost:11434"


def test_health_endpoint(db_session):
    from main import app

    with TestClient(app) as client:  # lifespan에서 시드 upsert 실행
        res = client.get("/health")

    assert res.status_code == 200
    body = res.json()
    assert body["scenario"] in ("a", "example")
    assert body["harness"] in ("on", "off")
    assert set(body["models"]) == {"npc", "core", "embedding"}
    assert body["db"] == "ok"


def test_scenario_fallback_when_a_is_missing(monkeypatch):
    build_scenario.cache_clear()
    monkeypatch.setitem(sys.modules, "apps.scenarios.scenario_a", None)
    monkeypatch.setitem(sys.modules, "apps.scenarios.scenario_a.adapter", None)

    scenario = build_scenario("a")

    assert scenario.name() == "example"
    build_scenario.cache_clear()


def test_unknown_scenario_fails_fast():
    with pytest.raises(ValueError):
        build_scenario("no-such-scenario")


def test_llm_factory_switches(monkeypatch):
    from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
    from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM

    assert isinstance(build_llm("fake", "m", _OLLAMA), FakeLLM)
    assert isinstance(build_llm("ollama", "gemma3:12b", _OLLAMA), OllamaLLM)
    from types import SimpleNamespace
    from google import genai
    from apps.engine.adapter.outbound.llm.gemini_llm import GeminiLLM
    from apps.engine.dependencies import llm_factory
    monkeypatch.setattr(llm_factory, "get_settings", lambda: SimpleNamespace(gemini_api_key="test-key", gemini_requests_per_minute=10))
    monkeypatch.setattr(genai, "Client", lambda **_: SimpleNamespace())
    gemini = build_llm("gemini", "gemini-test", _OLLAMA)
    assert isinstance(gemini, GeminiLLM) and gemini._model == "gemini-test"
    with pytest.raises(ValueError):
        build_llm("no-such-provider", "m", _OLLAMA)


def test_embedding_factory_switches():
    from apps.engine.adapter.outbound.embedding.fake_embedding import FakeEmbedding

    assert isinstance(build_embedding("fake"), FakeEmbedding)
    with pytest.raises(ValueError):
        build_embedding("no-such-provider")

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
    # 공개 경로(api.remakeday.com)라 기동 확인에 필요한 DB 상태만 준다 — 모델·시나리오·하네스 구성은 노출하지 않는다.
    assert res.json() == {"db": "ok"}


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


def test_ollama_embedding_factory_reads_model_and_dimensions(monkeypatch):
    from types import SimpleNamespace

    from apps.engine.adapter.outbound.embedding.ollama_embedding import OllamaEmbedding
    from apps.engine.dependencies import llm_factory

    monkeypatch.setattr(llm_factory, "get_settings", lambda: SimpleNamespace(
        ollama_base_url=_OLLAMA, embedding_model="emb-test", embedding_dimensions=1536))
    emb = build_embedding("ollama")
    assert isinstance(emb, OllamaEmbedding) and emb._model == "emb-test" and emb._dimensions == 1536


def test_alternative_rank_uses_stem_overlap_for_fake_embedding():
    from apps.engine.adapter.outbound.embedding.fake_embedding import FakeEmbedding
    from apps.engine.app.use_cases.alternative_rank import EmbeddingRank, StemOverlapRank
    from apps.engine.dependencies.llm_factory import build_alternative_rank

    assert isinstance(build_alternative_rank("fake", FakeEmbedding()), StemOverlapRank)
    assert isinstance(build_alternative_rank("ollama", FakeEmbedding()), EmbeddingRank)


def test_ollama_embedding_instruct_only_for_qwen3(monkeypatch):
    from apps.engine.dependencies import llm_factory
    from core.matrix.grid_keymaker_secret_manager import get_settings
    for model, expected in (("qwen3-embedding:4b", llm_factory.QWEN3_QUERY_INSTRUCT), ("bge-m3", None)):
        monkeypatch.setattr(get_settings(), "embedding_model", model)
        assert llm_factory.build_embedding("ollama")._query_instruct == expected

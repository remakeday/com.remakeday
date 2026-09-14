"""LLM·임베딩 provider 팩토리 — .env 스위치의 유일한 해석 지점 (모델정책 v1 §1).

알 수 없는 provider는 기동 실패(fail-fast).
"""

from functools import lru_cache

from apps.engine.adapter.outbound.embedding.fake_embedding import FakeEmbedding
from apps.engine.adapter.outbound.embedding.gemini_embedding import GeminiEmbedding
from apps.engine.adapter.outbound.llm.fake_llm import FakeLLM
from apps.engine.adapter.outbound.llm.gemini_llm import GeminiLLM
from apps.engine.adapter.outbound.llm.ollama_llm import OllamaLLM
from apps.engine.app.ports.output.embedding_port import EmbeddingPort
from apps.engine.app.ports.output.llm_port import LLMPort
from core.matrix.grid_keymaker_secret_manager import get_settings


def build_llm(provider: str, model: str, base_url: str) -> LLMPort:
    if provider == "fake":
        return FakeLLM()
    if provider == "ollama":
        return OllamaLLM(base_url=base_url, model=model)
    if provider == "gemini":
        settings = get_settings()
        return GeminiLLM(api_key=settings.gemini_api_key, model=model,
                         requests_per_minute=settings.gemini_requests_per_minute)
    raise ValueError(f"알 수 없는 LLM provider: {provider}")


def build_embedding(provider: str) -> EmbeddingPort:
    if provider == "fake":
        return FakeEmbedding()
    if provider == "gemini":
        return GeminiEmbedding(api_key=get_settings().gemini_api_key)
    raise ValueError(f"알 수 없는 임베딩 provider: {provider}")


@lru_cache(maxsize=1)
def get_npc_llm() -> LLMPort:
    s = get_settings()
    return build_llm(s.npc_llm_provider, s.npc_llm_model, s.ollama_base_url)


@lru_cache(maxsize=1)
def get_core_llm() -> LLMPort:
    s = get_settings()
    return build_llm(s.core_llm_provider, s.core_llm_model, s.ollama_base_url)


@lru_cache(maxsize=1)
def get_embedding() -> EmbeddingPort:
    return build_embedding(get_settings().embedding_provider)
